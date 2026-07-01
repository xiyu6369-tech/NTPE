"""
NTPE Foundation-05.6 Production Runtime
Incremental module: integrates Stage Registry, Dependency Resolver, Scheduler,
Lifecycle Manager, Metrics, and Production Pipeline Contract Integration.

This module is intentionally dependency-light and backward-compatible. It uses
soft imports where possible so older Foundation snapshots can still load it.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, Iterable, List, Optional
import time
import uuid


RuntimeHandler = Callable[[Dict[str, Any]], Dict[str, Any]]


@dataclass
class ProductionRuntimeConfig:
    runtime_id: str = "production-runtime"
    version: str = "05.6"
    strict: bool = True
    collect_metrics: bool = True
    enable_trace: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ProductionRuntimeResult:
    ok: bool
    status: str
    output: Dict[str, Any] = field(default_factory=dict)
    state: Dict[str, Any] = field(default_factory=dict)
    trace: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def create_runtime_config(**kwargs: Any) -> Dict[str, Any]:
    return ProductionRuntimeConfig(**kwargs).to_dict()


def validate_runtime_config(config: Dict[str, Any]) -> bool:
    if not isinstance(config, dict):
        return False
    if not config.get("runtime_id"):
        return False
    if not config.get("version"):
        return False
    return True


def create_runtime_event(event_type: str, **data: Any) -> Dict[str, Any]:
    return {
        "event_id": str(uuid.uuid4()),
        "type": event_type,
        "timestamp": time.time(),
        "data": data,
    }


def create_runtime_state(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    cfg = config or create_runtime_config()
    return {
        "runtime": cfg,
        "status": "created",
        "counters": {
            "runs": 0,
            "success": 0,
            "failure": 0,
            "stages": 0,
            "events": 0,
        },
        "events": [],
        "payload": {},
    }


def append_runtime_event(state: Dict[str, Any], event_type: str, **data: Any) -> Dict[str, Any]:
    event = create_runtime_event(event_type, **data)
    state.setdefault("events", []).append(event)
    state.setdefault("counters", {}).setdefault("events", 0)
    state["counters"]["events"] += 1
    return event


def normalize_runtime_payload(payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if payload is None:
        payload = {}
    if not isinstance(payload, dict):
        payload = {"source": payload}
    payload.setdefault("source", "")
    payload.setdefault("context", {})
    payload.setdefault("metadata", {})
    return payload


class ProductionRuntime:
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or create_runtime_config()
        if not validate_runtime_config(self.config):
            raise ValueError("Invalid production runtime config")
        self.handlers: Dict[str, RuntimeHandler] = {}
        self.stage_order: List[str] = []
        self.state = create_runtime_state(self.config)

    def register_stage(self, stage_id: str, handler: RuntimeHandler, *, enabled: bool = True) -> None:
        if not stage_id:
            raise ValueError("stage_id is required")
        if not callable(handler):
            raise TypeError("handler must be callable")
        self.handlers[stage_id] = handler
        if enabled and stage_id not in self.stage_order:
            self.stage_order.append(stage_id)
        append_runtime_event(self.state, "runtime.stage_registered", stage_id=stage_id, enabled=enabled)

    def set_schedule(self, stage_ids: Iterable[str]) -> None:
        ordered = list(stage_ids)
        missing = [stage_id for stage_id in ordered if stage_id not in self.handlers]
        if missing and self.config.get("strict", True):
            raise ValueError(f"Unknown stage(s): {', '.join(missing)}")
        self.stage_order = [stage_id for stage_id in ordered if stage_id in self.handlers]
        append_runtime_event(self.state, "runtime.schedule_set", stages=list(self.stage_order))

    def run(self, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        start = time.perf_counter()
        self.state["status"] = "running"
        self.state["payload"] = normalize_runtime_payload(payload)
        self.state["counters"]["runs"] += 1
        append_runtime_event(self.state, "runtime.started", stages=list(self.stage_order))

        output = dict(self.state["payload"])
        stage_records: List[Dict[str, Any]] = []

        try:
            for index, stage_id in enumerate(self.stage_order):
                stage_start = time.perf_counter()
                append_runtime_event(self.state, "runtime.stage_started", stage_id=stage_id, index=index)
                result = self.handlers[stage_id](output)
                if result is None:
                    result = output
                if not isinstance(result, dict):
                    result = {"value": result}
                output.update(result)
                elapsed = time.perf_counter() - stage_start
                stage_records.append({
                    "stage_id": stage_id,
                    "index": index,
                    "status": "completed",
                    "duration_seconds": elapsed,
                })
                self.state["counters"]["stages"] += 1
                append_runtime_event(self.state, "runtime.stage_completed", stage_id=stage_id, duration_seconds=elapsed)

            self.state["status"] = "completed"
            self.state["counters"]["success"] += 1
            total = time.perf_counter() - start
            metrics = self._build_metrics("completed", total, stage_records)
            trace = self._build_trace()
            append_runtime_event(self.state, "runtime.completed", duration_seconds=total)
            return ProductionRuntimeResult(True, "completed", output, self.state, trace, metrics).to_dict()

        except Exception as exc:
            self.state["status"] = "failed"
            self.state["counters"]["failure"] += 1
            total = time.perf_counter() - start
            append_runtime_event(self.state, "runtime.failed", error=str(exc), duration_seconds=total)
            metrics = self._build_metrics("failed", total, stage_records)
            trace = self._build_trace()
            return ProductionRuntimeResult(False, "failed", output, self.state, trace, metrics, error=str(exc)).to_dict()

    def _build_trace(self) -> Dict[str, Any]:
        return {
            "runtime_id": self.config.get("runtime_id"),
            "version": self.config.get("version"),
            "events": list(self.state.get("events", [])),
        }

    def _build_metrics(self, status: str, duration: float, stages: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "runtime_id": self.config.get("runtime_id"),
            "status": status,
            "duration_seconds": duration,
            "stage_count": len(stages),
            "stages": stages,
            "counters": dict(self.state.get("counters", {})),
        }

    def manifest(self) -> Dict[str, Any]:
        return {
            "runtime": self.config,
            "status": self.state.get("status"),
            "registered_stages": list(self.handlers.keys()),
            "schedule": list(self.stage_order),
            "counters": dict(self.state.get("counters", {})),
        }


class ProductionRuntimeAdapter:
    def __init__(self, runtime: Optional[ProductionRuntime] = None) -> None:
        self.runtime = runtime or ProductionRuntime()

    def register(self, stage_id: str, handler: RuntimeHandler, **kwargs: Any) -> "ProductionRuntimeAdapter":
        self.runtime.register_stage(stage_id, handler, **kwargs)
        return self

    def schedule(self, stage_ids: Iterable[str]) -> "ProductionRuntimeAdapter":
        self.runtime.set_schedule(stage_ids)
        return self

    def run(self, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.runtime.run(payload)

    def validate(self) -> bool:
        return validate_runtime_config(self.runtime.config)

    def manifest(self) -> Dict[str, Any]:
        return self.runtime.manifest()


# Backward-compatible helper aliases
create_production_runtime_config = create_runtime_config
create_production_runtime_state = create_runtime_state
normalize_production_runtime_payload = normalize_runtime_payload
