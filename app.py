"""데모 — 실행: streamlit run app.py

보고서와 함께 '절마다 누가 무엇을 읽고 무엇을 썼는지'를 보여 준다.
숫자만 보여 주는 화면이 아니라, 원고·읽기 경로·원문 대목을 나란히 놓는 데 집중했다.
"""
import json
import os
import threading
import time
from pathlib import Path

import pandas as pd
import streamlit as st

import config
from agents.citecheck import check_report
from agents.corpus import Corpus
from baseline import run_baseline
from graph import build_graph, run_question, Runtime
from metrics import fmt

st.set_page_config(page_title="딥리서치 에이전트", page_icon="🔎", layout="wide")

PRACTICE_CORPUS = config.DATA_DIR / "practice_corpus" / "docs.jsonl"


# ------------------------------------------------------------------ 불러오기
@st.cache_data(show_spinner=False)
def _load_corpus(path: str, mtime: float):
    return Corpus.load(Path(path))


def get_corpus(path: Path):
    return _load_corpus(str(path), path.stat().st_mtime)


@st.cache_data(show_spinner=False)
def _load_trace(path: str, mtime: float) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def list_runs() -> list:
    if not config.TRACES_DIR.exists():
        return []
    out = []
    for p in sorted(config.TRACES_DIR.glob("*.json"), reverse=True):
        t = _load_trace(str(p), p.stat().st_mtime)
        if t.get("metrics"):
            out.append(t)
    return out


def run_label(t: dict) -> str:
    practice = " · 연습" if t["settings"].get("practice") else ""
    return f"{t['qid']} · {t['variant_label']}{practice} · {t['run_id'][:15]}"


def questions() -> list:
    return json.loads((config.DATA_DIR / "questions.json").read_text(encoding="utf-8"))


def shrink_headings(md: str) -> str:
    """좁은 칸에서 나란히 볼 때 제목을 굵은 글씨로 바꿔 크기를 본문에 맞춘다."""
    out = []
    for line in md.splitlines():
        if line.startswith("#"):
            text = line.lstrip("#").strip()
            line = f"**{text}**" if text else ""
        out.append(line)
    return "\n".join(out)


def short(text: str, n: int = 38) -> str:
    return text if len(text) <= n else text[: n - 1] + "…"


# ------------------------------------------------------------------ 사이드바
st.sidebar.title("🔎 딥리서치 에이전트")
st.sidebar.caption("코디네이터가 나누고, 리서처들이 각자 읽고 쓰고, 이어 붙인다.")

default_corpus = config.CORPUS_PATH
if not default_corpus.exists() and PRACTICE_CORPUS.exists():
    default_corpus = PRACTICE_CORPUS
corpus_path = Path(st.sidebar.text_input("자료(docs.jsonl) 경로", str(default_corpus)))
corpus = None
if corpus_path.exists():
    corpus = get_corpus(corpus_path)
    st.sidebar.success(f"자료 {len(corpus.ids())}건 · {corpus.total_chars:,}자")
else:
    st.sidebar.warning("자료가 없습니다. 명령 프롬프트에서 `python build_corpus.py` 를 먼저 실행하세요.")
    if st.sidebar.button("연습용 합성 자료 만들기(사실 아님)"):
        from tests.make_fixture import build
        build(PRACTICE_CORPUS.parent)
        st.rerun()

has_key = bool(os.environ.get("OPENAI_API_KEY"))
st.sidebar.markdown(f"모델 `{config.MODEL}` · 컨텍스트 {config.CONTEXT_WINDOW:,} 토큰")
st.sidebar.markdown("API 키: " + ("✅ .env 에서 읽음" if has_key else "❌ 없음 → 연습 모드만 가능"))

runs = list_runs()
labels = [run_label(t) for t in runs]
picked_label = st.sidebar.selectbox("볼 실행", labels, index=0) if labels else None
current = runs[labels.index(picked_label)] if picked_label else None

tab_ask, tab_report, tab_work, tab_metrics, tab_compare, tab_corpus, tab_graph = st.tabs(
    ["질문하기", "보고서", "절별 작업 (누가 무엇을 읽고 썼나)", "지표", "비교", "자료", "파이프라인"])

