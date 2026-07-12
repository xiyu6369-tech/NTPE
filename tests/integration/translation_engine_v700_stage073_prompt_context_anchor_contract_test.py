from __future__ import annotations

import os

from core.adaptive_context_canary import apply_prompt_package_canary, clear_canary_records
from core.adaptive_context_prompt_anchor import (
    anchored_context_text,
    replace_anchored_context,
    resolve_prompt_context_anchor,
)


def _package(previous: str, *, duplicate_elsewhere: bool = False) -> dict[str, object]:
    elsewhere = previous + "\n" if duplicate_elsewhere else ""
    return {
        "package_id": "TXT_fixture_000003",
        "session": {"chunk_index": 3},
        "context": {"previous_chunk_tail": previous},
        "prompt": {
            "user_prompt": (
                "【翻譯規則】\n" + elsewhere
                + "【前文參考，僅供保持語氣與銜接，禁止重複翻譯】\n"
                + previous
                + "\n\n【待翻譯內容】\n原文"
            )
        },
    }


def test_anchor_addresses_section_even_when_content_occurs_elsewhere() -> None:
    previous = "第一句完整內容。第二句完整內容。第三句完整內容。"
    package = _package(previous, duplicate_elsewhere=True)
    anchor = resolve_prompt_context_anchor(package)
    assert anchor.addressable is True
    assert anchor.strategy == "zh-section"
    assert anchored_context_text(package, anchor) == previous
    original_prompt = package["prompt"]["user_prompt"]
    assert replace_anchored_context(package, anchor, "第一句完整內容。") is True
    updated = package["prompt"]["user_prompt"]
    assert updated.count(previous) == 1  # the unrelated occurrence remains untouched
    assert updated != original_prompt
    assert package["context"]["prompt_context_anchor"]["content_redacted"] is True


def test_canary_uses_anchor_and_changes_only_target_context(monkeypatch) -> None:
    previous = "第一句完整內容。第二句完整內容。第三句完整內容。"
    package = _package(previous, duplicate_elsewhere=True)
    monkeypatch.setenv("NTPE_TE_V7_ACE_MODE", "canary")
    monkeypatch.setenv("NTPE_TE_V7_ACE_CANARY_CHUNK", "3")
    monkeypatch.setenv("NTPE_TE_V7_ACE_CANARY_CONTEXT_TOKENS", "9")
    clear_canary_records()
    record = apply_prompt_package_canary(package)
    assert record is not None
    assert record.attempted is True
    assert record.activated is True
    assert record.estimated_tokens_saved > 0
    assert record.fallback_reasons == ()
    assert package["prompt"]["user_prompt"].count(previous) == 1
    assert package["context"]["prompt_context_anchor"]["strategy"] == "zh-section"


def test_anchor_fails_closed_on_missing_or_mismatched_section() -> None:
    missing = {
        "context": {"previous_chunk_tail": "前文。"},
        "prompt": {"user_prompt": "【待翻譯內容】\n原文"},
    }
    assert resolve_prompt_context_anchor(missing).reason == "prompt-context-anchor-marker-missing"

    mismatch = {
        "context": {"previous_chunk_tail": "真正前文。"},
        "prompt": {
            "user_prompt": "【前文參考，僅供保持語氣與銜接，禁止重複翻譯】\n不同內容。\n\n【待翻譯內容】\n原文"
        },
    }
    anchor = resolve_prompt_context_anchor(mismatch)
    assert anchor.addressable is False
    assert anchor.reason == "prompt-context-anchor-hash-mismatch"
