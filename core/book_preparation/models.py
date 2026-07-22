from __future__ import annotations

import re
from dataclasses import dataclass

from core.book_chunking import BookChunkPlan, TranslationChunk
from core.book_intake import (
    BookIntakeManifest,
    BookIntakeResult,
    BookPreflightResult,
)
from core.book_segmentation import BookSegmentationResult


PreparationValue = str | int | float | bool | None
_HEX_64 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class BookPreparationFinding:
    code: str
    severity: str
    message: str
    stage: str
    observed_value: PreparationValue = None


@dataclass(frozen=True)
class BookPreparationResult:
    schema_name: str
    schema_version: str
    strategy: str
    source_name: str
    intake_result: BookIntakeResult
    preflight_result: BookPreflightResult
    intake_manifest: BookIntakeManifest
    segmentation_result: BookSegmentationResult
    chunk_plan: BookChunkPlan
    source_content_fingerprint: str
    manifest_fingerprint: str
    segmentation_fingerprint: str
    chunk_plan_fingerprint: str
    status: str
    action: str
    findings: tuple[BookPreparationFinding, ...]
    summary: str
    preparation_fingerprint: str

    def __post_init__(self) -> None:
        if not isinstance(self.findings, tuple):
            raise TypeError("findings must be a tuple")
        for name, value in (
            ("source_content_fingerprint", self.source_content_fingerprint),
            ("manifest_fingerprint", self.manifest_fingerprint),
            ("segmentation_fingerprint", self.segmentation_fingerprint),
            ("chunk_plan_fingerprint", self.chunk_plan_fingerprint),
            ("preparation_fingerprint", self.preparation_fingerprint),
        ):
            if not _HEX_64.fullmatch(value):
                raise ValueError(f"{name} must be lowercase SHA-256 hex")

    def reconstruct_text(self) -> str:
        return self.chunk_plan.reconstruct_text()

    @property
    def translation_chunks(self) -> tuple[TranslationChunk, ...]:
        return self.chunk_plan.chunks

    @property
    def is_ready_for_translation(self) -> bool:
        return self.status == "ready"

    @property
    def requires_manual_review(self) -> bool:
        return self.status == "manual_review"

    @property
    def is_blocked(self) -> bool:
        return self.status == "blocked"
