from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import subprocess
from time import perf_counter, time
from typing import Protocol

from core.prompt_contract_verification_canary.corpus_identity import build_corpus_identity_contract, resolve_canary_corpus_id
from core.prompt_contract_verification_canary.framework import NvidiaTransport, ProviderOutcome
from core.translation_quality_provider_canary.framework import ALLOWED_MODEL, _build_prompts

STAGE_ID = "TE-v7.2-Stage12.5.8"
PROVIDER = "nvidia"
MODEL = ALLOWED_MODEL
LOGICAL_ID = "canary-001"
CANONICAL_ID = "canary-001-character-honorific"
SOURCE_HASH = "614a4ad6a8025a05ca165e6a7b35e8524ac3e0010649af081c47ab65a1bdf0f3"
FIXTURE_HASH = "53fe975f20561e65061488c82a47bc87838b911a5150df0324760bb11ed6bca5"
READY_GATE = "translation_quality_integration_ready_for_controlled_canary"
PASS_GATE = "translation_quality_prompt_contract_structurally_verified"
ARTIFACT_DIR = "artifacts/te_v72_stage1258_candidate_structural_verification_canary"
AUTHORIZATION_TOKEN = "AUTHORIZE_NTPE_TE_V72_STAGE1258_CANDIDATE_STRUCTURAL_CANARY"
FORBIDDEN_LABELS = (
    "譯文：", "原文：", "翻譯：", "Source:", "Translation:", "Korean:", "Chinese:",
    "【原文】", "【譯文】", "【Korean】", "【Output】",
)
PREPARATION_STEPS = (
    "git_worktree_clean", "origin_main_synchronized", "preparation_commit_present",
    "stage1254a_hashes_valid", "stage1255_readiness_valid", "stage1256_historical_seal_valid",
    "stage1257a_historical_seal_valid", "activation_gate_valid",
    "corpus_logical_id_exact_resolution", "source_fixture_hash_validation",
    "candidate_request_plan_construction", "request_budget_validation", "stage1258_claim_eligibility",
)


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha(value: bytes | str) -> str:
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Stage1258Config:
    authorization_id: str
    authorization_token: str
    preparation_commit: str
    provider: str = PROVIDER
    model: str = MODEL
    timeout_seconds: int = 180
    authorized_request_budget: int = 1
    attempts: int = 1
    retry_allowed: bool = False
    fallback_allowed: bool = False
    cross_provider_fallback: bool = False
    parallelism: int = 1
    automatic_rerun_allowed: bool = False

    def blockers(self) -> list[str]:
        failures: list[str] = []
        if self.authorization_token != AUTHORIZATION_TOKEN: failures.append("authorization_invalid")
        if self.provider != PROVIDER or self.model != MODEL: failures.append("provider_or_model_not_allowlisted")
        if self.timeout_seconds != 180: failures.append("timeout_not_frozen")
        if self.authorized_request_budget != 1 or self.attempts != 1: failures.append("single_request_contract_invalid")
        if self.retry_allowed or self.fallback_allowed or self.cross_provider_fallback: failures.append("retry_or_fallback_forbidden")
        if self.parallelism != 1 or self.automatic_rerun_allowed: failures.append("parallel_or_rerun_forbidden")
        if not re.fullmatch(r"[0-9a-f]{7,40}", self.preparation_commit): failures.append("preparation_commit_invalid")
        return failures


class Transport(Protocol):
    provenance: str
    def invoke(self, *, system_prompt: str, user_prompt: str, config: object) -> ProviderOutcome: ...


def build_candidate_request_plan(root: str | Path) -> dict[str, object]:
    base = Path(root).resolve()
    fixture = base / "tests/fixtures/te_v72_canary/golden_corpus.json"
    contract = build_corpus_identity_contract(fixture)
    resolution = resolve_canary_corpus_id(LOGICAL_ID, (contract,))
    if resolution.canonical_id != CANONICAL_ID: raise ValueError("candidate-corpus-resolution-mismatch")
    if resolution.source_hash != SOURCE_HASH or resolution.fixture_hash != FIXTURE_HASH:
        raise ValueError("candidate-corpus-hash-mismatch")
    payload = json.loads(fixture.read_text(encoding="utf-8"))
    matches = [row for row in payload.get("cases", ()) if row.get("case_id") == CANONICAL_ID]
    if len(matches) != 1: raise ValueError("candidate-corpus-must-resolve-exactly-once")
    source = str(matches[0]["source_text"])
    system_prompt, _baseline, candidate_prompt, metadata = _build_prompts(LOGICAL_ID, source)
    fingerprint_payload = {
        "stage_id": STAGE_ID, "provider": PROVIDER, "model": MODEL, "arm": "candidate",
        "logical_id": LOGICAL_ID, "canonical_id": CANONICAL_ID,
        "source_hash": SOURCE_HASH, "fixture_hash": FIXTURE_HASH,
        "system_prompt_fingerprint": sha(system_prompt), "prompt_fingerprint": sha(candidate_prompt),
        "authorized_request_budget": 1, "attempts": 1, "retry_allowed": False,
        "fallback_allowed": False, "automatic_rerun_allowed": False,
    }
    return {
        **fingerprint_payload,
        "request_plan_fingerprint": sha(canonical(fingerprint_payload)),
        "source": source, "system_prompt": system_prompt, "candidate_prompt": candidate_prompt, "metadata": metadata,
    }


