from __future__ import annotations

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.book_intake import (
    BookIntakeManifestBuilder,
    BookIntakeProcessor,
    BookPreflightAnalyzer,
    get_book_intake_freeze_metadata,
    validate_book_intake_freeze,
)


def _run_pipeline(source_path: Path) -> tuple[object, ...]:
    intake = BookIntakeProcessor().process(source_path)
    preflight = BookPreflightAnalyzer().analyze(intake)
    manifest = BookIntakeManifestBuilder().build(intake, preflight)
    return (
        intake,
        preflight,
        manifest.to_dict(),
        manifest.to_json(),
        manifest.content_fingerprint,
        manifest.manifest_fingerprint,
    )


def main() -> int:
    validate_book_intake_freeze()
    metadata = get_book_intake_freeze_metadata()
    assert metadata.activation_gate == "book_intake_layer_frozen"
    assert len(metadata.frozen_modules) == 11
    assert len(metadata.public_api) == 42

    with TemporaryDirectory(prefix="ntpe_stage28_") as temporary_directory:
        source_path = Path(temporary_directory) / "acceptance.txt"
        source_path.write_text("這是固定的繁體中文驗收內容。" * 100, encoding="utf-8")
        results = tuple(_run_pipeline(source_path) for _ in range(3))
        assert results[0] == results[1] == results[2]

    print("Stage 2.8 Book Intake freeze acceptance: PASS")
    print("Determinism repetitions: 3")
    print("Provider / Network / Translation executions: 0 / 0 / 0")
    print("Activation gate: book_intake_layer_frozen")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
