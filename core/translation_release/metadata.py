from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from lts.txt_translation_runtime import TxtTranslationOptions

from core.translation_release.models import DeliveryManifest, QualityCertificate, TOCEntry
from core.translation_release.validator import ValidationResult, ValidationCheck


def build_toc_from_chunk_records(
    chunk_records: list[dict],
    translated_chunks: list[str],
) -> list[TOCEntry]:
    """
    Build TOC from RM-8.2 context_state_metadata in chunk records.

    Each record.metadata.context_state contains:
    - scene_id, scene_version, chapter_id
    - boundary.type (scene_transition, chapter_transition, same_scene)

    Algorithm:
    1. Iterate records in order
    2. Detect chapter transitions (boundary.type == "chapter_transition" or new chapter_id)
    3. Group chunks by chapter_id
    4. Count scenes per chapter (unique scene_id)
    5. Estimate word count per chapter (sum of chunk lengths)
    6. **Chapter title**: ONLY from explicit marker in first chunk of chapter
       - Scan chunk text for patterns: `第N章`, `第 N 章`, `Chapter N`, `CHAPTER N`
       - If found: use as title (e.g., "第1章 初遇")
       - If NOT found: deterministic fallback "第N章" (no heuristic inference)
    """
    if not chunk_records or not translated_chunks:
        return []

    # Chapter pattern for explicit markers
    chapter_pattern = re.compile(r"(?:第\s*\d+\s*章|Chapter\s+\d+|CHAPTER\s+\d+)")

    chapters: dict[str, dict] = {}
    chapter_order: list[str] = []

    for idx, (record, chunk) in enumerate(zip(chunk_records, translated_chunks)):
        context_state = record.get("metadata", {}).get("context_state", {})
        chapter_id = context_state.get("chapter_id", f"chapter_{idx + 1}")
        scene_id = context_state.get("scene_id", f"scene_{idx + 1}")
        boundary_type = context_state.get("boundary", {}).get("type", "same_scene")

        if chapter_id not in chapters:
            chapters[chapter_id] = {
                "scene_ids": set(),
                "chunk_indices": [],
                "first_chunk_text": chunk,
                "total_chars": 0,
            }
            chapter_order.append(chapter_id)

        chapter_data = chapters[chapter_id]
        chapter_data["scene_ids"].add(scene_id)
        chapter_data["chunk_indices"].append(idx)
        chapter_data["total_chars"] += len(chunk.replace("\n", "").replace(" ", ""))

    toc_entries: list[TOCEntry] = []
    for chapter_num, chapter_id in enumerate(chapter_order, start=1):
        data = chapters[chapter_id]
        scene_ids = sorted(data["scene_ids"])
        scene_count = len(scene_ids)
        start_chunk = data["chunk_indices"][0] + 1
        end_chunk = data["chunk_indices"][-1] + 1
        word_count_estimate = data["total_chars"]

        # Extract chapter title from first chunk only
        first_chunk = data["first_chunk_text"]
        match = chapter_pattern.search(first_chunk)
        if match:
            chapter_title = match.group(0).replace(" ", "")
        else:
            chapter_title = f"第{chapter_num}章"

        toc_entries.append(TOCEntry(
            chapter_id=chapter_id,
            chapter_title=chapter_title,
            scene_count=scene_count,
            start_chunk_index=start_chunk,
            end_chunk_index=end_chunk,
            scene_ids=scene_ids,
            word_count_estimate=word_count_estimate,
        ))

    return toc_entries


def inject_metadata_into_text(
    text: str,
    *,
    title: str,
    author: str = "未知作者",
    translator: str = "NTPE Translation Engine",
    date: str,
    model: str,
    pipeline_version: str,
    toc: list[TOCEntry],
    quality_cert_summary: str,
) -> str:
    """
    Inject metadata as structured header + TOC at start of novel.

    Format:
    【書誌資訊】
    書名：{title}
    作者：{author}
    譯者：{translator}
    翻譯日期：{date}
    翻譯模型：{model}
    管線版本：{pipeline_version}
    品質狀態：{quality_cert_summary}

    【目錄】
    第1章 章節標題 .......... 3 場景 (Chunk 1-3)
    第2章 章節標題 .......... 2 場景 (Chunk 4-5)
    ...

    ───
    {original_novel_text}
    """
    lines = [
        "【書誌資訊】",
        f"書名：{title}",
        f"作者：{author}",
        f"譯者：{translator}",
        f"翻譯日期：{date}",
        f"翻譯模型：{model}",
        f"管線版本：{pipeline_version}",
        f"品質狀態：{quality_cert_summary}",
        "",
        "【目錄】",
    ]

    for entry in toc:
        dots = "." * max(1, 12 - len(entry.chapter_title))
        lines.append(
            f"{entry.chapter_title} {dots} {entry.scene_count} 場景 (Chunk {entry.start_chunk_index}-{entry.end_chunk_index})"
        )

    lines.extend(["", "───", "", text])

    return "\n".join(lines)


