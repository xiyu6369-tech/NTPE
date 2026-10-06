"""Reader Project lifecycle (S9-02, S9 §11).

Minimal reliable persistence: create / load / save / update / list / delete.

Design constraints:
* Only Project metadata is persisted here.
* Runtime resume state and artifacts are referenced, never rewritten.
* Delete is explicit, confirmed, and scoped to exactly one project.
* Loading never deletes or mutates unrelated projects.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from .identity import compute_source_identity
from .models import (
    SCHEMA_VERSION,
    BookRecord,
    ExecutionRecord,
    OutputRecord,
    ReaderProject,
    ReaderStatus,
    SourceRecord,
    StateRecord,
    TargetRecord,
)
from .recovery import (
    RecoveryEligibility,
    validate_recovery_eligibility,
    get_recovery_blocked_reason,
    SourceIntegrityError,
    RuntimeArtifactError,
    RecoveryError,
)
from .store import ProjectStore


class ProjectError(Exception):
    """Base error for Reader Project operations."""


class ProjectNotFoundError(ProjectError):
    pass


class ProjectSchemaError(ProjectError):
    """Raised when a project's schema version cannot be handled."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _migrate(payload: dict) -> dict:
    """Migrate an older project payload to the current schema.

    Only schema v1 exists today; the ordered table is the extension point
    owned by S9-06. Unknown/older versions are rejected by ``load``.
    """
    version = int(payload.get("project_schema_version") or 0)
    while version < SCHEMA_VERSION:
        migration = _MIGRATIONS.get(version)
        if migration is None:
            raise ProjectSchemaError(
                f"no migration path from project schema v{version}"
            )
        payload = migration(payload)
        version = int(payload.get("project_schema_version") or 0)
    return payload


_MIGRATIONS: dict[int, "Callable[[dict], dict]"] = {}


