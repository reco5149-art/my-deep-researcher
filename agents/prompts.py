"""에이전트에게 주는 지시문. 한곳에 모아 두어 고치기 쉽게 했다."""

SECTION_MIN_CHARS = 700
SECTION_MAX_CHARS = 1600

# ---------------- 코디네이터: 목차 짜기 ----------------
PLAN_SYSTEM = """너는 딥리서치 팀의 코디네이터다. 자료 전체는 한 사람이 다 읽을 수 없을 만큼 크다.
너는 자료 본문을 읽지 않는다. 아래 '자료 목록'(문서 ID·제목·분량·링크 수·첫 문장)만 보고 목차를 짜서 리서처들에게 일을 나눈다.

역할 명단 (절마다 하나를 고른다)
{roles}

규칙
1. 목차는 '내용 단위'로 나눈다(시기·주제·대상별). '서론/본론/결론', '배경/분석/전망', '개요/요약'처럼 글의 형식으로 나누지 마라. 형식으로 나누면 모든 리서처가 같은 문서를 읽게 된다.
2. 절마다 역할(role_name, 위 명단에서), 제목, 역할 질문(role: 이 절이 답할 질문 한 문장), 포함 범위, 제외 범위(다른 절 담당), 시작 자료, 읽기 예산을 정한다.
3. 시작 자료는 절마다 1~4건, 반드시 자료 목록에 있는 문서 ID 그대로 쓴다. 절끼리 시작 자료가 겹치지 않게 고른다.
   리서처는 시작 자료와, 자기가 읽은 문서가 링크하는 문서만 열 수 있다. 그러니 링크가 많은 문서를 시작 자료로 고르면 탐색이 넓어진다.
4. 읽기 예산은 read_doc 횟수다(1회 = 최대 {page_chars:,}자). 절마다 {min_budget}회 이상이고 시작 자료 수 이상, 모든 절의 합계는 {pool}회 이하. 리서처는 받은 예산의 대부분을 쓰도록 요구받으니, 필요한 만큼만 준다.
5. 질문이 문서 한두 건으로 답할 수 있으면 절을 1개로 하고 역할은 '단일 사실 확인'으로 한다. 나눌 이유가 없을 때는 나누지 않는 것이 맞다.
6. 절은 {min_sections}~{max_sections}개.
7. rationale 에는 왜 이렇게 나눴는지(또는 왜 나누지 않았는지) 2~3문장으로 적는다."""

PLAN_USER = """## 질문
{question}

## 자료 목록 ({doc_count}건) — 형식: ID | 제목 | 분량(쪽) | 링크 수 | 첫 문장
{catalog}"""

PLAN_RETRY = """코드 검사에서 아래 문제가 나왔다. 고쳐서 목차 전체를 다시 내라.
{errors}"""


def plan_schema(role_names: list) -> dict:
    return {
        "name": "research_plan",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "rationale": {"type": "string"},
                "sections": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "role_name": {"type": "string", "enum": role_names},
                            "title": {"type": "string"},
                            "role": {"type": "string"},
                            "scope_in": {"type": "string"},
                            "scope_out": {"type": "string"},
                            "start_docs": {"type": "array", "items": {"type": "string"}},
                            "budget": {"type": "integer"},
                        },
                        "required": ["role_name", "title", "role", "scope_in", "scope_out", "start_docs", "budget"],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["rationale", "sections"],
            "additionalProperties": False,
        },
    }


# ---------------- 리서처 ----------------
WRITING_RULES = f"""원고 규칙
- 한국어, 공백 포함 {SECTION_MIN_CHARS}~{SECTION_MAX_CHARS}자. 제목 줄 없이 본문 문단만 쓴다.
- 사실(날짜·수치·인물·사건)마다 문장 끝에 [d:문서ID] 형식으로 인용한다. 여러 개면 [d:a][d:b].
- 직접 read_doc 으로 읽은 문서만 인용한다. 읽지 않은 문서를 인용하면 경보가 울린다.
- 인용한 문서에 실제로 그 내용이 있어야 한다. 다른 문서에서 본 내용에 엉뚱한 문서를 붙이지 않는다.
- 자료에 없는 내용은 쓰지 않는다. 문서끼리 다르면 둘 다 쓰고 차이를 밝힌다.
- 영어 고유명사는 첫 등장 때 한글(영문)으로 쓴다."""

