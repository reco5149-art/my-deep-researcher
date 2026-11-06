"""지표 — 정답표도 판정 모델도 쓰지 않는다.

재료는 두 가지뿐이다: 만들어진 글(보고서·절 원고)과 실제로 읽은 자료(읽기 기록).
- 신호(signal): 높낮이를 견주는 값. 순위표가 아니라 '어디를 고칠지' 가리키는 손가락이다.
- 경보(alarm): 0이어야 하는 값. 0이 아니면 그 장치가 고장 난 것이다.
지표마다 어느 장치를 보는지 적어 두었다. 설명이 한 줄로 안 되는 지표는 넣지 않았다.
"""
from itertools import combinations

from agents.cite import YEAR_RE, cited_sentences, extract_ids, unique_ids

DEFS = [
    # key, 이름, 종류, 보는 장치, 한 줄 설명
    ("budget_use", "예산 소진율", "signal", "예산 배분 · 대조군 공정성", "전체 읽기 예산 중 실제로 읽은 비율"),
    ("unique_docs_read", "읽은 문서 수", "signal", "탐색 (시작 자료·links)", "한 번 이상 연 서로 다른 문서 수"),
    ("link_hop_share", "시작 자료 밖 탐색 비율", "signal", "탐색 (links)", "읽은 문서 중 시작 자료가 아니라 링크를 따라가(OFF면 검색해) 연 문서의 비율"),
    ("read_overlap", "절 간 읽기 겹침", "signal", "남의 구역 알림 · 목차 분할", "절끼리 읽은 문서 집합이 겹치는 정도(쌍별 자카드 평균, 낮을수록 잘 갈림)"),
    ("cited_docs", "인용된 문서 수", "signal", "원고 규칙 (리서처)", "최종 보고서에 인용된 서로 다른 문서 수"),
    ("cite_density", "인용 밀도", "signal", "원고 규칙 (리서처)", "본문 1,000자당 인용 표시 수"),
    ("read_uncited_share", "읽고 안 쓴 비율", "signal", "예산 효율", "읽었지만 어디에도 인용하지 않은 문서의 비율"),
    ("year_grounding", "연도 원문 일치율", "signal", "원문 대조 (리서처 정확성)", "인용 붙은 문장의 연도 중 인용 문서 원문에 실제로 나오는 비율"),
    ("coordinator_seen_ratio", "코디네이터가 본 비율", "signal", "격리 (분업 구조)", "코디네이터가 받은 글자 수 ÷ 자료 전체 글자 수"),
    ("max_agent_seen_ratio", "최대 에이전트가 본 비율", "signal", "격리 (분업 구조)", "가장 많이 받은 에이전트의 글자 수 ÷ 자료 전체 글자 수"),
    ("insufficient_first", "1차 부족 신고", "signal", "점검·재파견", "1차 원고에서 스스로 '부족'이라 신고한 절 수"),
    ("resolved_after_recheck", "재파견 후 해결", "signal", "점검·재파견", "재파견 뒤 '충분'으로 바뀐 절 수"),
    ("plan_retries", "목차 재작성", "signal", "목차 검사 (코드)", "코디네이터 목차가 코드 검사에 걸려 다시 짠 횟수"),
    ("submit_rejections", "제출 거절", "signal", "원고 검사 (코드)", "인용 없음·안 읽은 문서 인용 등으로 코드가 제출을 돌려보낸 횟수"),
    ("gate_rejections", "예산 관문 반려", "signal", "제출 관문 (코드)", "예산을 덜 쓰고 제출·종료하려다 코드가 돌려보낸 횟수"),
    # ---- 경보: 0이어야 한다 ----
    ("unread_citations", "안 읽은 문서 인용", "alarm", "원고 규칙 (리서처)", "쓴 에이전트가 읽지 않은 문서를 인용한 수"),
    ("unknown_ids", "없는 문서 ID", "alarm", "목차 검사 · 원고 검사", "최종 목차·보고서에 자료에 없는 문서 ID가 남은 수"),
    ("budget_overrun", "예산 초과", "alarm", "예산 장치", "배정 예산보다 많이 읽은 횟수"),
    ("lost_citations", "종합 중 잃은 인용", "alarm", "종합 (코디네이터)", "절 원고에 있던 인용 문서가 최종본에서 사라진 수"),
    ("synthesis_new_citations", "종합이 만든 새 인용", "alarm", "종합 (코디네이터)", "맺음말이 어느 절 원고에도 없던 문서를 인용한 수"),
    ("empty_sections", "빈 절", "alarm", "리서처 · 점검", "인용이 하나도 없거나 제출에 실패한 절 수"),
    ("control_underuse", "대조군 예산 미소진", "alarm", "비교 공정성", "대조군이 예산의 90% 미만을 쓰고 멈췄으면 1 (상대를 묶어 둔 비교)"),
]
DEF_BY_KEY = {d[0]: d for d in DEFS}


def _jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if (a or b) else 0.0


def collect_reads(trace: dict) -> dict:
    """에이전트별 읽기 기록 {에이전트 이름: reads dict}."""
    if trace.get("variant") == "single":
        return {"단일 에이전트": trace["single"]["reads"]}
    return {f"리서처 {sid}": sec["reads"] for sid, sec in trace["sections"].items()}


