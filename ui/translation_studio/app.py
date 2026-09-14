from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from .main_window import MainWindow


def run() -> int:
    """啟動 NTPE 翻譯工作室 UI Shell"""
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("NTPE Translation Studio")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("NTPE")
    
    # 設定預設字型
    font = QFont()
    font.setFamily("Microsoft JhengHei")
    font.setPointSize(10)
    app.setFont(font)
    
    window = MainWindow()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(run())