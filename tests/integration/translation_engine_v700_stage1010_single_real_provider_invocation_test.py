from __future__ import annotations

import json
import shutil
import socket
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest

import core.adaptive_context_real_provider_preflight.validator as preflight_validator
import core.adaptive_context_single_real_invocation.runner as invocation_runner
from core.adaptive_context_real_provider_preflight import PreflightAttemptPlan
from core.adaptive_context_single_real_invocation import (
    EXECUTION_AUTHORIZATION_TOKEN,
    INVOCATION_VERSION,
    FakeSingleInvocationTransport,
    SingleRealInvocationConfig,
    SingleRealInvocationRunner,
    inspect_translation_output,
    verify_invocation_artifact,
    write_translation_review,
)
from ntpe_single_real_provider_invocation import build_parser

ROOT = Path(__file__).resolve().parents[2]
MODEL = "meta/llama-3.3-70b-instruct"
FAKE_CREDENTIAL = "stage1010-fake-credential-never-persist"
AUTHORIZATION_ID = "stage1010-authorization-001"


@pytest.fixture
def sandbox() -> Path:
    path = ROOT / ".ntpe_test_sandbox" / "stage1010" / uuid.uuid4().hex
    yield path
    shutil.rmtree(path, ignore_errors=True)
    parent = ROOT / ".ntpe_test_sandbox" / "stage1010"
    if parent.exists() and not any(parent.iterdir()):
        parent.rmdir()
    root = ROOT / ".ntpe_test_sandbox"
    if root.exists() and not any(root.iterdir()):
        root.rmdir()


def _plans(*, retry: bool = False, timeout: int = 30):
    first = PreflightAttemptPlan(1, MODEL, timeout, False)
    if not retry:
        return (first,)
    return (first, PreflightAttemptPlan(2, MODEL, 60, True))


def _config(sandbox: Path, **changes: object) -> SingleRealInvocationConfig:
    values: dict[str, object] = {
        "enabled": True,
        "boundary_enabled": True,
        "real_provider_enabled": True,
        "authorization_id": AUTHORIZATION_ID,
        "execution_authorization_token": EXECUTION_AUTHORIZATION_TOKEN,
        "execution_mode": "fake",
        "provider": "nvidia",
        "provider_url": "https://integrate.api.nvidia.com/v1/chat/completions",
        "model": MODEL,
        "session_id": "stage1010-session-001",
        "chunk_index": 1,
        "chunk_size": 600,
        "chunk_count": 1,
        "single_chunk_only": True,
        "single_controlled_session": True,
        "resumed": False,
        "attempt_plan": _plans(),
        "max_retries": 1,
        "artifact_path": str(sandbox / "invocation.json"),
        "review_path": str(sandbox / "review.txt"),
    }
    values.update(changes)
    return SingleRealInvocationConfig(**values)


def _run(
    sandbox: Path, *, config: SingleRealInvocationConfig | None = None,
    transport: FakeSingleInvocationTransport | None = None,
    environ=None,
):
    return SingleRealInvocationRunner().run(
        config or _config(sandbox), root=ROOT,
        environ={"NVIDIA_API_KEY": FAKE_CREDENTIAL} if environ is None else environ,
        transport=transport,
    )


def test_default_disabled_has_zero_network_requests(sandbox: Path) -> None:
    result = _run(sandbox, config=SingleRealInvocationConfig())
    assert result.artifact.status == "blocked"
    assert result.blockers == ("single-real-invocation-disabled",)
    assert result.artifact.network_requests == 0


def test_missing_boundary_enable_is_blocked(sandbox: Path) -> None:
    result = _run(sandbox, config=_config(sandbox, boundary_enabled=False))
    assert "boundary-enable-required" in result.blockers[0]


def test_missing_real_provider_enable_is_blocked(sandbox: Path) -> None:
    result = _run(sandbox, config=_config(sandbox, real_provider_enabled=False))
    assert "real-provider-enable-required" in result.blockers[0]


