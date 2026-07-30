import json
from pathlib import Path

from core.translation_quality_v5 import (
    QualityRepairPlanner,
    QualityRetryOrchestrator,
    QualityChunkRebuildPlanner,
    QualityRepairPipeline,
)


def check(name, condition):
    print(f"{name:<54} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def main():
    print("NTPE TE-v5.1 Stage-5.1.6 Quality Repair Pipeline Freeze Test")
    print("=" * 90)

    root = Path(__file__).resolve().parent
    path = root / "manifests" / "te_v51_quality_repair_pipeline_freeze_manifest.json"
    check("Freeze Manifest Exists", path.exists())
    manifest = json.loads(path.read_text(encoding="utf-8"))
    check("Freeze Enabled", manifest["frozen"] is True)
    check("Version Correct", manifest["version"] == "TE-v5.1")
    check("Stages Complete", manifest["stages"] == [
        "5.1.1", "5.1.2", "5.1.3", "5.1.4", "5.1.5"
    ])
    check("Repair Planner Import", QualityRepairPlanner is not None)
    check("Retry Orchestrator Import", QualityRetryOrchestrator is not None)
    check("Chunk Rebuild Import", QualityChunkRebuildPlanner is not None)
    check("Repair Pipeline Import", QualityRepairPipeline is not None)
    check("Runtime Unchanged", manifest["translation_runtime_modified"] is False)
    check("Provider Unchanged", manifest["provider_runtime_modified"] is False)
    check("Launcher Unchanged", manifest["launcher_modified"] is False)

    print("NTPE TE-v5.1 Stage-5.1.6 Quality Repair Pipeline Freeze PASS")


if __name__ == "__main__":
    main()
