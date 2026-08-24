from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from time import perf_counter
from typing import Protocol

from core.literary import LiteraryPromptBuilder, estimate_tokens
from core.translation_engine.nvidia_client import NvidiaClient
from core.translation_quality_canary import (
    ACTIVATION_GATE_READY,
    CANDIDATE_FLAGS,
    CHECKLIST,
    build_offline_canary_stores,
)
from core.translation_quality_integration_v72 import (
    QualityIntegrationRequest,
    integrate_prompt,
)
from core.production_runtime.manifest import get_te_v7_stage_path

AUTHORIZATION_TOKEN = "AUTHORIZE_NTPE_TE_V72_STAGE1252_PROVIDER_CANARY"
PROVIDER_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
ALLOWED_MODEL = "meta/llama-3.3-70b-instruct"
SELECTION_TIME = "2026-07-19T00:03:00Z"


def _sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


@dataclass(frozen=True)
class CanaryExecutionConfig:
    authorization_id: str
    authorization_token: str
    provider: str = "nvidia"
    provider_url: str = PROVIDER_URL
    model: str = ALLOWED_MODEL
    timeout_seconds: int = 180
    max_output_tokens: int = 800
    temperature: float = 0.12
    top_p: float = 0.82
    attempt_limit_per_arm: int = 1
    retry_count: int = 0
    fallback: bool = False
    parallel_jobs: int = 1
    excerpt_limit: int = 2

    def validate(self) -> tuple[str, ...]:
        blockers: list[str] = []
        if not self.authorization_id or not self.authorization_id.replace("-", "").replace("_", "").isalnum():
            blockers.append("authorization-id-invalid")
        if self.authorization_token != AUTHORIZATION_TOKEN:
            blockers.append("execution-authorization-invalid")
        if self.provider != "nvidia" or self.provider_url != PROVIDER_URL:
            blockers.append("provider-not-allowlisted")
        if self.model != ALLOWED_MODEL:
            blockers.append("model-not-allowlisted")
        if self.timeout_seconds != 180 or self.max_output_tokens != 800:
            blockers.append("execution-settings-not-frozen")
        if self.temperature != 0.12 or self.top_p != 0.82:
            blockers.append("sampling-settings-not-frozen")
        if self.attempt_limit_per_arm != 1 or self.retry_count != 0:
            blockers.append("single-attempt-zero-retry-required")
        if self.fallback or self.parallel_jobs != 1:
            blockers.append("fallback-or-parallelism-forbidden")
        if self.excerpt_limit != 2:
            blockers.append("exactly-two-excerpts-required")
        return tuple(blockers)


@dataclass(frozen=True)
class ProviderOutcome:
    success: bool
    content: str
    latency_ms: float
    error_category: str | None = None
    actual_prompt_tokens: int | None = None
    actual_completion_tokens: int | None = None
    cost: float | None = None


class CanaryTransport(Protocol):
    provenance: str

    def invoke(self, *, system_prompt: str, user_prompt: str, config: CanaryExecutionConfig) -> ProviderOutcome: ...


class NvidiaCanaryTransport:
    provenance = "real"

    def invoke(self, *, system_prompt: str, user_prompt: str, config: CanaryExecutionConfig) -> ProviderOutcome:
        client = NvidiaClient(api_url=config.provider_url, timeout=config.timeout_seconds)
        started = perf_counter()
        try:
            output = client.chat(
                model=config.model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=config.temperature,
                top_p=config.top_p,
                max_tokens=config.max_output_tokens,
            )
            return ProviderOutcome(True, output, round((perf_counter() - started) * 1000, 3))
        except RuntimeError as exc:
            message = str(exc).lower()
            category = "timeout" if "timeout" in message else "provider_error"
            return ProviderOutcome(False, "", round((perf_counter() - started) * 1000, 3), category)


@dataclass(frozen=True)
class CanaryExecutionResult:
    status: str
    request_count: int
    network_request_count: int
    artifact_root: str
    blockers: tuple[str, ...] = ()


def _load_cases(root: Path, limit: int) -> list[dict[str, object]]:
    corpus = root / "tests/fixtures/te_v72_canary/golden_corpus.json"
    payload = json.loads(corpus.read_text(encoding="utf-8"))
    cases = payload.get("cases")
    if not isinstance(cases, list) or len(cases) < limit:
        raise ValueError("engineering-corpus-insufficient")
    return cases[:limit]


