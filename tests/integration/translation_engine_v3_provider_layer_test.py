import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.translation_engine import provider_runtime
from core.translation_engine.translation_engine import TranslationEngine


class FakeNvidiaClient:
    calls = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def chat(self, *, model, system_prompt, user_prompt, temperature, top_p, max_tokens):
        self.calls.append(model)
        if model == "primary-model":
            raise RuntimeError("NVIDIA API error 503: DEGRADED function cannot be invoked")
        return "translated text"


def test_translation_engine_v3_uses_provider_fallback():
    FakeNvidiaClient.calls = []
    original_client = provider_runtime.NvidiaClient
    original_key = os.environ.get("NVIDIA_API_KEY")
    original_fallbacks = os.environ.get("NTPE_FALLBACK_MODELS")
    provider_runtime.NvidiaClient = FakeNvidiaClient
    os.environ["NVIDIA_API_KEY"] = "test-key"
    os.environ["NTPE_FALLBACK_MODELS"] = "backup-model"

    try:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "config").mkdir(parents=True)
            (root / "config" / "provider_config.json").write_text(
                json.dumps(
                    {
                        "default_provider": "nvidia",
                        "translation_engine_v3": {
                            "fallback_models_env": "NTPE_FALLBACK_MODELS",
                            "fallback_models": [],
                            "retry_defaults": {"max_attempts": 1, "base_delay_seconds": 0.0},
                        },
                        "providers": {"nvidia": {"env_var": "NVIDIA_API_KEY", "default_model": "primary-model"}},
                    }
                ),
                encoding="utf-8",
            )

            package = {
                "package_id": "provider-v3-test",
                "model_profile": {
                    "model": "primary-model",
                    "temperature": 0.15,
                    "top_p": 0.85,
                    "max_output_tokens": 128,
                },
                "prompt": {"system_prompt": "translate", "user_prompt": "source text"},
                "source": {"char_count": 11},
                "session": {"file_name": "sample.txt", "chunk_index": 1},
            }

            result = TranslationEngine(root).translate_package(package)
    finally:
        provider_runtime.NvidiaClient = original_client
        if original_key is None:
            os.environ.pop("NVIDIA_API_KEY", None)
        else:
            os.environ["NVIDIA_API_KEY"] = original_key
        if original_fallbacks is None:
            os.environ.pop("NTPE_FALLBACK_MODELS", None)
        else:
            os.environ["NTPE_FALLBACK_MODELS"] = original_fallbacks

    assert result["status"] == "success"
    assert result["provider"]["provider"].startswith("nvidia_fallback_")
    assert result["provider"]["model"] == "backup-model"
    assert FakeNvidiaClient.calls == ["primary-model", "backup-model"]


if __name__ == "__main__":
    test_translation_engine_v3_uses_provider_fallback()
    print("PASS")
