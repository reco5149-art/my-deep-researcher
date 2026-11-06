"""리서처 에이전트(절 하나 담당)와 단일 에이전트 대조군(모든 절 담당).

둘 다 같은 도구와 같은 읽기 규칙을 쓴다.
- links 탐색 ON: 열 수 있는 문서 = 시작 자료 + 이미 읽은 문서가 링크하는 문서
- links 탐색 OFF(비교 실험): 아무 문서나 열 수 있고, 문서 ID는 제목 검색(find_docs)으로 찾는다
- read_doc 1회 = 예산 1회. 예산을 넘는 읽기는 코드가 막는다.
- 예산을 너무 적게 쓰고 제출(끝)하려 하면 코드가 안 읽은 자료 목록을 보여 주며 돌려보낸다(관문).
"""
import config

from . import fake, prompts
from .cite import unique_ids
from .llm import Conversation, LLMResult

FORCE_SUBMIT = {"type": "function", "function": {"name": "submit_section"}}


class ReadState:
    """누가 무엇을 어디서(어떤 링크를 따라) 읽었는지 기록한다."""

    def __init__(self, corpus, start_docs: list, budget: int, page_chars: int, use_links: bool = True):
        self.corpus = corpus
        self.page_chars = page_chars
        self.budget = budget
        self.used = 0
        self.use_links = use_links
        self.start_docs = [d for d in start_docs if corpus.exists(d)]
        self.frontier = {d: "start" for d in self.start_docs}
        self.parts_read = {}   # doc -> set(part)
        self.log = []          # [{n, doc, part, via, round, chars}]
        self.blocked = []      # 열 수 없는 문서를 열려 한 기록
        self.unknown = []      # 자료에 없는 ID 를 열려 한 기록
        self.over_budget = 0   # 예산을 넘겨 읽으려 한 횟수(코드가 막음)

    @property
    def left(self) -> int:
        return self.budget - self.used

    def docs_read(self) -> list:
        return list(self.parts_read)

    def can_open(self, doc_id: str) -> bool:
        return doc_id in self.frontier or not self.use_links

    def read(self, doc_id: str, part: int, round_no: int) -> str:
        c = self.corpus
        if not c.exists(doc_id):
            self.unknown.append(doc_id)
            return f"오류: '{doc_id}' 는 자료에 없는 문서 ID다. 시작 자료나 목록에 나온 ID만 쓸 수 있다."
        if not self.can_open(doc_id):
            self.blocked.append(doc_id)
            return (f"오류: '{doc_id}' 는 아직 열 수 없다. 시작 자료이거나, 네가 이미 읽은 문서가 링크하는 문서만 열 수 있다. "
                    "list_links 로 열 수 있는 문서를 확인하라.")
        if self.left <= 0:
            self.over_budget += 1
            return "오류: 읽기 예산을 다 썼다. 지금까지 읽은 것으로 제출하라."
        total = c.parts(doc_id, self.page_chars)
        part = min(max(int(part or 1), 1), total)
        text = c.page(doc_id, part, self.page_chars)
        first_time = doc_id not in self.parts_read
        self.parts_read.setdefault(doc_id, set()).add(part)
        self.used += 1
        via = self.frontier.get(doc_id, "search")
        self.log.append({"n": self.used, "doc": doc_id, "part": part, "parts": total,
                         "via": via, "round": round_no, "chars": len(text)})
        if first_time and self.use_links:
            for t in c.links(doc_id):
                self.frontier.setdefault(t, doc_id)
        footer = ""
        if self.use_links:
            links = c.links(doc_id)
            shown = ", ".join(f"{t}({c.title(t)})" for t in links[:25])
            more = f" 외 {len(links) - 25}건(list_links 로 전체 확인)" if len(links) > 25 else ""
            footer = f"\n\n이 문서가 링크하는 문서(이제 열 수 있음): {shown or '없음'}{more}"
        return f"[d:{doc_id}] {c.title(doc_id)} — {part}/{total}쪽 (남은 예산 {self.left}회)\n\n{text}{footer}"

    def list_links(self, doc_id: str) -> str:
        c = self.corpus
        if doc_id not in self.parts_read:
            return f"오류: '{doc_id}' 는 아직 읽지 않았다. 읽은 문서의 링크만 볼 수 있다."
        rows = [f"- {t} | {c.title(t)} | {c.parts(t, self.page_chars)}쪽" + (" | 읽음" if t in self.parts_read else "")
                for t in c.links(doc_id)]
        return f"[d:{doc_id}] 이 링크하는 문서 {len(rows)}건\n" + ("\n".join(rows) or "없음")

    def find_docs(self, keyword: str) -> str:
        c, kw = self.corpus, (keyword or "").lower().strip()
        if not kw:
            return "오류: 낱말을 넣어라."
        hits = [d for d in c.ids() if kw in c.title(d).lower() or kw in d][:20]
        rows = [f"- {d} | {c.title(d)} | {c.parts(d, self.page_chars)}쪽" + (" | 읽음" if d in self.parts_read else "")
                for d in hits]
        return f"'{keyword}' 제목 검색 {len(rows)}건\n" + ("\n".join(rows) or "없음")

    # ---- 관문에 쓸 '아직 안 읽은 것' 목록 ----
    def unread_starts(self, starts: list = None) -> list:
        return [d for d in (starts if starts is not None else self.start_docs)
                if self.corpus.exists(d) and d not in self.parts_read]

    def link_candidates(self, limit: int = 8) -> list:
        if not self.use_links:
            return []
        cand = [d for d, via in self.frontier.items() if via != "start" and d not in self.parts_read]
        return sorted(cand, key=lambda d: -self.corpus.in_degree(d))[:limit]

    def to_dict(self) -> dict:
        return {"budget": self.budget, "used": self.used, "log": self.log, "start_docs": self.start_docs,
                "docs_read": self.docs_read(), "blocked": self.blocked, "unknown": self.unknown,
                "over_budget": self.over_budget}


