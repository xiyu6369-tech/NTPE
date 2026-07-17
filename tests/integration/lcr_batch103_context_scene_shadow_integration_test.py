from __future__ import annotations

import json
import subprocess
from pathlib import Path

import core.lcr_production_shadow_hook as lcr
from tests.unit.test_lcr_context_scene_shadow import ENABLED, T2, context_store, package


ROOT = Path(__file__).resolve().parents[2]


def test_batch103_end_to_end_harness_only_snapshot_injection():
    store, previous_hash = context_store()
    store_before = json.dumps(store.to_dict(), ensure_ascii=False, sort_keys=True)
    production = package()
    production_before = json.dumps(production, ensure_ascii=False, sort_keys=True)
    sink = lcr.InMemoryEvidenceSink()
    outcome = lcr.run_read_only_lcr_shadow_hook(
        production, feature_flags=ENABLED, evidence_sink=sink, context_scene_store=store,
        context_scene_snapshot_id="snapshot-integration", chapter_id="chapter-1", scene_id="scene-1",
        sequence_index=5, character_ids=("char-present", "char-mentioned"),
        previous_translation_allowed=True, expected_previous_translation_hash=previous_hash,
        created_at_factory=lambda: T2,
    )
    assert outcome.status == "completed" and outcome.baseline_continues
    assert len(sink.records) == 1 and sink.records[0].context_scene
    result = sink.records[0].context_scene
    assert result.selected_records >= 1 and result.estimated_tokens <= 256
    assert not result.context_injected and not result.previous_translation_injected
    assert not result.scene_state_applied and not result.cache_identity_applied
    assert sink.records[0].provider_requests_executed == 0
    assert not sink.records[0].production_output_changed
    assert json.dumps(store.to_dict(), ensure_ascii=False, sort_keys=True) == store_before
    assert json.dumps(production, ensure_ascii=False, sort_keys=True) == production_before


def test_production_wrapper_and_frozen_lcr_cores_are_not_modified():
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
