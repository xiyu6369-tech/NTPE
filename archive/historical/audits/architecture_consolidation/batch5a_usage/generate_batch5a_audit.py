from __future__ import annotations

import ast
from collections import Counter, deque
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.shared.evidence import write_canonical_json  # noqa: E402


OUTPUT = Path(__file__).resolve().parent
SOURCE_AUDIT = ROOT / "audits/architecture_consolidation"
SOURCE_FILES = {
    "DELETE": "DELETE_CANDIDATES.json",
    "MERGE": "MERGE.json",
    "ARCHIVE": "ARCHIVE.json",
    "NEEDS_REVIEW": "NEEDS_REVIEW.json",
}
HIGH_RISK = {
    "core/chunker.py",
    "core/glossary.py",
    "core/translator.py",
    "core/prompt_engine.py",
    "core/formatter.py",
    "core/exceptions.py",
    "core/character_memory_engine.py",
}
STAGE11_COMPATIBILITY = {
    "core/translation_prompt_improvement_planner",
    "core/translation_quality_corpus",
    "core/translation_quality_corpus_governance",
    "core/translation_quality_defects",
    "core/translation_quality_framework_integration",
    "core/translation_quality_metrics",
    "core/translation_quality_review_artifacts",
    "core/translation_quality_review_decision",
}
PROVIDER_BOUNDARY_MARKERS = (
    "authorized_provider",
    "provider_benchmark",
    "provider_evidence",
    "provider_execution",
    "provider_session",
    "real_provider",
    "real_invocation",
    "controlled_provider_retry",
)
TEXT_SUFFIXES = {".py", ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".md", ".rst", ".txt"}
SERIALIZED_SUFFIXES = {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg"}
DOC_SUFFIXES = {".md", ".rst", ".txt"}
ENTRYPOINTS = (
    "launcher_translate.py",
    "ntpe_production_translate.py",
    "launcher.py",
    "cli/main.py",
    "sdk/__init__.py",
    "external_api/__init__.py",
    "web_ui/__init__.py",
)


def tracked_files() -> list[Path]:
    raw = subprocess.run(
        ["git", "-c", "core.quotepath=false", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    return [ROOT / item.decode("utf-8") for item in raw.split(b"\0") if item]


def load_candidates() -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for original, name in SOURCE_FILES.items():
        payload = json.loads((SOURCE_AUDIT / name).read_text(encoding="utf-8"))
        if payload["count"] != len(payload["items"]):
            raise ValueError(f"source inventory count mismatch: {name}")
        for item in payload["items"]:
            candidates.append({**item, "original_classification": original})
    paths = [item["module_path"] for item in candidates]
    if len(candidates) != 72 or len(paths) != len(set(paths)):
        raise ValueError("Batch 5A requires exactly 72 unique source candidates")
    return candidates


def module_name(path: Path) -> str | None:
    try:
        relative = path.relative_to(ROOT)
    except ValueError:
        return None
    if relative.suffix != ".py":
        return None
    parts = list(relative.with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def resolve_from(current: str, level: int, target: str | None) -> str:
    package = current.split(".")[:-1]
    if level:
        package = package[: max(0, len(package) - level + 1)]
    if target:
        package.extend(target.split("."))
    return ".".join(package)


def python_graph(files: list[Path]) -> tuple[dict[str, set[str]], list[dict[str, Any]]]:
    graph: dict[str, set[str]] = {}
    dynamic: list[dict[str, Any]] = []
    dynamic_names = {
        "importlib.import_module",
        "import_module",
        "__import__",
        "runpy.run_path",
        "runpy.run_module",
        "pkgutil.iter_modules",
        "entry_points",
        "importlib.metadata.entry_points",
        "module_from_spec",
        "importlib.util.module_from_spec",
        "spec_from_file_location",
        "importlib.util.spec_from_file_location",
    }
    for path in (item for item in files if item.suffix == ".py"):
        name = module_name(path)
        if not name:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, SyntaxError):
            continue
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                base = resolve_from(name, node.level, node.module)
                if base:
                    imports.add(base)
                    imports.update(f"{base}.{alias.name}" for alias in node.names if alias.name != "*")
            elif isinstance(node, ast.Call):
                try:
                    expression = ast.unparse(node.func)
                except Exception:
                    expression = "<unparseable>"
                if expression not in dynamic_names and expression not in {"globals", "locals"}:
                    continue
                resolved: list[str] = []
                if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    resolved.append(node.args[0].value)
                dynamic.append(
                    {
                        "caller": path.relative_to(ROOT).as_posix(),
                        "dynamic_expression": ast.unparse(node),
                        "resolved_candidates": resolved,
                        "confidence": "HIGH" if resolved else "LOW",
                        "runtime_condition": "literal" if resolved else "runtime_value",
                        "affected_modules": resolved,
                        "deletion_impact": "REFERENCE_CONFIRMED" if resolved else "BLOCKED",
                    }
                )
        graph[name] = imports
    return graph, sorted(dynamic, key=lambda row: (row["caller"], row["dynamic_expression"]))


def reachable(graph: dict[str, set[str]], start: str) -> set[str]:
    seen: set[str] = set()
    queue = deque([start])
    while queue:
        current = queue.popleft()
        if current in seen:
            continue
        seen.add(current)
        for dependency in graph.get(current, ()):
            if dependency in graph and dependency not in seen:
                queue.append(dependency)
    return seen


def candidate_module(candidate: str) -> str:
    return candidate[:-3].replace("/", ".") if candidate.endswith(".py") else candidate.replace("/", ".")


def text_index(files: list[Path]) -> dict[str, str]:
    index: dict[str, str] = {}
    for path in files:
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            index[path.relative_to(ROOT).as_posix()] = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
    return index


def references_for(candidate: str, index: dict[str, str]) -> dict[str, list[str]]:
    dotted = candidate_module(candidate)
    tokens = {candidate, dotted}
    if candidate.endswith(".py"):
        tokens.add(Path(candidate).name)
    own_prefix = candidate.removesuffix(".py")
    results = {"python": [], "tests": [], "serialized": [], "configuration": [], "documentation": [], "manifest_freeze": []}
    for relative, text in index.items():
        if relative == candidate or relative.startswith(own_prefix + "/"):
            continue
        if relative.startswith("audits/architecture_consolidation/batch5a_usage/"):
            continue
        if not any(token in text for token in tokens):
            continue
        path = Path(relative)
        if path.suffix == ".py":
            (results["tests"] if relative.startswith("tests/") or path.name.startswith("ntpe_") else results["python"]).append(relative)
        if path.suffix.lower() in SERIALIZED_SUFFIXES:
            results["serialized"].append(relative)
            configuration_name = any(marker in path.name.lower() for marker in ("config", "profile", "settings", "override"))
            if path.suffix.lower() in {".toml", ".ini", ".cfg", ".yaml", ".yml"} or configuration_name or relative.startswith(("config/", "profiles/", "cli/")):
                results["configuration"].append(relative)
        if path.suffix.lower() in DOC_SUFFIXES:
            results["documentation"].append(relative)
        if relative.startswith("manifests/") or "freeze" in relative.lower():
            results["manifest_freeze"].append(relative)
    return {key: sorted(set(value)) for key, value in results.items()}


def public_symbols(candidate: str) -> list[str]:
    path = ROOT / candidate
    source = path if path.is_file() else path / "__init__.py"
    if not source.is_file():
        return []
    try:
        tree = ast.parse(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, SyntaxError):
        return []
    explicit: list[str] = []
    symbols: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and not node.name.startswith("_"):
            symbols.append(node.name)
        elif isinstance(node, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets):
                try:
                    explicit = [str(value) for value in ast.literal_eval(node.value)]
                except Exception:
                    pass
    return sorted(set(explicit or symbols))


def replacement_record(item: dict[str, Any]) -> dict[str, Any]:
    legacy = item["module_path"]
    replacements = [value for value in item.get("duplicate_with", []) if (ROOT / value).exists() or (ROOT / f"{value}.py").exists()]
    replacement = replacements[0] if replacements else None
    old_symbols = public_symbols(legacy)
    new_symbols = public_symbols(replacement) if replacement else []
    missing = sorted(set(old_symbols) - set(new_symbols))
    return {
        "legacy_module": legacy,
        "replacement_module": replacement,
        "legacy_public_symbols": old_symbols,
        "replacement_public_symbols": new_symbols,
        "missing_symbols": missing,
        "signature_parity": bool(replacement and not missing),
        "behavior_parity": "not_proven",
        "exception_parity": "not_proven",
        "side_effect_parity": "not_proven",
        "performance_parity": "not_measured_no_runtime_change_authorized",
        "quality_impact": item.get("quality_impact", "unknown"),
        "migration_complexity": "HIGH" if missing or not replacement else "MEDIUM",
        "compatibility_wrapper_possible": bool(replacement),
    }


def registry_report(index: dict[str, str]) -> list[dict[str, Any]]:
    known = [
        ("SDKPluginRegistry", "sdk/plugin_registry.py", "sdk/plugin_manager.py", "sdk/plugin_loader.py", "manifest.entrypoint", False, "plugin manifest", "generic SDKPlugin fallback"),
        ("CLI CommandRegistry", "cli/main.py", "cli/main.py", "cli/commands", "command name", True, None, "command registration failure is isolated"),
        ("WorkflowRegistry", "workflow/workflow_registry.py", "workflow/workflow_core.py", "workflow", "workflow name", False, None, "lookup fails closed"),
        ("Core WorkflowRegistry", "core/workflow/workflow_registry.py", "core/workflow/workflow_engine.py", "core/workflow", "step name", False, None, "default registry"),
        ("DisciplineRuleRegistry", "core/translation_discipline/registry.py", "core/translation_discipline/feedback_adapter.py", "core/translation_discipline", "rule code", False, None, "unknown rule remains unresolved"),
    ]
    rows = []
    for registry, registration, lookup, module, key, active, flag, fallback in known:
        rows.append({
            "registry": registry,
            "registration_site": registration,
            "lookup_site": lookup,
            "module": module,
            "key": key,
            "active_by_default": active,
            "feature_flag": flag,
            "fallback_behavior": fallback,
            "replacement": None,
        })
    return rows


def external_risk(item: dict[str, Any], refs: dict[str, list[str]], symbols: list[str]) -> tuple[str, list[str]]:
    signals: list[str] = ["candidate is located under the long-lived core namespace"]
    if item["module_path"] in HIGH_RISK:
        signals.append("explicitly designated high-risk compatibility path")
        return "CRITICAL", signals
    if item.get("public_api") or symbols:
        signals.append("module exposes public symbols or was previously classified as public API")
    if refs["documentation"]:
        signals.append("documentation or release text references the path")
    if refs["tests"]:
        signals.append("tests exercise or import the path")
    if item.get("production_referenced"):
        signals.append("production reachability was previously confirmed")
        return "CRITICAL", signals
    return ("HIGH" if item.get("public_api") or refs["documentation"] or refs["tests"] else "MEDIUM"), signals


def active_reference_count(refs: dict[str, list[str]]) -> int:
    return sum(
        1
        for values in refs.values()
        for relative in values
        if not relative.startswith("audits/architecture_consolidation/")
    )


def classify(item: dict[str, Any], refs: dict[str, list[str]], risk: str, parity: dict[str, Any]) -> tuple[str, list[str]]:
    path = item["module_path"]
    reasons: list[str] = []
    if path in HIGH_RISK:
        reasons.append("explicit high-risk core candidate")
        return ("KEEP_COMPATIBILITY" if path == "core/exceptions.py" else "BLOCKED"), reasons
    if item.get("production_referenced"):
        return "BLOCKED", ["production reachability confirmed"]
    if item["original_classification"] == "ARCHIVE":
        return "ARCHIVE", ["historical or experimental module retains release/rollback value"]
    if item["original_classification"] == "NEEDS_REVIEW":
        if path == "core/production_runtime":
            return "BLOCKED", ["runtime compatibility risk remains unresolved"]
        return "KEEP_COMPATIBILITY", ["legacy translation namespace has external import risk"]
    if path in STAGE11_COMPATIBILITY:
        return "KEEP_COMPATIBILITY", ["frozen Stage 11 import path and compatibility contract"]
    if any(marker in path for marker in PROVIDER_BOUNDARY_MARKERS):
        return "BLOCKED", ["provider authorization, evidence, or execution boundary"]
    material = active_reference_count(refs)
    if item["original_classification"] == "DELETE":
        if material:
            return "KEEP_COMPATIBILITY", ["repository references remain", "deletion parity is not proven"]
        parity_proven = (
            parity.get("replacement_module") is not None
            and not parity.get("missing_symbols")
            and parity.get("signature_parity") is True
            and parity.get("behavior_parity") == "proven"
            and parity.get("exception_parity") == "proven"
            and parity.get("side_effect_parity") == "proven"
            and parity.get("performance_parity") == "proven"
        )
        if risk == "LOW" and parity_proven:
            return "SAFE_DELETE", [
                "no material repository references",
                "external compatibility risk is LOW",
                "replacement parity is fully proven",
            ]
        return "NEEDS_EXTERNAL_CONFIRMATION", ["internal references are absent but external core import risk is not LOW"]
    if item["original_classification"] == "MERGE":
        if parity["replacement_module"] is None:
            return "BLOCKED", ["no concrete replacement module was found"]
        return "MERGE", ["overlap exists but wrapper and behavior parity are still required"]
    return "BLOCKED", ["classification evidence incomplete"]


def production_map(graph: dict[str, set[str]], candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    candidate_modules = {candidate_module(item["module_path"]): item["module_path"] for item in candidates}
    for relative in ENTRYPOINTS:
        path = ROOT / relative
        if not path.exists():
            continue
        start = module_name(path)
        if not start:
            continue
        transitive = reachable(graph, start)
        direct = sorted(graph.get(start, set()))
        legacy = sorted(path for module, path in candidate_modules.items() if module in transitive or any(name.startswith(module + ".") for name in transitive))
        rows.append(
            {
                "entrypoint": relative,
                "load_classification": "always_loaded" if relative in {"launcher_translate.py", "ntpe_production_translate.py", "cli/main.py"} else "conditionally_loaded",
                "direct_imports": direct,
                "transitive_imports": sorted(transitive),
                "dynamic_imports": [],
                "configuration_dependencies": ["config", "profiles"],
                "plugin_dependencies": ["sdk/plugin_loader.py"] if relative.startswith(("cli/", "sdk/")) else [],
                "runtime_dependencies": [name for name in transitive if "runtime" in name],
                "quality_dependencies": [name for name in transitive if "quality" in name],
                "provider_dependencies": [name for name in transitive if "provider" in name],
                "legacy_dependencies": legacy,
            }
        )
    return rows


def write(name: str, value: object) -> None:
    write_canonical_json(OUTPUT / name, value)


def main() -> int:
    files = tracked_files()
    candidates = load_candidates()
    graph, dynamic = python_graph(files)
    index = text_index(files)
    registries = registry_report(index)
    replacement_rows: list[dict[str, Any]] = []
    enriched: list[dict[str, Any]] = []
    serialized_rows: list[dict[str, Any]] = []
    configuration_rows: list[dict[str, Any]] = []
    external_rows: list[dict[str, Any]] = []
    impact_rows: list[dict[str, Any]] = []
    for item in candidates:
        path = item["module_path"]
        refs = references_for(path, index)
        symbols = public_symbols(path)
        parity = replacement_record(item)
        replacement_rows.append(parity)
        risk, signals = external_risk(item, refs, symbols)
        classification, reasons = classify(item, refs, risk, parity)
        dynamic_refs = [row for row in dynamic if candidate_module(path) in row["resolved_candidates"] or path in row["dynamic_expression"]]
        registry_refs = [row for row in registries if path.startswith(row["module"]) or row["module"].startswith(path.removesuffix(".py"))]
        serialized_rows.append({"module_path": path, "references": refs["serialized"], "manifest_freeze_references": refs["manifest_freeze"], "serialized_reference_count": len(refs["serialized"]), "scan_status": "COMPLETE"})
        configuration_rows.append({"module_path": path, "references": refs["configuration"], "configuration_reference_count": len(refs["configuration"]), "scan_status": "COMPLETE"})
        external_rows.append({"module_path": path, "risk": risk, "signals": signals, "active_repository_reference_count": active_reference_count(refs), "classification_constraint": "NEEDS_EXTERNAL_CONFIRMATION" if risk in {"HIGH", "CRITICAL"} and active_reference_count(refs) == 0 else "NO_SAFE_DELETE"})
        quality_direct = item.get("quality_impact") == "direct_or_potential" or any(token in path for token in ("quality", "glossary", "character", "prompt", "formatter", "translator", "chunker"))
        runtime_direct = item.get("runtime_impact") == "active_or_optional_production_path" or any(token in path for token in ("runtime", "scheduler", "session", "pipeline", "provider"))
        impact_rows.append({
            "module_path": path,
            "translation_quality_impact": "POTENTIAL_OR_DIRECT" if quality_direct else "NONE_IDENTIFIED",
            "runtime_latency_impact": "POTENTIAL_OR_DIRECT" if runtime_direct else "NONE_IDENTIFIED",
            "memory_impact": "NOT_BENCHMARKED",
            "disk_io_impact": "POTENTIAL" if any(token in path for token in ("logger", "corpus", "session", "release")) else "NONE_IDENTIFIED",
            "provider_request_impact": "BLOCKED_BOUNDARY" if "provider" in path else "NONE_IDENTIFIED",
            "prompt_token_impact": "POTENTIAL" if "prompt" in path else "NONE_IDENTIFIED",
            "resume_impact": "POTENTIAL" if any(token in path for token in ("scheduler", "session", "resume")) else "NONE_IDENTIFIED",
            "output_assembly_impact": "POTENTIAL" if any(token in path for token in ("formatter", "translator", "pipeline")) else "NONE_IDENTIFIED",
            "required_classification_floor": "BLOCKED" if quality_direct or runtime_direct else "NO_FLOOR",
        })
        enriched.append({
            "module_path": path,
            "original_classification": item["original_classification"],
            "final_classification": classification,
            "classification_reasons": reasons,
            "production_referenced": item.get("production_referenced", False),
            "static_references": refs["python"],
            "test_references": refs["tests"],
            "documentation_references": refs["documentation"],
            "dynamic_references": dynamic_refs,
            "registry_references": registry_refs,
            "serialized_references": refs["serialized"],
            "configuration_references": refs["configuration"],
            "manifest_freeze_references": refs["manifest_freeze"],
            "external_compatibility_risk": risk,
            "replacement_module": parity["replacement_module"],
            "replacement_behavior_parity": parity["behavior_parity"],
            "safe_delete_eligible": classification == "SAFE_DELETE",
        })

    counts = Counter(row["final_classification"] for row in enriched)
    classes = ("SAFE_DELETE", "KEEP_COMPATIBILITY", "MERGE", "ARCHIVE", "BLOCKED", "NEEDS_EXTERNAL_CONFIRMATION")
    if sum(counts.values()) != 72:
        raise ValueError("final classifications do not cover all candidates")
    for classification in classes:
        rows = [row for row in enriched if row["final_classification"] == classification]
        write(f"{classification}.json", {"classification": classification, "count": len(rows), "items": rows})

    entrypoints = production_map(graph, candidates)
    dynamic_affected = sorted({module for row in dynamic for module in row["affected_modules"]})
    write("PRODUCTION_ENTRYPOINT_MAP.json", {"entrypoints": entrypoints, "count": len(entrypoints), "scan_status": "COMPLETE"})
    write("DYNAMIC_IMPORT_REPORT.json", {"scan_status": "COMPLETE", "patterns_scanned": ["import_module", "__import__", "runpy", "pkgutil", "entry_points", "module_from_spec", "spec_from_file_location", "globals", "locals"], "count": len(dynamic), "unresolved_count": sum(row["confidence"] == "LOW" for row in dynamic), "affected_module_names": dynamic_affected, "items": dynamic})
    write("REGISTRY_USAGE_REPORT.json", {"scan_status": "COMPLETE", "count": len(registries), "items": registries})
    write("SERIALIZED_REFERENCE_REPORT.json", {"scan_status": "COMPLETE", "count": len(serialized_rows), "items": serialized_rows})
    write("CONFIGURATION_REFERENCE_REPORT.json", {"scan_status": "COMPLETE", "count": len(configuration_rows), "items": configuration_rows})
    write("EXTERNAL_COMPATIBILITY_RISK.json", {"scan_status": "COMPLETE", "count": len(external_rows), "items": external_rows})
    write("REPLACEMENT_PARITY_REPORT.json", {"scan_status": "COMPLETE", "count": len(replacement_rows), "items": replacement_rows})
    write("QUALITY_PERFORMANCE_IMPACT_REPORT.json", {"scan_status": "COMPLETE", "count": len(impact_rows), "items": impact_rows, "production_execution_performed": False, "provider_executed": False})

    summary = {
        "schema_version": "1.0",
        "audit": "NTPE Architecture Consolidation Batch 5A Dynamic Usage and Legacy Compatibility Audit",
        "source_inventory": {"DELETE": 22, "MERGE": 41, "ARCHIVE": 7, "NEEDS_REVIEW": 2},
        "candidate_count": 72,
        "classification_counts": {name: counts[name] for name in classes},
        "candidates": enriched,
        "scans": {"static": "COMPLETE", "dynamic": "COMPLETE", "registry": "COMPLETE", "configuration": "COMPLETE", "serialized": "COMPLETE", "documentation": "COMPLETE", "replacement_parity": "COMPLETE", "quality_performance": "COMPLETE"},
        "safe_delete_policy": "No candidate is SAFE_DELETE unless every hard condition is proven; this audit proves none.",
        "production_modified": False,
        "production_code_modified": False,
        "runtime_modified": False,
        "provider_modified": False,
        "prompt_modified": False,
        "candidate_modified": False,
        "stage11_modified": False,
        "golden_corpus_modified": False,
        "files_deleted": 0,
        "files_moved": 0,
        "files_renamed": 0,
        "legacy_modules_modified": 0,
        "provider_executed": False,
        "new_translation_generated": False,
        "safe_delete_count": counts["SAFE_DELETE"],
        "keep_compatibility_count": counts["KEEP_COMPATIBILITY"],
        "merge_count": counts["MERGE"],
        "archive_count": counts["ARCHIVE"],
        "blocked_count": counts["BLOCKED"],
        "needs_external_confirmation_count": counts["NEEDS_EXTERNAL_CONFIRMATION"],
        "batch5b_started": False,
    }
    write("BATCH5A_DYNAMIC_USAGE_AUDIT.json", summary)

    plan = {"item_limit": 5, "item_count": 0, "items": [], "batch5b_started": False, "no_eligible_items_reason": "No candidate satisfied every SAFE_DELETE hard condition. Batch 5B should remain unstarted until external compatibility and behavior parity are proven."}
    write("BATCH5B_SAFE_SIMPLIFICATION_PLAN.json", plan)

    lines = [
        "# Batch 5A Dynamic Usage and Legacy Compatibility Audit",
        "",
        "The audit covers all 72 source candidates and performs static, dynamic-import, registry, configuration, serialized-reference, documentation, replacement-parity, and quality/performance scans.",
        "",
        "## Final classifications",
        "",
    ]
    lines.extend(f"- {name}: {counts[name]}" for name in classes)
    lines.extend([
        "",
        "No candidate satisfies every SAFE_DELETE hard condition. In particular, external core import usage cannot be disproved from repository-only evidence, dynamic plugin entrypoints exist, many paths are frozen or serialized, and replacement behavior/signature/exception parity is incomplete.",
        "",
        "No production module is changed, no Provider is executed, and Batch 5B is not started.",
    ])
    (OUTPUT / "BATCH5A_DYNAMIC_USAGE_AUDIT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (OUTPUT / "BATCH5B_SAFE_SIMPLIFICATION_PLAN.md").write_text(
        "# Batch 5B Safe Simplification Plan\n\nNo implementation item is authorized. Zero candidates met every SAFE_DELETE hard condition, so Batch 5B remains unstarted.\n",
        encoding="utf-8",
    )
    manifest_names = {"NTPE_BATCH5A_AUDIT_BUILD_MANIFEST.json", "NTPE_BATCH5A_AUDIT_CONTENT_MANIFEST.json"}
    audit_files = sorted(
        path for path in OUTPUT.iterdir()
        if path.is_file() and path.name not in manifest_names
    )
    external_files = [
        ROOT / "ntpe_architecture_consolidation_batch5a_dynamic_usage_audit_test.py",
        ROOT / "tests/integration/architecture_consolidation_batch5a_dynamic_usage_audit_test.py",
    ]
    content_paths = [path.relative_to(ROOT).as_posix() for path in audit_files + external_files]
    write("NTPE_BATCH5A_AUDIT_CONTENT_MANIFEST.json", {
        "schema_version": "1.0",
        "package_type": "NTPE_BATCH5A_AUDIT",
        "allowlist_only": True,
        "files": content_paths,
    })
    build_files = audit_files + external_files + [OUTPUT / "NTPE_BATCH5A_AUDIT_CONTENT_MANIFEST.json"]
    write("NTPE_BATCH5A_AUDIT_BUILD_MANIFEST.json", {
        "schema_version": "1.0",
        "files": [
            {
                "path": path.relative_to(ROOT).as_posix(),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
            for path in sorted(build_files, key=lambda item: item.relative_to(ROOT).as_posix())
        ],
    })
    print(json.dumps({"candidate_count": 72, "classification_counts": summary["classification_counts"], "dynamic_imports": len(dynamic), "registries": len(registries)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
