"""1단계 확인 — 자료 총량이 컨텍스트 윈도우를 넘는지, 링크가 얼마나 이어져 있는지 숫자로 보인다.

실행:  python corpus_stats.py
결과:  화면 출력 + data/corpus_stats.json (웹 화면이 읽는다)
"""
import json
import sys
from collections import Counter

import config
from agents.corpus import Corpus, CorpusMissing
from tokens import count_tokens, method as token_method


def largest_component(corpus: Corpus) -> int:
    """링크를 방향 없이 봤을 때 가장 큰 연결 덩어리의 문서 수."""
    neighbors = {d: set() for d in corpus.ids()}
    for d in corpus.ids():
        for t in corpus.links(d):
            neighbors[d].add(t)
            neighbors[t].add(d)
    seen, best = set(), 0
    for start in neighbors:
        if start in seen:
            continue
        stack, size = [start], 0
        seen.add(start)
        while stack:
            cur = stack.pop()
            size += 1
            for nxt in neighbors[cur] - seen:
                seen.add(nxt)
                stack.append(nxt)
        best = max(best, size)
    return best


def compute_stats(corpus: Corpus, context_window: int = config.CONTEXT_WINDOW) -> dict:
    total_chars = sum(len(corpus.text(d)) for d in corpus.ids())
    total_tokens = sum(count_tokens(corpus.text(d)) for d in corpus.ids())
    method = token_method()
    meta = getattr(corpus, "meta", {}) or {}
    if (not method.startswith("tiktoken") and str(meta.get("token_method", "")).startswith("tiktoken")
            and meta.get("doc_count") == len(corpus.ids())):
        # 이 PC 에 tiktoken 인코딩이 없으면, 수집할 때 tiktoken 으로 센 값을 그대로 쓴다
        total_tokens, method = meta["total_tokens"], meta["token_method"] + " (corpus.json 기록값)"
    indeg = Counter(t for d in corpus.ids() for t in corpus.links(d))
    out_degrees = [len(corpus.links(d)) for d in corpus.ids()]
    return {
        "doc_count": len(corpus.ids()),
        "total_chars": total_chars,
        "total_tokens": total_tokens,
        "token_method": method,
        "model": config.MODEL,
        "context_window": context_window,
        "ratio_to_context": round(total_tokens / context_window, 2),
        "exceeds_context": total_tokens > context_window,
        "link_edges": sum(out_degrees),
        "avg_out_links": round(sum(out_degrees) / max(len(out_degrees), 1), 1),
        "docs_without_out_links": sum(1 for n in out_degrees if n == 0),
        "docs_without_in_links": sum(1 for d in corpus.ids() if indeg[d] == 0),
        "largest_component": largest_component(corpus),
        "top_in_links": [[d, corpus.title(d), n] for d, n in indeg.most_common(10)],
        "largest_docs": sorted(([d, corpus.title(d), len(corpus.text(d))] for d in corpus.ids()),
                               key=lambda x: -x[2])[:10],
    }


def main() -> None:
    try:
        corpus = Corpus.load()
    except CorpusMissing as exc:
        sys.exit(str(exc))
    stats = compute_stats(corpus)
    (config.DATA_DIR / "corpus_stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=1), encoding="utf-8")

    print("===== 자료 세트 =====")
    print(f"문서 수            {stats['doc_count']:>12,} 건")
    print(f"총 글자 수         {stats['total_chars']:>12,} 자")
    print(f"총 토큰 수         {stats['total_tokens']:>12,} 토큰  ({stats['token_method']})")
    print(f"컨텍스트 윈도우    {stats['context_window']:>12,} 토큰  ({stats['model']})")
    verdict = "넘는다 → 한 에이전트가 전부 읽을 수 없다" if stats["exceeds_context"] else "넘지 않는다 → 이 구조를 쓸 이유가 약하다"
    print(f"배수               {stats['ratio_to_context']:>12} 배  → {verdict}")
    print("\n===== 링크 (links) =====")
    print(f"링크 수            {stats['link_edges']:>12,} 개 (문서당 평균 {stats['avg_out_links']}개)")
    print(f"나가는 링크 없는 문서 {stats['docs_without_out_links']}건 · 들어오는 링크 없는 문서 {stats['docs_without_in_links']}건")
    print(f"가장 큰 연결 덩어리  {stats['largest_component']} / {stats['doc_count']} 건")
    print("많이 가리켜지는 문서:", ", ".join(f"{t}({n})" for _, t, n in stats["top_in_links"][:5]))


if __name__ == "__main__":
    main()
