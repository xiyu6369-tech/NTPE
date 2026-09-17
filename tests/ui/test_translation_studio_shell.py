from __future__ import annotations

import sys
from PySide6.QtWidgets import QApplication, QLabel, QPushButton
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt

from ui.translation_studio.main_window import MainWindow
from ui.translation_studio.pages.home_page import HomePage
from ui.translation_studio.pages.project_page import ProjectPage
from ui.translation_studio.resources.translations import Strings


def test_application_creation():
    """測試應用程式可以建立"""
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    assert window is not None
    assert window.windowTitle() == Strings.APP_TITLE
    window.close()
    print("✓ test_application_creation passed")


def test_main_window_title():
    """測試主視窗標題為繁體中文"""
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    title = window.windowTitle()
    assert title == "NTPE 翻譯工作室"
    assert "Translation" not in title
    assert "Studio" not in title
    window.close()
    print("✓ test_main_window_title passed")


def test_home_page_chinese_labels():
    """測試首頁所有標籤為繁體中文"""
    app = QApplication.instance() or QApplication(sys.argv)
    home = HomePage()

    # 找到所有 QLabel 和 QPushButton
    labels = home.findChildren(QLabel)
    buttons = home.findChildren(QPushButton)

    # 合併所有文字
    all_text = " ".join([w.text() for w in labels] + [w.text() for w in buttons])

    # 檢查關鍵繁體中文文字存在
    assert "NTPE 翻譯工作室" in all_text
    assert "歡迎使用" in all_text
    assert "匯入 TXT" in all_text
    assert "匯入 EPUB" in all_text
    assert "新增專案" in all_text
    assert "開啟專案" in all_text

    # 確保無英文主要標籤
    forbidden_en = ["Import", "Export", "Configure", "Preview", "Translate", "Retry", "Settings"]
    for word in forbidden_en:
        assert word not in all_text, f"Found forbidden English label: {word}"

    home.close()
    print("✓ test_home_page_chinese_labels passed")


def test_navigation_home_to_project():
    """測試首頁導航至專案頁"""
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    window.show()

    # 初始應在首頁
    assert window.stack.currentIndex() == 0

    # 點擊專案導航按鈕
    project_btn = window.nav_buttons["project"]
    QTest.mouseClick(project_btn, Qt.MouseButton.LeftButton)

    # 應切換到專案頁
    assert window.stack.currentIndex() == 1
    assert window._current_page == "project"

    window.close()
    print("✓ test_navigation_home_to_project passed")


def test_navigation_project_to_home():
    """測試專案頁返回首頁"""
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    window.show()

    # 先切到專案頁
    window._navigate_to("project")
    assert window.stack.currentIndex() == 1

    # 點擊首頁導航按鈕
    home_btn = window.nav_buttons["home"]
    QTest.mouseClick(home_btn, Qt.MouseButton.LeftButton)

    # 應切回首頁
    assert window.stack.currentIndex() == 0
    assert window._current_page == "home"

    window.close()
    print("✓ test_navigation_project_to_home passed")


def test_lifecycle():
    """測試應用程式生命週期：建立 -> 顯示 -> 關閉"""
    app = QApplication.instance() or QApplication(sys.argv)

    # 建立
    window = MainWindow()
    assert window is not None

    # 顯示
    window.show()
    assert window.isVisible()

    # 關閉
    window.close()
    assert not window.isVisible()

    print("✓ test_lifecycle passed")


def test_no_nvidia_import():
    """測試 UI 不會匯入 NVIDIA 相關模組"""
    # 檢查 ui.translation_studio 模組不匯入 production 相關模組
    import ui.translation_studio.app as app_module
    import ui.translation_studio.main_window as mw_module
    import ui.translation_studio.pages.home_page as hp_module
    import ui.translation_studio.pages.project_page as pp_module

    modules = [app_module, mw_module, hp_module, pp_module]

    import re
    for mod in modules:
        source_path = mod.__file__
        if source_path and source_path.endswith('.py'):
            try:
                with open(source_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 不應包含 NVIDIA 相關匯入（檢查實際 import 陳述式，非子字串）
                forbidden_imports = [
                    r'import\s+nvidia\b',
                    r'from\s+nvidia\b',
                    r'import\s+Nvidia\b',
                    r'from\s+Nvidia\b',
                    r'import\s+NVIDIA\b',
                    r'from\s+NVIDIA\b',
                    r'from\s+core\.translation_engine\b',
                    r'import\s+core\.translation_engine\b',
                    r'from\s+core\.translation_engine\.translation_engine\b',
                    r'from\s+core\.translation_engine\.provider_runtime\b',
                    r'from\s+core\.ai_provider\b',
                    r'from\s+core\.translation_engine\.nvidia_client\b',
                ]
                for pattern in forbidden_imports:
                    assert not re.search(pattern, content), f"Module {mod.__name__} has forbidden import matching: {pattern}"

                # 允許 canonical runtime import（lts.txt_translation_runtime）
                # 這是正確的架構邊界
            except (OSError, IOError):
                pass  # 跳過無法讀取的模組

    print("✓ test_no_nvidia_import passed")


def test_strings_localization():
    """測試字串資源為繁體中文"""
    # 檢查關鍵字串
    from ui.translation_studio.resources.translations import Strings, EN_TO_ZH
    assert Strings.APP_TITLE == "NTPE 翻譯工作室"
    assert Strings.NAV_HOME == "首頁"
    assert Strings.NAV_PROJECT == "專案"
    assert Strings.HOME_ACTION_IMPORT_TXT == "匯入 TXT"
    assert Strings.HOME_ACTION_IMPORT_EPUB == "匯入 EPUB"
    assert Strings.BTN_BACK == "返回"
    assert Strings.BTN_CLOSE == "關閉"
    assert Strings.PROJECT_TITLE == "專案管理"

    # 檢查 EN_TO_ZH 對照表（模組層級變數）
    assert EN_TO_ZH["Import"] == "匯入"
    assert EN_TO_ZH["Export"] == "匯出"
    assert EN_TO_ZH["Translate"] == "翻譯"
    assert EN_TO_ZH["Settings"] == "設定"

    print("✓ test_strings_localization passed")


if __name__ == "__main__":
    # 執行所有測試
    test_application_creation()
    test_main_window_title()
    test_home_page_chinese_labels()
    test_navigation_home_to_project()
    test_navigation_project_to_home()
    test_lifecycle()
    test_no_nvidia_import()
    test_strings_localization()
    print("\n✅ All UI tests passed!")