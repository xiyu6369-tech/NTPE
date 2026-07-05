from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4


@dataclass(frozen=True)
class TranslationResource:
    """Stable resource contract for NTPE 1.2 Professional.

    A resource is metadata-first and may be resolved lazily.  The manager never
    mutates frozen Foundation/LTS files; it only registers handles that Runtime,
    Session, Pipeline, SDK, and UI layers can share.
    """

    name: str
    kind: str
    version: str = "1.2-professional-stage-07"
    path: str | None = None
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "version": self.version,
            "path": self.path,
            "enabled": self.enabled,
            "metadata": dict(self.metadata),
        }


ResourceFactory = Callable[[Path], TranslationResource]


class TranslationResourceManager:
    """Official resource registry for the Professional runtime.

    Stage-07 is deliberately additive: resources are registered and resolved
    through this manager without replacing the Stage-06 pipeline or LTS runtime.
    """

    version = "1.2-professional-stage-07"
    compatibility_floor = "1.1-lts-stable"

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.registry: dict[str, TranslationResource] = {}
        self._load_official_defaults()

    @property
    def resource_dir(self) -> Path:
        return self.root / ".ntpe_resources"

    def register(self, resource: TranslationResource, replace: bool = False) -> TranslationResource:
        key = self._key(resource.kind, resource.name)
        if key in self.registry and not replace:
            raise ValueError(f"resource already registered: {key}")
        self.registry[key] = resource
        return resource

    def register_factory(self, kind: str, name: str, factory: ResourceFactory, replace: bool = False) -> TranslationResource:
        resource = factory(self.root)
        if resource.kind != kind or resource.name != name:
            resource = TranslationResource(
                name=name,
                kind=kind,
                version=resource.version,
                path=resource.path,
                enabled=resource.enabled,
                metadata={**resource.metadata, "factory_kind": resource.kind, "factory_name": resource.name},
            )
        return self.register(resource, replace=replace)

    def get(self, kind: str, name: str = "default") -> TranslationResource | None:
        return self.registry.get(self._key(kind, name))

    def require(self, kind: str, name: str = "default") -> TranslationResource:
        resource = self.get(kind, name)
        if resource is None:
            raise KeyError(f"missing resource: {kind}:{name}")
        return resource

    def list(self, kind: str | None = None) -> list[dict[str, Any]]:
        resources = self.registry.values()
        if kind is not None:
            resources = [resource for resource in resources if resource.kind == kind]
        return [resource.to_dict() for resource in resources]

    def describe(self) -> dict[str, Any]:
        return {
            "status": "success",
            "version": self.version,
            "compatibility_floor": self.compatibility_floor,
            "resource_count": len(self.registry),
            "resources": self.list(),
        }

    def validate(self) -> dict[str, Any]:
        required = (
            ("prompt", "default"),
            ("glossary", "default"),
            ("character_memory", "default"),
            ("context", "default"),
            ("provider", "default"),
            ("formatter", "default"),
            ("qa", "default"),
        )
        missing = [f"{kind}:{name}" for kind, name in required if self.get(kind, name) is None]
        disabled = [f"{resource.kind}:{resource.name}" for resource in self.registry.values() if not resource.enabled]
        status = "success" if not missing else "failed"
        return {
            "status": status,
            "version": self.version,
            "compatibility_floor": self.compatibility_floor,
            "missing": missing,
            "disabled": disabled,
            "resource_count": len(self.registry),
        }

    def save_manifest(self, manifest_id: str | None = None) -> dict[str, Any]:
        manifest_id = manifest_id or uuid4().hex
        path = self.resource_dir / manifest_id / "resource_manifest.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        import json

        payload = {
            "manifest_id": manifest_id,
            "version": self.version,
            "compatibility_floor": self.compatibility_floor,
            "resources": self.list(),
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"status": "success", "manifest_id": manifest_id, "manifest_path": str(path), "manifest": payload}

    def _load_official_defaults(self) -> None:
        defaults = (
            TranslationResource("default", "prompt", path=str(self.root / "prompt_packages"), metadata={"role": "prompt_builder"}),
            TranslationResource("default", "glossary", path=str(self.root / "glossary.txt"), metadata={"role": "term_lock"}),
            TranslationResource("default", "character_memory", path=str(self.root / "character_memory.json"), metadata={"role": "name_consistency"}),
            TranslationResource("default", "context", metadata={"role": "context_window"}),
            TranslationResource("default", "provider", metadata={"role": "ai_provider", "adapter": "runtime_provider"}),
            TranslationResource("default", "formatter", metadata={"role": "taiwan_formatter"}),
            TranslationResource("default", "qa", metadata={"role": "runtime_qa"}),
        )
        for resource in defaults:
            self.registry[self._key(resource.kind, resource.name)] = resource

    @staticmethod
    def _key(kind: str, name: str) -> str:
        return f"{kind}:{name}"
