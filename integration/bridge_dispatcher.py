"""Command dispatcher for the SDK-CLI bridge."""
from __future__ import annotations

from typing import Any

from .bridge_models import BridgeCommand, BridgeResult
from .bridge_registry import BridgeRegistry


class BridgeDispatcher:
    version = "0.8.2"

    def __init__(self, registry: BridgeRegistry) -> None:
        self.registry = registry

    def dispatch(self, command: BridgeCommand) -> BridgeResult:
        try:
            endpoint_name = self._resolve_endpoint(command.surface)
            endpoint = self.registry.require(endpoint_name)
            target = endpoint.instance
            method_name = self._resolve_method(target, command.action)
            method = getattr(target, method_name)
            value = method(**command.payload)
            return BridgeResult.success(command.action, command.surface, value=value, endpoint=endpoint_name, method=method_name, session_id=command.session_id, correlation_id=command.correlation_id)
        except Exception as exc:
            return BridgeResult.failure(command.action, command.surface, str(exc), session_id=command.session_id, correlation_id=command.correlation_id)

    @staticmethod
    def _resolve_endpoint(surface: str) -> str:
        if surface in {"sdk", "cli", "runtime"}:
            return surface
        return surface

    @staticmethod
    def _resolve_method(target: Any, action: str) -> str:
        aliases = {
            "translate": ["translate", "translate_text", "execute"],
            "translate_text": ["translate_text", "translate", "execute"],
            "run": ["run", "execute"],
            "execute": ["execute", "run"],
            "status": ["status", "health"],
            "configure": ["configure", "set_config"],
        }
        for candidate in aliases.get(action, [action]):
            if hasattr(target, candidate):
                return candidate
        raise AttributeError(f"bridge action unavailable: {action}")