def generate_delivery_manifest(
    *,
    novel_id: str,
    input_path: str,
    output_path: str,
    chunk_records: list[dict],
    translated_chunks: list[str],
    locked_dictionary: dict,
    options: TxtTranslationOptions,
    literary_quality_aggregate: dict,
    qc_result: ValidationResult,
    toc: list[TOCEntry],
    artifact_paths: dict,
) -> DeliveryManifest:
    """Build complete DeliveryManifest from all pipeline data."""
    # Build context continuity aggregate from chunk records
    scene_ids = set()
    chapter_ids = set()
    scene_transitions = 0

    for record in chunk_records:
        context_state = record.get("metadata", {}).get("context_state", {})
        if context_state.get("scene_id"):
            scene_ids.add(context_state["scene_id"])
        if context_state.get("chapter_id"):
            chapter_ids.add(context_state["chapter_id"])
        if context_state.get("boundary", {}).get("type") == "scene_transition":
            scene_transitions += 1

    context_continuity = {
        "scene_count": len(scene_ids),
        "chapter_count": len(chapter_ids),
        "scene_transitions": scene_transitions,
    }

    # Build QC result dict
    qc_dict = {
        "status": "PASS" if qc_result.overall_passed else "FAIL",
        "score": qc_result.overall_score,
        "checks": {c.name: {"passed": c.passed, "score": c.score, "severity": c.severity} for c in qc_result.checks},
        "failed_critical": qc_result.failed_critical,
        "failed_major": qc_result.failed_major,
    }

    return DeliveryManifest(
        novel_id=novel_id,
        generated_at=datetime.now().isoformat(),
        pipeline_version="NTPE_RM83_v1",
        input_path=input_path,
        output_path=output_path,
        chunk_total=len(chunk_records),
        chunk_size=options.chunk_size,
        model=options.model,
        speed=options.speed,
        quality_profile=options.quality_profile,
        literary_quality=dict(literary_quality_aggregate),
        context_continuity=context_continuity,
        qc_result=qc_dict,
        artifacts=dict(artifact_paths),
        table_of_contents=[{
            "chapter_id": e.chapter_id,
            "title": e.chapter_title,
            "scene_count": e.scene_count,
            "start_chunk": e.start_chunk_index,
            "end_chunk": e.end_chunk_index,
        } for e in toc],
    )


def generate_quality_certificate(
    *,
    novel_id: str,
    qc_result: ValidationResult,
    literary_quality_aggregate: dict,
    context_continuity_aggregate: dict,
) -> QualityCertificate:
    """Build QualityCertificate from validation results."""
    # Map check names to dimension scores
    check_scores = {c.name: c.score for c in qc_result.checks}

    # Dimension score mapping
    literary_quality_score = check_scores.get("chinese_char_ratio", 100.0)
    format_consistency_score = min(
        check_scores.get("paragraph_structure", 100.0),
        check_scores.get("punctuation_consistency", 100.0),
        check_scores.get("quote_balance", 100.0),
    )
    term_lock_compliance_score = check_scores.get("locked_term_compliance", 100.0)
    completeness_score = check_scores.get("length_ratio_global", 100.0)
    context_continuity_score = check_scores.get("repeated_lines_global", 100.0)

    # Convert checks to dict
    checks_dict = {}
    for check in qc_result.checks:
        checks_dict[check.name] = {
            "passed": check.passed,
            "score": check.score,
            "severity": check.severity,
            "details": dict(check.details),
        }

    return QualityCertificate(
        novel_id=novel_id,
        issued_at=datetime.now().isoformat(),
        pipeline_version="NTPE_RM83_v1",
        overall_status="PASS" if qc_result.overall_passed else "FAIL",
        overall_score=qc_result.overall_score,
        literary_quality_score=literary_quality_score,
        format_consistency_score=format_consistency_score,
        term_lock_compliance_score=term_lock_compliance_score,
        completeness_score=completeness_score,
        context_continuity_score=context_continuity_score,
        checks=checks_dict,
        literary_quality_aggregate=dict(literary_quality_aggregate),
        context_continuity_aggregate=dict(context_continuity_aggregate),
    )