def _build_prompts(case_id: str, source: str) -> tuple[str, str, str, dict[str, object]]:
    prompt = LiteraryPromptBuilder().build(
        chunk_text=source, locked_dictionary={}, alias_map={}, previous_context="", profile="literary"
    )
    characters, contexts = build_offline_canary_stores()
    request = QualityIntegrationRequest(
        source_text=source,
        base_prompt_tokens=prompt.prompt_profile.total_tokens,
        glossary_tokens=prompt.prompt_profile.glossary_tokens,
        flags=CANDIDATE_FLAGS,
        character_store=characters,
        context_scene_store=contexts,
        active_character_ids=("char-yeonghui",),
        chapter_id="chapter-1",
        scene_id="scene-1",
        sequence_index=2,
        source_language="ko",
        scope={"chapter_id": "chapter-1", "segment_id": case_id},
        selection_time=SELECTION_TIME,
    )
    candidate = integrate_prompt(prompt.user_prompt, request)
    return prompt.system_prompt, prompt.user_prompt, candidate.user_prompt, candidate.metadata.to_dict()


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_canonical_bytes(value))


def _claim(path: Path, config: CanaryExecutionConfig) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    claim = {
        "stage": "TE-v7.2-Stage12.5.2",
        "authorization_id": config.authorization_id,
        "claimed": True,
        "request_budget": config.excerpt_limit * 2,
        "attempt_limit_per_arm": 1,
        "retry": 0,
        "fallback": False,
        "parallel_jobs": 1,
    }
    try:
        with path.open("xb") as stream:
            stream.write(_canonical_bytes(claim))
    except FileExistsError as exc:
        raise ValueError("provider-canary-authorization-already-claimed") from exc


