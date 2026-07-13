from __future__ import annotations

import json
import shutil
import subprocess
import sys
import uuid
from dataclasses import replace
from pathlib import Path

from core.adaptive_context_production_benchmark import (
    BENCHMARK_VERSION, BenchmarkContract, ChunkEvidence, collect_chunk, collect_run,
    compare_runs, load_run, write_artifact,
)
from ntpe_production_translate import build_parser

ROOT = Path(__file__).resolve().parents[2]


def _contract(*, ace: bool, **changes: object) -> BenchmarkContract:
    values = dict(
        set_name="Golden_Set", source_file_hash="a" * 64, chunk_count=1,
        chunk_plan=("Golden_Set:1:0:100:" + "b" * 64,), profile="literary", model="frozen-model",
        api_timeout=180, provider_attempts=2, chunk_size=600, max_output_tokens=4096,
        prompt_policy_version="prompt-v1", quality_v5_version="quality-v5",
        retry_recovery_policy_version="retry-v1", ace_enabled=ace, rollout_percent=5 if ace else 0,
    )
    values.update(changes)
    return BenchmarkContract(**values)  # type: ignore[arg-type]


def _chunk(*, ace: str, **changes: object) -> ChunkEvidence:
    values = dict(
        set_name="Golden_Set", chunk_index=1, source_hash="a" * 64, source_offset="0:100",
        chunk_hash="b" * 64, completion="provider_completed", ace_state=ace, provider_calls=1,
        provider_attempts=1, provider_latency_ms=100.0, execution_ms=110.0, prompt_tokens=500,
        context_tokens=100, qa_status="accepted", quality_score=90.0, quality_evidence_complete=True,
    )
    values.update(changes)
    return ChunkEvidence(**values)  # type: ignore[arg-type]


def _runs(*, baseline_chunk: ChunkEvidence | None = None, candidate_chunk: ChunkEvidence | None = None):
    baseline = collect_run(run_kind="baseline", mode="provider", stage="TE-v7.0-Stage09-Baseline", contract=_contract(ace=False), chunks=(baseline_chunk or _chunk(ace="disabled"),), execution_total_ms=120)
    candidate = collect_run(run_kind="candidate", mode="provider", stage="TE-v7.0-Stage09-Candidate", contract=_contract(ace=True), chunks=(candidate_chunk or _chunk(ace="activated", provider_latency_ms=80, prompt_tokens=450, context_tokens=70),), execution_total_ms=100)
    return baseline, candidate


def test_contract_pairing_and_performance_gain_ready() -> None:
    report = compare_runs(*_runs())
    assert report.ready and report.status == "pass"
    assert report.performance["provider_calls_delta"] == 0
    assert report.performance["prompt_tokens_saved"] == 50
    assert report.performance["activated_chunks"] == 1 == report.performance["paired_chunks"]


def test_contract_mismatches_fail_closed() -> None:
    baseline, candidate = _runs()
    for field, value in (("source_file_hash", "c" * 64), ("chunk_plan", ("different",)), ("model", "other"), ("api_timeout", 181), ("provider_attempts", 3)):
        changed = replace(candidate, contract=replace(candidate.contract, **{field: value}))
        report = compare_runs(baseline, changed)
        assert report.status == "benchmark-comparison-invalid" and not report.ready


def test_resume_excluded_and_cannot_contain_latency() -> None:
    try:
        collect_chunk({**_chunk(ace="disabled").__dict__, "completion": "resume", "provider_latency_ms": 1})
    except ValueError:
        pass
    else:
        raise AssertionError("resume latency accepted")
    baseline, candidate = _runs(candidate_chunk=_chunk(ace="activated", completion="resume", provider_calls=0, provider_attempts=0, provider_latency_ms=None))
    report = compare_runs(baseline, candidate)
    assert report.performance["paired_chunks"] == 0 and not report.ready


def test_unsampled_chunk_is_not_activated() -> None:
    report = compare_runs(*_runs(candidate_chunk=_chunk(ace="not_sampled", prompt_tokens=450)))
    assert report.performance["activated_chunks"] == 0
    assert "no-activated-paired-chunk" in report.blockers


def test_activated_chunk_regressions_block_individually() -> None:
    cases = (
        (dict(omission_issues=1), "new-omission"),
        (dict(unsupported_detail_issues=1), "new-unsupported-detail"),
        (dict(completeness_issues=1), "completeness-regression"),
        (dict(quality_score=89), "quality-score-regression"),
        (dict(qa_status="failed"), "accepted-to-failed"),
    )
    for changes, marker in cases:
        report = compare_runs(*_runs(candidate_chunk=_chunk(ace="activated", **changes)))
        assert not report.ready and any(marker in blocker for blocker in report.blockers)


def test_provider_calls_added_blocks_ready() -> None:
    report = compare_runs(*_runs(candidate_chunk=_chunk(ace="activated", provider_calls=2)))
    assert not report.ready and "provider-calls-added" in report.blockers


def test_no_performance_gain_is_not_ready() -> None:
    report = compare_runs(*_runs(candidate_chunk=_chunk(ace="activated")))
    assert report.status == "pass_without_performance_gain" and not report.ready


