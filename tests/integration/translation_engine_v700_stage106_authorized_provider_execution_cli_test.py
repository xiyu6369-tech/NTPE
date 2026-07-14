from __future__ import annotations

import inspect
import json
import shutil
import socket
import uuid
from pathlib import Path

import pytest

from core.adaptive_context_authorized_provider_cli import (
    CLI_VERSION,
    AuthorizedProviderCliConfig,
    build_parser,
    parse_config,
    resolve_stage10_report_path,
    run_authorized_provider_cli,
)
from core.adaptive_context_authorized_provider_harness import FakeAuthorizedProviderTransport
from core.adaptive_context_provider_benchmark_session import ProviderAttemptPlan

ROOT = Path(__file__).resolve().parents[2]
MODEL = "meta/llama-3.3-70b-instruct"
URL = "https://integrate.api.nvidia.com/v1/chat/completions"


def _config(**changes: object) -> AuthorizedProviderCliConfig:
    values: dict[str, object] = {
        "boundary_enabled": True,
        "real_provider_enabled": True,
        "authorization_id": "stage106-authorization",
        "execution_mode": "fake",
        "provider": "nvidia",
        "provider_url": URL,
        "model": MODEL,
        "session_id": "stage106-session",
        "source_fingerprint": "a" * 64,
        "chunk_fingerprint": "b" * 64,
        "chunk_index": 1,
    }
    values.update(changes)
    return AuthorizedProviderCliConfig(**values)


def _run(**changes: object):
    return run_authorized_provider_cli(_config(**changes), root=ROOT, environ={})


def test_cli_is_disabled_by_default_and_requires_three_gates() -> None:
    blockers = AuthorizedProviderCliConfig().validate()
    assert "authorized-harness-boundary-enable-required" in blockers
    assert "authorized-harness-real-provider-enable-required" in blockers
    assert "authorized-harness-authorization-id-required" in blockers


@pytest.mark.parametrize("field,blocker", [
    ("boundary_enabled", "authorized-harness-boundary-enable-required"),
    ("real_provider_enabled", "authorized-harness-real-provider-enable-required"),
    ("authorization_id", "authorized-harness-authorization-id-required"),
])
def test_each_authorization_gate_fails_closed(field: str, blocker: str) -> None:
    value: object = "" if field == "authorization_id" else False
    with pytest.raises(ValueError, match=blocker):
        _run(**{field: value})


@pytest.mark.parametrize("field,value,blocker", [
    ("provider", "custom", "provider-not-allowlisted"),
    ("provider_url", "https://invalid.example/v1", "endpoint-not-allowlisted"),
    ("model", "unapproved", "model-not-allowlisted"),
])
def test_provider_endpoint_and_model_allowlists_are_reused(
    field: str, value: str, blocker: str,
) -> None:
    with pytest.raises(ValueError, match=blocker):
        _run(**{field: value})


@pytest.mark.parametrize("field", ["source_fingerprint", "chunk_fingerprint"])
def test_fingerprints_must_be_sha256_shape(field: str) -> None:
    with pytest.raises(ValueError, match="fingerprint-invalid"):
        _run(**{field: "raw source is forbidden"})


def test_only_one_chunk_is_admitted() -> None:
    with pytest.raises(ValueError, match="single-chunk-required"):
        _run(chunk_index=2)


def test_parser_exposes_no_raw_secret_or_content_arguments() -> None:
    destinations = {action.dest for action in build_parser()._actions}
    assert not destinations.intersection({
        "api_key", "credential", "source_text", "prompt", "request_body",
        "response_body", "payload", "production_launcher_hook",
    })


def test_parser_rejects_api_key_argument() -> None:
    with pytest.raises(SystemExit):
        parse_config(["--api-key", "secret", "--session-id", "s",
                      "--source-fingerprint", "a" * 64, "--chunk-fingerprint", "b" * 64])


def test_fake_transport_runs_exactly_one_controlled_session() -> None:
    transport = FakeAuthorizedProviderTransport()
    result = run_authorized_provider_cli(_config(), root=ROOT, transport=transport, environ={})
    assert transport.calls == 1
    assert result.harness_result.single_controlled_session is True
    assert result.harness_result.invocation.session.summary.attempts_executed == 1


