"""Compatibility test for Stage-14.2 release manifest layer."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packaging import ReleaseManifest  # noqa: E402


def main() -> None:
    manifest = ReleaseManifest()
    payload = manifest.to_dict()
    required_components = {
        "foundation",
        "cli",
        "sdk",
        "integration",
        "workflow",
        "platform_services",
        "runtime_api",
        "external_api",
        "web_ui",
        "packaging",
    }
    names = {item["name"] for item in payload["components"]}
    assert required_components.issubset(names)
    assert payload["compatibility"]["foundation_v1_frozen"] is True
    assert payload["compatibility"]["additive_only"] is True
    print("NTPE Stage-14.2 Compatibility PASS")


if __name__ == "__main__":
    main()
