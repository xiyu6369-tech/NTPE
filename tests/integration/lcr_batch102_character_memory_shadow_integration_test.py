from __future__ import annotations

import json
from pathlib import Path

import core.lcr_production_shadow_hook as lcr

from tests.unit.test_lcr_character_memory_shadow import ENABLED, T1, package, store_with_selection_cases


ROOT = Path(__file__).resolve().parents[2]


def test_batch102_end_to_end_harness_only_store_injection():
    store = store_with_selection_cases()
    store_before = json.dumps(store.to_dict(), ensure_ascii=False, sort_keys=True)
    production = package()
    production_before = json.dumps(production, ensure_ascii=False, sort_keys=True)
    sink = lcr.InMemoryEvidenceSink()
    outcome = lcr.run_read_only_lcr_shadow_hook(
        production, feature_flags=ENABLED, evidence_sink=sink,
        character_memory_store=store, character_ids=("char-1",),
        character_memory_snapshot_id="snapshot-integration", created_at_factory=lambda: T1,
    )
    assert outcome.status == "completed" and outcome.baseline_continues
    assert len(sink.records) == 1 and sink.records[0].character_memory
    character = sink.records[0].character_memory
    assert character.selected_count >= 1 and character.estimated_tokens <= 128
    assert not character.memory_injected and not character.cache_identity_applied
    assert sink.records[0].provider_requests_executed == 0
    assert not sink.records[0].production_output_changed
    assert json.dumps(store.to_dict(), ensure_ascii=False, sort_keys=True) == store_before
    assert json.dumps(production, ensure_ascii=False, sort_keys=True) == production_before


def test_production_wrapper_and_frozen_lcr_cores_are_not_modified():
    import subprocess
    changed = subprocess.run(["git", "diff", "--name-only"], cwd=ROOT, check=True,
        capture_output=True, text=True, encoding="utf-8").stdout.splitlines()
    forbidden = {
        "core/adaptive_context_runtime_shadow/hook.py", "core/character_memory_v2",
        "core/context_scene_memory", "core/chunk_cache_v2", "core/dual_pass_translation",
        "core/semantic_verification", "core/multilingual_profiles", "core/provider_routing",
    }
    assert not [path for path in changed if path in forbidden or any(path.startswith(item + "/") for item in forbidden)]
    text = (ROOT / "core/adaptive_context_runtime_shadow/hook.py").read_text(encoding="utf-8")
    assert text.count("run_read_only_lcr_shadow_hook(package)") == 1
