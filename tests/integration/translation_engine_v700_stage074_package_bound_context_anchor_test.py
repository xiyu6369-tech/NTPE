from __future__ import annotations

import os

from core.adaptive_context_canary import apply_prompt_package_canary, clear_canary_records
from core.adaptive_context_prompt_anchor import (
    PACKAGE_ANCHOR_VERSION,
    anchored_context_text,
    bind_prompt_context_anchor,
    resolve_prompt_context_anchor,
)


def _package(previous: str) -> dict[str, object]:
    marker = "【前文參考，僅供保持語氣與銜接，禁止重複翻譯】\n"
    # The policy intentionally repeats the marker text, reproducing the real ambiguity.
    prompt = (
        "【Policy】Do not translate the marker name: " + marker
        + "【Rules】Keep continuity.\n"
        + marker + previous + "\n\n【待翻譯內容】\n원문"
    )
    return {
        "package_id": "TXT_fixture_000003",
        "session": {"chunk_index": 3},
        "context": {"previous_chunk_tail": previous},
        "prompt": {"user_prompt": prompt},
    }


def test_package_binding_selects_unique_matching_section_despite_duplicate_marker() -> None:
    previous = "第一句完整內容。第二句完整內容。第三句完整內容。"
    package = _package(previous)
    legacy = resolve_prompt_context_anchor(package)
    assert legacy.addressable is False
    assert legacy.reason == "prompt-context-anchor-ambiguous"

    bound = bind_prompt_context_anchor(package)
    assert bound.addressable is True
    assert bound.strategy == "package-bound"
    metadata = package["context"]["prompt_context_anchor_bound"]
    assert metadata["version"] == PACKAGE_ANCHOR_VERSION
    assert metadata["content_redacted"] is True
    resolved = resolve_prompt_context_anchor(package)
    assert resolved.addressable is True
    assert resolved.strategy == "package-bound"
    assert anchored_context_text(package, resolved) == previous


def test_canary_uses_bound_offset_and_changes_only_context(monkeypatch) -> None:
    previous = "第一句完整內容。第二句完整內容。第三句完整內容。"
    package = _package(previous)
    bind_prompt_context_anchor(package)
    before = package["prompt"]["user_prompt"]
    monkeypatch.setenv("NTPE_TE_V7_ACE_MODE", "canary")
    monkeypatch.setenv("NTPE_TE_V7_ACE_CANARY_CHUNK", "3")
    monkeypatch.setenv("NTPE_TE_V7_ACE_CANARY_CONTEXT_TOKENS", "9")
    clear_canary_records()
    record = apply_prompt_package_canary(package)
    assert record is not None and record.activated is True
    after = package["prompt"]["user_prompt"]
    assert after != before
    assert after.startswith(before[: package["context"]["prompt_context_anchor"]["start"]])
    assert record.estimated_tokens_saved > 0
    assert record.fallback_reasons == ()


def test_bound_metadata_tamper_fails_closed() -> None:
    package = _package("第一句。第二句。")
    bind_prompt_context_anchor(package)
    package["prompt"]["user_prompt"] += "tamper"
    anchor = resolve_prompt_context_anchor(package)
    assert anchor.addressable is False
    assert anchor.reason == "prompt-context-bound-anchor-hash-mismatch"
