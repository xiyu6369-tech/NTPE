from __future__ import annotations

from ..command import CLICommand, CommandRegistry
from ..context import CLIContext
from ..result import CLIResult
from .manifest import attach_translate_manifest
from .translate_options import TranslateOptions
from .translate_runner import TranslateRunner


def command_translate(context: CLIContext, args: object) -> CLIResult:
    try:
        options = TranslateOptions.from_args(args)
        runner = TranslateRunner(context)
        summary = runner.run(options)
        data = summary.to_dict()
        attach_translate_manifest(data)
        if summary.progress.failed:
            return CLIResult.failure(
                "Translation completed with failures",
                exit_code=2,
                errors=[f"{summary.progress.failed} file(s) failed"],
                **data,
            )
        return CLIResult.success("Translation completed", **data)
    except Exception as exc:
        return CLIResult.failure(f"Translation failed: {exc}", exit_code=2)


def register_translate_command(registry: CommandRegistry) -> CommandRegistry:
    registry.register(CLICommand("translate", "translate a TXT file or folder", command_translate))
    return registry