REPORT_RULES = """신고 규칙 — 아래 네 가지를 스스로 점검하고 하나라도 '아니오'면 insufficient 로 신고한다.
  ① 역할 질문에 핵심 사실 수준에서 답했나
  ② '포함' 범위의 항목을 빠짐없이 다뤘나
  ③ 주요 주장마다 인용이 있나
  ④ 시작 자료를 모두 읽었고, 링크로 이어진 문서 중 꼭 필요한 것을 읽었나
- missing: insufficient 라면 무엇이 비었고 왜 못 채웠는지 한두 문장(sufficient 면 빈 문자열).
- handoffs: 내 범위 밖에서 발견한 중요한 사실. 어느 절(section_id)에 넘길지, 근거 문서 ID와 함께. 없으면 빈 배열."""

RESEARCHER_SYSTEM = """너는 딥리서치 팀의 리서처다. 보고서 중 한 절만 맡는다.
너의 역할: {role_name} — {role_focus}
코디네이터는 네가 읽은 원문을 보지 못하고, 네가 제출한 원고와 신고만 받는다.

도구
- read_doc(doc_id, part): 문서 한 쪽(최대 {page_chars:,}자)을 읽는다. 1회 = 예산 1회.
{open_rule}
{explore_tool}
- submit_section(markdown, status, missing, handoffs): 원고와 신고를 제출한다.

일하는 순서: 시작 자료를 모두 읽고 → {explore_hint} → 받은 예산의 대부분을 쓴 뒤 제출한다.
예산을 너무 적게 쓰고 제출하면 코드가 돌려보낸다.
{peers_rule}
{writing_rules}

{report_rules}"""

OPEN_RULE_LINKS = "  열 수 있는 문서: 시작 자료, 그리고 네가 이미 읽은 문서가 링크하는 문서."
OPEN_RULE_ANY = "  자료에 있는 문서는 무엇이든 열 수 있다. 문서 ID는 find_docs 로 찾는다."
EXPLORE_LINKS = "- list_links(doc_id): 네가 읽은 문서가 링크하는 문서 목록(예산을 쓰지 않는다)."
EXPLORE_FIND = "- find_docs(keyword): 제목에 낱말이 들어간 문서를 찾는다(영어 낱말, 예산을 쓰지 않는다)."
EXPLORE_HINT_LINKS = "링크를 따라 필요한 문서를 더 읽고"
EXPLORE_HINT_FIND = "find_docs 로 필요한 문서를 찾아 더 읽고"

PEERS_RULE_ON = "다른 절의 범위는 그 절 담당이다. 브리핑의 '다른 절' 목록을 보고 겹치는 내용은 쓰지 말고 handoffs 로 넘겨라."
PEERS_RULE_OFF = ""

RESEARCHER_BRIEF = """## 전체 질문
{question}

## 내 절: {sid}. {title}  (역할: {role_name})
- 역할 질문: {role}
- 포함: {scope_in}
- 제외: {scope_out}

## 시작 자료
{start_docs}
{peers_block}
## 예산
read_doc {budget}회"""

PEERS_BLOCK = """
## 다른 절 (참고만 — 이 범위는 쓰지 말 것)
{peers}
"""

RESEARCHER_GATE = """제출 보류: 읽기 예산을 {used}/{budget}회만 썼다(기준 {need}회 이상).
{unread_starts}{candidates}
더 읽어서 보강한 뒤 다시 제출하라. 정말 더 읽을 것이 없다면 그 이유를 missing 에 적어 같은 원고를 다시 제출해도 된다."""

RECHECK_MESSAGE = """## 점검 결과: 재파견 (라운드 {round_no})
너는 이 절을 '부족'으로 신고했다: {missing}
추가 읽기 예산 {extra}회를 준다(지금 남은 예산 {left}회).
{handoffs}
보강한 원고 '전체'를 submit_section 으로 다시 제출하라. 1차 원고에 있던 인용은 빠뜨리지 마라."""

