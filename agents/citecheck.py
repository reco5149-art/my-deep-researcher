"""인용 대조 도우미: 인용이 붙은 문장마다, 인용된 문서 원문에서 가장 그럴듯한 대목을 찾아 나란히 보여 준다.

판정은 하지 않는다. '읽은 문서를 엉뚱한 문장에 갖다 붙였는지'는 사람이 이 대목을 보고 판단한다.
단서로 쓰는 것: 문장 속 연도·숫자·영문 고유명사.
"""
import random
import re

from .cite import YEAR_RE, cited_sentences

LATIN_RE = re.compile(r"[A-Za-z][A-Za-z.\-']{2,}")
NUM_RE = re.compile(r"\d[\d,.]*\d|\d")


def clues(sentence: str) -> list:
    terms = set(YEAR_RE.findall(sentence))
    terms |= {w.strip(".-'") for w in LATIN_RE.findall(sentence) if len(w.strip(".-'")) >= 3}
    for num in NUM_RE.findall(sentence):
        digits = num.replace(",", "")
        if len(digits) >= 2 and not YEAR_RE.fullmatch(digits):
            terms.add(num)
            if "," in num:
                terms.add(digits)
    return sorted(terms, key=len, reverse=True)


def best_snippet(text: str, terms: list, radius: int = 260):
    if not terms:
        return None, []
    low = text.lower()
    best, best_hits = None, []
    for term in terms:
        for m in re.finditer(re.escape(term.lower()), low):
            start, end = max(0, m.start() - radius), min(len(text), m.end() + radius)
            window = low[start:end]
            hits = [t for t in terms if t.lower() in window]
            if len(hits) > len(best_hits):
                best, best_hits = (start, end), hits
    if best is None:
        return None, []
    start, end = best
    snippet = ("…" if start else "") + " ".join(text[start:end].split()) + ("…" if end < len(text) else "")
    return snippet, best_hits


def check_report(markdown_d: str, corpus) -> list:
    rows = []
    for sentence, ids in cited_sentences(markdown_d):
        terms = clues(sentence)
        for doc_id in dict.fromkeys(ids):
            if not corpus.exists(doc_id):
                rows.append({"sentence": sentence, "doc": doc_id, "title": "(자료에 없음)", "snippet": None,
                             "clues": terms, "hits": []})
                continue
            snippet, hits = best_snippet(corpus.text(doc_id), terms)
            rows.append({"sentence": sentence, "doc": doc_id, "title": corpus.title(doc_id), "snippet": snippet,
                         "clues": terms, "hits": hits})
    return rows


def sample(rows: list, k: int = 5, seed: int = 7) -> list:
    rng = random.Random(seed)
    rows = list(rows)
    rng.shuffle(rows)
    return rows[:k]
