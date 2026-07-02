from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Iterable, Optional

from .command import CLICommand, CommandRegistry
from .context import CLIContext
from .errors import CLIError
from .manifest import attach_cli_manifest, build_cli_manifest
from .parser import build_parser
from .result import CLIResult


def command_version(context: CLIContext, args: object) -> CLIResult:
    version = context.read_version(default="1.0.0-beta")
    return CLIResult.success("NTPE version", version=version, cli=build_cli_manifest()["version"])


def command_doctor(context: CLIContext, args: object) -> CLIResult:
    required = ["core", "runtime", "translation"]
    recommended = ["benchmark", "tests", "config"]
    existing_required = [name for name in required if context.path(name).exists()]
    missing_required = [name for name in required if name not in existing_required]
    missing_recommended = [name for name in recommended if not context.path(name).exists()]
    strict = bool(getattr(args, "strict", False))

    data = {
        "root": str(context.root),
        "required_ok": not missing_required,
        "existing_required": existing_required,
        "missing_required": missing_required,
        "missing_recommended": missing_recommended,
    }
    attach_cli_manifest(data)

    if missing_required or (strict and missing_recommended):
        errors = []
        if missing_required:
            errors.append("missing required directories: " + ", ".join(missing_required))
        if strict and missing_recommended:
            errors.append("missing recommended directories: " + ", ".join(missing_recommended))
        return CLIResult.failure("NTPE doctor found issues", exit_code=1, errors=errors, **data)

    return CLIResult.success("NTPE doctor passed", **data)


def build_registry() -> CommandRegistry:
    registry = CommandRegistry()
    registry.register(CLICommand("version", "show NTPE version", command_version))
    registry.register(CLICommand("doctor", "check project structure", command_doctor))
    return registry


def format_result(result: CLIResult, as_json: bool = False) -> str:
    if as_json:
        return json.dumps(result.to_dict(), ensure_ascii=False, indent=2)
    if result.message:
        if result.data:
            parts = [result.message]
            for key, value in result.data.items():
                if key == "manifests":
                    continue
                parts.append(f"{key}: {value}")
            if result.errors:
                parts.append("errors: " + "; ".join(result.errors))
            return "\n".join(parts)
        return result.message
    return "OK" if result.ok else "FAIL"


def run_cli(argv: Optional[Iterable[str]] = None, context: Optional[CLIContext] = None) -> CLIResult:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    root = Path(args.root).resolve() if getattr(args, "root", None) else None
    cli_context = context or CLIContext.discover(root)

    if not args.command:
        return CLIResult.success("NTPE CLI", manifest=build_cli_manifest(), commands=build_registry().names())

    registry = build_registry()
    try:
        command = registry.get(args.command)
        return command.execute(cli_context, args)
    except CLIError as exc:
        return CLIResult.failure(str(exc), exit_code=getattr(exc, "exit_code", 1))
    except Exception as exc:  # defensive boundary for CLI entrypoint
        return CLIResult.failure(f"Command failed: {exc}", exit_code=3)


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_parser()
    args_list = list(argv) if argv is not None else sys.argv[1:]
    args = parser.parse_args(args_list)
    result = run_cli(args_list)
    print(format_result(result, as_json=getattr(args, "as_json", False)))
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
