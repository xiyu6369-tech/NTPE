from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QDialog, QVBoxLayout, QScrollArea, QTextEdit, QDialogButtonBox, QTabWidget, QFrame
from PySide6.QtGui import QFont

from ..resources.translations import Strings


class PreviewDialog(QDialog):
    """內容預覽對話框"""

    def __init__(self, book_info: dict, parent: QWidget | None = None):
        super().__init__(parent)
        self._book_info = book_info
        self.setWindowTitle(Strings.PREVIEW_TITLE)
        self.setMinimumSize(700, 500)
        self.resize(800, 600)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 標題區域
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        title_label = QLabel(self._book_info.get("title", Strings.UNKNOWN))
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setWeight(QFont.Weight.Bold)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)

        # 狀態標籤
        status = self._book_info.get("status", "")
        if status == "partial":
            status_label = QLabel("部分匯入")
            status_label.setStyleSheet("color: #ffc107; font-weight: 600; padding: 4px 8px; background-color: #fff3cd; border-radius: 4px;")
            header_layout.addWidget(status_label)
        elif status == "success" or status == "ready":
            status_label = QLabel("已匯入")
            status_label.setStyleSheet("color: #198754; font-weight: 600; padding: 4px 8px; background-color: #d1e7dd; border-radius: 4px;")
            header_layout.addWidget(status_label)

        header_layout.addStretch()

        # 來源檔案
        source_label = QLabel(self._book_info.get("source", ""))
        source_label.setStyleSheet("color: #6c757d; font-size: 12px;")
        source_label.setWordWrap(True)
        header_layout.addWidget(source_label)

        layout.addLayout(header_layout)

        # 分隔線
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        # 內容區域
        chapter_map = self._book_info.get("chapter_map", [])

        if chapter_map:
            # EPUB：分章節顯示
            tab_widget = QTabWidget()
            tab_widget.setTabPosition(QTabWidget.TabPosition.North)

            # 全文標籤
            full_text_widget = QWidget()
            full_text_layout = QVBoxLayout(full_text_widget)
            full_text_layout.setContentsMargins(0, 0, 0, 0)

            full_text_edit = QTextEdit()
            full_text_edit.setReadOnly(True)
            full_text_edit.setFont(QFont("Microsoft JhengHei", 11))
            full_text_edit.setPlainText(self._book_info.get("preview_text", Strings.PREVIEW_NO_CONTENT))
            full_text_layout.addWidget(full_text_edit)

            tab_widget.addTab(full_text_widget, Strings.PREVIEW_FULL)

            # 章節標籤
            for ch in self._book_info.get("chapter_map", []):
                ch_widget = QWidget()
                ch_layout = QVBoxLayout(ch_widget)
                ch_layout.setContentsMargins(0, 0, 0, 0)

                ch_text_edit = QTextEdit()
                ch_text_edit.setReadOnly(True)
                ch_text_edit.setFont(QFont("Microsoft JhengHei", 11))

                # 從 preview_text 提取章節內容
                start = ch.get("start_offset", 0)
                end = ch.get("end_offset", 0)
                full_text = self._book_info.get("preview_text", "")
                if 0 <= start < end <= len(full_text):
                    ch_content = full_text[start:end]
                else:
                    ch_content = full_text

                ch_text_edit.setPlainText(ch_content)
                ch_layout.addWidget(ch_text_edit)

                tab_widget.addTab(ch_widget, ch.get("title", f"Chapter {ch.get('index', '?')}"))

            layout.addWidget(tab_widget)

        else:
            # TXT 或無章節資訊：顯示全文
            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            text_edit.setFont(QFont("Microsoft JhengHei", 11))

            preview_text = self._book_info.get("preview_text", Strings.PREVIEW_NO_CONTENT)
            if not preview_text or preview_text.strip() == "":
                preview_text = Strings.PREVIEW_NO_CONTENT

            text_edit.setPlainText(preview_text)
            layout.addWidget(text_edit)

        # 警告顯示
        warnings = self._book_info.get("warnings", [])
        if warnings:
            warning_text = Strings.PREVIEW_WARNINGS.format(warnings="; ".join(warnings))
            warning_label = QLabel(warning_text)
            warning_label.setStyleSheet("color: #ffc107; padding: 8px; background-color: #fff3cd; border-radius: 4px;")
            warning_label.setWordWrap(True)
            layout.addWidget(warning_label)

        # 截取提示
        preview_text = self._book_info.get("preview_text", "")
        if len(preview_text) > 10000:
            trunc_label = QLabel(Strings.PREVIEW_TRUNCATED.format(chars=10000))
            trunc_label.setStyleSheet("color: #6c757d; font-size: 11px;")
            layout.addWidget(trunc_label)

        # 底部按鈕
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.StandardButton.Close).setText(Strings.PREVIEW_CLOSE)
        layout.addWidget(button_box)