def test_fake_transport_does_not_access_environment_credential() -> None:
    result = run_authorized_provider_cli(
        _config(), root=ROOT, environ={"NVIDIA_API_KEY": "stage106-secret-key"},
    )
    assert result.harness_result.invocation.credential_source == "not_accessed"
    assert "stage106-secret-key" not in json.dumps(result.to_dict())


def test_real_mode_requires_dependency_injected_transport() -> None:
    with pytest.raises(ValueError, match="real-transport-dependency-required"):
        _run(execution_mode="real")


def test_transport_provenance_mismatch_fails_before_execution() -> None:
    transport = FakeAuthorizedProviderTransport()
    with pytest.raises(ValueError, match="transport-provenance-mismatch"):
        run_authorized_provider_cli(
            _config(execution_mode="real"), root=ROOT, transport=transport, environ={},
        )
    assert transport.calls == 0


def test_retry_timeout_and_fallback_evidence_are_preserved() -> None:
    transport = FakeAuthorizedProviderTransport(("timeout", "success"))
    plans = (
        ProviderAttemptPlan(1, MODEL, 30, False, 100, 80),
        ProviderAttemptPlan(2, MODEL, 60, True, 100, 80),
    )
    result = run_authorized_provider_cli(
        _config(), root=ROOT, transport=transport, plans=plans, environ={},
    )
    rows = result.harness_result.invocation.session.evidence.records
    assert len(rows) == 2 and rows[0].error_category == "timeout"
    assert rows[1].fallback_used is True


def test_http_503_evidence_is_preserved() -> None:
    result = run_authorized_provider_cli(
        _config(), root=ROOT, transport=FakeAuthorizedProviderTransport(("503",)), environ={},
    )
    row = result.harness_result.invocation.session.evidence.records[0]
    assert row.http_status == 503 and row.error_category == "http_503"


def test_report_path_is_limited_and_report_is_redacted() -> None:
    sandbox = ROOT / ".ntpe_test_sandbox" / "stage106" / uuid.uuid4().hex
    report = sandbox / "report.json"
    try:
        result = run_authorized_provider_cli(
            _config(report_path=str(report), authorization_id="stage106-secret-auth"),
            root=ROOT, environ={},
        )
        content = Path(result.report_path).read_text(encoding="utf-8")
        assert "stage106-secret-auth" not in content
        assert '"content_redacted": true' in content
    finally:
        shutil.rmtree(ROOT / ".ntpe_test_sandbox" / "stage106", ignore_errors=True)


def test_report_path_rejects_outside_destination() -> None:
    with pytest.raises(ValueError, match="outside-stage10-sandbox"):
        resolve_stage10_report_path(ROOT / "outside.json", root=ROOT)


def test_stage09_report_overwrite_is_rejected() -> None:
    with pytest.raises(ValueError):
        resolve_stage10_report_path(ROOT / "artifacts/te_v7_stage09/report.json", root=ROOT)


def test_fake_cli_performs_no_network_request(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("network access forbidden")
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    result = _run()
    assert result.network_requests == 0


def test_cli_does_not_evaluate_comparison_or_readiness() -> None:
    result = _run()
    assert result.comparison_evaluated is False
    assert result.readiness_evaluated is False
    assert result.harness_result.baseline_artifact_created is False
    assert result.harness_result.candidate_artifact_created is False


def test_cli_entrypoint_has_no_production_hook_import() -> None:
    source = (ROOT / "ntpe_authorized_provider_invocation.py").read_text(encoding="utf-8")
    assert "launcher_translate" not in source
    assert "ntpe_production_translate" not in source
    assert "requests" not in source and "httpx" not in source


def test_cli_version_and_runner_contract_are_explicit() -> None:
    assert CLI_VERSION == "7.0.0-stage10.6"
    signature = inspect.signature(run_authorized_provider_cli)
    assert "transport" in signature.parameters and "plans" in signature.parameters
