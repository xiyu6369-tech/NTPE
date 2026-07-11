from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


class RuntimeIntegrationDisabledGuard:
    """Guard future runtime integration paths behind an explicit enabled flag."""

    stage = "3.3.3"
    safety_boundaries = {
        "provider_runtime": "external",
        "http_client": "forbidden",
        "api_key": "forbidden",
        "launcher_flow": "unchanged",
        "translation_runtime_flow": "unchanged",
    }

    def guard(self, flag_state: Mapping[str, Any] | None, request: Mapping[str, Any] | None = None) -> dict[str, Any]:
        flag = dict(flag_state or {})
        enabled = flag.get("enabled") is True
        return {
            "allowed": enabled,
            "blocked": not enabled,
            "reason": "runtime_integration_enabled" if enabled else "runtime_integration_disabled",
            "stage": self.stage,
            "request_summary": self._request_summary(request),
            "safety_boundaries": dict(self.safety_boundaries),
            "metadata": {
                "guard": "runtime_integration_disabled_guard",
                "flag_source": flag.get("source", "missing"),
                "flag_reason": flag.get("reason", "missing_flag_state"),
            },
        }

    def is_blocked(self, guard_result: Mapping[str, Any] | None) -> bool:
        result = dict(guard_result or {})
        return result.get("blocked") is True

    def validate_guard_result(self, guard_result: Mapping[str, Any] | None) -> dict[str, Any]:
        result = dict(guard_result or {})
        errors: list[str] = []

        if not isinstance(result.get("allowed"), bool):
            errors.append("allowed boolean is required")
        if not isinstance(result.get("blocked"), bool):
            errors.append("blocked boolean is required")
        if result.get("allowed") == result.get("blocked"):
            errors.append("allowed and blocked must be opposites")
        if result.get("reason") not in {"runtime_integration_disabled", "runtime_integration_enabled"}:
            errors.append("reason is invalid")
        if result.get("stage") != self.stage:
            errors.append("stage must be 3.3.3")
        if not isinstance(result.get("request_summary"), Mapping):
            errors.append("request_summary mapping is required")

        boundaries = result.get("safety_boundaries")
        if not isinstance(boundaries, Mapping):
            errors.append("safety_boundaries mapping is required")
            boundaries = {}
        for key, expected in self.safety_boundaries.items():
            if boundaries.get(key) != expected:
                errors.append(f"{key} boundary must be {expected}")

        if not isinstance(result.get("metadata"), Mapping):
            errors.append("metadata mapping is required")

        return {"valid": not errors, "errors": errors}

    def _request_summary(self, request: Mapping[str, Any] | None) -> dict[str, Any]:
        data = dict(request or {})
        chunk_count = self._chunk_count(data)
        return {
            "request_type": str(data.get("type", data.get("request_type", "unknown"))),
            "runtime_id": str(data.get("runtime_id", "runtime-state-unknown")),
            "chunk_count": chunk_count,
            "has_source_text": any(key in data for key in ("source_text", "text", "chunks")),
            "keys": sorted(str(key) for key in data if key not in {"source_text", "text", "chunks"}),
        }

    def _chunk_count(self, request: Mapping[str, Any]) -> int:
        chunks = request.get("chunks")
        if isinstance(chunks, Sequence) and not isinstance(chunks, (str, bytes, bytearray)):
            return len(chunks)
        if "source_text" in request or "text" in request:
            return 1
        return 0


__all__ = ["RuntimeIntegrationDisabledGuard"]
