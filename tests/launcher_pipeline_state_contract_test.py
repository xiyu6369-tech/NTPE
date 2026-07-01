"""
NTPE Foundation-04.4 Pipeline State Contract Test
Run:
    python tests\launcher_pipeline_state_contract_test.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.pipeline_state_contract import (
    attach_payload_to_state,
    complete_stage_state,
    create_pipeline_state,
    fail_stage_state,
    normalize_pipeline_state,
    record_adapter_trace,
    record_plugin_trace,
    update_stage_state,
    validate_pipeline_state,
)
from core.pipeline_state_adapter import PipelineStateAdapter


def check(label: str, condition: bool) -> None:
    status = "PASS" if condition else "FAIL"
    print(f"{label:<22} {status}")
    if not condition:
        raise AssertionError(label)


def main() -> None:
    print("NTPE Foundation-04.4 Pipeline State Contract Test")
    print("=" * 58)

    legacy = {
        "stage": "context",
        "done_stages": ["bootstrap"],
        "failures": [],
    }
    normalized = normalize_pipeline_state(legacy)
    check("Legacy State", normalized["current_stage"] == "context")
    check("Legacy Completed", normalized["completed_stages"] == ["bootstrap"])
    check("Counters Created", normalized["counters"]["stage_count"] == 1)

    payload = {
        "text": "안녕하세요.",
        "language": "繁體中文",
    }
    state = create_pipeline_state(payload, stage="context")
    check("State Created", state["state_version"] == "04.4")
    check("Payload Attached", state["payload"]["source_text"] == "안녕하세요.")

    running = update_stage_state(state, "prompt", "running")
    check("Stage Running", running["current_stage"] == "prompt")
    check("Status Running", running["status"] == "running")

    adapter_traced = record_adapter_trace(running, "unit_adapter", "before")
    check("Adapter Trace", adapter_traced["counters"]["adapter_count"] == 1)

    plugin_traced = record_plugin_trace(adapter_traced, "quality_plugin", "after")
    check("Plugin Trace", plugin_traced["counters"]["plugin_count"] == 1)

    completed = complete_stage_state(plugin_traced, "prompt")
    check("Stage Completed", "prompt" in completed["completed_stages"])
    check("Completed Status", completed["status"] == "completed")

    validated = validate_pipeline_state(completed)
    check("Validate State", validated.ok is True)

    attached = attach_payload_to_state(completed, {"source_text": "새 문장", "target_language": "繁體中文"})
    check("Attach Payload", attached["payload"]["source_text"] == "새 문장")

    failed = fail_stage_state(attached, "quality", "quality gate failed")
    check("Failure Status", failed["status"] == "failed")
    check("Failure Counter", failed["counters"]["error_count"] == 1)

    adapter = PipelineStateAdapter()
    created_by_adapter = adapter.create(payload, stage="context")
    before = adapter.before_stage(created_by_adapter, "narrative")
    after = adapter.after_stage(before, "narrative")
    check("Adapter Before", before["current_stage"] == "narrative")
    check("Adapter After", "narrative" in after["completed_stages"])
    check("Adapter Counter", after["counters"]["adapter_count"] == 2)

    print("PASS")


if __name__ == "__main__":
    main()
