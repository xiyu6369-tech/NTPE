r"""
NTPE Foundation-04.5 Pipeline Execution Trace Test
Run:
    python tests\launcher_pipeline_execution_trace_test.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.pipeline_execution_trace import (
    append_trace_event,
    attach_trace_to_state,
    begin_trace_stage,
    complete_trace_stage,
    create_execution_trace,
    fail_trace_stage,
    normalize_execution_trace,
    record_trace_adapter,
    record_trace_plugin,
    state_trace_event,
    validate_execution_trace,
)
from core.pipeline_execution_trace_adapter import PipelineExecutionTraceAdapter
from core.pipeline_state_contract import create_pipeline_state


def check(label: str, condition: bool) -> None:
    status = "PASS" if condition else "FAIL"
    print(f"{label:<24} {status}")
    if not condition:
        raise AssertionError(label)


def main() -> None:
    print("NTPE Foundation-04.5 Pipeline Execution Trace Test")
    print("=" * 62)

    legacy = {
        "id": "legacy-trace",
        "trace": [{"event_type": "stage", "event": "started", "stage": "context"}],
    }
    normalized = normalize_execution_trace(legacy)
    check("Legacy Trace", normalized["trace_id"] == "legacy-trace")
    check("Legacy Event", normalized["events"][0]["type"] == "stage")
    check("Summary Created", normalized["summary"]["event_count"] == 1)

    trace = create_execution_trace(trace_id="unit-trace")
    check("Trace Created", trace["trace_version"] == "04.5")
    check("Trace ID", trace["trace_id"] == "unit-trace")

    trace = begin_trace_stage(trace, "context")
    check("Stage Begin", trace["events"][-1]["name"] == "context")
    check("Stage Counter", trace["summary"]["stage_event_count"] == 1)

    trace = record_trace_plugin(trace, "context_plugin")
    check("Plugin Event", trace["summary"]["plugin_event_count"] == 1)

    trace = record_trace_adapter(trace, "context_adapter")
    check("Adapter Event", trace["summary"]["adapter_event_count"] == 1)

    trace = complete_trace_stage(trace, "context")
    check("Stage Complete", trace["events"][-1]["status"] == "completed")

    trace = append_trace_event(trace, "payload", "attached", name="payload")
    check("Payload Event", trace["events"][-1]["type"] == "payload")

    failed_trace = fail_trace_stage(trace, "quality", "quality gate failed")
    check("Failure Event", failed_trace["summary"]["error_event_count"] == 1)

    validated = validate_execution_trace(failed_trace)
    check("Validate Trace", validated.ok is True)

    state = create_pipeline_state({"text": "안녕하세요.", "language": "繁體中文"}, stage="context")
    attached = attach_trace_to_state(state, trace)
    check("Attach To State", attached["execution_trace"]["trace_id"] == "unit-trace")

    state_evented = state_trace_event(attached, "quality", "validated", name="quality_gate")
    check("State Event", state_evented["execution_trace"]["events"][-1]["name"] == "quality_gate")

    adapter = PipelineExecutionTraceAdapter()
    adapter_trace = adapter.create(trace_id="adapter-trace")
    adapter_trace = adapter.before_stage(adapter_trace, "prompt")
    adapter_trace = adapter.plugin(adapter_trace, "prompt_plugin")
    adapter_trace = adapter.adapter(adapter_trace, "prompt_adapter")
    adapter_trace = adapter.after_stage(adapter_trace, "prompt")
    check("Adapter Before", adapter_trace["events"][1]["name"] == "prompt")
    check("Adapter Plugin", adapter_trace["summary"]["plugin_event_count"] == 1)
    check("Adapter Counter", adapter_trace["summary"]["adapter_event_count"] == 1)
    check("Adapter After", adapter_trace["events"][-1]["status"] == "completed")

    print("PASS")


if __name__ == "__main__":
    main()
