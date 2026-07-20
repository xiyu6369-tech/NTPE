from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

import core.prompt_contract_verification_canary.candidate_structural_canary as canary
from core.prompt_contract_verification_canary.framework import ProviderOutcome
from tools.generate_te_v720_stage1258_candidate_structural_verification_canary import build_preparation_artifacts

ROOT = Path(__file__).resolve().parents[2]
SOURCE = "영희가 민수와 선생님을 번갈아 보며 말했다. ‘선생님, 민수 씨도 함께 가실까요?’"


def config(**changes: object) -> canary.Stage1258Config:
    values = {
        "authorization_id": "offline-test", "authorization_token": canary.AUTHORIZATION_TOKEN,
        "preparation_commit": "f76a85a",
    }
    values.update(changes)
    return canary.Stage1258Config(**values)


def all_preflight_overrides() -> dict[str, bool]:
    return {name: True for name in canary.PREPARATION_STEPS}


def test_preflight_order_and_exact_resolution_before_claim(tmp_path: Path) -> None:
    claim = tmp_path / "authorization_claim.json"
    result, plan = canary.build_preflight(
        ROOT, config(), claim_path=claim, check_overrides=all_preflight_overrides(),
    )
    assert result["status"] == "PASS" and plan is not None
    assert [row["name"] for row in result["ordered_steps"]] == list(canary.PREPARATION_STEPS)
    assert plan["logical_id"] == canary.LOGICAL_ID and plan["canonical_id"] == canary.CANONICAL_ID
    assert plan["source_hash"] == canary.SOURCE_HASH and plan["fixture_hash"] == canary.FIXTURE_HASH
    assert not claim.exists()


def test_claim_not_created_on_dirty_worktree(tmp_path: Path) -> None:
    overrides = all_preflight_overrides()
    overrides["git_worktree_clean"] = False
    claim = tmp_path / "authorization_claim.json"
    result, plan = canary.build_preflight(ROOT, config(), claim_path=claim, check_overrides=overrides)
    assert result["status"] == "FAIL" and plan is None
    assert result["claim_created"] is False and result["provider_requests"] == 0
    assert not claim.exists()


def test_single_request_retry_and_fallback_are_hard_limited() -> None:
    assert config().blockers() == []
    assert "single_request_contract_invalid" in config(authorized_request_budget=2).blockers()
    assert "single_request_contract_invalid" in config(attempts=2).blockers()
    assert "retry_or_fallback_forbidden" in config(retry_allowed=True).blockers()
    assert "retry_or_fallback_forbidden" in config(fallback_allowed=True).blockers()
    assert "parallel_or_rerun_forbidden" in config(automatic_rerun_allowed=True).blockers()


def test_single_use_claim_and_historical_claims_are_not_replayed(tmp_path: Path) -> None:
    plan = canary.build_candidate_request_plan(ROOT)
    claim = canary.build_claim(config(), plan, created_at=1.0)
    target = tmp_path / "authorization_claim.json"
    canary.create_single_use_claim(target, claim)
    with pytest.raises(ValueError, match="replay-rejected"):
        canary.create_single_use_claim(target, claim)
    historical = [
        ROOT / "artifacts/te_v72_stage1256_prompt_verification_canary/authorization_claim.json",
        ROOT / "artifacts/te_v72_stage1257_prompt_verification_canary/authorization_claim.json",
    ]
    before = [path.read_bytes() for path in historical]
    assert [path.read_bytes() for path in historical] == before


class OneShotTransport:
    provenance = "real"

    def __init__(self, outcome: ProviderOutcome | None = None, error: Exception | None = None) -> None:
        self.outcome, self.error, self.calls = outcome, error, 0

    def invoke(self, **_kwargs: object) -> ProviderOutcome:
        self.calls += 1
        if self.error is not None: raise self.error
        assert self.outcome is not None
        return self.outcome


