from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

from core.adaptive_context_provider_session_cli import CLI_VERSION, build_parser, run_harness
from core.adaptive_context_provider_benchmark_session import verify_session_report

ROOT = Path(__file__).resolve().parents[2]
HASH_A = "a" * 64
HASH_B = "b" * 64


def _sandbox(name: str) -> Path:
    path = ROOT / ".ntpe_test_sandbox" / name / uuid.uuid4().hex
    path.mkdir(parents=True, exist_ok=False)
    return path


def _args(report: Path, *extra: str) -> list[str]:
    return [
        "--enable-controlled-session", "--pair-id", "stage103-pair", "--run-kind", "baseline",
        "--set-name", "Smoke_Set", "--chunk-index", "1", "--source-hash", HASH_A,
        "--chunk-hash", HASH_B, "--model", "mock-model", "--timeout-seconds", "180",
        "--estimated-input-tokens", "100", "--estimated-output-tokens", "80",
        "--report", str(report), *extra,
    ]


def test_disabled_by_default_creates_no_report() -> None:
    sandbox = _sandbox("stage103_disabled"); report = sandbox / "report.json"
    try:
        assert run_harness(["--report", str(report)]) == 2
        assert not report.exists()
    finally: shutil.rmtree(sandbox, ignore_errors=True)


def test_required_metadata_fails_closed() -> None:
    sandbox = _sandbox("stage103_required")
    try: assert run_harness(["--enable-controlled-session", "--report", str(sandbox / "r.json")]) == 2
    finally: shutil.rmtree(sandbox, ignore_errors=True)


def test_source_hash_must_be_sha256() -> None:
    sandbox = _sandbox("stage103_source_hash")
    try:
        args = _args(sandbox / "r.json"); args[args.index(HASH_A)] = "bad"
        assert run_harness(args) == 2
    finally: shutil.rmtree(sandbox, ignore_errors=True)


def test_chunk_hash_must_be_sha256() -> None:
    sandbox = _sandbox("stage103_chunk_hash")
    try:
        args = _args(sandbox / "r.json"); args[args.index(HASH_B)] = "bad"
        assert run_harness(args) == 2
    finally: shutil.rmtree(sandbox, ignore_errors=True)


def test_single_chunk_index_must_be_positive() -> None:
    sandbox = _sandbox("stage103_chunk")
    try:
        args = _args(sandbox / "r.json"); args[args.index("1")] = "0"
        assert run_harness(args) == 2
    finally: shutil.rmtree(sandbox, ignore_errors=True)


def test_malformed_attempt_plan_fails_closed() -> None:
    sandbox = _sandbox("stage103_plan")
    try: assert run_harness(_args(sandbox / "r.json", "--attempt", "bad")) == 2
    finally: shutil.rmtree(sandbox, ignore_errors=True)


def test_mock_outcome_count_must_match_plan() -> None:
    sandbox = _sandbox("stage103_outcome_count")
    try:
        args = _args(sandbox / "r.json", "--attempt", "m1|10|0", "--attempt", "m2|10|1", "--mock-outcome", "timeout", "--mock-outcome", "failed", "--mock-outcome", "success")
        assert run_harness(args) == 2
    finally: shutil.rmtree(sandbox, ignore_errors=True)


def test_mock_output_token_count_must_match_plan() -> None:
    sandbox = _sandbox("stage103_token_count")
    try:
        args = _args(sandbox / "r.json", "--attempt", "m1|10|0", "--attempt", "m2|10|1", "--mock-output-tokens", "1", "--mock-output-tokens", "2", "--mock-output-tokens", "3")
        assert run_harness(args) == 2
    finally: shutil.rmtree(sandbox, ignore_errors=True)


def test_successful_mock_session_writes_report() -> None:
    sandbox = _sandbox("stage103_success"); report = sandbox / "report.json"
    try:
        assert run_harness(_args(report)) == 0
        payload = verify_session_report(report)
        assert payload["summary"]["state"] == "completed" and payload["content_redacted"] is True
    finally: shutil.rmtree(sandbox, ignore_errors=True)


def test_standalone_cli_entrypoint_runs() -> None:
    sandbox = _sandbox("stage103_subprocess"); report = sandbox / "report.json"
    try:
        result = subprocess.run([sys.executable, "ntpe_provider_benchmark_session.py", *_args(report)], cwd=ROOT, text=True, capture_output=True, check=False)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "controlled_provider_session_readiness_evaluated: false" in result.stdout
    finally: shutil.rmtree(sandbox, ignore_errors=True)


