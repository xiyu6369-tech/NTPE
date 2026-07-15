"""Fail-closed adapters from frozen Stage 11 corpus representations."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
import json
from pathlib import Path
from types import MappingProxyType

from core.translation_quality_corpus import (
    GoldenReviewCase,
    corpus_sha256,
    validate_golden_cases,
)
from core.translation_quality_corpus_governance import (
    CorpusGovernanceRecord,
    deserialize_governance_record,
    validate_governance_record,
)


def corpus_input(value: object) -> tuple[tuple[GoldenReviewCase, ...], str, tuple[str, ...]]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        if not all(isinstance(row, GoldenReviewCase) for row in value):
            raise TypeError("corpus sequence must contain GoldenReviewCase models")
        cases = validate_golden_cases(value)
        payload = {"cases": [row.to_dict() for row in cases]}
        return cases, corpus_sha256(payload), ()
    raw, reference, file_digest = _mapping(value, label="golden corpus")
    payload = dict(raw)
    integrity = payload.pop("integrity", None)
    if not isinstance(integrity, Mapping) or integrity.get("algorithm") != "sha256" or integrity.get("payload_sha256") != corpus_sha256(payload):
        raise ValueError("golden corpus integrity failure")
    rows = payload.get("cases")
    if not isinstance(rows, list):
        raise ValueError("golden corpus cases missing")
    try:
        cases = tuple(GoldenReviewCase(**row) for row in rows)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("golden corpus cases invalid") from exc
    return validate_golden_cases(cases), file_digest or corpus_sha256(payload), (reference,) if reference else ()


def governance_input(value: object | None) -> tuple[CorpusGovernanceRecord | Mapping[str, object] | None, tuple[tuple[str, int], ...], tuple[str, ...]]:
    if value is None:
        return None, (), ()
    if isinstance(value, CorpusGovernanceRecord):
        record = validate_governance_record(value)
        return record, ((record.status.value, 1),), ()
    raw, reference, _ = _mapping(value, label="corpus governance")
    if "current_corpus_summary" in raw:
        policy = raw.get("human_only_approval_policy")
        summary = raw.get("current_corpus_summary")
        boundary = raw.get("boundary")
        if not isinstance(policy, Mapping) or policy.get("accepted_decision_is_approval") is not False or policy.get("automatic_approval") is not False:
            raise ValueError("corpus governance human-only policy invalid")
        if not isinstance(summary, Mapping) or not isinstance(boundary, Mapping):
            raise ValueError("corpus governance summary invalid")
        if summary.get("approved_cases") != 0 or summary.get("approved_translations") != 0 or summary.get("all_existing_approved_final_translation_null") is not True:
            raise ValueError("corpus governance fixture unexpectedly approves content")
        if boundary.get("golden_corpus_content_modified") is not False or boundary.get("approved_translations_added") != 0:
            raise ValueError("corpus governance boundary invalid")
        status = raw.get("fixture", {}).get("status") if isinstance(raw.get("fixture"), Mapping) else None
        lifecycle = ((str(status), 1),) if status else ()
        summary_view = MappingProxyType(
            {
                "status": status,
                "approved_cases": summary.get("approved_cases"),
                "approved_translations": summary.get("approved_translations"),
                "accepted_decision_is_approval": policy.get("accepted_decision_is_approval"),
                "automatic_approval": policy.get("automatic_approval"),
                "content_modified": boundary.get("golden_corpus_content_modified"),
            }
        )
        return summary_view, lifecycle, (reference,) if reference else ()
    try:
        record = deserialize_governance_record(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError("corpus governance record invalid") from exc
    return record, ((record.status.value, 1),), (reference,) if reference else ()


def _mapping(value: object, *, label: str) -> tuple[Mapping[str, object], str | None, str | None]:
    if isinstance(value, Mapping):
        return value, None, None
    if isinstance(value, Path) or (isinstance(value, str) and not value.lstrip().startswith("{")):
        path = Path(value)
        try:
            data = path.read_bytes()
            raw = json.loads(data.decode("utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid {label} artifact: {exc}") from exc
        if not isinstance(raw, Mapping):
            raise ValueError(f"{label} artifact must be a JSON object")
        return raw, path.resolve().as_posix(), hashlib.sha256(data).hexdigest()
    if isinstance(value, (str, bytes, bytearray)):
        try:
            raw = json.loads(value)
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid serialized {label}: {exc}") from exc
        if not isinstance(raw, Mapping):
            raise ValueError(f"serialized {label} must be a JSON object")
        return raw, None, None
    raise TypeError(f"{label} must be a frozen model, mapping, JSON payload, or artifact path")


__all__ = ["corpus_input", "governance_input"]
