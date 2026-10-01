from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QDialog, QVBoxLayout, QScrollArea, QTextEdit, QDialogButtonBox, QTabWidget, QFrame, QMessageBox
from PySide6.QtGui import QFont

from ..resources.translations import Strings
from ..translation_worker import TranslationRunner
from lts.txt_translation_runtime import TxtTranslationOptions
from core.epub_translation.runtime.adapter import EpubTranslationOptions
from core.adapters.epub_extraction_boundary import EpubExtractionBoundary
from core.adapters.canonical_book_intake_adapter import CanonicalBookIntakeAdapter
from core.adapters.epub_extraction_boundary import ExtractedTextIntakeRequest
from core.epub_translation.chunking import chunk_epub_translation_input, ChunkingOptions
from core.epub_translation.contract import (
    EpubTranslationInput, EpubMetadata, EpubChapterBoundary,
    ResourceRef, TocEntry, ExtractionManifest
)
from types import MappingProxyType


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
        self._translation_runner: TranslationRunner | None = None
        self._current_translation_row: int | None = None
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

        # 開始翻譯按鈕
        self.btn_translate = QPushButton(Strings.PROJECT_ACTION_TRANSLATE)
        self.btn_translate.setFixedHeight(36)
        self.btn_translate.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_translate.setEnabled(False)
        self.btn_translate.clicked.connect(self._on_translate)
        self.btn_translate.setStyleSheet("""
            QPushButton {
                background-color: #198754;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 0 20px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover:enabled {
                background-color: #157347;
            }
            QPushButton:disabled {
                background-color: #dee2e6;
                color: #adb5bd;
            }
        """)
        toolbar.addWidget(self.btn_translate)

        # 新增專案按鈕 — 專案持久化尚未支援，明確呈現為不可用
        self.btn_new_project = QPushButton(Strings.PROJECT_ACTION_NEW)
        self.btn_new_project.setFixedHeight(36)
        self.btn_new_project.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_new_project.clicked.connect(self._on_new_project)
        self.btn_new_project.setEnabled(False)
        self.btn_new_project.setToolTip(Strings.UNSUPPORTED_FEATURE_TOOLTIP)
        self.btn_new_project.setStyleSheet("""
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
            QPushButton:disabled {
                background-color: #dee2e6;
                color: #adb5bd;
            }
        """)
        toolbar.addWidget(self.btn_new_project)

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

                # 支援的專案類型（TXT 與 EPUB）：有有效來源且未在翻譯中即可啟用
                has_source = bool(project.get("source", "").strip())
                not_translating = self._current_translation_row != row
                self.btn_translate.setEnabled(has_source and not_translating)

                if not has_source:
                    self.btn_translate.setToolTip(Strings.TRANSLATION_NO_VALID_SOURCE)
                elif not not_translating:
                    self.btn_translate.setToolTip(Strings.TRANSLATION_ALREADY_RUNNING)
                else:
                    self.btn_translate.setToolTip("")
                return
        self.btn_preview.setEnabled(False)
        self.btn_translate.setEnabled(False)
        self.btn_translate.setToolTip("")

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
        # 專案持久化尚未支援；按鈕已停用，不呈現任何假成功流程。
        return

    def _on_translate(self) -> None:
        """啟動翻譯"""
        row = self.table.currentRow()
        if not (0 <= row < len(self._projects)):
            return

        project = self._projects[row]

        # 檢查是否有有效來源
        source = project.get("source", "")
        if not source:
            QMessageBox.warning(self, "提示", Strings.TRANSLATION_NO_VALID_SOURCE)
            return

        # 檢查是否已經在翻譯
        if self._current_translation_row == row:
            QMessageBox.information(self, "提示", Strings.TRANSLATION_ALREADY_RUNNING)
            return

        # 建立翻譯選項
        source_path = Path(source)

        is_epub = bool(project.get("chapter_map"))

        if is_epub:
            # EPUB 的最終輸出路徑由 canonical EPUB runtime / packager 決定
            # （source-adjacent，見 translation_worker._runtime_epub_translate），
            # 並非由 UI 指定，因此不傳入任何 UI output path。
            options = self._build_epub_options(project, source_path)
        else:
            # TXT 使用 UI 決定的專案輸出資料夾。
            output_dir = Path("output") / source_path.stem
            output_dir.mkdir(parents=True, exist_ok=True)
            options = TxtTranslationOptions(
                input_path=source_path,
                output_dir=output_dir,
                chunk_size=1000,
                model="meta/llama-3.2-90b-vision-instruct",
                project_name=project.get("name", "NTPE Novel Translation"),
                source_language="ko",
                target_language="zh-TW",
                resume=True,
                dry_run=False,
                max_retries=3,
                retry_base_seconds=5.0,
                glossary_path=None,
                character_memory_path=None,
                strict_lock_terms=True,
                qa_enabled=True,
                qa_fail_policy="retry",
                min_length_ratio=0.18,
                max_korean_chars=2,
                max_repeated_lines=2,
                output_formatter_enabled=True,
                taiwan_traditional_normalization=True,
                quality_profile="literary",
                previous_context_chars=700,
                simplified_chinese_policy="normalize",
                progress_enabled=True,
                speed="balanced",
                quality_v5_enabled=True,
                quality_v5_report_enabled=True,
                quality_integration_v72=False,
                quality_character_memory_v72=False,
                quality_context_scene_v72=False,
                quality_naturalness_v72=False,
                quality_integration_kill_switch_v72=False,
                quality_delivery_v83=False,
                quality_delivery_formats_v83=("txt",),
            )

        # 更新 UI 狀態
        self._current_translation_row = row
        self._update_project_status(row, Strings.TRANSLATION_STATUS_PREPARING, "0%")
        self.btn_translate.setEnabled(False)
        self.btn_preview.setEnabled(False)

        # 啟動翻譯 worker
        # 專案根目錄：repo root (parents[3] 從 ui/translation_studio/pages/ 往上三層)
        root_path = Path(__file__).resolve().parents[3]
        self._translation_runner = TranslationRunner(options, root_path)
        self._translation_runner.start(
            on_progress=self._on_translation_progress,
            on_finished=self._on_translation_finished,
            on_error=self._on_translation_error,
        )

    def _build_epub_options(self, project: dict, source_path: Path):
        """Build EPUB translation options from project data.

        The EPUB output destination is owned by the canonical EPUB runtime and
        packager (source-adjacent); the UI does not select it, so no output
        path is accepted or forwarded here.
        """
        # Step 1: Extract EPUB
        extractor = EpubExtractionBoundary()
        extraction_result = extractor.extract(source_path)

        # Step 2: Create intake request
        intake_request = ExtractedTextIntakeRequest(
            source_path=extraction_result.source_path,
            source_format="epub",
            extracted_text=extraction_result.extracted_text,
            original_file_hash=extraction_result.original_hash,
            extracted_text_hash=extraction_result.extracted_hash,
            epub_metadata=dict(extraction_result.metadata.raw) if extraction_result.metadata.raw else {},
            chapter_map=extraction_result.chapter_map,
            extraction_manifest=extraction_result.extraction_manifest,
            extractor_version=extraction_result.extraction_manifest.extractor_version,
            status=extraction_result.status,
            warnings=extraction_result.warnings,
        )

        # Step 3: Process through canonical intake adapter
        adapter = CanonicalBookIntakeAdapter()
        intake_result = adapter.ingest_extracted(intake_request)

        if not intake_result.submission_eligible:
            raise ValueError(f"EPUB intake not eligible for translation: {intake_result.status}")

        # Step 4: Build EpubTranslationInput from intake result
        epub_metadata = EpubMetadata(
            title=intake_result.epub_metadata.get("title") if intake_result.epub_metadata else None,
            author=intake_result.epub_metadata.get("author") if intake_result.epub_metadata else None,
            language=intake_result.epub_metadata.get("language") if intake_result.epub_metadata else None,
            identifier=intake_result.epub_metadata.get("identifier") if intake_result.epub_metadata else None,
            publisher=intake_result.epub_metadata.get("publisher") if intake_result.epub_metadata else None,
            date=intake_result.epub_metadata.get("date") if intake_result.epub_metadata else None,
            raw=MappingProxyType(dict(intake_result.epub_metadata.get("raw", {})) if intake_result.epub_metadata else {}),
        )

        chapter_map = tuple(
            EpubChapterBoundary(
                index=cb.index,
                spine_position=cb.spine_position,
                title=cb.title,
                source_href=cb.source_href,
                start_offset=cb.start_offset,
                end_offset=cb.end_offset,
                is_linear=cb.is_linear,
                word_count=cb.word_count,
                body_start_offset=cb.body_start_offset,
                body_end_offset=cb.body_end_offset,
                landmark_type=cb.landmark_type,
                status=cb.status,
                toc_level=cb.toc_level,
            )
            for cb in (intake_result.chapter_map or ())
        )

        resources = tuple(
            ResourceRef(
                type=rr.type,
                href=rr.href,
                chapter_index=rr.chapter_index,
                metadata=MappingProxyType(dict(rr.metadata)),
            )
            for rr in (intake_result.resource_refs or ())
        )

        extraction_manifest = None
        if intake_result.extraction_manifest:
            extraction_manifest = ExtractionManifest(
                extractor_version=intake_result.extraction_manifest.extractor_version,
                extracted_at=intake_result.extraction_manifest.extracted_at,
                chapter_count=intake_result.extraction_manifest.chapter_count,
                total_characters=intake_result.extraction_manifest.total_characters,
                total_words=intake_result.extraction_manifest.total_words,
                warnings=intake_result.extraction_manifest.warnings,
                resources=resources,
                spine_item_count=intake_result.extraction_manifest.spine_item_count,
                nav_toc_entries=intake_result.extraction_manifest.nav_toc_entries,
                encoding_used=intake_result.extraction_manifest.encoding_used,
                parsing_duration_ms=intake_result.extraction_manifest.parsing_duration_ms,
                fixed_layout=intake_result.extraction_manifest.fixed_layout,
            )

        translation_input = EpubTranslationInput(
            source_epub_path=source_path,
            original_hash=extraction_result.original_hash,
            extraction_status=extraction_result.status,
            warnings=extraction_result.warnings,
            metadata=epub_metadata,
            chapter_map=chapter_map,
            resources=resources,
            toc_entries=(),
            fixed_layout_info=intake_result.extraction_manifest.fixed_layout if intake_result.extraction_manifest else None,
            extraction_manifest=extraction_manifest,
        )

        # Step 5: Chunk the translation input
        chunking_options = ChunkingOptions(chunk_size=1000)
        chunks = chunk_epub_translation_input(translation_input, extraction_result.extracted_text, chunking_options)

        # Step 6: Build EPUB translation options
        return EpubTranslationOptions(
            translation_input=translation_input,
            chunks=chunks,
            model="meta/llama-3.2-90b-vision-instruct",
            project_name=project.get("name", "NTPE EPUB Translation"),
            source_language="ko",
            target_language="zh-TW",
            resume=True,
            dry_run=False,
            max_retries=3,
            retry_base_seconds=10.0,
            glossary_path=None,
            character_memory_path=None,
            strict_lock_terms=True,
            qa_enabled=True,
            qa_fail_policy="retry",
            min_length_ratio=0.18,
            max_korean_chars=2,
            max_repeated_lines=2,
            output_formatter_enabled=True,
            taiwan_traditional_normalization=True,
            quality_profile="literary",
            previous_context_chars=700,
            simplified_chinese_policy="normalize",
            progress_enabled=True,
            speed="balanced",
        )

    def _on_translation_progress(self, progress: dict) -> None:
        """處理翻譯進度更新"""
        if self._current_translation_row is None:
            return

        status = progress.get("status", "")
        chunk_total = progress.get("chunk_total", 0)
        chunk_completed = progress.get("chunk_completed", 0)
        message = progress.get("message", "")

        if status == "preparing":
            progress_text = "準備中..."
        elif status == "running":
            if chunk_total > 0:
                progress_text = Strings.TRANSLATION_PROGRESS_FORMAT.format(
                    completed=chunk_completed, total=chunk_total
                )
            else:
                progress_text = "翻譯中..."
        elif status == "completed":
            progress_text = Strings.TRANSLATION_PROGRESS_FORMAT.format(
                completed=chunk_completed, total=chunk_total
            )
        elif status == "incomplete":
            chunk_failed = progress.get("chunk_failed", 0)
            progress_text = f"未完成：{chunk_completed}/{chunk_total} 成功，{chunk_failed} 失敗"
        elif status == "dry_run":
            progress_text = Strings.TRANSLATION_STATUS_DRY_RUN
        elif status == "failed":
            progress_text = "失敗"
        else:
            progress_text = message or status

        self._update_project_status(self._current_translation_row, message, progress_text)

    def _on_translation_finished(self, result: dict) -> None:
        """處理翻譯完成"""
        if self._current_translation_row is None:
            return

        row = self._current_translation_row
        status = result.get("status", "unknown")

        if status == "success":
            output = result.get("output", "")
            chunk_total = result.get("chunk_total", 0)
            chunk_successful = result.get("chunk_successful", 0)
            session_id = result.get("session_id", "")

            self._update_project_status(
                row,
                Strings.TRANSLATION_STATUS_COMPLETED,
                Strings.TRANSLATION_CHUNKS_SUCCESSFUL.format(
                    successful=chunk_successful, total=chunk_total
                ),
            )

            # 顯示完成訊息
            QMessageBox.information(
                self,
                Strings.TRANSLATION_STATUS_COMPLETED,
                f"翻譯完成！\n\n"
                f"輸出位置：{output}\n"
                f"成功區塊：{chunk_successful} / {chunk_total}\n"
                f"Session ID：{session_id}",
            )

        elif status == "incomplete":
            chunk_total = result.get("chunk_total", 0)
            chunk_successful = result.get("chunk_successful", 0)
            chunk_failed = result.get("chunk_failed", 0)
            error = result.get("error", "未知錯誤")

            self._update_project_status(
                row,
                Strings.TRANSLATION_STATUS_INCOMPLETE,
                f"{chunk_successful}/{chunk_total} 成功",
            )

            QMessageBox.warning(
                self,
                Strings.TRANSLATION_STATUS_INCOMPLETE,
                f"翻譯未完成\n\n"
                f"成功：{chunk_successful} / {chunk_total}\n"
                f"失敗：{chunk_failed}\n"
                f"錯誤：{error}",
            )

        elif status == "dry_run":
            self._update_project_status(
                row,
                Strings.TRANSLATION_STATUS_DRY_RUN,
                "Dry-Run",
            )
            QMessageBox.information(
                self,
                Strings.TRANSLATION_STATUS_DRY_RUN,
                "Dry-Run 已完成，未執行正式翻譯，也未產生正式輸出。",
            )

        else:
            error = result.get("error", "未知錯誤")
            self._update_project_status(
                row,
                Strings.TRANSLATION_STATUS_FAILED,
                "失敗",
            )
            QMessageBox.critical(
                self,
                Strings.TRANSLATION_STATUS_FAILED,
                f"{Strings.TRANSLATION_ERROR_PREFIX}{error}",
            )

        # 重置狀態
        self._current_translation_row = None
        self._translation_runner = None
        self._update_selection_buttons()

    def _on_translation_error(self, error: str) -> None:
        """處理翻譯錯誤"""
        if self._current_translation_row is None:
            return

        row = self._current_translation_row
        self._update_project_status(
            row,
            Strings.TRANSLATION_STATUS_FAILED,
            "錯誤",
        )
        QMessageBox.critical(
            self,
            Strings.TRANSLATION_STATUS_FAILED,
            f"{Strings.TRANSLATION_ERROR_PREFIX}{error}",
        )

        self._current_translation_row = None
        self._translation_runner = None
        self._update_selection_buttons()

    def _update_project_status(self, row: int, status: str, progress: str) -> None:
        """更新專案列表中的狀態和進度"""
        if 0 <= row < len(self._projects):
            self._projects[row]["status"] = status
            self._projects[row]["progress"] = progress

            status_item = self.table.item(row, 2)
            progress_item = self.table.item(row, 3)

            if status_item:
                status_item.setText(status)
            if progress_item:
                progress_item.setText(progress)

    def _update_selection_buttons(self) -> None:
        """更新選擇相關按鈕狀態"""
        self._on_selection_changed()
