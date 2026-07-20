from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import subprocess
from time import time
from typing import Protocol

from core.prompt_contract_verification_canary.corpus_identity import build_corpus_identity_contract, resolve_canary_corpus_id
from core.prompt_contract_verification_canary.framework import NvidiaTransport, ProviderOutcome, validate_output
from core.translation_quality_provider_canary.framework import ALLOWED_MODEL, _build_prompts

AUTHORIZATION_TOKEN = "AUTHORIZE_NTPE_TE_V72_STAGE1257_PROMPT_VERIFICATION_CANARY"
GATE_READY = "translation_quality_integration_ready_for_controlled_canary"
ARTIFACT_DIR = "artifacts/te_v72_stage1257_prompt_verification_canary"
LOGICAL_ID = "canary-001"
CANONICAL_ID = "canary-001-character-honorific"
SOURCE_HASH = "614a4ad6a8025a05ca165e6a7b35e8524ac3e0010649af081c47ab65a1bdf0f3"
FIXTURE_HASH = "53fe975f20561e65061488c82a47bc87838b911a5150df0324760bb11ed6bca5"
HISTORICAL_CLAIM_HASH = "82a0747c084e3844047e8d6e701bc4c4309ba20b56519119b2f7c0988c56f5eb"

def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def _sha(value: bytes) -> str: return hashlib.sha256(value).hexdigest()
def _write(root: Path, name: str, value: object) -> None: (root / name).write_bytes(_canonical(value))

@dataclass(frozen=True)
class Stage1257Config:
    authorization_id: str
    authorization_token: str
    provider: str = "nvidia"
    model: str = ALLOWED_MODEL
    timeout_seconds: int = 180
    authorized_request_budget: int = 2
    attempts_per_arm: int = 1
    retry: int = 0
    fallback: bool = False
    cross_provider_fallback: bool = False
    parallelism: int = 1
    automatic_rerun: bool = False

    def valid(self) -> bool:
        return (self.authorization_token == AUTHORIZATION_TOKEN and self.provider == "nvidia" and
                self.model == ALLOWED_MODEL and self.timeout_seconds == 180 and
                self.authorized_request_budget == 2 and self.attempts_per_arm == 1 and self.retry == 0 and
                not self.fallback and not self.cross_provider_fallback and self.parallelism == 1 and not self.automatic_rerun)

class Transport(Protocol):
    provenance: str
    def invoke(self, *, system_prompt: str, user_prompt: str, config: object) -> ProviderOutcome: ...

