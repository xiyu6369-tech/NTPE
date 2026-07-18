from __future__ import annotations

import subprocess
from pathlib import Path

import core.character_memory_v2 as cm
import core.context_scene_memory as cs
import lts.txt_translation_runtime as runtime
from core.translation_quality_integration_v72 import PromptBudget, QualityIntegrationFlags, apply_to_prompt_package
from lts.batch_translation_runtime import BatchTranslationOptions, build_txt_options


ROOT = Path(__file__).resolve().parents[2]


def _options(**overrides) -> runtime.TxtTranslationOptions:
    values = {"input_path": Path("novel.txt"), "output_dir": Path("output")}
    values.update(overrides)
    return runtime.TxtTranslationOptions(**values)


def _package(options=None):
    return runtime.build_prompt_package(
        options=options or _options(),
        chunk_text="영희가 말했다.",
        chunk_index=1,
        chunk_total=2,
        locked_dictionary={"영희": "英熙"},
        previous_context="그녀는 서재에 있었다.",
    )


def test_all_flags_false_preserve_runtime_package_identity_and_value(monkeypatch) -> None:
    monkeypatch.setattr(runtime, "now_iso", lambda: "2026-07-19T00:00:00Z")
    baseline = _package(_options())
    explicit_false = _package(_options(
        quality_integration_v72=False,
        quality_character_memory_v72=False,
        quality_context_scene_v72=False,
        quality_naturalness_v72=False,
    ))
    assert explicit_false == baseline
    assert apply_to_prompt_package(baseline, flags=QualityIntegrationFlags()) is baseline


def test_naturalness_only_changes_prompt_not_provider_resume_or_output_contract() -> None:
    baseline = _package()
    enabled = _package(_options(quality_naturalness_v72=True))
    assert enabled["prompt"]["user_prompt"] != baseline["prompt"]["user_prompt"]
    assert "自然度政策" in enabled["prompt"]["user_prompt"]
    for key in ("model_profile", "runtime", "source", "session"):
        assert enabled[key] == baseline[key]
    meta = enabled["prompt_runtime"]["translation_quality_integration_v72"]
    assert meta["provider_requests_added"] == 0 and meta["network_requests_added"] == 0
    assert meta["resume_changed"] is False and meta["output_changed"] is False


def test_kill_switch_restores_baseline_prompt() -> None:
    baseline = _package()
    killed = _package(_options(quality_integration_v72=True, quality_integration_kill_switch_v72=True))
    assert killed == baseline


def test_tight_budget_preserves_complete_source() -> None:
    enabled = _package(_options(
        quality_naturalness_v72=True,
        quality_prompt_budget_v72=PromptBudget(total_prompt_tokens=1, character_tokens=0, context_tokens=0, scene_tokens=0, naturalness_tokens=0),
    ))
    assert enabled["source"]["chunk_text"] == "영희가 말했다."
    assert enabled["prompt"]["user_prompt"].count("영희가 말했다.") == 1


def test_batch_options_propagate_all_quality_flags() -> None:
    batch = BatchTranslationOptions(
        input_dir=Path("input"),
        output_dir=Path("output"),
        quality_integration_v72=True,
        quality_character_memory_v72=True,
        quality_context_scene_v72=True,
        quality_naturalness_v72=True,
        quality_integration_kill_switch_v72=True,
    )
    txt = build_txt_options(Path("input/a.txt"), Path("output"), batch)
    assert txt.quality_integration_v72 and txt.quality_character_memory_v72
    assert txt.quality_context_scene_v72 and txt.quality_naturalness_v72
    assert txt.quality_integration_kill_switch_v72


def test_cli_exposes_default_off_independent_and_global_flags() -> None:
    from ntpe_production_translate import build_parser

    parser = build_parser()
    default = parser.parse_args(["txt", "novel.txt", "output", "--dry-run"])
    enabled = parser.parse_args([
        "txt", "novel.txt", "output", "--dry-run",
        "--quality-character-memory-v72", "--quality-context-scene-v72", "--quality-naturalness-v72",
    ])
    assert not default.quality_integration_v72 and not default.quality_naturalness_v72
    assert enabled.quality_character_memory_v72 and enabled.quality_context_scene_v72 and enabled.quality_naturalness_v72


def test_frozen_sources_match_head() -> None:
    frozen = [
        ROOT / "core/character_memory_v2",
        ROOT / "core/context_scene_memory",
        ROOT / "core/literary/literary_prompt_builder.py",
        ROOT / "core/literary_prompt_quality_candidate_v72",
    ]
    paths = []
    for item in frozen:
        paths.extend(sorted(item.glob("*.py")) if item.is_dir() else [item])
    for path in paths:
        relative = path.relative_to(ROOT).as_posix()
        head = subprocess.run(["git", "show", f"HEAD:{relative}"], cwd=ROOT, check=True, capture_output=True).stdout
        assert path.read_bytes() == head


def test_adapter_is_provider_network_resume_output_free_by_static_boundary() -> None:
    module = (ROOT / "core/translation_quality_integration_v72/adapter.py").read_text(encoding="utf-8")
    forbidden_imports = ("import requests", "import httpx", "import socket", "ProviderManager", "NVIDIA_API_KEY")
    assert not any(value in module for value in forbidden_imports)
    assert "provider_requests_added\": 0" in module and "network_requests_added\": 0" in module

