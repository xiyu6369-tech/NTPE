from __future__ import annotations

from pathlib import Path
from typing import Any

from core.shared.evidence import (
    canonical_json_bytes,
    read_json,
    resolve_project_relative_path,
    sha256_bytes,
    sha256_file,
    sha256_text,
)

from core.production_runtime.manifest import (
    get_te_v7_stage_path,
    TE_V71_STAGE111_TRANSLATION_DEFECTS,
    TE_V72_STAGE1223_SOURCE_EXCERPT_FREEZE,
)

PRAISE_TERMS = ("很好", "自然", "出版級", "語氣正確", "人物口吻正確", "忠實且流暢", "approved", "accepted as final")


def _to_relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def discover_review_files(root: str | Path) -> list[str]:
    base = Path(root).resolve()
    found: set[str] = set()
    artifacts = base / "artifacts"
    for path in artifacts.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".json", ".txt", ".md"} and (
            "review" in path.name.lower() or "defect" in path.name.lower()
        ):
            found.add(_to_relative(base, path))
    for path in (base / "docs" / "releases").rglob("*.md"):
        found.add(_to_relative(base, path))
    for path in (base / "tests" / "literary" / "outputs").rglob("evaluation.md"):
        found.add(_to_relative(base, path))
    found.add(_to_relative(base, get_te_v7_stage_path(base, "te_v72_stage1223") / TE_V72_STAGE1223_SOURCE_EXCERPT_FREEZE))
    return sorted(found)


def _json_object(root: Path, relative: str) -> dict[str, Any]:
    value = read_json(resolve_project_relative_path(root, relative, must_exist=True))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {relative}")
    return value


def _unique_offset(text: str, excerpt: object) -> tuple[str | None, int | None, int]:
    if not isinstance(excerpt, str) or not excerpt:
        return None, None, 0
    count = text.count(excerpt)
    if count != 1:
        return None, None, count
    return excerpt, text.find(excerpt), count


def _alignment_id(case_id: str, evidence_id: str, source_sha: str, translation_sha: str) -> str:
    identity = {
        "case_id": case_id,
        "evidence_id": evidence_id,
        "source_sha256": source_sha,
        "translation_sha256": translation_sha,
        "method": "manual_evidence_anchor",
    }
    return "TIC-ALIGN-B5-" + sha256_bytes(canonical_json_bytes(identity))[:20].upper()


