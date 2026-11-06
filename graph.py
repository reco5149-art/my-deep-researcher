"""파이프라인 — LangGraph 로 짠 '기획 → 배치 → 서브에이전트 → 점검 → 종합 → 측정'.

    python graph.py --q Q4                 기본(모든 장치 ON)으로 Q4 실행
    python graph.py --q Q4 --practice      연습 모드(API 없이 가짜 모델)
    python graph.py --question "직접 쓴 질문"
    python graph.py --mermaid              그래프 구조를 Mermaid 코드로 출력

그래프의 상태(State)에는 직렬화할 수 있는 값(목차·원고·라운드)만 두고,
대화 기록을 가진 에이전트 객체는 Runtime 에 둔다(노드가 클로저로 꺼내 쓴다).
"""
import argparse
import json
import operator
import sys
from dataclasses import asdict
from datetime import datetime
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

import config
from agents import prompts
from agents.coordinator import Coordinator, merge_drafts, plan_system_text, validate_plan
from agents.corpus import Corpus, CorpusMissing
from agents.llm import make_llm
from agents.report import assemble
from agents.researcher import Researcher, SingleAgent
from agents.trace import RunTrace
from metrics import compute as compute_metrics, fmt


# ------------------------------------------------------------------ 상태
def merge_dict(a: dict, b: dict) -> dict:
    return {**(a or {}), **(b or {})}


class State(TypedDict, total=False):
    question: str
    plan: dict                                   # 코디네이터가 짠 목차
    round: int                                   # 0 = 1차 배치, 1.. = 재파견 라운드
    jobs: list                                   # 이번 라운드에 내보낼 절 [{sid, extra, note}]
    incoming: Annotated[dict, merge_dict]        # 서브에이전트들이 동시에 채우는 원고 {"r0:S1": draft}
    drafts: dict                                 # 절마다 지금 채택된 원고 {sid: draft}
    merges: Annotated[list, operator.add]        # 두 번째 원고 처리 기록
    recheck_log: Annotated[list, operator.add]   # 점검 기록
    reserve_left: int                            # 남은 재파견 예약 예산
    report: dict
    metrics: dict


class SubTask(TypedDict):
    sid: str
    round: int
    extra: int
    note: str


class Runtime:
    """그래프 밖에 두는 것들: 자료, 모델, 에이전트 객체(대화 기록 포함), 실행 기록."""

    def __init__(self, question, qid, settings, corpus, trace, plan=None, plan_source="new"):
        self.question, self.qid, self.settings, self.corpus, self.trace = question, qid, settings, corpus, trace
        self.llm = make_llm(settings)
        self.coord = Coordinator(question, corpus, settings, self.llm, trace)
        self.given_plan, self.plan_source = plan, plan_source
        self.researchers = {}
        self.single = None


def _failed(error: str) -> dict:
    return {"round": 1, "markdown": "", "status": "failed", "missing": error, "handoffs": [], "cited": [],
            "unread_cited": [], "unknown_cited": [], "chars": 0, "reads_used": 0}


