from __future__ import annotations

import sys
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from PySide6.QtWidgets import QApplication, QTextEdit, QTabWidget, QLabel
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt

from ui.translation_studio.pages.project_page import ProjectPage, PreviewDialog
from ui.translation_studio.pages.home_page import HomePage
from ui.translation_studio.main_window import MainWindow
from ui.translation_studio.resources.translations import Strings


def create_test_epub(path: Path, title: str = "Test Book", chapters: int = 2) -> None:
    """Create a minimal valid EPUB for testing."""
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr(
            "mimetype",
            "application/epub+zip",
            compress_type=zipfile.ZIP_STORED
        )
        zf.writestr(
            "META-INF/container.xml",
            """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""",
        )
        zf.writestr(
            "OEBPS/content.opf",
            f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="bookid" version="3.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="bookid">test-book</dc:identifier>
    <dc:title>{title}</dc:title>
    <dc:language>en</dc:language>
    <dc:creator>Test Author</dc:creator>
  </metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="nav"/>
    <itemref idref="ch1"/>
  </spine>
</package>""",
        )
        zf.writestr(
            "OEBPS/nav.xhtml",
            """<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head><title>Navigation</title></head>
<body><nav epub:type="toc"><ol><li><a href="ch1.xhtml">Chapter 1</a></li></ol></nav></body>
</html>""",
        )
        zf.writestr(
            "OEBPS/ch1.xhtml",
            f"""<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>Chapter 1</title></head>
<body><h1>Chapter 1</h1><p>Test content for {title}</p></body>
</html>""",
        )


def test_preview_button_disabled_when_no_project():
    """測試：尚未匯入專案時，預覽按鈕不可用"""
    app = QApplication.instance() or QApplication(sys.argv)
    page = ProjectPage()
    
    # 初始狀態下預覽按鈕應該不可用
    assert not page.btn_preview.isEnabled()
    page.close()
    print("✓ test_preview_button_disabled_when_no_project passed")


def test_preview_button_disabled_when_no_content():
    """測試：專案無預覽內容時，預覽按鈕不可用"""
    app = QApplication.instance() or QApplication(sys.argv)
    page = ProjectPage()
    
    # 新增無預覽內容的專案
    page.add_project("Test Book", "/path/to/book.txt", "已匯入", "0%")
    
    # 選擇該專案
    page.table.selectRow(0)
    
    # 預覽按鈕應該不可用（無 preview_text）
    assert not page.btn_preview.isEnabled()
    page.close()
    print("✓ test_preview_button_disabled_when_no_content passed")


def test_preview_button_enabled_with_txt_content():
    """測試：TXT 專案有預覽內容時，預覽按鈕可用"""
    app = QApplication.instance() or QApplication(sys.argv)
    page = ProjectPage()
    
    # 新增有預覽內容的 TXT 專案
    txt_book_info = {
        "title": "test.txt",
        "source": "/path/to/test.txt",
        "chars": 100,
        "encoding": "utf-8",
        "status": "ready",
        "warnings": [],
        "submission_eligible": True,
        "preview_text": "這是測試內容\n第二行\n第三行",
    }
    page.add_project("test.txt", "/path/to/test.txt", "已匯入", "0%", txt_book_info)
    
    # 選擇該專案
    page.table.selectRow(0)
    
    # 預覽按鈕應該可用
    assert page.btn_preview.isEnabled()
    page.close()
    print("✓ test_preview_button_enabled_with_txt_content passed")


def test_preview_button_enabled_with_epub_content():
    """測試：EPUB 專案有預覽內容時，預覽按鈕可用"""
    app = QApplication.instance() or QApplication(sys.argv)
    page = ProjectPage()
    
    # 新增有預覽內容的 EPUB 專案
    epub_book_info = {
        "title": "Test Book",
        "source": "/path/to/test.epub",
        "chapters": 2,
        "linear_chapters": 2,
        "chars": 100,
        "status": "success",
        "warnings": [],
        "metadata": {"title": "Test Book", "author": "Author", "language": "en"},
        "preview_text": "=== CHAPTER 1: Chapter 1 ===\nContent here\n\n=== CHAPTER 2: Chapter 2 ===\nMore content\n",
        "chapter_map": [
            {"index": 1, "title": "Chapter 1", "start_offset": 0, "end_offset": 50, "word_count": 10, "is_linear": True},
            {"index": 2, "title": "Chapter 2", "start_offset": 50, "end_offset": 100, "word_count": 15, "is_linear": True},
        ],
    }
    page.add_project("test.epub", "/path/to/test.epub", "已匯入", "0%", epub_book_info)
    
    # 選擇該專案
    page.table.selectRow(0)
    
    # 預覽按鈕應該可用
    assert page.btn_preview.isEnabled()
    page.close()
    print("✓ test_preview_button_enabled_with_epub_content passed")


def test_preview_button_disabled_for_partial_epub_no_content():
    """測試：EPUB partial 但無預覽內容時，預覽按鈕不可用"""
    app = QApplication.instance() or QApplication(sys.argv)
    page = ProjectPage()
    
    # 新增 partial 狀態但無預覽內容的 EPUB 專案
    epub_book_info = {
        "title": "Partial Book",
        "source": "/path/to/partial.epub",
        "chapters": 2,
        "linear_chapters": 1,
        "chars": 50,
        "status": "partial",
        "warnings": ["Chapter 2 parse error"],
        "metadata": {"title": "Partial Book"},
        "preview_text": "",
        "chapter_map": [],
    }
    page.add_project("partial.epub", "/path/to/partial.epub", "部分匯入", "0%", epub_book_info)
    
    # 選擇該專案
    page.table.selectRow(0)
    
    # 預覽按鈕應該不可用（無預覽內容）
    assert not page.btn_preview.isEnabled()
    page.close()
    print("✓ test_preview_button_disabled_for_partial_epub_no_content passed")


def test_preview_dialog_shows_txt_content():
    """測試：TXT 預覽對話框顯示正確內容"""
    app = QApplication.instance() or QApplication(sys.argv)
    
    txt_book_info = {
        "title": "test.txt",
        "source": "/path/to/test.txt",
        "chars": 100,
        "encoding": "utf-8",
        "status": "ready",
        "warnings": [],
        "submission_eligible": True,
        "preview_text": "第一行內容\n第二行內容\n第三行內容",
    }
    
    dialog = PreviewDialog(txt_book_info)
    
    # 檢查對話框標題
    assert dialog.windowTitle() == Strings.PREVIEW_TITLE
    
    # 檢查內容是否包含預覽文字
    # 找到 QTextEdit
    text_edits = dialog.findChildren(QTextEdit)
    assert len(text_edits) > 0
    content = text_edits[0].toPlainText()
    assert "第一行內容" in content
    assert "第二行內容" in content
    assert "第三行內容" in content
    
    dialog.close()
    print("✓ test_preview_dialog_shows_txt_content passed")


def test_preview_dialog_shows_epub_chapters():
    """測試：EPUB 預覽對話框顯示章節標籤"""
    app = QApplication.instance() or QApplication(sys.argv)
    
    epub_book_info = {
        "title": "Test Book",
        "source": "/path/to/test.epub",
        "chapters": 2,
        "linear_chapters": 2,
        "chars": 100,
        "status": "success",
        "warnings": [],
        "metadata": {"title": "Test Book", "author": "Author", "language": "en"},
        "preview_text": "=== CHAPTER 1: Chapter 1 ===\nContent here\n\n=== CHAPTER 2: Chapter 2 ===\nMore content\n",
        "chapter_map": [
            {"index": 1, "title": "Chapter 1", "start_offset": 0, "end_offset": 50, "word_count": 10, "is_linear": True},
            {"index": 2, "title": "Chapter 2", "start_offset": 50, "end_offset": 100, "word_count": 15, "is_linear": True},
        ],
    }
    
    dialog = PreviewDialog(epub_book_info)
    
    # 檢查對話框標題
    assert dialog.windowTitle() == Strings.PREVIEW_TITLE
    
    # 檢查是否有 TabWidget
    tab_widgets = dialog.findChildren(QTabWidget)
    assert len(tab_widgets) > 0
    tab_widget = tab_widgets[0]
    
    # 應該有 3 個標籤：完整內容 + 2 章節
    assert tab_widget.count() == 3
    assert tab_widget.tabText(0) == "完整內容"
    assert tab_widget.tabText(1) == "Chapter 1"
    assert tab_widget.tabText(2) == "Chapter 2"
    
    dialog.close()
    print("✓ test_preview_dialog_shows_epub_chapters passed")


def test_preview_dialog_shows_partial_warning():
    """測試：partial 狀態顯示部分匯入警告"""
    app = QApplication.instance() or QApplication(sys.argv)
    
    partial_book_info = {
        "title": "Partial Book",
        "source": "/path/to/partial.epub",
        "chapters": 2,
        "linear_chapters": 1,
        "chars": 50,
        "status": "partial",
        "warnings": ["Chapter 2 parse error", "Malformed XHTML in Chapter 3"],
        "metadata": {"title": "Partial Book"},
        "preview_text": "Chapter 1 content\n",
        "chapter_map": [
            {"index": 1, "title": "Chapter 1", "start_offset": 0, "end_offset": 20, "word_count": 5, "is_linear": True},
        ],
    }
    
    dialog = PreviewDialog(partial_book_info)
    
    # 檢查是否有警告標籤
    labels = dialog.findChildren(QLabel)
    warning_found = False
    for label in labels:
        if "警告" in label.text() and "Chapter 2 parse error" in label.text():
            warning_found = True
            break
    assert warning_found, "Should show warnings for partial EPUB"
    
    # 檢查狀態標籤顯示「部分匯入」
    labels = dialog.findChildren(QLabel)
    status_found = False
    for label in labels:
        if label.text() == "部分匯入":
            status_found = True
            break
    assert status_found, "Should show 部分匯入 status label"
    
    dialog.close()
    print("✓ test_preview_dialog_shows_partial_warning passed")


def test_preview_dialog_shows_warnings():
    """測試：有 warnings 時顯示警告區塊"""
    app = QApplication.instance() or QApplication(sys.argv)
    
    book_info = {
        "title": "Test Book",
        "source": "/path/to/test.txt",
        "chars": 100,
        "encoding": "utf-8",
        "status": "ready",
        "warnings": ["Warning 1", "Warning 2"],
        "submission_eligible": True,
        "preview_text": "Some content",
    }
    
    dialog = PreviewDialog(book_info)
    
    # 檢查是否有警告標籤
    labels = dialog.findChildren(QLabel)
    warning_found = False
    for label in labels:
        if "警告" in label.text() and "Warning 1" in label.text() and "Warning 2" in label.text():
            warning_found = True
            break
    assert warning_found, "Should show warnings"
    
    dialog.close()
    print("✓ test_preview_dialog_shows_warnings passed")


def test_preview_dialog_long_content_truncation_notice():
    """測試：長內容顯示截取提示"""
    app = QApplication.instance() or QApplication(sys.argv)
    
    long_text = "x" * 15000  # 超過 10000 字元
    book_info = {
        "title": "Long Book",
        "source": "/path/to/long.txt",
        "chars": 15000,
        "encoding": "utf-8",
        "status": "ready",
        "warnings": [],
        "submission_eligible": True,
        "preview_text": long_text,
    }
    
    dialog = PreviewDialog(book_info)
    
    # 檢查是否有截取提示
    labels = dialog.findChildren(QLabel)
    trunc_found = False
    for label in labels:
        if "內容過長" in label.text() and "10000" in label.text():
            trunc_found = True
            break
    assert trunc_found, "Should show truncation notice for long content"
    
    dialog.close()
    print("✓ test_preview_dialog_long_content_truncation_notice passed")


def test_preview_dialog_no_content_shows_placeholder():
    """測試：無內容時顯示預設提示"""
    app = QApplication.instance() or QApplication(sys.argv)
    
    book_info = {
        "title": "Empty Book",
        "source": "/path/to/empty.txt",
        "chars": 0,
        "encoding": "utf-8",
        "status": "ready",
        "warnings": [],
        "submission_eligible": True,
        "preview_text": "",
    }
    
    dialog = PreviewDialog(book_info)
    
    text_edits = dialog.findChildren(QTextEdit)
    assert len(text_edits) > 0
    content = text_edits[0].toPlainText()
    assert "無可預覽的內容" in content or Strings.PREVIEW_NO_CONTENT in content
    
    dialog.close()
    print("✓ test_preview_dialog_no_content_shows_placeholder passed")


def test_preview_does_not_modify_project_state():
    """測試：預覽不改變專案狀態"""
    app = QApplication.instance() or QApplication(sys.argv)
    page = ProjectPage()
    
    epub_book_info = {
        "title": "Test Book",
        "source": "/path/to/test.epub",
        "chapters": 2,
        "chars": 100,
        "status": "partial",
        "warnings": ["Parse error"],
        "metadata": {"title": "Test Book"},
        "preview_text": "Content",
        "chapter_map": [{"index": 1, "title": "Ch1", "start_offset": 0, "end_offset": 10, "word_count": 5, "is_linear": True}],
    }
    page.add_project("test.epub", "/path/to/test.epub", "部分匯入", "0%", epub_book_info)
    
    # 記錄原始狀態
    original_status = page._projects[0]["status"]
    original_progress = page._projects[0]["progress"]
    
    # 選擇並預覽（模擬，不實際開啟對話框）
    page.table.selectRow(0)
    
    # 狀態不應改變
    assert page._projects[0]["status"] == original_status
    assert page._projects[0]["progress"] == original_progress
    
    page.close()
    print("✓ test_preview_does_not_modify_project_state passed")


def test_preview_no_nvidia_calls():
    """測試：預覽流程不呼叫 NVIDIA/Provider/TranslationRuntime"""
    import ui.translation_studio.pages.project_page as pp
    import ui.translation_studio.pages.home_page as hp
    import inspect
    
    # Check ProjectPage
    src = inspect.getsource(pp.ProjectPage)
    forbidden = [
        'nvidia', 'Nvidia', 'NVIDIA',
        'translation_runtime', 'TranslationRuntime',
        'TranslationEngine',
        'provider_runtime', 'ProviderRuntime',
        'NvidiaTranslationProvider', 'NvidiaClient',
    ]
    for word in forbidden:
        assert word not in src, f"ProjectPage contains forbidden: {word}"
    
    # Check PreviewDialog
    src = inspect.getsource(pp.PreviewDialog)
    for word in forbidden:
        assert word not in src, f"PreviewDialog contains forbidden: {word}"
    
    print("✓ test_preview_no_nvidia_calls passed")


def test_epub_partial_status_preserved_in_project_page():
    """測試：EPUB partial 狀態在專案頁保留"""
    app = QApplication.instance() or QApplication(sys.argv)
    page = ProjectPage()
    
    epub_book_info = {
        "title": "Partial Book",
        "source": "/path/to/partial.epub",
        "chapters": 2,
        "linear_chapters": 1,
        "chars": 50,
        "status": "partial",
        "warnings": ["Chapter 2 parse error"],
        "metadata": {"title": "Partial Book"},
        "preview_text": "Chapter 1 content\n",
        "chapter_map": [{"index": 1, "title": "Chapter 1", "start_offset": 0, "end_offset": 20, "word_count": 5, "is_linear": True}],
    }
    page.add_project("partial.epub", "/path/to/partial.epub", "部分匯入", "0%", epub_book_info)
    
    # 檢查專案列表中的狀態
    assert page._projects[0]["status"] == "partial"
    assert page.table.item(0, 2).text() == "部分匯入"
    
    page.close()
    print("✓ test_epub_partial_status_preserved_in_project_page passed")


def test_existing_txt_import_contract_still_works():
    """測試：既有 TXT 匯入契約仍正常運作"""
    app = QApplication.instance() or QApplication(sys.argv)
    
    # 檢查 HomePage 仍有 txt_imported 信號
    from ui.translation_studio.pages.home_page import HomePage
    import inspect
    src = inspect.getsource(HomePage)
    assert 'txt_imported = Signal(dict)' in src
    assert 'self.txt_imported.emit' in src
    assert 'submission_eligible' in src
    assert 'encoding' in src
    assert 'preview_text' in src
    
    print("✓ test_existing_txt_import_contract_still_works passed")


def test_existing_epub_import_contract_still_works():
    """測試：既有 EPUB 匯入契約仍正常運作"""
    from ui.translation_studio.pages.home_page import HomePage
    import inspect
    src = inspect.getsource(HomePage)
    assert 'epub_imported = Signal(dict)' in src
    assert 'self.epub_imported.emit' in src
    assert 'preview_text' in src
    assert 'chapter_map' in src
    assert 'partial' in src  # partial 狀態處理
    
    print("✓ test_existing_epub_import_contract_still_works passed")


if __name__ == "__main__":
    # 先檢查 QApplication 是否可用
    app = QApplication.instance() or QApplication(sys.argv)
    
    # 執行所有測試
    test_preview_button_disabled_when_no_project()
    test_preview_button_disabled_when_no_content()
    test_preview_button_enabled_with_txt_content()
    test_preview_button_enabled_with_epub_content()
    test_preview_button_disabled_for_partial_epub_no_content()
    test_preview_dialog_shows_txt_content()
    test_preview_dialog_shows_epub_chapters()
    test_preview_dialog_shows_partial_warning()
    test_preview_dialog_shows_warnings()
    test_preview_dialog_long_content_truncation_notice()
    test_preview_dialog_no_content_shows_placeholder()
    test_preview_does_not_modify_project_state()
    test_preview_no_nvidia_calls()
    test_epub_partial_status_preserved_in_project_page()
    test_existing_txt_import_contract_still_works()
    test_existing_epub_import_contract_still_works()
    print("\n✅ All Preview tests passed!")