def execute_canary(
    config: CanaryExecutionConfig,
*,
    root: str | Path,
    transport: CanaryTransport | None = None,
    claim: bool = True,
) -> CanaryExecutionResult:
    blockers = config.validate()
    base = Path(root).resolve()
    artifact_root = get_te_v7_stage_path(base, "te_v72_canary_execution")
    if blockers:
        return CanaryExecutionResult("blocked", 0, 0, str(artifact_root), blockers)
    active = transport or NvidiaCanaryTransport()
    if active.provenance != "real":
        return CanaryExecutionResult("blocked", 0, 0, str(artifact_root), ("real-transport-required",))
    cases = _load_cases(base, config.excerpt_limit)
    if claim:
        _claim(artifact_root / "execution_claim.json", config)

    rows: list[dict[str, object]] = []
    requests = 0
    for case in cases:
        case_id = str(case["case_id"])
        source = str(case["source_text"])
        system, baseline, candidate, integration = _build_prompts(case_id, source)
        for arm, user_prompt in (("baseline", baseline), ("candidate", candidate)):
            requests += 1
            try:
                outcome = active.invoke(system_prompt=system, user_prompt=user_prompt, config=config)
            except Exception as exc:
                outcome = ProviderOutcome(
                    False, "", 0.0,
                    "timeout" if "timeout" in str(exc).lower() else "provider_error",
                )
            output_path = artifact_root / f"{arm}_output/{case_id}.txt"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(outcome.content, encoding="utf-8", newline="\n")
            estimated_prompt = estimate_tokens(system) + estimate_tokens(user_prompt)
            estimated_completion = estimate_tokens(outcome.content) if outcome.content else 0
            row = {
                "case_id": case_id,
                "arm": arm,
                "success": outcome.success,
                "source_sha256": _sha_text(source),
                "system_prompt_sha256": _sha_text(system),
                "user_prompt_sha256": _sha_text(user_prompt),
                "translation_sha256": _sha_text(outcome.content) if outcome.content else None,
                "attempts": 1,
                "retry": 0,
                "fallback": False,
                "latency_ms": outcome.latency_ms,
                "prompt_tokens": outcome.actual_prompt_tokens,
                "completion_tokens": outcome.actual_completion_tokens,
                "estimated_prompt_tokens": estimated_prompt,
                "estimated_completion_tokens": estimated_completion,
                "token_usage_source": "provider" if outcome.actual_prompt_tokens is not None else "estimate",
                "cost": outcome.cost,
                "error_category": outcome.error_category,
                "feature_flags": {
                    "quality_integration": arm == "candidate",
                    "character": arm == "candidate",
                    "context": arm == "candidate",
                    "naturalness": arm == "candidate",
                },
                "integration_metrics": integration if arm == "candidate" else {
                    "enabled": False,
                    "character_records_selected": 0,
                    "context_records_selected": 0,
                    "scene_records_selected": 0,
                    "total_added_tokens": 0,
                },
            }
            rows.append(row)

    complete = all(bool(row["success"]) for row in rows)
    quality_cases = [{
        "case_id": str(case["case_id"]),
        "checklist": {dimension: None for dimension in CHECKLIST},
        "allowed_values": ["Improved", "Same", "Regressed"],
        "review_status": "awaiting_human_review" if all(
            bool(row["success"]) for row in rows if row["case_id"] == str(case["case_id"])
        ) else "not_reviewable_incomplete_pair",
    } for case in cases]
    _write_json(artifact_root / "quality_report.json", {
        "stage": "TE-v7.2-Stage12.5.2",
        "status": "AWAITING_HUMAN_REVIEW" if complete else "FAIL_CLOSED_INCOMPLETE_EXECUTION",
        "canary_pass": False,
        "quality_cases": quality_cases,
        "regressions": None,
        "hallucinations": None,
        "activation_gate": ACTIVATION_GATE_READY,
    })
    manual = ["# TE v7.2 Stage 12.5.2 Manual Review", "", "Status: PENDING", ""]
    for case in cases:
        manual.extend([
            f"## {case['case_id']}", "", "Overall:", "", "Major improvement:", "",
            "Minor improvement:", "", "Regression:", "", "Comments:", "",
        ])
    (artifact_root / "manual_review.md").write_text("\n".join(manual), encoding="utf-8", newline="\n")
    _write_json(artifact_root / "provider_metrics.json", {
        "provider": config.provider,
        "model": config.model,
        "attempt_limit_per_arm": 1,
        "provider_requests": requests,
        "network_requests": requests,
        "timeout_seconds": config.timeout_seconds,
        "retry": 0,
        "fallback": False,
        "parallel_jobs": 1,
        "profile": "literary",
        "glossary_sha256": _sha_text("{}"),
        "token_statistics": {
            "actual_prompt_tokens": sum(int(row["prompt_tokens"] or 0) for row in rows),
            "actual_completion_tokens": sum(int(row["completion_tokens"] or 0) for row in rows),
            "estimated_prompt_tokens": sum(int(row["estimated_prompt_tokens"]) for row in rows),
            "estimated_completion_tokens": sum(int(row["estimated_completion_tokens"]) for row in rows),
        },
        "performance": {
            "total_latency_ms": round(sum(float(row["latency_ms"]) for row in rows), 3),
            "maximum_latency_ms": round(max(float(row["latency_ms"]) for row in rows), 3),
            "cost": None,
            "cost_status": "provider_did_not_supply_cost",
        },
        "rows": rows,
    })
    _write_json(artifact_root / "execution_summary.json", {
        "stage": "TE-v7.2-Stage12.5.2",
        "status": "execution_complete_awaiting_human_review" if complete else "execution_incomplete_fail_closed",
        "excerpt_count": len(cases),
        "provider_requests": requests,
        "network_requests": requests,
        "successful_requests": sum(bool(row["success"]) for row in rows),
        "failed_requests": sum(not bool(row["success"]) for row in rows),
        "activation_gate": ACTIVATION_GATE_READY,
        "boundary": {
            "runtime_modified": False,
            "runtime_default_modified": False,
            "provider_modified": False,
            "milestone_a_modified": False,
            "production_authorized": False,
            "active_production_authorized": False,
            "automatic_rollout_authorized": False,
            "formal_output_replacement_authorized": False,
        },
    })
    return CanaryExecutionResult(
        "execution_complete_awaiting_human_review" if complete else "execution_incomplete_fail_closed",
        requests,
        requests,
        str(artifact_root),
    )


