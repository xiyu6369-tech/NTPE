from dataclasses import replace
import json
from pathlib import Path
import shutil

import pytest

from core.lcr_production_shadow_hook.batch107_real_provider_validation import (
    PACKAGE_RELATIVE_PATH,
    Batch107ExecutionResult,
    authorization_scope_fingerprint,
    execute_batch107,
    load_execution_package,
    package_integrity_fingerprint,
    validate_execution_package,
    validate_package_authorization,
)
from core.lcr_production_shadow_hook.single_chunk_execution_authorization import seal_authorization


ROOT = Path(__file__).resolve().parents[2]
NOW = "2026-07-18T04:00:00Z"


def package() -> dict:
    return json.loads((ROOT / PACKAGE_RELATIVE_PATH).read_text(encoding="utf-8"))


def reseal(value: dict) -> dict:
    value = json.loads(json.dumps(value))
    value["authorization_fingerprint"] = authorization_scope_fingerprint(value)
    value["package_integrity"]["payload_sha256"] = package_integrity_fingerprint(value)
    return value


def authorization(value=None, **changes):
    item = value or package()
    fields = dict(
        authorization_id="lcr-batch107-user-authorization",
        authorized_at="2026-07-18T03:55:00Z",
        expires_at="2026-07-18T04:30:00Z",
        document_id=item["document_id"],
        chunk_id=item["chunk_id"],
        source_hash=item["source_hash"],
        production_translation_hash=item["production_translation_hash"],
        rollback_baseline_hash=item["rollback_baseline_hash"],
        provider=item["provider"],
        model=item["model"],
        source_profile=item["source_profile"],
        target_profile=item["target_profile"],
        max_provider_requests=item["max_provider_requests"],
        max_network_requests=item["max_network_requests"],
        timeout_seconds=item["timeout_seconds"],
        retry_limit=0,
        allow_draft_request=True,
        allow_polish_request=True,
        allow_semantic_verification=True,
        allow_output_replacement=False,
        allow_resume_write=False,
        allow_cache_write=False,
        allow_store_write=False,
        allow_cross_provider_fallback=False,
        allow_automatic_rollout=False,
        explicit_execution_authorization=True,
        reviewer_identity_hash="a" * 64,
    )
    fields.update(changes)
    return seal_authorization(**fields)


class FakeProvider:
    provenance = "fake"

    def __init__(self, outputs=None):
        self.outputs = list(outputs or (
            "鄭泰義感到十分為難，但這並不是他應該為難的事。",
            "鄭泰義感到為難，但實際上這並不是他該為難的事。",
        ))
        self.calls = []
        self.network_requests = 0

    def __call__(self, request):
        self.calls.append(dict(request))
        self.network_requests += 1
        return self.outputs[len(self.calls) - 1]


class State:
    value = "passed"


class PassedVerification:
    status = State()


def sandbox(tmp_path: Path) -> Path:
    target = tmp_path / "artifacts/tic_batch2/TRANSLATION_CASES.json"
    target.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / "artifacts/tic_batch2/TRANSLATION_CASES.json", target)
    return tmp_path


def execute(tmp_path, *, value=None, auth=None, provider=None, environ=None, **changes) -> Batch107ExecutionResult:
    item = value or package()
    values = dict(
        package=item,
        authorization=auth or authorization(item),
        root=sandbox(tmp_path),
        now=NOW,
        confirm_execution_id=item["execution_id"],
        environ={"NVIDIA_API_KEY": "offline-fake-secret"} if environ is None else environ,
        provider=provider or FakeProvider(),
        test_mode=True,
        semantic_verifier=lambda item: PassedVerification(),
    )
    values.update(changes)
    return execute_batch107(**values)


def test_prepared_package_is_immutable_integrity_bound_and_zero_request():
    item = load_execution_package(PACKAGE_RELATIVE_PATH, root=ROOT)
    assert not validate_execution_package(item)
    assert item["execution_status"] == "awaiting_user_authorization"
    assert item["real_provider_execution_authorized"] is False
    assert item["provider_requests"] == item["network_requests"] == 0
    with pytest.raises(TypeError):
        item["provider_requests"] = 1


def test_exact_authorization_and_expiration_gate():
    item = package()
    assert validate_package_authorization(item, authorization(item), now=NOW)[0]
    expired = authorization(item, expires_at=NOW)
    valid, reasons = validate_package_authorization(item, expired, now=NOW)
    assert not valid and "authorization_expired" in reasons


