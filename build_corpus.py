"""1단계 — 자료 모으기: 영문 위키백과에서 크로스핏 관련 문서를 모아 data/corpus.json 에 저장한다.

실행 (프로젝트 폴더에서):
    python build_corpus.py

- 표준 라이브러리만 써서 pip 설치 없이 바로 돌아간다. 인터넷 연결이 필요하다(약 5~10분, 위키백과가 쉬라고 하면 더 걸린다).
- 위키백과가 "요청이 너무 많다(429)"고 하지 않도록 요청 사이에 1초씩 쉰다.
- 받아 온 문서는 data/cache/ 에 바로 저장한다. 중간에 멈춰도 다시 실행하면 이어서 한다.
- data/seeds.txt 의 문서를 먼저 모으고, 총량이 '컨텍스트 윈도우 × 1.2' 토큰을 넘을 때까지
  'CrossFit'을 언급하는 문서 중 이미 모은 문서들이 많이 링크하는 문서를 더 모은다.
- 결과: data/corpus.json = {"meta": 수집 요약, "docs": [{id, title, url, text, chars, tokens, links}, ...]}
  links 는 그 문서가 가리키는(위키 링크로 연결된) 자료 안의 다른 문서 ID 목록이다.

옵션:
    --target-tokens 520000   목표 토큰 수를 직접 지정
    --max-docs 300           문서 수 상한
    --delay 1.0              요청 사이 쉬는 시간(초). 429 가 계속 나면 2 로 늘린다
    --no-expand              seeds.txt 문서만 모은다
"""
import argparse
import hashlib
import json
import os
import re
import ssl
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

import config
from agents.corpus import DISAMBIG_RE
from tokens import count_tokens, method as token_method

API = "https://en.wikipedia.org/w/api.php"
# 위키백과는 프로그램 이름과 연락처가 적힌 User-Agent 를 요구한다. 연락처는 .env 의 WIKI_CONTACT 로 넣을 수 있다.
_CONTACT = os.environ.get("WIKI_CONTACT", "").strip()
HEADERS = {"User-Agent": "CrossFitDeepResearchStudentProject/1.2 (non-commercial class project"
                         + (f"; {_CONTACT}" if _CONTACT else "") + ")"}
CUT_HEADINGS = (
    "See also", "References", "External links", "Notes", "Further reading",
    "Bibliography", "Citations", "Sources", "Footnotes", "Notes and references",
)
CUT_RE = re.compile(r"^==\s*(%s)\s*==\s*$" % "|".join(re.escape(h) for h in CUT_HEADINGS), re.M | re.I)
SKIP_TITLE_RE = re.compile(r"^(List of|Lists of|Category:|Template:|Help:|Portal:)|\(identifier\)$")

DELAY = 1.0          # 요청 사이 쉬는 시간(초) — main() 에서 --delay 로 바꿀 수 있다
OFFLINE = False      # True 면 위키백과에 묻지 않고 cache 에 받아 둔 것만 쓴다(--offline)
_SSL_CONTEXT = None  # 기본 인증서로 안 되면 certifi 인증서 묶음으로 바꾼다
_REQUESTS = {"n": 0}


def _certifi_context():
    try:
        import certifi  # openai 를 설치하면 함께 깔린다
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return None


def _describe(exc: Exception) -> str:
    if isinstance(exc, urllib.error.HTTPError):
        try:
            body = exc.read().decode("utf-8", "ignore")[:120].replace("\n", " ")
        except Exception:
            body = ""
        return f"HTTP {exc.code} {exc.reason} {body}".strip()
    return f"{type(exc).__name__}: {exc}"


def api(params: dict, retries: int = 8) -> dict:
    global _SSL_CONTEXT
    if OFFLINE:
        raise RuntimeError("오프라인 모드에서는 위키백과에 요청하지 않는다")
    params = {**params, "format": "json", "formatversion": "2"}
    url = API + "?" + urllib.parse.urlencode(params)
    last = ""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30, context=_SSL_CONTEXT) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            _REQUESTS["n"] += 1
            time.sleep(DELAY)  # 위키백과 서버에 대한 예의(빠르게 연달아 보내면 429)
            return data
        except Exception as exc:
            last = _describe(exc)
            if "CERTIFICATE_VERIFY_FAILED" in last and _SSL_CONTEXT is None:
                _SSL_CONTEXT = _certifi_context()
                if _SSL_CONTEXT is not None:
                    print("   ! 인증서 확인 실패 → certifi 인증서로 다시 시도")
                    continue
            code = exc.code if isinstance(exc, urllib.error.HTTPError) else None
            if code == 429 or (code and code >= 500):
                retry_after = exc.headers.get("Retry-After", "") if exc.headers else ""
                wait = int(retry_after) if retry_after.isdigit() else 20 * (attempt + 1)
                wait = min(max(wait, 10), 180)
                print(f"   … 위키백과가 '요청이 너무 많다'고 해서 {wait}초 쉬었다가 다시 합니다 ({attempt + 1}/{retries})")
            else:
                wait = 2 ** attempt
                print(f"   ! 요청 실패({last}). {wait}초 후 다시 시도")
            time.sleep(wait)
    raise RuntimeError(f"위키백과 API 요청이 계속 실패했습니다: {last}")


