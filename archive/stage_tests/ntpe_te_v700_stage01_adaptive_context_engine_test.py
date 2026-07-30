from __future__ import annotations

from dataclasses import FrozenInstanceError
import hashlib
import json
from pathlib import Path

from core.adaptive_context import (
    ACE_VERSION, ContextItem, build_adaptive_context, calculate_dynamic_budget,
    compress_narrative, diff_context, preserve_dialogue, rank_context,
)


def _items() -> list[ContextItem]:
    return [
        ContextItem("char-a", "character", "林靜是本幕主要人物。", ("林靜",), relevance=0.8),
        ContextItem("dialogue-a", "dialogue", "敘述背景。\n「別回頭。」\n走廊很暗。\n「我知道。」", ("林靜",), recency=1.0),
        ContextItem("narrative-a", "narrative", "雨落在老宅屋簷。走廊盡頭沒有燈。她記得昨夜的約定。", continuity=0.9),
        ContextItem("other-a", "other", "低優先補充資料。"),
    ]


def main() -> int:
    assert ACE_VERSION == "7.0.0-stage01.1"
    ranked = rank_context(_items(), active_characters=("林靜",))
    assert ranked[0].item.item_id in {"char-a", "dialogue-a"}
    assert ranked[-1].item.item_id == "other-a"
    budget = calculate_dynamic_budget(model_context_limit=100, fixed_prompt_tokens=20, source_tokens=30, reserved_output_tokens=10, requested_context_tokens=80)
    assert budget.available_tokens == 40 and budget.hard_limit == 40
    dialogue = preserve_dialogue("敘述。\n「第一句。」\n背景。\n「第二句。」", 12)
    assert "敘述" not in dialogue and "「" in dialogue
    narrative = compress_narrative("第一句很重要。第二句補充背景。第三句延伸說明。", 8)
    assert narrative and len(narrative) < len("第一句很重要。第二句補充背景。第三句延伸說明。")
    result = build_adaptive_context(_items(), active_characters=("林靜",), model_context_limit=120, reserved_output_tokens=20, requested_context_tokens=35)
    assert result.estimated_tokens <= result.token_budget
    assert len(result.fingerprint) == 64
    assert result.observability["raw_context_retained"] is False
    assert "林靜是本幕主要人物" not in repr(result.observability)
    repeated = build_adaptive_context(_items(), active_characters=("林靜",), model_context_limit=120, reserved_output_tokens=20, requested_context_tokens=35)
    assert repeated.fingerprint == result.fingerprint
    changed = build_adaptive_context(_items()[:-1], active_characters=("林靜",), requested_context_tokens=100)
    delta = diff_context(result, changed)
    assert isinstance(delta.fingerprint_changed, bool)
    try:
        result.version = "changed"  # type: ignore[misc]
        raise AssertionError("ACE result must be immutable")
    except FrozenInstanceError:
        pass
    root = Path(__file__).resolve().parent
    manifest = json.loads((root / "manifests/te_v700_stage01_adaptive_context_engine_manifest.json").read_text(encoding="utf-8"))
    assert manifest["frozen_boundaries"]["te_v6_runtime_modified"] is False
    for name, digest in manifest["integrity"]["files"].items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest
    print("TE v7.0 Stage 01 Adaptive Context Engine ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
