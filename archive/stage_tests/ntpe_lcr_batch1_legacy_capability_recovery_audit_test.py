from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
AUDIT = ROOT / "audits" / "legacy_capability_recovery" / "batch1"
SOURCE = ROOT / "audits" / "legacy_capability_recovery" / "source_material"
ALLOWED_PREFIXES = (
    "audits/legacy_capability_recovery/",
    "ntpe_lcr_batch1_legacy_capability_recovery_audit_test.py",
    "tests/integration/lcr_batch1_legacy_capability_recovery_audit_test.py",
)
REQUIRED_CAPABILITIES = {
    "character_memory", "dynamic_character_extraction", "character_voice_memory", "previous_translation_context",
    "scene_memory", "narrative_memory", "chunk_splitting", "chunk_cache", "resume_recovery",
    "realtime_output_assembly", "glossary_enforcement", "unknown_name_handling", "provider_fallback",
    "multi_provider_routing", "dual_model_workflow", "draft_translation", "polish_workflow",
    "semantic_verification", "quality_retry", "basic_output_validation", "encoding_detection", "gui_workflow",
    "batch_processing", "pause_resume", "configuration_persistence",
}
REQUIRED_CURRENT = {
    "Runtime", "Provider Layer", "Resume/Recovery", "Chunking", "Output Assembly", "Glossary",
    "Character Memory", "Adaptive Context", "Narrative State", "Quality Engine", "TIC Failure Corpus",
    "Active Regression", "Offline Quality Gate", "Prompt Builder", "Stage 11 Quality Framework", "Stage 12 Candidate",
}
VALID_DECISIONS = {
    "KEEP_CURRENT", "MERGE_WITH_CURRENT", "REIMPLEMENT_FROM_CONCEPT", "EXPERIMENT_ONLY",
    "DROP_UNSAFE", "LICENSE_OR_SECURITY_BLOCKED",
}
SECRET_PATTERNS = {
    "nvidia_key": re.compile(r"nvapi-[A-Za-z0-9._-]+", re.I),
    "generic_secret_key": re.compile(r"(?:sk|key)-[A-Za-z0-9_-]{20,}", re.I),
    "bearer_value": re.compile(r"Bearer\s+[A-Za-z0-9._-]{12,}", re.I),
}


def load(name: str):
    return json.loads((AUDIT / name).read_text(encoding="utf-8"))


def digest_manifest(files: list[dict[str, str]]) -> str:
    h = hashlib.sha256()
    for item in files:
        rel = item["path"]
        data = (ROOT / rel).read_bytes()
        actual = hashlib.sha256(data).hexdigest()
        assert actual == item["sha256"], f"frozen file changed: {rel}"
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        h.update(actual.encode("ascii"))
        h.update(b"\n")
    return h.hexdigest()


def changed_paths() -> list[str]:
    result = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"], cwd=ROOT, check=True,
        capture_output=True, text=True, encoding="utf-8",
    )
    return [line[3:].strip().strip('"').replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]


