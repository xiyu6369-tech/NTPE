from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import time
from types import MappingProxyType
from typing import Callable, Mapping

import core.post_polish_semantic_verification as semantic
from core.translation_engine.nvidia_client import NvidiaClient

from .review_candidate_artifact import build_review_artifact, write_review_artifact
from .single_chunk_execution_authorization import (
    SingleChunkExecutionAuthorization,
    validate_execution_authorization,
)


PACKAGE_RELATIVE_PATH = Path("artifacts/lcr_batch107/LCR_BATCH107_REAL_PROVIDER_EXECUTION_PACKAGE.json")
REVIEW_RELATIVE_DIRECTORY = Path("artifacts/lcr_batch107_review")
SOURCE_RELATIVE_PATH = Path("artifacts/tic_batch2/TRANSLATION_CASES.json")
PROVIDER = "nvidia"
MODEL = "meta/llama-3.3-70b-instruct"
PROVIDER_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
CREDENTIAL_ENV = "NVIDIA_API_KEY"
HANGUL = re.compile(r"[\uac00-\ud7a3]")
REFUSAL_MARKERS = ("i cannot", "i can't", "cannot assist", "unable to comply", "抱歉，我無法")


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _scope_payload(value: Mapping[str, object]) -> dict[str, object]:
    return {
        "document_id": value["document_id"],
        "chunk_id": value["chunk_id"],
        "source_hash": value["source_hash"],
        "production_translation_hash": value["production_translation_hash"],
        "rollback_baseline_hash": value["rollback_baseline_hash"],
        "provider": value["provider"],
        "model": value["model"],
        "source_profile": value["source_profile"],
        "target_profile": value["target_profile"],
        "max_provider_requests": value["max_provider_requests"],
        "max_network_requests": value["max_network_requests"],
        "retry_limit": value["retry_limit"],
        "fallback_allowed": value["fallback_allowed"],
        "parallelism": value["parallelism"],
    }


def authorization_scope_fingerprint(value: Mapping[str, object]) -> str:
    return sha256_text(canonical_json(_scope_payload(value)))


def package_integrity_fingerprint(value: Mapping[str, object]) -> str:
    payload = dict(value)
    payload.pop("package_integrity", None)
    return sha256_text(canonical_json(payload))


@dataclass(frozen=True)
class Batch107Target:
    document_id: str
    chunk_id: str
    chunk_index: int
    source_text: str
    source_hash: str
    production_translation: str
    production_translation_hash: str
    rollback_baseline_hash: str
    source_profile: str
    target_profile: str
    bounded_context: Mapping[str, object]
    glossary_subset: Mapping[str, str]


@dataclass(frozen=True)
class Batch107ExecutionResult:
    status: str
    outcome: str
    reason_codes: tuple[str, ...] = ()
    provider_requests: int = 0
    network_requests: int = 0
    draft_request_status: str = "not_run"
    polish_request_status: str = "not_run"
    retry_count: int = 0
    fallback_used: bool = False
    elapsed_milliseconds: float = 0.0
    response_status_classification: str = "not_run"
    semantic_verification_outcome: str = "not_run"
    review_artifact_path: str | None = None
    review_artifact_hash: str | None = None
    formal_output_changed: bool = False
    resume_changed: bool = False
    cache_changed: bool = False
    stores_changed: bool = False

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _safe_resolve(root: Path, relative: Path, expected: Path) -> Path:
    candidate = (root / relative).resolve()
    wanted = (root / expected).resolve()
    if candidate != wanted:
        raise ValueError("unsafe_or_unexpected_path")
    return candidate


