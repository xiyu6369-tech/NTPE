from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, DefaultDict, Dict, List
from collections import defaultdict

from .execution_context import ExecutionContext


BEFORE_EXECUTION = "before_execution"
AFTER_EXECUTION = "after_execution"
BEFORE_RETRY = "before_retry"
AFTER_RETRY = "after_retry"
ON_FAILURE = "on_failure"
ON_TIMEOUT = "on_timeout"
ON_COMPLETE = "on_complete"


Hook = Callable[[ExecutionContext, Dict[str, object]], None]


@dataclass
class ExecutionHookRegistry:
    _hooks: DefaultDict[str, List[Hook]] = field(default_factory=lambda: defaultdict(list))

    def register(self, name: str, hook: Hook) -> None:
        self._hooks[name].append(hook)

    def run(self, name: str, context: ExecutionContext, payload: Dict[str, object] | None = None) -> None:
        data = payload or {}
        for hook in list(self._hooks.get(name, [])):
            hook(context, data)

    def manifest(self) -> Dict[str, int]:
        return {name: len(callbacks) for name, callbacks in self._hooks.items()}
