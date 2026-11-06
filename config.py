"""설정 읽기. 도메인에 묶인 값은 config.json, 비밀 값(API 키)과 개인 설정은 .env 에 둔다.

우선순위: .env/환경변수 > config.json > 아래 기본값. (표준 라이브러리만 사용)
"""
import json
import os
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
CORPUS_PATH = DATA_DIR / "corpus.json"
CACHE_DIR = DATA_DIR / "cache"
OUTPUT_DIR = ROOT / "output"
TRACES_DIR = OUTPUT_DIR / "traces"
REPORTS_DIR = OUTPUT_DIR / "reports"
RUNS_JSONL = OUTPUT_DIR / "runs.jsonl"
ABLATION_JSON = OUTPUT_DIR / "ablation.json"


def _load_dotenv(path: Path = ROOT / ".env") -> None:
    """python-dotenv 없이 .env 를 읽는다. 이미 있는 환경변수는 덮어쓰지 않는다."""
    if not path.exists():
        return
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:  # 메모장에서 ANSI(CP949)로 저장한 경우
        text = path.read_text(encoding="cp949")
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()
if "여기에" in os.environ.get("OPENAI_API_KEY", ""):  # .env.example 의 안내 문구를 그대로 둔 경우
    os.environ.pop("OPENAI_API_KEY")

CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
ROLES = CFG["roles"]
ROLE_NAMES = [r["name"] for r in ROLES]


def _env(name: str, default):
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    return type(default)(raw)


MODEL = _env("OPENAI_MODEL", CFG["model"]["name"])
CONTEXT_WINDOW = _env("CONTEXT_WINDOW", CFG["model"]["context_window"])


@dataclass
class Settings:
    """한 번의 실행에 쓰는 설정. 화면(app.py)과 명령줄에서 바꿀 수 있다."""

    model: str = MODEL
    context_window: int = CONTEXT_WINDOW
    reasoning_effort: str = _env("REASONING_EFFORT", CFG["model"]["reasoning_effort"])

    # 읽기 예산: read_doc 한 번 = 1회 = 최대 page_chars 글자
    total_reads: int = _env("TOTAL_READS", CFG["budget"]["total_reads"])     # 한 질문 전체(대조군도 같은 값)
    recheck_reserve: int = _env("RECHECK_RESERVE", CFG["budget"]["recheck_reserve"])  # 그중 재파견용 예약
    min_section_budget: int = CFG["budget"]["min_per_section"]
    page_chars: int = CFG["budget"]["page_chars"]
    min_sections: int = CFG["sections"]["min"]
    max_sections: int = CFG["sections"]["max"]
    recheck_rounds: int = CFG["recheck"]["max_rounds"]               # 재파견 바퀴 수 상한
    recheck_reads_per_section: int = CFG["recheck"]["reads_per_section"]

    # 제출 관문: 예산을 너무 적게 쓰고 끝내려 하면 돌려보낸다
    researcher_min_use: float = CFG["gates"]["researcher_min_use"]
    researcher_max_rejections: int = CFG["gates"]["researcher_max_rejections"]
    single_min_use: float = CFG["gates"]["single_min_use"]
    single_max_rejections: int = CFG["gates"]["single_max_rejections"]

    # 스위치(장치). ablation.py 가 하나씩 끈다.
    tell_peers: bool = True      # 리서처에게 남의 구역을 알려 준다
    recheck: bool = True         # 부족 신고한 절만 다시 내보낸다
    use_links: bool = True       # 리서처는 links 를 따라서만 새 문서를 연다(끄면 아무 문서나 연다)
    single_agent: bool = False   # 대조군: 에이전트 1명이 모든 절을 쓴다

    practice: bool = False       # 연습 모드: API 없이 가짜 모델로 흐름만 확인
    max_workers: int = 6
    extra: dict = field(default_factory=dict)

    @property
    def section_pool(self) -> int:
        """코디네이터가 절들에 나눠 줄 수 있는 읽기 예산(재파견 몫 제외)."""
        return self.total_reads - (self.recheck_reserve if self.recheck else 0)

    def variant_name(self) -> str:
        if self.single_agent:
            return "single"
        for name, flags in VARIANTS.items():
            if name in ("full", "single"):
                continue
            if all(getattr(self, k) == v for k, v in flags.items()):
                return name
        return "full"


VARIANTS = {
    "full": dict(),
    "no_peers": dict(tell_peers=False),
    "no_recheck": dict(recheck=False),
    "no_links": dict(use_links=False),
    "single": dict(single_agent=True, recheck=False),
}

VARIANT_LABELS = {
    "full": "기본 (모든 장치 ON)",
    "no_peers": "남의 구역 알림 OFF",
    "no_recheck": "점검·재파견 OFF",
    "no_links": "links 탐색 OFF",
    "single": "단일 에이전트 대조군",
}


def make_settings(variant: str = "full", **overrides) -> Settings:
    return Settings(**{**VARIANTS[variant], **overrides})
