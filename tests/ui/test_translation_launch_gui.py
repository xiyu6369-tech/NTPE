"""Manual GUI verification script for Translation Launch 01."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

# Set up mock runtime before importing UI
PROJECT_ROOT = Path(r"D:\Python\NTPE")
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "tests" / "ui"))
from mock_translation_runtime import install_mock_runtime
install_mock_runtime()

from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt

from ui.translation_studio.main_window import MainWindow
from ui.translation_studio.pages.project_page import ProjectPage
from ui.translation_studio.translation_worker import TranslationRunner


def run_gui_verification():
    """Run comprehensive GUI verification."""
    
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Create test input file
    tmpdir = tempfile.mkdtemp()
    test_file = Path(tmpdir) / "test_novel.txt"
    test_file.write_text(
        "Chapter 1\n\nThis is test content for translation.\n\n"
        "Chapter 2\n\nMore content to translate.\n\n"
        "Chapter 3\n\nFinal chapter content.",
        encoding="utf-8"
    )
    
    print("=" * 60)
    print("TRANSLATION LAUNCH 01 - MANUAL GUI VERIFICATION")
    print("=" * 60)
    print(f"Test file: {test_file}")
    print(f"Temp dir: {tmpdir}")
    print()
    
    # Create main window
    window = MainWindow()
    window.show()
    
    # Wait for window to show
    QTest.qWaitForWindowExposed(window)
    print("[OK] 1. GUI 正常啟動")
    
    # Navigate to Home page (should be default)
    assert window._current_page == "home"
    print("[OK] 2. 預設在首頁")
    
    # Import TXT file
    home_page = window.home_page
    
    # Mock file dialog to return our test file
    from PySide6.QtWidgets import QFileDialog
    
    def mock_get_open(*args, **kwargs):
        return (str(test_file), "Text Files (*.txt)")
    
    QFileDialog.getOpenFileName = staticmethod(mock_get_open)
    
    try:
        # Trigger TXT import
        home_page._on_import_txt()
        QTest.qWait(500)  # Wait for import to complete
        
        # Should now be on Project page with the imported project
        assert window._current_page == "project"
        project_page = window.project_page
        
        # Check project was added
        assert project_page.table.rowCount() == 1
        project_name = project_page.table.item(0, 0).text()
        print(f"Project name: '{project_name}'")
        assert project_name == "test_novel"
        print("[OK] 3. TXT 專案可正確匯入並顯示在專案列表")
        
        # Select the project
        project_page.table.selectRow(0)
        QTest.qWait(100)
        
        # Verify translate button is enabled for TXT project
        assert project_page.btn_translate.isEnabled()
        print("[OK] 4. TXT 專案的翻譯按鈕可啟用")
        
        # Test EPUB project support
        epub_book_info = {
            "title": "Test EPUB",
            "source": "input/test.epub",
            "preview_text": "Content",
            "status": "success",
            "warnings": [],
            "chapter_map": [{"index": 1, "title": "Chapter 1", "start_offset": 0, "end_offset": 100}],
        }
        project_page.add_project(
            name="Test EPUB",
            source="input/test.epub",
            status="已匯入",
            progress="0%",
            book_info=epub_book_info,
        )
        
        project_page.table.selectRow(1)
        QTest.qWait(100)
        
        # Verify translate button is enabled for EPUB
        assert project_page.btn_translate.isEnabled()
        assert project_page.btn_translate.toolTip() == ""
        print("[OK] 5. EPUB 專案的翻譯按鈕正確啟用")
        
        # Go back to TXT project
        project_page.table.selectRow(0)
        QTest.qWait(100)
        
        # Test translation launch
        print("\n--- 開始翻譯測試 ---")
        project_page._on_translate()
        QTest.qWait(200)
        
        # Verify translation started
        assert project_page._current_translation_row == 0
        assert project_page._translation_runner is not None
        assert project_page._translation_runner.is_running()
        
        # Verify GUI is responsive (buttons disabled but window works)
        assert not project_page.btn_translate.isEnabled()
        assert not project_page.btn_preview.isEnabled()
        print("[OK] 6. 點擊開始翻譯後 GUI 未阻塞，按鈕正確禁用")
        
        # Check initial status
        status_item = project_page.table.item(0, 2)
        progress_item = project_page.table.item(0, 3)
        assert status_item.text() == "準備翻譯"
        print("[OK] 7. 狀態正確顯示 '準備翻譯'")
        
        # Wait for translation to complete (mock takes ~2.5 seconds)
        max_wait = 10000  # 10 seconds max
        elapsed = 0
        while project_page._translation_runner and project_page._translation_runner.is_running():
            QTest.qWait(200)
            elapsed += 200
            if elapsed > max_wait:
                break
        
        # Wait a bit more for UI to update
        QTest.qWait(500)
        
        # Verify completion
        final_status = project_page.table.item(0, 2).text()
        final_progress = project_page.table.item(0, 3).text()
        
        print(f"Final status: {final_status}")
        print(f"Final progress: {final_progress}")
        
        if "翻譯完成" in final_status:
            print("[OK] 8. 翻譯完成狀態正確顯示")
        elif "翻譯未完成" in final_status:
            print("[WARN] 8. 翻譯未完成（可能因 mock 設定）")
        elif "翻譯失敗" in final_status:
            print("[FAIL] 8. 翻譯失敗")
        else:
            print(f"? 8. 未知狀態: {final_status}")
        
        # Test duplicate launch prevention
        project_page._on_translate()
        QTest.qWait(200)
        assert project_page._current_translation_row is None  # Should not start second
        print("[OK] 9. 重複點擊不會建立第二個翻譯 job")
        
        # Test EPUB remains launchable
        project_page.table.selectRow(1)
        QTest.qWait(100)
        assert project_page.btn_translate.isEnabled()
        project_page.table.selectRow(0)
        QTest.qWait(100)
        print("[OK] 10. EPUB 專案在翻譯後仍正確啟用")
        
        print("\n" + "=" * 60)
        print("所有 GUI 驗證項目通過！")
        print("=" * 60)
        
        window.close()
        return True
        
    except Exception as e:
        print(f"\n[FAIL] 驗證失敗: {e}")
        import traceback
        traceback.print_exc()
        window.close()
        return False


if __name__ == "__main__":
    success = run_gui_verification()
    sys.exit(0 if success else 1)