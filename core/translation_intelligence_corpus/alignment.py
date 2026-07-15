from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .evidence_linker import link_all_evidence, sha256_file, sha256_text
from .segmentation import segment_text

BATCH1_INPUTS = (
    "artifacts/tic_batch1/TRANSLATION_CORPUS_INVENTORY.json",
    "artifacts/tic_batch1/TRANSLATION_CORPUS_STATISTICS.json",
)
BATCH2_INPUTS = (
    "artifacts/tic_batch2/TRANSLATION_CASES.json",
    "artifacts/tic_batch2/TRANSLATION_CASE_INDEX.json",
    "artifacts/tic_batch2/TRANSLATION_CASE_STATISTICS.json",
)
ARTIFACT_DIR = Path("artifacts/tic_batch3")
EVIDENCE_SOURCE = ARTIFACT_DIR / "KNOWN_SUBJECT_SHIFT_HUMAN_REVIEW.json"
INVENTORY = ARTIFACT_DIR / "MANUAL_EVIDENCE_INVENTORY.json"
LINKS = ARTIFACT_DIR / "MANUAL_EVIDENCE_LINKS.json"
UNITS = ARTIFACT_DIR / "TRANSLATION_ALIGNMENT_UNITS.json"
STATISTICS = ARTIFACT_DIR / "TRANSLATION_ALIGNMENT_STATISTICS.json"
INDEX = ARTIFACT_DIR / "TRANSLATION_ALIGNMENT_INDEX.json"
ARTIFACT_MANIFEST = ARTIFACT_DIR / "TRANSLATION_ALIGNMENT_MANIFEST.json"
ROOT_MANIFEST = Path("manifests/tic_batch3_manual_evidence_alignment_manifest.json")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON object required: {path}")
    return payload


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def _evidence_id(path: str, suffix: str = "") -> str:
    return "TIC-EVID-B3-" + hashlib.sha256(f"{path}|{suffix}".encode("utf-8")).hexdigest()[:20].upper()


def build_evidence_inventory(root: Path, cases: list[dict[str, Any]]) -> dict[str, Any]:
    known = next(case for case in cases if case["translation_file"] == "artifacts/te_v72_stage1223/baseline/translation.txt")
    stage10101 = next(case for case in cases if case["translation_file"] == "artifacts/te_v7_stage10101/review/TE_V7_STAGE10101_TRANSLATION_REVIEW.txt")
    known_review = _load(root / EVIDENCE_SOURCE)
    sources = [
        {
            "evidence_id": _evidence_id("artifacts/te_v71_stage111/TE_V71_STAGE111_TRANSLATION_DEFECTS.json"),
            "evidence_type": "human_confirmed_defect_collection",
            "evidence_path": "artifacts/te_v71_stage111/TE_V71_STAGE111_TRANSLATION_DEFECTS.json",
            "review_source": "TE-v7.1-Stage11.1 from Stage10.10.1 human review",
            "reviewer_type": "human",
            "human_provenance": {"complete": True, "origin": "human_review_stage10101", "reviewer_id": "human-reviewer-001"},
            "created_at": "2026-07-14T00:00:00+08:00",
            "referenced_translation_path": stage10101["translation_file"],
            "referenced_source_path": stage10101["source_file"],
            "referenced_case_ids": [stage10101["case_id"]],
            "review_status": "human_reviewed",
            "quality_judgement": "human_confirmed_failure",
            "defect_categories": ["lexical_choice", "omission", "semantic_mistranslation", "semantic_precision", "narrative_naturalness", "traditional_chinese_style"],
            "excerpts": {"source": None, "translation": "相當理性的人間"},
            "notes": "Human-confirmed defects; suggested revisions remain suggestions only.",
            "usable_for_failure_corpus": True,
            "usable_for_excellence_corpus": False,
        },
        {
            "evidence_id": _evidence_id("artifacts/te_v71_stage112/TE_V71_STAGE112_QUALITY_METRICS.json"),
            "evidence_type": "automatic_quality_metrics",
            "evidence_path": "artifacts/te_v71_stage112/TE_V71_STAGE112_QUALITY_METRICS.json",
            "review_source": "TE-v7.1-Stage11.2 automatic metrics",
            "reviewer_type": "automatic",
            "human_provenance": {"complete": False, "origin": None, "reviewer_id": None},
            "created_at": "2026-07-14T00:00:00+08:00",
            "referenced_translation_path": None,
            "referenced_source_path": None,
            "referenced_case_ids": [],
            "review_status": "unreviewed",
            "quality_judgement": "insufficient_evidence",
            "defect_categories": [],
            "excerpts": {"source": None, "translation": None},
            "notes": "Metrics are inventoried but cannot establish failure or excellence.",
            "usable_for_failure_corpus": False,
            "usable_for_excellence_corpus": False,
        },
        {
            "evidence_id": _evidence_id("artifacts/te_v72_stage1223/TE_V72_STAGE1223_MANUAL_AB_REVIEW.json"),
            "evidence_type": "incomplete_manual_review_template",
            "evidence_path": "artifacts/te_v72_stage1223/TE_V72_STAGE1223_MANUAL_AB_REVIEW.json",
            "review_source": "TE-v7.2-Stage12.2.3 incomplete A/B review",
            "reviewer_type": "unknown",
            "human_provenance": {"complete": False, "origin": None, "reviewer_id": None},
            "created_at": "2026-07-14T00:00:00+08:00",
            "referenced_translation_path": known["translation_file"],
            "referenced_source_path": known["source_file"],
            "referenced_case_ids": [known["case_id"]],
            "review_status": "unreviewed",
            "quality_judgement": "insufficient_evidence",
            "defect_categories": [],
            "excerpts": {"source": None, "translation": None},
            "notes": "Review was not completed and cannot establish a quality label.",
            "usable_for_failure_corpus": False,
            "usable_for_excellence_corpus": False,
        },
        {
            "evidence_id": known_review["evidence_id"],
            "evidence_type": "user_human_review_directive",
            "evidence_path": EVIDENCE_SOURCE.as_posix(),
            "review_source": known_review["review_source"],
            "reviewer_type": "human",
            "human_provenance": known_review["human_provenance"],
            "created_at": known_review["created_at"],
            "referenced_translation_path": known["translation_file"],
            "referenced_source_path": known["source_file"],
            "referenced_case_ids": [known["case_id"]],
            "review_status": "human_reviewed",
            "quality_judgement": "human_confirmed_failure",
            "defect_categories": ["subject_reference_shift"],
            "excerpts": known_review["excerpts"],
            "notes": "No revised translation is approved or generated.",
            "usable_for_failure_corpus": True,
            "usable_for_excellence_corpus": False,
        },
    ]
    for item in sources:
        item["evidence_sha256"] = sha256_file(root / item["evidence_path"])
    return {"schema_version": "tic.batch3.manual-evidence-inventory.v1", "items": sources}