def _describe_unread(state: ReadState, starts: list = None) -> tuple:
    c = state.corpus
    us = state.unread_starts(starts)
    lc = state.link_candidates()
    unread = ("아직 안 읽은 시작 자료: " + ", ".join(f"{d}({c.title(d)})" for d in us) + "\n") if us else ""
    cands = ("링크로 열 수 있는 문서 예: " + ", ".join(f"{d}({c.title(d)})" for d in lc) + "\n") if lc else ""
    return unread, cands, bool(us or lc or not state.use_links)


class AgentBase:
    role = "agent"

    def __init__(self, name: str, question: str, corpus, settings, llm, trace):
        self.name = name
        self.question = question
        self.corpus = corpus
        self.settings = settings
        self.llm = llm
        self.trace = trace
        self.conv = Conversation(name, self.role)
        self.state = None
        self.submit_rejections = 0
        self.gate_rejections = 0
        self.unread_warned = False

    @property
    def tools(self) -> list:
        explore = prompts.TOOL_LINKS if self.settings.use_links else prompts.TOOL_FIND
        return [prompts.TOOL_READ, explore] + self._extra_tools()

    def _extra_tools(self) -> list:
        return [prompts.TOOL_SUBMIT]

    def _system_bits(self) -> dict:
        links = self.settings.use_links
        return {
            "open_rule": prompts.OPEN_RULE_LINKS if links else prompts.OPEN_RULE_ANY,
            "explore_tool": prompts.EXPLORE_LINKS if links else prompts.EXPLORE_FIND,
            "explore_hint": prompts.EXPLORE_HINT_LINKS if links else prompts.EXPLORE_HINT_FIND,
        }

    # -- 도구 처리 --
    def _tool(self, tc, round_no: int):
        if tc.name == "read_doc":
            out = self.state.read(str(tc.arguments.get("doc_id", "")), tc.arguments.get("part", 1), round_no)
            if not out.startswith("오류"):
                e = self.state.log[-1]
                self.trace.log(self.name, f"읽기 {self.state.used}/{self.state.budget}: {e['doc']} {e['part']}쪽 (경로: {e['via']})")
            return out, None
        if tc.name == "list_links":
            return self.state.list_links(str(tc.arguments.get("doc_id", ""))), None
        if tc.name == "find_docs":
            return self.state.find_docs(str(tc.arguments.get("keyword", ""))), None
        if tc.name == "submit_section":
            return self._submit(tc.arguments, round_no)
        if tc.name == "finish":
            return self._finish()
        return f"오류: 모르는 도구 {tc.name}", None

    def _finish(self):
        return "오류: 이 에이전트에는 finish 도구가 없다. submit_section 으로 제출하라.", None

    def _check_draft(self, markdown: str):
        """제출 원고 검사. (문제 설명, 인용, 안 읽은 인용, 없는 ID 인용)"""
        cited = unique_ids(markdown)
        unknown = [d for d in cited if not self.corpus.exists(d)]
        unread = [d for d in cited if self.corpus.exists(d) and d not in self.state.parts_read]
        problems = []
        if len((markdown or "").strip()) < 200:
            problems.append("원고가 너무 짧다(200자 미만).")
        if not cited:
            problems.append("인용 [d:문서ID] 이 하나도 없다.")
        return problems, cited, unread, unknown

    def _call(self, tool_choice="required") -> LLMResult:
        result = self.llm.chat(self.conv, tools=self.tools, tool_choice=tool_choice, agent=self)
        self.conv.add_assistant(result)
        return result

    def meter(self) -> dict:
        return self.conv.meter()

    def fake_reply(self, conv, tools=None, tool_choice=None, json_schema=None) -> LLMResult:
        raise NotImplementedError