def build_evidence_and_manifest(*, root: str | Path) -> tuple[Path, Path]:
    base = Path(root).resolve()
    artifact_root = get_te_v7_stage_path(base, "te_v72_canary_execution")
    quality = json.loads((artifact_root / "quality_report.json").read_text(encoding="utf-8"))
    human_review_completed = bool(quality.get("human_review_completed"))
    canary_pass = bool(quality.get("canary_pass"))
    evidence_files = sorted(path for path in artifact_root.rglob("*") if path.is_file() and path.name != "canary_execution_evidence.json")
    hashes = {path.relative_to(base).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in evidence_files}
    evidence = {
        "stage": "TE-v7.2-Stage12.5.2",
        "evidence_hashes": hashes,
        "activation_gate": ACTIVATION_GATE_READY,
        "decision": quality.get("decision"),
        "quality_status": quality.get("status"),
        "human_review_completed": human_review_completed,
        "canary_pass": canary_pass,
        "production_authorized": False,
    }
    evidence_path = artifact_root / "canary_execution_evidence.json"
    _write_json(evidence_path, evidence)
    metrics = json.loads((artifact_root / "provider_metrics.json").read_text(encoding="utf-8"))
    source_hashes = {
        path: hashlib.sha256((base / path).read_bytes()).hexdigest()
        for path in (
            "core/translation_quality_provider_canary/__init__.py",
            "core/translation_quality_provider_canary/framework.py",
            "tools/run_te_v720_authorized_provider_canary.py",
            "tests/fixtures/te_v72_canary/golden_corpus.json",
        )
    }
    release_path = base / "docs/releases/te_v7_2/TE_V720_AUTHORIZED_PROVIDER_CANARY.md"
    fingerprint_payload = {
        "source_hashes": source_hashes,
        "evidence_sha256": hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
        "release_sha256": hashlib.sha256(release_path.read_bytes()).hexdigest(),
        "provider": metrics["provider"],
        "model": metrics["model"],
        "provider_requests": metrics["provider_requests"],
    }
    manifest = {
        "schema_version": "te-v7.2-stage12.5.2-authorized-provider-canary-v1",
        "stage": "TE-v7.2-Stage12.5.2",
        "provider": "nvidia",
        "model": ALLOWED_MODEL,
        "attempt_limit_per_arm": 1,
        "timeout_seconds": 180,
        "retry": 0,
        "fallback": False,
        "parallel_jobs": 1,
        "provider_requests": 4,
        "network_requests": 4,
        "prompt_tokens": metrics["token_statistics"]["actual_prompt_tokens"],
        "completion_tokens": metrics["token_statistics"]["actual_completion_tokens"],
        "estimated_prompt_tokens": metrics["token_statistics"]["estimated_prompt_tokens"],
        "estimated_completion_tokens": metrics["token_statistics"]["estimated_completion_tokens"],
        "latency_ms": metrics["performance"]["total_latency_ms"],
        "cost": metrics["performance"]["cost"],
        "cost_status": metrics["performance"]["cost_status"],
        "source_hashes": source_hashes,
        "release_sha256": hashlib.sha256(release_path.read_bytes()).hexdigest(),
        "evidence_sha256": fingerprint_payload["evidence_sha256"],
        "evidence_hashes": hashes,
        "deterministic_metadata": {
            "corpus_sha256": hashlib.sha256((base / "tests/fixtures/te_v72_canary/golden_corpus.json").read_bytes()).hexdigest(),
            "framework_sha256": hashlib.sha256((base / "core/translation_quality_provider_canary/framework.py").read_bytes()).hexdigest(),
            "fingerprint": hashlib.sha256(_canonical_bytes(fingerprint_payload)).hexdigest(),
        },
        "activation_gate": ACTIVATION_GATE_READY,
        "runtime_modified": False,
        "runtime_default_modified": False,
        "prompt_builder_modified": False,
        "provider_modified": False,
        "production_authorized": False,
        "active_production_authorized": False,
        "automatic_rollout_authorized": False,
        "formal_output_replacement_authorized": False,
        "quality_status": quality.get("status"),
        "decision": quality.get("decision"),
        "human_review_completed": human_review_completed,
        "canary_pass": canary_pass,
        "commit_performed": False,
        "push_performed": False,
        "tag_performed": False,
    }
    manifest_path = base / "manifests/te_v720_authorized_provider_canary_manifest.json"
    _write_json(manifest_path, manifest)
    return evidence_path, manifest_path
