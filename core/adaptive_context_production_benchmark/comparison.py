from __future__ import annotations

from .baseline import validate_run_role
from .model import BenchmarkComparison, BenchmarkRun, ChunkEvidence
from .performance import compare_performance
from .quality import compare_quality
from .readiness import evaluate_readiness


def compare_runs(baseline: BenchmarkRun, candidate: BenchmarkRun) -> BenchmarkComparison:
    role_blockers = (*validate_run_role(baseline), *validate_run_role(candidate))
    mismatch = tuple(key for key, value in baseline.contract.comparison_values().items() if candidate.contract.comparison_values().get(key) != value)
    if mismatch or role_blockers:
        blockers = (*role_blockers, *(f"contract-mismatch-{key}" for key in mismatch))
        return BenchmarkComparison("benchmark-comparison-invalid", False, False, tuple(blockers), ())
    b_map = {row.pair_key: row for row in baseline.chunks if row.provider_completed and row.quality_evidence_complete}
    c_map = {row.pair_key: row for row in candidate.chunks if row.provider_completed and row.quality_evidence_complete}
    pairs: tuple[tuple[ChunkEvidence, ChunkEvidence], ...] = tuple((b_map[key], c_map[key]) for key in sorted(b_map.keys() & c_map.keys()))
    performance = compare_performance(baseline, candidate, pairs)
    quality, quality_blockers = compare_quality(pairs)
    paired_payload = tuple({"set_name": left.set_name, "chunk_index": left.chunk_index, "chunk_hash": left.chunk_hash, "candidate_ace_state": right.ace_state} for left, right in pairs)
    status, ready, blockers, limitations = evaluate_readiness(baseline, candidate, performance, quality, quality_blockers)
    return BenchmarkComparison(status, ready, True, blockers, limitations, performance, quality, paired_payload)