def _group(segments: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    groups: list[list[dict[str, Any]]] = []
    for segment in segments:
        paragraph = int(segment["paragraph_index"])
        while len(groups) <= paragraph:
            groups.append([])
        groups[paragraph].append(segment)
    return groups


def _unit(case_id: str, source: list[dict[str, Any]], translation: list[dict[str, Any]], method: str, confidence: str) -> dict[str, Any]:
    if source and translation:
        if len(source) == len(translation) == 1:
            kind = "one_to_one"
        elif len(source) == 1:
            kind = "one_to_many"
        elif len(translation) == 1:
            kind = "many_to_one"
        else:
            kind = "many_to_many"
    elif source:
        kind = "source_only"
    elif translation:
        kind = "translation_only"
    else:
        kind = "unresolved"
    source_text = "".join(str(item["text"]) for item in source)
    translation_text = "".join(str(item["text"]) for item in translation)
    identity = f"{case_id}|{'/'.join(str(x['segment_id']) for x in source)}|{'/'.join(str(x['segment_id']) for x in translation)}"
    return {
        "alignment_id": "TIC-ALIGN-B3-" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20].upper(),
        "case_id": case_id,
        "source_segment_ids": [item["segment_id"] for item in source],
        "translation_segment_ids": [item["segment_id"] for item in translation],
        "source_text": source_text,
        "translation_text": translation_text,
        "source_start_offset": source[0]["start_offset"] if source else None,
        "source_end_offset": source[-1]["end_offset"] if source else None,
        "translation_start_offset": translation[0]["start_offset"] if translation else None,
        "translation_end_offset": translation[-1]["end_offset"] if translation else None,
        "alignment_type": kind,
        "alignment_method": method if kind not in {"source_only", "translation_only", "unresolved"} else "unresolved",
        "alignment_confidence": confidence if kind not in {"source_only", "translation_only", "unresolved"} else "low",
        "source_sha256": sha256_text(source_text),
        "translation_sha256": sha256_text(translation_text),
        "manual_evidence_ids": [],
        "review_status": "unreviewed",
        "quality_label": "unreviewed",
        "failure_category": None,
        "evidence_overlay": False,
        "coverage_eligible": True,
        "anchor_source_overlap": None,
        "anchor_translation_overlap": None,
    }


