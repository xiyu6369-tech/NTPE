"""
NTPE Foundation-05.1 Pipeline Stage Registry

Incremental module for registering, validating, querying, and exporting
production pipeline stages without mutating existing Foundation-04.x / 05.0
contracts.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, Iterable, List, Mapping, MutableMapping, Optional, Tuple


StageHandler = Callable[[Any], Any]


@dataclass(frozen=True)
class PipelineStageDefinition:
    """Stable contract object describing a pipeline stage."""

    name: str
    version: str = "1.0.0"
    handler: Optional[StageHandler] = None
    enabled: bool = True
    priority: int = 100
    dependencies: Tuple[str, ...] = field(default_factory=tuple)
    provides: Tuple[str, ...] = field(default_factory=tuple)
    tags: Tuple[str, ...] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def stage_id(self) -> str:
        return build_stage_id(self.name, self.version)

    def to_dict(self, include_handler: bool = False) -> Dict[str, Any]:
        data = asdict(self)
        data["stage_id"] = self.stage_id
        data["dependencies"] = list(self.dependencies)
        data["provides"] = list(self.provides)
        data["tags"] = list(self.tags)
        data["metadata"] = dict(self.metadata or {})
        if include_handler:
            data["handler"] = self.handler
        else:
            data.pop("handler", None)
        return data


def build_stage_id(name: str, version: str = "1.0.0") -> str:
    name = normalize_stage_name(name)
    version = str(version or "1.0.0").strip()
    return f"{name}@{version}"


def normalize_stage_name(name: str) -> str:
    value = str(name or "").strip()
    if not value:
        raise ValueError("stage name is required")
    return value


def normalize_stage_definition(stage: Any, **overrides: Any) -> PipelineStageDefinition:
    """Normalize legacy dict/object/function inputs into a stage definition."""

    if isinstance(stage, PipelineStageDefinition):
        data = stage.to_dict(include_handler=True)
    elif isinstance(stage, Mapping):
        data = dict(stage)
    elif callable(stage):
        data = {
            "name": getattr(stage, "__name__", "anonymous_stage"),
            "handler": stage,
        }
    else:
        # Lightweight object compatibility for existing plugin/stage classes.
        data = {
            key: getattr(stage, key)
            for key in (
                "name",
                "version",
                "handler",
                "enabled",
                "priority",
                "dependencies",
                "provides",
                "tags",
                "metadata",
            )
            if hasattr(stage, key)
        }
        if "handler" not in data and callable(stage):
            data["handler"] = stage

    data.update({k: v for k, v in overrides.items() if v is not None})

    name = normalize_stage_name(data.get("name") or data.get("stage") or data.get("id"))
    version = str(data.get("version") or "1.0.0").strip()

    def _tuple(value: Any) -> Tuple[str, ...]:
        if value is None:
            return tuple()
        if isinstance(value, str):
            return (value,)
        return tuple(str(item) for item in value)

    return PipelineStageDefinition(
        name=name,
        version=version,
        handler=data.get("handler"),
        enabled=bool(data.get("enabled", True)),
        priority=int(data.get("priority", 100)),
        dependencies=_tuple(data.get("dependencies") or data.get("requires")),
        provides=_tuple(data.get("provides")),
        tags=_tuple(data.get("tags")),
        metadata=dict(data.get("metadata") or {}),
    )


def validate_stage_definition(stage: PipelineStageDefinition) -> bool:
    if not isinstance(stage, PipelineStageDefinition):
        raise TypeError("stage must be PipelineStageDefinition")
    normalize_stage_name(stage.name)
    if not stage.version:
        raise ValueError("stage version is required")
    if stage.handler is not None and not callable(stage.handler):
        raise TypeError("stage handler must be callable")
    if not isinstance(stage.priority, int):
        raise TypeError("stage priority must be int")
    return True


class PipelineStageRegistry:
    """In-memory stage registry used by Production Pipeline runtime."""

    def __init__(self) -> None:
        self._stages: Dict[str, PipelineStageDefinition] = {}
        self._latest_by_name: Dict[str, str] = {}
        self._events: List[Dict[str, Any]] = []

    def register(self, stage: Any, **overrides: Any) -> PipelineStageDefinition:
        definition = normalize_stage_definition(stage, **overrides)
        validate_stage_definition(definition)
        self._stages[definition.stage_id] = definition
        self._latest_by_name[definition.name] = definition.stage_id
        self._events.append({"type": "stage_registered", "stage_id": definition.stage_id})
        return definition

    def unregister(self, name: str, version: Optional[str] = None) -> Optional[PipelineStageDefinition]:
        stage_id = self.resolve_stage_id(name, version)
        removed = self._stages.pop(stage_id, None)
        if removed:
            remaining = [s for s in self._stages.values() if s.name == removed.name]
            if remaining:
                latest = sorted(remaining, key=lambda s: s.version)[-1]
                self._latest_by_name[removed.name] = latest.stage_id
            else:
                self._latest_by_name.pop(removed.name, None)
            self._events.append({"type": "stage_unregistered", "stage_id": stage_id})
        return removed

    def resolve_stage_id(self, name: str, version: Optional[str] = None) -> str:
        name = normalize_stage_name(name)
        if version:
            return build_stage_id(name, version)
        if name in self._latest_by_name:
            return self._latest_by_name[name]
        # Allow callers to pass full stage_id.
        if "@" in name and name in self._stages:
            return name
        return build_stage_id(name)

    def get(self, name: str, version: Optional[str] = None) -> PipelineStageDefinition:
        stage_id = self.resolve_stage_id(name, version)
        if stage_id not in self._stages:
            raise KeyError(f"stage not registered: {stage_id}")
        return self._stages[stage_id]

    def exists(self, name: str, version: Optional[str] = None) -> bool:
        try:
            return self.resolve_stage_id(name, version) in self._stages
        except Exception:
            return False

    def enable(self, name: str, version: Optional[str] = None) -> PipelineStageDefinition:
        return self._replace_enabled(name, version, True)

    def disable(self, name: str, version: Optional[str] = None) -> PipelineStageDefinition:
        return self._replace_enabled(name, version, False)

    def _replace_enabled(self, name: str, version: Optional[str], enabled: bool) -> PipelineStageDefinition:
        current = self.get(name, version)
        updated = PipelineStageDefinition(
            name=current.name,
            version=current.version,
            handler=current.handler,
            enabled=enabled,
            priority=current.priority,
            dependencies=current.dependencies,
            provides=current.provides,
            tags=current.tags,
            metadata=current.metadata,
        )
        self._stages[updated.stage_id] = updated
        self._events.append({"type": "stage_enabled" if enabled else "stage_disabled", "stage_id": updated.stage_id})
        return updated

    def list(self, enabled_only: bool = False, tag: Optional[str] = None) -> List[PipelineStageDefinition]:
        stages = list(self._stages.values())
        if enabled_only:
            stages = [stage for stage in stages if stage.enabled]
        if tag:
            stages = [stage for stage in stages if tag in stage.tags]
        return sorted(stages, key=lambda s: (s.priority, s.name, s.version))

    def handlers(self, enabled_only: bool = True) -> List[StageHandler]:
        return [stage.handler for stage in self.list(enabled_only=enabled_only) if stage.handler is not None]

    def export_manifest(self) -> Dict[str, Any]:
        return {
            "schema": "ntpe.pipeline.stage_registry.v1",
            "count": len(self._stages),
            "stages": [stage.to_dict() for stage in self.list()],
            "events": list(self._events),
        }

    def import_manifest(self, manifest: Mapping[str, Any]) -> None:
        for item in manifest.get("stages", []):
            self.register(item)


def create_stage_registry(stages: Optional[Iterable[Any]] = None) -> PipelineStageRegistry:
    registry = PipelineStageRegistry()
    for stage in stages or []:
        registry.register(stage)
    return registry
