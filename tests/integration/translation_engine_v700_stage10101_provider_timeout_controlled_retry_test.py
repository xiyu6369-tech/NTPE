from __future__ import annotations

import hashlib
import json
import shutil
import socket
import uuid
from dataclasses import replace
from pathlib import Path

import pytest

import core.adaptive_context_controlled_provider_retry.runner as retry_runner
from core.adaptive_context_controlled_provider_retry import (
    CONTROLLED_RETRY_AUTHORIZATION_TOKEN,
    CONTROLLED_RETRY_VERSION,
    ControlledProviderRetryConfig,
    ControlledProviderRetryRunner,
    PriorTimeoutEvidence,
    verify_controlled_retry_artifact,
)
from core.adaptive_context_single_real_invocation import (
    EXECUTION_AUTHORIZATION_TOKEN,
    FakeSingleInvocationTransport,
    verify_invocation_artifact,
)
from ntpe_controlled_real_provider_retry import build_parser

ROOT = Path(__file__).resolve().parents[2]
PRIOR = ROOT / "artifacts/te_v7_stage1010/TE_V7_STAGE1010_SINGLE_REAL_INVOCATION.json"
MODEL = "meta/llama-3.3-70b-instruct"
FAKE_CREDENTIAL = "stage10101-fake-credential-never-persist"
AUTHORIZATION_ID = "stage10101-authorization-001"


@pytest.fixture
def sandbox() -> Path:
    path = ROOT / ".ntpe_test_sandbox" / "stage10101" / uuid.uuid4().hex
    yield path
    shutil.rmtree(path, ignore_errors=True)
    parent = ROOT / ".ntpe_test_sandbox" / "stage10101"
    if parent.exists() and not any(parent.iterdir()):
        parent.rmdir()
    root = ROOT / ".ntpe_test_sandbox"
    if root.exists() and not any(root.iterdir()):
        root.rmdir()


def _config(sandbox: Path, **changes: object) -> ControlledProviderRetryConfig:
    values: dict[str, object] = {
        "enabled": True,
        "boundary_enabled": True,
        "real_provider_enabled": True,
        "authorization_id": AUTHORIZATION_ID,
        "execution_authorization_token": CONTROLLED_RETRY_AUTHORIZATION_TOKEN,
        "execution_mode": "fake",
        "invocation_id": "stage10101-test-001",
        "artifact_path": str(sandbox / "artifact.json"),
        "review_path": str(sandbox / "review.txt"),
    }
    values.update(changes)
    return ControlledProviderRetryConfig(**values)


def _prepare(sandbox: Path, **changes: object):
    return ControlledProviderRetryRunner().prepare(
        _config(sandbox, **changes),
        root=ROOT,
        environ={"NVIDIA_API_KEY": FAKE_CREDENTIAL},
    )


def _run(
    sandbox: Path, *, config: ControlledProviderRetryConfig | None = None,
    transport: FakeSingleInvocationTransport | None = None, environ=None,
):
    return ControlledProviderRetryRunner().run(
        config or _config(sandbox),
        root=ROOT,
        environ={"NVIDIA_API_KEY": FAKE_CREDENTIAL} if environ is None else environ,
        transport=transport,
    )


def _prior_with(**changes: object) -> PriorTimeoutEvidence:
    artifact = replace(verify_invocation_artifact(PRIOR), **changes)
    raw = PRIOR.read_bytes()
    return PriorTimeoutEvidence(artifact, hashlib.sha256(raw).hexdigest(), raw)


def test_default_disabled() -> None:
    result = ControlledProviderRetryRunner().prepare(
        ControlledProviderRetryConfig(), root=ROOT, environ={},
    )
    assert result.blockers == ("controlled-retry-disabled",)
    assert result.artifact.network_requests == 0


@pytest.mark.parametrize("field,expected", [
    ("boundary_enabled", "boundary-enable-required"),
    ("real_provider_enabled", "real-provider-enable-required"),
    ("authorization_id", "authorization-id-required"),
])
def test_required_admission_gates(
    sandbox: Path, field: str, expected: str,
) -> None:
    result = _prepare(sandbox, **{field: False if field != "authorization_id" else ""})
    assert expected in result.blockers[0]


def test_prior_artifact_missing_fails_closed(
    sandbox: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        retry_runner,
        "validate_prior_timeout_evidence",
        lambda *a, **k: (_ for _ in ()).throw(ValueError("controlled-retry-prior-artifact-missing")),
    )
    assert "prior-artifact-missing" in _prepare(sandbox).blockers[0]


def test_prior_artifact_integrity_invalid_fails_closed(
    sandbox: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        retry_runner,
        "validate_prior_timeout_evidence",
        lambda *a, **k: (_ for _ in ()).throw(ValueError("controlled-retry-prior-artifact-integrity-invalid")),
    )
    assert "integrity-invalid" in _prepare(sandbox).blockers[0]


