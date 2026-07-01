from __future__ import annotations
class HealthMonitor:
    def check(self, provider):
        try:
            status = provider.health()
            status.setdefault("healthy", True)
            return status
        except Exception as exc:
            return {"provider": getattr(provider, "name", "unknown"), "healthy": False, "error": str(exc)}