def test_provider_failure_is_external_limitation() -> None:
    report = compare_runs(*_runs(candidate_chunk=_chunk(ace="activated", timeout_count=1)))
    assert report.status == "incomplete_external_provider_limitation" and not report.ready
    report_503 = compare_runs(*_runs(candidate_chunk=_chunk(ace="activated", http_503_count=1)))
    assert report_503.status == "incomplete_external_provider_limitation"


def test_redacted_mutable_artifact_integrity() -> None:
    sandbox = ROOT / ".ntpe_test_sandbox" / "stage09_artifact" / uuid.uuid4().hex
    sandbox.mkdir(parents=True, exist_ok=False)
    try:
        baseline, _ = _runs(); path = write_artifact(baseline, sandbox / "baseline.json")
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["content_redacted"] is True and "artifact_sha256" in payload
        assert load_run(path) == baseline
        payload["stage"] = "tampered"; path.write_text(json.dumps(payload), encoding="utf-8")
        try: load_run(path)
        except ValueError: pass
        else: raise AssertionError("tampered mutable artifact accepted")
        try: write_artifact({"source_text": "secret"}, sandbox / "unsafe.json")
        except ValueError: pass
        else: raise AssertionError("plaintext artifact accepted")
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def test_cli_contract_and_comparison_mode_has_no_provider_path() -> None:
    args = build_parser().parse_args(["regression", "--ace-production-benchmark", "--ace-production-benchmark-mode", "comparison", "--ace-production-benchmark-baseline-stage", "base", "--ace-production-benchmark-candidate-stage", "candidate"])
    assert args.ace_production_benchmark and args.ace_production_benchmark_mode == "comparison"
    assert BENCHMARK_VERSION == "7.0.0-stage09"
    sandbox = ROOT / ".ntpe_test_sandbox" / "stage09_comparison" / uuid.uuid4().hex
    readiness_path = ROOT / "artifacts" / "te_v7_stage09" / "TE_V7_STAGE09_READINESS.json"
    readiness_before = readiness_path.read_bytes() if readiness_path.exists() else None
    sandbox.mkdir(parents=True, exist_ok=False)
    try:
        baseline, candidate = _runs()
        baseline_path = write_artifact(baseline, sandbox / "baseline.json")
        candidate_path = write_artifact(candidate, sandbox / "candidate.json")
        report_path = sandbox / "comparison.json"
        result = subprocess.run([
            sys.executable, "launcher_translate.py", "regression", "--ace-production-benchmark",
            "--ace-production-benchmark-mode", "comparison",
            "--ace-production-benchmark-baseline-stage", str(baseline_path),
            "--ace-production-benchmark-candidate-stage", str(candidate_path),
            "--ace-production-benchmark-report", str(report_path),
        ], cwd=ROOT, text=True, capture_output=True, check=False)
        assert result.returncode == 0, result.stdout + result.stderr
        assert json.loads(report_path.read_text(encoding="utf-8"))["ready"] is True
        assert "provider request start" not in result.stdout.lower()
    finally:
        if readiness_before is None: readiness_path.unlink(missing_ok=True)
        else: readiness_path.write_bytes(readiness_before)
        shutil.rmtree(sandbox, ignore_errors=True)


def test_rollout_cap_and_rollback_compatibility() -> None:
    baseline, candidate = _runs()
    assert candidate.contract.rollout_percent == 5
    rolled_back = replace(candidate, rollback_triggered=True)
    assert "rollback-triggered" in compare_runs(baseline, rolled_back).blockers
    over = replace(candidate, contract=replace(candidate.contract, rollout_percent=6))
    assert not compare_runs(baseline, over).ready


def test_assembly_harness_does_not_call_provider() -> None:
    token = uuid.uuid4().hex
    sandbox = ROOT / ".ntpe_test_sandbox" / "stage09_assembly" / token
    stage = f"TE_V7_STAGE09_ASSEMBLY_{token}"
    output = ROOT / "tests" / "literary" / "outputs" / stage
    package = ROOT / "prompt_packages" / "txt_runtime" / "original_ko_chunk_000001.json"
    before = package.read_bytes() if package.exists() else None
    sandbox.mkdir(parents=True, exist_ok=False)
    try:
        report = sandbox / "assembly.json"
        result = subprocess.run([
            sys.executable, "launcher_translate.py", "regression", "--set", "smoke", "--stage", stage,
            "--chunk-size", "600", "--dry-run", "--no-evaluate", "--overwrite",
            "--ace-production-benchmark", "--ace-production-benchmark-mode", "assembly",
            "--ace-production-benchmark-report", str(report),
        ], cwd=ROOT, text=True, capture_output=True, check=False)
        assert result.returncode == 0, result.stdout + result.stderr
        payload = json.loads(report.read_text(encoding="utf-8"))
        assert payload["mode"] == "assembly" and payload["provider_evidence_complete"] is True
        assert all(row["provider_calls"] == 0 for row in payload["chunk_evidence"])
        assert "provider request start" not in result.stdout.lower()
    finally:
        if before is None: package.unlink(missing_ok=True)
        else: package.write_bytes(before)
        shutil.rmtree(sandbox, ignore_errors=True)
        shutil.rmtree(output, ignore_errors=True)
