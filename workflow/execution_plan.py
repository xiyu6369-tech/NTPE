"""Execution plan builder for NTPE Stage-09.2 Pipeline Orchestrator."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Set
from .pipeline_models import PipelineDefinition, PipelineStage

@dataclass
class ExecutionPlan:
    pipeline_name: str
    stages: List[PipelineStage] = field(default_factory=list)

    @classmethod
    def build(cls, pipeline: PipelineDefinition) -> "ExecutionPlan":
        stage_by_name: Dict[str, PipelineStage] = {stage.name: stage for stage in pipeline.stages}
        if len(stage_by_name) != len(pipeline.stages):
            raise ValueError("pipeline contains duplicate stage names")

        ordered: List[PipelineStage] = []
        visiting: Set[str] = set()
        visited: Set[str] = set()

        def visit(stage: PipelineStage) -> None:
            if stage.name in visited:
                return
            if stage.name in visiting:
                raise ValueError(f"pipeline dependency cycle detected at: {stage.name}")
            visiting.add(stage.name)
            for dependency in stage.depends_on:
                if dependency not in stage_by_name:
                    raise ValueError(f"stage {stage.name} missing dependency: {dependency}")
                visit(stage_by_name[dependency])
            visiting.remove(stage.name)
            visited.add(stage.name)
            ordered.append(stage)

        for stage in pipeline.stages:
            visit(stage)
        return cls(pipeline_name=pipeline.name, stages=ordered)

    def names(self) -> List[str]:
        return [stage.name for stage in self.stages]

    def validate(self) -> bool:
        completed: Set[str] = set()
        for stage in self.stages:
            if any(dep not in completed for dep in stage.depends_on):
                return False
            completed.add(stage.name)
        return True

    def to_dict(self) -> dict:
        return {"pipeline_name": self.pipeline_name, "stages": self.names(), "valid": self.validate()}
