"""NTPE Reader-First Project persistence (S9).

A persistent Project is the reader-visible unit: one novel, one project.

This package owns Project metadata persistence only. It does NOT:
- implement translation
- call providers
- create a second checkpoint engine
- rewrite runtime resume state

It references the existing canonical runtime resume state and artifacts.
"""

from __future__ import annotations

from .models import (
    SCHEMA_VERSION,
    ReaderStatus,
    ReaderProject,
    SourceRecord,
    BookRecord,
    TargetRecord,
    StateRecord,
    ExecutionRecord,
    OutputRecord,
)
from .identity import SourceIdentity
from .store import ProjectStore, resolve_ntpe_home
from .manager import ReaderProjectManager
from .state import derive_reader_status, derive_state, read_resume_state
from .recovery import (
    RecoveryEligibility,
    validate_recovery_eligibility,
    get_recovery_blocked_reason,
    check_recovery_eligibility,
    validate_source_integrity,
    validate_runtime_artifact,
    SourceIntegrityError,
    RuntimeArtifactError,
    RecoveryError,
)

__all__ = [
    "SCHEMA_VERSION",
    "ReaderStatus",
    "ReaderProject",
    "SourceRecord",
    "BookRecord",
    "TargetRecord",
    "StateRecord",
    "ExecutionRecord",
    "OutputRecord",
    "SourceIdentity",
    "ProjectStore",
    "resolve_ntpe_home",
    "ReaderProjectManager",
    "derive_reader_status",
    "derive_state",
    "read_resume_state",
]
