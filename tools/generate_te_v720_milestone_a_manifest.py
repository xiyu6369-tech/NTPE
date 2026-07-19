from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "artifacts/te_v72_milestone_a"
MANIFEST = ROOT / "manifests/te_v720_milestone_a_translation_quality_integration_manifest.json"

SOURCE_PATHS = [
    *sorted((ROOT / "core/translation_quality_integration_v72").glob("*.py")),
    ROOT / "lts/txt_translation_runtime.py",
    ROOT / "lts/batch_translation_runtime.py",
    ROOT / "ntpe_production_translate.py",
]
TEST_PATHS = [
    ROOT / "tests/unit/test_translation_quality_integration_v72.py",
    ROOT / "tests/unit/test_translation_quality_integration_v72_core.py",
    ROOT / "tests/integration/translation_engine_v720_milestone_a_translation_quality_integration_test.py",
    ROOT / "tests/integration/translation_engine_v720_milestone_a_runtime_memory_test.py",
    ROOT / "tests/performance/test_translation_quality_integration_v72_performance.py",
    ROOT / "tests/fixtures/te_v72_milestone_a/quality_cases.json",
    ROOT / "ntpe_te_v720_milestone_a_translation_quality_integration_test.py",
]
EVIDENCE_PATHS = sorted(ARTIFACT_DIR.glob("*.json"))
FROZEN_PATHS = [
    *sorted((ROOT / "core/character_memory_v2").glob("*.py")),
    *sorted((ROOT / "core/context_scene_memory").glob("*.py")),
    *sorted((ROOT / "core/multilingual_profiles").glob("*.py")),
    ROOT / "core/literary/literary_prompt_builder.py",
    *sorted((ROOT / "core/literary_prompt_quality_candidate_v72").glob("*.py")),
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hashes(paths: list[Path]) -> dict[str, str]:
    return {path.relative_to(ROOT).as_posix(): sha256(path) for path in sorted(paths)}


def frozen_modified() -> list[str]:
    modified = []
    for path in FROZEN_PATHS:
        relative = path.relative_to(ROOT).as_posix()
        head = subprocess.run(["git", "show", f"HEAD:{relative}"], cwd=ROOT, check=True, capture_output=True).stdout
        if path.read_bytes() != head:
            modified.append(relative)
    return modified


def main() -> int:
    performance = json.loads((ARTIFACT_DIR / "performance_evidence.json").read_text(encoding="utf-8"))
    modified = frozen_modified()
    payload = {
        "schema_version": "te-v7.2-milestone-a-manifest-v1",
        "milestone": "TE v7.2 Milestone A",
        "stages": ["12.3", "12.4", "12.5"],
        "source_hashes": hashes(SOURCE_PATHS),
        "test_hashes": hashes(TEST_PATHS),
        "evidence_hashes": hashes(EVIDENCE_PATHS),
        "flags": {
            "--quality-integration-v72": False,
            "--quality-character-memory-v72": False,
            "--quality-context-scene-v72": False,
            "--quality-naturalness-v72": False,
            "--quality-integration-kill-switch-v72": False,
        },
        "activation_gate": "translation_quality_integration_ready_for_controlled_canary",
        "frozen_boundary_status": {"modified_count": len(modified), "modified_paths": modified},
        "provider_requests_added": 0,
        "network_requests_added": 0,
        "production_hook_count": 1,
        "runtime_behavior_default": "unchanged_default_off",
        "active_production_status": "inactive",
        "authorization_state": {
            "active_production_authorized": False,
            "provider_execution_authorized": False,
            "automatic_rollout_authorized": False,
            "formal_output_replacement_authorized": False,
            "dual_pass_authorized": False,
        },
        "deterministic_fingerprint": "sha256-canonical-json",
        "performance_summary": {
            key: performance[key]
            for key in ("single_chunk_p50_ms", "single_chunk_p95_ms", "single_chunk_max_ms", "hundred_run_total_ms", "determinism_runs", "targets_passed")
        },
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(MANIFEST.relative_to(ROOT).as_posix())
    print(hashlib.sha256(MANIFEST.read_bytes()).hexdigest())
    return 0 if not modified else 1


if __name__ == "__main__":
    raise SystemExit(main())