def public_request_plan(plan: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in plan.items() if key not in {"source", "system_prompt", "candidate_prompt", "metadata"}}


def _git(base: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=base, capture_output=True, text=True, check=False)


def _manifest_valid(base: Path, relative: str) -> bool:
    path = base / relative
    if not path.is_file(): return False
    payload = json.loads(path.read_text(encoding="utf-8"))
    return all(
        (base / item).is_file() and sha((base / item).read_bytes()) == digest
        for group in ("artifact_hashes", "source_hashes", "test_hashes")
        for item, digest in payload.get(group, {}).items()
    )


def _json(base: Path, relative: str) -> dict[str, object]:
    path = base / relative
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def build_preflight(
    root: str | Path,
    config: Stage1258Config,
    *,
    claim_path: str | Path | None = None,
    check_overrides: dict[str, bool] | None = None,
) -> tuple[dict[str, object], dict[str, object] | None]:
    base = Path(root).resolve()
    claim = Path(claim_path) if claim_path is not None else base / ARTIFACT_DIR / "authorization_claim.json"
    overrides = check_overrides or {}
    checks: list[dict[str, object]] = []

    def add(name: str, passed: bool, **evidence: object) -> None:
        checks.append({"ordinal": len(checks) + 1, "name": name, "passed": overrides.get(name, passed), **evidence})

    clean = _git(base, "status", "--porcelain")
    add(PREPARATION_STEPS[0], clean.returncode == 0 and not clean.stdout.strip())
    sync = _git(base, "rev-list", "--left-right", "--count", "origin/main...main")
    add(PREPARATION_STEPS[1], sync.returncode == 0 and sync.stdout.split() == ["0", "0"])
    anchor = _git(base, "merge-base", "--is-ancestor", config.preparation_commit, "HEAD")
    add(PREPARATION_STEPS[2], anchor.returncode == 0, preparation_commit=config.preparation_commit)
    add(PREPARATION_STEPS[3], _manifest_valid(base, "manifests/te_v720_stage1254_prompt_contract_preservation_manifest.json"))
    readiness = _json(base, "artifacts/te_v72_prompt_canary_readiness/readiness_summary.json")
    add(PREPARATION_STEPS[4], readiness.get("status") == "PASS" and readiness.get("prompt_canary_ready") is True)
    seal56 = _json(base, "artifacts/te_v72_stage1256a_claim_safe_corpus_binding_remediation/historical_stage1256_seal.json")
    add(PREPARATION_STEPS[5], seal56.get("status") == "PASS" and seal56.get("historical_claim_preserved") is True)
    seal57 = _json(base, "artifacts/te_v72_stage1257a_execution_evidence_sealing/historical_execution_seal.json")
    add(PREPARATION_STEPS[6], seal57.get("status") == "PASS" and seal57.get("execution_status") == "completed_fail_closed")
    add(PREPARATION_STEPS[7], readiness.get("activation_gate") == READY_GATE and seal57.get("activation_gate") == READY_GATE)
    plan: dict[str, object] | None = None
    try:
        plan = build_candidate_request_plan(base)
        add(PREPARATION_STEPS[8], plan["canonical_id"] == CANONICAL_ID, logical_id=LOGICAL_ID, canonical_id=CANONICAL_ID)
        add(PREPARATION_STEPS[9], plan["source_hash"] == SOURCE_HASH and plan["fixture_hash"] == FIXTURE_HASH)
        add(PREPARATION_STEPS[10], bool(plan["request_plan_fingerprint"] and plan["prompt_fingerprint"]))
    except Exception as exc:
        add(PREPARATION_STEPS[8], False, error=type(exc).__name__)
        add(PREPARATION_STEPS[9], False)
        add(PREPARATION_STEPS[10], False)
    add(PREPARATION_STEPS[11], not config.blockers(), blockers=config.blockers())
    add(PREPARATION_STEPS[12], not claim.exists())
    passed = all(bool(row["passed"]) for row in checks)
    result = {
        "stage": STAGE_ID, "status": "PASS" if passed else "FAIL", "ordered_steps": checks,
        "claim_created": False, "provider_requests": 0, "network_requests": 0, "fail_closed": not passed,
    }
    return result, plan if passed else None


