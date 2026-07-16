"""Pure-offline, fixed-case TIC Batch 7 translation quality gate."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Mapping

from core.shared.evidence import canonical_json_bytes, read_json, sha256_bytes, sha256_file, sha256_text

from .quality_gate_models import QualityGateResult, QualityGateSuiteResult, TranslationCandidate
from .regression_activation import evaluate_active_regression


ROOT = Path(__file__).resolve().parents[2]
BATCH61_DIR = Path("artifacts/tic_batch61")
APPROVALS_PATH = BATCH61_DIR / "HUMAN_APPROVAL_RECORDS.json"
CORRECTIONS_PATH = BATCH61_DIR / "HUMAN_CORRECTION_RECORDS_V2.json"
REGRESSIONS_PATH = BATCH61_DIR / "ACTIVE_TRANSLATION_QUALITY_REGRESSIONS.json"
VALIDATION_PATH = BATCH61_DIR / "ACTIVE_REGRESSION_VALIDATION.json"
STATISTICS_PATH = BATCH61_DIR / "TIC_BATCH61_STATISTICS.json"
INDEX_PATH = BATCH61_DIR / "ACTIVE_REGRESSION_INDEX.json"
BATCH61_MANIFEST = Path("manifests/tic_batch61_human_approval_regression_activation_manifest.json")
BATCH6_REGRESSIONS = Path("artifacts/tic_batch6/TRANSLATION_QUALITY_REGRESSION_CASES.json")
FORMAL_INPUTS = (APPROVALS_PATH, CORRECTIONS_PATH, REGRESSIONS_PATH, VALIDATION_PATH, STATISTICS_PATH, INDEX_PATH)


@dataclass(frozen=True, slots=True)
class QualityGateContext:
    regressions: tuple[Mapping[str, Any], ...]
    approvals: Mapping[str, Mapping[str, Any]]
    corrections: Mapping[str, Mapping[str, Any]]
    source_anchors: Mapping[str, str]


def _object(root: Path, relative: Path) -> dict[str, Any]:
    value = read_json(root / relative)
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {relative.as_posix()}")
    return value


def _valid_integrity(item: Mapping[str, Any]) -> bool:
    body = {key: value for key, value in item.items() if key != "integrity"}
    expected = sha256_bytes(canonical_json_bytes(body))
    return item.get("integrity", {}).get("payload_sha256") == expected


def validate_untrusted_regression_records(
    *, regressions: tuple[Mapping[str, Any], ...], approvals: tuple[Mapping[str, Any], ...]
) -> tuple[bool, tuple[str, ...]]:
    """Validate an untrusted in-memory snapshot without evaluating candidates."""
    reasons: list[str] = []
    approval_map = {item.get("approval_id"): item for item in approvals}
    for regression in regressions:
        if not _valid_integrity(regression):
            reasons.append("tampered_regression_integrity")
            continue
        approval = approval_map.get(regression.get("approval_id"))
        if approval is None or approval.get("approval_status") != "human_approved":
            reasons.append("missing_human_approval")
            continue
        if sha256_text(regression.get("approved_translation", "")) != regression.get("approved_translation_sha256"):
            reasons.append("approved_translation_sha_mismatch")
        if regression.get("approved_translation_sha256") != approval.get("approved_translation_sha256"):
            reasons.append("approval_regression_sha_mismatch")
    return not reasons, tuple(reasons)


def validate_batch1_through_batch61_anchors(root: str | Path = ROOT) -> dict[str, str]:
    base = Path(root).resolve()
    manifest = _object(base, BATCH61_MANIFEST)
    anchors = dict(manifest["source_anchors"])
    for relative, expected in anchors.items():
        if sha256_file(base / relative) != expected:
            raise ValueError(f"frozen Batch 1-6 anchor SHA mismatch: {relative}")
    for relative in FORMAL_INPUTS:
        key = relative.as_posix()
        actual = sha256_file(base / relative)
        if manifest["files"].get(key) != actual:
            raise ValueError(f"frozen Batch 6.1 input SHA mismatch: {key}")
        anchors[key] = actual
    anchors[BATCH61_MANIFEST.as_posix()] = sha256_file(base / BATCH61_MANIFEST)
    return dict(sorted(anchors.items()))


def load_quality_gate_context(root: str | Path = ROOT) -> QualityGateContext:
    base = Path(root).resolve()
    anchors = validate_batch1_through_batch61_anchors(base)
    regressions = _object(base, REGRESSIONS_PATH)["items"]
    approvals = _object(base, APPROVALS_PATH)["items"]
    corrections = _object(base, CORRECTIONS_PATH)["items"]
    defect_cases = _object(base, BATCH6_REGRESSIONS)["items"]
    approval_map = {item["approval_id"]: item for item in approvals}
    correction_map = {item["failure_case_id"]: item for item in corrections}
    defect_map = {item["failure_case_id"]: item for item in defect_cases}
    if len(regressions) != 2 or len(approval_map) != 2 or len(correction_map) != 2:
        raise ValueError("quality gate requires exactly two traceable active regressions")
    enriched: list[dict[str, Any]] = []
    for regression in regressions:
        if not _valid_integrity(regression):
            raise ValueError("tampered regression integrity")
        approval = approval_map.get(regression.get("approval_id"))
        correction = correction_map.get(regression.get("failure_case_id"))
        defect = defect_map.get(regression.get("failure_case_id"))
        if approval is None or approval.get("approval_status") != "human_approved":
            raise ValueError("missing human approval")
        if correction is None or correction.get("correction_status") != "human_approved":
            raise ValueError("missing human-approved correction")
        if defect is None:
            raise ValueError("missing defect metadata")
        approved_sha = sha256_text(regression["approved_translation"])
        if approved_sha != regression.get("approved_translation_sha256") or approved_sha != approval.get("approved_translation_sha256"):
            raise ValueError("approved translation SHA mismatch")
        if sha256_text(regression["source_text"]) != regression.get("source_sha256"):
            raise ValueError("source SHA mismatch")
        item = dict(regression)
        item.update(
            {
                "case_id": correction["case_id"],
                "alignment_id": correction["alignment_id"],
                "defect_blocking": bool(defect["blocking"]),
                "regression_gate_blocking": bool(regression["blocking"]),
                "applicability_type": "fixed_source_sha_and_case_metadata",
            }
        )
        enriched.append(item)
    return QualityGateContext(tuple(enriched), approval_map, correction_map, anchors)


@lru_cache(maxsize=1)
def _default_context() -> QualityGateContext:
    return load_quality_gate_context(ROOT)


def _candidate_id(candidate: TranslationCandidate, requested: tuple[str, ...] | None) -> str:
    if candidate.candidate_id:
        return candidate.candidate_id
    identity = {
        "source_sha256": sha256_text(candidate.source_text) if isinstance(candidate.source_text, str) else "invalid",
        "translation_sha256": sha256_text(candidate.translation_text) if isinstance(candidate.translation_text, str) else "invalid",
        "applicable_regression_ids": list(requested or ()),
        "case_id": candidate.case_id,
        "failure_case_id": candidate.failure_case_id,
    }
    return "TIC-CAND-B7-" + sha256_bytes(canonical_json_bytes(identity))[:20].upper()


def _result(
    *, candidate: TranslationCandidate, requested: tuple[str, ...] | None,
    all_ids: tuple[str, ...], applicable: tuple[str, ...] = (), passed: tuple[str, ...] = (),
    failed: tuple[str, ...] = (), status: str, reasons: Iterable[str] = (), details: Iterable[Mapping[str, Any]] = (),
) -> QualityGateResult:
    allowed = status == "pass"
    body = {
        "candidate_id": _candidate_id(candidate, requested),
        "source_sha256": sha256_text(candidate.source_text) if isinstance(candidate.source_text, str) else "",
        "translation_sha256": sha256_text(candidate.translation_text) if isinstance(candidate.translation_text, str) else "",
        "applicable_regressions": list(applicable),
        "passed_regressions": list(passed),
        "failed_regressions": list(failed),
        "skipped_regressions": [item for item in all_ids if item not in applicable],
        "gate_status": status,
        "gate_blocking": status != "pass",
        "quality_candidate_allowed": allowed,
        "review_ready": allowed,
        "regression_safe": allowed,
        "failure_reasons": list(reasons),
        "evaluation_details": [dict(item) for item in details],
        "provider_executed": False,
        "network_requests": 0,
        "disk_writes": 0,
    }
    integrity = {"algorithm": "sha256", "payload_sha256": sha256_bytes(canonical_json_bytes(body))}
    return QualityGateResult(
        candidate_id=body["candidate_id"], source_sha256=body["source_sha256"], translation_sha256=body["translation_sha256"],
        applicable_regressions=tuple(body["applicable_regressions"]), passed_regressions=tuple(body["passed_regressions"]),
        failed_regressions=tuple(body["failed_regressions"]), skipped_regressions=tuple(body["skipped_regressions"]),
        gate_status=status, gate_blocking=body["gate_blocking"], quality_candidate_allowed=allowed,
        review_ready=allowed, regression_safe=allowed, failure_reasons=tuple(body["failure_reasons"]),
        evaluation_details=tuple(body["evaluation_details"]), integrity=integrity,
    )


def _metadata_matches(candidate: TranslationCandidate, regression: Mapping[str, Any]) -> bool:
    alignment_id = candidate.metadata.get("alignment_id")
    return (
        candidate.case_id == regression["case_id"]
        and candidate.failure_case_id == regression["failure_case_id"]
        and alignment_id == regression["alignment_id"]
    )


def _evaluate_candidate(
    candidate: TranslationCandidate,
    requested: tuple[str, ...] | None,
    context: QualityGateContext,
) -> QualityGateResult:
    all_ids = tuple(item["regression_id"] for item in context.regressions)
    if not isinstance(candidate.source_text, str) or not candidate.source_text.strip() or not isinstance(candidate.translation_text, str) or not candidate.translation_text.strip():
        return _result(candidate=candidate, requested=requested, all_ids=all_ids, status="invalid_input", reasons=("source_or_translation_is_empty_or_invalid",))
    if requested is not None and (not isinstance(requested, tuple) or any(not isinstance(item, str) for item in requested)):
        return _result(candidate=candidate, requested=None, all_ids=all_ids, status="invalid_input", reasons=("applicable_regression_ids_must_be_a_tuple_of_strings",))
    unknown = tuple(item for item in (requested or ()) if item not in all_ids)
    if unknown:
        return _result(candidate=candidate, requested=requested, all_ids=all_ids, status="invalid_input", reasons=("unknown_regression_id",))

    applicable_records: list[Mapping[str, Any]] = []
    explicit_mismatch = False
    for regression in context.regressions:
        regression_id = regression["regression_id"]
        source_match = candidate.source_text == regression["source_text"] and sha256_text(candidate.source_text) == regression["source_sha256"]
        requested_match = requested is not None and regression_id in requested
        metadata_match = _metadata_matches(candidate, regression)
        if regression["category"] == "lexical_choice":
            applies = source_match and (requested_match or metadata_match)
        else:
            applies = source_match and (requested is None or requested_match) and (
                not any((candidate.case_id, candidate.failure_case_id, candidate.metadata.get("alignment_id"))) or metadata_match
            )
        if requested_match and not applies:
            explicit_mismatch = True
        if applies:
            applicable_records.append(regression)
    if explicit_mismatch:
        return _result(candidate=candidate, requested=requested, all_ids=all_ids, status="insufficient_evidence", reasons=("explicit_regression_lacks_matching_source_or_case_metadata",))
    if not applicable_records:
        return _result(candidate=candidate, requested=requested, all_ids=all_ids, status="not_applicable", reasons=("no_fixed_case_applicability",))

    passed: list[str] = []
    failed: list[str] = []
    details: list[dict[str, Any]] = []
    for regression in applicable_records:
        result = evaluate_active_regression(dict(regression), candidate.translation_text)
        regression_id = regression["regression_id"]
        details.append({"regression_id": regression_id, "category": regression["category"], "accepted": result["accepted"], "checks": result["checks"]})
        (passed if result["accepted"] else failed).append(regression_id)
    status = "fail" if failed else "pass"
    reasons = ("one_or_more_active_regressions_failed",) if failed else ()
    return _result(candidate=candidate, requested=requested, all_ids=all_ids, applicable=tuple(item["regression_id"] for item in applicable_records), passed=tuple(passed), failed=tuple(failed), status=status, reasons=reasons, details=details)


def evaluate_translation_candidate(
    *, source_text: str, translation_text: str,
    applicable_regression_ids: tuple[str, ...] | None = None,
    candidate_id: str | None = None,
) -> QualityGateResult:
    candidate = TranslationCandidate(candidate_id, source_text, translation_text)
    try:
        context = _default_context()
    except (KeyError, TypeError, ValueError) as exc:
        empty = QualityGateContext((), {}, {}, {})
        return _result(candidate=candidate, requested=applicable_regression_ids, all_ids=(), status="invalid_input", reasons=(f"invalid_regression_context:{type(exc).__name__}",))
    return _evaluate_candidate(candidate, applicable_regression_ids, context)


def evaluate_regression_suite(*, candidates: tuple[TranslationCandidate, ...]) -> QualityGateSuiteResult:
    if not isinstance(candidates, tuple):
        raise TypeError("candidates must be a tuple")
    context = _default_context()
    results = tuple(_evaluate_candidate(item, None, context) for item in candidates)
    counts = {status: sum(item.gate_status == status for item in results) for status in ("pass", "fail", "not_applicable", "insufficient_evidence", "invalid_input")}
    body = {"result_integrities": [dict(item.integrity) for item in results], "total_candidates": len(results), "counts": counts}
    integrity = {"algorithm": "sha256", "payload_sha256": sha256_bytes(canonical_json_bytes(body))}
    return QualityGateSuiteResult(results, len(results), counts["pass"], counts["fail"], counts["not_applicable"], counts["insufficient_evidence"], counts["invalid_input"], bool(results) and all(item.regression_safe for item in results), integrity=integrity)
