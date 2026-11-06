"""단일 에이전트 대조군 — 예산을 맞춘다.

    python baseline.py --q Q4              Q4 의 '기본' 실행과 같은 목차·시작 자료·총예산으로 혼자 쓴다
    python baseline.py --q Q4 --practice

맞추는 것: 같은 자료(data/corpus.json) · 같은 모델 · 같은 도구(read_doc / list_links / submit_section)
          · 같은 목차와 시작 자료(기본 실행의 것을 재사용) · 같은 총 읽기 예산(config.json 의 total_reads)
확인하는 것: 대조군이 예산을 다 썼는가. 예산의 90% 미만으로 끝내려 하면 코드가 안 읽은 자료를 보여 주며
            돌려보내고(최대 6회), 그래도 멈추면 '대조군 예산 미소진' 경보가 울린다.
            중간에 멈춘 대조군을 이기는 것은 상대를 묶어 둔 비교이기 때문이다.
"""
import argparse
import sys

import config
from agents.corpus import Corpus, CorpusMissing
from graph import find_reusable_plan, print_metrics, resolve_question, run_question


def run_baseline(question: str, qid: str, practice: bool = False, corpus: Corpus = None, progress=None, **overrides) -> dict:
    corpus = corpus or Corpus.load()
    plan, source = find_reusable_plan(qid, practice, corpus.name)
    if plan is None and progress:
        progress("※ 같은 질문의 기본 실행이 없어 목차를 새로 짭니다. 공정한 비교를 위해 graph.py 를 먼저 실행하세요.")
    settings = config.make_settings("single", practice=practice, **overrides)
    return run_question(question, qid, settings, corpus=corpus, progress=progress, plan=plan, plan_source=source)


def main() -> None:
    p = argparse.ArgumentParser(description="단일 에이전트 대조군")
    p.add_argument("--q")
    p.add_argument("--question")
    p.add_argument("--practice", action="store_true")
    p.add_argument("--corpus")
    args = p.parse_args()
    if not (args.q or args.question):
        sys.exit("질문을 고르세요: python baseline.py --q Q4")
    qid, question = resolve_question(args.q, args.question)
    try:
        corpus = Corpus.load(args.corpus) if args.corpus else Corpus.load()
    except CorpusMissing as exc:
        sys.exit(str(exc))
    print(f"▶ {qid} · {config.VARIANT_LABELS['single']}")
    t = run_baseline(question, qid, practice=args.practice, corpus=corpus, progress=print)
    print_metrics(t)
    use = t["metrics"]["values"]["budget_use"]
    print(f"\n예산 확인: {use:.0%} 사용 — " + ("공정한 비교" if use >= 0.9 else "90% 미만: 이 비교는 상대를 묶어 둔 비교일 수 있다"))


if __name__ == "__main__":
    main()