def align_segments(case_id: str, source: list[dict[str, Any]], translation: list[dict[str, Any]]) -> list[dict[str, Any]]:
    source_groups, translation_groups = _group(source), _group(translation)
    units: list[dict[str, Any]] = []
    for index in range(max(len(source_groups), len(translation_groups))):
        left = source_groups[index] if index < len(source_groups) else []
        right = translation_groups[index] if index < len(translation_groups) else []
        if len(left) == len(right) and left:
            units.extend(_unit(case_id, [s], [t], "sentence_group_order", "high") for s, t in zip(left, right))
        else:
            units.append(_unit(case_id, left, right, "paragraph_order", "medium"))
    return units or [_unit(case_id, [], [], "unresolved", "low")]


def _segments_covering(
    segments: list[dict[str, Any]], case_id: str, start: int, end: int
) -> list[dict[str, Any]]:
    selected = [
        segment
        for segment in segments
        if segment["case_id"] == case_id
        and int(segment["end_offset"]) > start
        and int(segment["start_offset"]) < end
    ]
    if not selected:
        return []
    selected.sort(key=lambda segment: int(segment["segment_index"]))
    if int(selected[0]["start_offset"]) > start or int(selected[-1]["end_offset"]) < end:
        return []
    if any(
        int(left["end_offset"]) != int(right["start_offset"])
        for left, right in zip(selected, selected[1:])
    ):
        return []
    return selected


def _unit_fully_covers(
    unit: dict[str, Any],
    source_excerpt: str,
    translation_excerpt: str,
    source_start: int,
    translation_start: int,
) -> bool:
    if not unit["source_text"] or not unit["translation_text"]:
        return False
    if unit["alignment_type"] in {"source_only", "translation_only", "unresolved"}:
        return False
    source_end = source_start + len(source_excerpt)
    translation_end = translation_start + len(translation_excerpt)
    return bool(
        unit["source_start_offset"] is not None
        and unit["translation_start_offset"] is not None
        and int(unit["source_start_offset"]) <= source_start
        and int(unit["source_end_offset"]) >= source_end
        and int(unit["translation_start_offset"]) <= translation_start
        and int(unit["translation_end_offset"]) >= translation_end
        and source_excerpt in unit["source_text"]
        and translation_excerpt in unit["translation_text"]
    )


def _mark_failure(unit: dict[str, Any], evidence: dict[str, Any]) -> None:
    evidence_id = evidence["evidence_id"]
    if evidence_id not in unit["manual_evidence_ids"]:
        unit["manual_evidence_ids"].append(evidence_id)
    unit["review_status"] = "human_reviewed"
    unit["quality_label"] = "human_confirmed_failure"
    unit["failure_category"] = evidence["defect_categories"][0]
    unit["anchor_source_overlap"] = 1.0
    unit["anchor_translation_overlap"] = 1.0


def _apply_evidence(
    units: list[dict[str, Any]],
    inventory: dict[str, Any],
    links: list[dict[str, Any]],
    source_segments: list[dict[str, Any]],
    translation_segments: list[dict[str, Any]],
) -> None:
    items = {item["evidence_id"]: item for item in inventory["items"]}
    for link in links:
        link["precise_alignment_status"] = "not_applicable"
        link["precise_alignment_unit_ids"] = []
        if not link["case_id"]:
            continue
        evidence = items[link["evidence_id"]]
        source_excerpt = evidence["excerpts"].get("source")
        translation_excerpt = evidence["excerpts"].get("translation")
        is_confirmed_failure = bool(
            link["human_confirmed"]
            and link["link_confidence"] in {"exact", "high"}
            and evidence["quality_judgement"] == "human_confirmed_failure"
        )
        if not is_confirmed_failure:
            continue
        link["precise_alignment_status"] = "linked_but_not_aligned"
        if (
            not source_excerpt
            or not translation_excerpt
            or link["case_source_offset"] is None
            or link["case_translation_offset"] is None
        ):
            continue
        source_start = int(link["case_source_offset"])
        translation_start = int(link["case_translation_offset"])
        candidates = [
            unit
            for unit in units
            if unit["case_id"] == link["case_id"]
            and not unit.get("evidence_overlay", False)
            and _unit_fully_covers(
                unit,
                source_excerpt,
                translation_excerpt,
                source_start,
                translation_start,
            )
        ]
        if len(candidates) == 1:
            target = candidates[0]
        elif candidates:
            continue
        else:
            source = _segments_covering(
                source_segments,
                link["case_id"],
                source_start,
                source_start + len(source_excerpt),
            )
            translation = _segments_covering(
                translation_segments,
                link["case_id"],
                translation_start,
                translation_start + len(translation_excerpt),
            )
            if not source or not translation:
                continue
            target = _unit(
                link["case_id"], source, translation, "manual_evidence_anchor", "high"
            )
            target["alignment_id"] = "TIC-ALIGN-B3-" + hashlib.sha256(
                f"{link['case_id']}|{link['evidence_id']}|manual_evidence_anchor".encode("utf-8")
            ).hexdigest()[:20].upper()
            target["evidence_overlay"] = True
            target["coverage_eligible"] = False
            if not _unit_fully_covers(
                target,
                source_excerpt,
                translation_excerpt,
                source_start,
                translation_start,
            ):
                continue
            units.append(target)
        _mark_failure(target, evidence)
        link["precise_alignment_status"] = "aligned"
        link["precise_alignment_unit_ids"] = [target["alignment_id"]]