def check_connection() -> None:
    """시작하자마자 한 번 연결해 보고, 안 되면 이유를 보여 주고 멈춘다."""
    print("위키백과 연결 확인 중…")
    try:
        api({"action": "query", "meta": "siteinfo"})
    except RuntimeError as exc:
        print(f"\n✖ 위키백과에 연결하지 못했습니다.\n  {exc}")
        print("  - 인터넷이 연결돼 있는지 확인해 주세요.")
        print("  - 'HTTP 429' 면 10분쯤 쉬었다가 다시 실행해 주세요(받아 둔 문서는 그대로 이어서 씁니다).")
        print("  - 'HTTP 403' 이면 .env 에 WIKI_CONTACT=본인이메일 을 한 줄 넣고 다시 실행해 보세요.")
        print("  - 'CERTIFICATE' 가 보이면 python -m pip install -r requirements.txt 를 먼저 실행한 뒤 다시 해 보세요.")
        sys.exit(1)
    print("연결 OK\n")


def clean_text(text: str) -> str:
    """참고문헌·외부 링크 같은 꼬리 부분을 잘라내고 빈 줄을 정리한다."""
    match = CUT_RE.search(text)
    if match:
        text = text[: match.start()]
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def slugify(title: str) -> str:
    ascii_title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "_", ascii_title.lower()).strip("_")
    return slug or "doc"


# ------------------------------------------------------------------ 캐시(이어서 하기)
def _cache_path(title: str):
    key = slugify(title)[:60] + "_" + hashlib.md5(title.encode("utf-8")).hexdigest()[:8]
    return config.CACHE_DIR / f"{key}.json"


def _cache_get(title: str):
    path = _cache_path(title)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def _cache_put(title: str, value) -> None:
    path = _cache_path(title)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


# ------------------------------------------------------------------ 위키백과에서 가져오기
def fetch_page(title: str):
    """본문(plain text)·정식 제목·주소·링크를 가져온다. 없는 문서면 None. 한 번 받은 문서는 캐시에서 읽는다."""
    cached = _cache_get(title)
    if cached is not None:
        return cached.get("page")
    if OFFLINE:
        return None
    data = api({
        "action": "query", "prop": "extracts|info|links", "titles": title, "redirects": 1,
        "explaintext": 1, "exsectionformat": "wiki", "inprop": "url", "plnamespace": 0, "pllimit": "max",
    })
    pages = data.get("query", {}).get("pages", [])
    page = pages[0] if pages else {}
    if not page or page.get("missing") or page.get("invalid") or not page.get("extract"):
        _cache_put(title, {"page": None})
        return None
    links = [link["title"] for link in page.get("links", [])]
    cont = data.get("continue")
    while cont and "plcontinue" in cont:  # 링크가 500개를 넘는 문서만 이어서 받는다
        more = api({"action": "query", "prop": "links", "titles": page["title"], "plnamespace": 0,
                    "pllimit": "max", **cont})
        for p in more.get("query", {}).get("pages", []):
            links += [link["title"] for link in p.get("links", [])]
        cont = more.get("continue")
    result = {"title": page["title"], "url": page.get("fullurl", ""), "text": clean_text(page["extract"]),
              "links": links}
    _cache_put(title, {"page": result})
    return result


def search_titles(term: str = "CrossFit", limit: int = 1000) -> list:
    """위키백과 안에서 term 을 언급하는 문서 제목들(관련도 순)."""
    cached = _cache_get(f"__search__{term}")
    if cached is not None:
        return cached["titles"]
    if OFFLINE:
        return []
    titles, offset = [], 0
    while offset < limit:
        data = api({"action": "query", "list": "search", "srsearch": term, "srnamespace": 0,
                    "srlimit": 500, "sroffset": offset, "srprop": ""})
        titles += [r["title"] for r in data.get("query", {}).get("search", [])]
        cont = data.get("continue", {})
        if "sroffset" not in cont:
            break
        offset = cont["sroffset"]
    _cache_put(f"__search__{term}", {"titles": titles})
    return titles