def run_validation() -> dict[str, object]:
    inventory = load("LEGACY_CAPABILITY_INVENTORY.json")
    current = load("CURRENT_NTPE_CAPABILITY_MAP.json")
    matrix = load("LCR_CAPABILITY_DECISION_MATRIX.json")
    multilingual = load("MULTILINGUAL_RECOVERY_IMPACT.json")
    character = load("CHARACTER_MEMORY_V2_DESIGN.json")
    cache = load("CHUNK_CACHE_V2_DESIGN.json")
    dual = load("DUAL_PASS_RECOVERY_DESIGN.json")
    roadmap = load("LCR_IMPLEMENTATION_ROADMAP.json")
    security = load("SECURITY_FINDINGS.json")
    audit = load("LCR_BATCH1_AUDIT.json")

    source_files = [SOURCE / "v12_dynamic_memory_legacy.txt", SOURCE / "translate_realtime_v2_legacy.txt"]
    assert all(path.is_file() and path.stat().st_size > 0 for path in source_files)
    assert "update_character_memory_via_ai" in source_files[0].read_text(encoding="utf-8")
    assert "translate_chunk_with_retry" in source_files[1].read_text(encoding="utf-8")
    assert "[REDACTED_API_KEY]" in source_files[1].read_text(encoding="utf-8")

    scanned = []
    for path in [*SOURCE.glob("*.txt"), *AUDIT.glob("*")]:
        if not path.is_file() or path.suffix.lower() == ".zip":
            continue
        text = path.read_text(encoding="utf-8", errors="strict")
        for label, pattern in SECRET_PATTERNS.items():
            assert not pattern.search(text), f"secret pattern {label} in {path.relative_to(ROOT)}"
        scanned.append(path.relative_to(ROOT).as_posix())

    ids = [row["capability_id"] for row in inventory]
    assert REQUIRED_CAPABILITIES <= set(ids)
    assert len(ids) == len(set(ids))
    for row in inventory:
        for key in (
            "legacy_file", "legacy_symbol", "description", "inputs", "outputs", "side_effects", "provider_calls",
            "disk_writes", "state_files", "quality_intent", "reliability_intent", "performance_intent",
            "security_risk", "quality_risk", "runtime_risk", "data_integrity_risk", "current_ntpe_equivalent", "feature_gap",
        ):
            assert key in row and row[key] not in (None, "")

    current_names = {row["capability"] for row in current}
    assert current_names == REQUIRED_CURRENT
    for row in current:
        assert set(("capability", "current_module", "production_connected", "frozen", "tested", "quality_value", "performance_cost", "known_limitations")) <= set(row)

    decisions = {row["capability"]: row for row in matrix}
    assert set(decisions) == set(ids)
    assert all(row["decision"] in VALID_DECISIONS for row in matrix)
    assert all(row["reason"] for row in matrix if row["decision"] == "DROP_UNSAFE")
    assert all(row["quality_impact"] == "direct" for row in matrix if row["decision"] == "REIMPLEMENT_FROM_CONCEPT")
    assert decisions["dynamic_character_extraction"]["decision"] == "REIMPLEMENT_FROM_CONCEPT"
    assert decisions["previous_translation_context"]["decision"] == "MERGE_WITH_CURRENT"
    assert decisions["provider_fallback"]["decision"] == "EXPERIMENT_ONLY"
    assert decisions["academic_degraded_fallback"]["decision"] == "DROP_UNSAFE"
    assert decisions["resume_recovery"]["decision"] == "KEEP_CURRENT"

    required_character = {"character_id", "canonical_name", "aliases", "language", "speech_style", "personality_traits", "relationships", "current_emotion", "scene_state", "evidence", "confidence", "source_case_id", "source_offsets", "status", "version", "created_at", "updated_at", "expires_at", "human_approved", "prompt_eligible"}
    assert required_character <= set(character["record_schema"])
    assert character["rules"]["low_confidence_prompt_eligible"] is False
    assert character["rules"]["unbounded_append"] is False
    assert character["rules"]["token_budget_required"] is True
    assert character["implemented"] is False

    required_cache = {"chunk_id", "source_sha256", "prompt_sha256", "provider", "model", "attempt", "status", "translation_sha256", "quality_status", "created_at", "completed_at", "resume_eligible"}
    assert required_cache <= set(cache["record_schema"])
    assert cache["partial_output_completed"] is False
    assert "ResumeJournal" in cache["resume_integration"]
    assert cache["implemented"] is False

    assert set(dual["modes"]) == {"single_pass", "dual_pass", "selective_polish"}
    assert set(("draft_provider", "draft_model", "polish_provider", "polish_model", "same_model_allowed", "provider_requests", "timeout_budget", "retry_policy", "fallback_policy", "quality_gate", "semantic_rollback")) <= set(dual["shared_configuration"])
    assert dual["implemented"] is False

    profiles = multilingual["profiles"]
    assert set(("ko", "ja", "en")) <= set(profiles)
    assert profiles["target"] == "zh-Hant"
    assert {row["capability"] for row in multilingual["capabilities"]} == set(ids)

    assert len(roadmap) == 9
    assert roadmap[0]["batch"] == "LCR Batch 2"
    assert roadmap[0]["scope"] == "Character Memory V2"
    assert all(set(("direct_quality_value", "performance_gate", "timeout_gate", "regression_gate", "production_boundary")) <= set(row) for row in roadmap)

    assert security["plaintext_api_key_detected"] is True
    assert security["redacted_copy_created"] is True
    assert security["key_value_saved"] is False
    assert security["key_tested"] is False
    assert security["rotation_recommended"] is True

    for group in ("production", "runtime", "provider", "prompt", "tic_batch7"):
        frozen = audit["baseline_hashes"][group]
        assert frozen["file_count"] > 0, f"empty hash group: {group}"
        assert digest_manifest(frozen["files"]) == frozen["aggregate_sha256"]

    boundaries = audit["boundaries"]
    expected_false = [
        "provider_executed", "new_translation_generated", "production_code_modified", "runtime_modified",
        "provider_modified", "prompt_modified", "qa_engine_modified", "tic_modified", "legacy_source_code_integrated",
        "character_memory_v2_implemented", "chunk_cache_v2_implemented", "dual_pass_implemented",
        "multilingual_profiles_implemented", "lcr_batch2_started",
    ]
    assert all(boundaries[key] is False for key in expected_false)
    assert boundaries["network_requests"] == 0
    assert boundaries["legacy_concepts_audited"] is True
    assert boundaries["legacy_secrets_redacted"] is True

    paths = changed_paths()
    assert paths, "expected Batch 1 additions"
    assert all(any(path == prefix or path.startswith(prefix) for prefix in ALLOWED_PREFIXES) for path in paths), paths
    deleted = subprocess.run(["git", "ls-files", "--deleted"], cwd=ROOT, check=True, capture_output=True, text=True, encoding="utf-8").stdout.strip()
    assert not deleted

    return {
        "legacy_capabilities": len(inventory), "current_capabilities": len(current),
        "secret_scanned_files": len(scanned), "changed_paths": paths,
        "hash_groups": list(audit["baseline_hashes"]), "network_requests": 0,
    }


def main() -> int:
    report = run_validation()
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    print("LCR Batch 1 Legacy Capability Recovery Audit ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