class ReaderProjectManager:
    """Create, persist, load, and manage Reader Projects."""

    def __init__(self, home: str | Path | None = None, store: ProjectStore | None = None):
        self.store = store or ProjectStore(home)

    # -- create ------------------------------------------------------------

    def create(
        self,
        source_path: str | Path,
        *,
        format: str | None = None,
        title: str | None = None,
        language: str = "ko",
        encoding: str | None = None,
        book: BookRecord | None = None,
        target: TargetRecord | None = None,
    ) -> ReaderProject:
        identity = compute_source_identity(source_path, format=format)
        now = _now_iso()
        display_title = title or Path(identity.path).stem

        project = ReaderProject(
            project_id=uuid.uuid4().hex,
            source=identity.to_source_record(
                title=display_title, language=language, encoding=encoding
            ),
            book=book
            or BookRecord(
                format=identity.format,
                title=display_title,
            ),
            target=target or TargetRecord(),
            state=StateRecord(reader_status=ReaderStatus.NOT_STARTED.value),
            execution=ExecutionRecord(
                pipeline_mode="epub" if identity.format == "epub" else "runtime"
            ),
            output=OutputRecord(),
            project_schema_version=SCHEMA_VERSION,
            created_at=now,
            updated_at=now,
            last_activity_at=now,
        )
        self.store.write(project.project_id, project.to_dict())
        return project

    # -- load / save -------------------------------------------------------

    def load(self, project_id: str) -> ReaderProject:
        try:
            payload = self.store.read_raw(project_id)
        except FileNotFoundError as exc:
            raise ProjectNotFoundError(str(exc)) from exc
        return self._load_payload(payload)

    def load_from_path(self, path: str | Path) -> ReaderProject:
        try:
            payload = self.store.read_from_path(path)
        except FileNotFoundError as exc:
            raise ProjectNotFoundError(str(exc)) from exc
        return self._load_payload(payload)

    def _load_payload(self, payload: dict) -> ReaderProject:
        version = int(payload.get("project_schema_version") or 0)
        if version > SCHEMA_VERSION:
            raise ProjectSchemaError(
                f"project schema v{version} is newer than supported v{SCHEMA_VERSION}"
            )
        if version < SCHEMA_VERSION:
            payload = _migrate(payload)
        return ReaderProject.from_dict(payload)

    def save(self, project: ReaderProject) -> ReaderProject:
        project.updated_at = _now_iso()
        self.store.write(project.project_id, project.to_dict())
        return project

    def update(
        self,
        project: ReaderProject,
        *,
        source: SourceRecord | None = None,
        book: BookRecord | None = None,
        target: TargetRecord | None = None,
        state: StateRecord | None = None,
        execution: ExecutionRecord | None = None,
        output: OutputRecord | None = None,
        touch_activity: bool = True,
    ) -> ReaderProject:
        updated = replace(
            project,
            source=source if source is not None else project.source,
            book=book if book is not None else project.book,
            target=target if target is not None else project.target,
            state=state if state is not None else project.state,
            execution=execution if execution is not None else project.execution,
            output=output if output is not None else project.output,
        )
        now = _now_iso()
        updated.updated_at = now
        if touch_activity:
            updated.last_activity_at = now
        self.store.write(updated.project_id, updated.to_dict())
        return updated

    # -- glossary (S12-02) -------------------------------------------------

    def attach_glossary(self, project: ReaderProject, source_path: str | Path) -> ReaderProject:
        """Validate/import a glossary, store a project-owned snapshot, attach it.

        The snapshot is written first (content-hash named, atomic); the project
        record is updated only afterwards, so a failure never leaves the project
        pointing at a partially written snapshot. Old snapshots are collected only
        after the new project state is persisted.
        """
        from .glossary import build_record_for_file, persist_snapshot

        record = build_record_for_file(source_path)
        record = persist_snapshot(self.store, project.project_id, record)

        updated = replace(project, glossary=record)
        now = _now_iso()
        updated.updated_at = now
        updated.last_activity_at = now
        self.store.write(updated.project_id, updated.to_dict())

        self.store.delete_glossary_snapshots(project.project_id, keep=Path(record.stored_path))
        return updated

    def replace_glossary(self, project: ReaderProject, source_path: str | Path) -> ReaderProject:
        """Replace the attached glossary atomically (same path as attach)."""
        return self.attach_glossary(project, source_path)

    def detach_glossary(self, project: ReaderProject) -> ReaderProject:
        """Clear the glossary attachment; unrelated project state is untouched."""
        if project.glossary is not None:
            self.store.delete_glossary_snapshots(project.project_id, keep=None)
        updated = replace(project, glossary=None)
        now = _now_iso()
        updated.updated_at = now
        updated.last_activity_at = now
        self.store.write(updated.project_id, updated.to_dict())
        return updated

    def glossary_option_path(self, project: ReaderProject) -> Path | None:
        from .glossary import glossary_option_path

        return glossary_option_path(project)

    def resolve_glossary(self, project: ReaderProject) -> dict[str, str]:
        from .glossary import resolve_active_glossary

        return resolve_active_glossary(project)

    # -- list / delete -----------------------------------------------------

    def list_projects(self) -> list[ReaderProject]:
        projects: list[ReaderProject] = []
        for file_path in self.store.list_project_files():
            try:
                payload = self.store.read_from_path(file_path)
                projects.append(self._load_payload(payload))
            except (OSError, ValueError, ProjectError):
                continue
        projects.sort(key=lambda p: p.last_activity_at or "", reverse=True)
        return projects

    def exists(self, project_id: str) -> bool:
        return self.store.exists(project_id)

    def delete(self, project_id: str, *, confirm: bool = False) -> bool:
        """Delete exactly one project directory.

        Requires ``confirm=True`` (S9 §11). Never touches sources, outputs,
        runtime checkpoints, or other projects.
        """
        if not confirm:
            raise ProjectError("delete requires explicit confirmation")
        return self.store.delete(project_id)

    # -- recovery validation (S9-06) -----------------------------------------

    def validate_recovery_eligibility(self, project_id: str) -> "RecoveryEligibility":
        """Check if a project is eligible for recovery per canonical contract.

        Returns RecoveryEligibility with deterministic result.
        """
        project = self.load(project_id)
        return validate_recovery_eligibility(project)

    def get_recovery_blocked_reason(self, project_id: str) -> tuple[str, str]:
        """Get human-readable reason why recovery is blocked.

        Returns (blocked_by, reason) where blocked_by is one of:
        "project", "source", "artifact", "state", or "" if eligible.
        """
        project = self.load(project_id)
        from .recovery import get_recovery_blocked_reason
        return get_recovery_blocked_reason(project)

    def validate_source_integrity(self, project_id: str) -> tuple[bool, str, dict]:
        """Validate source file still matches recorded identity.

        Returns (is_valid, reason, details).
        """
        project = self.load(project_id)
        from .recovery import validate_source_integrity
        return validate_source_integrity(project)

    def validate_runtime_artifact(self, project_id: str) -> tuple[bool, str, dict]:
        """Validate runtime artifact exists, is readable, and bindings are correct."""
        project = self.load(project_id)
        from .recovery import validate_runtime_artifact
        return validate_runtime_artifact(project)
