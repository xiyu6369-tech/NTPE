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

    return parser
