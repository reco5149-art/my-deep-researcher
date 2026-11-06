"""build_corpus.py 를 인터넷 없이 시험한다(가짜 위키백과 응답). 실행: python -m tests.test_build_corpus"""
import io
import json
import sys
import tempfile
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import build_corpus  # noqa: E402
import config  # noqa: E402

PAGES = {
    "CrossFit": ("CrossFit is a fitness program founded by Greg Glassman. CrossFit Games began in 2007.\n\n"
                 "== History ==\nCrossFit grew fast.\n\n== References ==\n[1] cut me", ["Greg Glassman", "CrossFit Games", "Rich Froning", "Santa Cruz"]),
    "Greg Glassman": ("Greg Glassman founded CrossFit in 2000. CrossFit CrossFit.", ["CrossFit"]),
    "CrossFit Games": ("The CrossFit Games started 2007. CrossFit athletes compete.", ["CrossFit", "Rich Froning Jr."]),
    "Rich Froning Jr.": ("Rich Froning Jr. won the CrossFit Games four times. CrossFit legend.", ["CrossFit Games"]),
    "Santa Cruz": ("Santa Cruz is a city in California.", []),
}
REDIRECTS = {"Rich Froning": "Rich Froning Jr."}


def fake_api(params, retries=5):
    if params.get("meta") == "siteinfo":
        return {"query": {"general": {"sitename": "Wikipedia"}}}
    if params.get("list") == "search":
        return {"query": {"search": [{"title": t} for t in ["CrossFit Games", "Rich Froning", "Santa Cruz"]]}}
    titles = params["titles"].split("|")
    prop = params["prop"]
    if prop.startswith("extracts"):
        t = REDIRECTS.get(titles[0], titles[0])
        if t not in PAGES:
            return {"query": {"pages": [{"title": t, "missing": True}]}}
        return {"query": {"pages": [{"title": t, "fullurl": f"https://en.wikipedia.org/wiki/{t}", "extract": PAGES[t][0],
                                     "links": [{"title": link} for link in PAGES[t][1]]}]}}
    if prop == "redirects":
        pages = []
        for t in titles:
            reds = [{"title": a} for a, c in REDIRECTS.items() if c == t]
            pages.append({"title": t, "redirects": reds})
        return {"query": {"pages": pages}}
    raise AssertionError(params)


def test_rate_limit_retry():
    """429 를 한 번 받으면 쉬었다가 다시 시도해야 한다."""
    calls = {"n": 0}

    class Resp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake_urlopen(req, timeout=30, context=None):
        calls["n"] += 1
        if calls["n"] == 1:
            raise urllib.error.HTTPError(req.full_url, 429, "Too Many Requests", {"Retry-After": "1"}, io.BytesIO(b"slow down"))
        return Resp(b'{"ok": true}')

    real_urlopen, real_sleep = build_corpus.urllib.request.urlopen, build_corpus.time.sleep
    build_corpus.urllib.request.urlopen = fake_urlopen
    build_corpus.time.sleep = lambda s: None
    try:
        assert build_corpus.api({"action": "query"}) == {"ok": True}
        assert calls["n"] == 2
    finally:
        build_corpus.urllib.request.urlopen, build_corpus.time.sleep = real_urlopen, real_sleep
    print("OK 429 재시도")


def run():
    test_rate_limit_retry()
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "seeds.txt").write_text("CrossFit\nGreg Glassman\nNo Such Page\n", encoding="utf-8")
        config.DATA_DIR = tmp
        config.CACHE_DIR = tmp / "cache"
        config.CORPUS_PATH = tmp / "corpus.json"
        real_api = build_corpus.api
        build_corpus.api = fake_api
        try:
            sys.argv = ["build_corpus.py", "--target-tokens", "10000", "--delay", "0"]
            build_corpus.main()
            # 두 번째 실행은 캐시에서 읽어야 한다(위키백과에 다시 묻지 않음)
            build_corpus.api = lambda *a, **k: (_ for _ in ()).throw(AssertionError("캐시를 안 썼다")) \
                if a and a[0].get("prop", "").startswith("extracts") else fake_api(*a, **k)
            build_corpus.main()
            # 오프라인: 위키백과에 전혀 묻지 않고 캐시만으로 같은 결과를 만들어야 한다
            build_corpus.api = real_api
            sys.argv = ["build_corpus.py", "--target-tokens", "10000", "--delay", "0", "--offline"]
            build_corpus.main()
            build_corpus.OFFLINE = False
        finally:
            build_corpus.api = real_api
        data = json.loads((tmp / "corpus.json").read_text(encoding="utf-8"))
        docs, meta = data["docs"], data["meta"]
        by_id = {d["id"]: d for d in docs}
        assert "crossfit" in by_id and "crossfit_games" in by_id, by_id.keys()
        assert "santa_cruz" not in by_id, "CrossFit을 언급하지 않는 문서는 확장에서 빠져야 한다"
        assert "rich_froning_jr" in by_id
        assert "rich_froning_jr" in by_id["crossfit"]["links"], "넘겨주기 이름(Rich Froning) 링크도 연결돼야 한다"
        assert "cut me" not in by_id["crossfit"]["text"], "References 이후는 잘려야 한다"
        assert meta["missing_seeds"] == ["No Such Page"]
        print("OK build_corpus:", {d["id"]: d["links"] for d in docs})


if __name__ == "__main__":
    run()
