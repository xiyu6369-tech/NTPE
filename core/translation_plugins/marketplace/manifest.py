from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

from .versioning import VersionPolicy

_ALLOWED_CAPABILITIES = {
    "prompt", "glossary", "character_memory", "context", "provider", "qa", "formatter", "output"
}


@dataclass(frozen=True)
class MarketplacePluginManifest:
    plugin_id: str
    name: str
    version: str
    api_version: str = "1.2"
    ntpe_min_version: str = "1.1.0"
    ntpe_max_version: str | None = None
    author: str = "unknown"
    description: str = ""
    capabilities: tuple[str, ...] = field(default_factory=tuple)
    dependencies: tuple[str, ...] = field(default_factory=tuple)
    entrypoint: str = ""
    signature: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MarketplacePluginManifest":
        return cls(
            plugin_id=str(data.get("plugin_id", "")).strip(),
            name=str(data.get("name", "")).strip(),
            version=str(data.get("version", "")).strip(),
            api_version=str(data.get("api_version", "1.2")).strip(),
            ntpe_min_version=str(data.get("ntpe_min_version", "1.1.0")).strip(),
            ntpe_max_version=data.get("ntpe_max_version"),
            author=str(data.get("author", "unknown")).strip(),
            description=str(data.get("description", "")),
            capabilities=tuple(data.get("capabilities", ()) or ()),
            dependencies=tuple(data.get("dependencies", ()) or ()),
            entrypoint=str(data.get("entrypoint", "")).strip(),
            signature=data.get("signature"),
            metadata=dict(data.get("metadata", {}) or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["capabilities"] = list(self.capabilities)
        payload["dependencies"] = list(self.dependencies)
        return payload

    def validate(self, ntpe_version: str = "1.2.0") -> dict[str, Any]:
        errors: list[str] = []
        if not self.plugin_id:
            errors.append("plugin_id is required")
        if not self.name:
            errors.append("name is required")
        if not self.version:
            errors.append("version is required")
        invalid = [cap for cap in self.capabilities if cap not in _ALLOWED_CAPABILITIES]
        if invalid:
            errors.append("invalid capabilities: " + ", ".join(sorted(invalid)))
        try:
            policy = VersionPolicy(self.ntpe_min_version, self.ntpe_max_version)
            if not policy.accepts(ntpe_version):
                errors.append(f"ntpe version not supported: {ntpe_version}")
        except ValueError as exc:
            errors.append(str(exc))
        return {
            "status": "success" if not errors else "failed",
            "plugin_id": self.plugin_id,
            "errors": errors,
        }
