from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.pipeline.pipeline_v1 import ProductionPipelineV1


if __name__ == "__main__":
    pipeline = ProductionPipelineV1(ROOT)
    text = (ROOT / "engine" / "pipeline" / "pipeline_v1.py").read_text(encoding="utf-8-sig")

    checks = {
        "Plugin Adapter": hasattr(pipeline, "plugin_adapter"),
        "Payload Helper": "def _build_plugin_payload(" in text,
        "Build Context": "self.plugin_adapter.build_context(" in text,
        "Prompt Context": "context=plugin_context" in text,
        "Fallback": "PLUGIN CONTEXT FALLBACK" in text,
    }

    print("NTPE Foundation-04.2 Pipeline Context Migration Test")
    print("====================================================")

    for name, ok in checks.items():
        print(f"{name:<18} {'PASS' if ok else 'FAIL'}")

    if not all(checks.values()):
        print("FAIL")
        raise SystemExit(2)

    print("PASS")