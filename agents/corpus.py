"""자료 세트(코퍼스)를 읽고, 문서를 '쪽' 단위로 잘라 돌려준다."""
import json
import math
import re
from collections import Counter
from pathlib import Path

import config


# '…may refer to:', '… is a surname' 같은 동음이의(목록) 문서. 내용이 없어 시작 자료로 쓰면 안 된다.
DISAMBIG_RE = re.compile(r"(may refer to|may also refer to|is a surname|is a given name|is a feminine given name|"
                         r"is a masculine given name)", re.I)


class CorpusMissing(FileNotFoundError):
    pass


class Corpus:
    def __init__(self, docs: list, name: str = "corpus"):
        self.name = name
        self._docs = {d["id"]: d for d in docs}
        self._order = [d["id"] for d in docs]
        self._in = Counter(t for d in docs for t in d.get("links", []))
        self.meta = {}
        self._disambig = {d["id"] for d in docs if d.get("kind") == "disambiguation" or DISAMBIG_RE.search(d["text"][:400])}

    @classmethod
    def load(cls, path: Path = None) -> "Corpus":
        """data/corpus.json ({"meta":..., "docs":[...]}) 또는 docs.jsonl(한 줄에 문서 하나)을 읽는다."""
        path = Path(path) if path else config.CORPUS_PATH
        if not path.exists():
            raise CorpusMissing(
                f"{path} 이 없습니다. 먼저 'python build_corpus.py' 를 실행해 자료를 모아 주세요.")
        text = path.read_text(encoding="utf-8")
        if path.suffix == ".jsonl":
            docs, meta = [json.loads(line) for line in text.splitlines() if line.strip()], {}
        else:
            data = json.loads(text)
            docs, meta = data["docs"], data.get("meta", {})
        corpus = cls(docs, name=meta.get("name") or path.stem)
        corpus.meta = meta
        return corpus

    # ---- 기본 조회 ----
    def ids(self) -> list:
        return list(self._order)

    def exists(self, doc_id: str) -> bool:
        return doc_id in self._docs

    def title(self, doc_id: str) -> str:
        return self._docs[doc_id]["title"]

    def url(self, doc_id: str) -> str:
        return self._docs[doc_id].get("url", "")

    def text(self, doc_id: str) -> str:
        return self._docs[doc_id]["text"]

    def links(self, doc_id: str) -> list:
        return [t for t in self._docs[doc_id].get("links", []) if t in self._docs]

    def is_disambiguation(self, doc_id: str) -> bool:
        return doc_id in self._disambig

    def in_degree(self, doc_id: str) -> int:
        return self._in.get(doc_id, 0)

    @property
    def total_chars(self) -> int:
        return sum(len(d["text"]) for d in self._docs.values())

    # ---- 쪽 단위 읽기 ----
    def parts(self, doc_id: str, page_chars: int) -> int:
        return max(1, math.ceil(len(self.text(doc_id)) / page_chars))

    def page(self, doc_id: str, part: int, page_chars: int) -> str:
        text = self.text(doc_id)
        start = (part - 1) * page_chars
        return text[start:start + page_chars]

    # ---- 코디네이터가 보는 목록(본문은 보지 않는다) ----
    def catalog(self, page_chars: int, lead_chars: int = 220) -> list:
        rows = []
        for doc_id in self._order:
            if doc_id in self._disambig:  # 동음이의 문서는 코디네이터 목록에서 뺀다
                continue
            text = self.text(doc_id)
            lead = " ".join(text[:lead_chars].split())
            rows.append({
                "id": doc_id,
                "title": self.title(doc_id),
                "chars": len(text),
                "parts": self.parts(doc_id, page_chars),
                "out_links": len(self.links(doc_id)),
                "in_links": self.in_degree(doc_id),
                "lead": lead,
            })
        return rows

    def catalog_text(self, page_chars: int) -> str:
        lines = []
        for row in self.catalog(page_chars):
            lines.append(f"- {row['id']} | {row['title']} | {row['chars']:,}자({row['parts']}쪽) | "
                         f"링크 out {row['out_links']}/in {row['in_links']} | {row['lead']}")
        return "\n".join(lines)
