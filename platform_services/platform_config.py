"""Platform service configuration layer for NTPE 1.0 Beta Stage-10.1.

This module is additive to Stage-10.0. It provides a small in-memory
configuration contract that platform services can consume without changing
Foundation, CLI, SDK, Integration, or Workflow frozen APIs.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Mapping, Optional

PLATFORM_CONFIG_VERSION = "1.0.0-beta.10.1"
PLATFORM_CONFIG_STAGE = "10.1"


@dataclass(frozen=True)
class PlatformConfigEntry:
    """Single resolved platform configuration entry."""

    key: str
    value: Any
    source: str = "default"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.key or not str(self.key).strip():
            raise ValueError("platform config key is required")
        object.__setattr__(self, "key", str(self.key))
        object.__setattr__(self, "source", str(self.source or "default"))
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "source": self.source,
            "metadata": dict(self.metadata),
        }


class PlatformConfigStore:
    """Deterministic in-memory configuration store for platform services."""

    version = PLATFORM_CONFIG_VERSION
    stage = PLATFORM_CONFIG_STAGE

    def __init__(self, initial: Optional[Mapping[str, Any]] = None, *, source: str = "initial", metadata: Optional[Dict[str, Any]] = None) -> None:
        self.metadata = dict(metadata or {})
        self._entries: Dict[str, PlatformConfigEntry] = {}
        if initial:
            self.load(initial, source=source)

    def set(self, key: str, value: Any, *, source: str = "runtime", metadata: Optional[Dict[str, Any]] = None) -> PlatformConfigEntry:
        entry = PlatformConfigEntry(key=key, value=value, source=source, metadata=dict(metadata or {}))
        self._entries[entry.key] = entry
        return entry

    def load(self, values: Mapping[str, Any], *, source: str = "load", metadata: Optional[Dict[str, Any]] = None) -> "PlatformConfigStore":
        for key, value in dict(values).items():
            self.set(str(key), value, source=source, metadata=metadata)
        return self

    def get(self, key: str, default: Any = None) -> Any:
        entry = self._entries.get(str(key))
        return default if entry is None else entry.value

    def entry(self, key: str) -> Optional[PlatformConfigEntry]:
        return self._entries.get(str(key))

    def require(self, key: str) -> Any:
        entry = self.entry(key)
        if entry is None:
            raise KeyError(f"platform config not found: {key}")
        return entry.value

    def merge(self, *stores: "PlatformConfigStore") -> "PlatformConfigStore":
        merged = PlatformConfigStore(metadata={"merged": True, **self.metadata})
        for entry in self.entries():
            merged.set(entry.key, entry.value, source=entry.source, metadata=entry.metadata)
        for store in stores:
            for entry in store.entries():
                merged.set(entry.key, entry.value, source=entry.source, metadata=entry.metadata)
        return merged

    def subset(self, keys: Iterable[str]) -> Dict[str, Any]:
        return {str(key): self.require(str(key)) for key in keys}

    def entries(self) -> tuple[PlatformConfigEntry, ...]:
        return tuple(self._entries.values())

    def values(self) -> Dict[str, Any]:
        return {key: entry.value for key, entry in self._entries.items()}

    def manifest(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "stage": self.stage,
            "count": len(self._entries),
            "keys": sorted(self._entries.keys()),
            "entries": [entry.to_dict() for entry in self.entries()],
            "metadata": dict(self.metadata),
        }


@dataclass
class PlatformServiceConfig:
    """Configuration snapshot attached to a platform service."""

    service_name: str
    store: PlatformConfigStore = field(default_factory=PlatformConfigStore)
    defaults: Dict[str, Any] = field(default_factory=dict)
    overrides: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    version = PLATFORM_CONFIG_VERSION
    stage = PLATFORM_CONFIG_STAGE

    def __post_init__(self) -> None:
        if not self.service_name or not str(self.service_name).strip():
            raise ValueError("platform service config requires service_name")
        self.service_name = str(self.service_name)
        self.defaults = dict(self.defaults)
        self.overrides = dict(self.overrides)
        self.metadata = dict(self.metadata)
        self.store = PlatformConfigStore(self.defaults, source="default", metadata={"service": self.service_name}).merge(self.store)
        self.store.load(self.overrides, source="override", metadata={"service": self.service_name})

    def get(self, key: str, default: Any = None) -> Any:
        return self.store.get(key, default)

    def require(self, key: str) -> Any:
        return self.store.require(key)

    def as_kwargs(self, keys: Iterable[str]) -> Dict[str, Any]:
        return self.store.subset(keys)

    def manifest(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "stage": self.stage,
            "service_name": self.service_name,
            "config": self.store.manifest(),
            "metadata": dict(self.metadata),
            "foundation_status": "frozen",
            "cli_status": "frozen",
            "sdk_status": "complete",
            "integration_status": "frozen",
            "workflow_status": "frozen",
            "additive_only": True,
        }


def create_platform_config(initial: Optional[Mapping[str, Any]] = None, **kwargs: Any) -> PlatformConfigStore:
    return PlatformConfigStore(initial, **kwargs)


def create_service_config(service_name: str, *, defaults: Optional[Mapping[str, Any]] = None, overrides: Optional[Mapping[str, Any]] = None, store: Optional[PlatformConfigStore] = None, metadata: Optional[Dict[str, Any]] = None) -> PlatformServiceConfig:
    return PlatformServiceConfig(
        service_name=service_name,
        store=store or PlatformConfigStore(),
        defaults=dict(defaults or {}),
        overrides=dict(overrides or {}),
        metadata=dict(metadata or {}),
    )