def generate_batch3_artifacts(root: str | Path) -> dict[str, Path]:
    base = Path(root).resolve()
    cases_payload = _load(base / BATCH2_INPUTS[0])
    cases = cases_payload["translation_cases"]
    inventory = build_evidence_inventory(base, cases)
    links_list = link_all_evidence(inventory["items"], cases)
    source_segments: list[dict[str, Any]] = []
    translation_segments: list[dict[str, Any]] = []
    units: list[dict[str, Any]] = []
    for case in cases:
        source = segment_text(case["source_text"], case_id=case["case_id"], language="ko")
        translation = segment_text(case["translation_text"], case_id=case["case_id"], language="zh-Hant")
        source_segments.extend(source)
        translation_segments.extend(translation)
        units.extend(align_segments(case["case_id"], source, translation))
    _apply_evidence(
        units, inventory, links_list, source_segments, translation_segments
    )
    links = {"schema_version": "tic.batch3.manual-evidence-links.v1", "items": links_list}
    unit_payload = {"schema_version": "tic.batch3.translation-alignment-units.v1", "source_segments": source_segments, "translation_segments": translation_segments, "alignment_units": units}
    coverage_units = [unit for unit in units if unit.get("coverage_eligible", True)]
    align_counts = Counter(unit["alignment_type"] for unit in coverage_units)
    confidence_counts = Counter(unit["alignment_confidence"] for unit in coverage_units)
    quality_counts = Counter(unit["quality_label"] for unit in units)
    covered = sum(1 for unit in coverage_units if unit["alignment_type"] not in {"source_only", "translation_only", "unresolved"})
    confirmed_failure_links = [
        link
        for link in links_list
        if link["human_confirmed"]
        and link["link_confidence"] in {"exact", "high"}
        and next(item for item in inventory["items"] if item["evidence_id"] == link["evidence_id"])["quality_judgement"] == "human_confirmed_failure"
    ]
    stats = {
        "schema_version": "tic.batch3.translation-alignment-statistics.v1",
        "total_cases_processed": len(cases), "total_source_segments": len(source_segments), "total_translation_segments": len(translation_segments), "total_alignment_units": len(units),
        **{f"{name}_count": align_counts[name] for name in ("one_to_one", "one_to_many", "many_to_one", "many_to_many", "source_only", "translation_only", "unresolved")},
        "coverage_eligible_alignment_units": len(coverage_units),
        "evidence_overlay_count": len(units) - len(coverage_units),
        "alignment_coverage": covered / len(coverage_units) if coverage_units else 0.0,
        "coverage_definition": "coverage-eligible alignment units with both source and translation divided by all coverage-eligible units, including unresolved/source-only/translation-only units; evidence overlays are explicitly excluded",
        "high_confidence_alignment_count": confidence_counts["high"], "medium_confidence_alignment_count": confidence_counts["medium"], "low_confidence_alignment_count": confidence_counts["low"],
        "manual_evidence_count": len(inventory["items"]), "human_evidence_count": sum(x["reviewer_type"] == "human" for x in inventory["items"]), "automatic_evidence_count": sum(x["reviewer_type"] == "automatic" for x in inventory["items"]), "unknown_evidence_count": sum(x["reviewer_type"] == "unknown" for x in inventory["items"]),
        "linked_evidence_count": sum(x["case_id"] is not None for x in links_list), "unlinked_evidence_count": sum(x["case_id"] is None for x in links_list),
        "human_confirmed_failure_units": quality_counts["human_confirmed_failure"], "human_confirmed_failure_evidence_count": len(confirmed_failure_links), "human_confirmed_failure_unit_count": quality_counts["human_confirmed_failure"], "evidence_without_precise_alignment_count": sum(link["precise_alignment_status"] != "aligned" for link in confirmed_failure_links), "human_confirmed_excellence_units": quality_counts["human_confirmed_excellence"], "human_reviewed_neutral_units": quality_counts["human_reviewed_neutral"], "unreviewed_units": quality_counts["unreviewed"], "insufficient_evidence_units": quality_counts["insufficient_evidence"],
    }
    case_map = {case["case_id"]: case for case in cases}
    index_items = []
    for unit in units:
        case = case_map[unit["case_id"]]
        index_items.append({
            "alignment_id": unit["alignment_id"], "case_id": unit["case_id"], "corpus_id": case["corpus_id"], "source_file": case["source_file"], "translation_file": case["translation_file"], "stage": case["stage"], "version": case["version"], "provider": case["provider"], "model": case["model"],
            "segment_type": sorted(set([next(x["segment_type"] for x in source_segments if x["segment_id"] == sid) for sid in unit["source_segment_ids"]] + [next(x["segment_type"] for x in translation_segments if x["segment_id"] == sid) for sid in unit["translation_segment_ids"]])),
            "alignment_type": unit["alignment_type"], "alignment_confidence": unit["alignment_confidence"], "review_status": unit["review_status"], "quality_label": unit["quality_label"], "failure_category": unit["failure_category"], "manual_evidence_id": unit["manual_evidence_ids"],
        })
    index_payload = {"schema_version": "tic.batch3.translation-alignment-index.v1", "items": index_items}
    outputs = {INVENTORY: inventory, LINKS: links, UNITS: unit_payload, STATISTICS: stats, INDEX: index_payload}
    for path, payload in outputs.items():
        _write(base / path, payload)
    return {path.as_posix(): base / path for path in outputs}