def search_historical_human_evidence(
    root: str | Path, cases_by_id: dict[str, dict[str, Any]]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    base = Path(root).resolve()
    files = discover_review_files(base)
    defects_path = _to_relative(base, get_te_v7_stage_path(base, "te_v71_stage111") / TE_V71_STAGE111_TRANSLATION_DEFECTS)
    defects_payload = _json_object(base, defects_path)
    if defects_payload.get("human_review_based") is not True:
        raise ValueError("Stage 11 defects lack human-review provenance")
    case = cases_by_id["TIC-CASE-B2-598DC16E43DB4363D420"]
    source_freeze_path = _to_relative(base, get_te_v7_stage_path(base, "te_v72_stage1223") / TE_V72_STAGE1223_SOURCE_EXCERPT_FREEZE)
    source_freeze = _json_object(base, source_freeze_path)
    if source_freeze["parent_source_reference"] != case["source_file"]:
        raise ValueError("Stage 12.2.3 source freeze references a different source")
    if source_freeze["parent_source_sha256"] != case["source_sha256"]:
        raise ValueError("Stage 12.2.3 source freeze SHA mismatch")
    if f"{defects_path}#TQ-DEF-A" not in source_freeze["evidence_references"]:
        raise ValueError("Stage 12.2.3 source freeze lacks TQ-DEF-A reference")
    defect_file_sha = sha256_file(
        resolve_project_relative_path(base, defects_path, must_exist=True)
    )
    items: list[dict[str, Any]] = []
    for defect in defects_payload["defects"]:
        if defect.get("human_confirmed") is not True:
            continue
        source_excerpt, source_start, source_count = _unique_offset(
            case["source_text"], defect.get("source_excerpt")
        )
        frozen_source_match_count = None
        if defect["defect_id"] == "TQ-DEF-A" and source_excerpt is None:
            freeze_start = int(source_freeze["excerpt_start_offset"])
            freeze_end = int(source_freeze["excerpt_end_offset"])
            frozen_text = case["source_text"][freeze_start:freeze_end]
            reported = defect.get("source_excerpt")
            frozen_source_match_count = frozen_text.count(reported) if reported else 0
            if isinstance(reported, str) and reported and frozen_source_match_count == 1:
                source_excerpt = reported
                source_start = freeze_start + frozen_text.find(reported)
        translation_excerpt, translation_start, translation_count = _unique_offset(
            case["translation_text"], defect.get("translation_excerpt")
        )
        precise = source_excerpt is not None and translation_excerpt is not None
        evidence_id = (
            "TIC-EVID-B3-4C47ECCEDCAB1775DE59"
            if defect["defect_id"] == "TQ-DEF-A"
            else f"TIC-EVID-B5-{defect['defect_id']}"
        )
        source_sha = sha256_text(source_excerpt) if source_excerpt else ""
        translation_sha = sha256_text(translation_excerpt) if translation_excerpt else ""
        alignment_id = (
            _alignment_id(case["case_id"], evidence_id, source_sha, translation_sha)
            if precise
            else None
        )
        items.append(
            {
                "evidence_id": evidence_id,
                "source_batch": "TIC Batch 3 / TE-v7.1-Stage11.1",
                "evidence_type": "historical_human_confirmed_defect",
                "evidence_path": defects_path,
                "evidence_sha256": defect_file_sha,
                "reviewer_type": "human",
                "human_provenance": {
                    "complete": True,
                    "origin": defect["review_origin"],
                    "defect_id": defect["defect_id"],
                },
                "review_source": "TE-v7.1-Stage11.1 from Stage10.10.1 human review",
                "review_status": "human_reviewed",
                "source_file": case["source_file"],
                "translation_file": case["translation_file"],
                "case_id": case["case_id"],
                "source_excerpt": source_excerpt,
                "translation_excerpt": translation_excerpt,
                "source_start_offset": source_start if source_excerpt is not None else None,
                "source_end_offset": source_start + len(source_excerpt) if source_excerpt is not None and source_start is not None else None,
                "translation_start_offset": translation_start if translation_excerpt is not None else None,
                "translation_end_offset": translation_start + len(translation_excerpt) if translation_excerpt is not None and translation_start is not None else None,
                "source_excerpt_sha256": source_sha if source_excerpt else None,
                "translation_excerpt_sha256": translation_sha if translation_excerpt else None,
                "failure_category": defect["category"],
                "failure_subcategory": None,
                "quality_judgement": "human_confirmed_failure",
                "precise_alignment_status": "aligned" if precise else "linked_but_not_aligned",
                "alignment_id": alignment_id,
                "alignment_confidence": "high" if precise else "unresolved",
                "alignment_method": "manual_evidence_anchor" if precise else "unresolved",
                "evidence_overlay": precise,
                "coverage_eligible": False if precise else None,
                "source_overlap": 1.0 if precise else 0.0,
                "translation_overlap": 1.0 if precise else (1.0 if translation_excerpt else 0.0),
                "severity": defect["severity"],
                "blocking": defect["blocking"],
                "observed_error": defect["reason"],
                "expected_semantic_constraint": defect["expected_behavior"],
                "usable_for_failure_corpus": precise,
                "usable_for_future_excellence_corpus": False,
                "search_method": "exact_unique_substring_with_repository_frozen_evidence_range"
                if defect["defect_id"] == "TQ-DEF-A"
                else "exact_unique_substring_in_immutable_batch2_case",
                "search_evidence": {
                    "defect_id": defect["defect_id"],
                    "reported_source_excerpt": defect.get("source_excerpt"),
                    "reported_translation_excerpt": defect.get("translation_excerpt"),
                    "source_match_count": source_count,
                    "source_match_count_in_frozen_range": frozen_source_match_count,
                    "translation_match_count": translation_count,
                    "source_disambiguation_artifact": source_freeze["evidence_path"]
                    if defect["defect_id"] == "TQ-DEF-A"
                    else None,
                    "source_disambiguation_range": [
                        source_freeze["excerpt_start_offset"],
                        source_freeze["excerpt_end_offset"],
                    ]
                    if defect["defect_id"] == "TQ-DEF-A"
                    else None,
                },
                "ambiguity_reason": None
                if precise
                else "One or both reported excerpts are absent, non-unique, or not literal text from the immutable Batch 2 case.",
            }
        )
    praise_files: list[str] = []
    for relative in files:
        path = resolve_project_relative_path(base, relative, must_exist=True)
        try:
            text = path.read_text(encoding="utf-8-sig")
        except (UnicodeDecodeError, OSError):
            continue
        if any(term.lower() in text.lower() for term in PRAISE_TERMS):
            praise_files.append(relative)
    report = {
        "schema_version": "tic.batch5.human-evidence-search-report.v1",
        "files_scanned": len(files),
        "human_review_files_found": len(files),
        "human_evidence_candidates": len(items),
        "human_evidence_confirmed": len(items),
        "human_evidence_rejected": 0,
        "human_evidence_unresolved": sum(
            item["precise_alignment_status"] != "aligned" for item in items
        ),
        "exact_source_anchors_found": sum(item["source_excerpt"] is not None for item in items),
        "exact_translation_anchors_found": sum(
            item["translation_excerpt"] is not None for item in items
        ),
        "precise_bilateral_alignments_created": sum(
            item["precise_alignment_status"] == "aligned" for item in items
        ),
        "failure_cases_added": sum(item["usable_for_failure_corpus"] for item in items),
        "future_excellence_candidates_found": 0,
        "scanned_paths": files,
        "praise_keyword_files_reviewed_but_not_admitted": praise_files,
        "inclusion_rule": "Only structured human-confirmed defects with unique exact source and translation excerpts in one immutable Batch 2 case are admitted.",
        "exclusion_rules": [
            "automatic_or_unknown_reviewer",
            "metrics_or_score_only",
            "release_or_test_success_only",
            "praise_keyword_without_precise_human_provenance",
            "missing_or_non_unique_bilateral_excerpt",
        ],
    }
    return items, report
