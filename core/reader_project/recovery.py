"""Recovery & Source Integrity Validation (S9-06).

Canonical decision boundary for Project recovery eligibility.
Does NOT implement translation/runtime logic; only validates preconditions.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from .identity import source_changed, compute_source_identity
from .models import ReaderProject, ReaderStatus, OutputRecord, ExecutionRecord


def read_resume_state(path: str | Path | None) -> tuple[dict[str, Any] | None, str | None]:
    """Return ``(resume_state, error)``.

    * ``(None, None)``  no resume state (not started)
    * ``(data, None)``  readable resume state
    * ``(None, "<reason>")`` unreadable/corrupt resume state
    """
    if not path:
        return None, None
    file_path = Path(path)
    if not file_path.is_file():
        return None, None
    try:
        data = json.loads(file_path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        return None, str(exc)
    if not isinstance(data, dict) or not isinstance(data.get("chunks", {}), dict):
        return None, "resume state has an unexpected shape"
    return data, None


class RecoveryError(Exception):
    """Base error for recovery validation."""

    def __init__(self, message: str, code: str = "RECOVERY_ERROR"):
        super().__init__(message)
        self.code = code


class SourceIntegrityError(RecoveryError):
    """Raised when source integrity validation fails."""

    def __init__(self, message: str, code: str = "SOURCE_INTEGRITY_ERROR"):
        super().__init__(message, code)


class RuntimeArtifactError(RecoveryError):
    """Raised when runtime artifact validation fails."""

    def __init__(self, message: str, code: str = "RUNTIME_ARTIFACT_ERROR"):
        super().__init__(message, code)


class ProjectNotFoundError(RecoveryError):
    """Raised when project cannot be found."""

    def __init__(self, message: str, code: str = "PROJECT_NOT_FOUND"):
        super().__init__(message, code)


@dataclass(frozen=True)
class RecoveryEligibility:
    """Result of recovery eligibility validation."""

    eligible: bool
    project_id: str
    reason: str = ""
    blocked_by: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.details is None:
            object.__setattr__(self, "details", {})


def validate_project_identity(project: ReaderProject) -> tuple[bool, str]:
    """Validate project identity is present and valid."""
    if not project.project_id:
        return False, "project_id is missing"
    if not isinstance(project.project_id, str) or len(project.project_id) < 8:
        return False, "project_id appears invalid"
    return True, ""


def validate_source_identity(project: ReaderProject) -> tuple[bool, str]:
    """Validate source identity is present and computable."""
    if not project.source.path:
        return False, "source path is missing"
    if not project.source.identity_kind:
        return False, "source identity_kind is missing"
    if not project.source.hash:
        return False, "source hash is missing"
    if project.source.format not in ("txt", "epub"):
        return False, f"unsupported source format: {project.source.format}"
    return True, ""


def validate_source_integrity(project: ReaderProject) -> tuple[bool, str, dict]:
    """Validate source file still matches recorded identity.

    Returns (is_valid, reason, details).
    """
    from .identity import source_changed, compute_source_identity

    if not project.source.path:
        return False, "source path is empty", {"missing": True}

    try:
        source_path = Path(project.source.path)
    except (TypeError, ValueError) as exc:
        return False, f"invalid source path: {exc}", {"invalid_path": True}

    if not source_path.exists():
        return False, "source file not found", {"missing": True}

    # Use canonical source identity comparison
    try:
        current_identity = compute_source_identity(source_path, format=project.source.format)
    except (OSError, ValueError, FileNotFoundError) as exc:
        return False, f"cannot compute source identity: {exc}", {"compute_error": True}

    # Compare with recorded identity
    identity_match = (
        current_identity.identity_kind == project.source.identity_kind
        and current_identity.hash == project.source.hash
    )

    if not identity_match:
        return False, "source content has changed", {
            "changed": True,
            "recorded_hash": project.source.hash,
            "current_hash": current_identity.hash,
        }

    return True, "", {"matched": True, "current_hash": current_identity.hash}


def validate_runtime_artifact(project: ReaderProject) -> tuple[bool, str, dict]:
    """Validate runtime artifact exists, is readable, and bindings are correct.

    Checks:
    - Project owns a resume_state_path
    - The file exists and is readable
    - The resume state contains sufficient evidence
    - Project and source bindings match
    """
    exec_rec = project.execution
    if not exec_rec.resume_state_path:
        return False, "no resume_state_path recorded", {"missing_resume_state": True}

    path = Path(exec_rec.resume_state_path)
    if not path.exists():
        return False, "resume state file not found", {"missing_file": True}

    if not path.is_file():
        return False, "resume_state_path is not a file", {"not_file": True}

    # Try to read and validate structure
    try:
        resume_data, error = read_resume_state(path)
    except Exception as exc:
        return False, f"failed to read resume state: {exc}", {"read_error": str(exc)}

    if error is not None:
        return False, f"resume state unreadable: {error}", {"read_error": error}

    if resume_data is None:
        return False, "resume state is empty (not started)", {"no_resume_state": True}

    chunks = resume_data.get("chunks", {})
    if not isinstance(chunks, dict) or not chunks:
        return False, "resume state has no chunks", {"empty_chunks": True}

    # Check for sufficient recovery evidence
    completed = sum(
        1
        for entry in chunks.values()
        if isinstance(entry, dict)
        and entry.get("status") in ("success", "pass_with_warning")
    )
    total = len(chunks)
    if completed == 0 and total > 0:
        return False, "no completed chunks in resume state", {"completed": completed, "total": total}

    return True, "", {
        "resume_path": str(path),
        "chunks_total": total,
        "chunks_completed": completed,
        "valid": True,
    }


def validate_project_binding(project: ReaderProject) -> tuple[bool, str, dict]:
    """Validate runtime artifact belongs to this project.

    S10-03 F3 (S9-06 contract §6): ownership must be *provable*. The runtime
    artifact records the output directory it was produced in; that directory
    must match the artifact's own location and, when the project records an
    output directory, must match it too. A runtime artifact that carries no
    ownership evidence is treated as unverifiable and therefore blocks recovery.
    """
    exec_rec = project.execution
    if not exec_rec.resume_state_path:
        return True, "", {}

    path = Path(exec_rec.resume_state_path)
    if not path.exists():
        return True, "", {}

    resume_data, error = read_resume_state(path)
    if error or resume_data is None:
        return False, "cannot read resume state for project binding", {"read_error": error}

    artifact_output_dir = resume_data.get("output_dir")
    if not artifact_output_dir:
        return False, "runtime artifact lacks project ownership evidence", {
            "missing_project_binding": True,
        }

    try:
        artifact_dir = Path(str(artifact_output_dir)).resolve()
        resume_dir = path.resolve().parent
    except (OSError, ValueError) as exc:
        return False, f"cannot validate project binding: {exc}", {"binding_error": str(exc)}

    if artifact_dir != resume_dir:
        return False, "runtime artifact output_dir does not match its location", {
            "project_binding_mismatch": True,
            "artifact_output_dir": str(artifact_dir),
            "resume_dir": str(resume_dir),
        }

    if project.output.output_dir:
        try:
            project_dir = Path(project.output.output_dir).resolve()
        except (OSError, ValueError) as exc:
            return False, f"cannot validate project binding: {exc}", {"binding_error": str(exc)}
        if project_dir != artifact_dir:
            return False, "runtime artifact belongs to a different project output directory", {
                "project_binding_mismatch": True,
                "project_output_dir": str(project_dir),
                "artifact_output_dir": str(artifact_dir),
            }

    return True, "", {"project_bound": True}


def validate_source_binding(project: ReaderProject) -> tuple[bool, str, dict]:
    """Validate runtime artifact source identity matches project source.

    S10-03 F3 (S9-06 contract §6): the resume state records the input path it
    was produced from. That evidence must exist and resolve to the project's
    source. Missing evidence is unverifiable and blocks recovery.
    """
    exec_rec = project.execution
    if not exec_rec.resume_state_path:
        return True, "", {}

    path = Path(exec_rec.resume_state_path)
    if not path.exists():
        return True, "", {}

    resume_data, error = read_resume_state(path)
    if error or resume_data is None:
        return False, "cannot read resume state for source binding", {"read_error": error}

    chunks = resume_data.get("chunks", {})
    if not chunks:
        return True, "", {}

    recorded_input = resume_data.get("input")
    if not recorded_input:
        return False, "runtime artifact lacks source ownership evidence", {
            "missing_source_binding": True,
        }
    if not project.source.path:
        return False, "project source path is missing", {"missing_source_binding": True}

    try:
        recorded = Path(str(recorded_input)).resolve()
        expected = Path(project.source.path).resolve()
    except (OSError, ValueError) as exc:
        return False, f"cannot validate source binding: {exc}", {"binding_error": str(exc)}

    if recorded != expected:
        return False, "resume state was produced from a different source", {
            "source_binding_mismatch": True,
            "recorded_input": str(recorded),
            "project_source": str(expected),
        }

    return True, "", {
        "project_source_hash": project.source.hash,
        "project_identity_kind": project.source.identity_kind,
        "binding_checked": True,
    }


def validate_runtime_state_recoverable(project: ReaderProject) -> tuple[bool, str, dict]:
    """Validate that runtime state has sufficient evidence to resume."""
    exec_rec = project.execution
    if not exec_rec.resume_state_path:
        return False, "no resume state path", {"missing": True}

    path = Path(exec_rec.resume_state_path)
    if not path.exists():
        return False, "resume state file not found", {"missing_file": True}

    resume_data, error = read_resume_state(path)
    if error:
        return False, f"resume state unreadable: {error}", {"read_error": error}

    if resume_data is None:
        return False, "no resume state data", {"no_data": True}

    chunks = resume_data.get("chunks", {})
    if not chunks:
        return False, "no chunk data in resume state", {"empty_chunks": True}

    # Check for at least one completed or in-progress chunk
    has_resumable = any(
        isinstance(entry, dict)
        and entry.get("status") in ("success", "pass_with_warning", "running", "pending")
        for entry in chunks.values()
    )

    if not has_resumable:
        return False, "no resumable chunks found", {"no_resumable": True}

    return True, "", {"has_resumable": True}


def check_recovery_eligibility(project: ReaderProject) -> RecoveryEligibility:
    """Full recovery eligibility check per canonical contract.

    Returns RecoveryEligibility with deterministic True/False result.
    """
    pid = project.project_id

    # 1. Project identity
    valid, reason = validate_project_identity(project)
    if not valid:
        return RecoveryEligibility(
            eligible=False,
            project_id=pid,
            reason=f"Project identity invalid: {reason}",
            blocked_by="project",
            details={"check": "project_identity", "error": reason},
        )

    # 2. Source identity valid
    valid, reason = validate_source_identity(project)
    if not valid:
        return RecoveryEligibility(
            eligible=False,
            project_id=pid,
            reason=f"Source identity invalid: {reason}",
            blocked_by="source",
            details={"check": "source_identity", "error": reason},
        )

    # 3. Source integrity
    valid, reason, details = validate_source_integrity(project)
    if not valid:
        return RecoveryEligibility(
            eligible=False,
            project_id=pid,
            reason=f"Source integrity failed: {reason}",
            blocked_by="source",
            details={"check": "source_integrity", "error": reason, **details},
        )

    # 4. Runtime artifact exists
    valid, reason, details = validate_runtime_artifact(project)
    if not valid:
        return RecoveryEligibility(
            eligible=False,
            project_id=pid,
            reason=f"Runtime artifact invalid: {reason}",
            blocked_by="artifact",
            details={"check": "runtime_artifact", "error": reason, **details},
        )

    # 5. Runtime artifact belongs to project
    valid, reason, details = validate_project_binding(project)
    if not valid:
        return RecoveryEligibility(
            eligible=False,
            project_id=pid,
            reason=f"Runtime artifact project binding invalid: {reason}",
            blocked_by="artifact",
            details={"check": "project_binding", "error": reason, **details},
        )

    # 6. Runtime artifact belongs to source
    valid, reason, details = validate_source_binding(project)
    if not valid:
        return RecoveryEligibility(
            eligible=False,
            project_id=pid,
            reason=f"Runtime artifact source binding invalid: {reason}",
            blocked_by="artifact",
            details={"check": "source_binding", "error": reason, **details},
        )

    # 7. Runtime state recoverable
    valid, reason, details = validate_runtime_state_recoverable(project)
    if not valid:
        return RecoveryEligibility(
            eligible=False,
            project_id=pid,
            reason=f"Runtime state not recoverable: {reason}",
            blocked_by="state",
            details={"check": "runtime_state", "error": reason, **details},
        )

    # All checks passed
    return RecoveryEligibility(
        eligible=True,
        project_id=pid,
        reason="All recovery preconditions satisfied",
        blocked_by="",
        details={"all_checks": "passed"},
    )


def validate_recovery_eligibility(project: ReaderProject) -> RecoveryEligibility:
    """Public API: check if a project is eligible for recovery."""
    return check_recovery_eligibility(project)


def get_recovery_blocked_reason(project: ReaderProject) -> tuple[str, str]:
    """Get human-readable reason why recovery is blocked.

    Returns (blocked_by, reason) where blocked_by is one of:
    "project", "source", "artifact", "state", or "" if eligible.
    """
    result = check_recovery_eligibility(project)
    if result.eligible:
        return "", ""
    return result.blocked_by, result.reason