class Researcher(AgentBase):
    role = "researcher"

    def __init__(self, section: dict, all_sections: list, question: str, corpus, settings, llm, trace, index: int):
        super().__init__(f"리서처 {section['id']}", question, corpus, settings, llm, trace)
        self.section = section
        self.index = index
        self.all_sections = all_sections
        self.state = ReadState(corpus, section["start_docs"], section["budget"], settings.page_chars, settings.use_links)
        self.drafts = []
        self.round_no = 1
        self._round_gates = 0
        self._start()

    def _start(self) -> None:
        s, c = self.section, self.corpus
        role_name = s.get("role_name") or "-"
        focus = next((r["focus"] for r in config.ROLES if r["name"] == role_name), "")
        peers_rule = prompts.PEERS_RULE_ON if self.settings.tell_peers else prompts.PEERS_RULE_OFF
        self.conv.add_input("system", prompts.RESEARCHER_SYSTEM.format(
            role_name=role_name, role_focus=focus, page_chars=self.settings.page_chars, peers_rule=peers_rule,
            writing_rules=prompts.WRITING_RULES, report_rules=prompts.REPORT_RULES, **self._system_bits()))
        start = "\n".join(f"- [d:{d}] {c.title(d)} ({c.parts(d, self.settings.page_chars)}쪽)" for d in s["start_docs"])
        peers_block = ""
        if self.settings.tell_peers:
            peers = "\n".join(
                f"- {p['id']}. {p['title']} [{p.get('role_name', '-')}] — {p['role']} (포함: {p['scope_in']}) / "
                f"시작 자료: {', '.join(p['start_docs'])}"
                for p in self.all_sections if p["id"] != s["id"])
            peers_block = prompts.PEERS_BLOCK.format(peers=peers or "- (없음: 이 보고서는 절이 하나다)")
        self.conv.add_input("user", prompts.RESEARCHER_BRIEF.format(
            question=self.question, sid=s["id"], title=s["title"], role_name=role_name, role=s["role"],
            scope_in=s["scope_in"], scope_out=s["scope_out"], start_docs=start, peers_block=peers_block,
            budget=s["budget"]))

    def _gate(self):
        """예산을 너무 적게 썼으면 돌려보낸다. 반환: 돌려보낼 메시지 또는 None"""
        st, s = self.state, self.settings
        need = int(round(st.budget * s.researcher_min_use))
        unread, cands, more = _describe_unread(st)
        if st.left <= 0:
            return None
        if (st.used < need or st.unread_starts()) and more and self._round_gates < s.researcher_max_rejections:
            self._round_gates += 1
            self.gate_rejections += 1
            return prompts.RESEARCHER_GATE.format(used=st.used, budget=st.budget, need=need,
                                                  unread_starts=unread, candidates=cands)
        return None

    def _submit(self, args: dict, round_no: int):
        markdown = args.get("markdown", "")
        problems, cited, unread, unknown = self._check_draft(markdown)
        if problems:
            self.submit_rejections += 1
            return "제출 거절: " + " ".join(problems) + " 고쳐서 다시 submit_section 하라.", None
        if (unread or unknown) and not self.unread_warned:
            # 코드가 한 번 잡아 준다. 그래도 고치지 않으면 받아들이되 경보로 남긴다.
            self.unread_warned = True
            self.submit_rejections += 1
            bad = ", ".join(unread + unknown)
            return (f"제출 보류: 읽지 않았거나 없는 문서를 인용했다({bad}). 읽은 문서로 인용을 고치거나 해당 문장을 빼고 "
                    "다시 제출하라."), None
        gate = self._gate()
        if gate:
            self.trace.log(self.name, f"제출 관문: 예산 {self.state.used}/{self.state.budget}회만 써서 돌려보냄")
            return gate, None
        draft = {
            "round": round_no, "markdown": markdown.strip(), "status": args.get("status", "insufficient"),
            "missing": args.get("missing", ""), "handoffs": args.get("handoffs", []) or [],
            "cited": cited, "unread_cited": unread, "unknown_cited": unknown,
            "chars": len(markdown.strip()), "reads_used": self.state.used,
        }
        self.drafts.append(draft)
        return "제출됨.", draft

    def run_round(self, extra_budget: int = 0, recheck_note: str = "") -> dict:
        if self.drafts:
            self.round_no += 1
        self._round_gates = 0
        if extra_budget:
            self.state.budget += extra_budget
        if recheck_note:
            self.conv.add_input("user", recheck_note)
        max_turns = self.state.left + 10
        for _ in range(max_turns):
            choice = "required" if self.state.left > 0 else FORCE_SUBMIT
            result = self._call(choice)
            if not result.tool_calls:
                self.conv.add_input("user", "도구로만 답하라. 다 읽었으면 submit_section 을 호출하라.")
                continue
            submitted = None
            for tc in result.tool_calls:
                if submitted is not None:
                    self.conv.add_tool_result(tc.id, "무시됨(이미 제출함).")
                    continue
                out, draft = self._tool(tc, self.round_no)
                self.conv.add_tool_result(tc.id, out)
                if draft is not None:
                    submitted = draft
            if submitted is not None:
                self.trace.log(self.name, f"제출(라운드 {self.round_no}): {submitted['chars']}자, 인용 문서 "
                                          f"{len(submitted['cited'])}건, 읽기 {self.state.used}/{self.state.budget}, "
                                          f"신고 {submitted['status']}")
                return submitted
        # 턴 상한에 걸리면 관문 없이 마지막으로 한 번 강제 제출
        self._round_gates = self.settings.researcher_max_rejections
        result = self._call(FORCE_SUBMIT)
        forced = None
        for tc in result.tool_calls:
            if forced is not None:
                self.conv.add_tool_result(tc.id, "무시됨(이미 제출함).")
                continue
            out, draft = self._tool(tc, self.round_no)
            self.conv.add_tool_result(tc.id, out)
            forced = draft
        if forced is not None:
            return forced
        failed = {"round": self.round_no, "markdown": "", "status": "failed", "missing": "턴 상한 안에 제출하지 못함",
                  "handoffs": [], "cited": [], "unread_cited": [], "unknown_cited": [], "chars": 0,
                  "reads_used": self.state.used}
        self.drafts.append(failed)
        self.trace.log(self.name, "제출 실패(턴 상한)")
        return failed

    def fake_reply(self, conv, tools=None, tool_choice=None, json_schema=None) -> LLMResult:
        return fake.researcher_step(self, tool_choice)


