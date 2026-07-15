from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import socket

import pytest


ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "audits/architecture_consolidation/batch5a_usage"
GENERATOR = AUDIT / "generate_batch5a_audit.py"
BOUNDARIES = (ROOT / "launcher_translate.py", ROOT / "ntpe_production_translate.py", ROOT / "core/translation_runtime", ROOT / "core/ai_provider", ROOT / "core/prompt_compiler")


def load(name: str) -> dict:
    return json.loads((AUDIT / name).read_text(encoding="utf-8"))


def digest_boundaries() -> dict[str, str]:
    rows: dict[str, str] = {}
    for base in BOUNDARIES:
        files = [base] if base.is_file() else [path for path in base.rglob("*") if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"]
        for path in files:
            rows[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return rows


def test_entrypoint_dynamic_and_registry_scans_fail_closed_without_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def blocked(*args: object, **kwargs: object) -> None:
        raise AssertionError("network access attempted")
    monkeypatch.setattr(socket, "create_connection", blocked)
    before = digest_boundaries()
    entrypoints = load("PRODUCTION_ENTRYPOINT_MAP.json")
    assert entrypoints["scan_status"] == "COMPLETE"
    assert {"launcher_translate.py", "ntpe_production_translate.py"}.issubset(row["entrypoint"] for row in entrypoints["entrypoints"])
    dynamic = load("DYNAMIC_IMPORT_REPORT.json")
    assert dynamic["scan_status"] == "COMPLETE" and dynamic["unresolved_count"] > 0
    assert any(row["deletion_impact"] == "BLOCKED" for row in dynamic["items"] if row["confidence"] == "LOW")
    registry = load("REGISTRY_USAGE_REPORT.json")
    assert registry["scan_status"] == "COMPLETE"
    assert any(row["registry"] == "SDKPluginRegistry" and row["registration_site"] == "sdk/plugin_registry.py" for row in registry["items"])
    assert digest_boundaries() == before


def test_serialized_configuration_and_high_risk_evidence_are_preserved() -> None:
    serialized = {row["module_path"]: row for row in load("SERIALIZED_REFERENCE_REPORT.json")["items"]}
    configuration = {row["module_path"]: row for row in load("CONFIGURATION_REFERENCE_REPORT.json")["items"]}
    assert serialized["core/translation_scheduler"]["serialized_reference_count"] > 0
    assert configuration["core/adaptive_context_profile_budget"]["configuration_reference_count"] > 0
    safe = {row["module_path"] for row in load("SAFE_DELETE.json")["items"]}
    assert not safe.intersection({"core/chunker.py", "core/glossary.py", "core/translator.py", "core/prompt_engine.py", "core/formatter.py", "core/exceptions.py", "core/character_memory_engine.py"})


def test_fully_proven_zero_reference_fixture_can_be_safe_delete() -> None:
    spec = importlib.util.spec_from_file_location("batch5a_generator", GENERATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    item = {"module_path": "core/synthetic_legacy.py", "original_classification": "DELETE", "production_referenced": False}
    refs = {name: [] for name in ("python", "tests", "config", "serialized", "docs", "manifest_freeze")}
    parity = {"replacement_module": "core.synthetic", "missing_symbols": [], "signature_parity": True, "behavior_parity": "proven", "exception_parity": "proven", "side_effect_parity": "proven", "performance_parity": "proven"}
    classification, reasons = module.classify(item, refs, "LOW", parity)
    assert classification == "SAFE_DELETE"
    assert "replacement parity is fully proven" in reasons


def test_all_json_reports_parse_and_inventory_is_consistent() -> None:
    for path in AUDIT.glob("*.json"):
        assert isinstance(json.loads(path.read_text(encoding="utf-8")), dict)
    classes = ("SAFE_DELETE", "KEEP_COMPATIBILITY", "MERGE", "ARCHIVE", "BLOCKED", "NEEDS_EXTERNAL_CONFIRMATION")
    rows = [row for name in classes for row in load(f"{name}.json")["items"]]
    assert len(rows) == 72
    assert len({row["module_path"] for row in rows}) == 72
    assert sum(load(f"{name}.json")["count"] for name in classes) == 72
