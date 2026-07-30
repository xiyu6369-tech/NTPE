from __future__ import annotations

import math
import hashlib
import json
from pathlib import Path

from core.adaptive_context import (
    ACE_VERSION, ContextItem, build_adaptive_context, compress_narrative,
    estimate_tokens, preserve_dialogue,
)


def main() -> int:
    assert ACE_VERSION == "7.0.0-stage01.1"

    zh = estimate_tokens("這是一段繁體中文測試")
    ko = estimate_tokens("이것은한국어문장테스트")
    ja = estimate_tokens("これは日本語のテストです")
    en = estimate_tokens("thisisenglishtexttest")
    mixed = estimate_tokens("中文한국어日本語English123！")
    assert all(value > 0 for value in (zh, ko, ja, en, mixed))
    assert ko >= len("이것은한국어문장테스트")
    same_length_latin = estimate_tokens("abcdefghijklmnopqrstuv"[:len("이것은한국어문장테스트")])
    assert ko >= same_length_latin * 3
    assert estimate_tokens("한글") == 6

    for sentence in (
        "他沒有離開。後來天亮了。",
        "如果雨停了，我們就出發。否則留在這裡。",
        "因為門已鎖上，所以他轉身離開。街上沒有人。",
        "他本想答應，但是最後保持沉默。鐘聲隨後響起。",
    ):
        first = sentence.split("。")[0] + "。"
        compressed = compress_narrative(sentence, estimate_tokens(first))
        assert compressed == first
    assert compress_narrative("第一個完整句子無法容納。第二句。", 1) == ""

    dialogue = preserve_dialogue("旁白。\n「完整的第一句。」\n背景。\n「完整的第二句。」", 9)
    assert not dialogue or all(line.endswith("」") for line in dialogue.splitlines())

    required = ContextItem("required", "glossary", "不可省略的必要術語內容", required=True)
    optional = ContextItem("optional", "dialogue", "「可選對話。」", relevance=1.0, recency=1.0)
    overflow = build_adaptive_context([required], requested_context_tokens=2)
    assert not overflow.admissible and overflow.fallback_required
    assert overflow.selected == () and overflow.fallback_reasons == ("required-context-overflow:required",)
    after_optional = build_adaptive_context([optional, required], requested_context_tokens=2)
    assert not after_optional.admissible and after_optional.selected == ()

    for invalid_id in ("", "   "):
        try:
            ContextItem(invalid_id, "other", "x")
            raise AssertionError("blank ID accepted")
        except ValueError:
            pass
    try:
        build_adaptive_context([ContextItem("same", "other", "a"), ContextItem("same", "other", "b")])
        raise AssertionError("duplicate IDs accepted")
    except ValueError:
        pass
    for value in (math.nan, math.inf, -math.inf):
        try:
            ContextItem("finite", "other", "x", relevance=value)
            raise AssertionError("non-finite score accepted")
        except ValueError:
            pass

    negative = build_adaptive_context([optional], model_context_limit=-1, requested_context_tokens=-5)
    assert negative.token_budget == 0
    first = build_adaptive_context([optional], requested_context_tokens=20)
    second = build_adaptive_context([optional], requested_context_tokens=20)
    assert first == second and first.fingerprint == second.fingerprint
    assert "可選對話" not in repr(first.observability)
    assert first.observability["raw_context_retained"] is False
    root = Path(__file__).resolve().parent
    manifest = json.loads((root / "manifests/te_v700_stage011_adaptive_context_safety_stabilization_manifest.json").read_text(encoding="utf-8"))
    assert manifest["contract_changes"]["fingerprint_payload"] == ["selected_item_id", "selected_item_kind", "selected_content_sha256"]
    for name, digest in manifest["integrity"]["files"].items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest
    print("TE v7.0 Stage 01.1 Adaptive Context Safety Stabilization ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
