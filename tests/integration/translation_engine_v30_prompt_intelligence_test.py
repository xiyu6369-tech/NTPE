from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.translation_engine import provider_runtime
from core.translation_engine.prompt_intelligence import PROMPT_INTELLIGENCE_MARKER
from core.translation_engine.translation_engine import TranslationEngine


class FakeNvidiaClient:
    calls: list[dict] = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def chat(self, *, model, system_prompt, user_prompt, temperature, top_p, max_tokens):
        self.calls.append(
            {
                "model": model,
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "temperature": temperature,
                "top_p": top_p,
                "max_tokens": max_tokens,
            }
        )
        return "完整譯文：「我會留下。」\n"


def test_translation_engine_applies_prompt_intelligence_to_legacy_package() -> None:
    FakeNvidiaClient.calls = []
    original_client = provider_runtime.NvidiaClient
    original_key = os.environ.get("NVIDIA_API_KEY")
    provider_runtime.NvidiaClient = FakeNvidiaClient
    os.environ["NVIDIA_API_KEY"] = "test-key"

    try:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "config").mkdir(parents=True)
            (root / "config" / "provider_config.json").write_text(
                json.dumps(
                    {
                        "default_provider": "nvidia",
                        "translation_engine_v3": {
                            "fallback_models": [],
                            "retry_defaults": {"max_attempts": 1, "base_delay_seconds": 0.0},
                        },
                        "providers": {"nvidia": {"env_var": "NVIDIA_API_KEY", "default_model": "test-model"}},
                    }
                ),
                encoding="utf-8",
            )
            package = {
                "package_id": "v30-prompt-intelligence-integration",
                "model_profile": {
                    "model": "test-model",
                    "temperature": 0.15,
                    "top_p": 0.85,
                    "max_output_tokens": 128,
                },
                "prompt": {"system_prompt": "translate", "user_prompt": "Translate this novel scene."},
                "source": {"chunk_text": '"Stay here," she whispered.', "char_count": 28},
                "session": {"file_name": "sample.txt", "chunk_index": 1},
            }

            result = TranslationEngine(root).translate_package(package)
            cache_payload = json.loads(Path(result["cache_path"]).read_text(encoding="utf-8"))
    finally:
        provider_runtime.NvidiaClient = original_client
        if original_key is None:
            os.environ.pop("NVIDIA_API_KEY", None)
        else:
            os.environ["NVIDIA_API_KEY"] = original_key

    assert result["status"] == "success"
    assert FakeNvidiaClient.calls
    assert PROMPT_INTELLIGENCE_MARKER in FakeNvidiaClient.calls[0]["user_prompt"]
    assert "do not summarize" in FakeNvidiaClient.calls[0]["user_prompt"]
    assert cache_payload["package"]["metadata"]["prompt_intelligence"]["profile"] == "dialogue_heavy"


if __name__ == "__main__":
    test_translation_engine_applies_prompt_intelligence_to_legacy_package()
    print("PASS")
