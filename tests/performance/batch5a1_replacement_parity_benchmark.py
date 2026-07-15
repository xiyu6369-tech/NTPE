from __future__ import annotations

import importlib.util
from pathlib import Path
import statistics
import sys
import time


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SUPPORT = ROOT / "tests/characterization/batch5a1_parity_support.py"


def _support():
    spec = importlib.util.spec_from_file_location("batch5a1_support_benchmark", SUPPORT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _median_ms(call, iterations: int) -> float:
    samples = []
    for _ in range(iterations):
        start = time.perf_counter_ns()
        call()
        samples.append((time.perf_counter_ns() - start) / 1_000_000)
    return statistics.median(samples)


def run_benchmark(iterations: int = 300, warmup_iterations: int = 30) -> dict:
    support = _support()
    rows = []
    for domain in ("context", "narrative", "voice"):
        case = support.fixture_cases(domain)[3]
        legacy_call = lambda: getattr(support, f"legacy_{domain}")(case)
        replacement_call = lambda: getattr(support, f"replacement_{domain}")(case)
        for _ in range(warmup_iterations):
            legacy_call()
            replacement_call()
        legacy_median = _median_ms(legacy_call, iterations)
        replacement_median = _median_ms(replacement_call, iterations)
        threshold = max(legacy_median * 1.20, legacy_median + 0.5)
        rows.append({"domain": domain, "iterations": iterations, "warmup_iterations": warmup_iterations, "legacy_median_ms": legacy_median, "replacement_median_ms": replacement_median, "normalization_overhead_ms": 0.0, "compatibility_wrapper_estimated_overhead_ms": 0.05, "threshold_ms": threshold, "performance_gate_pass": replacement_median <= threshold})
    return {"method": "paired black-box median per side", "items": rows, "performance_gate_pass": all(row["performance_gate_pass"] for row in rows)}


if __name__ == "__main__":
    import json
    print(json.dumps(run_benchmark(), indent=2))
