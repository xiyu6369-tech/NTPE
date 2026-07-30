from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> int:
    manifest = json.loads((ROOT / "manifests/te_v700_stage074_package_bound_context_anchor_manifest.json").read_text(encoding="utf-8"))
    for name, digest in manifest["integrity"]["files"].items():
        target = ROOT / name
        assert target.exists(), name
        assert not name.startswith("manifests/"), name
        assert hashlib.sha256(target.read_bytes()).hexdigest() == digest, name

    from core.adaptive_context_prompt_anchor import PACKAGE_ANCHOR_VERSION, bind_prompt_context_anchor, resolve_prompt_context_anchor
    assert PACKAGE_ANCHOR_VERSION == "7.0.0-stage07.4"
    previous = "第一句完整內容。第二句完整內容。"
    marker = "【前文參考，僅供保持語氣與銜接，禁止重複翻譯】\n"
    package = {
        "context": {"previous_chunk_tail": previous},
        "prompt": {"user_prompt": "policy:" + marker + marker + previous + "\n\n【待翻譯內容】\n원문"},
    }
    assert resolve_prompt_context_anchor(package).reason == "prompt-context-anchor-ambiguous"
    assert bind_prompt_context_anchor(package).addressable is True
    assert resolve_prompt_context_anchor(package).strategy == "package-bound"

    import ntpe_te_v700_stage073_prompt_context_anchor_contract_test as stage073
    assert stage073.main() == 0
    print("TE v7.0 Stage 07.4 Package-Bound Context Anchor ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
