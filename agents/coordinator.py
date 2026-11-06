"""코디네이터: 목차를 짜고(코드가 검사), 신고를 보고 재파견할 절을 고르고, 두 번째 원고를 병합하고, 이어 붙인다.

코디네이터는 자료 본문을 읽지 않는다. 보는 것은 자료 목록(제목·첫 문장), 리서처의 원고와 신고뿐이다.
"""
import json
import re

import config

from . import fake, prompts
from .cite import paragraphs, unique_ids
from .llm import Conversation, LLMResult

def _strip_prefix(doc_id: str) -> str:
    return doc_id[2:] if doc_id.startswith("d:") else doc_id


FORMAT_TITLE_RE = re.compile(r"(서론|본론|결론|개요|요약|배경|전망|맺음말|introduction|conclusion|overview|summary|background)", re.I)


class Coordinator:
    role = "coordinator"

    def __init__(self, question: str, corpus, settings, llm, trace):
        self.question = question
        self.corpus = corpus
        self.settings = settings
        self.llm = llm
        self.trace = trace
        self.conv = Conversation("코디네이터", self.role)
        self.plan_attempts = []   # [{attempt, plan, errors, warnings}]
        self._mode = None

    # ------------------------------------------------------------ 목차
    def plan(self, max_attempts: int = 3) -> dict:
        s = self.settings
        self.conv.add_input("system", plan_system_text(s))
        self.conv.add_input("user", prompts.PLAN_USER.format(
            question=self.question, doc_count=len(self.corpus.ids()), catalog=self.corpus.catalog_text(s.page_chars)))
        self._mode = "plan"
        for attempt in range(1, max_attempts + 1):
            result = self.llm.chat(self.conv, json_schema=prompts.plan_schema(config.ROLE_NAMES), agent=self,
                                   max_tokens=12_000)
            self.conv.add_assistant(result)
            try:
                raw = json.loads(result.content)
            except json.JSONDecodeError:
                raw = {"rationale": "", "sections": []}
            plan = self._normalize(raw)
            errors, warnings = validate_plan(plan, self.corpus, self.settings)
            self.plan_attempts.append({"attempt": attempt, "plan": plan, "errors": errors, "warnings": warnings})
            self.trace.log("코디네이터", f"목차 시도 {attempt}: 절 {len(plan['sections'])}개, 오류 {len(errors)}건, 경고 {len(warnings)}건")
            if not errors:
                plan["warnings"] = warnings
                return plan
            self.conv.add_input("user", prompts.PLAN_RETRY.format(errors="\n".join(f"- {e}" for e in errors)))
        raise RuntimeError("코디네이터가 코드 검사를 통과하는 목차를 만들지 못했습니다:\n" + "\n".join(errors))

    @staticmethod
    def _normalize(raw: dict) -> dict:
        sections = []
        for i, sec in enumerate(raw.get("sections", []), 1):
            sections.append({
                "id": f"S{i}",
                "role_name": str(sec.get("role_name", "")).strip(),
                "title": str(sec.get("title", "")).strip(),
                "role": str(sec.get("role", "")).strip(),
                "scope_in": str(sec.get("scope_in", "")).strip(),
                "scope_out": str(sec.get("scope_out", "")).strip(),
                "start_docs": [_strip_prefix(str(d).strip()) for d in sec.get("start_docs", [])],
                "budget": int(sec.get("budget", 0) or 0),
            })
        return {"rationale": str(raw.get("rationale", "")), "sections": sections}

    # ------------------------------------------------------------ 점검
    @staticmethod
    def pick_recheck(latest: dict) -> list:
        """스스로 '부족'이라 신고한 절만 고른다."""
        return [sid for sid, d in latest.items() if d.get("status") == "insufficient"]

    @staticmethod
    def handoffs_for(sid: str, latest: dict) -> list:
        out = []
        for other, d in latest.items():
            if other == sid:
                continue
            for h in d.get("handoffs", []):
                if str(h.get("section_id", "")).strip() == sid:
                    out.append({"from": other, **h})
        return out

    # ------------------------------------------------------------ 종합
    def synthesize(self, sections: list, finals: dict) -> dict:
        self._mode = "synth"
        self._synth_sections = sections
        body = "\n\n".join(f"### {s['id']}. {s['title']}\n{finals[s['id']]['markdown']}" for s in sections
                           if finals.get(s["id"], {}).get("markdown"))
        self.conv.add_input("system", prompts.SYNTH_SYSTEM)
        self.conv.add_input("user", prompts.SYNTH_USER.format(question=self.question, sections=body))
        result = self.llm.chat(self.conv, json_schema=prompts.SYNTH_SCHEMA, agent=self, max_tokens=8_000)
        self.conv.add_assistant(result)
        try:
            frame = json.loads(result.content)
        except json.JSONDecodeError:
            frame = {"title": self.question, "intro": "", "transitions": [], "conclusion": ""}
        self.trace.log("코디네이터", "종합: 서론·연결 문장·맺음말 작성")
        return frame

    def meter(self) -> dict:
        return self.conv.meter()

    def fake_reply(self, conv, tools=None, tool_choice=None, json_schema=None) -> LLMResult:
        if self._mode == "plan":
            return LLMResult(content=json.dumps(fake.plan(self), ensure_ascii=False))
        return LLMResult(content=json.dumps(fake.synth(self), ensure_ascii=False))


