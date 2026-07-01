import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.pipeline.stage_registry import (
    PipelineStageDefinition,
    build_stage_id,
    create_stage_registry,
    normalize_stage_definition,
    validate_stage_definition,
)
from adapters.pipeline_stage_registry_adapter import (
    adapter_export_stage_manifest,
    adapter_register_stage,
    adapter_validate_stage,
    build_stage_registry_adapter,
)


def mark(name, ok):
    if not ok:
        raise AssertionError(name)
    print(f"{name:<24} PASS")


def sample_handler(payload):
    if isinstance(payload, dict):
        payload = dict(payload)
        payload["sample"] = True
        return payload
    return payload


def main():
    print("NTPE Foundation-05.1 Pipeline Stage Registry Test")
    print("=" * 56)

    legacy = {"name": "context", "handler": sample_handler, "priority": 10, "tags": ["foundation"]}
    normalized = normalize_stage_definition(legacy)
    mark("Legacy Normalize", normalized.name == "context")
    mark("Stage ID", build_stage_id("context", "1.0.0") == "context@1.0.0")
    mark("Stage Created", isinstance(normalized, PipelineStageDefinition))
    mark("Validate Stage", validate_stage_definition(normalized) is True)

    registry = create_stage_registry()
    mark("Registry Created", registry is not None)

    registered = registry.register(normalized)
    mark("Stage Registered", registered.stage_id == "context@1.0.0")
    mark("Stage Exists", registry.exists("context"))
    mark("Stage Get", registry.get("context").name == "context")

    registry.register({"name": "quality", "version": "1.0.0", "priority": 30, "dependencies": ["context"], "provides": ["quality_report"]})
    registry.register({"name": "prompt", "version": "1.0.0", "priority": 20, "dependencies": ["context"]})
    names = [stage.name for stage in registry.list()]
    mark("Stage List", names == ["context", "prompt", "quality"])
    mark("Enabled List", len(registry.list(enabled_only=True)) == 3)

    registry.disable("prompt")
    mark("Stage Disabled", registry.get("prompt").enabled is False)
    registry.enable("prompt")
    mark("Stage Enabled", registry.get("prompt").enabled is True)

    handlers = registry.handlers()
    mark("Handler Query", len(handlers) == 1 and handlers[0]({"x": 1})["sample"] is True)

    manifest = registry.export_manifest()
    mark("Manifest Created", manifest["schema"] == "ntpe.pipeline.stage_registry.v1")
    mark("Manifest Count", manifest["count"] == 3)
    mark("Registry Events", len(manifest["events"]) >= 3)

    imported = create_stage_registry()
    imported.import_manifest(manifest)
    mark("Manifest Imported", imported.exists("quality"))

    removed = imported.unregister("quality")
    mark("Stage Unregistered", removed.name == "quality" and not imported.exists("quality"))

    adapter_registry = build_stage_registry_adapter()
    mark("Adapter Created", adapter_registry is not None)
    adapter_stage = adapter_register_stage(adapter_registry, {"name": "adapter_context", "priority": 5})
    mark("Adapter Register", adapter_stage["name"] == "adapter_context")
    mark("Adapter Validate", adapter_validate_stage({"name": "adapter_quality"}) is True)
    adapter_manifest = adapter_export_stage_manifest(adapter_registry)
    mark("Adapter Manifest", adapter_manifest["count"] == 1)

    mark("Backward Compatible", registry.exists("context") and registry.exists("prompt"))
    print("PASS")


if __name__ == "__main__":
    main()
