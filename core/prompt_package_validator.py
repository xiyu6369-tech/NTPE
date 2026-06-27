# =====================================================
# NTPE Prompt Package Validator v1.0
# 放置位置：D:\Python\NTPE\core\prompt_package_validator.py
# =====================================================

from __future__ import annotations

import json
from pathlib import Path


REQUIRED_FIELDS = [
    "package_id",
    "project",
    "session",
    "model_profile",
    "style_profile",
    "source",
    "context",
    "knowledge",
    "rules",
    "prompt",
    "token_estimate",
    "qa_requirements",
    "metadata",
]


def load_json(path: str | Path) -> dict:
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8-sig"))


def validate_prompt_package(package: dict) -> tuple[bool, list[str]]:
    errors = []

    if not isinstance(package, dict):
        return False, ["Prompt Package must be a JSON object."]

    for field in REQUIRED_FIELDS:
        if field not in package:
            errors.append(f"Missing required field: {field}")

    if "prompt" in package:
        prompt = package["prompt"]
        if not isinstance(prompt, dict):
            errors.append("prompt must be an object.")
        else:
            if not prompt.get("system_prompt"):
                errors.append("prompt.system_prompt is empty.")
            if not prompt.get("user_prompt"):
                errors.append("prompt.user_prompt is empty.")
            if prompt.get("prompt_mode") not in ["translate", "revise", "qa_fix"]:
                errors.append("prompt.prompt_mode must be translate / revise / qa_fix.")

    if "source" in package:
        source = package["source"]
        if not isinstance(source, dict):
            errors.append("source must be an object.")
        else:
            if not source.get("chunk_text"):
                errors.append("source.chunk_text is empty.")

    if "knowledge" in package:
        knowledge = package["knowledge"]
        if not isinstance(knowledge, dict):
            errors.append("knowledge must be an object.")
        else:
            if not isinstance(knowledge.get("character_matches", []), list):
                errors.append("knowledge.character_matches must be a list.")
            if not isinstance(knowledge.get("glossary_matches", []), list):
                errors.append("knowledge.glossary_matches must be a list.")
            if not isinstance(knowledge.get("locked_dictionary", {}), dict):
                errors.append("knowledge.locked_dictionary must be a dict.")

    return len(errors) == 0, errors


def validate_file(path: str | Path) -> tuple[bool, list[str]]:
    package = load_json(path)
    return validate_prompt_package(package)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python core/prompt_package_validator.py <prompt_package.json>")
        raise SystemExit(1)

    ok, errors = validate_file(sys.argv[1])

    if ok:
        print("PASS: valid NTPE Prompt Package")
    else:
        print("FAIL: invalid NTPE Prompt Package")
        for e in errors:
            print("-", e)
        raise SystemExit(2)
