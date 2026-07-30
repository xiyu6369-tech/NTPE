from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

from core.adaptive_context_controlled_provider_retry import (
    CONTROLLED_RETRY_VERSION,
    verify_controlled_retry_artifact,
)
from core.adaptive_context_single_real_invocation import verify_invocation_artifact

ROOT = Path(__file__).resolve().parent


def main() -> int:
    assert CONTROLLED_RETRY_VERSION == "7.0.0-stage10.10.1"
    prior_path = ROOT / "artifacts/te_v7_stage1010/TE_V7_STAGE1010_SINGLE_REAL_INVOCATION.json"
    prior_before = prior_path.read_bytes()
    sandbox = ROOT / ".ntpe_test_sandbox" / "stage10101_root" / uuid.uuid4().hex
    result = subprocess.run([
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "tests/integration/translation_engine_v700_stage10101_provider_timeout_controlled_retry_test.py",
        "--basetemp",
        str(sandbox),
    ], cwd=ROOT, text=True, capture_output=True, check=False)
    try:
        assert result.returncode == 0, result.stdout + result.stderr
        passed = int(result.stdout.split(" passed")[0].split()[-1])
        assert passed >= 35, result.stdout
    finally:
        shutil.rmtree(ROOT / ".ntpe_test_sandbox" / "stage10101_root", ignore_errors=True)

    assert prior_path.read_bytes() == prior_before
    prior = verify_invocation_artifact(prior_path)
    assert prior.status == "single_real_invocation_failed"
    assert prior.network_requests == 1 and prior.timeout_detected is True

    manifest = json.loads((
        ROOT / "manifests/te_v700_stage10101_provider_timeout_controlled_retry_manifest.json"
    ).read_text(encoding="utf-8"))
    assert manifest["stage"] == "TE-v7.0-Stage10.10.1"
    assert manifest["network_requests"] == 0
    assert manifest["real_provider_executed"] is False
    for name, digest in manifest["files"].items():
        path = ROOT / name
        assert path.exists(), name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, name

    artifact = verify_controlled_retry_artifact(
        ROOT / "artifacts/te_v7_stage10101/TE_V7_STAGE10101_CONTROLLED_RETRY.json"
    )
    assert artifact.prior_timeout_evidence_valid is True
    assert artifact.timeout_seconds == 180 and artifact.attempt_limit == 1
    assert artifact.fallback_allowed is False
    if artifact.status == "controlled_retry_contract_prepared":
        assert artifact.network_requests == 0
        assert artifact.real_provider_execution is False
        assert artifact.retry_executed is False
        assert artifact.translation_output_generated is False
    elif artifact.status == "single_controlled_retry_completed":
        assert artifact.network_requests == 1
        assert artifact.real_provider_execution is True
        assert artifact.retry_executed is True
        assert artifact.translation_output_generated is True
        assert artifact.timeout_detected is False
        assert artifact.http_503_detected is False
        assert all(attempt.fallback_used is False for attempt in artifact.attempts)
        assert artifact.human_review_required is True
        assert artifact.comparison_executed is False
        assert artifact.readiness_evaluated is False
        assert artifact.baseline_created is False
        assert artifact.candidate_created is False
        assert artifact.production_ready is False
    else:
        raise AssertionError(f"unsupported controlled retry artifact status: {artifact.status}")
    print("TE v7.0 Stage 10.10.1 Provider Timeout Controlled Retry Contract ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
