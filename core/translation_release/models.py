from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class TOCEntry:
    chapter_id: str
    chapter_title: str
    scene_count: int
    start_chunk_index: int
    end_chunk_index: int
    scene_ids: list[str]
    word_count_estimate: int


@dataclass(frozen=True)
class DeliveryManifest:
    """Delivery package manifest — extends translation manifest with delivery metadata."""
    # Core identification
    novel_id: str
    generated_at: str
    pipeline_version: str

    # Source & translation config
    input_path: str
    output_path: str
    chunk_total: int
    chunk_size: int
    model: str
    speed: str
    quality_profile: str

    # RM-8.1 Literary Quality Aggregate
    literary_quality: dict

    # RM-8.2 Cross-Chunk Context Aggregate
    context_continuity: dict

    # Delivery QC Results
    qc_result: dict

    # Output artifacts
    artifacts: dict

    # TOC (from RM-8.2 metadata)
    table_of_contents: list[dict]

    def to_dict(self) -> dict:
        return {
            "novel_id": self.novel_id,
            "generated_at": self.generated_at,
            "pipeline_version": self.pipeline_version,
            "input_path": self.input_path,
            "output_path": self.output_path,
            "chunk_total": self.chunk_total,
            "chunk_size": self.chunk_size,
            "model": self.model,
            "speed": self.speed,
            "quality_profile": self.quality_profile,
            "literary_quality": dict(self.literary_quality),
            "context_continuity": dict(self.context_continuity),
            "qc_result": dict(self.qc_result),
            "artifacts": dict(self.artifacts),
            "table_of_contents": [dict(entry) for entry in self.table_of_contents],
        }


@dataclass(frozen=True)
class QualityCertificate:
    """Quality certificate for delivery — human-readable + machine-parseable."""
    novel_id: str
    issued_at: str
    pipeline_version: str

    # Overall verdict
    overall_status: str
    overall_score: float

    # Dimension scores
    literary_quality_score: float
    format_consistency_score: float
    term_lock_compliance_score: float
    completeness_score: float
    context_continuity_score: float

    # Detailed checks
    checks: dict

    # RM-8.1 traceability
    literary_quality_aggregate: dict

    # RM-8.2 traceability
    context_continuity_aggregate: dict

    def to_dict(self) -> dict:
        return {
            "novel_id": self.novel_id,
            "issued_at": self.issued_at,
            "pipeline_version": self.pipeline_version,
            "overall_status": self.overall_status,
            "overall_score": self.overall_score,
            "literary_quality_score": self.literary_quality_score,
            "format_consistency_score": self.format_consistency_score,
            "term_lock_compliance_score": self.term_lock_compliance_score,
            "completeness_score": self.completeness_score,
            "context_continuity_score": self.context_continuity_score,
            "checks": {k: dict(v) for k, v in self.checks.items()},
            "literary_quality_aggregate": dict(self.literary_quality_aggregate),
            "context_continuity_aggregate": dict(self.context_continuity_aggregate),
        }


@dataclass(frozen=True)
class DeliveryResult:
    """Return value from delivery pipeline — fully immutable, constructed once."""
    status: str
    output_path: str
    manifest_path: str
    qc_certificate_path: str
    epub_path: Optional[str] = None
    pdf_path: Optional[str] = None
    error: Optional[str] = None