# ------------------------------------------------------------------ 질문하기
with tab_ask:
    st.subheader("질문하기")
    qs = questions()
    options = [f"{q['id']} [{q['type_label']}] {q['question']}" for q in qs] + ["직접 입력"]
    choice = st.selectbox("질문", options)
    if choice == "직접 입력":
        qid, question = "custom", st.text_input("질문을 입력하세요", "")
    else:
        q = qs[options.index(choice)]
        qid, question = q["id"], q["question"]
        st.info(f"**왜 나눌 만한가** — {q['why_split']}")
    variants = st.multiselect("만들 보고서(같은 질문으로 여러 편)", list(config.VARIANTS),
                              default=["full"], format_func=lambda v: config.VARIANT_LABELS[v])
    c1, c2 = st.columns(2)
    practice = c1.checkbox("연습 모드(API 없이 가짜 모델)", value=not has_key)
    total_reads = c2.number_input("전체 읽기 예산(read_doc 횟수, 대조군도 같음)", 6, 200, config.Settings().total_reads)
    st.caption("'기본'을 먼저 실행하면 나머지 변형은 같은 목차를 재사용해 장치 하나만 달라지게 한다.")
    if st.button("실행", type="primary", disabled=not (corpus and question and variants)):
        order = [v for v in ["full", "no_peers", "no_recheck", "no_links", "single"] if v in variants]
        lines, result = [], {"dirs": []}

        def work():
            try:
                for v in order:
                    lines.append(f"▶ {config.VARIANT_LABELS[v]}")
                    if v == "single":
                        t = run_baseline(question, qid, practice=practice, corpus=corpus, progress=lines.append,
                                         total_reads=int(total_reads))
                    else:
                        s = config.make_settings(v, practice=practice, total_reads=int(total_reads))
                        t = run_question(question, qid, s, corpus=corpus, progress=lines.append)
                    result["dirs"].append(t["run_id"])
            except Exception as exc:  # 화면에 보여 준다
                result["error"] = exc

        th = threading.Thread(target=work, daemon=True)
        th.start()
        with st.status("실행 중… (GPT 실행은 몇 분 걸립니다)", expanded=True) as status:
            box = st.empty()
            while th.is_alive():
                box.code("\n".join(lines[-28:]) or "준비 중")
                time.sleep(0.5)
            box.code("\n".join(lines[-28:]))
            if "error" in result:
                status.update(label=f"오류: {result['error']}", state="error")
            else:
                status.update(label=f"완료 — 보고서 {len(result['dirs'])}편", state="complete")
        if result["dirs"]:
            st.success("왼쪽 '볼 실행'에서 새 결과를 고르세요.")
            st.cache_data.clear()

# ------------------------------------------------------------------ 보고서
with tab_report:
    if not current:
        st.info("아직 실행 결과가 없습니다. '질문하기'에서 실행하세요.")
    else:
        t = current
        m = t["metrics"]
        a, b, c, d = st.columns(4)
        a.metric("변형", t["variant_label"])
        b.metric("읽기", f"{m['raw']['reads_used']}/{m['raw']['total_budget']}")
        c.metric("인용 문서", m["values"]["cited_docs"])
        d.metric("경보", len(m["alarms_fired"]), delta=None if not m["alarms_fired"] else "확인 필요", delta_color="inverse")
        if t["settings"].get("practice"):
            st.warning("연습 모드 결과입니다. 원고는 실제 모델이 쓴 글이 아닙니다.")
        with st.expander("코디네이터의 목차와 나눈 이유", expanded=False):
            st.write(t["plan"].get("rationale", ""))
            st.dataframe(pd.DataFrame([{"절": s["id"], "역할": s.get("role_name", "-"), "제목": s["title"], "역할 질문": s["role"],
                                        "시작 자료": ", ".join(s["start_docs"]), "예산": s["budget"]}
                                       for s in t["plan"]["sections"]]), hide_index=True)
        st.markdown(t["report"]["markdown"])
        st.download_button("report.md 내려받기", t["report"]["markdown"], file_name=f"{t['run_id']}.md")

