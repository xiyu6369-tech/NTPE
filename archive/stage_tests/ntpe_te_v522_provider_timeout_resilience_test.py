from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

from core.translation_runtime.runtime_speed_policy import effective_timeout, get_runtime_speed_policy
from lts.txt_translation_runtime import (
    TxtTranslationOptions,
    _effective_provider_timeout,
    timeout_retry_delay_seconds,
    translate_package_with_retry,
)


class FakeEngine:
    def __init__(self):
        self.calls = 0

    def translate_package(self, package, package_path=None):
        self.calls += 1
        if self.calls < 4:
            return {"status": "failed", "error": "NVIDIA API timeout"}
        return {"status": "success", "translated_text": "完成"}


def main() -> int:
    old = dict(os.environ)
    try:
        os.environ["NTPE_API_TIMEOUT"] = "180"
        os.environ["NTPE_API_TIMEOUT_EXPLICIT"] = "1"
        os.environ["NTPE_TIMEOUT_RETRY_DELAYS"] = "5,15,30"

        assert effective_timeout(get_runtime_speed_policy("balanced"), 180) == 120
        from lts.txt_translation_runtime import apply_runtime_speed_policy
        applied = apply_runtime_speed_policy(TxtTranslationOptions(input_path=Path("x.txt"), output_dir=Path("out"), speed="balanced"))
        assert applied.runtime_timeout == 180
        package = {"package_id": "TEST", "source": {"char_count": 575}, "runtime": {"speed_timeout": 120}, "model_profile": {"model": "model"}}
        assert _effective_provider_timeout(package, 1) == 180
        assert [timeout_retry_delay_seconds(i, 5) for i in (1, 2, 3, 4)] == [5.0, 15.0, 30.0, 30.0]

        opts = TxtTranslationOptions(input_path=Path("x.txt"), output_dir=Path("out"), provider_attempts=4, progress_enabled=False)
        engine = FakeEngine()
        with patch("lts.txt_translation_runtime.time.sleep") as sleep:
            result = translate_package_with_retry(engine, package, Path("x.json"), opts)
        assert result["status"] == "success"
        assert engine.calls == 4
        assert [call.args[0] for call in sleep.call_args_list] == [5.0, 15.0, 30.0]

        print("TE v5.2.2 Provider Timeout Resilience Test")
        print("==========================================")
        print("Explicit timeout propagation       PASS")
        print("Configurable provider attempts     PASS")
        print("Timeout waits 5/15/30              PASS")
        print("Fourth attempt recovery            PASS")
        print("ALL PASS")
        return 0
    finally:
        os.environ.clear()
        os.environ.update(old)


if __name__ == "__main__":
    raise SystemExit(main())