def compute(trace: dict, corpus) -> dict:
    variant = trace.get("variant")
    single = variant == "single"
    sections = trace["plan"]["sections"]
    report_d = trace["report"]["markdown_d"]
    finals = {sid: sec.get("final", {}) for sid, sec in trace["sections"].items()}
    reads = collect_reads(trace)
    total_budget = trace["settings"]["total_reads"]

    used = sum(r["used"] for r in reads.values())
    docs_read = set()
    per_agent_docs = per_agent_hops = 0   # 에이전트마다 '시작 자료가 아닌데 링크로 찾아 연 문서'를 센다
    for r in reads.values():
        via = {}
        for e in r["log"]:
            docs_read.add(e["doc"])
            via.setdefault(e["doc"], e["via"])
        per_agent_docs += len(via)
        per_agent_hops += sum(1 for v in via.values() if v != "start")

    cited = set(unique_ids(report_d))
    known_cited = {d for d in cited if corpus.exists(d)}

    # 연도 원문 일치율
    years_total = years_found = 0
    for sentence, ids in cited_sentences(report_d):
        texts = [corpus.text(d) for d in ids if corpus.exists(d)]
        for y in set(YEAR_RE.findall(sentence)):
            years_total += 1
            years_found += any(y in t for t in texts)

    # 절 간 읽기 겹침 (분업일 때만)
    overlap = None
    if not single and len(reads) >= 2:
        sets = [set(r["docs_read"]) for r in reads.values()]
        pairs = list(combinations(sets, 2))
        overlap = round(sum(_jaccard(a, b) for a, b in pairs) / len(pairs), 3)

    # 격리: 받은 글자 수
    meters = trace.get("meters", {})
    corpus_chars = max(corpus.total_chars, 1)
    coord_seen = meters.get("코디네이터", {}).get("seen_chars", 0)
    agent_seen = {k: v.get("seen_chars", 0) for k, v in meters.items() if k != "코디네이터"}

    # 점검
    insufficient_first = resolved = None
    if not single:
        firsts = {sid: (sec.get("drafts") or [{}])[0] for sid, sec in trace["sections"].items()}
        insufficient_first = sum(1 for d in firsts.values() if d.get("status") == "insufficient")
        resolved = sum(1 for sid, d in firsts.items()
                       if d.get("status") == "insufficient" and finals[sid].get("status") == "sufficient")

    # ---- 경보 ----
    unread = 0
    if single:
        read_set = set(trace["single"]["reads"]["docs_read"])
        unread = sum(1 for sid, f in finals.items() for d in f.get("cited", []) if corpus.exists(d) and d not in read_set)
    else:
        for sid, f in finals.items():
            read_set = set(trace["sections"][sid]["reads"]["docs_read"])
            unread += sum(1 for d in f.get("cited", []) if corpus.exists(d) and d not in read_set)
    unknown = len({d for d in cited if not corpus.exists(d)}) + sum(
        1 for s in sections for d in s["start_docs"] if not corpus.exists(d))
    overrun = sum(max(0, r["used"] - r["budget"]) for r in reads.values())
    section_cited = {d for f in finals.values() for d in unique_ids(f.get("markdown", ""))}
    lost = len(section_cited - cited)
    concl_cited = set(unique_ids(trace["report"].get("conclusion_d", "")))
    synth_new = len(concl_cited - section_cited)
    empty = sum(1 for s in sections if not unique_ids(finals.get(s["id"], {}).get("markdown", "")))
    underuse = None
    if single:
        underuse = 1 if used < 0.9 * total_budget else 0

    plan_attempts = trace.get("plan_attempts", [])
    values = {
        "budget_use": round(used / total_budget, 3) if total_budget else None,
        "unique_docs_read": len(docs_read),
        "link_hop_share": round(per_agent_hops / per_agent_docs, 3) if per_agent_docs else None,
        "read_overlap": overlap,
        "cited_docs": len(known_cited),
        "cite_density": round(len(extract_ids(report_d)) / max(len(report_d), 1) * 1000, 2),
        "read_uncited_share": round(len(docs_read - cited) / len(docs_read), 3) if docs_read else None,
        "year_grounding": round(years_found / years_total, 3) if years_total else None,
        "coordinator_seen_ratio": round(coord_seen / corpus_chars, 4),
        "max_agent_seen_ratio": round(max(agent_seen.values()) / corpus_chars, 4) if agent_seen else None,
        "insufficient_first": insufficient_first,
        "resolved_after_recheck": resolved,
        "plan_retries": max(0, len(plan_attempts) - 1) if plan_attempts else 0,
        "submit_rejections": trace.get("submit_rejections", 0),
        "gate_rejections": trace.get("gate_rejections", 0),
        "unread_citations": unread,
        "unknown_ids": unknown,
        "budget_overrun": overrun,
        "lost_citations": lost,
        "synthesis_new_citations": synth_new,
        "empty_sections": empty,
        "control_underuse": underuse,
    }
    rows = []
    for key, label, kind, device, desc in DEFS:
        rows.append({"key": key, "label": label, "kind": kind, "device": device, "desc": desc, "value": values[key]})
    return {
        "rows": rows,
        "values": values,
        "raw": {
            "reads_used": used, "total_budget": total_budget, "corpus_chars": corpus.total_chars,
            "coordinator_seen_chars": coord_seen, "agent_seen_chars": agent_seen,
            "years_checked": years_total, "years_found": years_found,
        },
        "alarms_fired": [r["key"] for r in rows if r["kind"] == "alarm" and r["value"]],
    }


def fmt(key: str, value) -> str:
    if value is None:
        return "—"
    if key in ("budget_use", "link_hop_share", "read_uncited_share", "year_grounding"):
        return f"{value:.0%}"
    if key in ("coordinator_seen_ratio", "max_agent_seen_ratio"):
        return f"{value:.2%}"
    if key == "read_overlap":
        return f"{value:.2f}"
    return str(value)
