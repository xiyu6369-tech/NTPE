from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.plugins import (
    PluginContext,
    PluginRegistry,
    ContextMemoryPlugin,
    PromptBuilderPlugin,
)
from core.runtime import RuntimeManager


if __name__ == "__main__":
    runtime = RuntimeManager(ROOT)
    context = PluginContext(root=ROOT, runtime=runtime)

    registry = PluginRegistry(context)
    registry.register(ContextMemoryPlugin())
    registry.register(PromptBuilderPlugin())

    payload = {
        "previous_tail": "鄭泰義帶著煩躁的目光望向玄關。",
        "chunk_text": """
초인종이 울린 순간 정태의는 멈칫했다.

손에 쥐고 있던 젓가락에서 콩자반이 떨어져 굴렀다.
""",
        "file_name": "prompt_plugin_test.txt",
        "chunk_index": 1,
        "chunk_total": 1,
        "session_id": "PROMPT_PLUGIN_TEST",
    }

    payload = registry.run_stage("context", payload)
    result = registry.run_stage("prompt", payload)

    package = result.get("prompt_package", {})
    prompt = result.get("prompt", {})

    checks = {
        "Context Plugin": "context" in result,
        "Prompt Package": bool(package),
        "Prompt": bool(prompt),
        "System Prompt": bool(prompt.get("system_prompt")),
        "User Prompt": bool(prompt.get("user_prompt")),
        "Package ID": bool(package.get("package_id")),
    }

    print("NTPE v1.2 Foundation Prompt Plugin Test")
    print("=======================================")

    for name, ok in checks.items():
        print(f"{name:<18} {'PASS' if ok else 'FAIL'}")

    if not all(checks.values()):
        print("FAIL")
        raise SystemExit(2)

    print("PASS")