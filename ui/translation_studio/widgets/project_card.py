"""Reader project card widget (S9-04)."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)

from ui.translation_studio.project_view_model import ProjectCardModel


class ProjectCard(QFrame):
    """A single reader project card in the "我的小說" library."""

    activated = Signal(str)          # project_id (open / select)
    selected = Signal(str)           # project_id (card body click → select)
    action_requested = Signal(str)   # project_id (primary action button: 開始翻譯)
    resume_requested = Signal(str)   # project_id (S9-06: Recovery action: 繼續翻譯)
    delete_requested = Signal(str)   # project_id
    open_result_requested = Signal(str)    # project_id (S9-05)
    reveal_folder_requested = Signal(str)  # project_id (S9-05)

    def __init__(self, model: ProjectCardModel, parent=None):
        super().__init__(parent)
        self._model = model
        self._selected = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("ProjectCard")
        self._setup_ui()
        self._apply_style()

    @property
    def project_id(self) -> str:
        return self._model.project_id

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel(self._model.title)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setWeight(QFont.Weight.Bold)
        title.setFont(title_font)
        header.addWidget(title)
        header.addStretch()

        status = QLabel(self._model.status_label)
        status.setStyleSheet(
            "color: #0d6efd; font-weight: 600; padding: 2px 8px;"
            " background-color: #e7f1ff; border-radius: 4px;"
        )
        header.addWidget(status)

        # S9-06: Recovery badge
        if self._model.recovery_eligible:
            recovery_badge = QLabel("可恢復")
            recovery_badge.setStyleSheet(
                "color: #198754; font-weight: 600; padding: 2px 8px;"
                " background-color: #d1e7dd; border-radius: 4px;"
            )
            header.addWidget(recovery_badge)
        elif self._model.recovery_blocked_by:
            recovery_badge = QLabel(f"不可恢復：{self._model.recovery_blocked_reason}")
            recovery_badge.setStyleSheet(
                "color: #dc3545; font-weight: 600; padding: 2px 8px;"
                " background-color: #f8d7da; border-radius: 4px;"
            )
            header.addWidget(recovery_badge)

        layout.addLayout(header)

        meta = QLabel(f"{self._model.format_label} · {self._model.direction}")
        meta.setStyleSheet("color: #6c757d; font-size: 12px;")
        layout.addWidget(meta)

        progress_row = QHBoxLayout()
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(self._percent())
        bar.setTextVisible(False)
        bar.setFixedHeight(8)
        bar.setStyleSheet(
            "QProgressBar { background-color: #e9ecef; border: none; border-radius: 4px; }"
            "QProgressBar::chunk { background-color: #198754; border-radius: 4px; }"
        )
        progress_row.addWidget(bar, stretch=1)
        progress = QLabel(self._model.progress_label)
        progress.setStyleSheet("color: #495057; font-size: 12px;")
        progress_row.addWidget(progress)
        layout.addLayout(progress_row)

        if self._model.total_units > 0:
            units = QLabel(
                f"已完成 {self._model.completed_units} / {self._model.total_units} 章"
            )
            units.setStyleSheet("color: #6c757d; font-size: 12px;")
            layout.addWidget(units)

        if not self._model.source_exists:
            missing = QLabel("來源檔案不存在或已移動")
            missing.setStyleSheet("color: #dc3545; font-size: 12px;")
            layout.addWidget(missing)

        if self._model.note:
            note = QLabel(self._model.note)
            note.setStyleSheet("color: #dc3545; font-size: 12px;")
            layout.addWidget(note)

        # S9-05: output presentation (only when a reference exists)
        if self._model.output_reference_present and self._model.output_name:
            output_label = QLabel(
                f"輸出：{self._model.output_kind_label} · {self._model.output_name}"
            )
            output_label.setStyleSheet("color: #495057; font-size: 12px;")
            layout.addWidget(output_label)

        if self._model.output_note:
            output_note = QLabel(self._model.output_note)
            output_note.setStyleSheet("color: #dc3545; font-size: 12px;")
            layout.addWidget(output_note)

        footer = QHBoxLayout()
        source = QLabel(self._model.source_name)
        source.setStyleSheet("color: #adb5bd; font-size: 11px;")
        footer.addWidget(source)
        footer.addStretch()

        if self._model.can_act:
            action = QPushButton(self._model.action_label)
            action.setCursor(Qt.CursorShape.PointingHandCursor)
            action.setStyleSheet(
                "QPushButton { background-color: #198754; color: white; border: none;"
                " border-radius: 6px; padding: 6px 16px; font-weight: 600; }"
                "QPushButton:hover { background-color: #157347; }"
            )
            action.clicked.connect(lambda: self.action_requested.emit(self._model.project_id))
            footer.addWidget(action)

        if self._model.can_open_result:
            open_result = QPushButton("開啟成品")
            open_result.setCursor(Qt.CursorShape.PointingHandCursor)
            open_result.setStyleSheet(
                "QPushButton { background-color: #0d6efd; color: white; border: none;"
                " border-radius: 6px; padding: 6px 16px; font-weight: 600; }"
                "QPushButton:hover { background-color: #0b5ed7; }"
            )
            open_result.clicked.connect(
                lambda: self.open_result_requested.emit(self._model.project_id)
            )
            footer.addWidget(open_result)

        # S9-06: Recovery action - 只有當 recovery_eligible 時才顯示
        if self._model.recovery_eligible:
            resume = QPushButton("繼續翻譯")
            resume.setCursor(Qt.CursorShape.PointingHandCursor)
            resume.setStyleSheet(
                "QPushButton { background-color: #198754; color: white; border: none;"
                " border-radius: 6px; padding: 6px 16px; font-weight: 600; }"
                "QPushButton:hover { background-color: #157347; }"
            )
            resume.clicked.connect(
                lambda: self.resume_requested.emit(self._model.project_id)
            )
            footer.addWidget(resume)

        if self._model.can_reveal_folder:
            reveal = QPushButton("開啟資料夾")
            reveal.setCursor(Qt.CursorShape.PointingHandCursor)
            reveal.setStyleSheet(
                "QPushButton { background-color: transparent; color: #0d6efd;"
                " border: 1px solid #a9c7ff; border-radius: 6px; padding: 6px 12px; }"
                "QPushButton:hover { background-color: #e7f1ff; }"
            )
            reveal.clicked.connect(
                lambda: self.reveal_folder_requested.emit(self._model.project_id)
            )
            footer.addWidget(reveal)

        delete = QPushButton("刪除")
        delete.setCursor(Qt.CursorShape.PointingHandCursor)
        delete.setStyleSheet(
            "QPushButton { background-color: transparent; color: #dc3545;"
            " border: 1px solid #f1aeb5; border-radius: 6px; padding: 6px 12px; }"
            "QPushButton:hover { background-color: #f8d7da; }"
        )
        delete.clicked.connect(lambda: self.delete_requested.emit(self._model.project_id))
        footer.addWidget(delete)

        layout.addLayout(footer)

    def _percent(self) -> int:
        total = self._model.total_units
        if total <= 0:
            return 0
        return max(0, min(100, int(round(self._model.completed_units * 100 / total))))

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        self._apply_style()

    def _apply_style(self) -> None:
        border = "#0d6efd" if self._selected else "#dee2e6"
        width = "2px" if self._selected else "1px"
        background = "#f8f9ff" if self._selected else "#ffffff"
        self.setStyleSheet(
            f"QFrame#ProjectCard {{ background-color: {background};"
            f" border: {width} solid {border}; border-radius: 10px; }}"
        )

    def mousePressEvent(self, event) -> None:  # noqa: N802 (Qt override)
        self.selected.emit(self._model.project_id)
        super().mousePressEvent(event)
