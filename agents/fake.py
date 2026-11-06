"""연습 모드의 가짜 모델. API 없이 흐름(배정 → 읽기 → 제출 → 재파견 → 병합 → 종합)이 도는지 확인하는 용도다.

원고는 읽은 문서의 첫 문장을 이어 붙인 것일 뿐, 실제 모델이 쓴 글이 아니다.
"""
import re

import config

from .llm import LLMResult, ToolCall

PRACTICE_NOTE = "(연습 모드 원고 — 실제 모델이 쓴 글이 아닙니다.)"

# 질문 속 한국어 낱말 → 문서 ID 에 들어 있을 영어 조각
KEYWORDS = {
    "크로스핏": ["crossfit"], "게임즈": ["games"], "투미": ["toomey"], "하이록스": ["hyrox"],
    "리복": ["reebok"], "머프": ["murphy"], "비판": ["rhabdo", "strength_and_conditioning"],
    "논쟁": ["rhabdo", "jillian"], "영양": ["diet", "paleo", "zone"], "방법론": ["interval", "circuit", "functional"],
    "f45": ["f45"], "오렌지": ["orangetheory"], "설립": ["glassman"], "역도": ["weightlifting"],
    "예선": ["games"], "선수": ["froning", "fraser", "toomey"],
}
_counter = {"n": 0}


def _call(name: str, args: dict) -> LLMResult:
    _counter["n"] += 1
    return LLMResult(tool_calls=[ToolCall(id=f"fake_{_counter['n']}", name=name, arguments=args)])


def _keywords(question: str) -> list:
    q = question.lower()
    out = []
    for ko, parts in KEYWORDS.items():
        if ko in q:
            out += parts
    return out or ["crossfit"]


def _score(doc_id: str, keys: list) -> int:
    return sum(k in doc_id for k in keys)


def _lead(text: str, limit: int = 220) -> str:
    text = re.sub(r"==+[^=]+==+", " ", text)
    text = " ".join(text.split())
    cut = text[:limit]
    dot = cut.rfind(". ")
    return (cut[:dot + 1] if dot > 60 else cut).strip()


