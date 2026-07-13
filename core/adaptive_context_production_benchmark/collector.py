from __future__ import annotations

from dataclasses import fields
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from .model import BenchmarkContract, BenchmarkRun, ChunkEvidence

_COMPLETION = {"provider_completed", "resume", "skipped", "failed"}
_ACE_STATE = {"activated", "sampled_fallback", "not_sampled", "disabled"}


def collect_chunk(payload: Mapping[str, Any]) -> ChunkEvidence:
    allowed = {item.name for item in fields(ChunkEvidence)}
    values = {key: payload[key] for key in allowed if key in payload}
    chunk = ChunkEvidence(**values)  # type: ignore[arg-type]
    if chunk.completion not in _COMPLETION:
        raise ValueError("invalid chunk completion")
    if chunk.ace_state not in _ACE_STATE:
        raise ValueError("invalid ACE state")
    if chunk.completion == "resume" and (chunk.provider_calls or chunk.provider_attempts or chunk.provider_latency_ms):
        raise ValueError("resume chunk contains current-run provider evidence")
    if chunk.ace_state == "activated" and chunk.completion == "resume":
        raise ValueError("resume chunk cannot be current-run ACE activation")
    return chunk


def collect_run(
    *, run_kind: str, mode: str, stage: str, contract: BenchmarkContract,
    chunks: Iterable[ChunkEvidence | Mapping[str, Any]], execution_total_ms: float = 0.0,
    rollback_triggered: bool = False, artifact_integrity: bool = True,
    status: str = "complete", limitations: Iterable[str] = (),
) -> BenchmarkRun:
    rows = tuple(row if isinstance(row, ChunkEvidence) else collect_chunk(row) for row in chunks)
    completed = tuple(row for row in rows if row.provider_completed)
    timing_complete = mode != "provider" or (bool(completed) and all(row.provider_latency_ms is not None for row in completed))
    return BenchmarkRun(
        run_kind=run_kind, mode=mode, stage=stage, contract=contract, chunks=rows,
        execution_total_ms=max(0.0, float(execution_total_ms)), rollback_triggered=rollback_triggered,
        artifact_integrity=artifact_integrity, provider_evidence_complete=timing_complete,
        status=status, limitations=tuple(dict.fromkeys(str(value) for value in limitations)),
    )


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {}
    return value if isinstance(value, dict) else {}


def _quality(row: Mapping[str, Any]) -> tuple[str, float | None, int, int, int, int, int, int]:
    qa = row.get("qa") if isinstance(row.get("qa"), Mapping) else {}
    unified = qa.get("unified_quality_report") if isinstance(qa.get("unified_quality_report"), Mapping) else {}
    qv5 = qa.get("quality_v5") if isinstance(qa.get("quality_v5"), Mapping) else {}
    raw_score = unified.get("score", qv5.get("quality_score", qa.get("score")))
    try: score = float(raw_score) if raw_score is not None else None
    except (TypeError, ValueError): score = None
    serialized = json.dumps(qa, ensure_ascii=False).upper()
    status = str(qa.get("status") or qa.get("decision") or row.get("status") or "unknown").lower()
    status = "accepted" if status in {"success", "pass", "pass_with_warning", "accepted"} else "retry" if "retry" in status else "failed" if status in {"failed", "fail", "qa_failed"} else "unknown"
    return (
        status, score, serialized.count("OMISSION") + serialized.count("TOO_SHORT"),
        serialized.count("UNSUPPORTED") + serialized.count("ADDED_DETAIL") + serialized.count("HALLUCINATION"),
        serialized.count("COMPLETENESS"), serialized.count("NATURALNESS_ACTION"),
        serialized.count("NATURALNESS_WARNING"), serialized.count("RECOVERY"),
    )


