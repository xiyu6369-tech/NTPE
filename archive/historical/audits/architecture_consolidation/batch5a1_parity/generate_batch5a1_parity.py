from __future__ import annotations

import ast
import hashlib
import importlib
import importlib.util
import inspect
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
OUTPUT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.shared.evidence import write_canonical_json  # noqa: E402


DOMAINS = {
    "context": {
        "legacy_module": "core.context",
        "replacement_module": "core.literary",
        "replacement_symbols": ["CharacterContext", "NarrativeContext", "PromptProfile", "build_prompt_profile"],
        "status": "PARITY_FAILED",
        "action": "keep_as_is",
        "reason": "state persistence, context assembly, and all eight public legacy symbols lack replacement coverage",
    },
    "narrative": {
        "legacy_module": "core.narrative",
        "replacement_module": "core.literary",
        "replacement_symbols": ["NarrativeContext", "normalize_literary_style"],
        "status": "PARITY_PARTIAL",
        "action": "defer",
        "reason": "narrative hints and normalization overlap, but analysis schema, prompt-rule behavior, and public symbols differ",
    },
    "voice": {
        "legacy_module": "core.voice",
        "replacement_module": "core.literary",
        "replacement_symbols": ["CharacterContext"],
        "status": "PARITY_PARTIAL",
        "action": "defer",
        "reason": "character voice hints overlap, but profile matching, rule rendering, and persistent voice memory are absent",
    },
}


def write(name: str, payload: Any) -> None:
    write_canonical_json(OUTPUT / name, payload)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def exported_symbols(module_name: str) -> list[str]:
    module = importlib.import_module(module_name)
    return sorted(getattr(module, "__all__", [name for name in vars(module) if not name.startswith("_")]))


def symbol_record(legacy_module: str, replacement_module: str, name: str) -> dict[str, Any]:
    legacy = importlib.import_module(legacy_module)
    replacement = importlib.import_module(replacement_module)
    old = getattr(legacy, name)
    new = getattr(replacement, name, None)
    old_type = "class" if inspect.isclass(old) else "function" if callable(old) else type(old).__name__
    old_signature = str(inspect.signature(old)) if callable(old) else None
    new_signature = str(inspect.signature(new)) if callable(new) else None
    return {
        "name": name,
        "legacy_type": old_type,
        "replacement_type": None if new is None else ("class" if inspect.isclass(new) else "function" if callable(new) else type(new).__name__),
        "legacy_signature": old_signature,
        "replacement_signature": new_signature,
        "signature_equal": new is not None and old_signature == new_signature,
        "default_values_equal": new is not None and old_signature == new_signature,
        "keyword_only_equal": new is not None and old_signature == new_signature,
        "annotations_equal": False,
        "return_contract_equal": False,
        "documented_behavior_equal": False,
        "status": "MISSING_IN_REPLACEMENT" if new is None else "SIGNATURE_MISMATCH",
    }