class SingleAgent(AgentBase):
    """대조군: 같은 목차·시작 자료·도구·총예산으로 혼자 모든 절을 쓴다."""

    role = "single"

    def __init__(self, sections: list, question: str, corpus, settings, llm, trace, budget: int):
        super().__init__("단일 에이전트", question, corpus, settings, llm, trace)
        self.sections = sections
        starts = [d for s in sections for d in s["start_docs"]]
        self.state = ReadState(corpus, list(dict.fromkeys(starts)), budget, settings.page_chars, settings.use_links)
        self.drafts = {}          # sid -> 최신 원고
        self.history = []         # 모든 제출 기록
        self.finish_rejections = 0
        self.finished = False
        c = corpus
        self.conv.add_input("system", prompts.SINGLE_SYSTEM.format(
            page_chars=settings.page_chars, budget=budget,
            writing_rules=prompts.WRITING_RULES, report_rules=prompts.REPORT_RULES, **self._system_bits()))
        lines = []
        for s in sections:
            docs = ", ".join(f"[d:{d}] {c.title(d)}" for d in s["start_docs"])
            lines.append(f"- {s['id']}. {s['title']} [{s.get('role_name', '-')}] — {s['role']}\n"
                         f"  포함: {s['scope_in']} / 제외: {s['scope_out']}\n"
                         f"  시작 자료: {docs} / 코디네이터가 제안한 예산: {s['budget']}회")
        self.conv.add_input("user", prompts.SINGLE_BRIEF.format(question=question, sections="\n".join(lines), budget=budget))

    def _extra_tools(self) -> list:
        return [prompts.TOOL_SUBMIT_SINGLE, prompts.TOOL_FINISH]

    def _submit(self, args: dict, round_no: int):
        sid = args.get("section_id", "")
        if sid not in {s["id"] for s in self.sections}:
            return f"제출 거절: 목차에 없는 section_id '{sid}'.", None
        markdown = args.get("markdown", "")
        problems, cited, unread, unknown = self._check_draft(markdown)
        if problems:
            self.submit_rejections += 1
            return "제출 거절: " + " ".join(problems), None
        if (unread or unknown) and not self.unread_warned:
            self.unread_warned = True
            self.submit_rejections += 1
            return f"제출 보류: 읽지 않았거나 없는 문서를 인용했다({', '.join(unread + unknown)}). 고쳐서 다시 제출하라.", None
        draft = {"round": len([h for h in self.history if h["section_id"] == sid]) + 1, "section_id": sid,
                 "markdown": markdown.strip(), "status": args.get("status", "insufficient"),
                 "missing": args.get("missing", ""), "handoffs": args.get("handoffs", []) or [],
                 "cited": cited, "unread_cited": unread, "unknown_cited": unknown,
                 "chars": len(markdown.strip()), "reads_used": self.state.used}
        self.drafts[sid] = draft
        self.history.append(draft)
        self.trace.log(self.name, f"{sid} 제출: {draft['chars']}자, 인용 문서 {len(cited)}건, 읽기 {self.state.used}/{self.state.budget}")
        return f"{sid} 제출됨.", None

    def _finish(self):
        missing = [s["id"] for s in self.sections if s["id"] not in self.drafts]
        if missing:
            return f"아직 제출하지 않은 절이 있다: {', '.join(missing)}", None
        st, s = self.state, self.settings
        need = int(round(st.budget * s.single_min_use))
        if st.used < need and self.finish_rejections < s.single_max_rejections:
            self.finish_rejections += 1
            self.gate_rejections += 1
            unread_lines = []
            for sec in self.sections:
                us = st.unread_starts(sec["start_docs"])
                if us:
                    unread_lines.append(f"{sec['id']}: " + ", ".join(f"{d}({self.corpus.title(d)})" for d in us))
            unread = ("아직 안 읽은 시작 자료 — " + " / ".join(unread_lines) + "\n") if unread_lines else ""
            _, cands, _ = _describe_unread(st, starts=[])
            self.trace.log(self.name, f"끝내기 관문: 예산 {st.used}/{st.budget}회만 써서 돌려보냄({self.finish_rejections}회째)")
            return prompts.SINGLE_NOT_DONE.format(used=st.used, budget=st.budget, need=need,
                                                  unread_starts=unread, candidates=cands), None
        self.finished = True
        return "끝.", None

    def run(self) -> dict:
        max_turns = self.state.budget + 4 * len(self.sections) + 20
        for _ in range(max_turns):
            result = self._call("required")
            if not result.tool_calls:
                self.conv.add_input("user", "도구로만 답하라.")
                continue
            for tc in result.tool_calls:
                if self.finished:
                    self.conv.add_tool_result(tc.id, "무시됨(이미 끝남).")
                    continue
                out, _ = self._tool(tc, 1)
                self.conv.add_tool_result(tc.id, out)
            if self.finished:
                break
        if not self.finished:
            self.trace.log(self.name, "턴 상한 도달 — 제출된 절까지만 사용")
        return self.drafts

    def fake_reply(self, conv, tools=None, tool_choice=None, json_schema=None) -> LLMResult:
        return fake.single_step(self)
