from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> int:
    manifest_path = ROOT / "manifests/te_v700_stage073_prompt_context_anchor_contract_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for name, digest in manifest["integrity"]["files"].items():
        target = ROOT / name
        assert target.exists(), name
        assert not name.startswith("manifests/"), name
        assert hashlib.sha256(target.read_bytes()).hexdigest() == digest, name

    from core.adaptive_context_prompt_anchor import ANCHOR_VERSION, resolve_prompt_context_anchor
    assert ANCHOR_VERSION == "7.0.0-stage07.3"
    package = {
        "context": {"previous_chunk_tail": "第一句。第二句。"},
        "prompt": {"user_prompt": "【前文參考，僅供保持語氣與銜接，禁止重複翻譯】\n第一句。第二句。\n\n【待翻譯內容】\n원문"},
    }
    anchor = resolve_prompt_context_anchor(package)
    assert anchor.addressable is True
    assert anchor.start >= 0 and anchor.end > anchor.start
    assert anchor.content_sha256
    assert anchor.to_metadata()["content_redacted"] is True

    import ntpe_te_v700_stage072_canary_diagnostics_target_stop_test as stage072
    assert stage072.main() == 0
    print("TE v7.0 Stage 07.3 Prompt Context Anchor Contract ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
