from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
STAGE11 = (
    "core/translation_quality_defects",
    "core/translation_quality_metrics",
    "core/translation_quality_review_artifacts",
    "core/translation_prompt_improvement_planner",
    "core/translation_quality_review_decision",
    "core/translation_quality_corpus",
    "core/translation_quality_corpus_governance",
    "core/translation_quality_framework_integration",
)


def _digest() -> str:
    digest = hashlib.sha256()
    files = [path for relative in STAGE11 for path in (ROOT / relative).rglob("*.py")]
    for path in sorted(files, key=lambda item: item.relative_to(ROOT).as_posix()):
        digest.update(path.relative_to(ROOT).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def test_public_and_legacy_import_paths_coexist() -> None:
    from ntpe.corpus import manage
    from ntpe.quality import assess, build_review_view
    from core.translation_quality_defects import TranslationDefect
    from core.translation_quality_framework_integration import QualityFrameworkIntegration

    assert callable(assess) and callable(build_review_view) and callable(manage)
    assert TranslationDefect.__module__.startswith("core.translation_quality_defects")
    assert QualityFrameworkIntegration.__module__.startswith("core.translation_quality_framework_integration")


def test_frozen_stage11_modules_are_unchanged() -> None:
    assert _digest() == "22beb3a54e3ef07e2d86d14d14e9d8115aca4f27db98c3ed19dea4ec8a9764b1"


def test_public_exports_do_not_leak_stage_specific_names() -> None:
    import ntpe.corpus
    import ntpe.quality

    names = tuple(ntpe.quality.__all__) + tuple(ntpe.corpus.__all__)
    assert not any("stage11" in name.lower() or "stage_11" in name.lower() for name in names)


def test_frozen_artifact_and_schema_files_remain_byte_identical() -> None:
    assert hashlib.sha256((ROOT / "archive/historical/quality_corpus/golden_review/te_v71_initial_defects.json").read_bytes()).hexdigest() == "4a06d256d900c8bb7706098fd79f2d53889d469e9b62516d81334ef34433f2cc"

