"""NTPE 1.0 Beta Stage-07.8 SDK Documentation & Packaging test."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sdk import (  # noqa: E402
    PACKAGE_VERSION,
    PACKAGE_STAGE,
    SDK_STAGE_NAME,
    SDK_API_LEVEL,
    SDKPackageMetadata,
    package_metadata,
    package_classifiers,
    version_info,
    NTPEClient,
    SDKPluginManager,
    SDK_CONFIG_STAGE,
)


def check(name: str, condition: bool) -> None:
    print(f"{name:<30} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


def load_wheel_helper():
    helper = ROOT / "packaging" / "wheel_build.py"
    spec = importlib.util.spec_from_file_location("ntpe_wheel_build", helper)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def main() -> None:
    print("NTPE 1.0 Beta Stage-07.8 SDK Documentation & Packaging Test")
    print("=" * 72)

    check("SDK Package Structure", (ROOT / "sdk" / "py.typed").exists() and (ROOT / "sdk" / "__about__.py").exists())

    docs = [
        ROOT / "docs" / "sdk" / "getting_started.md",
        ROOT / "docs" / "sdk" / "session_api.md",
        ROOT / "docs" / "sdk" / "translation_api.md",
        ROOT / "docs" / "sdk" / "batch_api.md",
        ROOT / "docs" / "sdk" / "streaming_api.md",
        ROOT / "docs" / "sdk" / "plugin_api.md",
        ROOT / "docs" / "sdk" / "configuration_api.md",
    ]
    check("SDK Documentation", all(path.exists() and path.read_text(encoding="utf-8").strip() for path in docs))

    examples = [ROOT / "examples" / name for name in ["sdk_basic.py", "sdk_batch.py", "sdk_stream.py", "sdk_plugin.py"]]
    check("SDK Examples", all(path.exists() and "from sdk" in path.read_text(encoding="utf-8") for path in examples))

    metadata = package_metadata()
    info = version_info()
    check("SDK Metadata", metadata["version"] == PACKAGE_VERSION and info["stage"] == PACKAGE_STAGE and SDK_API_LEVEL == "1.0-beta")
    check("SDK Metadata Class", SDKPackageMetadata().to_dict()["foundation_status"] == "frozen" and package_classifiers())

    pyproject = ROOT / "packaging" / "pyproject.toml"
    manifest = ROOT / "packaging" / "MANIFEST.in"
    check("SDK Packaging", pyproject.exists() and "ntpe-sdk" in pyproject.read_text(encoding="utf-8") and manifest.exists())

    helper = load_wheel_helper()
    build_result = helper.validate_packaging(ROOT)
    check("Wheel Build", build_result["ok"] is True and build_result["missing"] == [])

    client = NTPEClient(translator=lambda segment, ctx: {"translation": str(segment)})
    translated = client.translate_text("stage-07.8")
    check("Backward Compatible", translated.ok and translated.text == "stage-07.8" and "07.6" in SDK_CONFIG_STAGE)
    check("Plugin Compatible", SDKPluginManager() is not None)
    check("Stage Metadata", PACKAGE_STAGE == "07.8" and "Packaging" in SDK_STAGE_NAME)

    print("PASS")


if __name__ == "__main__":
    main()
