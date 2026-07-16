from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Mapping

from .serialization import deterministic_fingerprint, validate_safe_metadata


@dataclass(frozen=True)
class ReadOnlyView:
    adapter: str
    payload: Mapping[str, Any]
    source_fingerprint: str


def _adapt(name: str, value: Mapping[str, Any], allowed: tuple[str, ...]) -> ReadOnlyView:
    before = deterministic_fingerprint(value)
    validate_safe_metadata(value)
    copied = copy.deepcopy(dict(value))
    payload = {key: copied[key] for key in allowed if key in copied}
    if deterministic_fingerprint(value) != before:
        raise RuntimeError("production metadata mutated during shadow adaptation")
    return ReadOnlyView(name, payload, before)


def adapt_runtime_metadata(value: Mapping[str, Any]) -> ReadOnlyView:
    return _adapt("runtime_metadata", value, ("runtime_version", "document_id", "chunk_index"))


def adapt_prompt_identity(value: Mapping[str, Any]) -> ReadOnlyView:
    return _adapt("prompt_identity", value, ("prompt_identity", "context_fingerprint", "glossary_fingerprint"))


def adapt_resume_read_only(value: Mapping[str, Any]) -> ReadOnlyView:
    return _adapt("resume_read_only", value, ("resume_identity", "status", "attempt_count"))


def adapt_output_contract(value: Mapping[str, Any]) -> ReadOnlyView:
    return _adapt("output_contract", value, ("output_contract_identity", "format", "encoding"))


def adapt_quality_evidence(value: Mapping[str, Any]) -> ReadOnlyView:
    return _adapt("quality_evidence", value, ("quality_policy_identity", "requires_semantic_verification"))


def adapt_provider_metadata(value: Mapping[str, Any]) -> ReadOnlyView:
    return _adapt("provider_metadata", value, ("provider_identity", "model_identity", "prepare_only"))
