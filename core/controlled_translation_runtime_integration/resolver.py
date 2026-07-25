"""Resolve one authenticated Stage 7.2 work reference to one local fixture."""

from dataclasses import dataclass
from pathlib import Path

from core.book_intake import BookIntakeProcessor
from core.controlled_runtime_scheduling_dispatch import ControlledRuntimeDispatchPackage
from lts.txt_translation_runtime import split_text

from .errors import (
    ControlledTranslationMultipleChunkError, ControlledTranslationResolutionError,
    ControlledTranslationSourceIntegrityError,
)
from .policy import (
    CHUNK_SIZE, SOURCE_CHARACTER_COUNT, SOURCE_FIXTURE_FINGERPRINT,
    SOURCE_FIXTURE_ID, SOURCE_FIXTURE_PATH,
)
from .serialization import canonical_sha256


@dataclass(frozen=True)
class _ResolvedWorkPackage:
    source_fixture_id: str
    source_fingerprint: str
    source_text: str
    source_character_count: int
    chunk_count: int
    work_package_reference_fingerprint: str
    execution_plan_reference_fingerprint: str


class ControlledDispatchWorkPackageResolver:
    def resolve(self, dispatch_package, *, root) -> _ResolvedWorkPackage:
        if not isinstance(dispatch_package, ControlledRuntimeDispatchPackage):
            raise TypeError("dispatch_package must be authentic Stage 7.2 type")
        base = Path(root).resolve()
        expected = (base / SOURCE_FIXTURE_PATH).resolve()
        if base not in expected.parents or not expected.is_file():
            raise ControlledTranslationResolutionError("authorized source fixture unavailable")
        intake = BookIntakeProcessor().process(expected)
        if intake.status not in {"ready", "ready_with_warnings"}:
            raise ControlledTranslationSourceIntegrityError("source intake did not pass")
        text = intake.text
        fingerprint = canonical_sha256(text)
        if (
            fingerprint != SOURCE_FIXTURE_FINGERPRINT
            or len(text) != SOURCE_CHARACTER_COUNT
            or intake.language_result.language != "ko"
        ):
            raise ControlledTranslationSourceIntegrityError("source identity mismatch")
        chunks = split_text(text, CHUNK_SIZE)
        if len(chunks) != 1:
            raise ControlledTranslationMultipleChunkError("exactly one authentic chunk required")
        if not chunks[0].strip() or chunks[0].strip() != text.strip():
            raise ControlledTranslationSourceIntegrityError("chunker did not preserve source")
        return _ResolvedWorkPackage(
            source_fixture_id=SOURCE_FIXTURE_ID,
            source_fingerprint=fingerprint,
            source_text=text,
            source_character_count=len(text),
            chunk_count=1,
            work_package_reference_fingerprint=(
                dispatch_package.work_package_reference_fingerprint
            ),
            execution_plan_reference_fingerprint=(
                dispatch_package.execution_plan_reference_fingerprint
            ),
        )
