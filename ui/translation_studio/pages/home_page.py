from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QFileDialog, QMessageBox
from PySide6.QtGui import QFont

from ..resources.translations import Strings


class HomePage(QWidget):
    """首頁 - 歡迎畫面與主要動作入口"""
    
    # 導航信號
    navigate_to_project = Signal()
    navigate_to_import_txt = Signal()
    navigate_to_import_epub = Signal()
    txt_imported = Signal(dict)  # 成功匯入後發出書籍資訊
    
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._intake_adapter = None
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(24)
        layout.setContentsMargins(48, 48, 48, 48)
        
        # 標題區塊
        title_label = QLabel(Strings.APP_TITLE)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(28)
        title_font.setWeight(QFont.Weight.Bold)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # 副標題
        subtitle = QLabel(Strings.HOME_DESCRIPTION)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_font = QFont()
        subtitle_font.setPointSize(14)
        subtitle.setFont(subtitle_font)
        subtitle.setStyleSheet("color: #666666;")
        layout.addWidget(subtitle)
        
        layout.addSpacing(32)
        
        # 動作按鈕區塊
        actions_frame = QFrame()
        actions_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        actions_layout = QVBoxLayout(actions_frame)
        actions_layout.setSpacing(16)
        actions_layout.setContentsMargins(32, 24, 32, 24)
        
        # 匯入 TXT 按鈕
        btn_import_txt = self._create_action_button(
            Strings.HOME_ACTION_IMPORT_TXT,
            "匯入純文字檔案進行翻譯",
            self._on_import_txt
        )
        actions_layout.addWidget(btn_import_txt)
        
        # 匯入 EPUB 按鈕
        btn_import_epub = self._create_action_button(
            Strings.HOME_ACTION_IMPORT_EPUB,
            "匯入 EPUB 電子書進行翻譯",
            self._on_import_epub
        )
        actions_layout.addWidget(btn_import_epub)
        
        # 新增專案按鈕
        btn_new_project = self._create_action_button(
            Strings.HOME_ACTION_NEW_PROJECT,
            "建立新的翻譯專案",
            self._on_new_project
        )
        actions_layout.addWidget(btn_new_project)
        
        # 開啟專案按鈕
        btn_open_project = self._create_action_button(
            Strings.HOME_ACTION_OPEN_PROJECT,
            "開啟現有翻譯專案",
            self._on_open_project
        )
        actions_layout.addWidget(btn_open_project)
        
        layout.addWidget(actions_frame)
        layout.addStretch()
        
        # 底部版本資訊
        version_label = QLabel("NTPE Translation Studio v0.1.0")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet("color: #999999; font-size: 11px;")
        layout.addWidget(version_label)
    
    def _create_action_button(self, title: str, description: str, callback) -> QPushButton:
        """建立主要動作按鈕"""
        btn = QPushButton()
        btn.setFixedHeight(64)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(callback)
        
        btn_layout = QHBoxLayout(btn)
        btn_layout.setContentsMargins(24, 12, 24, 12)
        btn_layout.setSpacing(16)
        
        # 標題與描述
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setWeight(QFont.Weight.DemiBold)
        title_label.setFont(title_font)
        text_layout.addWidget(title_label)
        
        desc_label = QLabel(description)
        desc_label.setStyleSheet("color: #666666;")
        desc_font = QFont()
        desc_font.setPointSize(11)
        desc_label.setFont(desc_font)
        text_layout.addWidget(desc_label)
        
        btn_layout.addLayout(text_layout)
        btn_layout.addStretch()
        
        # 箭頭指示
        arrow = QLabel("→")
        arrow_font = QFont()
        arrow_font.setPointSize(20)
        arrow.setFont(arrow_font)
        arrow.setStyleSheet("color: #999999;")
        btn_layout.addWidget(arrow)
        
        # 樣式
        btn.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
            }
        """)
        
        return btn
    
    def _on_import_txt(self) -> None:
        """處理 TXT 匯入 - 使用 CanonicalBookIntakeAdapter"""
        # 開啟檔案選擇器
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            Strings.TXT_IMPORT_DIALOG_TITLE,
            "",
            Strings.TXT_FILE_FILTER,
        )
        
        if not file_path:
            # 使用者取消
            return
        
        source_path = Path(file_path)
        
        try:
            # 延遲導入以避免 circular import
            from core.adapters.canonical_book_intake_adapter import CanonicalBookIntakeAdapter
            
            if self._intake_adapter is None:
                self._intake_adapter = CanonicalBookIntakeAdapter()
            
            # 執行 canonical TXT intake
            result = self._intake_adapter.process_path(source_path)
            
            if result.status in ("ready", "ready_with_warnings"):
                # 匯入成功
                book_info = self._build_book_info(result, source_path)
                QMessageBox.information(
                    self,
                    Strings.TXT_IMPORT_SUCCESS_TITLE,
                    Strings.TXT_IMPORT_SUCCESS_MSG.format(
                        title=book_info.get("title", Strings.UNKNOWN),
                        source=book_info.get("source", str(source_path)),
                        chars=book_info.get("chars", 0),
                        encoding=book_info.get("encoding", Strings.UNKNOWN),
                    ),
                )
                self.txt_imported.emit(book_info)
            else:
                # 匯入失敗或有問題
                error_msg = Strings.TXT_IMPORT_FAILED_MSG.format(
                    status=result.status,
                    warnings="; ".join(result.warnings) if result.warnings else Strings.NO_DETAILS,
                )
                QMessageBox.warning(
                    self,
                    Strings.TXT_IMPORT_FAILED_TITLE,
                    error_msg,
                )
                
        except Exception as e:
            QMessageBox.critical(
                self,
                Strings.TXT_IMPORT_ERROR_TITLE,
                Strings.TXT_IMPORT_ERROR_MSG.format(error=str(e)),
            )
    
    def _build_book_info(self, result, source_path: Path) -> dict:
        """從 canonical intake result 建立書籍資訊"""
        intake_result = result.intake_result
        book_info = {
            "title": intake_result.file_name or source_path.stem,
            "source": str(source_path),
            "chars": intake_result.text_length,
            "encoding": intake_result.encoding,
            "status": result.status,
            "warnings": list(result.warnings),
            "submission_eligible": result.submission_eligible,
        }
        return book_info
    
    def _on_import_epub(self) -> None:
        """處理 EPUB 匯入 - 使用 EpubExtractionBoundary"""
        # 開啟檔案選擇器
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            Strings.EPUB_IMPORT_DIALOG_TITLE,
            "",
            Strings.EPUB_FILE_FILTER,
        )
        
        if not file_path:
            # 使用者取消
            return
        
        source_path = Path(file_path)
        
        try:
            # 延遲導入以避免 circular import
            from core.adapters.epub_extraction_boundary import EpubExtractionBoundary, EpubExtractionError
            
            extractor = EpubExtractionBoundary()
            extraction_result = None
            
            try:
                extraction_result = extractor.extract(source_path)
            except EpubExtractionError as e:
                if e.blocked:
                    QMessageBox.critical(
                        self,
                        Strings.EPUB_IMPORT_ERROR_TITLE,
                        Strings.EPUB_IMPORT_ERROR_MSG.format(error=str(e)),
                    )
                    return
                # manual_review_required: warn but continue
                QMessageBox.warning(
                    self,
                    Strings.EPUB_IMPORT_ERROR_TITLE,
                    Strings.EPUB_IMPORT_ERROR_MSG.format(error=str(e)),
                )
                # For non-blocked errors, we need to attempt extraction again or return
                # Since extraction failed, we cannot proceed
                return
            
            if extraction_result is None:
                return
            
            if extraction_result.status in ("success", "partial"):
                # 匯入成功
                book_info = self._build_epub_book_info(extraction_result, source_path)
                QMessageBox.information(
                    self,
                    Strings.EPUB_IMPORT_SUCCESS_TITLE,
                    Strings.EPUB_IMPORT_SUCCESS_MSG.format(
                        title=book_info.get("title", Strings.UNKNOWN),
                        source=book_info.get("source", str(source_path)),
                        chapters=book_info.get("chapters", 0),
                        chars=book_info.get("chars", 0),
                    ),
                )
                self.txt_imported.emit(book_info)
            else:
                # 匯入失敗
                error_msg = Strings.EPUB_IMPORT_FAILED_MSG.format(
                    status=extraction_result.status,
                    warnings="; ".join(extraction_result.warnings) if extraction_result.warnings else Strings.NO_DETAILS,
                )
                QMessageBox.warning(
                    self,
                    Strings.EPUB_IMPORT_FAILED_TITLE,
                    error_msg,
                )
                
        except Exception as e:
            QMessageBox.critical(
                self,
                Strings.EPUB_IMPORT_ERROR_TITLE,
                Strings.EPUB_IMPORT_ERROR_MSG.format(error=str(e)),
            )
    
    def _build_epub_book_info(self, extraction_result, source_path: Path) -> dict:
        """從 EPUB extraction result 建立書籍資訊"""
        metadata = extraction_result.metadata
        chapter_map = extraction_result.chapter_map
        
        # 計算線性章節數（用於顯示）
        linear_chapters = sum(1 for ch in chapter_map if ch.is_linear)
        total_chapters = len(chapter_map)
        
        book_info = {
            "title": metadata.title or source_path.stem,
            "source": str(source_path),
            "chapters": total_chapters,
            "linear_chapters": linear_chapters,
            "chars": len(extraction_result.extracted_text),
            "encoding": "utf-8",
            "status": extraction_result.status,
            "warnings": list(extraction_result.warnings),
            "metadata": {
                "title": metadata.title,
                "author": metadata.author,
                "language": metadata.language,
                "identifier": metadata.identifier,
                "publisher": metadata.publisher,
                "date": metadata.date,
            },
        }
        return book_info
    
    def _on_new_project(self) -> None:
        self.navigate_to_project.emit()
    
    def _on_open_project(self) -> None:
        self.navigate_to_project.emit()