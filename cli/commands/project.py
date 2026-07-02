from __future__ import annotations

from ..command import CLICommand, CommandRegistry
from ..context import CLIContext
from ..result import CLIResult
from .project_manager import ProjectManager
from .project_report import project_summary
from .manifest import attach_project_manifest


def command_project(context: CLIContext, args: object) -> CLIResult:
    action = getattr(args, "project_action", None)
    if not action:
        return CLIResult.failure("project action is required", exit_code=2)
    try:
        manager = ProjectManager(context.root)
        if action == "create":
            data = manager.create(
                path=getattr(args, "path", "."),
                name=getattr(args, "name", None),
                input_dir=str(getattr(args, "input", "input") or "input"),
                output_dir=str(getattr(args, "output", "output") or "output"),
                force=bool(getattr(args, "force", False)),
            )
            message = "Project created"
        elif action == "open":
            data = manager.open(getattr(args, "path", "."))
            message = "Project opened"
        elif action == "info":
            data = manager.info(getattr(args, "path", "."))
            message = "Project info"
        elif action == "validate":
            validation = manager.validate(getattr(args, "path", "."))
            data = {"validation": validation.to_dict()}
            attach_project_manifest(data)
            if not validation.ok or (bool(getattr(args, "strict", False)) and validation.warnings):
                return CLIResult.failure("Project validation failed", exit_code=1, errors=validation.warnings + validation.missing_dirs, **data)
            message = "Project validation passed"
        elif action == "list":
            data = manager.list(getattr(args, "path", "."))
            message = "Project list"
        elif action == "export":
            data = manager.export(getattr(args, "path", "."), getattr(args, "output", None))
            message = "Project exported"
        elif action == "import":
            data = manager.import_package(
                package=getattr(args, "package"),
                output=getattr(args, "output", "."),
                replace=bool(getattr(args, "replace", False)),
            )
            message = "Project imported"
        else:
            return CLIResult.failure(f"unknown project action: {action}", exit_code=2)
        payload = project_summary(action, data)
        attach_project_manifest(payload)
        return CLIResult.success(message, **payload)
    except Exception as exc:
        return CLIResult.failure(f"Project command failed: {exc}", exit_code=2)


def register_project_command(registry: CommandRegistry) -> CommandRegistry:
    registry.register(CLICommand("project", "manage NTPE projects", command_project))
    return registry