def _execute_isolated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, transport: OneShotTransport) -> dict[str, object]:
    source_plan = canary.build_candidate_request_plan(ROOT)
    passed = {"stage": canary.STAGE_ID, "status": "PASS", "ordered_steps": [],
              "claim_created": False, "provider_requests": 0, "network_requests": 0, "fail_closed": False}
    monkeypatch.setattr(canary, "build_preflight", lambda *_args, **_kwargs: (passed, source_plan))
    return canary.execute_stage1258(config(), root=tmp_path, transport=transport)


def test_timeout_and_top_level_exception_never_rerun(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    timeout_transport = OneShotTransport(ProviderOutcome(False, "", 180.0, timeout=True, error="provider_timeout"))
    timeout_result = _execute_isolated(tmp_path / "timeout", monkeypatch, timeout_transport)
    assert timeout_transport.calls == 1 and timeout_result["provider_requests"] == 1
    assert timeout_result["canary_status"] == "inconclusive_provider_timeout"
    exception_transport = OneShotTransport(error=RuntimeError("local-failure"))
    exception_result = _execute_isolated(tmp_path / "exception", monkeypatch, exception_transport)
    assert exception_transport.calls == 1 and exception_result["provider_requests"] == 1
    assert exception_result["canary_status"] == "inconclusive_provider_error"


@pytest.mark.parametrize(
    ("output", "failure"),
    [
        (SOURCE, "exact_source_echo"),
        ("영희가 민수와 선생님", "partial_source_echo"),
        ("譯文：英熙望著敏洙與老師。", "forbidden_label"),
        (chr(96) * 3 + "\n英熙望向老師。\n" + chr(96) * 3, "markdown_wrapper"),
        ('{"translation":"英熙望向老師。"}', "json_wrapper"),
        ("", "empty_output"),
        ("她說", "abnormal_short_output"),
        ("英熙望向老師，接著說…", "terminal_truncation"),
        ("英熙望向老師。\n英熙望向老師。", "repeated_output_block"),
        ("她说这句话时看着老师和学生。", "traditional_chinese_target_signal"),
    ],
)
def test_structural_failure_detectors(output: str, failure: str) -> None:
    result = canary.validate_candidate_output(SOURCE, output, success=True, timeout=False)
    assert failure in result["failures"]
    assert result["canary_status"] == "candidate_structural_failed"


def test_structural_pass_and_activation_gate_invariants() -> None:
    result = canary.validate_candidate_output(SOURCE, "英熙輪流看了敏洙與老師一眼，問道：「老師，敏洙先生也一起去嗎？」", success=True, timeout=False)
    assert result["candidate_structural_pass"] is True
    artifacts = {path.name: json.loads(data) for path, data in build_preparation_artifacts().items()}
    activation = artifacts["activation_contract.json"]
    assert activation["maximum_gate_on_structural_pass"] == canary.PASS_GATE
    assert activation["production_authorized"] is False
    assert activation["candidate_improved"] is None


def test_preparation_generation_is_deterministic_and_secret_free() -> None:
    first = build_preparation_artifacts()
    second = build_preparation_artifacts()
    assert first == second
    raw = b"".join(first.values()).lower()
    assert b"bearer " not in raw and b"x-api-key" not in raw and b"api_key" not in raw
    assert all(path.name not in {"authorization_claim.json", "candidate_response.json"} for path in first)


def test_request_plan_fingerprint_is_stable() -> None:
    first = canary.build_candidate_request_plan(ROOT)
    second = canary.build_candidate_request_plan(ROOT)
    assert first["request_plan_fingerprint"] == second["request_plan_fingerprint"]
    assert hashlib.sha256(canary.canonical({
        key: first[key] for key in (
            "stage_id", "provider", "model", "arm", "logical_id", "canonical_id", "source_hash",
            "fixture_hash", "system_prompt_fingerprint", "prompt_fingerprint",
            "authorized_request_budget", "attempts", "retry_allowed", "fallback_allowed",
            "automatic_rerun_allowed",
        )
    })).hexdigest() == first["request_plan_fingerprint"]