# ---------------------------------------------------------------- 코디네이터
def plan(coord) -> dict:
    c, s = coord.corpus, coord.settings
    keys = _keywords(coord.question)
    ranked = sorted((d for d in c.ids() if not c.is_disambiguation(d)), key=lambda d: (-_score(d, keys), -c.in_degree(d)))
    single_hint = any(w in coord.question for w in ("누가", "이름", "어떤 종목"))
    pool = s.section_pool
    n_sec = 1 if single_hint else min(4, s.max_sections, max(1, len(ranked) // 3))
    n_sec = max(1, min(n_sec, pool // max(s.min_section_budget, 2)))
    sections = []
    for i in range(n_sec):
        docs = ranked[i * 2:i * 2 + 2] or ranked[:1]
        budget = max(s.min_section_budget, len(docs), pool // n_sec)
        roles = [r for r in config.ROLE_NAMES if r != "단일 사실 확인"]
        sections.append({
            "role_name": "단일 사실 확인" if n_sec == 1 else roles[i % len(roles)],
            "title": f"{c.title(docs[0])} 갈래", "role": f"질문 중 '{c.title(docs[0])}' 쪽에서 답할 수 있는 것은?",
            "scope_in": ", ".join(c.title(d) for d in docs), "scope_out": "다른 절의 시작 자료가 다루는 내용",
            "start_docs": docs, "budget": budget,
        })
    over = sum(x["budget"] for x in sections) - pool
    while over > 0:
        reduced = False
        for x in sections:
            if over > 0 and x["budget"] > max(s.min_section_budget, len(x["start_docs"])):
                x["budget"] -= 1
                over -= 1
                reduced = True
        if not reduced:
            break
    return {"rationale": "연습 모드: 질문 낱말과 많이 링크된 문서 순으로 시작 자료를 골라 나눴다.", "sections": sections}


def synth(coord) -> dict:
    secs = coord._synth_sections
    return {
        "title": f"{coord.question} (연습 모드)",
        "intro": f"{PRACTICE_NOTE} 이 보고서는 '{coord.question}'에 답하기 위해 {len(secs)}개 절로 나눠 조사했다.",
        "transitions": [{"section_id": x["id"], "sentence": f"이어서 {x['title']}를 본다."} for x in secs],
        "conclusion": f"{PRACTICE_NOTE} 각 절의 원고를 이어 붙였다. 실제 결론은 GPT로 실행해야 나온다.",
    }


# ---------------------------------------------------------------- 리서처
def _next_doc(state, keys, prefer=None):
    unread_start = [d for d, via in state.frontier.items() if via == "start" and d not in state.parts_read]
    if prefer:
        unread_start = [d for d in unread_start if d in prefer] or unread_start
    if unread_start:
        return unread_start[0]
    pool = state.frontier if state.use_links else state.corpus.ids()
    cand = [d for d in pool if d not in state.parts_read]
    if not cand:
        return None
    return sorted(cand, key=lambda d: (-_score(d, keys), -state.corpus.in_degree(d), d))[0]


def _next_read(state, keys):
    """다음에 읽을 (문서, 쪽). 새 문서가 없으면 이미 연 문서의 다음 쪽."""
    doc = _next_doc(state, keys)
    if doc:
        return doc, 1
    for d, parts in state.parts_read.items():
        total = state.corpus.parts(d, state.page_chars)
        nxt = next((p for p in range(1, total + 1) if p not in parts), None)
        if nxt:
            return d, nxt
    return None, None


def _compose(state, docs: list) -> str:
    paras = [f"{_lead(state.corpus.text(d))} [d:{d}]" for d in docs]
    return PRACTICE_NOTE + "\n\n" + "\n\n".join(paras)


def researcher_step(agent, tool_choice) -> LLMResult:
    st = agent.state
    keys = _keywords(agent.question)
    forced = isinstance(tool_choice, dict)
    if not forced and st.left > 0:
        doc, part = _next_read(st, keys)
        if doc:
            return _call("read_doc", {"doc_id": doc, "part": part})
    docs = st.docs_read() or agent.section["start_docs"][:1]
    round_no = agent.round_no
    if round_no >= 2 and agent.index % 4 == 3 and len(docs) > 2:
        docs = docs[1:]  # 일부러 이전 인용 하나를 빠뜨려 '보강' 병합 규칙을 시험한다
    insufficient = round_no == 1 and agent.index % 2 == 1
    others = {d: p["id"] for p in agent.all_sections if p["id"] != agent.section["id"] for d in p["start_docs"]}
    handoffs = [{"section_id": others[d], "note": f"{st.corpus.title(d)} 문서에 그 절에 필요한 내용이 있다.", "doc_id": d}
                for d in docs if d in others][:2]
    return _call("submit_section", {
        "markdown": _compose(st, docs),
        "status": "insufficient" if insufficient else "sufficient",
        "missing": "연습 모드: 링크를 더 따라가야 한다." if insufficient else "",
        "handoffs": handoffs,
    })


# ---------------------------------------------------------------- 단일 에이전트
def single_step(agent) -> LLMResult:
    st = agent.state
    keys = _keywords(agent.question)
    if st.left > 0:
        doc, part = _next_read(st, keys)
        if doc:
            return _call("read_doc", {"doc_id": doc, "part": part})
    for sec in agent.sections:
        if sec["id"] not in agent.drafts:
            mine = [d for d in st.docs_read() if d in sec["start_docs"] or st.frontier.get(d) in sec["start_docs"]]
            return _call("submit_section", {"section_id": sec["id"], "markdown": _compose(st, mine or st.docs_read()[:2]),
                                            "status": "sufficient", "missing": "", "handoffs": []})
    return _call("finish", {})