@pytest.mark.parametrize("changes,expected", [
    ({"status": "single_real_invocation_completed"}, "status-invalid"),
    ({"timeout_detected": False}, "timeout-required"),
    ({"translation_output_generated": True}, "translation-output-unexpected"),
    ({"network_requests": 0}, "network-evidence-invalid"),
])
def test_prior_timeout_contract_is_strict(
    sandbox: Path, monkeypatch: pytest.MonkeyPatch,
    changes: dict[str, object], expected: str,
) -> None:
    evidence = _prior_with(**changes)
    def validate(*args: object, **kwargs: object) -> PriorTimeoutEvidence:
        artifact = evidence.artifact
        if artifact.status != "single_real_invocation_failed":
            raise ValueError("controlled-retry-prior-artifact-status-invalid")
        if artifact.network_requests != 1:
            raise ValueError("controlled-retry-prior-network-evidence-invalid")
        if not artifact.timeout_detected:
            raise ValueError("controlled-retry-prior-timeout-required")
        if artifact.translation_output_generated:
            raise ValueError("controlled-retry-prior-translation-output-unexpected")
        return evidence
    monkeypatch.setattr(retry_runner, "validate_prior_timeout_evidence", validate)
    assert expected in _prepare(sandbox).blockers[0]


def test_stage1010b_artifact_is_byte_identical_after_prepare(sandbox: Path) -> None:
    before = PRIOR.read_bytes()
    assert not _prepare(sandbox).blockers
    assert PRIOR.read_bytes() == before


def test_old_authorization_token_is_rejected(sandbox: Path) -> None:
    result = _prepare(sandbox, execution_authorization_token=EXECUTION_AUTHORIZATION_TOKEN)
    assert "execution-authorization-invalid" in result.blockers[0]


@pytest.mark.parametrize("token", ["", "WRONG"])
def test_missing_or_incorrect_new_authorization_is_rejected(
    sandbox: Path, token: str,
) -> None:
    result = _prepare(sandbox, execution_authorization_token=token)
    assert "execution-authorization" in result.blockers[0]
    assert result.artifact.network_requests == 0


def test_missing_credential_is_rejected(sandbox: Path) -> None:
    result = ControlledProviderRetryRunner().prepare(
        _config(sandbox), root=ROOT, environ={},
    )
    assert result.blockers == ("controlled-retry-missing-credential",)


@pytest.mark.parametrize("changes,expected", [
    ({"model": "invalid"}, "model-not-allowlisted"),
    ({"provider_url": "https://invalid.example/v1"}, "endpoint-not-allowlisted"),
    ({"timeout_seconds": 179}, "timeout-frozen"),
    ({"attempt_limit": 2}, "attempt-limit-frozen"),
    ({"fallback_allowed": True}, "fallback-forbidden"),
    ({"chunk_count": 2}, "single-chunk-required"),
    ({"chunk_index": 2}, "single-chunk-required"),
    ({"single_chunk_only": False}, "single-chunk-required"),
    ({"single_controlled_session": False}, "single-session-required"),
    ({"resumed": True}, "resume-forbidden"),
    ({"chunk_size": 601}, "chunk-size-frozen"),
])
def test_frozen_retry_shape_is_enforced(
    sandbox: Path, changes: dict[str, object], expected: str,
) -> None:
    assert expected in _prepare(sandbox, **changes).blockers[0]


def test_wrong_source_path_is_rejected(sandbox: Path) -> None:
    result = _prepare(sandbox, source_path="tests/literary/Smoke_Set/original_ko.txt")
    assert "source-path-not-golden-set" in result.blockers[0]


@pytest.mark.parametrize("path,expected", [
    ("bad.txt", "artifact-extension-invalid"),
    ("artifacts/te_v7_stage09/retry.json", "artifact-path-forbidden"),
    ("artifacts/te_v7_stage1010/retry.json", "artifact-path-forbidden"),
    ("outside-stage10101.json", "artifact-path-forbidden"),
])
def test_artifact_path_protection(
    sandbox: Path, path: str, expected: str,
) -> None:
    assert expected in _prepare(sandbox, artifact_path=str(ROOT / path)).blockers[0]


def test_prepared_artifact_has_frozen_non_claims(sandbox: Path) -> None:
    artifact = _prepare(sandbox).artifact
    assert artifact.status == "controlled_retry_contract_prepared"
    assert artifact.timeout_seconds == 180 and artifact.attempt_limit == 1
    assert artifact.fallback_allowed is False
    assert artifact.network_requests == 0 and artifact.retry_executed is False
    assert artifact.real_provider_execution is False
    assert artifact.translation_output_generated is False
    assert artifact.comparison_executed is False and artifact.readiness_evaluated is False
    assert artifact.baseline_created is False and artifact.candidate_created is False