def _worktree_clean(root: Path) -> bool:
    result = subprocess.run(["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True, check=False)
    return result.returncode == 0 and not result.stdout.strip()

def _hash_map_valid(root: Path, mapping: dict[str, str]) -> bool:
    return all((root / path).is_file() and _sha((root / path).read_bytes()) == digest for path, digest in mapping.items())

def _manifest_valid(root: Path, path: Path) -> bool:
    if not path.is_file(): return False
    data = json.loads(path.read_text(encoding="utf-8"))
    return all(_hash_map_valid(root, data.get(group, {})) for group in ("artifact_hashes", "source_hashes", "test_hashes"))

def build_preflight(root: str | Path, config: Stage1257Config, *, clean_override: bool | None = None,
                    claim_path: str | Path | None = None, artifact_validation_override: bool | None = None) -> tuple[dict[str, object], dict[str, object] | None]:
    base = Path(root).resolve(); artifact_root = base / ARTIFACT_DIR
    claim = Path(claim_path) if claim_path is not None else artifact_root / "authorization_claim.json"
    readiness = json.loads((base / "artifacts/te_v72_prompt_canary_readiness/readiness_summary.json").read_text(encoding="utf-8"))
    stage1254 = json.loads((base / "manifests/te_v720_stage1254_prompt_contract_preservation_manifest.json").read_text(encoding="utf-8"))
    old_claim = base / "artifacts/te_v72_stage1256_prompt_verification_canary/authorization_claim.json"
    seal = base / "artifacts/te_v72_stage1256a_claim_safe_corpus_binding_remediation/historical_stage1256_seal.json"
    manifest_a = base / "manifests/te_v720_stage1256a_claim_safe_corpus_binding_remediation_manifest.json"
    steps: list[dict[str, object]] = []
    def add(name: str, passed: bool, **extra: object) -> None: steps.append({"ordinal": len(steps)+1, "name": name, "passed": passed, **extra})
    add("git_worktree_validation", _worktree_clean(base) if clean_override is None else clean_override)
    add("artifact_hash_validation", (_hash_map_valid(base, stage1254.get("artifact_hashes", {})) and _manifest_valid(base, manifest_a)) if artifact_validation_override is None else artifact_validation_override)
    add("readiness_gate_validation", readiness.get("prompt_canary_ready") is True and readiness.get("activation_gate") == GATE_READY)
    old_hash = _sha(old_claim.read_bytes()) if old_claim.is_file() else None
    seal_data = json.loads(seal.read_text(encoding="utf-8")) if seal.is_file() else {}
    add("historical_stage1256_seal_validation", old_hash == HISTORICAL_CLAIM_HASH and seal_data.get("historical_claim_sha256") == old_hash)
    add("authorization_budget_validation", config.valid())
    plan = None
    try:
        fixture = base / "tests/fixtures/te_v72_canary/golden_corpus.json"
        contract = build_corpus_identity_contract(fixture); resolution = resolve_canary_corpus_id(LOGICAL_ID, (contract,))
        add("corpus_identity_resolution", resolution.canonical_id == CANONICAL_ID, logical_id=LOGICAL_ID, canonical_id=resolution.canonical_id)
        hash_ok = contract.source_hash == SOURCE_HASH and contract.fixture_hash == FIXTURE_HASH
        add("source_fixture_hash_validation", hash_ok, source_hash=contract.source_hash, fixture_hash=contract.fixture_hash)
        corpus = json.loads(fixture.read_text(encoding="utf-8")); exact = [row for row in corpus["cases"] if row.get("case_id") == resolution.canonical_id]
        if len(exact) == 1 and hash_ok:
            prompts = _build_prompts(LOGICAL_ID, str(exact[0]["source_text"]))
            plan = {"logical_id": LOGICAL_ID, "canonical_id": CANONICAL_ID, "source": exact[0]["source_text"],
                    "system_prompt": prompts[0], "baseline_prompt": prompts[1], "candidate_prompt": prompts[2], "metadata": prompts[3]}
        add("request_plan_validation", plan is not None)
    except Exception as exc:
        add("corpus_identity_resolution", False, error=type(exc).__name__)
        add("source_fixture_hash_validation", False); add("request_plan_validation", False)
    add("stage1257_claim_eligibility_validation", not claim.exists())
    passed = all(bool(row["passed"]) for row in steps)
    return {"stage": "TE-v7.2-Stage12.5.7", "status": "PASS" if passed else "FAIL", "ordered_steps": steps,
            "claim_created": False, "provider_requests": 0, "fail_closed": not passed}, plan if passed else None

def _claim(path: Path, config: Stage1257Config) -> None:
    payload = {"stage": "TE-v7.2-Stage12.5.7", "authorization_id": config.authorization_id, "single_use": True,
               "created_at_epoch_seconds": time(), "authorized_request_budget": 2, "consumed_request_count": 0}
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream: stream.write(_canonical(payload))
    except FileExistsError as exc: raise ValueError("stage1257-claim-replay-rejected") from exc

def execute_stage1257(config: Stage1257Config, *, root: str | Path, transport: Transport | None = None) -> dict[str, object]:
    base = Path(root).resolve(); out = base / ARTIFACT_DIR; out.mkdir(parents=True, exist_ok=True)
    preflight, plan = build_preflight(base, config); _write(out, "preflight.json", preflight)
    if plan is None:
        summary = {"status": "preflight_failed", "request_count": 0, "claim_created": False, "activation_gate": GATE_READY}
        _write(out, "execution_summary.json", summary); return summary
    _write(out, "corpus_resolution.json", {"logical_id": LOGICAL_ID, "canonical_id": CANONICAL_ID,
           "source_hash": SOURCE_HASH, "fixture_hash": FIXTURE_HASH, "status": "PASS"})
    _write(out, "request_plan.json", {"order": ["baseline", "candidate"], "request_budget": 2,
           "attempts_per_arm": 1, "retry": 0, "fallback": False,
           "prompt_fingerprints": {"baseline": _sha(str(plan["baseline_prompt"]).encode()), "candidate": _sha(str(plan["candidate_prompt"]).encode())}})
    active = transport or NvidiaTransport()
    if active.provenance != "real": raise ValueError("real-transport-required")
    claim_path = out / "authorization_claim.json"; _claim(claim_path, config)
    arms: dict[str, dict[str, object]] = {}; requests = 0
    try:
        for arm in ("baseline", "candidate"):
            prompt = str(plan[f"{arm}_prompt"]); started = time(); requests += 1
            result = active.invoke(system_prompt=str(plan["system_prompt"]), user_prompt=prompt, config=config); ended = time()
            validation = validate_output(str(plan["source"]), result.raw_response, success=result.success, timeout=result.timeout, malformed=result.malformed)
            request = {"arm": arm, "logical_corpus_id": LOGICAL_ID, "canonical_corpus_id": CANONICAL_ID,
                       "exact_source": plan["source"], "source_hash": SOURCE_HASH, "exact_serialized_prompt": prompt,
                       "prompt_fingerprint": _sha(prompt.encode()), "model": config.model, "request_ordinal": requests,
                       "start_timestamp_epoch_seconds": started, "end_timestamp_epoch_seconds": ended,
                       "request_metadata": {"attempts": 1, "retry": 0, "fallback": False, "parallelism": 1}}
            response = {"arm": arm, "provider_status": result.http_status if result.success else result.error,
                        "success": result.success, "timeout": result.timeout, "error": result.error,
                        "elapsed_seconds": result.elapsed_seconds, "raw_response": result.raw_response, **validation}
            _write(out, f"{arm}_request.json", request); _write(out, f"{arm}_response.json", response); arms[arm] = response
            if not result.success or result.timeout: break
    except Exception as exc:
        arms["uncaught_exception"] = {"type": type(exc).__name__, "status": "FAIL"}
    baseline = arms.get("baseline", {}); candidate = arms.get("candidate", {})
    structural = {"baseline": baseline, "candidate": candidate, "candidate_structural_pass": candidate.get("status") == "PASS",
                  "request_count": requests, "fail_closed": candidate.get("status") != "PASS"}
    _write(out, "structural_validation.json", structural)
    b=float(baseline.get("elapsed_seconds",0)); c=float(candidate.get("elapsed_seconds",0))
    _write(out, "latency_comparison.json", {"baseline_elapsed_seconds": b, "candidate_elapsed_seconds": c,
           "absolute_delta_seconds": round(c-b,6), "relative_ratio": round(c/b,6) if b else None})
    reviewable = bool(baseline.get("status") == "PASS" and candidate.get("status") == "PASS")
    _write(out, "manual_review_package.json", {"manual_review_status": "pending_chatgpt_review" if reviewable else "not_reviewable",
           "allowed_decisions": ["candidate_improved","candidate_same","candidate_regressed","not_reviewable"],
           "dimensions": ["Fidelity","Completeness","Naturalness","Character voice","Dialogue quality","Honorific handling","Context continuity","Era-appropriate wording","Additions","Omissions","Overall preference"],
           "automated_quality_claim": None})
    _write(out, "provisional_activation_decision.json", {"activation_decision": "provisional", "manual_review_status": "pending_chatgpt_review" if reviewable else "not_reviewable",
           "prompt_contract_verification_canary_passed": False, "activation_gate": GATE_READY,
           "active_production_authorized": False, "automatic_rollout_authorized": False,
           "formal_output_replacement_authorized": False, "production_authorized": False})
    summary = {"status": "pending_chatgpt_review" if reviewable else "execution_failed_closed", "request_count": requests,
               "baseline_success": baseline.get("success",False), "candidate_success": candidate.get("success",False), "activation_gate": GATE_READY}
    _write(out, "execution_summary.json", summary); return summary
