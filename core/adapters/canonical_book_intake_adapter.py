from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.book_intake import BookIntakeProcessor, BookIntakeResult
from core.book_intake.models import BookIntakeResult as _BookIntakeResult


@dataclass(frozen=True)
class SourceIdentity:
    source_path: Path
    source_hash: str
    file_size: int
    modified_time: float


@dataclass(frozen=True)
class CanonicalIntakeRequest:
    source_path: Path
    source_identity: SourceIdentity


@dataclass(frozen=True)
class CanonicalIntakeResult:
    intake_result: BookIntakeResult
    source_identity: SourceIdentity
    status: str
    warnings: tuple[str, ...]
    submission_eligible: bool


class CanonicalBookIntakeAdapter:
    def __init__(self, processor: BookIntakeProcessor | None = None):
        self.processor = processor or BookIntakeProcessor()

    def process(self, request: CanonicalIntakeRequest) -> CanonicalIntakeResult:
        intake_result = self.processor.process(request.source_path)

        status = intake_result.status
        warnings: list[str] = []

        if intake_result.quality_report.status == "warning":
            warnings.append("Text quality warnings detected during intake")
        if intake_result.language_result.language in ("unknown", "mixed"):
            warnings.append(f"Language detection uncertain: {intake_result.language_result.language}")

        submission_eligible = status in ("ready", "ready_with_warnings")

        return CanonicalIntakeResult(
            intake_result=intake_result,
            source_identity=request.source_identity,
            status=status,
            warnings=tuple(warnings),
            submission_eligible=submission_eligible,
        )

    def process_path(self, source_path: Path) -> CanonicalIntakeResult:
        import hashlib
        stat = source_path.stat()
        content = source_path.read_bytes()
        source_hash = hashlib.sha256(content).hexdigest()[:16]
        source_identity = SourceIdentity(
            source_path=source_path,
            source_hash=source_hash,
            file_size=stat.st_size,
            modified_time=stat.st_mtime,
        )
        return self.process(CanonicalIntakeRequest(source_path=source_path, source_identity=source_identity))