def test_estimated_budget_is_separate_from_actual_usage(sandbox: Path) -> None:
    token = _prepare(sandbox).artifact.token_evidence
    assert token.estimated_output_token_budget == 800
    assert token.actual_input_tokens is None and token.actual_output_tokens is None
    assert token.token_usage_complete is False
    assert token.token_usage_source == "not_executed"


def test_fake_timeout_preserves_classification_without_actual_tokens(sandbox: Path) -> None:
    artifact = _run(
        sandbox, transport=FakeSingleInvocationTransport(("timeout",)),
    ).artifact
    assert artifact.status == "controlled_retry_contract_prepared"
    assert artifact.timeout_detected is True
    assert artifact.token_evidence.actual_output_tokens is None
    assert artifact.token_evidence.token_usage_complete is False
    assert artifact.retry_executed is False and artifact.network_requests == 0


def test_fake_http_503_is_classified(sandbox: Path) -> None:
    artifact = _run(
        sandbox, transport=FakeSingleInvocationTransport(("503",)),
    ).artifact
    assert artifact.http_503_detected is True
    assert artifact.attempts[0].http_503 is True


def test_fake_exception_is_redacted(sandbox: Path) -> None:
    artifact = _run(
        sandbox, transport=FakeSingleInvocationTransport(("exception",)),
    ).artifact
    rendered = json.dumps(artifact.to_dict(), ensure_ascii=False)
    assert "fake exception content" not in rendered
    assert artifact.attempts[0].attempt_status == "failed"


def test_fake_success_preserves_payload_and_prompt(sandbox: Path) -> None:
    artifact = _run(sandbox).artifact
    assert artifact.payload_preserved is True and artifact.prompt_preserved is True
    assert artifact.attempt_count == 1


def test_fake_provenance_cannot_claim_real(sandbox: Path) -> None:
    transport = FakeSingleInvocationTransport()
    result = _run(
        sandbox,
        config=_config(sandbox, execution_mode="real"),
        transport=transport,
    )
    assert "transport-provenance-mismatch" in result.blockers[0]
    assert transport.network_requests == 0


def test_fake_tests_do_not_open_socket(
    sandbox: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        socket.socket,
        "connect",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("network forbidden")),
    )
    assert _run(sandbox).artifact.network_requests == 0


def test_fake_path_never_constructs_real_client(
    sandbox: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        retry_runner,
        "NvidiaSingleInvocationTransport",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("real transport forbidden")),
    )
    assert _run(sandbox).artifact.real_provider_execution is False


def test_artifact_omits_source_authorization_and_credential(sandbox: Path) -> None:
    path = Path(_config(sandbox).artifact_path)
    _prepare(sandbox)
    rendered = path.read_text(encoding="utf-8")
    source_prefix = (ROOT / "tests/literary/Golden_Set/original_ko.txt").read_text(encoding="utf-8")[:30]
    assert source_prefix not in rendered
    assert CONTROLLED_RETRY_AUTHORIZATION_TOKEN not in rendered
    assert AUTHORIZATION_ID not in rendered
    assert FAKE_CREDENTIAL not in rendered


def test_artifact_integrity_tampering_fails_closed(sandbox: Path) -> None:
    path = Path(_config(sandbox).artifact_path)
    _prepare(sandbox)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["timeout_seconds"] = 30
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="integrity failure"):
        verify_controlled_retry_artifact(path)


def test_one_runner_instance_cannot_execute_twice(sandbox: Path) -> None:
    runner = ControlledProviderRetryRunner()
    config = _config(sandbox)
    first = runner.run(config, root=ROOT, environ={"NVIDIA_API_KEY": FAKE_CREDENTIAL})
    second = runner.run(config, root=ROOT, environ={"NVIDIA_API_KEY": FAKE_CREDENTIAL})
    assert first.artifact.status == "controlled_retry_contract_prepared"
    assert "session-already-claimed" in second.blockers[0]


def test_cli_does_not_accept_policy_or_secret_arguments() -> None:
    destinations = {action.dest for action in build_parser()._actions}
    assert not {
        "api_key", "execution_authorization_token", "timeout", "attempts",
        "fallback", "model", "provider_url", "chunk_index", "chunk_size",
    } & destinations


def test_authorization_is_hidden_from_config_repr(sandbox: Path) -> None:
    rendered = repr(_config(sandbox))
    assert CONTROLLED_RETRY_AUTHORIZATION_TOKEN not in rendered
    assert "execution_authorization_token" not in rendered


def test_entrypoint_has_no_production_launcher_hook() -> None:
    source = (ROOT / "ntpe_controlled_real_provider_retry.py").read_text(encoding="utf-8")
    assert "launcher_translate" not in source
    assert "ntpe_production_translate" not in source
    assert "requests" not in source


def test_version_is_stage_local() -> None:
    assert CONTROLLED_RETRY_VERSION == "7.0.0-stage10.10.1"