def load_execution_package(path: str | Path, *, root: str | Path) -> Mapping[str, object]:
    base = Path(root).resolve()
    supplied = Path(path)
    if supplied.is_absolute():
        candidate = supplied.resolve()
        if candidate != (base / PACKAGE_RELATIVE_PATH).resolve():
            raise ValueError("execution_package_path_not_allowlisted")
    else:
        candidate = _safe_resolve(base, supplied, PACKAGE_RELATIVE_PATH)
    value = json.loads(candidate.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("execution_package_not_object")
    blockers = validate_execution_package(value)
    if blockers:
        raise ValueError(",".join(blockers))
    return MappingProxyType(value)


def validate_execution_package(value: Mapping[str, object]) -> tuple[str, ...]:
    blockers: list[str] = []
    required = {
        "execution_id", "authorization_fingerprint", "document_id", "chunk_id", "chunk_index",
        "source_hash", "production_translation_hash", "rollback_baseline_hash", "provider", "model",
        "source_profile", "target_profile", "draft_request_allowed", "polish_request_allowed",
        "semantic_verification_required", "max_provider_requests", "max_network_requests", "retry_limit",
        "fallback_allowed", "parallelism", "formal_output_replacement_allowed", "resume_write_allowed",
        "cache_write_allowed", "store_write_allowed", "automatic_rollout_allowed", "execution_status",
        "real_provider_execution_authorized", "provider_requests", "network_requests", "source_reference",
        "review_artifact_directory", "package_integrity",
    }
    if required - set(value):
        blockers.append("execution_package_required_fields_missing")
        return tuple(blockers)
    if value.get("provider") != PROVIDER or value.get("model") != MODEL:
        blockers.append("provider_or_model_not_allowlisted")
    if value.get("max_provider_requests") != 2 or value.get("max_network_requests") != 2:
        blockers.append("request_budget_not_exact")
    if value.get("retry_limit") != 0 or value.get("fallback_allowed") is not False or value.get("parallelism") != 1:
        blockers.append("execution_policy_not_bounded")
    if value.get("draft_request_allowed") is not True or value.get("semantic_verification_required") is not True:
        blockers.append("required_step_disabled")
    forbidden = (
        "formal_output_replacement_allowed", "resume_write_allowed", "cache_write_allowed",
        "store_write_allowed", "automatic_rollout_allowed", "real_provider_execution_authorized",
    )
    if any(value.get(field) is not False for field in forbidden):
        blockers.append("forbidden_capability_enabled")
    if value.get("execution_status") != "awaiting_user_authorization":
        blockers.append("execution_status_not_prepared_only")
    if value.get("provider_requests") != 0 or value.get("network_requests") != 0:
        blockers.append("prepared_package_request_count_not_zero")
    if value.get("review_artifact_directory") != REVIEW_RELATIVE_DIRECTORY.as_posix():
        blockers.append("review_artifact_directory_not_allowlisted")
    reference = value.get("source_reference")
    if not isinstance(reference, Mapping) or reference.get("path") != SOURCE_RELATIVE_PATH.as_posix():
        blockers.append("source_reference_not_allowlisted")
    if value.get("authorization_fingerprint") != authorization_scope_fingerprint(value):
        blockers.append("authorization_scope_fingerprint_mismatch")
    integrity = value.get("package_integrity")
    if not isinstance(integrity, Mapping) or integrity.get("algorithm") != "sha256" or integrity.get("payload_sha256") != package_integrity_fingerprint(value):
        blockers.append("execution_package_integrity_mismatch")
    return tuple(dict.fromkeys(blockers))


def _load_target(package: Mapping[str, object], *, root: Path) -> Batch107Target:
    reference = package["source_reference"]
    assert isinstance(reference, Mapping)
    source_path = _safe_resolve(root, Path(str(reference["path"])), SOURCE_RELATIVE_PATH)
    document = json.loads(source_path.read_text(encoding="utf-8"))
    cases = document.get("translation_cases", [])
    matches = [item for item in cases if isinstance(item, dict) and item.get("case_id") == package["document_id"]]
    if len(matches) != 1:
        raise ValueError("document_identity_not_unique")
    item = matches[0]
    source = item.get("source_text")
    production = item.get("translation_text")
    if not isinstance(source, str) or not isinstance(production, str) or not source or not production:
        raise ValueError("source_or_production_translation_unavailable")
    checks = (
        (item.get("chunk_id"), package["chunk_id"], "chunk_id_mismatch"),
        (item.get("chunk_index"), package["chunk_index"], "chunk_index_mismatch"),
        (sha256_text(source), package["source_hash"], "source_hash_mismatch"),
        (sha256_text(production), package["production_translation_hash"], "production_translation_hash_mismatch"),
        (package["production_translation_hash"], package["rollback_baseline_hash"], "rollback_baseline_hash_mismatch"),
    )
    for actual, expected, reason in checks:
        if actual != expected:
            raise ValueError(reason)
    return Batch107Target(
        document_id=str(package["document_id"]), chunk_id=str(package["chunk_id"]),
        chunk_index=int(package["chunk_index"]), source_text=source, source_hash=str(package["source_hash"]),
        production_translation=production, production_translation_hash=str(package["production_translation_hash"]),
        rollback_baseline_hash=str(package["rollback_baseline_hash"]), source_profile=str(package["source_profile"]),
        target_profile=str(package["target_profile"]), bounded_context=MappingProxyType({"scope": "single_chunk_only"}),
        glossary_subset=MappingProxyType({}),
    )


def load_authorization(path: str | Path) -> SingleChunkExecutionAuthorization:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("authorization_not_object")
    return SingleChunkExecutionAuthorization(**value)


def validate_package_authorization(
    package: Mapping[str, object], authorization: SingleChunkExecutionAuthorization | None, *, now: str,
) -> tuple[bool, tuple[str, ...]]:
    valid, reasons = validate_execution_authorization(
        authorization, now=now, document_id=str(package["document_id"]), chunk_id=str(package["chunk_id"]),
        source_hash=str(package["source_hash"]), production_translation_hash=str(package["production_translation_hash"]),
        rollback_baseline_hash=str(package["rollback_baseline_hash"]), provider=str(package["provider"]),
        model=str(package["model"]), source_profile=str(package["source_profile"]), target_profile=str(package["target_profile"]),
    )
    if authorization is not None:
        auth_scope = {
            **asdict(authorization),
            "fallback_allowed": authorization.allow_cross_provider_fallback,
            "parallelism": 1,
        }
        if authorization_scope_fingerprint(auth_scope) != package["authorization_fingerprint"]:
            reasons = (*reasons, "authorization_scope_mismatch")
            valid = False
    return valid, tuple(dict.fromkeys(reasons))


class NvidiaBatch107Provider:
    provenance = "real"

    def __init__(self, *, api_key: str, model: str, timeout_seconds: int) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout_seconds = timeout_seconds
        self.network_requests = 0

    def __call__(self, request: Mapping[str, object]) -> str:
        kind = request.get("request_kind")
        source = request.get("source_text")
        if kind not in {"draft", "polish"} or not isinstance(source, str):
            raise ValueError("malformed_bounded_request")
        system = (
            "You are translating one bounded Korean fiction chunk into Traditional Chinese. "
            "Preserve meaning, names, viewpoint, paragraph intent, period tone, and narrative style. "
            "Return translation text only. Do not discuss the task."
        )
        if kind == "draft":
            user = f"Translate this single chunk into Traditional Chinese:\n\n{source}"
        else:
            candidate = request.get("candidate_text")
            if not isinstance(candidate, str):
                raise ValueError("malformed_polish_request")
            user = (
                "Polish the candidate for natural Traditional Chinese fiction while preserving every source fact.\n\n"
                f"SOURCE:\n{source}\n\nCANDIDATE:\n{candidate}"
            )
        client = NvidiaClient(api_key=self._api_key, api_url=PROVIDER_URL, timeout=self._timeout_seconds)
        # The shared client supports global runtime overrides; this isolated run must
        # honor the exact authorization instead of inheriting broader process policy.
        client.timeout = self._timeout_seconds
        client.connect_timeout = min(10, self._timeout_seconds)
        self.network_requests += 1
        return client.chat(
            model=self._model, system_prompt=system, user_prompt=user,
            temperature=0.12, top_p=0.82, max_tokens=800,
        )


def _validate_provider_text(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("empty_or_malformed_provider_response")
    text = value.strip()
    lower = text.lower()
    if any(marker in lower for marker in REFUSAL_MARKERS):
        raise ValueError("provider_policy_refusal")
    if len(HANGUL.findall(text)) > max(0, len(text) // 100):
        raise ValueError("hangul_residue_threshold_violation")
    if len(text) < 20 or text.endswith(("…", "...", "—", "-")):
        raise ValueError("obvious_truncation")
    return text


def _semantic_verify(
    target: Batch107Target, draft: str, polish: str, *, now: str,
    verifier: Callable[..., object] = semantic.verify_post_polish_semantics,
) -> object:
    # The production translation is deliberately present in the target identity and rollback baseline;
    # Batch 6's public input schema compares the verified draft with the optional polish candidate.
    if not target.production_translation:
        raise ValueError("production_translation_missing")
    item = semantic.create_verification_input(
        verification_id=f"batch107-{target.document_id}-{target.chunk_id}", document_id=target.document_id,
        chunk_index=target.chunk_index, source_language=target.source_profile, target_language=target.target_profile,
        source_text=target.source_text, verified_draft_text=draft, polish_text=polish,
        polish_scope={"scope_type": "single_chunk", "production_translation_hash": target.production_translation_hash},
        character_memory_fingerprint=sha256_text("no-store-bounded-character-view"),
        context_scene_fingerprint=sha256_text(canonical_json(dict(target.bounded_context))),
        glossary_fingerprint=sha256_text(canonical_json(dict(target.glossary_subset))),
        semantic_policy_id=semantic.POLICY_ID, semantic_policy_version=semantic.POLICY_VERSION, created_at=now,
    )
    return verifier(item)


def _status_value(result: object) -> str:
    status = getattr(result, "status", "")
    return str(getattr(status, "value", status))


def _claim_execution(directory: Path, execution_id: str, authorization_fingerprint: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    claim = (directory / f"execution-claim-{sha256_text(execution_id)[:24]}.json").resolve()
    if claim.parent != directory.resolve():
        raise ValueError("unsafe_execution_claim_path")
    payload = canonical_json({
        "execution_id": execution_id,
        "authorization_fingerprint": authorization_fingerprint,
        "status": "claimed_for_at_most_one_real_execution",
    }) + "\n"
    with claim.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    return claim


def execute_batch107(
    package: Mapping[str, object], *, authorization: SingleChunkExecutionAuthorization | None,
    root: str | Path, now: str, confirm_execution_id: str, environ: Mapping[str, str] | None = None,
    provider: Callable[[Mapping[str, object]], str] | None = None, test_mode: bool = False,
    semantic_verifier: Callable[..., object] = semantic.verify_post_polish_semantics,
) -> Batch107ExecutionResult:
    started = time.monotonic()
    blockers = validate_execution_package(package)
    if blockers:
        return Batch107ExecutionResult("blocked", "blocked", blockers)
    if confirm_execution_id != package["execution_id"]:
        return Batch107ExecutionResult("blocked", "blocked", ("execution_id_confirmation_mismatch",))
    valid, reasons = validate_package_authorization(package, authorization, now=now)
    if not valid:
        return Batch107ExecutionResult("blocked", "blocked", reasons)
    assert authorization is not None
    if authorization.max_provider_requests != 2 or authorization.max_network_requests != 2:
        return Batch107ExecutionResult("blocked", "blocked", ("authorization_request_budget_not_exact",))
    source = os.environ if environ is None else environ
    credential = str(source.get(CREDENTIAL_ENV, "")).strip()
    if not credential:
        return Batch107ExecutionResult("credential_unavailable", "blocked", ("credential_unavailable",))
    base = Path(root).resolve()
    try:
        target = _load_target(package, root=base)
        review_dir = _safe_resolve(base, Path(str(package["review_artifact_directory"])), REVIEW_RELATIVE_DIRECTORY)
    except (OSError, TypeError, ValueError) as exc:
        return Batch107ExecutionResult("blocked", "blocked", (str(exc),))
    if provider is not None and not test_mode:
        return Batch107ExecutionResult("blocked", "blocked", ("injected_provider_forbidden",))
    active_provider = provider or NvidiaBatch107Provider(
        api_key=credential, model=str(package["model"]), timeout_seconds=authorization.timeout_seconds,
    )
    if provider is None and getattr(active_provider, "provenance", "") != "real":
        return Batch107ExecutionResult("blocked", "blocked", ("real_provider_provenance_required",))
    try:
        _claim_execution(review_dir, str(package["execution_id"]), authorization.authorization_fingerprint)
    except FileExistsError:
        return Batch107ExecutionResult("blocked", "blocked", ("execution_already_claimed",))
    except (OSError, ValueError) as exc:
        return Batch107ExecutionResult("blocked", "blocked", (type(exc).__name__,))

    provider_requests = 0
    draft_status = "not_run"
    polish_status = "not_run"

    def call(request: Mapping[str, object]) -> str:
        nonlocal provider_requests
        if provider_requests >= 2:
            raise RuntimeError("third_request_structurally_forbidden")
        provider_requests += 1
        value = active_provider(MappingProxyType(dict(request)))
        network_requests = getattr(active_provider, "network_requests", provider_requests)
        if not isinstance(network_requests, int) or network_requests > 2:
            raise RuntimeError("network_request_budget_exhausted")
        return _validate_provider_text(value)

    try:
        draft = call({
            "request_kind": "draft", "source_text": target.source_text,
            "bounded_context": dict(target.bounded_context), "glossary_subset": dict(target.glossary_subset),
            "source_profile": target.source_profile, "target_profile": target.target_profile,
        })
        draft_status = "succeeded"
        polish = draft
        if bool(package["polish_request_allowed"]):
            polish = call({
                "request_kind": "polish", "source_text": target.source_text, "candidate_text": draft,
                "bounded_context": dict(target.bounded_context), "glossary_subset": dict(target.glossary_subset),
                "target_profile": target.target_profile,
            })
            polish_status = "succeeded"
        else:
            polish_status = "not_required"
    except Exception as exc:
        if draft_status != "succeeded" and provider_requests >= 1:
            draft_status = "failed"
        elif draft_status == "succeeded" and polish_status != "succeeded" and provider_requests >= 2:
            polish_status = "failed"
        elapsed = round((time.monotonic() - started) * 1000, 3)
        network_requests = getattr(active_provider, "network_requests", provider_requests)
        return Batch107ExecutionResult(
            "failed", "provider_failed", (type(exc).__name__,), provider_requests,
            network_requests if isinstance(network_requests, int) else provider_requests,
            draft_status, polish_status, elapsed_milliseconds=elapsed,
            response_status_classification="provider_failed",
        )
    try:
        verification = _semantic_verify(target, draft, polish, now=now, verifier=semantic_verifier)
        semantic_status = _status_value(verification)
    except Exception as exc:
        elapsed = round((time.monotonic() - started) * 1000, 3)
        return Batch107ExecutionResult(
            "failed", "semantic_failed", (type(exc).__name__,), provider_requests,
            int(getattr(active_provider, "network_requests", provider_requests)), draft_status, polish_status,
            elapsed_milliseconds=elapsed, response_status_classification="valid_provider_response",
            semantic_verification_outcome="semantic_failed",
        )
    if semantic_status == "failed":
        outcome = "semantic_failed"
    elif semantic_status != "passed":
        outcome = "insufficient_evidence"
    else:
        outcome = "verified_candidate"
    artifact_path = artifact_hash = None
    if outcome == "verified_candidate":
        elapsed = round((time.monotonic() - started) * 1000, 3)
        artifact = build_review_artifact({
            "schema_version": "1.0", "batch": "10.7", "execution_id": package["execution_id"],
            "authorization_fingerprint": authorization.authorization_fingerprint,
            "document_id": target.document_id, "chunk_id": target.chunk_id,
            "source_hash": target.source_hash, "production_translation_hash": target.production_translation_hash,
            "draft_hash": sha256_text(draft), "polish_hash": sha256_text(polish), "candidate_text": polish,
            "semantic_verification_summary": semantic_status, "provider": package["provider"], "model": package["model"],
            "provider_request_count": provider_requests,
            "network_request_count": int(getattr(active_provider, "network_requests", provider_requests)),
            "elapsed_milliseconds": elapsed, "rollback_baseline_identity": target.rollback_baseline_hash,
            "manual_review_status": "awaiting_manual_review", "formal_output_changed": False,
            "resume_changed": False, "cache_changed": False, "stores_changed": False,
        })
        artifact_path, artifact_hash = write_review_artifact(review_dir, artifact)
    elapsed = round((time.monotonic() - started) * 1000, 3)
    return Batch107ExecutionResult(
        "completed", outcome, provider_requests=provider_requests,
        network_requests=int(getattr(active_provider, "network_requests", provider_requests)),
        draft_request_status=draft_status, polish_request_status=polish_status,
        elapsed_milliseconds=elapsed, response_status_classification="valid_provider_response",
        semantic_verification_outcome=outcome, review_artifact_path=artifact_path,
        review_artifact_hash=artifact_hash,
    )
