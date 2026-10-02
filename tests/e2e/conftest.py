"""S9-07 Reader-First E2E shared fixtures.

Deterministic, offline, isolated: tmp NTPE_HOME, fake runtime, fake result
opener. Provider = 0, network = 0, real translation = 0.
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication

from core.reader_project.manager import ReaderProjectManager
from ui.translation_studio.pages.project_page import ProjectPage


@pytest.fixture(scope="session")
def qapp():
    return QApplication.instance() or QApplication(sys.argv)


class FakeTranslationRunner:
    """Records the options and lets the test drive callbacks deterministically."""

    instances: list["FakeTranslationRunner"] = []

    def __init__(self, options: Any, root_path: Path):
        self.options = options
        self.root_path = root_path
        self.started = False
        self._on_progress = None
        self._on_finished = None
        self._on_error = None
        FakeTranslationRunner.instances.append(self)

    @classmethod
    def last(cls) -> "FakeTranslationRunner | None":
        return cls.instances[-1] if cls.instances else None

    @classmethod
    def reset(cls) -> None:
        cls.instances = []

    def start(self, on_progress, on_finished, on_error) -> None:
        self.started = True
        self._on_progress = on_progress
        self._on_finished = on_finished
        self._on_error = on_error

    def emit_progress(self, payload: dict) -> None:
        self._on_progress(payload)

    def complete(self, result: dict) -> None:
        self._on_finished(result)

    def fail(self, error: str) -> None:
        self._on_error(error)

    def cancel(self, timeout: int = 5000) -> bool:
        return True

    def is_running(self) -> bool:
        return False

    def is_completed(self) -> bool:
        return True


class FakeResultOpener:
    """Records calls; never launches a real OS application."""

    def __init__(self, open_ok: bool = True, reveal_ok: bool = True):
        self.open_ok = open_ok
        self.reveal_ok = reveal_ok
        self.opened: list[str] = []
        self.revealed: list[str] = []

    def open_path(self, path) -> bool:
        self.opened.append(str(path))
        return self.open_ok

    def reveal_folder(self, path) -> bool:
        self.revealed.append(str(path))
        return self.reveal_ok


@pytest.fixture
def home(tmp_path: Path) -> Path:
    return tmp_path / "NTPE_HOME"


@pytest.fixture
def manager(home: Path) -> ReaderProjectManager:
    return ReaderProjectManager(home=home)


@pytest.fixture
def opener() -> FakeResultOpener:
    return FakeResultOpener()


@pytest.fixture
def page(qapp, manager, opener):
    FakeTranslationRunner.reset()
    p = ProjectPage()
    p.set_project_manager(manager)
    p.set_result_opener(opener)
    yield p
    p.close()


def make_txt(tmp_path: Path, name: str = "novel.txt", content: bytes | None = None) -> Path:
    path = tmp_path / name
    path.write_bytes(
        content if content is not None else "그는 문을 열었다. 바람이 불었다.\n".encode("utf-8")
    )
    return path


def make_epub(tmp_path: Path, name: str = "book.epub", title: str = "Test Book") -> Path:
    """Create a minimal deterministic EPUB3 fixture (2 chapters + 1 resource)."""
    epub_path = tmp_path / name
    with zipfile.ZipFile(epub_path, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
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
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>{title}</dc:title>
    <dc:creator>Test Author</dc:creator>
    <dc:language>en</dc:language>
    <dc:identifier id="bookid">urn:uuid:s9-07-fixture</dc:identifier>
  </metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
    <item id="ch2" href="ch2.xhtml" media-type="application/xhtml+xml"/>
    <item id="img" href="img.png" media-type="image/png"/>
  </manifest>
  <spine>
    <itemref idref="ch1" linear="yes"/>
    <itemref idref="ch2" linear="yes"/>
  </spine>
</package>""",
        )
        zf.writestr(
            "OEBPS/nav.xhtml",
            """<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
  <head><title>Navigation</title></head>
  <body><nav epub:type="toc"><ol>
    <li><a href="ch1.xhtml">Chapter One</a></li>
    <li><a href="ch2.xhtml">Chapter Two</a></li>
  </ol></nav></body>
</html>""",
        )
        zf.writestr(
            "OEBPS/ch1.xhtml",
            """<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Chapter One</title></head>
<body><h1>Chapter One</h1><p>This is the first paragraph of the book.</p>
<p>This is the second paragraph of the book.</p></body></html>""",
        )
        zf.writestr(
            "OEBPS/ch2.xhtml",
            """<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Chapter Two</title></head>
<body><h1>Chapter Two</h1><p>This is chapter two content of the book.</p></body></html>""",
        )
        zf.writestr("OEBPS/img.png", b"\x89PNG\r\n\x1a\n")
    return epub_path


def build_txt_book_info(source: Path, title: str = "Novel") -> dict:
    return {
        "title": title,
        "source": str(source),
        "format": "txt",
        "chars": len(source.read_bytes()),
        "encoding": "utf-8",
        "status": "ready",
        "warnings": [],
        "preview_text": source.read_text(encoding="utf-8", errors="replace"),
    }