# ------------------------------------------------------------------ 절별 작업
with tab_work:
    if not current:
        st.info("실행 결과를 고르세요.")
    else:
        t = current
        raw = t["metrics"]["raw"]
        st.subheader("격리: 누가 몇 글자를 봤나")
        st.caption("코디네이터는 자료 본문을 읽지 않는다(목록과 원고만 본다). 리서처는 자기가 연 문서만 본다.")
        seen = {"① 자료 전체": raw["corpus_chars"], "② 코디네이터": raw["coordinator_seen_chars"]}
        seen.update({f"③ {k}": v for k, v in raw["agent_seen_chars"].items()})
        st.bar_chart(pd.DataFrame({"받은 글자 수": seen}), horizontal=True)
        meters = t.get("meters", {})
        st.dataframe(pd.DataFrame([{"에이전트": k, "받은 글자": v["seen_chars"], "쓴 글자": v["written_chars"],
                                    "API 호출": v["calls"], "입력 토큰(재전송 포함)": v["prompt_tokens"],
                                    "출력 토큰": v["completion_tokens"]} for k, v in meters.items()]), hide_index=True)

        attempts = t.get("plan_attempts", [])
        if attempts:
            with st.expander(f"코디네이터 목차 시도 {len(attempts)}회 (코드 검사 결과)"):
                for att in attempts:
                    st.markdown(f"**시도 {att['attempt']}** — 오류 {len(att['errors'])}건, 경고 {len(att['warnings'])}건")
                    for e in att["errors"]:
                        st.error(e)
                    for w in att["warnings"]:
                        st.warning(w)
        elif t.get("plan_source") not in (None, "new"):
            st.caption(f"목차: 기본 실행 `{t['plan_source']}` 의 목차를 그대로 사용")

        titles = (lambda d: corpus.title(d) if corpus and corpus.exists(d) else d)
        if t["variant"] == "single":
            r = t["single"]["reads"]
            st.subheader(f"단일 에이전트 — 읽기 {r['used']}/{r['budget']}회, 문서 {len(r['docs_read'])}건")
            st.dataframe(pd.DataFrame([{"#": e["n"], "문서": titles(e["doc"]), "쪽": f"{e['part']}/{e['parts']}",
                                        "경로(어디서 링크)": "시작 자료" if e["via"] == "start" else titles(e["via"]),
                                        "글자": e["chars"]} for e in r["log"]]), hide_index=True)
        for s in t["plan"]["sections"]:
            sec = t["sections"].get(s["id"], {})
            final = sec.get("final", {})
            with st.expander(f"{s['id']}. {s['title']} [{s.get('role_name', '-')}] — {sec.get('agent', '')} · "
                             f"인용 문서 {len(final.get('cited', []))}건 · 최종 신고 {final.get('status', '?')}",
                             expanded=False):
                st.markdown(f"**역할** {s['role']}  \n**포함** {s['scope_in']}  \n**제외** {s['scope_out']}  \n"
                            f"**시작 자료** {', '.join(titles(d) for d in s['start_docs'])} · **배정 예산** {s['budget']}회")
                if t["variant"] != "single":
                    r = sec.get("reads", {})
                    col1, col2 = st.columns([3, 2])
                    with col1:
                        st.markdown(f"**읽은 것** {r.get('used', 0)}/{r.get('budget', 0)}회")
                        st.dataframe(pd.DataFrame([{"#": e["n"], "라운드": e["round"], "문서": titles(e["doc"]),
                                                    "쪽": f"{e['part']}/{e['parts']}",
                                                    "경로(어디서 링크)": "시작 자료" if e["via"] == "start" else titles(e["via"])}
                                                   for e in r.get("log", [])]), hide_index=True)
                        if r.get("blocked") or r.get("unknown"):
                            st.caption(f"막힌 시도 — 링크 밖 문서 {len(r.get('blocked', []))}회, 없는 ID {len(r.get('unknown', []))}회")
                        if sec.get("gate_rejections"):
                            st.caption(f"예산 관문에서 돌려보낸 횟수 {sec['gate_rejections']}회")
                    with col2:
                        dot = ["digraph G { rankdir=LR; node [shape=box, fontsize=10];", '"시작" [shape=oval];']
                        for e in r.get("log", []):
                            src = "시작" if e["via"] == "start" else short(titles(e["via"]), 24)
                            dot.append(f'"{src}" -> "{short(titles(e["doc"]), 24)}";')
                        dot.append("}")
                        st.graphviz_chart("\n".join(dict.fromkeys(dot)))
                drafts = sec.get("drafts", [])
                if drafts:
                    dtabs = st.tabs([f"원고 {i + 1} (라운드 {d.get('round')}, {d.get('status')})" for i, d in enumerate(drafts)] + ["최종"])
                    for dt, d in zip(dtabs, drafts):
                        with dt:
                            st.markdown(d.get("markdown") or "_(없음)_")
                            if d.get("missing"):
                                st.caption(f"부족 신고: {d['missing']}")
                            if d.get("handoffs"):
                                st.caption("다른 절로 넘긴 단서: " + "; ".join(f"{h.get('section_id')}: {h.get('note')} [{h.get('doc_id')}]"
                                                                        for h in d["handoffs"]))
                    with dtabs[-1]:
                        for mg in sec.get("merges", []):
                            st.info(f"라운드 {mg['round']} 원고 처리: **{mg['decision']}** — {mg['reason']}")
                        st.markdown(final.get("markdown") or "_(없음)_")

