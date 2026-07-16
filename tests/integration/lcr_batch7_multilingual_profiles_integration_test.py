from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

import core.multilingual_profiles as mp

ROOT = Path(__file__).resolve().parents[2]


def test_three_profiles_share_runtime_contract_but_not_language_rules():
    profiles = mp.list_language_profiles()
    assert len(profiles) == 3 and len({p.source_language for p in profiles}) == 3
    assert len({p.source_rules for p in profiles}) == 3
    assert all(p.target_rules is mp.COMMON_TARGET_POLICY for p in profiles)


def test_character_and_context_memory_interoperability_is_read_only():
    for p in mp.list_language_profiles():
        character = mp.build_character_memory_hints(p); context = mp.build_context_scene_hints(p)
        assert character["human_approved_priority"] and not character["creates_approved_memory"]
        assert context["scene_memory_remains_authority"] and not context["forces_reference_resolution"]


def test_cache_polish_and_verification_stale_on_profile_change():
    p = mp.get_language_profile("literary-ja-zh-hant")
    old = mp.build_cache_profile_identity(p)
    changed = replace(p, semantic_hints=replace(p.semantic_hints, ambiguity_markers=p.semantic_hints.ambiguity_markers + ("不確定",)), fingerprint="")
    changed = replace(changed, fingerprint=mp.build_language_profile_fingerprint(changed))
    new = mp.build_cache_profile_identity(changed)
    assert old != new
    assert mp.build_polish_profile_view(p)["profile_identity"] != mp.build_polish_profile_view(changed)["profile_identity"]
    assert mp.build_verification_profile_identity(p) != mp.build_verification_profile_identity(changed)


def test_batch6_hints_are_data_only_and_fail_closed_authority_unchanged():
    hints = mp.build_semantic_verification_hints(mp.get_language_profile("literary-en-zh-hant"))
    assert hints["origin"] == "rule_derived" and hints["verification_authority"] == "LCR Batch 6" and not hints["can_decide_pass"]
    assert not {"status", "decision", "accept_polish"} & set(hints)


def test_fixture_is_synthetic_and_not_tic_corpus():
    payload = json.loads((ROOT / "tests/fixtures/lcr_batch7/language_profile_cases.json").read_text(encoding="utf-8"))
    assert payload["fixture_kind"] == "synthetic language-profile fixture"
    assert not payload["human_approved_translation_corpus"] and not payload["new_translation_generated"]
    assert set(payload["cases"]) == {"ko", "ja", "en"}


def test_frozen_lcr_cores_and_production_paths_not_modified():
    import subprocess
    lines = subprocess.run(["git", "status", "--short"], cwd=ROOT, check=True, capture_output=True, text=True, encoding="utf-8").stdout.splitlines()
    allowed = ("core/multilingual_profiles/", "tests/unit/test_multilingual_profiles.py", "tests/integration/lcr_batch7_multilingual_profiles_integration_test.py", "tests/fixtures/lcr_batch7/", "ntpe_lcr_batch7_multilingual_profiles_test.py", "audits/legacy_capability_recovery/batch7/", "NTPE_LCR_BATCH7_AUDIT.zip")
    assert all(line[3:].replace("\\", "/").strip('"').startswith(allowed) for line in lines)
