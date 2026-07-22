from __future__ import annotations

import hashlib
import re
import sys
import tempfile
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from core.book_chunking import BookChunkPlanner
from core.book_intake import (
    BookIntakeManifestBuilder,
    BookIntakeProcessor,
    BookPreflightAnalyzer,
)
from core.book_preparation import (
    BookPreparationProcessor,
    get_book_preparation_freeze_metadata,
    validate_book_preparation_freeze,
)
from core.book_segmentation import BookStructureSegmenter


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    metadata = get_book_preparation_freeze_metadata()
    _require(metadata.component_name == "ntpe.book_preparation_pipeline", "component")
    _require(metadata.freeze_version == "3.4", "freeze version")
    _require(metadata.schema_name == "ntpe.book_preparation", "schema name")
    _require(metadata.schema_version == "1.0", "schema version")
    _require(metadata.activation_gate == "book_preparation_pipeline_frozen", "gate")
    _require(len(metadata.frozen_modules) == 15, "source inventory")
    _require(len(metadata.public_api) == 31, "public API inventory")
    _require(len(metadata.public_api) == len(set(metadata.public_api)), "API uniqueness")
    _require(not metadata.provider_execution_authorized, "provider authorization")
    _require(not metadata.automatic_translation_authorized, "translation authorization")

    validation = validate_book_preparation_freeze()
    _require(validation.valid and validation.hash_drift_count == 0, "freeze validation")

    text = (
        "Book title\r\n\r\nChapter 1\r\n"
        + "Sentence one. Sentence two. " * 100
        + "\r\n\r\nChapter 2\r\n"
        + "Final sentence. " * 80
    )
    with tempfile.TemporaryDirectory(prefix="ntpe-stage34-") as temporary:
        source_path = Path(temporary) / "fixture.txt"
        source_path.write_bytes(text.encode("utf-8"))
        intake = BookIntakeProcessor().process(source_path)
        preflight = BookPreflightAnalyzer().analyze(intake)
        manifest = BookIntakeManifestBuilder().build(intake, preflight)
        segmentation = BookStructureSegmenter().segment(intake, manifest=manifest)
        chunk_plan = BookChunkPlanner().plan(segmentation)
        preparations = tuple(
            BookPreparationProcessor().prepare_intake(intake) for _ in range(3)
        )

    _require(segmentation.reconstruct_text() == text, "segmentation reconstruction")
    _require(chunk_plan.reconstruct_text() == text, "chunk reconstruction")
    _require(preparations[0] == preparations[1] == preparations[2], "determinism")
    preparation = preparations[0]
    _require(preparation.reconstruct_text() == text, "preparation reconstruction")
    expected_source_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    _require(preparation.source_content_fingerprint == expected_source_hash, "source hash")
    for fingerprint in (
        manifest.manifest_fingerprint,
        segmentation.segmentation_fingerprint,
        chunk_plan.chunk_plan_fingerprint,
        preparation.preparation_fingerprint,
    ):
        _require(bool(re.fullmatch(r"[0-9a-f]{64}", fingerprint)), "fingerprint")

    print("BOOK PREPARATION STAGE 3.4 FREEZE ACCEPTANCE: PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"BOOK PREPARATION STAGE 3.4 FREEZE ACCEPTANCE: FAIL: {exc}")
        raise SystemExit(1) from exc
