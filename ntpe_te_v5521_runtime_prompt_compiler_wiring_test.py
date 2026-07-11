from __future__ import annotations

import os
from pathlib import Path

from lts.txt_translation_runtime import TxtTranslationOptions, build_prompt_package


def _options() -> TxtTranslationOptions:
    return TxtTranslationOptions(
        input_path=Path("tests/literary/Golden_Set/original_ko.txt"),
        output_dir=Path("tests/literary/outputs/TE-v5.5.2.1-WiringCheck"),
        quality_profile="literary",
        dry_run=True,
    )


def main() -> int:
    old = os.environ.get("NTPE_PROMPT_DISCIPLINE")
    try:
        os.environ["NTPE_PROMPT_DISCIPLINE"] = "1"
        package = build_prompt_package(
            options=_options(),
            chunk_text="정태의는 조용히 창밖을 바라보았다.",
            chunk_index=1,
            chunk_total=1,
            locked_dictionary={"정태의": "鄭泰義"},
        )
        prompt = package["prompt"]
        runtime = package["prompt_runtime"]
        assert "【翻譯紀律】" in prompt["user_prompt"]
        assert runtime["prompt_discipline_enabled"] is True
        assert runtime["discipline_rule_count"] == 8
        assert runtime["runtime_wiring_verified"] is True
        assert prompt["prompt_profile"]["policy_tokens"] > 74
        assert prompt["prompt_profile"]["total_tokens"] > 100

        os.environ["NTPE_PROMPT_DISCIPLINE"] = "0"
        disabled = build_prompt_package(
            options=_options(),
            chunk_text="정태의는 조용히 창밖을 바라보았다.",
            chunk_index=1,
            chunk_total=1,
            locked_dictionary={"정태의": "鄭泰義"},
        )
        assert "【翻譯紀律】" not in disabled["prompt"]["user_prompt"]
        assert disabled["prompt_runtime"]["prompt_discipline_enabled"] is False
        assert disabled["prompt_runtime"]["discipline_rule_count"] == 0

        print("TE v5.5.2.1 Runtime Prompt Compiler Wiring Fix")
        print("================================================")
        print("Runtime package contains discipline      PASS")
        print("Provider-ready prompt verified           PASS")
        print("Prompt profile includes discipline       PASS")
        print("Package metadata records wiring          PASS")
        print("Rollback switch remains compatible       PASS")
        print("ALL PASS")
        return 0
    finally:
        if old is None:
            os.environ.pop("NTPE_PROMPT_DISCIPLINE", None)
        else:
            os.environ["NTPE_PROMPT_DISCIPLINE"] = old


if __name__ == "__main__":
    raise SystemExit(main())