def _normalized(value: str) -> str:
    return re.sub(r"\s+", "", value).casefold()


def validate_candidate_output(source: str, output: str, *, success: bool, timeout: bool, error: str | None = None) -> dict[str, object]:
    stripped = output.strip()
    source_norm, output_norm = _normalized(source), _normalized(stripped)
    hangul_count = len(re.findall(r"[\uac00-\ud7a3\u1100-\u11ff]", stripped))
    exact_echo = bool(source_norm and source_norm in output_norm)
    source_sequences = [source_norm[index:index + 12] for index in range(max(len(source_norm) - 11, 0))]
    partial_echo = any(sequence in output_norm for sequence in source_sequences) or (
        len(output_norm) >= 6 and output_norm in source_norm and output_norm != source_norm
    )
    labels = [label for label in FORBIDDEN_LABELS if label.casefold() in stripped.casefold()]
    markdown = chr(96) * 3 in stripped or bool(re.search(r"(?m)^\s{0,3}#{1,6}\s", stripped))
    json_wrapper = stripped.startswith(("{", "[")) and stripped.endswith(("}", "]"))
    xml_wrapper = bool(re.search(r"<([A-Za-z][\w:-]*)\b[^>]*>.*</\1>", stripped, re.DOTALL))
    explanation = bool(re.search(r"(?:說明|解釋|摘要|譯者注|translator\s*note|summary)\s*[:：]", stripped, re.I))
    bilingual = bool(labels) or (hangul_count > 0 and bool(re.search(r"[\u4e00-\u9fff]", stripped)))
    non_empty = bool(stripped)
    minimum_length = len(stripped) >= 8
    terminal_truncation = stripped.endswith(("…", "...", "、", ",", "，", "（", "(", "：", ":"))
    blocks = [item.strip() for item in re.split(r"\n\s*\n|\n", stripped) if item.strip()]
    repeated_block = len(blocks) > 1 and len({_normalized(item) for item in blocks}) < len(blocks)
    malformed_fragment = bool(stripped and (stripped.count("「") != stripped.count("」") or stripped.count("『") != stripped.count("』")))
    simplified_markers = len(re.findall(r"[这为与发后里么们会时说对还从个来没过让应见实当开关进气学书车门间长东国体万无听头台]", stripped))
    traditional_target = simplified_markers <= 1 and bool(re.search(r"[\u4e00-\u9fff]", stripped))
    failures: list[str] = []
    if timeout: failures.append("provider_timeout")
    elif not success: failures.append("provider_error")
    if not non_empty: failures.append("empty_output")
    if exact_echo: failures.extend(("exact_source_echo", "complete_source_duplication"))
    if partial_echo: failures.append("partial_source_echo")
    if hangul_count: failures.append("hangul_residual")
    if labels: failures.append("forbidden_label")
    if markdown: failures.append("markdown_wrapper")
    if json_wrapper: failures.append("json_wrapper")
    if xml_wrapper: failures.append("xml_wrapper")
    if explanation: failures.append("explanation_or_summary")
    if bilingual: failures.append("bilingual_layout")
    if not minimum_length and non_empty: failures.append("abnormal_short_output")
    if terminal_truncation: failures.append("terminal_truncation")
    if repeated_block: failures.append("repeated_output_block")
    if malformed_fragment: failures.append("malformed_fragment")
    if non_empty and not traditional_target: failures.append("traditional_chinese_target_signal")
    structural_failures = [item for item in failures if not item.startswith("provider_")]
    if timeout: canary_status = "inconclusive_provider_timeout"
    elif not success: canary_status = "inconclusive_provider_error"
    elif structural_failures: canary_status = "candidate_structural_failed"
    else: canary_status = "candidate_structural_verified"
    passed = canary_status == "candidate_structural_verified"
    return {
        "provider_success": success, "timeout": timeout, "error_category": error,
        "raw_response_present": bool(output), "exact_source_echo": exact_echo,
        "normalized_source_echo": exact_echo, "partial_source_sequence": partial_echo,
        "hangul_character_count": hangul_count, "hangul_ratio": round(hangul_count / max(len(stripped), 1), 6),
        "forbidden_labels": labels, "markdown_wrapper": markdown, "json_wrapper": json_wrapper,
        "xml_wrapper": xml_wrapper, "explanation_or_summary": explanation, "bilingual_layout": bilingual,
        "non_empty": non_empty, "minimum_output_length_passed": minimum_length,
        "source_output_length_ratio": round(len(stripped) / max(len(source), 1), 6),
        "obvious_terminal_truncation": terminal_truncation, "complete_source_duplication": exact_echo,
        "repeated_output_block": repeated_block, "malformed_fragment": malformed_fragment,
        "traditional_chinese_target_signal": traditional_target, "simplified_marker_count": simplified_markers,
        "failures": failures, "candidate_structural_pass": passed,
        "prompt_contract_structural_verification_passed": passed, "canary_status": canary_status,
    }


