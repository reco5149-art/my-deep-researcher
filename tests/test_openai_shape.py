"""실제 API 없이, GPT 호출 경로가 올바른 모양의 요청을 만드는지 시험한다.
가짜 OpenAI 클라이언트가 요청을 검사하고 정해진 답을 돌려준다. 실행: python -m tests.test_openai_shape
"""
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace as NS

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import config  # noqa: E402
from agents.corpus import Corpus  # noqa: E402
from tests.make_fixture import build  # noqa: E402
from tests.test_pipeline import use_tmp_output  # noqa: E402


def check_messages(messages):
    """assistant 의 tool_calls 뒤에는 그 id 마다 tool 답이 와야 한다(OpenAI 규칙)."""
    pending = set()
    for m in messages:
        if m["role"] == "tool":
            assert m["tool_call_id"] in pending, "짝 없는 tool 메시지"
            pending.discard(m["tool_call_id"])
            continue
        assert not pending, f"tool 답이 빠졌다: {pending}"
        if m["role"] == "assistant" and m.get("tool_calls"):
            pending = {tc["id"] for tc in m["tool_calls"]}
    assert not pending, f"tool 답이 빠졌다: {pending}"


class FakeCompletions:
    def __init__(self):
        self.calls = 0
        self.n = 0

    def _msg(self, content=None, calls=None):
        tcs = None
        if calls:
            tcs = []
            for name, args in calls:
                self.n += 1
                tcs.append(NS(id=f"call_{self.n}", type="function",
                              function=NS(name=name, arguments=json.dumps(args, ensure_ascii=False))))
        return NS(choices=[NS(message=NS(content=content, tool_calls=tcs))],
                  usage=NS(prompt_tokens=100, completion_tokens=20))

    def create(self, **kw):
        self.calls += 1
        assert kw["model"] and kw["max_completion_tokens"] > 0
        assert "temperature" not in kw
        if kw["model"].startswith("gpt-5"):
            assert kw.get("reasoning_effort") == "low"
        check_messages(kw["messages"])
        if kw.get("response_format"):
            name = kw["response_format"]["json_schema"]["name"]
            if name == "research_plan":
                plan = {"rationale": "시험", "sections": [
                    {"role_name": "기원·방법론", "title": "창립", "role": "누가?", "scope_in": "a", "scope_out": "b", "start_docs": ["greg_glassman"], "budget": 3},
                    {"role_name": "대회·선수", "title": "대회", "role": "언제?", "scope_in": "a", "scope_out": "b", "start_docs": ["crossfit_games"], "budget": 3},
                ]}
                return self._msg(content=json.dumps(plan, ensure_ascii=False))
            return self._msg(content=json.dumps({"title": "T", "intro": "소개", "transitions": [],
                                                 "conclusion": "맺음 [d:greg_glassman]"}, ensure_ascii=False))
        tools = {t["function"]["name"] for t in kw["tools"]}
        for t in kw["tools"]:
            params = t["function"]["parameters"]
            assert params["additionalProperties"] is False and set(params["required"]) == set(params["properties"])
        last_tool = [m for m in kw["messages"] if m["role"] == "tool"]
        read_count = sum(1 for m in last_tool if m["content"].startswith("[d:"))
        if "finish" in tools:  # 단일 에이전트
            if read_count < 2:
                return self._msg(calls=[("read_doc", {"doc_id": "greg_glassman", "part": 1}),
                                        ("read_doc", {"doc_id": "crossfit_games", "part": 1})])
            if not any("S1 제출됨" in m["content"] for m in last_tool):
                body = "글래스먼 이야기다. " * 30 + "[d:greg_glassman]"
                return self._msg(calls=[("submit_section", {"section_id": "S1", "markdown": body, "status": "sufficient", "missing": "", "handoffs": []}),
                                        ("submit_section", {"section_id": "S2", "markdown": body.replace("greg_glassman", "crossfit_games"), "status": "sufficient", "missing": "", "handoffs": []})])
            return self._msg(calls=[("finish", {})])
        doc = "greg_glassman" if "greg_glassman" in kw["messages"][1]["content"].split("## 시작 자료")[1][:80] else "crossfit_games"
        if read_count == 0:
            return self._msg(calls=[("read_doc", {"doc_id": doc, "part": 1}), ("list_links", {"doc_id": doc})])
        body = "내용이다. " * 40 + f"[d:{doc}]"
        return self._msg(calls=[("submit_section", {"markdown": body, "status": "sufficient", "missing": "", "handoffs": []}),
                                ("read_doc", {"doc_id": doc, "part": 1})])


def main():
    tmp = Path(tempfile.mkdtemp())
    fake = FakeCompletions()
    try:
        os.environ["OPENAI_API_KEY"] = "test"
        use_tmp_output(tmp)
        from baseline import run_baseline
        from graph import run_question

        class FakeClient:
            def __init__(self, **kw):
                self.chat = NS(completions=fake)

        import openai
        openai.OpenAI = FakeClient
        corpus = Corpus.load(build(tmp / "corpus"))
        for variant in ["full", "single"]:
            if variant == "single":
                t = run_baseline("크로스핏 역사?", "QX", corpus=corpus, model="gpt-5-mini", total_reads=10, recheck_reserve=4)
            else:
                s = config.make_settings(variant, model="gpt-5-mini", total_reads=10, recheck_reserve=4)
                t = run_question("크로스핏 역사?", "QX", s, corpus=corpus)
            if variant == "single":
                # 가짜 모델이 2회만 읽고 끝내려 하면: finish 를 두 번 돌려보내고, 그래도 멈추면 경보가 울려야 한다
                assert t["single"]["finish_rejections"] == config.Settings().single_max_rejections
                assert t["metrics"]["alarms_fired"] == ["control_underuse"], t["metrics"]["alarms_fired"]
            else:
                assert not t["metrics"]["alarms_fired"], t["metrics"]["alarms_fired"]
            print(f"OK openai-shape {variant}: API 호출 누적 {fake.calls}회, 경보 {t['metrics']['alarms_fired'] or '없음'}")
        print("모든 시험 통과")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
