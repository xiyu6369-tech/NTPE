from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.plugins import PipelinePluginManager


if __name__ == "__main__":
    manager = PipelinePluginManager(ROOT)
    registry = manager.build_registry()

    plugins = registry.list_plugins()
    stages = registry.list_stages()

    checks = {
        "Context Plugin": "context_memory" in plugins,
        "Narrative Plugin": "narrative" in plugins,
        "Prompt Plugin": "prompt_builder" in plugins,
        "Quality Plugin": "quality" in plugins,
        "Context Stage": "context" in stages,
        "Narrative Stage": "narrative" in stages,
        "Prompt Stage": "prompt" in stages,
        "Quality Stage": "quality" in stages,
    }

    print("NTPE v1.2 Foundation Pipeline Plugin Manager Test")
    print("=================================================")

    for name, ok in checks.items():
        print(f"{name:<18} {'PASS' if ok else 'FAIL'}")

    if not all(checks.values()):
        print("FAIL")
        raise SystemExit(2)

    print("PASS")