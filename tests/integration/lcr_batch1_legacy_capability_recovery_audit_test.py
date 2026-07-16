from __future__ import annotations

import importlib.util
import json
from functools import lru_cache
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "audits" / "legacy_capability_recovery" / "batch1"
SOURCE = ROOT / "audits" / "legacy_capability_recovery" / "source_material"
SPEC = importlib.util.spec_from_file_location("lcr_batch1_root", ROOT / "ntpe_lcr_batch1_legacy_capability_recovery_audit_test.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def data(name: str):
    return json.loads((AUDIT / name).read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def validated():
    return MODULE.run_validation()


def test_legacy_source_ingestion_and_redaction():
    assert validated()["legacy_capabilities"] >= 25
    assert "[REDACTED_API_KEY]" in (SOURCE / "translate_realtime_v2_legacy.txt").read_text(encoding="utf-8")


def test_capability_extraction_uses_real_symbols():
    inventory = data("LEGACY_CAPABILITY_INVENTORY.json")
    symbols = " ".join(row["legacy_symbol"] for row in inventory)
    assert "update_character_memory_via_ai" in symbols
    assert "realtime_compile" in symbols


def test_current_legacy_comparison_is_complete():
    assert validated()["current_capabilities"] == 16


def test_decision_matrix_is_complete():
    matrix = data("LCR_CAPABILITY_DECISION_MATRIX.json")
    assert len(matrix) == validated()["legacy_capabilities"]


def test_character_memory_v2_design_is_not_implemented():
    design = data("CHARACTER_MEMORY_V2_DESIGN.json")
    assert design["implemented"] is False and design["rules"]["rollback_required"] is True


def test_chunk_cache_v2_design_rejects_partial_output():
    design = data("CHUNK_CACHE_V2_DESIGN.json")
    assert design["partial_output_completed"] is False


def test_dual_pass_modes_and_semantic_rollback():
    design = data("DUAL_PASS_RECOVERY_DESIGN.json")
    assert set(design["modes"]) == {"single_pass", "dual_pass", "selective_polish"}
    assert all(mode["semantic_rollback"] for mode in design["modes"].values())


def test_multilingual_profile_coverage():
    profiles = data("MULTILINGUAL_RECOVERY_IMPACT.json")["profiles"]
    assert profiles["target"] == "zh-Hant" and all(profiles[lang] for lang in ("ko", "ja", "en"))


def test_secret_scan_has_no_credential_values():
    assert validated()["secret_scanned_files"] >= 17


def test_production_runtime_provider_prompt_and_tic_hashes_are_frozen():
    assert set(validated()["hash_groups"]) == {"production", "runtime", "provider", "prompt", "tic_batch7"}


def test_no_provider_or_network_execution():
    boundaries = data("LCR_BATCH1_AUDIT.json")["boundaries"]
    assert boundaries["provider_executed"] is False and boundaries["network_requests"] == 0


def test_batch2_not_started_and_git_allowlist_only():
    boundaries = data("LCR_BATCH1_AUDIT.json")["boundaries"]
    assert boundaries["lcr_batch2_started"] is False
    assert validated()["changed_paths"]
