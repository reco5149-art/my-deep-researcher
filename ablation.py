"""스위치를 하나씩 끄고 평가하는 실험.

    python ablation.py --q Q4                  기본 → 남의 구역 OFF → 점검 OFF → links OFF → 단일 대조군, 5편
    python ablation.py --q Q4 --practice       연습 모드(API 없이)
    python ablation.py --q Q4 --only full,single
    python ablation.py --q Q4 --table-only     새로 실행하지 않고, 이미 있는 실행으로 표만 다시 만든다

- 장치를 끈 실행과 대조군은 '기본' 실행의 목차를 그대로 쓴다. 그래서 장치 하나만 달라진다.
- 결과: output/ablation.json(질문별 지표 표, 기본과의 차이, 대조군 예산 확인)
        output/ablation_<질문>.md(나란히 비교 문서 — 인용 대조 표본, '내 판단' 칸 포함)
- 지표는 명백한 실패를 거르고 어디를 볼지 가리키는 데만 쓴다. 어느 쪽이 나은지는 보고서를 읽고 사람이 정한다.
"""
import argparse
import json
import sys
from datetime import datetime

import config
from agents.citecheck import check_report, sample
from agents.corpus import Corpus, CorpusMissing
from baseline import run_baseline
from graph import resolve_question, run_question
from metrics import DEFS, fmt

ORDER = ["full", "no_peers", "no_recheck", "no_links", "single"]


def latest_traces(qid: str, practice: bool) -> dict:
    picked = {}
    for path in sorted(config.TRACES_DIR.glob(f"*_{qid}_*.json"), reverse=True):
        t = json.loads(path.read_text(encoding="utf-8"))
        if bool(t["settings"].get("practice")) == practice and t.get("metrics"):
            picked.setdefault(t["variant"], t)
    return {v: picked[v] for v in ORDER if v in picked}


def build_table(runs: dict) -> list:
    base = runs.get("full")
    rows = []
    for key, label, kind, device, desc in DEFS:
        row = {"key": key, "label": label, "kind": kind, "device": device, "desc": desc, "values": {}, "delta_vs_full": {}}
        for v, t in runs.items():
            val = t["metrics"]["values"].get(key)
            row["values"][v] = val
            if base and v != "full" and isinstance(val, (int, float)) and isinstance(base["metrics"]["values"].get(key), (int, float)):
                row["delta_vs_full"][v] = round(val - base["metrics"]["values"][key], 4)
        rows.append(row)
    return rows


def budget_check(runs: dict) -> dict:
    out = {}
    for v, t in runs.items():
        raw = t["metrics"]["raw"]
        out[v] = {"reads_used": raw["reads_used"], "total_budget": raw["total_budget"],
                  "use": round(raw["reads_used"] / raw["total_budget"], 3) if raw["total_budget"] else None}
    if "single" in runs:
        use = out["single"]["use"] or 0
        out["single"]["verdict"] = "공정(예산을 다 씀)" if use >= 0.9 else "주의: 90% 미만 — 상대를 묶어 둔 비교일 수 있다"
    return out


def section_rows(t: dict) -> list:
    rows = []
    for s in t["plan"]["sections"]:
        sec = t["sections"].get(s["id"], {})
        final = sec.get("final", {})
        if t["variant"] == "single":
            reads = "(단일 에이전트가 함께 읽음)"
        else:
            r = sec.get("reads", {})
            reads = f"{r.get('used', 0)}/{r.get('budget', 0)}회, 문서 {len(r.get('docs_read', []))}건"
        status = " → ".join(d.get("status", "?") for d in sec.get("drafts", [])) or "-"
        merge = "; ".join(m["decision"] for m in sec.get("merges", [])) or "-"
        rows.append(f"| {s['id']} {s['title']} [{s.get('role_name', '-')}] | {reads} | {len(final.get('cited', []))} | {status} | {merge} |")
    return rows