def test_missing_authorization_id_is_blocked(sandbox: Path) -> None:
    result = _run(sandbox, config=_config(sandbox, authorization_id=""))
    assert "authorization-id-required" in result.blockers[0]


def test_missing_stage109_eligibility_is_blocked(
    sandbox: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = SimpleNamespace(artifact=SimpleNamespace(eligible=False, status="disabled"))
    monkeypatch.setattr(invocation_runner, "evaluate_real_provider_preflight", lambda *a, **k: fake)
    result = _run(sandbox)
    assert "preflight-disabled" in result.blockers[0]


def test_missing_execution_authorization_token_is_blocked(sandbox: Path) -> None:
    result = _run(sandbox, config=_config(sandbox, execution_authorization_token=""))
    assert "execution-authorization-required" in result.blockers[0]
    assert result.artifact.network_requests == 0


def test_incorrect_execution_authorization_token_is_blocked(sandbox: Path) -> None:
    result = _run(sandbox, config=_config(sandbox, execution_authorization_token="WRONG"))
    assert "execution-authorization-invalid" in result.blockers[0]


def test_missing_credential_is_blocked_by_preflight(sandbox: Path) -> None:
    result = _run(sandbox, environ={})
    assert "blocked_missing_credential" in result.blockers[0]
    assert result.artifact.network_requests == 0


def test_invalid_endpoint_is_blocked(sandbox: Path) -> None:
    result = _run(sandbox, config=_config(sandbox, provider_url="https://invalid.example/v1"))
    assert "endpoint-not-allowlisted" in result.blockers[0]


def test_invalid_model_is_blocked(sandbox: Path) -> None:
    result = _run(sandbox, config=_config(sandbox, model="invalid-model"))
    assert "model-not-allowlisted" in result.blockers[0]


@pytest.mark.parametrize("changes", [
    {"chunk_count": 2}, {"chunk_index": 2}, {"single_chunk_only": False},
])
def test_multiple_chunk_contract_is_rejected(sandbox: Path, changes: dict[str, object]) -> None:
    result = _run(sandbox, config=_config(sandbox, **changes))
    assert "single-chunk-required" in result.blockers[0]


def test_multiple_session_contract_is_rejected(sandbox: Path) -> None:
    result = _run(sandbox, config=_config(sandbox, single_controlled_session=False))
    assert "single-session-required" in result.blockers[0]


def test_resume_is_rejected(sandbox: Path) -> None:
    result = _run(sandbox, config=_config(sandbox, resumed=True))
    assert "resume-forbidden" in result.blockers[0]


def test_chunk_size_is_frozen_to_600(sandbox: Path) -> None:
    result = _run(sandbox, config=_config(sandbox, chunk_size=601))
    assert "chunk-size-frozen" in result.blockers[0]


def test_invalid_artifact_extension_is_rejected(sandbox: Path) -> None:
    result = _run(sandbox, config=_config(sandbox, artifact_path=str(sandbox / "bad.txt")))
    assert "artifact-extension-invalid" in result.blockers[0]


def test_artifact_path_escape_is_rejected(sandbox: Path) -> None:
    result = _run(sandbox, config=_config(sandbox, artifact_path=str(ROOT / "outside1010.json")))
    assert "artifact-path-forbidden" in result.blockers[0]


def test_stage09_overwrite_path_is_rejected(sandbox: Path) -> None:
    result = _run(
        sandbox,
        config=_config(sandbox, artifact_path=str(ROOT / "artifacts/te_v7_stage09/invocation.json")),
    )
    assert "artifact-path-forbidden" in result.blockers[0]


def test_stage108_integrity_failure_blocks_current_preflight(
    sandbox: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        preflight_validator, "verify_freeze_artifact",
        lambda path: (_ for _ in ()).throw(ValueError("integrity failure")),
    )
    result = _run(sandbox)
    assert "blocked_freeze_integrity" in result.blockers[0]


def test_stage109_integrity_failure_is_rejected(
    sandbox: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        invocation_runner, "verify_preflight_artifact",
        lambda path: (_ for _ in ()).throw(ValueError("integrity failure")),
    )
    result = _run(sandbox)
    assert "stage109-integrity-required" in result.blockers[0]


def test_stage109_artifact_path_must_be_canonical(sandbox: Path) -> None:
    result = _run(
        sandbox,
        config=_config(sandbox, stage109_artifact_path=str(sandbox / "stage109.json")),
    )
    assert "stage109-integrity-required" in result.blockers[0]


def test_payload_and_prompt_preservation_are_recorded(sandbox: Path) -> None:
    artifact = _run(sandbox).artifact
    assert artifact.payload_preserved is True
    assert artifact.prompt_preserved is True


def test_retry_timing_and_fallback_are_preserved(sandbox: Path) -> None:
    transport = FakeSingleInvocationTransport(("timeout", "success"))
    result = _run(
        sandbox,
        config=_config(sandbox, attempt_plan=_plans(retry=True)),
        transport=transport,
    )
    assert result.artifact.attempt_count == 2
    assert result.artifact.total_retry_latency_ms >= 0
    assert result.artifact.fallback_used is True


def test_timeout_classification_is_preserved(sandbox: Path) -> None:
    artifact = _run(sandbox, transport=FakeSingleInvocationTransport(("timeout",))).artifact
    assert artifact.timeout_detected is True
    assert artifact.attempts[0].timeout is True


def test_http_503_classification_is_preserved(sandbox: Path) -> None:
    artifact = _run(sandbox, transport=FakeSingleInvocationTransport(("503",))).artifact
    assert artifact.http_503_detected is True
    assert artifact.attempts[0].http_503 is True


def test_exception_content_is_redacted(sandbox: Path) -> None:
    artifact = _run(sandbox, transport=FakeSingleInvocationTransport(("exception",))).artifact
    serialized = json.dumps(artifact.to_dict(), sort_keys=True)
    assert "fake exception content" not in serialized
    assert artifact.attempts[0].attempt_status == "failed"


def test_suspicious_short_output_is_signaled(sandbox: Path) -> None:
    transport = FakeSingleInvocationTransport(outputs=("太短。",))
    artifact = _run(sandbox, transport=transport).artifact
    assert artifact.suspicious_short_output is True


def test_empty_output_is_signaled(sandbox: Path) -> None:
    transport = FakeSingleInvocationTransport(outputs=("",))
    artifact = _run(sandbox, transport=transport).artifact
    assert artifact.empty_output is True
    assert artifact.translation_output_generated is False


def test_hangul_residue_is_signaled(sandbox: Path) -> None:
    transport = FakeSingleInvocationTransport(outputs=("한글잔류" * 30,))
    assert _run(sandbox, transport=transport).artifact.hangul_residue_signal is True


def test_invalid_response_format_is_signaled(sandbox: Path) -> None:
    transport = FakeSingleInvocationTransport(outputs=({"not": "text"},))
    assert _run(sandbox, transport=transport).artifact.response_format_invalid is True


def test_provider_refusal_is_signaled(sandbox: Path) -> None:
    transport = FakeSingleInvocationTransport(outputs=("I cannot assist with this request." * 5,))
    assert _run(sandbox, transport=transport).artifact.provider_refusal is True


def test_obvious_truncation_is_signaled() -> None:
    guard = inspect_translation_output("這是一段足夠長但結尾明顯中斷的內容" * 10 + "…", source_length=100)
    assert guard.obvious_truncation is True


def test_fake_provenance_cannot_become_real(sandbox: Path) -> None:
    transport = FakeSingleInvocationTransport()
    result = _run(
        sandbox,
        config=_config(sandbox, execution_mode="real"),
        transport=transport,
    )
    assert "transport-provenance-mismatch" in result.blockers[0]
    assert transport.network_requests == 0


def test_fake_validation_never_claims_real_execution(sandbox: Path) -> None:
    artifact = _run(sandbox).artifact
    assert artifact.status == "stage1010a_fake_transport_validated"
    assert artifact.real_provider_execution is False
    assert artifact.translation_output_generated is False


def test_no_comparison_baseline_or_candidate_is_created(sandbox: Path) -> None:
    artifact = _run(sandbox).artifact
    assert artifact.comparison_executed is False
    assert artifact.baseline_created is False and artifact.candidate_created is False


def test_no_readiness_or_production_claim_is_created(sandbox: Path) -> None:
    artifact = _run(sandbox).artifact
    assert artifact.readiness_evaluated is False
    assert artifact.production_ready is False
    assert artifact.human_review_required is True


def test_fake_tests_never_open_socket(sandbox: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("network request forbidden")
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    assert _run(sandbox).artifact.network_requests == 0


def test_fake_path_never_constructs_nvidia_client(
    sandbox: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        invocation_runner, "NvidiaClient",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("real client forbidden")),
    )
    assert _run(sandbox).artifact.network_requests == 0


def test_authorization_token_credential_and_source_are_absent_from_artifact(sandbox: Path) -> None:
    report = Path(_config(sandbox).artifact_path)
    _run(sandbox)
    serialized = report.read_text(encoding="utf-8")
    source_prefix = (ROOT / "tests/literary/Golden_Set/original_ko.txt").read_text(encoding="utf-8")[:30]
    assert EXECUTION_AUTHORIZATION_TOKEN not in serialized
    assert AUTHORIZATION_ID not in serialized
    assert FAKE_CREDENTIAL not in serialized
    assert source_prefix not in serialized


def test_artifact_integrity_tampering_fails_closed(sandbox: Path) -> None:
    report = Path(_config(sandbox).artifact_path)
    _run(sandbox)
    payload = json.loads(report.read_text(encoding="utf-8"))
    payload["network_requests"] = 1
    report.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="integrity failure"):
        verify_invocation_artifact(report)


