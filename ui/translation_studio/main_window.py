from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QPushButton, QLabel
from PySide6.QtGui import QFont, QIcon

from .pages import HomePage, ProjectPage
from .resources.translations import Strings


class MainWindow(QMainWindow):
    """主視窗 - 包含導航列與頁面堆疊"""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._current_page = "home"
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        self.setWindowTitle(Strings.APP_TITLE)
        self.setMinimumSize(960, 640)
        self.resize(1024, 720)

        # 中央元件
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 導航列
        self.nav_bar = self._create_nav_bar()
        main_layout.addWidget(self.nav_bar)

        # 頁面堆疊
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        # 建立頁面
        self.home_page = HomePage()
        self.project_page = ProjectPage()

        self.stack.addWidget(self.home_page)      # index 0
        self.stack.addWidget(self.project_page)   # index 1

        # 設定預設頁面
        self.stack.setCurrentIndex(0)
        self._update_nav_selection(0)

    def _create_nav_bar(self) -> QWidget:
        """建立導航列"""
        nav = QWidget()
        nav.setFixedHeight(56)
        nav.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-bottom: 1px solid #dee2e6;
            }
        """)

        layout = QHBoxLayout(nav)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(8)

        # Logo / App Title
        logo = QLabel(Strings.APP_TITLE)
        logo_font = QFont()
        logo_font.setPointSize(16)
        logo_font.setWeight(QFont.Weight.Bold)
        logo.setFont(logo_font)
        layout.addWidget(logo)

        layout.addStretch()

        # 導航按鈕
        self.nav_buttons = {}

        for page_id, label in [("home", Strings.NAV_HOME), ("project", Strings.NAV_PROJECT)]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setFixedHeight(36)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: none;
                    border-radius: 6px;
                    padding: 0 16px;
                    font-size: 13px;
                    font-weight: 500;
                    color: #495057;
                }
                QPushButton:hover {
                    background-color: #f8f9fa;
                    color: #0d6efd;
                }
                QPushButton:checked {
                    background-color: #e7f1ff;
                    color: #0d6efd;
                    font-weight: 600;
                }
            """)
            btn.clicked.connect(lambda checked, pid=page_id: self._on_nav_clicked(pid))
            self.nav_buttons[page_id] = btn
            layout.addWidget(btn)

        return nav

    def _connect_signals(self) -> None:
        self.home_page.navigate_to_project.connect(lambda: self._navigate_to("project"))
        self.home_page.navigate_to_import_txt.connect(lambda: self._on_import_action("txt"))
        self.home_page.navigate_to_import_epub.connect(lambda: self._on_import_action("epub"))
        self.project_page.navigate_home.connect(lambda: self._navigate_to("home"))
        # Import result signals
        self.home_page.txt_imported.connect(self._on_txt_imported)
        self.home_page.epub_imported.connect(self._on_epub_imported)

    def _on_nav_clicked(self, page_id: str) -> None:
        self._navigate_to(page_id)

    def _navigate_to(self, page_id: str) -> None:
        """切換頁面"""
        page_map = {
            "home": 0,
            "project": 1,
        }

        if page_id in page_map:
            self.stack.setCurrentIndex(page_map[page_id])
            self._current_page = page_id
            self._update_nav_selection(page_map[page_id])

    def _update_nav_selection(self, index: int) -> None:
        """更新導航按鈕選中狀態"""
        page_ids = ["home", "project"]
        for i, page_id in enumerate(page_ids):
            btn = self.nav_buttons.get(page_id)
            if btn:
                btn.setChecked(i == index)

    def _on_import_action(self, format_type: str) -> None:
        """處理匯入動作（尚未實作）"""
        from PySide6.QtWidgets import QMessageBox
        msg = f"{format_type.upper()} 匯入功能尚未實作，將在後續版本提供。"
        QMessageBox.information(self, "提示", msg)

    def _on_txt_imported(self, book_info: dict) -> None:
        """處理 TXT 匯入結果，加入專案列表"""
        title = book_info.get("title", "未知標題")
        source = book_info.get("source", "")
        self.project_page.add_project(name=title, source=source, status="已匯入", progress="0%")
        self._navigate_to("project")

    def _on_epub_imported(self, book_info: dict) -> None:
        """處理 EPUB 匯入結果，加入專案列表"""
        title = book_info.get("title", "未知標題")
        source = book_info.get("source", "")
        chapters = book_info.get("chapters", 0)
        status = "已匯入" if book_info.get("status") == "success" else "部分匯入"
        self.project_page.add_project(name=title, source=source, status=status, progress="0%")
        self._navigate_to("project")

    def closeEvent(self, event) -> None:
        """關閉視窗確認"""
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            Strings.BTN_CLOSE,
            Strings.MSG_CONFIRM_CLOSE,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()
