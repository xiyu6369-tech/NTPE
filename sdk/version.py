"""NTPE SDK version metadata for Stage-07.8."""
from __future__ import annotations

SDK_VERSION = "1.0.0b7"
SDK_STAGE = "07.8"
SDK_STAGE_NAME = "SDK Documentation & Packaging"
SDK_API_LEVEL = "1.0-beta"


def get_version() -> str:
    return SDK_VERSION


def version_info() -> dict:
    return {
        "version": SDK_VERSION,
        "stage": SDK_STAGE,
        "stage_name": SDK_STAGE_NAME,
        "api_level": SDK_API_LEVEL,
        "foundation": "1.0-frozen",
    }