# ------------------------------------------------------------------ 그래프
def build_graph(rt: Runtime):
    s = rt.settings

    def plan_node(state: State) -> dict:
        """① 기획: 코디네이터가 자료 '목록'만 보고 목차·역할·시작 자료·예산을 정한다(코드가 검사)."""
        plan = rt.given_plan or rt.coord.plan()
        rt.trace.set("plan", plan)
        rt.trace.set("plan_source", rt.plan_source)
        rt.trace.set("plan_attempts", rt.coord.plan_attempts)
        sections = plan["sections"]
        if s.single_agent:
            rt.single = SingleAgent(sections, rt.question, rt.corpus, s, rt.llm, rt.trace, budget=s.total_reads)
            return {"plan": plan, "round": 0, "jobs": [], "drafts": {}, "reserve_left": 0}
        rt.researchers = {sec["id"]: Researcher(sec, sections, rt.question, rt.corpus, s, rt.llm, rt.trace, index=i)
                          for i, sec in enumerate(sections)}
        rt.trace.log("코디네이터", f"리서처 {len(sections)}명 동시 파견 (남의 구역 알림 {'ON' if s.tell_peers else 'OFF'}, "
                                 f"links 탐색 {'ON' if s.use_links else 'OFF'})")
        return {"plan": plan, "round": 0, "drafts": {},
                "jobs": [{"sid": sec["id"], "extra": 0, "note": ""} for sec in sections],
                "reserve_left": s.recheck_reserve if s.recheck else 0}

    def dispatch(state: State):
        """② 배치: 이번 라운드의 절들을 서브에이전트로 동시에 내보낸다(Send = 병렬 분기)."""
        if s.single_agent:
            return "solo"
        return [Send("subagent", {"sid": j["sid"], "round": state["round"], "extra": j["extra"], "note": j["note"]})
                for j in state["jobs"]]

    def subagent_node(task: SubTask) -> dict:
        """서브에이전트: 자기 구역의 자료만 읽고 원고와 신고를 올린다(원문은 위로 올라가지 않는다)."""
        r = rt.researchers[task["sid"]]
        try:
            draft = r.run_round(task["extra"], task["note"])
        except Exception as exc:  # API 오류 등 — 이 절만 실패로 남기고 계속한다
            rt.trace.log(r.name, f"오류: {exc}")
            draft = _failed(f"오류: {exc}")
        return {"incoming": {f"r{task['round']}:{task['sid']}": draft}}

    def solo_node(state: State) -> dict:
        """대조군: 한 에이전트가 같은 목차·시작 자료·총예산으로 모든 절을 쓴다."""
        try:
            rt.single.run()
        except Exception as exc:
            rt.trace.log("단일 에이전트", f"오류: {exc}")
        drafts = {sec["id"]: rt.single.drafts.get(sec["id"]) or _failed("제출하지 않음") for sec in state["plan"]["sections"]}
        return {"drafts": drafts}

    def check_node(state: State) -> dict:
        """③ 점검: 원고를 받아(두 번째 원고는 병합 규칙으로) 스스로 '부족'이라 신고한 절만 다시 내보낸다."""
        rnd = state["round"]
        prefix = f"r{rnd}:"
        new = {k[len(prefix):]: v for k, v in state.get("incoming", {}).items() if k.startswith(prefix)}
        drafts = dict(state.get("drafts", {}))
        merges = []
        for sid, draft in new.items():
            if rnd == 0 or sid not in drafts:
                drafts[sid] = draft
                continue
            merged, decision, reason = merge_drafts(drafts[sid], draft)
            drafts[sid] = merged
            merges.append({"sid": sid, "round": rnd + 1, "decision": decision, "reason": reason})
            rt.trace.log("코디네이터", f"{sid} 두 번째 원고 처리: {decision} — {reason}")
        rt.trace.save()

        left = state.get("reserve_left", 0)
        todo = Coordinator.pick_recheck(drafts) if s.recheck else []
        if not s.recheck or rnd >= s.recheck_rounds or not todo or left <= 0:
            reason = ("점검 OFF" if not s.recheck else "바퀴 상한" if rnd >= s.recheck_rounds else
                      "부족 신고 없음" if not todo else "예약 예산 소진")
            return {"drafts": drafts, "merges": merges, "jobs": [],
                    "recheck_log": [{"after_round": rnd, "todo": todo, "given": {}, "stop": reason}]}
        per = min(s.recheck_reads_per_section, max(1, left // len(todo)))
        jobs, given = [], {}
        for sid in todo:
            if left <= 0:
                break
            extra = min(per, left)
            left -= extra
            given[sid] = extra
            hand = Coordinator.handoffs_for(sid, drafts)
            hand_text = ("다른 절 리서처들이 이 절로 넘긴 단서:\n" + "\n".join(
                f"- ({h['from']}) {h.get('note', '')} [d:{h.get('doc_id', '')}]" for h in hand)) if hand else ""
            note = prompts.RECHECK_MESSAGE.format(
                round_no=rnd + 2, missing=drafts[sid].get("missing") or "(사유 없음)", extra=extra,
                left=rt.researchers[sid].state.left + extra, handoffs=hand_text)
            jobs.append({"sid": sid, "extra": extra, "note": note})
        rt.trace.log("코디네이터", f"점검 {rnd + 1}바퀴째: 부족 신고 {todo} → 재파견 {given}")
        return {"drafts": drafts, "merges": merges, "jobs": jobs, "round": rnd + 1, "reserve_left": left,
                "recheck_log": [{"after_round": rnd, "todo": todo, "given": given}]}

    def route_after_check(state: State):
        if state.get("jobs"):
            return dispatch(state)
        return "synthesize"

    def synthesize_node(state: State) -> dict:
        """④ 종합: 절 원고는 코드가 그대로 붙이고, 코디네이터는 서론·연결 문장·맺음말만 쓴다."""
        sections = state["plan"]["sections"]
        try:
            frame = rt.coord.synthesize(sections, state["drafts"])
        except Exception as exc:
            rt.trace.log("코디네이터", f"종합 오류: {exc} — 서론·맺음말 없이 이어 붙인다")
            frame = {"title": rt.question, "intro": "", "transitions": [], "conclusion": ""}
        readers = {}
        if s.single_agent:
            readers = {d: ["단일"] for d in rt.single.state.docs_read()}
        else:
            for sid, r in rt.researchers.items():
                for d in r.state.docs_read():
                    readers.setdefault(d, []).append(sid)
        return {"report": assemble(rt.question, sections, state["drafts"], frame, rt.corpus, readers)}

    def measure_node(state: State) -> dict:
        """⑤ 측정: 정답표·판정 모델 없이, 만들어진 글과 실제로 읽은 기록만으로 지표를 계산한다."""
        _record(rt, state)
        metrics = compute_metrics(rt.trace.data, rt.corpus)
        rt.trace.set("metrics", metrics)
        alarms = metrics["alarms_fired"]
        rt.trace.log("측정", "경보 없음" if not alarms else f"경보: {', '.join(alarms)}")
        rt.trace.save()
        return {"metrics": metrics}

    g = StateGraph(State)
    g.add_node("plan", plan_node)
    g.add_node("subagent", subagent_node)
    g.add_node("solo", solo_node)
    g.add_node("check", check_node)
    g.add_node("synthesize", synthesize_node)
    g.add_node("measure", measure_node)
    g.add_edge(START, "plan")
    g.add_conditional_edges("plan", dispatch, ["subagent", "solo"])
    g.add_edge("subagent", "check")
    g.add_conditional_edges("check", route_after_check, ["subagent", "synthesize"])
    g.add_edge("solo", "synthesize")
    g.add_edge("synthesize", "measure")
    g.add_edge("measure", END)
    return g.compile()


def _record(rt: Runtime, state: State) -> None:
    """에이전트 객체에 있던 읽기 기록·계량값을 실행 기록(trace)으로 옮긴다."""
    s, t = rt.settings, rt.trace
    sections = state["plan"]["sections"]
    meters, submit_rej, gate_rej = {}, 0, 0
    merges_by = {}
    for m in state.get("merges", []):
        merges_by.setdefault(m["sid"], []).append(m)
    if s.single_agent:
        a = rt.single
        for sec in sections:
            t.section(sec["id"]).update({"meta": sec, "agent": a.name, "merges": [],
                                         "drafts": [h for h in a.history if h["section_id"] == sec["id"]],
                                         "final": state["drafts"][sec["id"]]})
        t.set("single", {"reads": a.state.to_dict(), "finish_rejections": a.finish_rejections, "finished": a.finished})
        meters[a.name] = a.meter()
        submit_rej, gate_rej = a.submit_rejections, a.gate_rejections
    else:
        for sec in sections:
            r = rt.researchers[sec["id"]]
            t.section(sec["id"]).update({"meta": sec, "agent": r.name, "reads": r.state.to_dict(), "drafts": r.drafts,
                                         "merges": merges_by.get(sec["id"], []), "final": state["drafts"][sec["id"]],
                                         "submit_rejections": r.submit_rejections, "gate_rejections": r.gate_rejections})
            meters[r.name] = r.meter()
            submit_rej += r.submit_rejections
            gate_rej += r.gate_rejections
    meters["코디네이터"] = rt.coord.meter()
    if rt.plan_source != "new":
        # 목차를 재사용한 실행도, 그 목차를 짤 때 코디네이터가 본 자료 목록 분량을 '본 글자'에 넣어야 공정하다
        planning = len(plan_system_text(s)) + len(prompts.PLAN_USER.format(
            question=rt.question, doc_count=len(rt.corpus.ids()), catalog=rt.corpus.catalog_text(s.page_chars)))
        meters["코디네이터"]["seen_chars"] += planning
        t.set("plan_seen_chars_added", planning)
    t.set("meters", meters)
    t.set("submit_rejections", submit_rej)
    t.set("gate_rejections", gate_rej)
    t.set("recheck", {"enabled": s.recheck, "rounds": state.get("recheck_log", []),
                      "reserve_left": state.get("reserve_left", 0)})
    t.set("report", state["report"])


# ------------------------------------------------------------------ 실행
def find_reusable_plan(qid: str, practice: bool, corpus_name: str):
    """같은 질문으로 먼저 돌린 '기본' 실행의 목차(장치 하나만 바꾼 비교를 위해 같은 목차를 쓴다)."""
    if not config.TRACES_DIR.exists():
        return None, None
    for path in sorted(config.TRACES_DIR.glob("*.json"), reverse=True):
        try:
            t = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if (t.get("qid") == qid and t.get("variant") == "full" and bool(t["settings"].get("practice")) == practice
                and t.get("plan") and t.get("corpus", {}).get("name") == corpus_name):
            return t["plan"], t["run_id"]
    return None, None


def run_question(question: str, qid: str, settings, corpus: Corpus = None, progress=None,
                 reuse_plan: bool = True, plan: dict = None, plan_source: str = None) -> dict:
    """한 질문을 끝까지 돌리고 실행 기록(trace)을 돌려준다. 결과는 output/ 에 저장된다."""
    corpus = corpus or Corpus.load()
    variant = settings.variant_name()
    run_id = f"{datetime.now():%Y%m%d-%H%M%S}_{qid}_{variant}" + ("_practice" if settings.practice else "")
    n = 2
    while (config.TRACES_DIR / f"{run_id}.json").exists():
        run_id = f"{run_id.split('~')[0]}~{n}"
        n += 1
    trace = RunTrace(run_id, {
        "qid": qid, "question": question, "variant": variant, "variant_label": config.VARIANT_LABELS[variant],
        "settings": asdict(settings), "corpus": {"name": corpus.name, "docs": len(corpus.ids()), "chars": corpus.total_chars},
    }, progress=progress)
    trace.log("시작", f"{config.VARIANT_LABELS[variant]} · 모델 {settings.model}{' (연습 모드)' if settings.practice else ''}")

    if plan is not None:
        plan_source = plan_source or "given"
        trace.log("코디네이터", f"같은 질문의 기본 실행({plan_source}) 목차를 그대로 쓴다")
    elif reuse_plan and variant != "full":
        plan, plan_source = find_reusable_plan(qid, settings.practice, corpus.name)
        if plan is not None:
            errors, _ = validate_plan(plan, corpus, settings)
            if errors and not settings.single_agent:
                trace.log("코디네이터", f"재사용 목차가 이번 설정의 검사를 통과하지 못해 새로 짠다: {errors[0]}")
                plan, plan_source = None, "new"
            else:
                trace.log("코디네이터", f"같은 질문의 기본 실행({plan_source}) 목차를 그대로 쓴다")
        else:
            plan_source = "new"
    else:
        plan_source = "new"

    rt = Runtime(question, qid, settings, corpus, trace, plan=plan, plan_source=plan_source)
    app = build_graph(rt)
    app.invoke({"question": question}, config={"recursion_limit": 60, "max_concurrency": settings.max_workers})

    config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = config.REPORTS_DIR / f"{run_id}.md"
    report_path.write_text(trace.data["report"]["markdown"], encoding="utf-8")
    m = trace.data["metrics"]
    line = {
        "run_id": run_id, "qid": qid, "question": question, "variant": variant, "model": settings.model,
        "practice": settings.practice, "started_at": trace.data["started_at"], "elapsed_sec": trace.data.get("elapsed_sec"),
        "reads_used": m["raw"]["reads_used"], "total_budget": m["raw"]["total_budget"], "alarms": m["alarms_fired"],
        "metrics": m["values"], "report": f"output/reports/{run_id}.md", "trace": f"output/traces/{run_id}.json",
    }
    with open(config.RUNS_JSONL, "a", encoding="utf-8") as f:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")
    return trace.data


def print_metrics(t: dict) -> None:
    print(f"\n── {t['variant_label']} · {t['run_id']}")
    for row in t["metrics"]["rows"]:
        flag = "🚨" if row["kind"] == "alarm" and row["value"] else ("  " if row["kind"] == "signal" else "✅")
        print(f" {flag} {row['label']:<16} {fmt(row['key'], row['value']):>8}   [{row['device']}]")
    print(f"보고서: output/reports/{t['run_id']}.md")


def load_questions() -> list:
    return json.loads((config.DATA_DIR / "questions.json").read_text(encoding="utf-8"))


def resolve_question(qid_arg: str = None, text: str = None):
    if text:
        return "custom", text
    for q in load_questions():
        if q["id"].lower() == (qid_arg or "").lower():
            return q["id"], q["question"]
    sys.exit(f"질문 ID {qid_arg} 가 없습니다. data/questions.json 을 확인하세요.")


def mermaid() -> str:
    """그래프 구조를 Mermaid 코드로 돌려준다(REPORT 의 구조도에 쓴다)."""
    dummy = Runtime.__new__(Runtime)
    dummy.settings = config.make_settings("full", practice=True)
    return build_graph(dummy).get_graph().draw_mermaid()


def main() -> None:
    p = argparse.ArgumentParser(description="딥리서치 파이프라인(LangGraph) 실행")
    p.add_argument("--q", help="질문 ID (예: Q4)")
    p.add_argument("--question", help="직접 쓴 질문")
    p.add_argument("--variant", default="full", choices=[v for v in config.VARIANTS if v != "single"],
                   help="장치 하나를 끈 변형(대조군은 baseline.py)")
    p.add_argument("--practice", action="store_true", help="연습 모드(API 없이)")
    p.add_argument("--corpus", help="자료 파일 경로(기본: data/corpus.json)")
    p.add_argument("--total-reads", type=int)
    p.add_argument("--mermaid", action="store_true", help="그래프 구조를 Mermaid 코드로 출력")
    args = p.parse_args()
    if args.mermaid:
        print(mermaid())
        return
    if not (args.q or args.question):
        sys.exit("질문을 고르세요: python graph.py --q Q4")
    qid, question = resolve_question(args.q, args.question)
    try:
        corpus = Corpus.load(args.corpus) if args.corpus else Corpus.load()
    except CorpusMissing as exc:
        sys.exit(str(exc))
    overrides = {"practice": args.practice}
    if args.total_reads:
        overrides["total_reads"] = args.total_reads
    settings = config.make_settings(args.variant, **overrides)
    print(f"▶ {qid} · {config.VARIANT_LABELS[args.variant]}")
    print_metrics(run_question(question, qid, settings, corpus=corpus, progress=print))


if __name__ == "__main__":
    main()