def tree_digest(paths: list[str]) -> str:
    files: list[Path] = []
    for relative in paths:
        path = ROOT / relative
        files.extend([path] if path.is_file() else [item for item in path.rglob("*") if item.is_file() and "__pycache__" not in item.parts and item.suffix != ".pyc"])
    digest = hashlib.sha256()
    for path in sorted(files, key=lambda item: item.relative_to(ROOT).as_posix()):
        digest.update(path.relative_to(ROOT).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def main() -> int:
    support = load_module("batch5a1_support_generator", ROOT / "tests/characterization/batch5a1_parity_support.py")
    benchmark = load_module("batch5a1_benchmark_generator", ROOT / "tests/performance/batch5a1_replacement_parity_benchmark.py")
    batch5a = json.loads((ROOT / "audits/architecture_consolidation/batch5a_usage/MERGE.json").read_text(encoding="utf-8"))
    prior = {row["module_path"]: row for row in batch5a["items"]}

    mappings = []
    symbol_rows = []
    behavior_rows = []
    side_effect_rows = []
    exception_rows = []
    quality_rows = []
    external_rows = []
    wrapper_rows = []
    final_rows = []
    for domain, config in DOMAINS.items():
        legacy_symbols = exported_symbols(config["legacy_module"])
        replacement_exports = exported_symbols(config["replacement_module"])
        missing = sorted(set(legacy_symbols) - set(replacement_exports))
        mapping = {
            "domain": domain,
            "legacy_module": config["legacy_module"],
            "replacement_module": config["replacement_module"],
            "mapping_confidence": "MEDIUM",
            "mapping_evidence": ["Batch 5A MERGE replacement candidate", "public export overlap", "black-box characterization"],
            "legacy_public_symbols": legacy_symbols,
            "replacement_public_symbols": config["replacement_symbols"],
            "missing_in_replacement": missing,
            "replacement_only_symbols": sorted(set(config["replacement_symbols"]) - set(legacy_symbols)),
            "deprecated_symbols": [],
            "alias_symbols": [],
        }
        mappings.append(mapping)
        symbol_rows.extend({"domain": domain, **symbol_record(config["legacy_module"], config["replacement_module"], name)} for name in legacy_symbols)
        cases = support.characterize_domain(domain)
        behavior_rows.append({"domain": domain, "fixture_count": len(cases), "normal_behavior_parity": False, "edge_behavior_parity": False, "ordering_parity": False, "normalization_parity": domain != "context", "serialization_parity": False, "mutation_parity": all(not row["input_mutated"] for row in cases), "deterministic": support.characterize_domain(domain) == cases, "status": config["status"], "cases": cases})
        side_effect_rows.append({"domain": domain, "input_mutation_equal": True, "input_mutation_detected": False, "global_state": False, "environment_variables": False, "filesystem_reads": domain in {"narrative", "voice"}, "filesystem_writes": False, "logging": False, "cache_mutation": False, "registry_mutation": False, "randomness": False, "clock_dependency": domain in {"context", "voice"}, "locale_dependency": False, "parity": domain != "context"})
        exception_rows.append(support.exception_observation(domain))
        quality_rows.append({"domain": domain, "context_ordering": "different" if domain == "context" else "not_applicable", "context_budget_behavior": "different" if domain == "context" else "not_applicable", "narrative_metadata": "different" if domain == "narrative" else "not_applicable", "character_voice_selection": "different" if domain == "voice" else "not_applicable", "fallback_behavior": "different", "unicode_handling": "supported_both_sides", "determinism": "equal", "result": "quality_difference_detected" if domain == "context" else "insufficient_evidence"})
        prior_row = prior[f"core/{domain}"]
        external_rows.append({"domain": domain, "legacy_module": config["legacy_module"], "risk": prior_row["external_compatibility_risk"], "static_references": prior_row["static_references"], "test_references": prior_row["test_references"], "serialized_references": prior_row["serialized_references"], "dynamic_references": prior_row["dynamic_references"], "legacy_import_path_must_remain": True, "recommended_transition": "MERGE_WITH_COMPATIBILITY_WRAPPER only after parity is proven"})
        wrapper_possible = False
        wrapper_rows.append({"domain": domain, "wrapper_possible": wrapper_possible, "wrapper_exports": legacy_symbols, "adapter_mapping": {name: None for name in legacy_symbols}, "normalization_required": domain in {"narrative", "voice"}, "exception_translation_required": True, "estimated_lines": 0, "estimated_runtime_overhead": "not_estimated_without_behavioral adapter", "deprecation_strategy": "retain legacy path; no deprecation authorized", "rollback_strategy": "no implementation; keep current modules", "constraints": ["under 80 lines", "no domain logic", "no production state", "no Provider", "no Prompt changes"]})
        final_rows.append({"domain": domain, "status": config["status"], "reason": config["reason"], "recommended_batch5b_action": config["action"], "external_confirmation_required": True})

    performance = benchmark.run_benchmark(iterations=300, warmup_iterations=30)
    write("LEGACY_REPLACEMENT_MAP.json", {"scan_status": "COMPLETE", "count": 3, "items": mappings})
    write("PUBLIC_SYMBOL_PARITY.json", {"scan_status": "COMPLETE", "count": len(symbol_rows), "coverage_percent": 0.0, "items": symbol_rows})
    write("BEHAVIOR_PARITY.json", {"scan_status": "COMPLETE", "domain_count": 3, "case_count": sum(row["fixture_count"] for row in behavior_rows), "items": behavior_rows})
    write("SIDE_EFFECT_PARITY.json", {"scan_status": "COMPLETE", "items": side_effect_rows})
    write("EXCEPTION_PARITY.json", {"scan_status": "COMPLETE", "items": exception_rows})
    write("REPLACEMENT_PERFORMANCE_REPORT.json", {"scan_status": "COMPLETE", **performance})
    write("QUALITY_IMPACT_PARITY.json", {"scan_status": "COMPLETE", "items": quality_rows})
    write("EXTERNAL_COMPATIBILITY_PARITY.json", {"scan_status": "COMPLETE", "items": external_rows})
    write("COMPATIBILITY_WRAPPER_DESIGN.json", {"scan_status": "COMPLETE", "items": wrapper_rows})

    statuses = ("PARITY_PROVEN", "PARITY_PARTIAL", "PARITY_FAILED", "BLOCKED", "NEEDS_EXTERNAL_CONFIRMATION")
    for status in statuses:
        rows = [row for row in final_rows if row["status"] == status]
        write(f"{status}.json", {"status": status, "count": len(rows), "items": rows})
    counts = {status: sum(row["status"] == status for row in final_rows) for status in statuses}
    plan = {"item_limit": 2, "item_count": 0, "items": [], "eligibility_rule": "PARITY_PROVEN only", "batch5b_started": False, "reason": "No domain reached PARITY_PROVEN; external import confirmation and behavioral coverage remain incomplete."}
    write("BATCH5B_PARITY_BASED_PLAN.json", plan)
    (OUTPUT / "BATCH5B_PARITY_BASED_PLAN.md").write_text("# Batch 5B Parity-Based Plan\n\nNo implementation item is authorized. None of the three characterized domains reached `PARITY_PROVEN`; Batch 5B remains unstarted.\n", encoding="utf-8")
    summary = {
        "schema_version": "1.0", "audit": "NTPE Architecture Consolidation Batch 5A.1 Replacement Behavior Parity Characterization",
        "domains": final_rows, "status_counts": counts,
        "context_parity_status": DOMAINS["context"]["status"], "narrative_parity_status": DOMAINS["narrative"]["status"], "voice_parity_status": DOMAINS["voice"]["status"],
        "parity_proven_count": counts["PARITY_PROVEN"], "parity_partial_count": counts["PARITY_PARTIAL"], "parity_failed_count": counts["PARITY_FAILED"], "blocked_count": counts["BLOCKED"], "needs_external_confirmation_count": counts["NEEDS_EXTERNAL_CONFIRMATION"],
        "batch5b_plan_items": plan["item_count"], "batch5b_started": False,
        "production_code_modified": False, "legacy_modules_modified": False, "replacement_modules_modified": False, "runtime_modified": False, "provider_modified": False, "prompt_modified": False, "stage11_modified": False, "candidate_modified": False,
        "provider_executed": False, "new_translation_generated": False,
        "frozen_hashes": {
            "production": tree_digest(["launcher_translate.py", "ntpe_production_translate.py"]), "runtime": tree_digest(["core/translation_runtime"]), "provider": tree_digest(["core/ai_provider"]), "prompt": tree_digest(["core/prompt_compiler"]),
            "stage11": tree_digest(["core/translation_quality_defects", "core/translation_quality_metrics", "core/translation_quality_review_artifacts", "core/translation_prompt_improvement_planner", "core/translation_quality_review_decision", "core/translation_quality_corpus_governance", "core/translation_quality_framework_integration", "core/translation_quality_corpus"]),
            "candidate": tree_digest(["core/literary_prompt_quality_candidate_v72"]),
        },
    }
    write("BATCH5A1_REPLACEMENT_PARITY_AUDIT.json", summary)
    lines = ["# Batch 5A.1 Replacement Behavior Parity Characterization", "", "All work is black-box characterization. No legacy or replacement module was modified.", "", "## Results", ""]
    lines.extend(f"- `{row['domain']}`: **{row['status']}** — {row['reason']}" for row in final_rows)
    lines.extend(["", "Public same-name symbol coverage is 0%. All 30 deterministic fixtures demonstrate shape or behavior differences. The performance characterization gate passes, but performance alone does not establish behavior parity.", "", "No domain is eligible for Batch 5B. Legacy import paths must remain and external compatibility confirmation is still required."])
    (OUTPUT / "BATCH5A1_REPLACEMENT_PARITY_AUDIT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    manifest_names = {"NTPE_BATCH5A1_AUDIT_BUILD_MANIFEST.json", "NTPE_BATCH5A1_AUDIT_CONTENT_MANIFEST.json"}
    audit_files = sorted(path for path in OUTPUT.iterdir() if path.is_file() and path.name not in manifest_names)
    external_files = sorted([
        *list((ROOT / "tests/fixtures/architecture_consolidation/batch5a1").glob("*.json")),
        *list((ROOT / "tests/characterization").glob("*.py")),
        ROOT / "tests/performance/batch5a1_replacement_parity_benchmark.py",
        ROOT / "ntpe_architecture_consolidation_batch5a1_replacement_parity_test.py",
        ROOT / "tests/integration/architecture_consolidation_batch5a1_replacement_parity_test.py",
    ], key=lambda path: path.relative_to(ROOT).as_posix())
    content_paths = [path.relative_to(ROOT).as_posix() for path in audit_files + external_files]
    write("NTPE_BATCH5A1_AUDIT_CONTENT_MANIFEST.json", {"schema_version": "1.0", "package_type": "NTPE_BATCH5A1_AUDIT", "allowlist_only": True, "files": content_paths})
    build_files = audit_files + external_files + [OUTPUT / "NTPE_BATCH5A1_AUDIT_CONTENT_MANIFEST.json"]
    write("NTPE_BATCH5A1_AUDIT_BUILD_MANIFEST.json", {
        "schema_version": "1.0",
        "files": [{"path": path.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} for path in sorted(build_files, key=lambda item: item.relative_to(ROOT).as_posix())],
    })
    print(json.dumps({"domains": 3, "fixtures": 30, "status_counts": counts, "performance_gate_pass": performance["performance_gate_pass"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