def test_review_output_is_separate_from_evidence_integrity(sandbox: Path) -> None:
    report = Path(_config(sandbox).artifact_path)
    _run(sandbox)
    before = report.read_bytes()
    review = write_translation_review("人工作品檢查文字", sandbox / "review.txt", root=ROOT)
    assert review.read_text(encoding="utf-8").strip() == "人工作品檢查文字"
    assert report.read_bytes() == before


def test_cli_accepts_neither_api_key_nor_execution_token_argument() -> None:
    destinations = {action.dest for action in build_parser()._actions}
    assert "api_key" not in destinations
    assert "execution_authorization_token" not in destinations


def test_execution_authorization_is_hidden_from_config_repr(sandbox: Path) -> None:
    rendered = repr(_config(sandbox))
    assert EXECUTION_AUTHORIZATION_TOKEN not in rendered
    assert "execution_authorization_token" not in rendered


def test_one_runner_instance_cannot_execute_twice(sandbox: Path) -> None:
    runner = SingleRealInvocationRunner()
    first = runner.run(_config(sandbox), root=ROOT, environ={"NVIDIA_API_KEY": FAKE_CREDENTIAL})
    second = runner.run(_config(sandbox), root=ROOT, environ={"NVIDIA_API_KEY": FAKE_CREDENTIAL})
    assert first.artifact.status == "stage1010a_fake_transport_validated"
    assert "session-already-claimed" in second.blockers[0]


def test_non_golden_source_path_is_rejected(sandbox: Path) -> None:
    result = _run(sandbox, config=_config(sandbox, source_path="tests/literary/Smoke_Set/original_ko.txt"))
    assert "source-path-not-golden-set" in result.blockers[0]


def test_invalid_attempt_plan_is_rejected(sandbox: Path) -> None:
    invalid = (PreflightAttemptPlan(2, MODEL, 30, True),)
    result = _run(sandbox, config=_config(sandbox, attempt_plan=invalid))
    assert "attempt-plan-invalid" in result.blockers[0]


def test_version_and_entrypoint_remain_stage_local() -> None:
    assert INVOCATION_VERSION == "7.0.0-stage10.10A"
    source = (ROOT / "ntpe_single_real_provider_invocation.py").read_text(encoding="utf-8")
    assert "launcher_translate" not in source
    assert "ntpe_production_translate" not in source
    assert "requests" not in source
