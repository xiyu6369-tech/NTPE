"""Package metadata helpers for the public NTPE SDK."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List

from .version import SDK_API_LEVEL, SDK_STAGE, SDK_STAGE_NAME, SDK_VERSION


@dataclass(frozen=True)
class SDKPackageMetadata:
    name: str = "ntpe-sdk"
    version: str = SDK_VERSION
    stage: str = SDK_STAGE
    stage_name: str = SDK_STAGE_NAME
    api_level: str = SDK_API_LEVEL
    python_requires: str = ">=3.10"
    foundation_status: str = "frozen"
    packages: tuple[str, ...] = ("sdk",)

    def to_dict(self) -> Dict[str, object]:
        data = asdict(self)
        data["packages"] = list(self.packages)
        return data


def package_metadata() -> Dict[str, object]:
    return SDKPackageMetadata().to_dict()


def package_classifiers() -> List[str]:
    return [
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Typing :: Typed",
    ]