def test_retry_attempts_remain_independent() -> None:
    sandbox = _sandbox("stage103_retry"); report = sandbox / "report.json"
    try:
        args = _args(report, "--attempt", "m1|10|0", "--attempt", "m2|20|1", "--mock-outcome", "timeout", "--mock-outcome", "success")
        assert run_harness(args) == 0
        records = verify_session_report(report)["evidence"]["records"]
        assert [row["attempt"] for row in records] == [1, 2]
    finally: shutil.rmtree(sandbox, ignore_errors=True)


def test_timeout_returns_provider_limited_without_readiness() -> None:
    sandbox = _sandbox("stage103_timeout"); report = sandbox / "report.json"
    try:
        assert run_harness(_args(report, "--mock-outcome", "timeout")) == 1
        payload = verify_session_report(report)
        assert payload["summary"]["state"] == "provider_limited" and payload["summary"]["readiness_evaluated"] is False
    finally: shutil.rmtree(sandbox, ignore_errors=True)


def test_http_503_returns_provider_limited() -> None:
    sandbox = _sandbox("stage103_503"); report = sandbox / "report.json"
    try:
        assert run_harness(_args(report, "--mock-outcome", "503")) == 1
        assert verify_session_report(report)["summary"]["http_503_attempts"] == 1
    finally: shutil.rmtree(sandbox, ignore_errors=True)


def test_resume_excludes_mock_provider_call() -> None:
    sandbox = _sandbox("stage103_resume"); report = sandbox / "report.json"
    try:
        assert run_harness(_args(report, "--resume")) == 0
        payload = verify_session_report(report)
        assert payload["summary"]["state"] == "excluded" and payload["summary"]["attempts_executed"] == 0
    finally: shutil.rmtree(sandbox, ignore_errors=True)


def test_short_output_is_visible_and_not_ready() -> None:
    sandbox = _sandbox("stage103_short"); report = sandbox / "report.json"
    try:
        args = _args(report, "--minimum-output-tokens", "50", "--mock-output-tokens", "10")
        assert run_harness(args) == 0
        evidence = verify_session_report(report)["evidence"]
        assert "suspicious-short-output" in evidence["limitations"] and evidence["ready_for_benchmark"] is False
    finally: shutil.rmtree(sandbox, ignore_errors=True)


def test_mock_evidence_never_claims_real_provider() -> None:
    sandbox = _sandbox("stage103_mock"); report = sandbox / "report.json"
    try:
        assert run_harness(_args(report)) == 0
        evidence = verify_session_report(report)["evidence"]
        assert evidence["status"] == "evidence_complete_mock_only"
        assert all(row["real_provider_execution"] is False for row in evidence["records"])
    finally: shutil.rmtree(sandbox, ignore_errors=True)


def test_report_path_cannot_overwrite_stage09_artifact() -> None:
    target = ROOT / "tests" / "fixtures" / "te_v7_stage09" / "TE_V7_STAGE09_BASELINE.json"
    before = hashlib.sha256(target.read_bytes()).hexdigest()
    assert run_harness(_args(target)) == 2
    assert hashlib.sha256(target.read_bytes()).hexdigest() == before


def test_cli_exposes_no_real_provider_or_raw_payload_options() -> None:
    destinations = {action.dest for action in build_parser()._actions}
    forbidden = {"api_key", "provider_url", "real_provider", "input", "prompt", "payload", "source_text"}
    assert not destinations & forbidden


def test_report_contains_no_source_prompt_or_provider_body() -> None:
    sandbox = _sandbox("stage103_redaction"); report = sandbox / "report.json"
    try:
        assert run_harness(_args(report)) == 0
        serialized = report.read_text(encoding="utf-8").lower()
        assert "source_text" not in serialized and "user_prompt" not in serialized and "response_body" not in serialized
    finally: shutil.rmtree(sandbox, ignore_errors=True)


def test_stage102_sources_remain_unchanged() -> None:
    targets = tuple(sorted((ROOT / "core/adaptive_context_provider_benchmark_session").glob("*.py")))
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in targets}
    sandbox = _sandbox("stage103_stage102"); report = sandbox / "r.json"
    try: assert run_harness(_args(report)) == 0
    finally: shutil.rmtree(sandbox, ignore_errors=True)
    assert before == {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in targets}


def test_frozen_runtime_and_stage09_artifacts_remain_unchanged() -> None:
    targets = (
        ROOT / "lts/txt_translation_runtime.py",
        ROOT / "core/translation_runtime/runtime_speed_policy.py",
        ROOT / "tests" / "fixtures" / "te_v7_stage09" / "TE_V7_STAGE09_BASELINE.json",
    )
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in targets}
    sandbox = _sandbox("stage103_frozen"); report = sandbox / "r.json"
    try: assert run_harness(_args(report)) == 0
    finally: shutil.rmtree(sandbox, ignore_errors=True)
    assert CLI_VERSION == "7.0.0-stage10.3"
    assert before == {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in targets}