class ProjectPage(QWidget):
    """專案管理頁面"""

    # 導航信號
    navigate_home = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._projects = []  # 專案資料列表
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # 頂部工具列
        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)

        # 返回按鈕
        btn_back = QPushButton(Strings.BTN_BACK)
        btn_back.setFixedHeight(36)
        btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_back.clicked.connect(self._on_back)
        btn_back.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 0 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #f8f9fa;
                border-color: #adb5bd;
            }
        """)
        toolbar.addWidget(btn_back)

        # 頁面標題
        title = QLabel(Strings.PROJECT_TITLE)
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setWeight(QFont.Weight.Bold)
        title.setFont(title_font)
        toolbar.addWidget(title)

        toolbar.addStretch()

        # 預覽內容按鈕
        self.btn_preview = QPushButton(Strings.PROJECT_ACTION_PREVIEW)
        self.btn_preview.setFixedHeight(36)
        self.btn_preview.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_preview.setEnabled(False)
        self.btn_preview.clicked.connect(self._on_preview)
        self.btn_preview.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 0 20px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover:enabled {
                background-color: #5a6268;
            }
            QPushButton:disabled {
                background-color: #dee2e6;
                color: #adb5bd;
            }
        """)
        toolbar.addWidget(self.btn_preview)

        # 新增專案按鈕
        btn_new = QPushButton("新增專案")
        btn_new.setFixedHeight(36)
        btn_new.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_new.clicked.connect(self._on_new_project)
        btn_new.setStyleSheet("""
            QPushButton {
                background-color: #0d6efd;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 0 20px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #0b5ed7;
            }
            QPushButton:pressed {
                background-color: #0a58ca;
            }
        """)
        toolbar.addWidget(btn_new)

        layout.addLayout(toolbar)

        # 專案列表表格
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            Strings.PROJECT_COLUMN_NAME,
            Strings.PROJECT_COLUMN_SOURCE,
            Strings.PROJECT_COLUMN_STATUS,
            Strings.PROJECT_COLUMN_PROGRESS,
        ])

        # 表格設定
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # 欄寬設定
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setMinimumSectionSize(100)

        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                font-size: 13px;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                border: none;
                border-bottom: 1px solid #dee2e6;
                padding: 10px 12px;
                font-weight: 600;
                font-size: 12px;
                color: #495057;
            }
            QTableWidget::item {
                padding: 8px 12px;
                border-bottom: 1px solid #f1f3f5;
            }
            QTableWidget::item:selected {
                background-color: #e7f1ff;
                color: #0d6efd;
            }
        """)

        layout.addWidget(self.table)

        # 連接選擇變更信號
        self.table.selectionModel().selectionChanged.connect(self._on_selection_changed)

        # 空狀態提示
        self.empty_label = QLabel(Strings.PROJECT_LIST_EMPTY)
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: #999999; font-size: 14px; padding: 48px;")
        self.empty_label.hide()
        layout.addWidget(self.empty_label)

        self._update_empty_state()

    def _update_empty_state(self) -> None:
        """更新空狀態顯示"""
        is_empty = len(self._projects) == 0
        self.table.setVisible(not is_empty)
        self.empty_label.setVisible(is_empty)

    def add_project(self, name: str, source: str, status: str = "待處理", progress: str = "0%", book_info: dict | None = None) -> None:
        """新增專案到列表"""
        row = self.table.rowCount()
        self.table.insertRow(row)

        # 專案名稱
        name_item = QTableWidgetItem(name)
        name_item.setFont(QFont("Microsoft JhengHei", 10))
        self.table.setItem(row, 0, name_item)

        # 來源檔案
        source_item = QTableWidgetItem(source)
        source_item.setForeground(Qt.GlobalColor.darkGray)
        self.table.setItem(row, 1, source_item)

        # 狀態
        status_item = QTableWidgetItem(status)
        status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 2, status_item)

        # 進度
        progress_item = QTableWidgetItem(progress)
        progress_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 3, progress_item)

        # 儲存完整書籍資訊（包含預覽內容）
        project_data = {
            "name": name,
            "source": source,
            "status": status,
            "progress": progress,
        }
        if book_info:
            project_data.update(book_info)

        self._projects.append(project_data)

        self._update_empty_state()


    def _on_selection_changed(self) -> None:
        """選擇變更時更新預覽按鈕狀態"""
        has_selection = len(self.table.selectedItems()) > 0
        if has_selection:
            row = self.table.currentRow()
            if 0 <= row < len(self._projects):
                project = self._projects[row]
                # 只有有預覽內容才啟用預覽按鈕
                has_preview = bool(project.get("preview_text", "").strip())
                self.btn_preview.setEnabled(has_preview)
                return
        self.btn_preview.setEnabled(False)

    def _on_preview(self) -> None:
        """開啟預覽對話框"""
        row = self.table.currentRow()
        if 0 <= row < len(self._projects):
            project = self._projects[row]
            dialog = PreviewDialog(project, self)
            dialog.exec()

    def _on_back(self) -> None:
        self.navigate_home.emit()

    def _on_new_project(self) -> None:
        # TODO: 實作新增專案對話框
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "提示", Strings.PLACEHOLDER_NOT_IMPLEMENTED)
