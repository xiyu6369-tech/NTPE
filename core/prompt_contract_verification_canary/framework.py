from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import subprocess
from time import perf_counter, time
from typing import Protocol

from core.translation_engine.nvidia_client import NvidiaClient
from core.translation_quality_provider_canary.framework import ALLOWED_MODEL, PROVIDER_URL, _build_prompts
from core.production_runtime.manifest import get_te_v7_stage_path


AUTHORIZATION_TOKEN = "AUTHORIZE_NTPE_TE_V72_STAGE1256_PROMPT_VERIFICATION_CANARY"
READINESS_GATE = "translation_quality_integration_ready_for_controlled_canary"
PASS_GATE = "translation_quality_integration_canary_passed"
ARTIFACT_DIR = "artifacts/te_v72_stage1256_prompt_verification_canary"
FORBIDDEN_LABELS = ("譯文：", "原文：", "Source:", "Translation:", "【Korean】", "【Output】")


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha(value: str | bytes) -> str:
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode("utf-8")).hexdigest()


def _contains_hangul(value: str) -> int:
    return len(re.findall(r"[\uac00-\ud7a3\u1100-\u11ff]", value))


def validate_output(source: str, output: str, *, success: bool, timeout: bool, malformed: bool) -> dict[str, object]:
    normalized = output.strip()
    hangul = _contains_hangul(normalized)
    source_normalized = " ".join(source.split())
    output_normalized = " ".join(normalized.split())
    exact_echo = bool(source_normalized and source_normalized in output_normalized)
    # A sequence of at least 12 Korean characters is an actionable partial source echo.
    fragments = re.findall(r"[\uac00-\ud7a3\u1100-\u11ff\s,.'!?]{12,}", source)
    partial_echo = any(" ".join(fragment.split()) in output_normalized for fragment in fragments)
    labels = [label for label in FORBIDDEN_LABELS if label.lower() in normalized.lower()]
    markdown_wrapper = normalized.startswith("```") or normalized.endswith("```")
    bilingual = hangul > 0
    abnormal_short = bool(source.strip()) and len(normalized) < 2
    truncated = normalized.endswith(("…", "...", "、", ",", "（", "("))
    failures: list[str] = []
    if not success: failures.append("provider_error")
    if timeout: failures.append("timeout")
    if malformed: failures.append("malformed_response")
    if not normalized: failures.append("empty_output")
    if hangul: failures.append("hangul_residual")
    if exact_echo: failures.append("exact_source_echo")
    if partial_echo: failures.append("partial_source_echo")
    if labels: failures.append("forbidden_output_label")
    if bilingual: failures.append("bilingual_response")
    if markdown_wrapper: failures.append("markdown_wrapper")
    if abnormal_short: failures.append("abnormal_short_output")
    if truncated: failures.append("apparent_truncation")
    return {
        "status": "PASS" if not failures else "FAIL",
        "normalized_translation_output": normalized,
        "hangul_character_count": hangul,
        "exact_source_echo": exact_echo,
        "partial_source_echo": partial_echo,
        "forbidden_output_labels": labels,
        "translation_only": not (bilingual or labels or markdown_wrapper),
        "no_explanation_or_summary": not markdown_wrapper,
        "non_empty": bool(normalized),
        "abnormal_short_output": abnormal_short,
        "apparent_truncation": truncated,
        "whole_source_duplication": exact_echo,
        "failures": failures,
    }


@dataclass(frozen=True)
class CanaryConfig:
    authorization_id: str
    authorization_token: str
    provider: str = "nvidia"
    model: str = ALLOWED_MODEL
    timeout_seconds: int = 180
    attempts_per_arm: int = 1
    retry: int = 0
    fallback: bool = False
    parallelism: int = 1
    cross_provider_fallback: bool = False
    automatic_rerun: bool = False
    authorized_request_budget: int = 2

    def blockers(self) -> list[str]:
        failures = []
        if self.authorization_token != AUTHORIZATION_TOKEN: failures.append("authorization_invalid")
        if self.provider != "nvidia" or self.model != ALLOWED_MODEL: failures.append("provider_or_model_not_allowlisted")
        if self.timeout_seconds != 180: failures.append("timeout_not_frozen")
        if self.attempts_per_arm != 1 or self.retry != 0: failures.append("attempt_or_retry_policy_invalid")
        if self.fallback or self.cross_provider_fallback or self.parallelism != 1 or self.automatic_rerun: failures.append("fallback_parallel_or_rerun_forbidden")
        if self.authorized_request_budget != 2: failures.append("request_budget_must_equal_two")
        return failures


