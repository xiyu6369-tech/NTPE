from dataclasses import asdict, replace

import pytest

from core.lcr_production_shadow_hook.single_chunk_execution_authorization import (
    seal_authorization,
    validate_execution_authorization,
)


NOW = "2026-07-18T02:00:00Z"


def authorization(**changes):
    values = dict(
        authorization_id="auth-106", authorized_at="2026-07-18T01:00:00Z", expires_at="2026-07-18T03:00:00Z",
        document_id="doc", chunk_id="chunk", source_hash="a" * 64, production_translation_hash="b" * 64,
        rollback_baseline_hash="b" * 64, provider="fake-provider", model="fake-model", source_profile="ko",
        target_profile="zh-Hant", explicit_execution_authorization=True, reviewer_identity_hash="c" * 64,
    )
    values.update(changes)
    return seal_authorization(**values)


def validate(value=None, **changes):
    values = dict(now=NOW, document_id="doc", chunk_id="chunk", source_hash="a" * 64,
                  production_translation_hash="b" * 64, rollback_baseline_hash="b" * 64,
                  provider="fake-provider", model="fake-model", source_profile="ko", target_profile="zh-Hant")
    values.update(changes)
    return validate_execution_authorization(value, **values)


def test_valid_authorization_is_immutable_and_fingerprint_bound():
    item = authorization()
    assert validate(item)[0]
    with pytest.raises(Exception):
        item.model = "other"
    assert not validate(replace(item, model="other"))[0]


@pytest.mark.parametrize("changes", [
    {"explicit_execution_authorization": False}, {"authorized_at": "bad"},
    {"authorized_at": "2026-07-18T02:30:00Z"}, {"authorized_at": "2026-07-18T03:00:00Z"},
    {"expires_at": "2026-07-18T02:00:00Z"}, {"max_provider_requests": 3},
    {"max_network_requests": 3}, {"max_network_requests": 1}, {"timeout_seconds": 0},
    {"timeout_seconds": 26}, {"retry_limit": 1}, {"allow_draft_request": False},
    {"allow_semantic_verification": False}, {"allow_output_replacement": True},
    {"allow_resume_write": True}, {"allow_cache_write": True}, {"allow_store_write": True},
    {"allow_cross_provider_fallback": True}, {"allow_automatic_rollout": True},
    {"reviewer_identity_hash": ""},
])
def test_negative_authorization_policy_branches_are_blocked(changes):
    assert not validate(authorization(**changes))[0]


@pytest.mark.parametrize("field,value", [
    ("document_id", "other"), ("chunk_id", "other"), ("source_hash", "d" * 64),
    ("production_translation_hash", "d" * 64), ("rollback_baseline_hash", "d" * 64),
    ("provider", "other"), ("model", "other"), ("source_profile", "en"), ("target_profile", "ja"),
])
def test_each_identity_mismatch_is_blocked(field, value):
    assert not validate(authorization(), **{field: value})[0]


def test_missing_authorization_and_fingerprint_mismatch_are_blocked():
    assert validate(None) == (False, ("missing_authorization",))
    assert not validate(replace(authorization(), authorization_fingerprint="0" * 64))[0]
