import json
from pathlib import Path

from core.translation_quality_v5 import (
    QualityRuntimeGateContract,
    QualityRuntimeGateAdmission,
    QualityRuntimeGateDecision,
    QualityRuntimeGatePilot,
)


def check(name, condition):
    print(f"{name:<54} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def main():
    print("NTPE TE-v5.2 Stage-5.2.6 Quality Runtime Gate Pilot Freeze Test")
    print("=" * 92)

    root = Path(__file__).resolve().parent
    path = root / "manifests" / "te_v52_quality_runtime_gate_pilot_freeze_manifest.json"
    check("Freeze Manifest Exists", path.exists())
    manifest = json.loads(path.read_text(encoding="utf-8"))
    check("Freeze Enabled", manifest["frozen"] is True)
    check("Version Correct", manifest["version"] == "TE-v5.2")
    check("Stages Complete", manifest["stages"] == [
        "5.2.1", "5.2.2", "5.2.3", "5.2.4", "5.2.5"
    ])
    check("Contract Import", QualityRuntimeGateContract is not None)
    check("Admission Import", QualityRuntimeGateAdmission is not None)
    check("Decision Import", QualityRuntimeGateDecision is not None)
    check("Pilot Import", QualityRuntimeGatePilot is not None)
    check("Runtime Result Unchanged", manifest["runtime_result_unchanged"] is True)
    check("Runtime Unchanged", manifest["translation_runtime_modified"] is False)
    check("Provider Unchanged", manifest["provider_runtime_modified"] is False)
    check("Launcher Unchanged", manifest["launcher_modified"] is False)

    print("NTPE TE-v5.2 Stage-5.2.6 Quality Runtime Gate Pilot Freeze PASS")


if __name__ == "__main__":
    main()