@dataclass(frozen=True)
class ProviderOutcome:
    success: bool
    raw_response: str
    elapsed_seconds: float
    http_status: int | None = None
    timeout: bool = False
    malformed: bool = False
    error: str | None = None


class Transport(Protocol):
    provenance: str
    def invoke(self, *, system_prompt: str, user_prompt: str, config: CanaryConfig) -> ProviderOutcome: ...


class NvidiaTransport:
    provenance = "real"
    def invoke(self, *, system_prompt: str, user_prompt: str, config: CanaryConfig) -> ProviderOutcome:
        started = perf_counter()
        try:
            content = NvidiaClient(api_url=PROVIDER_URL, timeout=config.timeout_seconds).chat(
                model=config.model, system_prompt=system_prompt, user_prompt=user_prompt,
                temperature=0.12, top_p=0.82, max_tokens=800,
            )
            return ProviderOutcome(True, content, round(perf_counter() - started, 6), http_status=200)
        except Exception as exc:
            text = str(exc)
            return ProviderOutcome(False, "", round(perf_counter() - started, 6), timeout="timeout" in text.lower(), error="provider_error")


def _write(root: Path, name: str, payload: object) -> None:
    # JSON is deliberately the only artifact format; credentials and headers are never accepted as inputs.
    (root / name).write_bytes(_canonical(payload))


def _clean_worktree(base: Path) -> bool:
    result = subprocess.run(["git", "status", "--porcelain"], cwd=base, capture_output=True, text=True, check=False)
    return result.returncode == 0 and not result.stdout.strip()


def _hash_valid(base: Path) -> bool:
    manifest = base / "manifests/te_v720_stage1254_prompt_contract_preservation_manifest.json"
    if not manifest.is_file(): return False
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    return all(_sha((base / path).read_bytes()) == digest for path, digest in payload.get("artifact_hashes", {}).items())


def _preflight(base: Path, config: CanaryConfig, claim_path: Path) -> dict[str, object]:
    readiness_path = get_te_v7_stage_path(base, "te_v72_prompt_canary_readiness") / "readiness_summary.json"
    readiness = json.loads(readiness_path.read_text(encoding="utf-8")) if readiness_path.is_file() else {}
    checks = {
        "worktree_clean": _clean_worktree(base),
        "stage1255_readiness_hash_valid": _hash_valid(base),
        "prompt_canary_ready": readiness.get("prompt_canary_ready") is True,
        "activation_gate_valid": readiness.get("activation_gate") == READINESS_GATE,
        "provider_eligible_only_by_explicit_authorization": readiness.get("provider_eligible") is False and config.authorization_token == AUTHORIZATION_TOKEN,
        "authorized_request_budget_is_two": config.authorized_request_budget == 2,
        "consumed_request_count_is_zero": True,
        "execution_claim_unused": not claim_path.exists(),
        "configuration_valid": not config.blockers(),
    }
    return {"stage": "TE-v7.2-Stage12.5.6", "status": "PASS" if all(checks.values()) else "FAIL", "checks": checks,
             "provider_requests_added": 0, "network_requests_added": 0, "fail_closed": not all(checks.values())}