def generate_manifests(root: str | Path) -> tuple[Path, Path]:
    base = Path(root).resolve()
    release_files = [
        "core/translation_intelligence_corpus/segmentation.py", "core/translation_intelligence_corpus/evidence_linker.py", "core/translation_intelligence_corpus/alignment.py",
        EVIDENCE_SOURCE.as_posix(), INVENTORY.as_posix(), LINKS.as_posix(), UNITS.as_posix(), STATISTICS.as_posix(), INDEX.as_posix(),
        "docs/translation_intelligence/TIC_BATCH3_MANUAL_EVIDENCE_AND_ALIGNMENT.md", "ntpe_tic_batch3_manual_evidence_alignment_test.py", "tests/integration/tic_batch3_manual_evidence_alignment_test.py",
    ]
    anchors = {name: sha256_file(base / name) for name in (*BATCH1_INPUTS, *BATCH2_INPUTS)}
    artifact_payload = {"schema_version": "tic.batch3.translation-alignment-manifest.v1", "batch": "TIC Batch 3", "status": "completed", "input_anchors": anchors, "files": {name: sha256_file(base / name) for name in release_files}, "sha256": {"algorithm": "sha256", "self_hash_excluded": True}}
    _write(base / ARTIFACT_MANIFEST, artifact_payload)
    root_files = [*release_files, ARTIFACT_MANIFEST.as_posix()]
    boundary = {"provider_executed": False, "network_requests": 0, "new_translation_generated": False, "historical_translation_modified": False, "runtime_modified": False, "provider_modified": False, "prompt_modified": False, "stage11_modified": False, "stage12_modified": False, "golden_corpus_modified": False, "batch1_inventory_rebuilt": False, "batch2_cases_rebuilt": False, "manual_evidence_inventory_created": True, "fine_grained_segments_created": True, "alignment_units_created": True, "failure_corpus_created": False, "excellence_corpus_created": False, "root_cause_analysis_executed": False, "tic_batch4_started": False}
    root_payload = {"schema_version": "tic.batch3.release-manifest.v1", "batch": "TIC Batch 3 - Manual Evidence Linking and Fine-Grained Alignment", "status": "TIC Batch 3 Completed", "next_batch_status": "TIC Batch 4 Not Started", "input_anchors": anchors, "files": {name: sha256_file(base / name) for name in root_files}, "tests": {"root": "ntpe_tic_batch3_manual_evidence_alignment_test.py", "focused_integration": "tests/integration/tic_batch3_manual_evidence_alignment_test.py"}, "boundaries": boundary, "sha256": {"algorithm": "sha256", "self_hash_excluded": True}}
    _write(base / ROOT_MANIFEST, root_payload)
    return base / ARTIFACT_MANIFEST, base / ROOT_MANIFEST


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic TIC Batch 3 alignment artifacts")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--manifests", action="store_true")
    args = parser.parse_args()
    generate_batch3_artifacts(args.root)
    if args.manifests:
        generate_manifests(args.root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
