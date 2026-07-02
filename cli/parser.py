from __future__ import annotations

import argparse


def _global_options() -> argparse.ArgumentParser:
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument("--json", action="store_true", dest="as_json", help="print command result as JSON")
    parent.add_argument("--root", default=None, help="project root directory")
    return parent


def build_parser() -> argparse.ArgumentParser:
    common = _global_options()
    parser = argparse.ArgumentParser(
        prog="ntpe",
        description="NTPE command line interface",
        parents=[common],
    )

    subparsers = parser.add_subparsers(dest="command")

    version = subparsers.add_parser("version", help="show NTPE version", parents=[common])
    version.set_defaults(command="version")

    doctor = subparsers.add_parser("doctor", help="check project structure and CLI readiness", parents=[common])
    doctor.add_argument("--strict", action="store_true", help="fail if recommended directories are missing")
    doctor.set_defaults(command="doctor")

    translate = subparsers.add_parser("translate", help="translate a TXT file or a folder", parents=[common])
    translate.add_argument("input", help="TXT file or folder to translate")
    translate.add_argument("--output", "-o", default=None, help="output directory")
    translate.add_argument("--resume", action="store_true", help="skip existing outputs")
    translate.add_argument("--provider", default="mock", help="provider name, e.g. nvidia/openai/gemini/mock")
    translate.add_argument("--quality", default="standard", help="quality profile, e.g. draft/standard/high")
    translate.add_argument("--dry-run", action="store_true", help="scan and plan without writing outputs")
    translate.add_argument("--pattern", default="*.txt", help="file glob when input is a folder")
    translate.add_argument("--overwrite", action="store_true", help="overwrite existing outputs")
    translate.add_argument("--suffix", default="_zh", help="output filename suffix")
    translate.set_defaults(command="translate")


    project = subparsers.add_parser("project", help="manage NTPE translation projects", parents=[common])
    project_sub = project.add_subparsers(dest="project_action")

    project_create = project_sub.add_parser("create", help="create an NTPE project", parents=[common])
    project_create.add_argument("path", nargs="?", default=".", help="project directory")
    project_create.add_argument("--name", default=None, help="project display name")
    project_create.add_argument("--input", default="input", help="input directory name")
    project_create.add_argument("--output", default="output", help="output directory name")
    project_create.add_argument("--force", action="store_true", help="overwrite project metadata if it exists")
    project_create.set_defaults(command="project")

    project_open = project_sub.add_parser("open", help="open an NTPE project", parents=[common])
    project_open.add_argument("path", nargs="?", default=".", help="project directory")
    project_open.set_defaults(command="project")

    project_info = project_sub.add_parser("info", help="show project information", parents=[common])
    project_info.add_argument("path", nargs="?", default=".", help="project directory")
    project_info.set_defaults(command="project")

    project_validate = project_sub.add_parser("validate", help="validate project structure", parents=[common])
    project_validate.add_argument("path", nargs="?", default=".", help="project directory")
    project_validate.add_argument("--strict", action="store_true", help="fail on warnings")
    project_validate.set_defaults(command="project")

    project_list = project_sub.add_parser("list", help="list projects under a directory", parents=[common])
    project_list.add_argument("path", nargs="?", default=".", help="directory to scan")
    project_list.set_defaults(command="project")

    project_export = project_sub.add_parser("export", help="export project metadata", parents=[common])
    project_export.add_argument("path", nargs="?", default=".", help="project directory")
    project_export.add_argument("--output", "-o", default=None, help="export file path")
    project_export.set_defaults(command="project")

    project_import = project_sub.add_parser("import", help="import project metadata", parents=[common])
    project_import.add_argument("package", help="project package JSON")
    project_import.add_argument("--output", "-o", default=".", help="target project directory")
    project_import.add_argument("--replace", action="store_true", help="replace existing metadata")
    project_import.set_defaults(command="project")

    return parser
