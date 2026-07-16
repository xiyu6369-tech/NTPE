from __future__ import annotations

import platform
import statistics
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.shared.evidence import write_canonical_json
from core.translation_intelligence_corpus.offline_quality_gate import _default_context, evaluate_regression_suite, evaluate_translation_candidate
from core.translation_intelligence_corpus.quality_gate_models import TranslationCandidate


OUTPUT = ROOT / "artifacts/tic_batch7/OFFLINE_QUALITY_GATE_PERFORMANCE.json"


def _median_ms(function, warmups: int, iterations: int) -> float:
    for _ in range(warmups):
        function()
    values = []
    for _ in range(iterations):
        started = time.perf_counter_ns()
        function()
        values.append((time.perf_counter_ns() - started) / 1_000_000)
    return statistics.median(values)


def run_benchmark() -> dict:
    subject, lexical = _default_context().regressions
    single = lambda: evaluate_translation_candidate(source_text=subject["source_text"], translation_text=subject["approved_translation"], applicable_regression_ids=(subject["regression_id"],))
    candidates = (
        TranslationCandidate("B7-BENCH-S", subject["source_text"], subject["approved_translation"], case_id=subject["case_id"], failure_case_id=subject["failure_case_id"], metadata={"alignment_id": subject["alignment_id"]}),
        TranslationCandidate("B7-BENCH-L", lexical["source_text"], lexical["approved_translation"], case_id=lexical["case_id"], failure_case_id=lexical["failure_case_id"], metadata={"alignment_id": lexical["alignment_id"]}),
    )
    suite = lambda: evaluate_regression_suite(candidates=candidates)
    hundred = tuple(candidates[index % 2] for index in range(100))
    batch = lambda: evaluate_regression_suite(candidates=hundred)
    warmups, iterations = 50, 300
    timings = {
        "single_candidate_median_ms": _median_ms(single, warmups, iterations),
        "two_regression_suite_median_ms": _median_ms(suite, warmups, iterations),
        "one_hundred_candidate_batch_median_ms": _median_ms(batch, 10, 30),
    }
    passed = timings["single_candidate_median_ms"] < 2 and timings["two_regression_suite_median_ms"] < 5 and timings["one_hundred_candidate_batch_median_ms"] < 250
    return {"schema_version": "tic.batch7.offline-quality-gate-performance.v1", "python_version": sys.version.split()[0], "platform": platform.platform(), "iterations": {"single": iterations, "suite": iterations, "batch_100": 30}, "warmups": {"single": warmups, "suite": warmups, "batch_100": 10}, "median_timings": timings, "thresholds_ms": {"single_candidate": 2, "two_regression_suite": 5, "one_hundred_candidate_batch": 250}, "provider_requests": 0, "network_requests": 0, "disk_writes": 0, "performance_gate_pass": passed}


def test_offline_quality_gate_performance():
    result = run_benchmark()
    assert result["performance_gate_pass"] is True


def main() -> int:
    result = run_benchmark()
    write_canonical_json(OUTPUT, result)
    if not result["performance_gate_pass"]:
        raise SystemExit("TIC Batch 7 offline quality gate performance FAIL")
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
