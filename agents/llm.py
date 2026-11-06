"""모델 호출 창구. 실제 GPT(OpenAIChat)와 연습용 가짜 모델(FakeChat)이 같은 모양으로 답한다.

에이전트마다 Conversation 하나를 갖고, 그 대화에 '받은 글자 수'를 센다.
→ 코디네이터가 본 글자 수와 리서처가 본 글자 수를 따로 세어 격리를 숫자로 보인다.
"""
import json
import os
import threading
import time
from dataclasses import dataclass, field


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict
    raw_arguments: str = ""


@dataclass
class LLMResult:
    content: str = ""
    tool_calls: list = field(default_factory=list)
    prompt_tokens: int = 0
    completion_tokens: int = 0


class Conversation:
    """한 에이전트의 대화 기록과 계량기."""

    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role                # coordinator / researcher / single
        self.messages = []
        self.seen_chars = 0             # 이 에이전트가 '받은' 글자 수(시스템·사용자·도구 결과)
        self.written_chars = 0          # 이 에이전트가 쓴 글자 수
        self.prompt_tokens = 0          # API가 청구한 입력 토큰(대화가 길어지면 다시 보낸 몫 포함)
        self.completion_tokens = 0
        self.calls = 0

    def add_input(self, role: str, content: str, **extra) -> None:
        msg = {"role": role, "content": content, **extra}
        self.messages.append(msg)
        self.seen_chars += len(content or "")

    def add_assistant(self, result: LLMResult) -> None:
        msg = {"role": "assistant", "content": result.content or ""}
        if result.tool_calls:
            msg["tool_calls"] = [{
                "id": tc.id, "type": "function",
                "function": {"name": tc.name, "arguments": tc.raw_arguments or json.dumps(tc.arguments, ensure_ascii=False)},
            } for tc in result.tool_calls]
        self.messages.append(msg)
        self.written_chars += len(result.content or "") + sum(len(tc.raw_arguments or "") for tc in result.tool_calls)
        self.prompt_tokens += result.prompt_tokens
        self.completion_tokens += result.completion_tokens
        self.calls += 1

    def add_tool_result(self, call_id: str, content: str) -> None:
        self.add_input("tool", content, tool_call_id=call_id)

    def meter(self) -> dict:
        return {"seen_chars": self.seen_chars, "written_chars": self.written_chars,
                "prompt_tokens": self.prompt_tokens, "completion_tokens": self.completion_tokens,
                "calls": self.calls}


class OpenAIChat:
    """실제 GPT 호출. .env 의 OPENAI_API_KEY 를 쓴다."""

    def __init__(self, settings):
        from openai import OpenAI  # 연습 모드에서는 설치 없이도 돌아가도록 여기서 불러온다

        if not os.environ.get("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY 가 없습니다. .env 파일에 키를 넣거나 연습 모드(--practice)로 실행하세요.")
        self.client = OpenAI(max_retries=4, timeout=300)
        self.settings = settings
        self._lock = threading.Lock()

    def _is_reasoning(self) -> bool:
        m = self.settings.model
        return m.startswith(("gpt-5", "gpt-6", "o1", "o3", "o4"))

    def chat(self, conv: Conversation, tools=None, tool_choice=None, json_schema=None, agent=None,
             max_tokens: int = 16_000) -> LLMResult:
        kwargs = {"model": self.settings.model, "messages": conv.messages, "max_completion_tokens": max_tokens}
        if self._is_reasoning() and self.settings.reasoning_effort:
            kwargs["reasoning_effort"] = self.settings.reasoning_effort
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice or "auto"
            kwargs["parallel_tool_calls"] = True
        if json_schema:
            kwargs["response_format"] = {"type": "json_schema", "json_schema": json_schema}
        for attempt in range(3):
            try:
                resp = self.client.chat.completions.create(**kwargs)
                break
            except Exception:  # 일시 오류는 몇 번 더 시도
                if attempt == 2:
                    raise
                time.sleep(5 * (attempt + 1))
        msg = resp.choices[0].message
        calls = []
        for tc in msg.tool_calls or []:
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {"_invalid_json": tc.function.arguments}
            calls.append(ToolCall(id=tc.id, name=tc.function.name, arguments=args, raw_arguments=tc.function.arguments or ""))
        usage = resp.usage
        return LLMResult(content=msg.content or "", tool_calls=calls,
                         prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0,
                         completion_tokens=getattr(usage, "completion_tokens", 0) or 0)


class FakeChat:
    """연습 모드: API 없이 규칙대로 움직이는 가짜 모델. 에이전트의 fake_reply()가 답을 정한다."""

    def __init__(self, settings):
        self.settings = settings

    def chat(self, conv: Conversation, tools=None, tool_choice=None, json_schema=None, agent=None,
             max_tokens: int = 16_000) -> LLMResult:
        if agent is None:
            raise RuntimeError("연습 모드에는 agent 가 필요합니다")
        result = agent.fake_reply(conv, tools=tools, tool_choice=tool_choice, json_schema=json_schema)
        result.prompt_tokens = sum(len(m.get("content") or "") for m in conv.messages) // 4
        result.completion_tokens = (len(result.content or "") + sum(len(json.dumps(t.arguments, ensure_ascii=False))
                                                                    for t in result.tool_calls)) // 4
        for tc in result.tool_calls:
            tc.raw_arguments = tc.raw_arguments or json.dumps(tc.arguments, ensure_ascii=False)
        return result


def make_llm(settings):
    return FakeChat(settings) if settings.practice else OpenAIChat(settings)
