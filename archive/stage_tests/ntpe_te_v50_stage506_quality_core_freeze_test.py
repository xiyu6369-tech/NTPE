import json
from pathlib import Path

from core.translation_quality_v5 import (
    TranslationQualityBaseline,
    CompletenessGuard,
    TerminologyConsistencyGuard,
    TraditionalChineseNormalizer,
    TranslationQualityCorePipeline,
)


def check(name, condition):
    print(f"{name:<52} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def main():
    print("NTPE TE-v5.0 Stage-5.0.6 Quality Core Freeze Test")
    print("=" * 86)

    root = Path(__file__).resolve().parent
    manifest_path = root / "manifests" / "te_v50_quality_core_freeze_manifest.json"
    check("Freeze Manifest Exists", manifest_path.exists())
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    check("Freeze Enabled", manifest["frozen"] is True)
    check("Version Correct", manifest["version"] == "TE-v5.0")
    check("Stages Complete", manifest["stages"] == [
        "5.0.1", "5.0.2", "5.0.3", "5.0.4", "5.0.5"
    ])
    check("Baseline Import", TranslationQualityBaseline is not None)
    check("Completeness Import", CompletenessGuard is not None)
    check("Terminology Import", TerminologyConsistencyGuard is not None)
    check("Normalizer Import", TraditionalChineseNormalizer is not None)
    check("Pipeline Import", TranslationQualityCorePipeline is not None)
    check("Runtime Unchanged", manifest["translation_runtime_modified"] is False)
    check("Provider Unchanged", manifest["provider_runtime_modified"] is False)
    check("Launcher Unchanged", manifest["launcher_modified"] is False)

    print("NTPE TE-v5.0 Stage-5.0.6 Quality Core Freeze PASS")


if __name__ == "__main__":
    main()
