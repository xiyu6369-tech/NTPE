from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.pipeline.pipeline_v1 import ProductionPipelineV1


if __name__ == "__main__":
    pipeline = ProductionPipelineV1(ROOT)

    checks = {
        "Pipeline Created": pipeline is not None,
        "Plugin Adapter": hasattr(pipeline, "plugin_adapter"),
        "Adapter Registry": hasattr(pipeline.plugin_adapter, "registry"),
        "Context Plugin": "context_memory" in pipeline.plugin_adapter.registry.list_plugins(),
        "Prompt Plugin": "prompt_builder" in pipeline.plugin_adapter.registry.list_plugins(),
        "Quality Plugin": "quality" in pipeline.plugin_adapter.registry.list_plugins(),
        "Narrative Plugin": "narrative" in pipeline.plugin_adapter.registry.list_plugins(),
    }

    print("NTPE Foundation-04.1 Pipeline Adapter Injection Test")
    print("===================================================")

    for name, ok in checks.items():
        print(f"{name:<18} {'PASS' if ok else 'FAIL'}")

    if not all(checks.values()):
        print("FAIL")
        raise SystemExit(2)

    print("PASS")