@pytest.mark.parametrize("field", ["document_id", "chunk_id", "source_hash", "production_translation_hash", "provider", "model"])
def test_each_exact_match_field_blocks_before_provider(tmp_path, field):
    item = package()
    altered = "0" * 64 if "hash" in field else "other"
    provider = FakeProvider()
    result = execute(tmp_path, value=item, auth=authorization(item, **{field: altered}), provider=provider)
    assert result.status == "blocked" and result.provider_requests == result.network_requests == 0
    assert not provider.calls


@pytest.mark.parametrize("field", ["source_hash", "production_translation_hash"])
def test_source_or_production_content_hash_mismatch_blocks_before_provider(tmp_path, field):
    item = package()
    item[field] = "0" * 64
    if field == "production_translation_hash":
        item["rollback_baseline_hash"] = item[field]
    item = reseal(item)
    provider = FakeProvider()
    result = execute(tmp_path, value=item, auth=authorization(item), provider=provider)
    assert result.status == "blocked" and not provider.calls
    assert result.provider_requests == result.network_requests == 0


def test_request_budget_retry_and_fallback_are_fail_closed(tmp_path):
    item = package()
    for index, changes in enumerate((
        {"max_provider_requests": 1, "max_network_requests": 1},
        {"retry_limit": 1},
        {"allow_cross_provider_fallback": True},
    )):
        provider = FakeProvider()
        result = execute(tmp_path / str(index), value=item, auth=authorization(item, **changes), provider=provider)
        assert result.status == "blocked" and not provider.calls


def test_two_requests_complete_and_third_request_is_structurally_unreachable(tmp_path):
    provider = FakeProvider()
    result = execute(tmp_path, provider=provider)
    assert result.outcome == "verified_candidate"
    assert result.provider_requests == result.network_requests == 2
    assert [call["request_kind"] for call in provider.calls] == ["draft", "polish"]
    assert result.retry_count == 0 and result.fallback_used is False


def test_missing_credential_blocks_without_claim_or_provider_call(tmp_path):
    provider = FakeProvider()
    result = execute(tmp_path, provider=provider, environ={})
    assert result.status == "credential_unavailable" and not provider.calls
    assert not (tmp_path / "artifacts/lcr_batch107_review").exists()


def test_artifact_path_is_fixed_safe_atomic_and_execution_is_at_most_once(tmp_path):
    provider = FakeProvider()
    result = execute(tmp_path, provider=provider)
    path = Path(result.review_artifact_path)
    assert path.parent == (tmp_path / "artifacts/lcr_batch107_review").resolve()
    assert not list(path.parent.glob("*.tmp-*"))
    second = execute_batch107(
        package(), authorization=authorization(), root=tmp_path, now=NOW,
        confirm_execution_id=package()["execution_id"], environ={"NVIDIA_API_KEY": "offline-fake-secret"},
        provider=FakeProvider(), test_mode=True, semantic_verifier=lambda item: PassedVerification(),
    )
    assert second.status == "blocked" and "execution_already_claimed" in second.reason_codes


def test_tampered_review_path_and_package_integrity_are_rejected():
    item = package()
    item["review_artifact_directory"] = "../../escape"
    item = reseal(item)
    assert "review_artifact_directory_not_allowlisted" in validate_execution_package(item)
    item = package()
    item["provider_requests"] = 1
    assert "prepared_package_request_count_not_zero" in validate_execution_package(item)
    assert "execution_package_integrity_mismatch" in validate_execution_package(item)


@pytest.mark.parametrize("output", ["", "I cannot assist with that request.", "번역할 수 없습니다.", "短文..."])
def test_empty_refusal_hangul_and_truncation_fail_without_retry(tmp_path, output):
    provider = FakeProvider((output,))
    result = execute(tmp_path, provider=provider)
    assert result.outcome == "provider_failed" and len(provider.calls) == 1
    assert result.draft_request_status == "failed" and result.polish_request_status == "not_run"
    assert result.retry_count == 0 and result.fallback_used is False


def test_secret_never_appears_in_package_claim_or_review_artifact(tmp_path):
    secret = "nvapi-offline-super-secret-value"
    result = execute(tmp_path, environ={"NVIDIA_API_KEY": secret})
    assert result.outcome == "verified_candidate"
    combined = b"".join(path.read_bytes() for path in (tmp_path / "artifacts/lcr_batch107_review").glob("*.json"))
    assert secret.encode() not in combined
    assert b"Bearer " not in combined
