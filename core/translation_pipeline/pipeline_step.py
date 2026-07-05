from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Callable


@dataclass(frozen=True)
class PipelineStep:
    """Declarative unit in the NTPE Professional translation pipeline."""

    name: str
    order: int
    handler: str
    required: bool = True
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PipelineStepResult:
    name: str
    status: str
    output: dict[str, Any]
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


PipelineHandler = Callable[[dict[str, Any]], dict[str, Any]]
