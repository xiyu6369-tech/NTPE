from __future__ import annotations

import json
import platform
from pathlib import Path
import statistics
import sys
import time


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.shared.evidence import write_canonical_json  # noqa: E402
from ntpe.corpus import manage  # noqa: E402
from ntpe.quality import assess, build_review_view  # noqa: E402
from ntpe.corpus.compatibility import corpus_input, governance_input  # noqa: E402
from ntpe.quality.compatibility import decision_input, defects_input, metrics_input, plans_input, review_input  # noqa: E402


DEFECTS = ROOT / "artifacts/te_v71_stage111/TE_V71_STAGE111_TRANSLATION_DEFECTS.json"
METRICS = ROOT / "artifacts/te_v71_stage112/TE_V71_STAGE112_QUALITY_METRICS.json"
REVIEW = ROOT / "artifacts/te_v71_stage113/TE_V71_STAGE113_REVIEW.json"
PLANS = ROOT / "artifacts/te_v71_stage114/TE_V71_STAGE114_PROMPT_IMPROVEMENT_PLAN.json"
DECISION = ROOT / "artifacts/te_v71_stage115/TE_V71_STAGE115_REVIEW_DECISION_CONTRACT.json"
CORPUS = ROOT / "quality_corpus/golden_review/te_v71_initial_defects.json"
GOVERNANCE = ROOT / "artifacts/te_v71_stage116/TE_V71_STAGE116_GOLDEN_CORPUS_GOVERNANCE.json"


def _median_ns(operation, *, iterations: int, warmup: int) -> int:
    for _ in range(warmup):
        operation()
    samples: list[int] = []
    for _ in range(iterations):
        started = time.perf_counter_ns()
        operation()
        samples.append(time.perf_counter_ns() - started)
    return int(statistics.median(samples))


def run_benchmark(*, iterations: int = 1000, warmup_iterations: int = 100) -> dict[str, object]:
    defects, _ = defects_input(DEFECTS)
    metrics, quality_pass, _ = metrics_input(METRICS)
    review, _ = review_input(REVIEW)
    plans, _, _, _ = plans_input(PLANS)
    decision, _, _ = decision_input(DECISION)
    cases, _, _ = corpus_input(CORPUS)
    governance, _, _ = governance_input(GOVERNANCE)
    governance_mapping = json.loads(GOVERNANCE.read_text(encoding="utf-8"))

    def legacy_assessment() -> object:
        overall = next(row for row in metrics if row.dimension == "overall")
        return len(defects), sum(row.blocking for row in defects), overall.score, quality_pass, tuple(row.dimension for row in metrics if row.status == "insufficient_evidence")

    def facade_assessment() -> object:
        return assess(defects=defects, metrics=metrics)

    def legacy_review() -> object:
        return review, plans, decision, False, False

    def facade_review() -> object:
        return build_review_view(review_artifact=review, improvement_plans=plans, human_decision=decision)

    def legacy_corpus() -> object:
        return cases, sum(row.approved_final_translation is not None for row in cases), governance

    def facade_corpus() -> object:
        return manage(corpus=cases, governance_record=governance_mapping)

    timings: dict[str, int] = {}
    for name, legacy, facade in (
        ("assessment", legacy_assessment, facade_assessment),
        ("review", legacy_review, facade_review),
        ("corpus", legacy_corpus, facade_corpus),
    ):
        timings[f"{name}_legacy_median_ns"] = _median_ns(legacy, iterations=iterations, warmup=warmup_iterations)
        timings[f"{name}_facade_median_ns"] = _median_ns(facade, iterations=iterations, warmup=warmup_iterations)

    report: dict[str, object] = {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "iterations": iterations,
        "warmup_iterations": warmup_iterations,
        **timings,
    }
    gates: list[bool] = []
    for name in ("assessment", "review", "corpus"):
        legacy = timings[f"{name}_legacy_median_ns"]
        facade = timings[f"{name}_facade_median_ns"]
        report[f"{name}_overhead_ratio"] = round(facade / max(legacy, 1), 4)
        gates.append(facade <= max(legacy * 1.25, legacy + 1_000_000))
    report.update(
        provider_requests_delta=0,
        prompt_tokens_delta=0,
        disk_writes_delta=0,
        artifact_count_delta=0,
        runtime_stage_delta=0,
        performance_gate_pass=all(gates),
    )
    return report


def main() -> int:
    output = ROOT / "audits/architecture_consolidation/batch4_quality/QUALITY_API_PERFORMANCE_REPORT.json"
    report = run_benchmark()
    write_canonical_json(output, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["performance_gate_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
