"""NTPE Stage-09.8 Workflow Freeze helpers.

This module is additive. It freezes the Workflow v1.0 public contract
without modifying Foundation, CLI, SDK, Integration, Runtime, Job Scheduler,
Pipeline, Task Queue, Worker Runtime, Persistence, or Distributed Execution.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List
import json

WORKFLOW_FREEZE_VERSION = "1.0.0"
WORKFLOW_FREEZE_STAGE = "NTPE 1.0 Beta Stage-09.8 Workflow Freeze"
WORKFLOW_FREEZE_STATUS = "frozen"
FOUNDATION_FREEZE_STATUS = "frozen"
INTEGRATION_FREEZE_STATUS = "frozen"

REQUIRED_WORKFLOW_CONTRACTS = [
    "workflow_core",
    "job_scheduler",
    "pipeline_orchestrator",
    "task_queue",
    "worker_runtime",
    "workflow_persistence",
    "distributed_execution",
]

WORKFLOW_COMPATIBILITY_TARGETS = [
    "foundation_v1",
    "cli_freeze",
    "sdk_stage_07",
    "integration_freeze",
    "workflow_core",
    "job_scheduler",
    "pipeline_orchestrator",
    "task_queue",
    "worker_runtime",
    "workflow_persistence",
    "distributed_execution",
    "workflow_benchmark",
]


@dataclass
class WorkflowFreezeResult:
    ok: bool
    status: str
    version: str = WORKFLOW_FREEZE_VERSION
    contracts: List[str] = field(default_factory=list)
    compatibility: Dict[str, bool] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "status": self.status,
            "version": self.version,
            "contracts": list(self.contracts),
            "compatibility": dict(self.compatibility),
            "errors": list(self.errors),
        }


def build_workflow_freeze_manifest(metadata: Dict[str, Any] | None = None) -> Dict[str, Any]:
    return {
        "name": "ntpe-workflow",
        "version": WORKFLOW_FREEZE_VERSION,
        "stage": WORKFLOW_FREEZE_STAGE,
        "status": WORKFLOW_FREEZE_STATUS,
        "foundation_status": FOUNDATION_FREEZE_STATUS,
        "integration_status": INTEGRATION_FREEZE_STATUS,
        "additive_only": True,
        "contracts": list(REQUIRED_WORKFLOW_CONTRACTS),
        "compatibility_targets": list(WORKFLOW_COMPATIBILITY_TARGETS),
        "metadata": dict(metadata or {}),
    }


def build_workflow_contract() -> Dict[str, Any]:
    return {
        "contract_version": WORKFLOW_FREEZE_VERSION,
        "status": WORKFLOW_FREEZE_STATUS,
        "frozen_surfaces": {
            "workflow_core": ["WorkflowCore", "WorkflowEngine", "WorkflowRegistry", "WorkflowContext"],
            "job_scheduler": ["JobScheduler", "JobManager", "JobQueue", "JobRegistry", "SchedulingPolicy"],
            "pipeline_orchestrator": ["PipelineOrchestrator", "PipelineRegistry", "PipelineDispatcher", "ExecutionPlan"],
            "task_queue": ["WorkflowTaskQueue", "TaskQueue", "TaskDispatcher", "TaskQueueManager", "QueueMetrics"],
            "worker_runtime": ["WorkerRuntime", "WorkerPool", "WorkerManager", "WorkerDispatcher"],
            "workflow_persistence": ["WorkflowPersistence", "PersistenceManager", "CheckpointManager", "RecoveryManager"],
            "distributed_execution": ["DistributedCoordinator", "NodeRegistry", "DistributedScheduler", "FailoverManager"],
        },
        "rules": {
            "backward_compatible": True,
            "no_breaking_changes": True,
            "additive_extensions_allowed": True,
            "foundation_v1_required": True,
            "cli_freeze_required": True,
            "sdk_stage_07_required": True,
            "integration_freeze_required": True,
        },
    }


def build_workflow_compatibility_matrix() -> Dict[str, Any]:
    matrix = {target: True for target in WORKFLOW_COMPATIBILITY_TARGETS}
    return {
        "version": WORKFLOW_FREEZE_VERSION,
        "status": WORKFLOW_FREEZE_STATUS,
        "matrix": matrix,
        "compatible_with": [
            "Foundation v1.0 Frozen",
            "Stage-06 CLI Frozen",
            "Stage-07 SDK",
            "Stage-08 Integration Frozen",
            "Stage-09.0 Workflow Core",
            "Stage-09.1 Job Scheduler",
            "Stage-09.2 Pipeline Orchestrator",
            "Stage-09.3 Task Queue",
            "Stage-09.4 Worker Runtime",
            "Stage-09.5 Workflow Persistence",
            "Stage-09.6 Distributed Execution",
            "Stage-09.7 Workflow Benchmark",
        ],
    }


def build_workflow_version_manifest() -> Dict[str, Any]:
    return {
        "component": "workflow",
        "version": WORKFLOW_FREEZE_VERSION,
        "stage": "09.8",
        "status": WORKFLOW_FREEZE_STATUS,
        "foundation_status": FOUNDATION_FREEZE_STATUS,
        "integration_status": INTEGRATION_FREEZE_STATUS,
        "public_contract": "workflow_contract.json",
        "compatibility_matrix": "compatibility_matrix.json",
    }


def validate_workflow_freeze_manifest(manifest: Dict[str, Any]) -> WorkflowFreezeResult:
    errors: List[str] = []
    contracts = list(manifest.get("contracts", []))
    compatibility_targets = list(manifest.get("compatibility_targets", []))
    compatibility = {target: target in compatibility_targets for target in WORKFLOW_COMPATIBILITY_TARGETS}

    if manifest.get("status") != WORKFLOW_FREEZE_STATUS:
        errors.append("workflow status is not frozen")
    if manifest.get("foundation_status") != FOUNDATION_FREEZE_STATUS:
        errors.append("foundation status is not frozen")
    if manifest.get("integration_status") != INTEGRATION_FREEZE_STATUS:
        errors.append("integration status is not frozen")
    for contract in REQUIRED_WORKFLOW_CONTRACTS:
        if contract not in contracts:
            errors.append(f"missing contract: {contract}")
    for target in WORKFLOW_COMPATIBILITY_TARGETS:
        if target not in compatibility_targets:
            errors.append(f"missing compatibility target: {target}")

    return WorkflowFreezeResult(
        ok=not errors,
        status=str(manifest.get("status", "unknown")),
        contracts=contracts,
        compatibility=compatibility,
        errors=errors,
    )


def write_workflow_freeze_artifacts(directory: str | Path, metadata: Dict[str, Any] | None = None) -> Dict[str, Path]:
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    artifacts = {
        "freeze_manifest.json": build_workflow_freeze_manifest(metadata),
        "workflow_contract.json": build_workflow_contract(),
        "compatibility_matrix.json": build_workflow_compatibility_matrix(),
        "version_manifest.json": build_workflow_version_manifest(),
    }
    written: Dict[str, Path] = {}
    for name, payload in artifacts.items():
        target = path / name
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        written[name] = target
    return written


def load_workflow_json(path: str | Path) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def workflow_freeze_is_compatible(matrix: Dict[str, Any], required: Iterable[str] | None = None) -> bool:
    values = dict(matrix.get("matrix", {}))
    keys = list(required or WORKFLOW_COMPATIBILITY_TARGETS)
    return all(values.get(key) is True for key in keys)