def build_markdown(qid: str, runs: dict, table: list, budget: dict, corpus) -> str:
    first = next(iter(runs.values()))
    labels = [config.VARIANT_LABELS[v] for v in runs]
    out = [f"# 비교: {qid} — {first['question']}", "",
           f"만든 시각 {datetime.now():%Y-%m-%d %H:%M} · 자료 {first['corpus']['docs']}건 · 모델 {first['settings']['model']}"
           + (" · 연습 모드" if first["settings"].get("practice") else ""), "",
           "## 1. 비교한 실행", "", "| 변형 | 실행 ID | 읽기 사용/총예산 | 목차 | 걸린 시간 |", "|---|---|---|---|---|"]
    for v, t in runs.items():
        b = budget[v]
        out.append(f"| {config.VARIANT_LABELS[v]} | `{t['run_id']}` | {b['reads_used']}/{b['total_budget']} | "
                   f"{t.get('plan_source', 'new')} | {t.get('elapsed_sec', '?')}초 |")
    if "single" in budget:
        out += ["", f"> 대조군 예산 확인: {budget['single']['use']:.0%} — {budget['single']['verdict']}"]

    out += ["", "## 2. 경보 — 0이어야 한다", "", "| 경보 | 보는 장치 | " + " | ".join(labels) + " |",
            "|---|---|" + "---|" * len(runs)]
    for row in table:
        if row["kind"] == "alarm":
            vals = [fmt(row["key"], row["values"].get(v)) for v in runs]
            vals = [f"🚨 {x}" if x not in ("0", "—") else x for x in vals]
            out.append(f"| {row['label']} | {row['device']} | " + " | ".join(vals) + " |")

    out += ["", "## 3. 신호 — 괄호는 기본과의 차이", "", "| 신호 | 보는 장치 | " + " | ".join(labels) + " |",
            "|---|---|" + "---|" * len(runs)]
    for row in table:
        if row["kind"] == "signal":
            cells = []
            for v in runs:
                cell = fmt(row["key"], row["values"].get(v))
                d = row["delta_vs_full"].get(v)
                if d not in (None, 0):
                    cell += f" ({'+' if d > 0 else ''}{fmt(row['key'], d) if row['key'] not in ('budget_use', 'link_hop_share', 'read_uncited_share', 'year_grounding') else f'{d:+.0%}'})"
                cells.append(cell)
            out.append(f"| {row['label']} | {row['device']} | " + " | ".join(cells) + " |")

    out += ["", "## 4. 절별로 누가 얼마나 읽고 썼나", ""]
    for v, t in runs.items():
        out += [f"### {config.VARIANT_LABELS[v]}", "", "| 절 [역할] | 읽기 | 인용 문서 | 신고 흐름 | 두 번째 원고 처리 |",
                "|---|---|---|---|---|"] + section_rows(t) + [""]

    out += ["## 5. 인용 대조 표본 (원문과 직접 대조)", "",
            "인용 붙은 문장마다 인용 문서에서 단서(연도·숫자·영문 고유명사)가 가장 많이 겹치는 대목을 붙였다.",
            "읽은 문서를 엉뚱한 문장에 붙인 것은 코드가 못 잡는다. 아래에서 직접 판단해 [ ] 에 표시한다.", ""]
    for v, t in runs.items():
        out += [f"### {config.VARIANT_LABELS[v]}", ""]
        for i, r in enumerate(sample(check_report(t["report"]["markdown_d"], corpus), k=5), 1):
            out += [f"{i}. **문장**: {r['sentence']}",
                    f"   - 인용: `{r['doc']}` {r['title']} · 단서: {', '.join(r['clues'][:6]) or '없음'}",
                    f"   - 원문 대목: {r['snippet'] or '(자동으로 찾을 단서가 없음 — 문서를 직접 열어 확인)'}",
                    "   - 판단: [ ] 제자리  [ ] 엉뚱한 문장  [ ] 원문에 없음", ""]

    out += ["## 6. 내 판단 (직접 적기)", "",
            "보고서들을 나란히 읽은 뒤 자기 말로 적는다. 지표 표는 명백한 실패를 거르는 데만 쓴다.", "",
            "- 어느 쪽이 나은가:", "- 그렇게 판단한 이유(구체적인 대목을 들어):", "",
            "### 마음에 안 드는 대목 → 어디서 비롯됐나", "",
            "| 대목(인용) | 보고서 | 절 | 리서처 원고(v1/v2)에도 있었나 | 근거 문서 | 원인 추정(목차·탐색·원고·종합) |",
            "|---|---|---|---|---|---|", "|  |  |  |  |  |  |", "|  |  |  |  |  |  |", ""]
    return "\n".join(out)


def write_outputs(qid: str, runs: dict, corpus) -> None:
    table = build_table(runs)
    budget = budget_check(runs)
    data = {}
    if config.ABLATION_JSON.exists():
        data = json.loads(config.ABLATION_JSON.read_text(encoding="utf-8"))
    key = qid + ("_practice" if next(iter(runs.values()))["settings"].get("practice") else "")
    data[key] = {
        "question": next(iter(runs.values()))["question"],
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "runs": {v: t["run_id"] for v, t in runs.items()},
        "budget_check": budget,
        "alarms": {v: t["metrics"]["alarms_fired"] for v, t in runs.items()},
        "table": table,
    }
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    config.ABLATION_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    md_path = config.OUTPUT_DIR / f"ablation_{key}.md"
    md_path.write_text(build_markdown(qid, runs, table, budget, corpus), encoding="utf-8")
    print(f"\n표: {config.ABLATION_JSON}\n비교 문서: {md_path}")
    for row in table:
        if row["kind"] == "alarm" and any(row["values"].get(v) for v in runs):
            print(f"🚨 {row['label']}: " + ", ".join(f"{config.VARIANT_LABELS[v]}={row['values'][v]}" for v in runs if row["values"].get(v)))


def main() -> None:
    p = argparse.ArgumentParser(description="스위치를 하나씩 끄고 평가하는 실험")
    p.add_argument("--q")
    p.add_argument("--question")
    p.add_argument("--practice", action="store_true")
    p.add_argument("--only", help="쉼표로 고른 변형만 (예: full,single)")
    p.add_argument("--table-only", action="store_true", help="실행 없이 기존 실행으로 표만 만든다")
    p.add_argument("--corpus")
    args = p.parse_args()
    if not (args.q or args.question):
        sys.exit("질문을 고르세요: python ablation.py --q Q4")
    qid, question = resolve_question(args.q, args.question)
    try:
        corpus = Corpus.load(args.corpus) if args.corpus else Corpus.load()
    except CorpusMissing as exc:
        sys.exit(str(exc))

    if not args.table_only:
        variants = [v for v in ORDER if not args.only or v in args.only.split(",")]
        for v in variants:
            print(f"\n▶ {qid} · {config.VARIANT_LABELS[v]}")
            if v == "single":
                t = run_baseline(question, qid, practice=args.practice, corpus=corpus, progress=print)
            else:
                settings = config.make_settings(v, practice=args.practice)
                t = run_question(question, qid, settings, corpus=corpus, progress=print)
            print(f"   → 읽기 {t['metrics']['raw']['reads_used']}/{t['metrics']['raw']['total_budget']}, "
                  f"경보 {t['metrics']['alarms_fired'] or '없음'}")

    runs = latest_traces(qid, args.practice)
    if len(runs) < 2:
        sys.exit("비교하려면 실행이 2편 이상 필요합니다.")
    write_outputs(qid, runs, corpus)


if __name__ == "__main__":
    main()