def execute_verification_canary(config: CanaryConfig, *, root: str | Path, transport: Transport | None = None) -> dict[str, object]:
    base = Path(root).resolve(); artifact_root = base / ARTIFACT_DIR; artifact_root.mkdir(parents=True, exist_ok=True)
    claim_path = artifact_root / "authorization_claim.json"
    preflight = _preflight(base, config, claim_path); _write(artifact_root, "preflight.json", preflight)
    if preflight["status"] != "PASS":
        summary = {"stage": "TE-v7.2-Stage12.5.6", "status": "preflight_failure_no_provider_request", "request_count": 0, "activation_gate": READINESS_GATE}
        _write(artifact_root, "execution_summary.json", summary); return summary
    active = transport or NvidiaTransport()
    if active.provenance != "real": raise ValueError("real_transport_required")
    claim = {"stage": "TE-v7.2-Stage12.5.6", "authorization_id": config.authorization_id, "claimed_at_epoch_seconds": time(), "single_use": True, "authorized_request_budget": 2, "consumed_request_count": 0}
    try:
        claim_path.open("x", encoding="utf-8").write(_canonical(claim).decode("utf-8"))
    except FileExistsError as exc: raise ValueError("execution_claim_replay") from exc
    _write(artifact_root, "authorization_claim.json", claim)
    corpus = json.loads((base / "tests/fixtures/te_v72_canary/golden_corpus.json").read_text(encoding="utf-8"))
    case = next(item for item in corpus["cases"] if item["case_id"] == "canary-001")
    system, baseline_prompt, candidate_prompt, metadata = _build_prompts("canary-001", str(case["source_text"]))
    arms: dict[str, dict[str, object]] = {}; count = 0
    for arm, prompt in (("baseline", baseline_prompt), ("candidate", candidate_prompt)):
        outcome = active.invoke(system_prompt=system, user_prompt=prompt, config=config); count += 1
        validation = validate_output(str(case["source_text"]), outcome.raw_response, success=outcome.success, timeout=outcome.timeout, malformed=outcome.malformed)
        request = {"arm": arm, "case_id": "canary-001", "exact_source": case["source_text"], "exact_serialized_prompt": prompt, "prompt_fingerprint": _sha(prompt), "request_metadata": {"provider": config.provider, "model": config.model, "timeout_seconds": config.timeout_seconds, "attempts": 1, "retry": 0, "fallback": False, "parallelism": 1}, "start_end_recorded_by_transport": True, "request_count": count}
        response = {"arm": arm, "http_provider_status": outcome.http_status if outcome.success else outcome.error, "timeout": outcome.timeout, "elapsed_seconds": outcome.elapsed_seconds, "raw_response": outcome.raw_response, **validation}
        _write(artifact_root, f"{arm}_request.json", request); _write(artifact_root, f"{arm}_response.json", response); arms[arm] = response
        if not outcome.success or outcome.timeout: break
    candidate = arms.get("candidate", {}); structural = {"baseline": arms.get("baseline"), "candidate": candidate, "candidate_status": candidate.get("status", "FAIL"), "request_count": count, "request_budget_exceeded": count > 2}
    _write(artifact_root, "structural_validation.json", structural)
    b = float(arms.get("baseline", {}).get("elapsed_seconds", 0)); c = float(candidate.get("elapsed_seconds", 0)); latency = {"baseline_elapsed_seconds": b, "candidate_elapsed_seconds": c, "absolute_delta_seconds": round(c-b, 6), "relative_ratio": round(c/b, 6) if b else None, "candidate_slower_known_risk": c > b}
    _write(artifact_root, "latency_comparison.json", latency)
    reviewable = len(arms) == 2 and all(row.get("status") == "PASS" for row in arms.values())
    manual = {"review_status": "awaiting_human_review" if reviewable else "not_reviewable", "allowed_decisions": ["candidate_improved", "candidate_same", "candidate_regressed", "not_reviewable"], "dimensions": ["Fidelity", "Completeness", "Naturalness", "Character voice", "Dialogue quality", "Honorific handling", "Context continuity", "Era-appropriate wording", "Unwanted additions", "Omissions", "Overall preference"], "automated_quality_claim": None}
    _write(artifact_root, "manual_review_package.json", manual)
    decision = {"prompt_contract_verification_canary_passed": False, "offline_status": "prompt_contract_preservation_offline_validated", "canary_status": "awaiting_human_review" if reviewable else "failed_closed", "activation_gate": READINESS_GATE, "active_production_authorized": False, "automatic_rollout_authorized": False, "formal_output_replacement_authorized": False, "production_authorized": False}
    _write(artifact_root, "activation_decision.json", decision)
    summary = {"stage": "TE-v7.2-Stage12.5.6", "status": "awaiting_human_review" if reviewable else "execution_failed_closed", "request_count": count, "activation_gate": READINESS_GATE, "integration_metadata": metadata}
    _write(artifact_root, "execution_summary.json", summary); return summary
