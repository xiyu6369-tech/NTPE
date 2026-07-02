from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Optional

from .context import CLIContext
from .errors import CommandNotFoundError
from .result import CLIResult

CommandHandler = Callable[[CLIContext, object], CLIResult]


@dataclass
class CLICommand:
    name: str
    description: str
    handler: CommandHandler

    def execute(self, context: CLIContext, args: object) -> CLIResult:
        return self.handler(context, args)


class CommandRegistry:
    def __init__(self) -> None:
        self._commands: Dict[str, CLICommand] = {}

    def register(self, command: CLICommand) -> CLICommand:
        if not command.name:
            raise ValueError("command name is required")
        self._commands[command.name] = command
        return command

    def get(self, name: str) -> CLICommand:
        try:
            return self._commands[name]
        except KeyError as exc:
            raise CommandNotFoundError(f"Unknown command: {name}") from exc

    def names(self) -> List[str]:
        return sorted(self._commands)

    def list(self) -> List[CLICommand]:
        return [self._commands[name] for name in self.names()]

    def __contains__(self, name: str) -> bool:
        return name in self._commands

    def __iter__(self) -> Iterable[CLICommand]:
        return iter(self.list())
