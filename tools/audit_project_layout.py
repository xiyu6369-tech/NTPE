from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "config/project_layout_policy.json"


def load_policy(path: Path = DEFAULT_POLICY) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_inventory(root: Path = ROOT, policy_path: Path = DEFAULT_POLICY) -> dict[str, Any]:
    policy = load_policy(policy_path)
    root_files = sorted(path.name for path in root.iterdir() if path.is_file())
    root_directories = sorted(path.name for path in root.iterdir() if path.is_dir())
    root_python = sorted(name for name in root_files if name.endswith(".py"))
    production = sorted(policy["production_entrypoints"])
    validation = sorted(policy["validation_entrypoints"])
    compatibility = sorted(policy["permitted_compatibility_wrappers"])
    allowed_files = set(policy["allowed_root_files"])
    allowed_directories = set(policy["allowed_root_directories"])
    ignored_directories = set(policy.get("ignored_root_directories", []))
    historical = sorted(
        name for name in policy.get("retained_root_wrappers", []) if name in root_python
    )
    unexpected_files = sorted(name for name in root_files if name not in allowed_files)
    unexpected_directories = sorted(
        name for name in root_directories if name not in allowed_directories and name not in ignored_directories
    )
    unclassified = sorted(name for name in unexpected_files if name not in historical)
    return {
        "schema_version": "ntpe.project-layout-inventory.v1",
        "root_total_files": len(root_files),
        "root_python_files": len(root_python),
        "production_entrypoints": production,
        "validation_entrypoints": validation,
        "historical_wrappers": historical,
        "permitted_compatibility_wrappers": compatibility,
        "unclassified_files": unclassified,
        "unexpected_root_files": unexpected_files,
        "unexpected_root_directories": unexpected_directories,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit the NTPE root directory layout")
    parser.add_argument("--output", type=Path, help="write the deterministic inventory as JSON")
    parser.add_argument("--report-only", action="store_true", help="report policy violations without failing")
    args = parser.parse_args()
    inventory = build_inventory()
    payload = json.dumps(inventory, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        output = args.output if args.output.is_absolute() else ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload, encoding="utf-8", newline="\n")
    print(payload, end="")
    violations = inventory["unexpected_root_files"] or inventory["unexpected_root_directories"]
    return 0 if args.report_only or not violations else 1


if __name__ == "__main__":
    raise SystemExit(main())
