from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.plugins import PluginContext, PluginRegistry, ContextMemoryPlugin
from core.runtime import RuntimeManager


if __name__ == "__main__":
    runtime = RuntimeManager(ROOT)
    context = PluginContext(root=ROOT, runtime=runtime)

    registry = PluginRegistry(context)
    registry.register(ContextMemoryPlugin())

    payload = {
        "previous_tail": "鄭泰義帶著煩躁的目光望向玄關。"
    }

    result = registry.run_stage("context", payload)

    checks = {
        "Plugin Registered": "context_memory" in registry.list_plugins(),
        "Stage Registered": "context" in registry.list_stages(),
        "Context Output": "context" in result,
        "Previous Summary": bool(result["context"].get("previous_summary")),
        "Previous Tail": bool(result["context"].get("previous_chunk_tail")),
    }

    print("NTPE v1.2 Foundation Context Plugin Test")
    print("========================================")

    for name, ok in checks.items():
        print(f"{name:<18} {'PASS' if ok else 'FAIL'}")

    if not all(checks.values()):
        print("FAIL")
        raise SystemExit(2)

    print("PASS")