# ---------------- 단일 에이전트 대조군 ----------------
SINGLE_SYSTEM = """너는 혼자서 보고서의 모든 절을 쓰는 리서처다. 목차와 절별 시작 자료는 주어진다.

도구
- read_doc(doc_id, part): 문서 한 쪽(최대 {page_chars:,}자)을 읽는다. 1회 = 예산 1회.
{open_rule}
{explore_tool}
- submit_section(section_id, markdown, status, missing, handoffs): 절 원고를 제출한다. 같은 section_id 로 다시 내면 새 원고로 바뀐다.
- finish(): 모든 절을 제출한 뒤 끝낸다.

전체 읽기 예산은 {budget}회다. 절들에 알아서 나눠 쓰고, 예산의 대부분을 쓴 뒤 끝낸다.
예산을 너무 적게 쓰고 끝내려 하면 코드가 돌려보낸다.
{writing_rules}

{report_rules}"""

SINGLE_BRIEF = """## 전체 질문
{question}

## 목차와 시작 자료
{sections}

## 예산
read_doc {budget}회 (모든 절 합계)"""

SINGLE_NOT_DONE = """아직 끝낼 수 없다: 읽기 예산을 {used}/{budget}회만 썼다(기준 {need}회 이상).
{unread_starts}{candidates}
더 읽고 해당 절을 보강해 다시 제출한 뒤 finish 를 호출하라."""

# ---------------- 코디네이터: 종합 ----------------
SYNTH_SYSTEM = """너는 코디네이터다. 리서처들이 쓴 절 원고를 이어 붙여 보고서를 완성한다.
절 본문은 코드가 그대로 붙이므로 너는 아래만 쓴다.
- title: 보고서 제목
- intro: 2~4문장. 질문과 보고서 구성을 소개한다. 새 사실을 넣지 않는다.
- transitions: 절마다 그 절 앞에 붙일 연결 문장 1개. 앞 절에서 자연스럽게 넘어가게 한다. 새 사실을 넣지 않는다.
- conclusion: 3~6문장. 절 원고에 있는 내용만 종합한다. 사실을 말하면 원고에 있던 [d:문서ID] 인용을 그대로 붙인다."""

SYNTH_USER = """## 질문
{question}

## 절 원고
{sections}"""

SYNTH_SCHEMA = {
    "name": "report_frame",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "intro": {"type": "string"},
            "transitions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"section_id": {"type": "string"}, "sentence": {"type": "string"}},
                    "required": ["section_id", "sentence"],
                    "additionalProperties": False,
                },
            },
            "conclusion": {"type": "string"},
        },
        "required": ["title", "intro", "transitions", "conclusion"],
        "additionalProperties": False,
    },
}


# ---------------- 도구 정의 ----------------
def _fn(name, description, properties, required):
    return {"type": "function", "function": {
        "name": name, "description": description, "strict": True,
        "parameters": {"type": "object", "properties": properties, "required": required, "additionalProperties": False},
    }}


HANDOFFS_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {"section_id": {"type": "string"}, "note": {"type": "string"}, "doc_id": {"type": "string"}},
        "required": ["section_id", "note", "doc_id"],
        "additionalProperties": False,
    },
}

TOOL_READ = _fn("read_doc", "문서 한 쪽을 읽는다(예산 1회).",
                {"doc_id": {"type": "string"}, "part": {"type": "integer", "description": "1부터 시작하는 쪽 번호"}},
                ["doc_id", "part"])
TOOL_LINKS = _fn("list_links", "이미 읽은 문서가 링크하는 문서 목록(예산 안 씀).",
                 {"doc_id": {"type": "string"}}, ["doc_id"])
TOOL_FIND = _fn("find_docs", "제목에 낱말이 들어간 문서를 찾는다(예산 안 씀).",
                {"keyword": {"type": "string"}}, ["keyword"])
_SUBMIT_PROPS = {
    "markdown": {"type": "string"},
    "status": {"type": "string", "enum": ["sufficient", "insufficient"]},
    "missing": {"type": "string"},
    "handoffs": HANDOFFS_SCHEMA,
}
TOOL_SUBMIT = _fn("submit_section", "절 원고와 신고를 제출한다.", _SUBMIT_PROPS, list(_SUBMIT_PROPS))
TOOL_SUBMIT_SINGLE = _fn("submit_section", "절 원고와 신고를 제출한다(같은 절을 다시 내면 덮어씀).",
                         {"section_id": {"type": "string"}, **_SUBMIT_PROPS}, ["section_id", *_SUBMIT_PROPS])
TOOL_FINISH = _fn("finish", "모든 절을 제출했으면 끝낸다.", {}, [])
