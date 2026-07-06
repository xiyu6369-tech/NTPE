# =====================================================
# NTPE 1.2 Professional
# Stage-14.1 Provider Runtime Binding Compatibility Shim
# Preserved for Stage-17.3 validator compatibility.
# =====================================================

from __future__ import annotations

from typing import Any


def bind_provider_manager(runtime: Any, manager: Any) -> dict[str, Any]:
    """Bind a ProviderManager to a runtime object without changing legacy runtime APIs."""

    if hasattr(runtime, "bind_ai_provider_manager"):
        return runtime.bind_ai_provider_manager(manager)
    setattr(runtime, "ai_provider_manager", manager)
    return {
        "status": "success",
        "providers": manager.registry.list() if hasattr(manager, "registry") else [],
    }


def register_provider(runtime: Any, provider: Any, default: bool = False) -> dict[str, Any]:
    """Register a provider on a runtime-bound ProviderManager."""

    if hasattr(runtime, "register_ai_provider"):
        return runtime.register_ai_provider(provider, default=default)
    manager = getattr(runtime, "ai_provider_manager", None)
    if manager is None or not hasattr(manager, "registry"):
        raise RuntimeError("runtime has no ai_provider_manager registry")
    manager.registry.register(provider, default=default)
    return {"status": "success", "provider": getattr(provider, "name", None)}