def collect_regression_run(
    *, root: str | Path, regression_result: Mapping[str, Any], run_kind: str, mode: str,
    profile: str, model: str, api_timeout: int, provider_attempts: int, chunk_size: int,
    max_output_tokens: int, ace_enabled: bool, rollout_percent: int = 0,
    rollout_records: Iterable[Mapping[str, Any]] = (), resume_snapshot: frozenset[tuple[str, int]] = frozenset(),
    rollback_triggered: bool = False,
) -> BenchmarkRun:
    from lts.txt_translation_runtime import read_text_auto, split_text

    root_path = Path(root)
    evidence: list[ChunkEvidence] = []
    plan: list[str] = []
    source_contract: list[str] = []
    observed_max_output_tokens: set[int] = set()
    rollout_rows = tuple(rollout_records)
    rollout_by_identity = {
        (str(row.get("source_hash_sha256", "")), int(row.get("chunk_index", 0) or 0)): row
        for row in rollout_rows
    }
    limitations: list[str] = []
    for record in regression_result.get("records", ()) or ():
        if not isinstance(record, Mapping): continue
        set_name = str(record.get("name", ""))
        source_path = Path(str(record.get("source", "")))
        try:
            source_bytes = source_path.read_bytes()
            source_text = read_text_auto(source_path)
        except OSError:
            limitations.append(f"source-unavailable-{set_name}")
            continue
        source_file_hash = _sha_bytes(source_bytes); source_contract.append(f"{set_name}:{source_file_hash}")
        chunks = split_text(source_text, chunk_size)
        output_dir = Path(str(record.get("output_dir", "")))
        resume_files = sorted(output_dir.glob("*_resume_state.json"))
        state = _json(resume_files[0]) if resume_files else {}
        state_chunks = state.get("chunks") if isinstance(state.get("chunks"), Mapping) else {}
        offset = 0
        for index, source_chunk in enumerate(chunks, 1):
            chunk_hash = _sha_bytes(source_chunk.encode("utf-8"))
            start = source_text.find(source_chunk, offset)
            if start < 0: start = offset
            end = start + len(source_chunk)
            source_offset = f"{start}:{end}"; offset = end
            plan.append(f"{set_name}:{index}:{source_offset}:{chunk_hash}")
            row = state_chunks.get(f"{index:06d}", {}) if isinstance(state_chunks, Mapping) else {}
            row = row if isinstance(row, Mapping) else {}
            resumed = (set_name, index) in resume_snapshot or index in {value for _, value in resume_snapshot}
            raw_status = str(row.get("status", record.get("status", "failed"))).lower()
            completion = "resume" if resumed else "provider_completed" if raw_status in {"success", "pass_with_warning", "qa_failed"} and mode == "provider" else "skipped" if raw_status == "skipped" or mode == "assembly" else "failed"
            rollout_identity = hashlib.sha256(chunk_hash.encode("utf-8")).hexdigest()
            rollout = rollout_by_identity.get((rollout_identity, index), {})
            ace_state = "activated" if rollout.get("activated") is True and not resumed else "sampled_fallback" if rollout.get("fallback_used") is True and not resumed else "not_sampled" if ace_enabled else "disabled"
            qa_status, score, omission, unsupported, completeness, naturalness_actions, warnings, recovery = _quality(row)
            attempts = 0 if resumed or mode == "assembly" else int(row.get("attempt", 0) or 0)
            raw_latency = row.get("provider_latency_ms", row.get("request_latency_ms"))
            try: latency = None if resumed or raw_latency is None else float(raw_latency)
            except (TypeError, ValueError): latency = None
            error_text = str(row.get("error", record.get("error", ""))).lower()
            package = _json(root_path / "prompt_packages" / "txt_runtime" / f"{source_path.stem}_chunk_{index:06d}.json")
            model_profile = package.get("model_profile") if isinstance(package.get("model_profile"), Mapping) else {}
            try:
                observed_max_output_tokens.add(int(model_profile.get("max_output_tokens", max_output_tokens) or max_output_tokens))
            except (TypeError, ValueError):
                limitations.append("max-output-token-evidence-invalid")
            prompt = package.get("prompt") if isinstance(package.get("prompt"), Mapping) else {}
            prompt_profile = prompt.get("prompt_profile") if isinstance(prompt.get("prompt_profile"), Mapping) else {}
            baseline_prompt_tokens = int(prompt_profile.get("total_tokens", 0) or 0)
            baseline_context_tokens = int(prompt_profile.get("context_tokens", 0) or 0)
            saved = int(rollout.get("estimated_tokens_saved", 0) or 0) if ace_state == "activated" else 0
            evidence.append(ChunkEvidence(
                set_name, index, source_file_hash, source_offset, chunk_hash, completion, ace_state,
                provider_calls=int(attempts > 0), provider_attempts=attempts, provider_latency_ms=latency,
                timeout_count=int("timeout" in error_text), http_503_count=int("503" in error_text),
                prompt_tokens=max(0, int(row.get("prompt_tokens", baseline_prompt_tokens) or 0) - saved),
                context_tokens=int(rollout.get("ace_context_tokens", baseline_context_tokens) or 0) if ace_state == "activated" else baseline_context_tokens,
                qa_status=qa_status, quality_score=score, omission_issues=omission,
                unsupported_detail_issues=unsupported, completeness_issues=completeness,
                naturalness_actions=naturalness_actions, naturalness_warnings=warnings,
                recovery_invocations=recovery, quality_evidence_complete=qa_status != "unknown" and score is not None,
                rollback_triggered=rollback_triggered,
            ))
    combined_source_hash = source_contract[0].split(":", 1)[1] if len(source_contract) == 1 else _sha_bytes("|".join(sorted(source_contract)).encode("utf-8"))
    if len(observed_max_output_tokens) > 1:
        limitations.append("max-output-token-contract-inconsistent")
    effective_max_output_tokens = next(iter(observed_max_output_tokens)) if len(observed_max_output_tokens) == 1 else max_output_tokens
    contract = BenchmarkContract(
        set_name="+".join(sorted(str(row.get("name", "")) for row in regression_result.get("records", ()) if isinstance(row, Mapping))),
        source_file_hash=combined_source_hash, chunk_count=len(plan), chunk_plan=tuple(plan), profile=profile,
        model=model, api_timeout=api_timeout, provider_attempts=provider_attempts, chunk_size=chunk_size,
        max_output_tokens=effective_max_output_tokens, prompt_policy_version="te-v6-frozen-prompt-policy",
        quality_v5_version="quality-v5-frozen", retry_recovery_policy_version="te-v6-frozen-retry-recovery",
        ace_enabled=ace_enabled, rollout_percent=rollout_percent,
    )
    elapsed = float((regression_result.get("summary") or {}).get("elapsed_seconds", 0) or 0) * 1000 if isinstance(regression_result.get("summary"), Mapping) else 0.0
    if mode == "provider" and any(row.provider_completed and row.provider_latency_ms is None for row in evidence):
        limitations.append("provider-request-timing-not-persisted-by-frozen-runtime")
    return collect_run(run_kind=run_kind, mode=mode, stage=str(regression_result.get("stage", "")), contract=contract, chunks=evidence, execution_total_ms=elapsed, rollback_triggered=rollback_triggered, status=str(regression_result.get("status", "complete")), limitations=limitations)