# ------------------------------------------------------------------ 지표
with tab_metrics:
    if not current:
        st.info("실행 결과를 고르세요.")
    else:
        rows = current["metrics"]["rows"]
        st.subheader("경보 — 0이어야 한다")
        st.dataframe(pd.DataFrame([{"상태": "🚨" if r["value"] else "✅", "경보": r["label"], "값": fmt(r["key"], r["value"]),
                                    "보는 장치": r["device"], "설명": r["desc"]} for r in rows if r["kind"] == "alarm"]),
                     hide_index=True, use_container_width=True)
        st.subheader("신호 — 높낮이를 견주는 값(순위표가 아님)")
        st.dataframe(pd.DataFrame([{"신호": r["label"], "값": fmt(r["key"], r["value"]), "보는 장치": r["device"],
                                    "설명": r["desc"]} for r in rows if r["kind"] == "signal"]),
                     hide_index=True, use_container_width=True)
        st.caption("정답표와 판정 모델 없이, 만들어진 글과 실제로 읽은 기록만으로 계산한다.")

# ------------------------------------------------------------------ 비교
with tab_compare:
    if len(runs) < 2:
        st.info("같은 질문으로 2편 이상 실행하면 나란히 비교할 수 있습니다.")
    else:
        qids = list(dict.fromkeys(t["qid"] for t in runs))
        qtext = {t["qid"]: t["question"] for t in runs}
        cq = st.selectbox("질문", qids, index=qids.index(current["qid"]) if current and current["qid"] in qids else 0,
                          format_func=lambda x: f"{x} — {qtext.get(x, '')}")
        same = [t for t in runs if t["qid"] == cq]
        same_labels = [run_label(t) for t in same]
        default = []
        for v in ["full", "single", "no_recheck", "no_links", "no_peers"]:  # 기본과 대조군을 먼저 나란히
            hit = next((run_label(t) for t in same if t["variant"] == v), None)
            if hit:
                default.append(hit)
        chosen = st.multiselect("나란히 볼 실행(2~4편)", same_labels, default=default[:4])
        sel = [same[same_labels.index(c)] for c in chosen][:4]
        if len(sel) >= 2:
            table = []
            for r in sel[0]["metrics"]["rows"]:
                row = {"구분": "경보" if r["kind"] == "alarm" else "신호", "지표": r["label"], "장치": r["device"]}
                for t in sel:
                    row[t["variant_label"]] = fmt(r["key"], t["metrics"]["values"].get(r["key"]))
                table.append(row)
            st.dataframe(pd.DataFrame(table), hide_index=True, use_container_width=True)
            st.caption("지표는 명백한 실패를 거르는 데만 쓴다. 어느 쪽이 나은지는 아래 보고서를 직접 읽고 판단한다.")
            cols = st.columns(len(sel))
            for col, t in zip(cols, sel):
                with col:
                    st.markdown(f"#### {t['variant_label']}")
                    with st.container(height=700):
                        st.markdown(shrink_headings(t["report"]["markdown"]))
            st.subheader("인용 대조 — 원문 대목과 나란히")
            st.caption("단서(연도·숫자·영문 고유명사)로 인용 문서에서 가장 비슷한 대목을 찾았다. 제자리에 붙었는지는 직접 판단한다.")
            pick = st.selectbox("보고서", [t["variant_label"] for t in sel])
            t = sel[[x["variant_label"] for x in sel].index(pick)]
            if corpus:
                for i, r in enumerate(check_report(t["report"]["markdown_d"], corpus)[:40], 1):
                    with st.expander(f"{i}. {short(r['sentence'], 70)} → {r['title']}"):
                        st.markdown(f"**문장** {r['sentence']}")
                        st.markdown(f"**원문 대목** {r['snippet'] or '_(자동으로 찾을 단서 없음 — 문서를 직접 확인)_'}")
                        st.caption("단서: " + ", ".join(r["clues"][:8]))
            note_path = config.OUTPUT_DIR / f"judgment_{cq}.md"
            note = st.text_area("내 판단 — 어느 쪽이 나은가, 왜 그렇게 봤나, 마음에 안 드는 대목은 어느 절·어느 자료에서 왔나",
                                note_path.read_text(encoding="utf-8") if note_path.exists() else "", height=220)
            if st.button("내 판단 저장"):
                note_path.parent.mkdir(parents=True, exist_ok=True)
                note_path.write_text(note, encoding="utf-8")
                st.success(f"저장: {note_path}")

