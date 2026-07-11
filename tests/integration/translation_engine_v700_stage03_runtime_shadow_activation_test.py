from __future__ import annotations

import os
from pathlib import Path

import lts.txt_translation_runtime as runtime
from core.adaptive_context_integration.utils import canonical_hash
from core.adaptive_context_runtime_shadow import (
    clear_shadow_records,
    install_txt_runtime_shadow_hook,
    shadow_records,
    uninstall_txt_runtime_shadow_hook,
)


def _options(tmp_path: Path) -> runtime.TxtTranslationOptions:
    return runtime.TxtTranslationOptions(input_path=tmp_path / "sample.txt", output_dir=tmp_path / "out")


def _build(tmp_path: Path) -> dict:
    return runtime.build_prompt_package(
        options=_options(tmp_path),
        chunk_text="정태의는 창밖을 보았다. 일라이는 문가에 서 있었다.",
        chunk_index=1,
        chunk_total=1,
        locked_dictionary={"정태의": "鄭泰義", "일라이": "伊萊"},
        previous_context="그들은 전날 늦게까지 이야기를 나누었다.",
    )


def test_shadow_hook_preserves_exact_prompt_package(tmp_path, monkeypatch):
    monkeypatch.setattr(runtime, "now_iso", lambda: "2026-07-12T00:00:00+00:00")
    uninstall_txt_runtime_shadow_hook()
    monkeypatch.setenv("NTPE_TE_V7_ACE_MODE", "disabled")
    baseline = _build(tmp_path)

    clear_shadow_records()
    assert install_txt_runtime_shadow_hook() is True
    assert install_txt_runtime_shadow_hook() is False
    monkeypatch.setenv("NTPE_TE_V7_ACE_MODE", "shadow")
    shadow = _build(tmp_path)

    assert shadow == baseline
    assert canonical_hash(shadow) == canonical_hash(baseline)
    records = shadow_records()
    assert len(records) == 1
    assert records[0].payload_equivalent is True
    assert records[0].provider_calls_added == 0
    assert "정태의" not in repr(records[0].to_dict())


def test_disabled_hook_emits_no_record(tmp_path, monkeypatch):
    monkeypatch.setattr(runtime, "now_iso", lambda: "2026-07-12T00:00:00+00:00")
    install_txt_runtime_shadow_hook()
    clear_shadow_records()
    monkeypatch.setenv("NTPE_TE_V7_ACE_MODE", "disabled")
    _build(tmp_path)
    assert shadow_records() == ()


def test_txt_dry_run_activates_shadow_without_provider(tmp_path, monkeypatch):
    root = tmp_path / "NTPE"
    root.mkdir()
    source = root / "input.txt"
    source.write_text("정태의는 창밖을 보았다.\n일라이는 방 안으로 들어왔다.\n", encoding="utf-8")
    monkeypatch.setenv("NTPE_TE_V7_ACE_MODE", "shadow")
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    install_txt_runtime_shadow_hook()
    clear_shadow_records()

    result = runtime.translate_txt(
        runtime.TxtTranslationOptions(input_path=source, output_dir=root / "out", dry_run=True),
        root=root,
    )
    assert result["status"] == "success"
    assert len(shadow_records()) >= 1
    assert all(record.provider_calls_added == 0 for record in shadow_records())
