import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.production.production_runtime import (
    ProductionRuntime,
    ProductionRuntimeAdapter,
    create_runtime_config,
    validate_runtime_config,
    create_runtime_state,
    normalize_runtime_payload,
)


def check(name, cond):
    print(f"{name:<28} {'PASS' if cond else 'FAIL'}")
    if not cond:
        raise AssertionError(name)


def main():
    print("NTPE Foundation-05.6 Production Runtime Test")
    print("==========================================")

    cfg = create_runtime_config(runtime_id="test-runtime")
    check("Config Created", cfg["runtime_id"] == "test-runtime")
    check("Validate Config", validate_runtime_config(cfg))

    state = create_runtime_state(cfg)
    check("State Created", state["status"] == "created")

    payload = normalize_runtime_payload({"source": "hello"})
    check("Payload Normalized", payload["source"] == "hello" and "context" in payload)

    rt = ProductionRuntime(cfg)
    check("Runtime Created", rt.manifest()["status"] == "created")

    def context_stage(p):
        return {"context": {"target_language": "zh-TW"}}

    def quality_stage(p):
        return {"quality": {"ok": True}}

    rt.register_stage("context", context_stage)
    rt.register_stage("quality", quality_stage)
    check("Stage Registered", rt.manifest()["registered_stages"] == ["context", "quality"])

    rt.set_schedule(["context", "quality"])
    check("Schedule Set", rt.manifest()["schedule"] == ["context", "quality"])

    result = rt.run({"source": "안녕하세요"})
    check("Runtime Completed", result["ok"] is True and result["status"] == "completed")
    check("Output Context", result["output"]["context"]["target_language"] == "zh-TW")
    check("Output Quality", result["output"]["quality"]["ok"] is True)
    check("Runtime Trace", len(result["trace"]["events"]) >= 4)
    check("Runtime Metrics", result["metrics"]["stage_count"] == 2)

    def fail_stage(p):
        raise RuntimeError("expected failure")

    fail_rt = ProductionRuntime(cfg)
    fail_rt.register_stage("fail", fail_stage)
    failed = fail_rt.run({"source": "x"})
    check("Runtime Failed", failed["ok"] is False and failed["status"] == "failed")
    check("Failure Error", "expected failure" in failed["error"])
    check("Failure Metrics", failed["metrics"]["status"] == "failed")

    adapter = ProductionRuntimeAdapter(ProductionRuntime(cfg))
    adapter.register("context", context_stage).register("quality", quality_stage).schedule(["context", "quality"])
    check("Adapter Created", adapter.validate())
    ar = adapter.run({"source": "adapter"})
    check("Adapter Run", ar["ok"] is True)
    check("Adapter Manifest", adapter.manifest()["schedule"] == ["context", "quality"])

    # Backward-compatible loose schedule behavior
    loose_cfg = create_runtime_config(strict=False)
    loose = ProductionRuntime(loose_cfg)
    loose.register_stage("context", context_stage)
    loose.set_schedule(["missing", "context"])
    check("Backward Compatible", loose.manifest()["schedule"] == ["context"])

    print("PASS")


if __name__ == "__main__":
    main()
