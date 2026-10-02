"""Project dashboard presentation model (S9-04).

Pure, Qt-free mapping from a persisted ReaderProject to a card view model.
It reuses the canonical S9-03 derivation (``state.derive_state``) and the S9-03
zh-TW label contract (``labels``); it does not define a second reader-state
system (S9-04 §4.2).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.reader_project import labels as ReaderLabels
from core.reader_project.models import ReaderProject, ReaderStatus, StateRecord
from core.reader_project.recovery import check_recovery_eligibility
from core.reader_project.state import derive_state


@dataclass(frozen=True)
class ProjectCardModel:
    project_id: str
    title: str
    format: str
    format_label: str
    direction: str
    reader_status: str
    status_label: str
    progress_label: str
    completed_units: int
    total_units: int
    source_name: str
    source_path: str
    source_exists: bool
    last_activity: str
    action_label: str
    can_act: bool
    can_delete: bool
    note: str
    output_reference_present: bool
    output_exists: bool
    output_kind_label: str
    output_name: str
    output_note: str
    can_open_result: bool
    can_reveal_folder: bool
    recovery_eligible: bool = False
    recovery_blocked_reason: str = ""
    recovery_blocked_by: str = ""


def build_card_model(
    project: ReaderProject,
    state: StateRecord | None = None,
    source_exists: bool | None = None,
) -> ProjectCardModel:
    """Build a reader-facing card model from a persisted project."""
    if state is None:
        state = derive_state(project)

    if source_exists is None:
        try:
            source_exists = bool(project.source.path) and Path(project.source.path).is_file()
        except (OSError, ValueError):
            source_exists = False

    status = state.reader_status

    artifact = project.output.artifact_path
    output_reference_present = bool(artifact)
    try:
        output_exists = bool(artifact) and Path(artifact).is_file()
    except (OSError, ValueError):
        output_exists = False

    output_kind_label = ""
    output_name = ""
    if artifact:
        output_kind_label = ReaderLabels.format_label(
            project.output.artifact_kind or project.source.format
        )
        try:
            output_name = Path(artifact).name
        except (TypeError, ValueError):
            output_name = ""

    # S9-05: completion and output availability are distinct.
    # A canonical COMPLETED status implies an available artifact; anything else
    # must not be presented as a normal completed result.
    output_note = ""
    if status == ReaderStatus.COMPLETED.value:
        action_label = ""
        can_open_result = output_exists
        can_reveal_folder = output_exists
        if not output_exists:
            output_note = "結果檔案不存在"
    else:
        # S9-05 owns completion/output; do not expose a fake output control.
        action_label = (
            ReaderLabels.primary_action_label(status) if source_exists else ""
        )
        can_open_result = False
        can_reveal_folder = False
        if output_reference_present and not output_exists:
            output_note = "結果檔案不存在"

    # S9-06: Recovery eligibility
    from core.reader_project.recovery import check_recovery_eligibility
    eligibility = check_recovery_eligibility(project)
    recovery_eligible = eligibility.eligible
    recovery_blocked_reason = eligibility.reason if not eligibility.eligible else ""
    recovery_blocked_by = eligibility.blocked_by

    return ProjectCardModel(
        project_id=project.project_id,
        title=project.book.title or project.source.title or project.project_id,
        format=project.source.format,
        format_label=ReaderLabels.format_label(project.source.format),
        direction=ReaderLabels.translation_direction(
            project.source.language, project.target.target_language
        ),
        reader_status=status,
        status_label=ReaderLabels.reader_status_label(status),
        progress_label=ReaderLabels.progress_text(state.completed_units, state.total_units),
        completed_units=state.completed_units,
        total_units=state.total_units,
        source_name=Path(project.source.path).name if project.source.path else "",
        source_path=project.source.path,
        source_exists=source_exists,
        last_activity=project.last_activity_at or project.updated_at or "",
        action_label=action_label,
        can_act=bool(action_label),
        can_delete=True,
        note=state.last_error or "",
        output_reference_present=output_reference_present,
        output_exists=output_exists,
        output_kind_label=output_kind_label,
        output_name=output_name,
        output_note=output_note,
        can_open_result=can_open_result,
        can_reveal_folder=can_reveal_folder,
        recovery_eligible=recovery_eligible,
        recovery_blocked_reason=recovery_blocked_reason,
        recovery_blocked_by=recovery_blocked_by,
    )