def build_claim(config: Stage1258Config, plan: dict[str, object], *, created_at: float | None = None) -> dict[str, object]:
    scope = {
        "stage_id": STAGE_ID, "provider": PROVIDER, "model": MODEL,
        "logical_corpus_id": LOGICAL_ID, "canonical_corpus_id": CANONICAL_ID,
        "authorized_request_budget": 1, "attempts": 1, "retry_allowed": False,
        "fallback_allowed": False, "automatic_rerun_allowed": False,
        "request_plan_fingerprint": plan["request_plan_fingerprint"], "prompt_fingerprint": plan["prompt_fingerprint"],
    }
    return {
        **scope, "single_use": True, "replay_allowed": False,
        "creation_timestamp_epoch_seconds": time() if created_at is None else created_at,
        "authorization_scope_hash": sha(canonical(scope)), "authorization_id": config.authorization_id,
    }


def create_single_use_claim(path: str | Path, claim: dict[str, object]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with target.open("xb") as stream: stream.write(canonical(claim))
    except FileExistsError as exc:
        raise ValueError("stage1258-claim-replay-rejected") from exc


def execute_stage1258(config: Stage1258Config, *, root: str | Path, transport: Transport | None = None) -> dict[str, object]:
    base = Path(root).resolve()
    artifact_root = base / ARTIFACT_DIR
    artifact_root.mkdir(parents=True, exist_ok=True)
    claim_path = artifact_root / "authorization_claim.json"
    preflight, plan = build_preflight(base, config, claim_path=claim_path)
    (artifact_root / "preflight.json").write_bytes(canonical(preflight))
    if plan is None:
        summary = {"stage": STAGE_ID, "canary_status": "blocked_before_provider", "claim_created": False,
                   "provider_requests": 0, "activation_gate": READY_GATE}
        (artifact_root / "execution_summary.json").write_bytes(canonical(summary))
        return summary
    claim = build_claim(config, plan)
    create_single_use_claim(claim_path, claim)
    request_count = 0
    started = perf_counter()
    try:
        active = transport or NvidiaTransport()
        if active.provenance != "real": raise ValueError("real-transport-required")
        request_count = 1
        outcome = active.invoke(system_prompt=str(plan["system_prompt"]), user_prompt=str(plan["candidate_prompt"]), config=config)
        validation = validate_candidate_output(str(plan["source"]), outcome.raw_response, success=outcome.success,
                                               timeout=outcome.timeout, error=outcome.error)
        response = {"stage": STAGE_ID, "arm": "candidate", "elapsed_seconds": outcome.elapsed_seconds,
                    "raw_response": outcome.raw_response, **validation}
    except Exception as exc:
        response = {"stage": STAGE_ID, "arm": "candidate", "elapsed_seconds": round(perf_counter() - started, 6),
                    "raw_response": "", **validate_candidate_output(str(plan["source"]), "", success=False,
                    timeout=False, error=type(exc).__name__)}
    request_artifact = {"stage": STAGE_ID, "arm": "candidate", **public_request_plan(plan),
                        "request_ordinal": 1, "attempts": 1, "retry": 0, "fallback": False}
    (artifact_root / "candidate_request.json").write_bytes(canonical(request_artifact))
    (artifact_root / "candidate_response.json").write_bytes(canonical(response))
    (artifact_root / "structural_validation.json").write_bytes(canonical(response))
    gate = PASS_GATE if response["candidate_structural_pass"] else READY_GATE
    decision = {
        "stage": STAGE_ID, "canary_status": response["canary_status"],
        "prompt_contract_structural_verification_passed": response["prompt_contract_structural_verification_passed"],
        "activation_gate": gate, "candidate_improved": None, "translation_quality_passed": None,
        "active_production_authorized": False, "automatic_rollout_authorized": False,
        "formal_output_replacement_authorized": False, "production_authorized": False,
    }
    (artifact_root / "final_activation_decision.json").write_bytes(canonical(decision))
    summary = {**decision, "provider_requests": request_count, "claim_created": True,
               "automatic_rerun": False, "retry": 0, "fallback": False}
    (artifact_root / "execution_summary.json").write_bytes(canonical(summary))
    return summary