def validate_plan(plan: dict, corpus, settings) -> tuple:
    """모델이 낸 목차를 코드로 검사한다. 모델은 그럴듯한 문서 ID와 제목을 지어내기 때문이다."""
    errors, warnings = [], []
    secs = plan["sections"]
    if not secs:
        return ["절이 하나도 없다."], warnings
    if len(secs) > settings.max_sections:
        errors.append(f"절이 {len(secs)}개다. 최대 {settings.max_sections}개.")
    if len(secs) < settings.min_sections:
        errors.append(f"절이 {len(secs)}개다. 최소 {settings.min_sections}개.")
    roles_used = [s.get("role_name", "") for s in secs]
    for r in sorted(set(roles_used)):
        if r and r not in config.ROLE_NAMES:
            errors.append(f"역할 '{r}' 은 역할 명단에 없다. 명단: {', '.join(config.ROLE_NAMES)}")
        elif roles_used.count(r) > 1:
            warnings.append(f"역할 '{r}' 을 {roles_used.count(r)}개 절이 함께 쓴다(시기로 나눴다면 괜찮다).")
    if "단일 사실 확인" in roles_used and len(secs) > 1:
        errors.append("'단일 사실 확인' 역할은 절이 하나일 때만 쓴다.")
    total = 0
    for s in secs:
        label = f"{s['id']}({s['title'] or '제목 없음'})"
        if not s["title"] or not s["role"]:
            errors.append(f"{label}: 제목과 역할 질문이 있어야 한다.")
        if not s.get("role_name"):
            errors.append(f"{label}: 역할 명단에서 역할(role_name)을 골라야 한다.")
        if FORMAT_TITLE_RE.search(s["title"]):
            errors.append(f"{label}: '{s['title']}' 은 형식 단위 제목이다. 내용(시기·주제·대상) 단위로 나눠라.")
        if not s["start_docs"]:
            errors.append(f"{label}: 시작 자료가 없다.")
        if len(s["start_docs"]) > 4:
            errors.append(f"{label}: 시작 자료가 {len(s['start_docs'])}건이다. 최대 4건.")
        bad = [d for d in s["start_docs"] if not corpus.exists(d)]
        if bad:
            errors.append(f"{label}: 자료 목록에 없는 문서 ID {bad}. 목록에 있는 ID 그대로 써라.")
        dis = [d for d in s["start_docs"] if corpus.exists(d) and corpus.is_disambiguation(d)]
        if dis:
            errors.append(f"{label}: {dis} 은 동음이의(이름 목록) 문서라 내용이 없다. 실제 내용 문서를 시작 자료로 골라라.")
        if len(set(s["start_docs"])) != len(s["start_docs"]):
            warnings.append(f"{label}: 같은 시작 자료를 두 번 적었다.")
        if s["budget"] < settings.min_section_budget:
            errors.append(f"{label}: 예산 {s['budget']}회는 최소 {settings.min_section_budget}회보다 적다.")
        if s["budget"] < len(set(s["start_docs"])):
            errors.append(f"{label}: 예산 {s['budget']}회로는 시작 자료 {len(s['start_docs'])}건을 다 읽을 수 없다.")
        total += max(s["budget"], 0)
    if total > settings.section_pool:
        errors.append(f"예산 합계 {total}회가 한도 {settings.section_pool}회를 넘는다.")
    # 절끼리 시작 자료가 겹치면 형식 단위로 나눈 신호다
    for i, a in enumerate(secs):
        for b in secs[i + 1:]:
            A, B = set(a["start_docs"]), set(b["start_docs"])
            if A and B:
                jac = len(A & B) / len(A | B)
                if jac >= 0.5:
                    errors.append(f"{a['id']}와 {b['id']}의 시작 자료가 {jac:.0%} 겹친다. 내용 단위로 다시 나눠라.")
                elif A & B:
                    warnings.append(f"{a['id']}와 {b['id']}가 시작 자료 {sorted(A & B)}를 함께 쓴다.")
    return errors, warnings