def fetch_aliases(titles: list) -> dict:
    """다른 이름(넘겨주기) → 정식 제목. 링크가 넘겨주기 이름으로 걸려 있어도 연결하기 위해."""
    saved = _cache_get("__aliases__") or {"aliases": {}}
    aliases = dict(saved["aliases"])
    known = set(aliases.values())
    todo = [t for t in titles if t not in known]
    if OFFLINE:
        return aliases
    for i in range(0, len(todo), 50):
        batch, cont = todo[i:i + 50], {}
        while True:
            data = api({"action": "query", "prop": "redirects", "titles": "|".join(batch),
                        "rdnamespace": 0, "rdlimit": "max", **cont})
            for page in data.get("query", {}).get("pages", []):
                for red in page.get("redirects", []):
                    aliases[red["title"]] = page["title"]
            if "continue" in data:
                cont = data["continue"]
            else:
                break
        _cache_put("__aliases__", {"aliases": aliases})
    return aliases


def read_seeds() -> list:
    path = config.DATA_DIR / "seeds.txt"
    seeds = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            seeds.append(line)
    return seeds


def main() -> None:
    global DELAY, OFFLINE
    parser = argparse.ArgumentParser(description="위키백과에서 크로스핏 자료를 모은다")
    parser.add_argument("--target-tokens", type=int, default=0)
    parser.add_argument("--max-docs", type=int, default=300)
    parser.add_argument("--max-tries", type=int, default=400, help="확장 후보를 열어 보는 최대 횟수")
    parser.add_argument("--delay", type=float, default=1.0, help="요청 사이 쉬는 시간(초)")
    parser.add_argument("--min-mentions", type=int, default=1, help="확장 문서가 'CrossFit'을 최소 몇 번 언급해야 하나")
    parser.add_argument("--no-expand", action="store_true")
    parser.add_argument("--offline", action="store_true", help="위키백과에 묻지 않고 data/cache 에 받아 둔 문서만으로 만든다")
    args = parser.parse_args()
    DELAY = args.delay
    OFFLINE = args.offline

    if OFFLINE:
        print("오프라인 모드: data/cache 에 받아 둔 문서만 씁니다.\n")
    else:
        check_connection()
    target = args.target_tokens or int(config.CONTEXT_WINDOW * config.CFG["corpus"]["target_ratio"])
    print(f"모델 {config.MODEL} · 컨텍스트 윈도우 {config.CONTEXT_WINDOW:,} 토큰 → 목표 {target:,} 토큰 이상 모으기")
    print(f"토큰 세는 방법: {token_method()} · 요청 사이 {DELAY}초 쉼 · 받은 문서는 data/cache 에 저장(이어서 하기)\n")

    docs = {}        # 정식 제목 → 문서
    missing, added_by_expansion, rejected = [], [], []
    min_mentions = args.min_mentions
    redirected = {}  # 입력한 제목 → 정식 제목 (넘겨주기)

    def add(title_in: str, origin: str):
        """결과: ('new', 정식제목) / ('dup', 정식제목) / ('missing', None) / ('rejected', 정식제목)"""
        page = fetch_page(title_in)
        if page is None:
            return "missing", None
        if page["title"] in docs:
            return "dup", page["title"]
        if origin == "expand" and page["text"].lower().count(config.CFG["corpus"]["mention_term"].lower()) < min_mentions:
            rejected.append(page["title"])
            return "rejected", page["title"]
        page["tokens"] = count_tokens(page["text"])
        docs[page["title"]] = page
        return "new", page["title"]

    total = lambda: sum(d["tokens"] for d in docs.values())  # noqa: E731

    seeds = read_seeds()
    print(f"[1/3] seeds.txt 문서 {len(seeds)}건 수집")
    for i, title in enumerate(seeds, 1):
        result, canonical = add(title, "seed")
        if canonical and canonical != title:
            redirected[title] = canonical
        if result == "missing":
            missing.append(title)
        label = {"new": "ok", "dup": f"이미 있음({canonical} 로 넘겨짐)", "missing": "없음(건너뜀)"}[result]
        print(f"   {i:>3}/{len(seeds)} {title} — {label}   누적 {total():,} 토큰")

    if not args.no_expand and total() < target:
        print(f"\n[2/3] 목표 {target:,} 토큰까지 확장: 'CrossFit'을 언급하는 문서 중 이미 모은 문서가 많이 링크하는 것부터")
        mentions = search_titles(config.CFG["corpus"]["mention_term"])
        rank = {t: i for i, t in enumerate(mentions)}
        tried = set(docs) | set(missing)
        tries = 0
        available = {t for t in mentions if _cache_path(t).exists()} if OFFLINE else None
        inlinks = {}
        for doc in docs.values():
            for link in doc["links"]:
                inlinks[link] = inlinks.get(link, 0) + 1
        while total() < target and len(docs) < args.max_docs and tries < args.max_tries:
            candidates = [t for t in mentions if t not in tried and not SKIP_TITLE_RE.search(t)
                          and (available is None or t in available)]
            if not candidates:
                break
            # 점수: 이미 모은 문서들이 링크한 횟수 ×10 + 제목에 CrossFit + 검색 관련도
            best = max(candidates, key=lambda t: (inlinks.get(t, 0) * 10 + (8 if "crossfit" in t.lower() else 0)
                                                  - rank[t] / 100))
            tried.add(best)
            tries += 1
            result, canonical = add(best, "expand")
            if canonical:
                tried.add(canonical)
                if canonical != best:
                    redirected[best] = canonical
            if result == "new":
                for link in docs[canonical]["links"]:
                    inlinks[link] = inlinks.get(link, 0) + 1
                added_by_expansion.append(canonical)
                print(f"   + {canonical}   누적 {total():,} 토큰 ({len(docs)}건)")
    else:
        print("\n[2/3] 확장 생략")

    print("\n[3/3] 문서끼리의 링크 정리")
    aliases = fetch_aliases(list(docs))
    for alias, canonical in redirected.items():
        aliases.setdefault(alias, canonical)
    ids, used = {}, set()
    for title in docs:
        slug = base = slugify(title)
        n = 2
        while slug in used:
            slug, n = f"{base}_{n}", n + 1
        used.add(slug)
        ids[title] = slug

    def resolve(link_title: str):
        canonical = link_title if link_title in docs else aliases.get(link_title)
        return ids.get(canonical) if canonical else None

    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    links_map, out_docs = {}, []
    for title, doc in docs.items():
        doc_id = ids[title]
        linked = sorted({resolve(link) for link in doc["links"]} - {None, doc_id})
        links_map[doc_id] = linked
        kind = "disambiguation" if DISAMBIG_RE.search(doc["text"][:400]) else "article"
        out_docs.append({"id": doc_id, "title": title, "url": doc["url"], "source": "wikipedia-en", "kind": kind,
                         "chars": len(doc["text"]), "tokens": doc["tokens"], "links": linked, "text": doc["text"]})

    total_chars = sum(len(d["text"]) for d in docs.values())
    meta = {
        "name": "crossfit-wikipedia",
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": config.CFG["corpus"]["source"],
        "doc_count": len(docs),
        "total_chars": total_chars,
        "total_tokens": total(),
        "token_method": token_method(),
        "model": config.MODEL,
        "context_window": config.CONTEXT_WINDOW,
        "ratio_to_context": round(total() / config.CONTEXT_WINDOW, 2),
        "link_edges": sum(len(v) for v in links_map.values()),
        "missing_seeds": missing,
        "added_by_expansion": added_by_expansion,
        "rejected_candidates": len(rejected),
        "api_requests_this_run": _REQUESTS["n"],
        "mode": "offline(cache)" if OFFLINE else "online",
        "min_mentions": min_mentions,
    }
    config.CORPUS_PATH.write_text(json.dumps({"meta": meta, "docs": out_docs}, ensure_ascii=False), encoding="utf-8")

    print("\n===== 수집 결과 =====")
    print(f"문서 {meta['doc_count']}건 · {total_chars:,}자 · {meta['total_tokens']:,} 토큰 ({meta['token_method']})")
    print(f"컨텍스트 윈도우 {config.CONTEXT_WINDOW:,} 토큰의 {meta['ratio_to_context']}배")
    print(f"링크 {meta['link_edges']:,}개 · seeds 중 없는 문서 {len(missing)}건 · 확장으로 추가 {len(added_by_expansion)}건")
    if meta["ratio_to_context"] <= 1:
        print("⚠ 아직 컨텍스트 윈도우를 넘지 못했습니다. --max-docs 를 늘려 다시 실행해 보세요.")
    print("다음 단계: python corpus_stats.py")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\n중단했습니다. 다시 실행하면 받아 둔 문서부터 이어서 합니다.")
    except RuntimeError as exc:
        sys.exit(f"\n✖ {exc}\n10분쯤 쉬었다가 다시 실행해 주세요. 받아 둔 문서는 data/cache 에 있어 이어서 합니다.")
