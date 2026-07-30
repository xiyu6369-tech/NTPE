from __future__ import annotations

import os
import tempfile
from pathlib import Path

from ntpe_production_translate import _apply_runtime_timeout_env, build_parser
from lts.txt_translation_runtime import (
    TxtTranslationOptions,
    _effective_provider_timeout,
    format_translation_output,
    save_partial_translation_output,
)
from core.translation_engine.translation_engine import TranslationEngine
from core.translation_runtime.runtime_qa import analyze_runtime_quality


def _package(chars: int = 575) -> dict:
    return {"source": {"char_count": chars}, "runtime": {"provider_attempt": 1}}


def test_cli_api_timeout_is_authoritative_for_short_chunks() -> None:
    old_env = dict(os.environ)
    try:
        os.environ.pop("NTPE_SHORT_CHUNK_FIRST_TIMEOUT", None)
        os.environ.pop("NTPE_RETRY_TIMEOUT", None)
        args = build_parser().parse_args([
            "regression",
            "--set",
            "golden",
            "--stage",
            "TER-v2.4-test",
            "--api-timeout",
            "180",
        ])
        _apply_runtime_timeout_env(args)
        assert os.environ.get("NTPE_API_TIMEOUT_EXPLICIT") == "1"
        assert _effective_provider_timeout(_package(), 1) == 180
        assert _effective_provider_timeout(_package(), 2) == 180
    finally:
        os.environ.clear()
        os.environ.update(old_env)


def test_engine_respects_current_runtime_timeout_without_second_clamp() -> None:
    old_env = dict(os.environ)
    try:
        os.environ["NTPE_CURRENT_API_TIMEOUT"] = "180"
        os.environ["NTPE_SHORT_CHUNK_FIRST_TIMEOUT"] = "90"
        engine = TranslationEngine(root=Path.cwd())
        assert engine._get_timeout({"source": {"char_count": 575}, "runtime": {"provider_attempt": 1}}) == 180
    finally:
        os.environ.clear()
        os.environ.update(old_env)


def test_dialogue_quotes_are_normalized_and_gate_detects_unformatted_output() -> None:
    raw = '他低聲說：“……但現在擔心也無濟於事。” 然後補了一句 "走吧。"'
    formatted = format_translation_output(raw)
    assert '“' not in formatted and '”' not in formatted and '"' not in formatted
    assert '「……但現在擔心也無濟於事。」' in formatted
    assert '「走吧。」' in formatted

    qa = analyze_runtime_quality("그는 말했다.", raw, extra_violations=[])
    assert qa["passed"] is False
    assert any(issue["code"] == "DIALOGUE_QUOTE_FORMAT" for issue in qa["issues"])


def test_partial_translation_is_preserved_on_failure() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        options = TxtTranslationOptions(input_path=Path("original_ko.txt"), output_dir=out)
        partial = save_partial_translation_output(
            output_dir=out,
            input_path=Path("original_ko.txt"),
            translated_chunks=["第一段譯文。", "第二段譯文。"],
            records=[{"chunk_index": 1, "status": "success"}],
            failed_chunk=3,
            error="provider timeout",
            options=options,
        )
        partial_output = Path(partial["partial_output"])
        partial_manifest = Path(partial["partial_manifest"])
        assert partial_output.exists()
        assert partial_manifest.exists()
        assert "第一段譯文" in partial_output.read_text(encoding="utf-8")
        assert "partial_failed" in partial_manifest.read_text(encoding="utf-8")


if __name__ == "__main__":
    test_cli_api_timeout_is_authoritative_for_short_chunks()
    test_engine_respects_current_runtime_timeout_without_second_clamp()
    test_dialogue_quotes_are_normalized_and_gate_detects_unformatted_output()
    test_partial_translation_is_preserved_on_failure()
    print("TER-v2.4 Runtime Provider Stability PASS")