# ------------------------------------------------------------------ 자료
with tab_corpus:
    if not corpus:
        st.info("자료가 없습니다.")
    else:
        stats_path = config.DATA_DIR / "corpus_stats.json"
        if stats_path.exists():
            stats = json.loads(stats_path.read_text(encoding="utf-8"))
        else:
            from corpus_stats import compute_stats
            stats = compute_stats(corpus)
        a, b, c, d = st.columns(4)
        a.metric("문서", f"{stats['doc_count']}건")
        b.metric("글자", f"{stats['total_chars']:,}")
        c.metric("토큰", f"{stats['total_tokens']:,}")
        d.metric("컨텍스트 윈도우 대비", f"{stats['ratio_to_context']}배")
        st.bar_chart(pd.DataFrame({"토큰": {"자료 전체": stats["total_tokens"], f"컨텍스트 윈도우({stats['model']})": stats["context_window"]}}),
                     horizontal=True)
        st.caption(f"토큰 세는 방법: {stats['token_method']} · 링크 {stats['link_edges']:,}개(문서당 평균 {stats['avg_out_links']}) · "
                   f"가장 큰 연결 덩어리 {stats['largest_component']}/{stats['doc_count']}건")
        search = st.text_input("문서 찾기", "")
        rows = [{"ID": r["id"], "제목": r["title"], "글자": r["chars"], "쪽": r["parts"], "나가는 링크": r["out_links"],
                 "들어오는 링크": r["in_links"]} for r in corpus.catalog(config.Settings().page_chars)
                if search.lower() in (r["id"] + r["title"]).lower()]
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

# ------------------------------------------------------------------ 파이프라인
with tab_graph:
    st.subheader("LangGraph 구조")
    st.caption("상태(State)에는 목차·원고·라운드만 두고, 대화 기록을 가진 에이전트는 Runtime 에 둔다. "
               "점선은 조건부 분기(Send 로 서브에이전트를 동시에 내보내거나, 재파견하거나, 종합으로 넘어감).")
    dummy = Runtime.__new__(Runtime)
    dummy.settings = config.make_settings("full", practice=True)
    g = build_graph(dummy).get_graph()
    labels = {"plan": "① 기획\n(코디네이터)", "subagent": "② 서브에이전트 ×N\n(동시 실행)", "solo": "대조군\n(단일 에이전트)",
              "check": "③ 점검\n(부족 신고만 재파견)", "synthesize": "④ 종합", "measure": "⑤ 측정",
              "__start__": "시작", "__end__": "끝"}
    dot = ["digraph G { rankdir=TB; node [shape=box, style=rounded, fontsize=11];"]
    for node in g.nodes:
        dot.append(f'"{node}" [label="{labels.get(node, node)}"];')
    for e in g.edges:
        style = ' [style=dashed]' if e.conditional else ""
        dot.append(f'"{e.source}" -> "{e.target}"{style};')
    dot.append("}")
    st.graphviz_chart("\n".join(dot))
    if current:
        rounds = current.get("recheck", {}).get("rounds", [])
        st.markdown("**선택한 실행에서 점검이 어떻게 흘렀나**")
        for r in rounds:
            st.markdown(f"- {r.get('after_round', 0) + 1}라운드 뒤: 부족 신고 {r.get('todo') or '없음'} → "
                        f"{'재파견 ' + str(r.get('given')) if r.get('given') else '종합으로 (' + str(r.get('stop', '')) + ')'}")
