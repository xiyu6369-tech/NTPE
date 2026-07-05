from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from .pipeline_manifest import PipelineManifest
from .pipeline_state import PipelineState
from .pipeline_step import PipelineHandler, PipelineStep, PipelineStepResult


OFFICIAL_PIPELINE: tuple[str, ...] = (
    "Encoding",
    "Chunk",
    "Context",
    "Glossary",
    "Character Memory",
    "Prompt Builder",
    "AI Provider",
    "QA",
    "Taiwan Formatter",
    "Output",
)


class TranslationPipelineManager:
    """Official pipeline manager for NTPE 1.2 Professional.

    The manager is additive and orchestration-only. It declares, validates, and
    executes the shared pipeline without replacing the frozen LTS TXT/batch
    implementations or the Stage-01 TranslationRuntime facade.
    """

    version = "1.2-professional-stage-06"
    compatibility_floor = "1.1-lts-stable"

    def __init__(self, root: str | Path, runtime: Any):
        self.root = Path(root)
        self.runtime = runtime

    @property
    def pipeline_dir(self) -> Path:
        return self.root / ".ntpe_pipeline"

    def default_steps(self) -> tuple[PipelineStep, ...]:
        return tuple(
            PipelineStep(
                name=name,
                order=index,
                handler=self._default_handler_name(name),
                description=f"Official NTPE translation pipeline step: {name}.",
            )
            for index, name in enumerate(OFFICIAL_PIPELINE, start=1)
        )

    def manifest(self, pipeline_id: str | None = None) -> PipelineManifest:
        return PipelineManifest(
            pipeline_id=pipeline_id or uuid4().hex,
            pipeline_version=self.version,
            compatibility_floor=self.compatibility_floor,
            steps=self.default_steps(),
        )

    def describe(self) -> dict[str, Any]:
        manifest = self.manifest("official-runtime-pipeline")
        return {"status": "success", "manifest": manifest.to_dict(), "resources": self.runtime.describe_resources() if hasattr(self.runtime, "describe_resources") else None}

    def validate(self) -> dict[str, Any]:
        steps = self.default_steps()
        names = [step.name for step in steps]
        missing = [name for name in OFFICIAL_PIPELINE if name not in names]
        wrong_order = names != list(OFFICIAL_PIPELINE)
        duplicate = len(names) != len(set(names))
        status = "success" if not missing and not wrong_order and not duplicate else "failed"
        return {
            "status": status,
            "version": self.version,
            "compatibility_floor": self.compatibility_floor,
            "missing_steps": missing,
            "wrong_order": wrong_order,
            "duplicate_steps": duplicate,
            "steps": [step.to_dict() for step in steps],
        }

    def execute(self, payload: dict[str, Any] | None = None, handlers: dict[str, PipelineHandler] | None = None) -> dict[str, Any]:
        payload = dict(payload or {})
        handlers = handlers or {}
        state = PipelineState()
        results: list[PipelineStepResult] = []

        for step in self.default_steps():
            state.mark_running(step.name)
            handler = handlers.get(step.name) or handlers.get(step.handler) or self._default_handler
            try:
                output = handler({"step": step.to_dict(), "payload": payload, "state": state.to_dict()})
                if not isinstance(output, dict):
                    output = {"value": output}
                payload.update(output.get("payload", output))
                result = PipelineStepResult(name=step.name, status="success", output=output)
                results.append(result)
                state.mark_step_completed(step.name)
            except Exception as exc:
                state.mark_failed(step.name, str(exc))
                results.append(PipelineStepResult(name=step.name, status="failed", output={}, error=str(exc)))
                return {
                    "status": "failed",
                    "version": self.version,
                    "state": state.to_dict(),
                    "results": [result.to_dict() for result in results],
                    "payload": payload,
                }

        state.mark_completed()
        return {
            "status": "success",
            "version": self.version,
            "state": state.to_dict(),
            "results": [result.to_dict() for result in results],
            "payload": payload,
        }

    def save_manifest(self, pipeline_id: str | None = None) -> dict[str, Any]:
        manifest = self.manifest(pipeline_id)
        path = manifest.save(self.pipeline_dir / manifest.pipeline_id / "pipeline_manifest.json")
        return {"status": "success", "pipeline_id": manifest.pipeline_id, "manifest_path": str(path), "manifest": manifest.to_dict()}

    @staticmethod
    def _default_handler_name(step_name: str) -> str:
        return step_name.lower().replace(" ", "_")

    @staticmethod
    def _default_handler(context: dict[str, Any]) -> dict[str, Any]:
        step = context.get("step", {})
        payload = dict(context.get("payload", {}))
        completed = list(payload.get("pipeline_trace", []))
        completed.append(step.get("name", "unknown"))
        payload["pipeline_trace"] = completed
        return {"payload": payload}
