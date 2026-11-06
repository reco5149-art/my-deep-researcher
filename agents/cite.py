"""[d:문서ID] 인용 표시를 다루는 함수들."""
import re

# [d:abc] 또는 [d:abc, d:def] / [d:abc; def] 모두 인정. 모델이 가끔 쓰는 (d:abc) 도 같은 인용으로 본다.
CITE_BLOCK_RE = re.compile(r"[\[(]d:\s*([^\])]+)[\])]")
YEAR_RE = re.compile(r"(?<!\d)(1[89]\d\d|20[0-4]\d)(?!\d)")
SENT_SPLIT_RE = re.compile(r"(?<=[.!?。])\s+|(?<=다\.)\s*|\n+")


def ids_in_block(block: str) -> list:
    out = []
    for piece in re.split(r"[,;]", block):
        piece = piece.strip()
        if piece.startswith("d:"):
            piece = piece[2:].strip()
        if piece:
            out.append(piece)
    return out


def extract_ids(text: str) -> list:
    """등장 순서대로 인용된 문서 ID (중복 포함)."""
    ids = []
    for m in CITE_BLOCK_RE.finditer(text or ""):
        ids.extend(ids_in_block(m.group(1)))
    return ids


def unique_ids(text: str) -> list:
    seen, out = set(), []
    for i in extract_ids(text):
        if i not in seen:
            seen.add(i)
            out.append(i)
    return out


def split_sentences(text: str) -> list:
    """대략적인 문장 나누기(한국어 '~다.' 와 영어 마침표 기준)."""
    parts = []
    for para in (text or "").split("\n"):
        para = para.strip()
        if not para:
            continue
        buf = ""
        for piece in re.split(r"((?:[\[(]d:[^\])]+[\])])+)", para):
            buf += piece
            if piece.startswith(("[d:", "(d:")):
                parts.append(buf.strip())
                buf = ""
        if buf.strip():
            parts.append(buf.strip())
    return parts


def cited_sentences(text: str) -> list:
    """[(문장, [인용 ID...])] — 인용이 붙은 문장만."""
    out = []
    for sent in split_sentences(text):
        ids = extract_ids(sent)
        if ids:
            out.append((CITE_BLOCK_RE.sub("", sent).strip(), ids))
    return out


def paragraphs(text: str) -> list:
    return [p.strip() for p in re.split(r"\n\s*\n", text or "") if p.strip()]


def to_numbered(text: str, numbering: dict) -> str:
    """[d:a][d:b] → [1][2]. 번호표에 없는 ID는 [?a] 로 남긴다. 바로 붙은 같은 번호([1][1])는 하나로 줄인다."""
    def repl(m):
        ids = ids_in_block(m.group(1))
        return "".join(f"[{numbering[i]}]" if i in numbering else f"[?{i}]" for i in ids)
    out = CITE_BLOCK_RE.sub(repl, text or "")
    return re.sub(r"(\[\??[^\[\]\s]+\])(?:\s*\1)+", r"\1", out)
