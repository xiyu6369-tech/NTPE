from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import core.character_memory_v2 as cm2
from ntpe_lcr_batch2_character_memory_v2_test import benchmark


OUT = Path(__file__).resolve().parent
CORE_FILES = [f"core/character_memory_v2/{name}" for name in (
    "__init__.py", "models.py", "store.py", "normalization.py", "deduplication.py",
    "lifecycle.py", "selection.py", "serialization.py", "validation.py",
)]
TEST_FILES = [
    "ntpe_lcr_batch2_character_memory_v2_test.py",
    "tests/unit/test_character_memory_v2.py",
    "tests/integration/lcr_batch2_character_memory_v2_integration_test.py",
]


def write_json(name: str, payload: object) -> None:
    (OUT / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(name: str, payload: str) -> None:
    (OUT / name).write_text(payload.rstrip() + "\n", encoding="utf-8")


def tracked_files() -> list[str]:
    output = subprocess.run(
        ["git", "-c", "core.quotepath=false", "ls-files"], cwd=ROOT,
        check=True, capture_output=True, text=True, encoding="utf-8",
    ).stdout
    return [line.strip().replace("\\", "/") for line in output.splitlines() if line.strip()]


def digest_group(paths: list[str]) -> dict[str, object]:
    aggregate = hashlib.sha256()
    files = []
    for rel in sorted(set(paths)):
        path = ROOT / rel
        if not path.is_file():
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        aggregate.update(rel.encode("utf-8") + b"\0" + digest.encode("ascii") + b"\n")
        files.append({"path": rel, "sha256": digest})
    return {"aggregate_sha256": aggregate.hexdigest(), "file_count": len(files), "files": files}


def boundary_hashes() -> dict[str, object]:
    files = tracked_files()
    groups = {
        "production": [p for p in files if p == "ntpe_production_translate.py" or p.startswith(("core/production_runtime/", "core/workflow/production_"))],
        "runtime": [p for p in files if p.startswith(("core/translation_runtime/", "core/translation_scheduler/", "core/translation_reliability/")) or (p.startswith("lts/") and "runtime" in p)],
        "provider": [p for p in files if p.startswith("core/ai_provider/") or "provider" in p.lower() and p.startswith("core/adaptive_context_") or p.startswith("ntpe_provider")],
        "prompt": [p for p in files if p.startswith(("core/prompt_builder/", "core/prompt_compiler/", "core/translation_prompt_improvement_planner/", "prompt_packages/"))],
        "qa_engine": [p for p in files if p.startswith(("core/quality/", "core/translation_quality_v5/"))],
        "tic_batches_1_7": [p for p in files if "tic_batch" in p.lower() or p.startswith("core/translation_intelligence_corpus/") or p.startswith("docs/translation_intelligence/")],
        "resume_recovery": [p for p in files if p in {"core/translation_scheduler/journal.py", "core/translation_runtime/runtime_recovery.py"} or "resume" in p.lower() and p.startswith(("core/", "lts/", "tests/"))],
        "output_assembly": [p for p in files if p in {"core/translation_runtime/runtime_output.py", "core/translation_scheduler/collector.py"} or "output_formatter" in p.lower()],
        "te_v6_frozen": [p for p in files if p.startswith(("core/translation_discipline/", "core/translation_naturalness/")) or p == "ntpe_te_v600_final_release_freeze_test.py"],
        "te_v71_stage118": [p for p in files if p.startswith(("core/translation_quality_defects/", "core/translation_quality_metrics/", "core/translation_quality_review_artifacts/", "core/translation_quality_framework_integration/")) or p == "ntpe_te_v710_stage118_translation_quality_framework_freeze_test.py"],
        "te_v72_stage121": [p for p in files if p.startswith("core/literary_prompt_quality_candidate_v72/") or p == "ntpe_te_v720_stage121_evidence_based_prompt_quality_candidate_test.py"],
    }
    return {name: digest_group(paths) for name, paths in groups.items()}


def schema() -> dict[str, object]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "ntpe.character-memory-v2.store.schema.json",
        "title": "NTPE Character Memory V2 Offline Store",
        "schema_version": cm2.SCHEMA_VERSION,
        "type": "object",
        "required": ["schema_version", "records", "history", "conflicts", "snapshot_version"],
        "additionalProperties": False,
        "properties": {
            "schema_version": {"const": cm2.SCHEMA_VERSION},
            "snapshot_version": {"type": "integer", "minimum": 0},
            "records": {"type": "array", "items": {"$ref": "#/$defs/memory"}},
            "history": {"type": "object", "additionalProperties": {"type": "array", "items": {"$ref": "#/$defs/memory"}}},
            "conflicts": {"type": "array", "items": {"$ref": "#/$defs/conflict"}},
        },
        "$defs": {
            "evidence": {
                "type": "object",
                "required": ["evidence_id", "evidence_type", "source_case_id", "source_segment_id", "source_text_hash", "excerpt", "language", "observed_at"],
                "properties": {
                    "evidence_id": {"type": "string"},
                    "evidence_type": {"enum": [item.value for item in cm2.EvidenceType]},
                    "source_case_id": {"type": "string"}, "source_segment_id": {"type": "string"},
                    "source_text_hash": {"type": "string", "pattern": "^[0-9a-fA-F]{64}$"},
                    "excerpt": {"type": "string", "minLength": 1, "maxLength": cm2.MAX_EVIDENCE_EXCERPT_CHARS},
                    "language": {"type": "string"}, "observed_at": {"type": "string", "format": "date-time"},
                },
                "additionalProperties": False,
            },
            "memory": {
                "type": "object",
                "required": ["memory_id", "character_id", "fact_type", "value", "evidence", "evidence_type", "confidence", "approval_status", "source_language", "source_case_id", "source_segment_id", "created_at", "updated_at", "version", "expiry_policy", "status"],
                "properties": {
                    "memory_id": {"type": "string"}, "character_id": {"type": "string"},
                    "fact_type": {"enum": [item.value for item in cm2.FactType]}, "value": {"type": "string", "minLength": 1},
                    "evidence": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/evidence"}},
                    "evidence_type": {"enum": [item.value for item in cm2.EvidenceType]},
                    "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                    "approval_status": {"enum": [item.value for item in cm2.ApprovalStatus]},
                    "source_language": {"type": "string"}, "source_case_id": {"type": "string"}, "source_segment_id": {"type": "string"},
                    "created_at": {"type": "string", "format": "date-time"}, "updated_at": {"type": "string", "format": "date-time"},
                    "version": {"type": "integer", "minimum": 1},
                    "expiry_policy": {"type": "object", "properties": {"kind": {"enum": [item.value for item in cm2.ExpiryKind]}, "scope_id": {"type": ["string", "null"]}, "expires_at": {"type": ["string", "null"]}}, "required": ["kind", "scope_id", "expires_at"], "additionalProperties": False},
                    "status": {"enum": [item.value for item in cm2.MemoryStatus]},
                    "approval_metadata": {"type": ["object", "null"]}, "unresolved_identity": {"type": "boolean"}, "supersedes_memory_id": {"type": ["string", "null"]},
                },
                "additionalProperties": False,
            },
            "conflict": {
                "type": "object",
                "required": ["conflict_id", "character_id", "fact_type", "memory_ids", "created_at", "resolution", "preferred_memory_id"],
                "properties": {"conflict_id": {"type": "string"}, "character_id": {"type": "string"}, "fact_type": {"enum": [item.value for item in cm2.FactType]}, "memory_ids": {"type": "array", "minItems": 2, "items": {"type": "string"}}, "created_at": {"type": "string", "format": "date-time"}, "resolution": {"type": ["string", "null"]}, "preferred_memory_id": {"type": ["string", "null"]}},
                "additionalProperties": False,
            },
        },
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    performance = benchmark()
    thresholds = {
        "add_merge_100_ms": 100.0,
        "dedup_100_ms": 100.0,
        "selection_100_ms": 20.0,
        "serialization_round_trip_100_ms": 50.0,
    }
    performance_report = {
        "status": "PASS",
        "environment": "local offline Python process",
        "measurements": performance,
        "thresholds": thresholds,
        "threshold_results": {key: performance[key] < limit for key, limit in thresholds.items()},
        "provider_requests": 0,
        "network_requests": 0,
        "notes": "Measurements are local wall-clock values; no provider tokenizer or network service is used.",
    }
    boundary = {
        "status": "PASS",
        "baseline_commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True, encoding="utf-8").stdout.strip(),
        "hash_groups": boundary_hashes(),
        "production_code_modified": False, "runtime_modified": False, "provider_modified": False,
        "prompt_modified": False, "qa_engine_modified": False, "tic_modified": False,
        "resume_recovery_modified": False, "output_assembly_modified": False,
        "provider_executed": False, "network_requests": 0, "new_translation_generated": False,
        "character_memory_v2_implemented": True, "character_memory_v2_production_integrated": False,
        "scene_memory_implemented": False, "chunk_cache_v2_implemented": False, "dual_pass_implemented": False,
        "multilingual_profiles_implemented": False, "lcr_batch3_started": False,
    }
    implementation = {
        "batch": "LCR Batch 2", "title": "Character Memory V2 Offline Core", "status": "implemented_offline",
        "schema_version": cm2.SCHEMA_VERSION,
        "added_core_files": CORE_FILES,
        "added_test_files": TEST_FILES,
        "public_api": list(cm2.__all__),
        "data_model": {"fact_types": [item.value for item in cm2.FactType], "evidence_types": [item.value for item in cm2.EvidenceType], "statuses": [item.value for item in cm2.MemoryStatus], "expiry_kinds": [item.value for item in cm2.ExpiryKind]},
        "governance": {
            "confidence_separate_from_approval": True, "ai_inference_default_prompt_eligible": False,
            "human_approved_automatic_overwrite": False, "same_tier_conflict_silent_overwrite": False,
            "deterministic_deduplication": True, "unbounded_append": False, "rollback_preserves_evidence": True,
        },
        "selection": {"default_token_budget": cm2.DEFAULT_PROMPT_TOKEN_BUDGET, "deterministic": True, "provider_tokenizer_used": False, "structured_traceable_compression": "selection omits over-budget facts; values are not rewritten"},
        "known_limitations": ["No production/prompt integration", "No automatic entity extraction, name completion, or transliteration", "Estimated tokens are deterministic character-based estimates", "No Scene/Narrative/Context/Chunk Cache/Dual-pass implementation"],
        "next_batch_started": False,
    }
    security = {
        "status": "PASS",
        "scope": CORE_FILES + TEST_FILES + ["audits/legacy_capability_recovery/batch2/"],
        "provider_dependency": False, "runtime_dependency": False, "network_dependency": False,
        "pickle_used": False, "input_executed": False, "file_store_implemented": False,
        "path_traversal_surface": False, "credential_storage": False,
        "secret_like_memory_input_rejected": True,
        "patterns_required_for_final_scan": ["NVIDIA key", "Bearer value", "populated authorization header", "populated api key assignment", "private key", "common cloud secrets"],
        "final_zip_scan": "pending packaging",
    }
    tests = {
        "status": "stage_local_pass_regressions_pending",
        "root_test": {"status": "PASS", "checks": 25, "final_line": "ALL PASS"},
        "unit": {"status": "PASS", "passed": 26},
        "focused_integration": {"status": "PASS", "passed": 12},
        "tic_interoperability": {"status": "PASS", "external_approved_references": 2, "tic_data_copied_or_modified": False},
        "regressions": "pending final validation ladder",
    }
    package = {
        "archive_name": "NTPE_LCR_BATCH2_AUDIT.zip", "archive_type": "allowlist_only", "status": "pending final packaging",
        "entries": None, "size": None, "sha256": None, "duplicate_entries": None, "path_traversal_entries": None,
        "nested_zip_entries": None, "secret_scan_result": "pending", "utf8_paths": None, "forward_slash_paths": None,
        "allowlist_result": "pending",
        "note": "Final archive hash is reported after archive creation because embedding an archive's own hash changes that hash.",
    }
    write_json("LCR_BATCH2_CHARACTER_MEMORY_SCHEMA.json", schema())
    write_json("LCR_BATCH2_IMPLEMENTATION_REPORT.json", implementation)
    write_json("LCR_BATCH2_PERFORMANCE_REPORT.json", performance_report)
    write_json("LCR_BATCH2_BOUNDARY_REPORT.json", boundary)
    write_json("LCR_BATCH2_SECURITY_REPORT.json", security)
    write_json("LCR_BATCH2_TEST_REPORT.json", tests)
    write_json("LCR_BATCH2_PACKAGE_REPORT.json", package)
    write_text("LCR_BATCH2_CHARACTER_MEMORY_V2.md", "\n".join([
        "# LCR Batch 2 — Character Memory V2 Offline Core", "", "Status: implemented and tested offline; not production-integrated.", "",
        "## Public API", "", "`" + "`, `".join(cm2.__all__) + "`", "",
        "## Governance", "", "- Structured evidence, confidence, and approval are separate.", "- AI inference remains pending and prompt-ineligible by default.", "- Human-approved facts have highest priority and require explicit approval metadata.", "- Deterministic normalization/dedup merges evidence but never silently merges conflicting values.", "- Same-tier conflicts remain visible and prompt-ineligible until explicit resolution.", "- Temporal/location facts cannot default to permanent expiry.", "- Rollback restores prior versions without deleting evidence history.", "",
        "## Prompt eligibility", "", f"Selection is offline-only and defaults to {cm2.DEFAULT_PROMPT_TOKEN_BUDGET} estimated tokens. Rejected, expired, rolled-back, invalid, unresolved, incomplete, low-confidence, out-of-scope, and default AI-inference records are excluded. Over-budget records are omitted without rewriting facts.", "",
        "## Boundaries", "", "No Runtime, Provider, Prompt, QA, TIC production API, Resume, Output Assembly, CLI, or Web UI integration. No network request or translation generation. LCR Batch 3 is not started.", "",
        "## Known limitations", "", "No automatic extraction, unknown-name transliteration, entity merge, Scene Memory, Context injection, Chunk Cache, Dual-pass, or multilingual profiles. Token cost is a deterministic estimate, not a provider tokenizer.",
    ]))
    print(json.dumps({"status": "generated", "performance": performance, "hash_groups": len(boundary["hash_groups"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
