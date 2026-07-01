"""
NTPE Foundation-05.0 Production Pipeline Contract Integration Test
Run from project root:
    python tests\launcher_production_pipeline_contract_integration_test.py
"""

from __future__ import annotations

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.production.production_pipeline_contract import (  # noqa: E402
    build_production_pipeline_context,
    create_production_pipeline_result,
    execute_production_pipeline,
    execute_production_pipeline_stage,
    validate_production_pipeline_result,
)


def check(label: str, condition: bool) -> None:
    print(f"{label:<24} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(label)


def main() -> None:
    print("NTPE Foundation-05.0 Production Pipeline Contract Integration Test")
    print("===============================================================")

    result = create_production_pipeline_result(status="created")
    check("Result Created", result["status"] == "created")
    check("Validate Result", validate_production_pipeline_result(result))

    context = build_production_pipeline_context(
        {"source": "안녕하세요", "target_language": "zh-TW"},
        policy={"max_attempts": 2, "fallback_enabled": True},
        metadata={"version": "Foundation-05.0"},
    )
    check("Context Created", "production_id" in context)
    check("Payload Attached", context["payload"]["source"] == "안녕하세요")
    check("State Created", context["state"]["status"] == "created")
    check("Trace Created", len(context["trace"]["events"]) >= 1)
    check("Policy Attached", context["policy"]["max_attempts"] == 2)

    def stage_ok(payload, ctx):
        return payload["source"] + " -> 你好"

    stage_result = execute_production_pipeline_stage("context", stage_ok, context)
    check("Stage Executed", stage_result["status"] == "completed")
    check("Stage Output", stage_result["output"].endswith("你好"))
    check("Stage Counter", stage_result["state"]["counters"]["stages_completed"] >= 1)
    check("Stage Trace", any(e["type"] == "stage.complete" for e in stage_result["trace"]["events"]))

    attempts = {"count": 0}

    def stage_retry(payload, ctx):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("temporary failure")
        return "retry-ok"

    retry_context = build_production_pipeline_context(
        {"source": "retry"},
        policy={"max_attempts": 2, "fallback_enabled": False},
    )
    retry_result = execute_production_pipeline_stage("quality", stage_retry, retry_context)
    check("Retry Completed", retry_result["status"] == "completed")
    check("Retry Attempts", retry_result["metadata"]["attempts"] == 2)
    check("Retry Trace", any(e["type"] == "production.retry" for e in retry_result["trace"]["events"]))

    def stage_fail(payload, ctx):
        raise ValueError("cannot translate")

    fallback_context = build_production_pipeline_context(
        {"source": "fallback"},
        policy={"max_attempts": 1, "fallback_enabled": True},
    )
    fallback_result = execute_production_pipeline_stage("prompt", stage_fail, fallback_context)
    check("Fallback Status", fallback_result["status"] == "fallback")
    check("Fallback Output", fallback_result["output"]["fallback"] is True)
    check("Fallback Recovery", fallback_result["recovery"]["decision"]["action"] == "fallback")

    abort_context = build_production_pipeline_context(
        {"source": "abort"},
        policy={"max_attempts": 1, "fallback_enabled": False},
    )
    abort_result = execute_production_pipeline_stage("narrative", stage_fail, abort_context)
    check("Abort Status", abort_result["status"] == "aborted")
    check("Abort Error", abort_result["errors"][0]["type"] == "ValueError")

    def context_stage(payload, ctx):
        payload["context"]["ready"] = True
        return payload

    def prompt_stage(payload, ctx):
        payload["metadata"]["prompt_ready"] = True
        return "prompt-ok"

    pipeline_result = execute_production_pipeline(
        {"source": "pipeline"},
        [("context", context_stage), ("prompt", prompt_stage)],
        policy={"max_attempts": 1, "fallback_enabled": False},
    )
    check("Pipeline Completed", pipeline_result["status"] == "completed")
    check("Pipeline Output", pipeline_result["output"] == "prompt-ok")
    check("Pipeline Payload", pipeline_result["payload"]["context"]["ready"] is True)
    check("Pipeline Trace", any(e["type"] == "production.complete" for e in pipeline_result["trace"]["events"]))

    print("PASS")


if __name__ == "__main__":
    main()
