from pathlib import Path
from typing import Any
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.plugins import PluginBase, PluginContext, PluginRegistry
from core.runtime import RuntimeManager


class AddOnePlugin(PluginBase):
    name = "add_one"
    stage = "math"
    priority = 10

    def run(self, payload: dict[str, Any], context: PluginContext) -> dict[str, Any]:
        payload["value"] = payload.get("value", 0) + 1
        return payload


class MultiplyPlugin(PluginBase):
    name = "multiply"
    stage = "math"
    priority = 20

    def run(self, payload: dict[str, Any], context: PluginContext) -> dict[str, Any]:
        payload["value"] = payload.get("value", 0) * 10
        return payload


ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    runtime = RuntimeManager(ROOT)
    context = PluginContext(root=ROOT, runtime=runtime)

    registry = PluginRegistry(context)
    registry.register(AddOnePlugin())
    registry.register(MultiplyPlugin())

    result = registry.run_stage("math", {"value": 2})

    checks = {
        "Registered Plugins": registry.list_plugins() == ["add_one", "multiply"],
        "Registered Stage": registry.list_stages() == ["math"],
        "Stage Execution": result["value"] == 30,
        "Runtime Context": context.runtime is runtime,
    }

    print("NTPE v1.2 Foundation Plugin Registry Test")
    print("=========================================")

    for name, ok in checks.items():
        print(f"{name:<22} {'PASS' if ok else 'FAIL'}")

    if not all(checks.values()):
        print("FAIL")
        raise SystemExit(2)

    print("PASS")