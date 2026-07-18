from __future__ import annotations

import json
from pathlib import Path
from statistics import median
import sys
from time import perf_counter_ns

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.translation_quality_integration_v72 import QualityIntegrationFlags, QualityIntegrationRequest, integrate_prompt


RUNS = 100


def measure_performance() -> dict[str, float | int | bool]:
    request = QualityIntegrationRequest(
        source_text="영희가 말했다.",
        base_prompt_tokens=500,
        flags=QualityIntegrationFlags(naturalness=True),
        selection_time="2026-07-19T00:00:00Z",
    )
    prompt = "BASE POLICY\n【韓文】\n영희가 말했다."
    durations = []
    fingerprints = set()
    outputs = set()
    for _ in range(RUNS):
        started = perf_counter_ns()
        result = integrate_prompt(prompt, request)
        durations.append((perf_counter_ns() - started) / 1_000_000)
        fingerprints.add(result.metadata.selection_fingerprint)
        outputs.add(result.user_prompt)
    ordered = sorted(durations)
    p95 = ordered[max(0, int(len(ordered) * 0.95) - 1)]
    return {
        "single_chunk_p50_ms": round(median(ordered), 6),
        "single_chunk_p95_ms": round(p95, 6),
        "single_chunk_max_ms": round(max(ordered), 6),
        "hundred_run_total_ms": round(sum(ordered), 6),
        "determinism_runs": RUNS,
        "unique_fingerprints": len(fingerprints),
        "unique_outputs": len(outputs),
        "p95_target_ms": 10.0,
        "max_target_ms": 25.0,
        "targets_passed": p95 <= 10.0 and max(ordered) <= 25.0,
    }


def test_offline_integration_performance_and_determinism() -> None:
    evidence = measure_performance()
    assert evidence["targets_passed"] is True
    assert evidence["unique_fingerprints"] == 1 and evidence["unique_outputs"] == 1


def main() -> int:
    print(json.dumps(measure_performance(), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
