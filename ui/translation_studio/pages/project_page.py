from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
from PySide6.QtGui import QFont

from ..resources.translations import Strings


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
    
    def add_project(self, name: str, source: str, status: str = "待處理", progress: str = "0%") -> None:
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
        
        self._projects.append({
            "name": name,
            "source": source,
            "status": status,
            "progress": progress,
        })
        
        self._update_empty_state()
    
    def _on_back(self) -> None:
        self.navigate_home.emit()
    
    def _on_new_project(self) -> None:
        # TODO: 實作新增專案對話框
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "提示", Strings.PLACEHOLDER_NOT_IMPLEMENTED)