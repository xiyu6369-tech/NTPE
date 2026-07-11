from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import lts.txt_translation_runtime as runtime
from core.adaptive_context_runtime_shadow import (
    SHADOW_RUNTIME_VERSION,
    clear_shadow_records,
    install_txt_runtime_shadow_hook,
    shadow_records,
    uninstall_txt_runtime_shadow_hook,
)
from core.adaptive_context_integration.utils import canonical_hash


def main() -> int:
    assert SHADOW_RUNTIME_VERSION == "7.0.0-stage03"
    root = Path(__file__).resolve().parent
    old_mode = os.environ.get("NTPE_TE_V7_ACE_MODE")
    old_now = runtime.now_iso
    try:
        runtime.now_iso = lambda: "2026-07-12T00:00:00+00:00"
        uninstall_txt_runtime_shadow_hook()
        options = runtime.TxtTranslationOptions(input_path=root / "tests" / "literary" / "Golden_Set" / "original_ko.txt", output_dir=root / "output")
        kwargs = dict(
            options=options,
            chunk_text="정태의는 창밖을 보았다. 일라이는 문가에 서 있었다.",
            chunk_index=1,
            chunk_total=1,
            locked_dictionary={"정태의": "鄭泰義", "일라이": "伊萊"},
            previous_context="그들은 전날 늦게까지 이야기를 나누었다.",
        )
        os.environ["NTPE_TE_V7_ACE_MODE"] = "disabled"
        baseline = runtime.build_prompt_package(**kwargs)
        clear_shadow_records()
        assert install_txt_runtime_shadow_hook() is True
        os.environ["NTPE_TE_V7_ACE_MODE"] = "shadow"
        shadow = runtime.build_prompt_package(**kwargs)
        assert shadow == baseline
        assert canonical_hash(shadow) == canonical_hash(baseline)
        records = shadow_records()
        assert len(records) == 1
        assert records[0].payload_equivalent
        assert records[0].provider_calls_added == 0
        assert "정태의" not in repr(records[0].to_dict())

        manifest_path = root / "manifests" / "te_v700_stage03_runtime_shadow_activation_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for name, digest in manifest["integrity"]["files"].items():
            actual = hashlib.sha256((root / name).read_bytes()).hexdigest()
            assert actual == digest, name
    finally:
        runtime.now_iso = old_now
        uninstall_txt_runtime_shadow_hook()
        if old_mode is None:
            os.environ.pop("NTPE_TE_V7_ACE_MODE", None)
        else:
            os.environ["NTPE_TE_V7_ACE_MODE"] = old_mode
    print("TE v7.0 Stage 03 Runtime Shadow Activation ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
