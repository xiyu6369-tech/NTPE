"""Fail-closed adapters from frozen Stage 11 quality representations."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import json
from pathlib import Path

from core.translation_prompt_improvement_planner import (
    PromptImprovementPlan,
    improvement_plan_sha256,
    validate_plans,
)
from core.translation_quality_defects import (
    DefectLocation,
    TranslationDefect,
    quality_defects_sha256,
    validate_defects,
)
from core.translation_quality_metrics import (
    QualityMetric,
    QualityMetricsConfig,
    quality_metrics_sha256,
)
from core.translation_quality_review_artifacts import (
    StructuredReview,
    review_artifact_sha256,
    validate_review,
)
from core.translation_quality_review_decision import (
    HumanReviewDecision,
    deserialize_review_decision,
)


def _serialized(value: object, *, label: str) -> tuple[Mapping[str, object], str | None]:
    if isinstance(value, Mapping):
        return value, None
    if isinstance(value, Path) or (isinstance(value, str) and not value.lstrip().startswith("{")):
        path = Path(value)
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid {label} artifact: {exc}") from exc
        if not isinstance(raw, Mapping):
            raise ValueError(f"{label} artifact must be a JSON object")
        return raw, path.resolve().as_posix()
    if isinstance(value, (str, bytes, bytearray)):
        try:
            raw = json.loads(value)
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid serialized {label}: {exc}") from exc
        if not isinstance(raw, Mapping):
            raise ValueError(f"serialized {label} must be a JSON object")
        return raw, None
    raise TypeError(f"{label} must be a frozen model, mapping, JSON payload, or artifact path")


def _verified_payload(raw: Mapping[str, object], digest, *, label: str) -> dict[str, object]:
    payload = dict(raw)
    integrity = payload.pop("integrity", None)
    if not isinstance(integrity, Mapping) or integrity.get("algorithm") != "sha256":
        raise ValueError(f"{label} integrity metadata missing")
    if integrity.get("payload_sha256") != digest(payload):
        raise ValueError(f"{label} integrity failure")
    return payload


def defects_input(value: object) -> tuple[tuple[TranslationDefect, ...], tuple[str, ...]]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        if not all(isinstance(row, TranslationDefect) for row in value):
            raise TypeError("defects sequence must contain TranslationDefect models")
        return validate_defects(value), ()
    raw, reference = _serialized(value, label="quality defects")
    payload = _verified_payload(raw, quality_defects_sha256, label="quality defects")
    if payload.get("human_review_based") is not True or payload.get("provider_execution_performed") is not False or payload.get("new_translation_generated") is not False:
        raise ValueError("quality defects artifact boundary invalid")
    rows = payload.get("defects")
    if not isinstance(rows, list) or payload.get("defect_count") != len(rows):
        raise ValueError("quality defects artifact schema invalid")
    try:
        defects = tuple(
            TranslationDefect(
                **{
                    **row,
                    "secondary_categories": tuple(row["secondary_categories"]),
                    "source_location": DefectLocation(**row["source_location"]),
                    "translation_location": DefectLocation(**row["translation_location"]),
                }
            )
            for row in rows
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("quality defects rows invalid") from exc
    defects = validate_defects(defects)
    if payload.get("blocking_defect_count") != sum(row.blocking for row in defects):
        raise ValueError("quality defects blocking count mismatch")
    return defects, (reference,) if reference else ()


def metrics_input(value: object) -> tuple[tuple[QualityMetric, ...], bool, tuple[str, ...]]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        if not all(isinstance(row, QualityMetric) for row in value):
            raise TypeError("metrics sequence must contain QualityMetric models")
        metrics = tuple(value)
        overall = _overall(metrics)
        quality_pass = overall.status == "evaluated" and overall.score >= QualityMetricsConfig().passing_score
        return metrics, quality_pass, ()
    raw, reference = _serialized(value, label="quality metrics")
    payload = _verified_payload(raw, quality_metrics_sha256, label="quality metrics")
    if payload.get("provider_execution_performed") is not False or payload.get("new_translation_generated") is not False or not isinstance(payload.get("quality_pass"), bool):
        raise ValueError("quality metrics artifact boundary invalid")
    rows = payload.get("metrics")
    if not isinstance(rows, list):
        raise ValueError("quality metrics rows missing")
    try:
        metrics = tuple(QualityMetric(**{**row, "related_defect_ids": tuple(row["related_defect_ids"])}) for row in rows)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("quality metrics rows invalid") from exc
    _overall(metrics)
    return metrics, payload["quality_pass"], (reference,) if reference else ()


def _overall(metrics: tuple[QualityMetric, ...]) -> QualityMetric:
    rows = [row for row in metrics if row.dimension == "overall"]
    if len(rows) != 1:
        raise ValueError("quality metrics require exactly one overall dimension")
    return rows[0]


def review_input(value: object) -> tuple[StructuredReview, tuple[str, ...]]:
    if isinstance(value, StructuredReview):
        return validate_review(value), ()
    raw, reference = _serialized(value, label="quality review")
    payload = _verified_payload(raw, review_artifact_sha256, label="quality review")
    try:
        review = StructuredReview(**{key: value for key, value in payload.items() if key != "stage"})
    except (TypeError, ValueError) as exc:
        raise ValueError("quality review schema invalid") from exc
    return validate_review(review), (reference,) if reference else ()


def plans_input(value: object) -> tuple[tuple[PromptImprovementPlan, ...], bool, bool, tuple[str, ...]]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        if not all(isinstance(row, PromptImprovementPlan) for row in value):
            raise TypeError("plans sequence must contain PromptImprovementPlan models")
        plans = validate_plans(value)
        return plans, False, any(row.requires_human_approval for row in plans), ()
    raw, reference = _serialized(value, label="improvement plans")
    payload = _verified_payload(raw, improvement_plan_sha256, label="improvement plans")
    boundaries = ("prompt_modified", "runtime_modified", "provider_executed", "new_translation_generated")
    if any(payload.get(field) is not False for field in boundaries) or payload.get("plans_applied") != 0 or payload.get("human_approval_required") is not True:
        raise ValueError("improvement plan artifact boundary invalid")
    rows = payload.get("plans")
    if not isinstance(rows, list):
        raise ValueError("improvement plans missing")
    try:
        plans = tuple(PromptImprovementPlan(**{**row, "related_defect_ids": tuple(row["related_defect_ids"])}) for row in rows)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("improvement plan rows invalid") from exc
    return validate_plans(plans), False, True, (reference,) if reference else ()


def decision_input(value: object | None) -> tuple[HumanReviewDecision | None, bool, tuple[str, ...]]:
    if value is None:
        return None, False, ()
    if isinstance(value, HumanReviewDecision):
        return deserialize_review_decision(value.to_dict()), False, ()
    raw, reference = _serialized(value, label="human decision")
    if "fixture" in raw:
        fixture = raw.get("fixture")
        boundary = raw.get("boundary")
        if not isinstance(fixture, Mapping) or not isinstance(boundary, Mapping):
            raise ValueError("human decision contract schema invalid")
        if fixture.get("fixture") is not True or fixture.get("not_applied") is not True or boundary.get("decision_applied") is not False:
            raise ValueError("human decision contract may not be applied")
        decision_raw = fixture.get("decision")
    else:
        decision_raw = raw
    if not isinstance(decision_raw, Mapping):
        raise ValueError("human decision payload missing")
    decision = deserialize_review_decision(decision_raw)
    return decision, False, (reference,) if reference else ()


__all__ = ["decision_input", "defects_input", "metrics_input", "plans_input", "review_input"]

