from dataclasses import replace
from pathlib import Path
import subprocess

import pytest

from core.controlled_multi_chunk_translation_canary.policy import (
    ArtifactRootValidationError,
    OUTPUT_ROOT,
    STAGE744_OUTPUT_ROOT,
    select_artifact_root,
)
from tests.unit.controlled_multi_chunk_translation_canary import build_context


def _repository(tmp_path: Path) -> Path:
    repository = tmp_path / "repository"
    (repository / "artifacts").mkdir(parents=True)
    return repository


def test_default_root_remains_stage743(tmp_path):
    repository = _repository(tmp_path)
    selection = select_artifact_root(repository)
    assert OUTPUT_ROOT == "artifacts/controlled_multi_chunk_translation_stage743"
    assert selection.repository_relative == OUTPUT_ROOT
    assert selection.absolute_path == (repository / OUTPUT_ROOT).resolve()
    assert selection.used_default is True


def test_explicit_stage744_override_is_canonical_and_clean(tmp_path):
    repository = _repository(tmp_path)
    selection = select_artifact_root(
        repository,
        "artifacts/controlled_multi_chunk_translation_stage744/",
        clean_root_required=True,
    )
    assert selection.repository_relative == STAGE744_OUTPUT_ROOT
    assert selection.absolute_path == (repository / STAGE744_OUTPUT_ROOT).resolve()
    assert selection.used_default is False
    assert selection.root_exists is False
    assert selection.root_empty is True


@pytest.mark.parametrize(
    "value",
    [
        "",
        "../artifacts/controlled_multi_chunk_translation_stage744",
        "artifacts/../artifacts/controlled_multi_chunk_translation_stage744",
        "file:///tmp/stage744",
        "sqlite:///tmp/stage744",
        "https://example.invalid/stage744",
        "http://example.invalid/stage744",
        r"\\server\share\stage744",
        "//server/share/stage744",
        "input",
        "output",
        "artifacts/input/stage744",
        "artifacts/output/stage744",
        ".",
        "artifacts",
        "artifacts/unapproved-stage-root",
    ],
)
def test_invalid_overrides_fail_closed_without_default_fallback(tmp_path, value):
    repository = _repository(tmp_path)
    with pytest.raises(ArtifactRootValidationError):
        select_artifact_root(repository, value, clean_root_required=True)
    assert not (repository / OUTPUT_ROOT).exists()


def test_absolute_path_outside_artifacts_is_rejected(tmp_path):
    repository = _repository(tmp_path)
    with pytest.raises(ArtifactRootValidationError):
        select_artifact_root(
            repository,
            str((tmp_path / "outside").resolve()),
            clean_root_required=True,
        )


def test_existing_non_empty_root_is_rejected_in_clean_mode(tmp_path):
    repository = _repository(tmp_path)
    target = repository / STAGE744_OUTPUT_ROOT
    target.mkdir(parents=True)
    (target / "stale-diagnostic.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ArtifactRootValidationError, match="nonexistent or empty"):
        select_artifact_root(
            repository, STAGE744_OUTPUT_ROOT, clean_root_required=True
        )


def test_file_path_is_rejected(tmp_path):
    repository = _repository(tmp_path)
    target = repository / STAGE744_OUTPUT_ROOT
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("not a directory", encoding="utf-8")
    with pytest.raises(ArtifactRootValidationError, match="directory"):
        select_artifact_root(repository, STAGE744_OUTPUT_ROOT)


def test_prior_root_is_rejected_when_explicit_clean_root_is_required(tmp_path):
    repository = _repository(tmp_path)
    with pytest.raises(ArtifactRootValidationError):
        select_artifact_root(repository, OUTPUT_ROOT, clean_root_required=True)


def test_symlink_or_junction_escape_is_rejected(tmp_path):
    repository = _repository(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    target = repository / STAGE744_OUTPUT_ROOT
    try:
        target.symlink_to(outside, target_is_directory=True)
    except OSError:
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(target), str(outside)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
    with pytest.raises(ArtifactRootValidationError, match="symlink or junction"):
        select_artifact_root(
            repository, STAGE744_OUTPUT_ROOT, clean_root_required=True
        )


def test_artifact_root_changes_deterministic_request_identity(tmp_path):
    context = build_context(tmp_path)
    default_request = context["request"]
    override_request = replace(
        default_request, artifact_root=STAGE744_OUTPUT_ROOT
    )
    assert default_request.artifact_root == OUTPUT_ROOT
    assert override_request.artifact_root == STAGE744_OUTPUT_ROOT
    assert override_request.request_fingerprint != default_request.request_fingerprint
    assert override_request.request_id != default_request.request_id
