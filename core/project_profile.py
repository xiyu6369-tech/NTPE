from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PROFILE = ROOT / "profiles" / "passion_profile.json"

REQUIRED_FIELDS = [
    "project",
    "language",
    "paths",
    "model_profile",
    "translation_style",
    "chunking",
    "context",
    "knowledge_sources",
    "qa",
    "output",
    "metadata",
]


def load_json(path: str | Path) -> dict:
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8-sig"))


def validate_project_profile(profile: dict) -> tuple[bool, list[str]]:
    errors = []

    if not isinstance(profile, dict):
        return False, ["Project Profile must be a JSON object."]

    for field in REQUIRED_FIELDS:
        if field not in profile:
            errors.append(f"Missing required field: {field}")

    project = profile.get("project", {})
    if not project.get("project_id"):
        errors.append("project.project_id is required.")
    if not project.get("project_name"):
        errors.append("project.project_name is required.")

    language = profile.get("language", {})
    if language.get("source_language") not in ["ko", "ja", "zh", "en"]:
        errors.append("language.source_language must be one of: ko / ja / zh / en.")
    if not language.get("target_language"):
        errors.append("language.target_language is required.")

    model = profile.get("model_profile", {})
    if not model.get("engine"):
        errors.append("model_profile.engine is required.")
    if not model.get("model"):
        errors.append("model_profile.model is required.")
    if int(model.get("context_window", 0) or 0) <= 0:
        errors.append("model_profile.context_window must be greater than 0.")

    chunking = profile.get("chunking", {})
    if int(chunking.get("chunk_size", 0) or 0) <= 0:
        errors.append("chunking.chunk_size must be greater than 0.")
    if int(chunking.get("max_chunk_size", 0) or 0) < int(chunking.get("chunk_size", 0) or 0):
        errors.append("chunking.max_chunk_size must be >= chunking.chunk_size.")

    qa = profile.get("qa", {})
    if int(qa.get("max_retry", 0) or 0) < 0:
        errors.append("qa.max_retry must be >= 0.")

    return len(errors) == 0, errors


def load_project_profile(path: str | Path | None = None) -> dict:
    if path is None:
        path = DEFAULT_PROFILE

    profile = load_json(path)
    ok, errors = validate_project_profile(profile)

    if not ok:
        raise ValueError("Invalid project profile:\n" + "\n".join(f"- {e}" for e in errors))

    return profile


def get_profile_summary(profile: dict) -> dict:
    return {
        "project_id": profile["project"]["project_id"],
        "project_name": profile["project"]["project_name"],
        "source_language": profile["language"]["source_language"],
        "target_language": profile["language"]["target_language"],
        "engine": profile["model_profile"]["engine"],
        "model": profile["model_profile"]["model"],
        "chunk_size": profile["chunking"]["chunk_size"],
        "qa_enabled": profile["qa"]["enabled"],
    }


if __name__ == "__main__":
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PROFILE
    profile = load_json(path)
    ok, errors = validate_project_profile(profile)

    if ok:
        print("PASS: valid NTPE Project Profile")
        print(json.dumps(get_profile_summary(profile), ensure_ascii=False, indent=2))
    else:
        print("FAIL: invalid NTPE Project Profile")
        for error in errors:
            print("-", error)
        raise SystemExit(2)
