"""절 원고를 코드로 그대로 이어 붙이고, 코디네이터가 쓴 서론·연결 문장·맺음말을 끼워 보고서를 만든다.

절 본문을 모델에게 다시 쓰게 하지 않는 이유: 다시 쓰는 과정에서 인용이 빠지거나 옮겨 붙기 때문이다.
"""
from .cite import to_numbered, unique_ids


def assemble(question: str, sections: list, finals: dict, frame: dict, corpus, readers: dict) -> dict:
    trans = {t.get("section_id"): t.get("sentence", "") for t in frame.get("transitions", [])}
    parts = [f"# {frame.get('title') or question}", frame.get("intro", "").strip()]
    for i, s in enumerate(sections, 1):
        final = finals.get(s["id"]) or {}
        body = (final.get("markdown") or "").strip() or "_(이 절은 제출된 원고가 없습니다)_"
        parts.append(f"## {i}. {s['title']}")
        if trans.get(s["id"]):
            parts.append(f"*{trans[s['id']].strip()}*")
        parts.append(body)
    conclusion = frame.get("conclusion", "").strip()
    parts += ["## 맺음말", conclusion]
    body_d = "\n\n".join(p for p in parts if p)

    order = unique_ids(body_d)
    numbering = {d: n for n, d in enumerate(order, 1)}
    citers = {}
    for s in sections:
        for d in unique_ids((finals.get(s["id"]) or {}).get("markdown", "")):
            citers.setdefault(d, []).append(s["id"])
    ref_lines = ["## 참고문헌"]
    for d, n in numbering.items():
        if corpus.exists(d):
            who_read = ", ".join(readers.get(d, [])) or "아무도 안 읽음 ⚠"
            who_cited = ", ".join(citers.get(d, [])) or "맺음말"
            ref_lines.append(f"[{n}] {corpus.title(d)} — English Wikipedia. {corpus.url(d)}  "
                             f"(읽은 쪽: {who_read} / 인용한 절: {who_cited})")
        else:
            ref_lines.append(f"[{n}] ⚠ 자료에 없는 문서 ID: {d}")
    markdown = to_numbered(body_d, numbering) + "\n\n" + "\n".join(ref_lines) + "\n"
    return {
        "markdown": markdown,
        "markdown_d": body_d,
        "conclusion_d": conclusion,
        "numbering": numbering,
        "frame": frame,
    }