def merge_drafts(prev: dict, new: dict) -> tuple:
    """두 번째 원고 처리 규칙.

    - 새 원고가 이전 원고의 인용 문서를 하나도 잃지 않았고, 읽지 않은 문서 인용이 늘지 않았으면 → 새 원고로 교체.
    - 아니면 → 이전 원고를 지키고, 새 원고에서 '이전에 없던 문서를 인용한 문단'만 뒤에 덧붙인다.
    이유: 무조건 덮어쓰면 인용을 빠뜨린 원고가 멀쩡한 원고를 지운다.
    """
    if new.get("status") == "failed" or not new.get("markdown"):
        return dict(prev), "유지", "두 번째 원고가 비었거나 제출 실패 → 이전 원고 유지"
    lost = [d for d in prev["cited"] if d not in new["cited"]]
    more_unread = len(new.get("unread_cited", [])) > len(prev.get("unread_cited", []))
    if not lost and not more_unread:
        return dict(new), "교체", f"이전 인용 {len(prev['cited'])}건을 모두 유지하고 {len(set(new['cited']) - set(prev['cited']))}건을 더함 → 교체"
    old_ids = set(prev["cited"])
    added = [p for p in paragraphs(new["markdown"]) if set(unique_ids(p)) - old_ids]
    merged = dict(prev)
    if added:
        merged["markdown"] = prev["markdown"].rstrip() + "\n\n" + "\n\n".join(added)
    merged["cited"] = unique_ids(merged["markdown"])
    merged["unread_cited"] = sorted(set(prev.get("unread_cited", [])) |
                                    {d for p in added for d in unique_ids(p) if d in set(new.get("unread_cited", []))})
    merged["unknown_cited"] = sorted(set(prev.get("unknown_cited", [])) |
                                     {d for p in added for d in unique_ids(p) if d in set(new.get("unknown_cited", []))})
    merged["status"] = new.get("status", prev.get("status"))
    merged["missing"] = new.get("missing", "")
    merged["handoffs"] = new.get("handoffs", [])
    merged["chars"] = len(merged["markdown"])
    merged["round"] = new.get("round")
    reason = (f"두 번째 원고가 이전 인용 {len(lost)}건({', '.join(lost[:4])})을 잃음" if lost else "읽지 않은 문서 인용이 늘어남")
    return merged, "보강", reason + f" → 이전 원고 유지 + 새 문단 {len(added)}개 덧붙임"


def plan_system_text(settings) -> str:
    roles = "\n".join(f"- {r['name']}: {r['focus']}" for r in config.ROLES)
    return prompts.PLAN_SYSTEM.format(
        roles=roles, page_chars=settings.page_chars, min_budget=settings.min_section_budget,
        pool=settings.section_pool, min_sections=settings.min_sections, max_sections=settings.max_sections)
