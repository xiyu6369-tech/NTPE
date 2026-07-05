from __future__ import annotations

import re
from dataclasses import dataclass

_VERSION_RE = re.compile(r"^(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:[-+]([A-Za-z0-9_.-]+))?$")


def parse_version(version: str) -> tuple[int, int, int, str]:
    match = _VERSION_RE.match(str(version).strip())
    if not match:
        raise ValueError(f"invalid version: {version}")
    major, minor, patch, suffix = match.groups()
    return int(major), int(minor or 0), int(patch or 0), suffix or ""


def compare_versions(left: str, right: str) -> int:
    left_parsed = parse_version(left)
    right_parsed = parse_version(right)
    left_core = left_parsed[:3]
    right_core = right_parsed[:3]
    if left_core < right_core:
        return -1
    if left_core > right_core:
        return 1
    if left_parsed[3] == right_parsed[3]:
        return 0
    if not left_parsed[3]:
        return 1
    if not right_parsed[3]:
        return -1
    return -1 if left_parsed[3] < right_parsed[3] else 1


@dataclass(frozen=True)
class VersionPolicy:
    minimum: str = "1.1.0"
    maximum: str | None = None

    def accepts(self, version: str) -> bool:
        if compare_versions(version, self.minimum) < 0:
            return False
        if self.maximum and compare_versions(version, self.maximum) > 0:
            return False
        return True
