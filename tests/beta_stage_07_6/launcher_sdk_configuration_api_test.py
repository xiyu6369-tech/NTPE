"""NTPE 1.0 Beta Stage-07.6 SDK Configuration API test."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sdk import (  # noqa: E402
    SDK_CONFIG_STAGE,
    SDK_CONFIG_VERSION,
    SDK_BATCH_STAGE,
    SDK_STREAM_STAGE,
    SDK_TRANSLATION_STAGE,
    SDKConfig,
    SDKConfigBuilder,
    SDKConfigLoader,
    SDKConfigValidator,
    build_sdk_config_manifest,
    config_builder,
    default_config,
    validate_config,
)


def check(name: str, condition: bool) -> None:
    print(f"{name:<30} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


def main() -> None:
    print("NTPE 1.0 Beta Stage-07.6 SDK Configuration API Test")
    print("=" * 68)

    cfg = default_config({"stage": "07.6"})
    check("SDK Config Created", cfg.version == SDK_CONFIG_VERSION and cfg.translation.target_language == "zh-TW")

    built = (
        SDKConfigBuilder()
        .provider(name="nvidia", model="meta/llama-3.3-70b-instruct", api_key="secret", timeout_seconds=180, max_retries=5)
        .runtime(work_dir="D:/Python/NTPE", cache_dir="cache", log_level="DEBUG")
        .translation(source_language="ko", target_language="zh-TW", chunk_size=2500, quality_check=True)
        .batch(continue_on_error=True, max_workers=1, output_suffix="_繁中")
        .streaming(emit_tokens=True, emit_segments=True, callback_errors="record")
        .metadata(project="NTPE")
        .build()
    )
    check("SDK Config Builder", built.provider.name == "nvidia" and built.batch.output_suffix == "_繁中")

    result = validate_config(built)
    check("SDK Config Validation", result.ok and result.errors == [])

    invalid = SDKConfig.from_dict(built.to_dict(include_secrets=True))
    invalid.translation.chunk_size = 0
    invalid_result = SDKConfigValidator().validate(invalid)
    check("SDK Invalid Config", not invalid_result.ok and "translation.chunk_size" in invalid_result.errors[0])

    data = built.to_dict()
    check("Secret Masking", data["provider"]["api_key"] == "***")
    restored = SDKConfig.from_dict(built.to_dict(include_secrets=True))
    check("SDK Config Restore", restored.provider.api_key == "secret" and restored.streaming.callback_errors == "record")

    loader = SDKConfigLoader()
    payload = loader.dumps(built, include_secrets=True)
    loaded = loader.loads(payload)
    check("SDK Config Serialization", loaded.provider.model == built.provider.model and loaded.translation.chunk_size == 2500)

    tmp = ROOT / "tmp_stage_07_6_sdk_config.json"
    try:
        loader.save(built, tmp, include_secrets=True)
        loaded_file = loader.load(tmp)
        check("SDK Config File IO", loaded_file.runtime.work_dir == "D:/Python/NTPE")
    finally:
        if tmp.exists():
            tmp.unlink()

    trans_options = built.to_translation_options()
    runtime_payload = built.to_runtime_payload()
    check("SDK Runtime Config", runtime_payload["runtime"]["resume_enabled"] is True and runtime_payload["sdk"]["version"] == SDK_CONFIG_VERSION)
    check("SDK Provider Config", runtime_payload["provider"]["name"] == "nvidia" and runtime_payload["provider"]["api_key"] == "***")
    check("SDK Translation Config", trans_options["source_language"] == "ko" and trans_options["target_language"] == "zh-TW")

    built2 = config_builder().provider(name="local", model="mock-model").translation(chunk_size=1200).build()
    check("SDK Config Helper", built2.provider.name == "local" and built2.translation.chunk_size == 1200)

    manifest = build_sdk_config_manifest({"translation_stage": SDK_TRANSLATION_STAGE, "batch_stage": SDK_BATCH_STAGE, "stream_stage": SDK_STREAM_STAGE})
    check("SDK Config Manifest", manifest["backward_compatible"] is True and "SDKConfigBuilder" in manifest["components"])
    check("Stage Links", "Stage-07.2" in manifest["metadata"]["translation_stage"] and "Stage-07.4" in manifest["metadata"]["stream_stage"])
    check("Backward Compatible", "Stage-07.5" in manifest["sdk_error_compatibility"] and "Stage-07.6" in SDK_CONFIG_STAGE)

    print("PASS")


if __name__ == "__main__":
    main()
