"""엔진 시험(인터넷·API 없이). 실행: python -m tests.test_pipeline"""
import shutil
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import config  # noqa: E402
from agents.coordinator import merge_drafts, validate_plan  # noqa: E402
from agents.corpus import Corpus  # noqa: E402
from tests.make_fixture import build  # noqa: E402


def use_tmp_output(tmp: Path) -> None:
    config.OUTPUT_DIR = tmp / "output"
    config.TRACES_DIR = config.OUTPUT_DIR / "traces"
    config.REPORTS_DIR = config.OUTPUT_DIR / "reports"
    config.RUNS_JSONL = config.OUTPUT_DIR / "runs.jsonl"
    config.ABLATION_JSON = config.OUTPUT_DIR / "ablation.json"


def test_validate_plan(corpus):
    s = config.make_settings("full", total_reads=20)
    plan = {"sections": [
        {"id": "S1", "role_name": "기원·방법론", "title": "서론", "role": "r", "scope_in": "", "scope_out": "", "start_docs": ["crossfit"], "budget": 3},
        {"id": "S2", "role_name": "대회·선수", "title": "게임즈", "role": "r", "scope_in": "", "scope_out": "", "start_docs": ["crossfit_gamez"], "budget": 3},
        {"id": "S3", "role_name": "없는 역할", "title": "선수", "role": "r", "scope_in": "", "scope_out": "", "start_docs": ["crossfit"], "budget": 30},
    ]}
    errors, _ = validate_plan(plan, corpus, s)
    joined = "\n".join(errors)
    assert "형식 단위" in joined, errors
    assert "crossfit_gamez" in joined, "지어낸 문서 ID를 잡아야 한다"
    assert "한도" in joined, "예산 합계 초과를 잡아야 한다"
    assert "겹친다" in joined, "시작 자료가 겹치는 절을 잡아야 한다"
    assert "역할 명단에 없다" in joined, "명단에 없는 역할을 잡아야 한다"
    print("OK validate_plan:", len(errors), "errors")


def test_merge():
    v1 = {"markdown": "가 [d:a]\n\n나 [d:b]", "cited": ["a", "b"], "unread_cited": [], "status": "insufficient"}
    good = {"markdown": "가 [d:a]\n\n나 [d:b]\n\n다 [d:c]", "cited": ["a", "b", "c"], "unread_cited": [], "status": "sufficient"}
    bad = {"markdown": "나 [d:b]\n\n다 [d:c]", "cited": ["b", "c"], "unread_cited": [], "status": "sufficient"}
    merged, decision, _ = merge_drafts(v1, good)
    assert decision == "교체" and merged["cited"] == ["a", "b", "c"]
    merged, decision, reason = merge_drafts(v1, bad)
    assert decision == "보강", reason
    assert "[d:a]" in merged["markdown"] and "[d:c]" in merged["markdown"], "이전 인용을 지키고 새 문단만 붙여야 한다"
    print("OK merge:", reason)


def test_cite_numbering():
    from agents.cite import extract_ids, to_numbered
    n = {"a": 1, "b": 2}
    assert to_numbered("가[d:a][d:a] 나[d:a, d:b] 다(d:b)", n) == "가[1] 나[1][2] 다[2]"
    assert extract_ids("가 (d:a) 나 [d:b; a]") == ["a", "b", "a"]
    assert to_numbered("(2010) 그대로", n) == "(2010) 그대로"
    print("OK 인용 번호: 겹친 [1][1] 정리, (d:..) 표기도 인정")


def test_variants(corpus_path):
    from ablation import latest_traces, write_outputs
    from baseline import run_baseline
    from graph import run_question
    corpus = Corpus.load(corpus_path)
    runs = {}
    q = "크로스핏은 어떻게 탄생해 어떤 과정을 거쳐 지금에 이르렀나?"
    for variant in ["full", "no_peers", "no_recheck", "no_links", "single"]:
        if variant == "single":
            t = run_baseline(q, "QT", practice=True, corpus=corpus, total_reads=10, recheck_reserve=4)
        else:
            s = config.make_settings(variant, practice=True, total_reads=10, recheck_reserve=4)
            t = run_question(q, "QT", s, corpus=corpus)
        runs[variant] = t
        m = t["metrics"]
        assert not m["alarms_fired"], (variant, m["alarms_fired"])
        assert (config.REPORTS_DIR / f"{t['run_id']}.md").exists()
        print(f"OK {variant}: 읽기 {m['raw']['reads_used']}/{m['raw']['total_budget']}, 인용 문서 {m['values']['cited_docs']}")
    assert runs["single"]["plan"]["sections"] == runs["full"]["plan"]["sections"], "대조군은 같은 목차를 써야 한다"
    assert runs["no_peers"]["plan_source"] != "new"
    assert runs["full"]["meters"]["코디네이터"]["seen_chars"] < corpus.total_chars, "코디네이터는 본문을 읽지 않는다"
    assert runs["single"]["single"]["reads"]["budget"] == runs["single"]["settings"]["total_reads"], "대조군은 같은 총예산"
    assert runs["full"]["recheck"]["rounds"], "점검 기록이 있어야 한다"
    lines = config.RUNS_JSONL.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 5, "runs.jsonl 에 5줄"
    write_outputs("QT", latest_traces("QT", True), corpus)
    assert config.ABLATION_JSON.exists()
    print("OK ablation 표·비교 문서")


def test_parallel(corpus_path):
    """서브에이전트들이 LangGraph Send 로 동시에 도는지(순서대로 돌면 시간이 절 수배로 늘어난다)."""
    from agents import fake
    from graph import run_question
    corpus = Corpus.load(corpus_path)
    real = fake.researcher_step

    def slow(agent, tool_choice):
        time.sleep(0.15)
        return real(agent, tool_choice)

    fake.researcher_step = slow
    try:
        s = config.make_settings("no_recheck", practice=True, total_reads=12)
        t0 = time.time()
        t = run_question("크로스핏의 역사", "QP", s, corpus=corpus, reuse_plan=False)
        took = time.time() - t0
    finally:
        fake.researcher_step = real
    n = len(t["plan"]["sections"])
    calls = sum(v["calls"] for k, v in t["meters"].items() if k.startswith("리서처"))
    serial = calls * 0.15
    assert n >= 2 and took < serial * 0.75, (n, took, serial)
    print(f"OK 병렬: 절 {n}개, 걸린 시간 {took:.2f}s < 순차 추정 {serial:.2f}s")


def main():
    tmp = Path(tempfile.mkdtemp())
    try:
        use_tmp_output(tmp)
        corpus_path = build(tmp / "corpus")
        corpus = Corpus.load(corpus_path)
        test_validate_plan(corpus)
        test_merge()
        test_cite_numbering()
        test_variants(corpus_path)
        test_parallel(corpus_path)
        print("모든 시험 통과")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
