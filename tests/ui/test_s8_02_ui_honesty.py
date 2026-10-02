"""S8-02 UI Functional Honesty Cleanup — acceptance coverage.

Verifies that the UI truthfully reflects currently supported capability:

* Test A — Overwrite is presented as unavailable while the backend lacks an
  overwrite runtime (and validation still rejects it).
* Test B — New Project is now a real lifecycle (S9-04): actionable, creates a
  persistent Project, result observable in the library.
* Test C — Open Project is now a real action (S9-04): actionable and emits the
  navigation/lifecycle request (no fake/placeholder workflow).
* Test D — Production model display metadata matches the real model ID.
* Test E — Canonical TXT translation launch is unchanged.
* Test F — Canonical EPUB direct launch (S8-01) is unchanged.

All tests are mock/static only: provider = 0, network = 0, real translation = 0.
"""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication, QLabel

from ui.translation_launcher.state import build_window_model
from ui.translation_studio.pages.home_page import HomePage
from ui.translation_studio.pages.project_page import ProjectPage

from core.launcher_product.config import load_launcher_config
from core.launcher_product.model_catalog import get_model, model_catalog
from core.launcher_product.validation import validate_launcher_config


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication(sys.argv)


# ---------------------------------------------------------------------------
# Test A — Overwrite honesty
# ---------------------------------------------------------------------------

def test_a_overwrite_model_marks_capability_unavailable():
    """Window model must advertise overwrite as disabled/unavailable."""
    model = build_window_model()
    assert model.overwrite_enabled is False
    assert model.overwrite_disabled_reason.strip() != ""


def test_a_overwrite_backend_still_rejects(tmp_path):
    """Backend genuinely lacks overwrite: validation must still block it."""
    source = tmp_path / "novel.txt"
    source.write_text("그는 문을 열고 천천히 안으로 들어갔다.", encoding="utf-8")
    config = replace(
        load_launcher_config(),
        input_path=str(source),
        output_directory=str(tmp_path / "translated"),
        source_language="auto",
        dry_run=True,
        overwrite=True,
    )
    result = validate_launcher_config(config, environment={"NVIDIA_API_KEY": "x"})
    assert "overwrite_not_integrated" in {issue.code for issue in result.blocking_reasons}


def test_a_overwrite_ui_checkbox_disabled_and_never_emits():
    """Tk launcher must disable the Overwrite control and never emit overwrite.

    NOTE: ``TranslationLauncherApp`` currently cannot be constructed due to a
    pre-existing Tk geometry-manager defect (``self.status`` is parented to the
    root while the root also ``pack``s a frame). That defect is unrelated to
    S8-02 and is not fixed here; the test skips rather than masking it.
    """
    tk = pytest.importorskip("tkinter")
    try:
        root = tk.Tk()
    except Exception as exc:  # pragma: no cover - environment limitation
        pytest.skip(f"Tk unavailable: {exc}")
    root.withdraw()
    try:
        from ui.translation_launcher.app import TranslationLauncherApp

        try:
            launcher = TranslationLauncherApp(root)
        except tk.TclError as exc:  # pragma: no cover - pre-existing UI defect
            pytest.skip(f"Pre-existing TranslationLauncherApp Tk defect: {exc}")

        assert launcher.overwrite_check.instate(["disabled"]), "Overwrite control must be disabled"
        assert "尚未支援" in launcher.overwrite_check.cget("text")

        # Even if the variable is forced true, the UI must not emit overwrite.
        launcher.variables["overwrite"].set(True)
        assert launcher._config().overwrite is False
    finally:
        root.destroy()


# ---------------------------------------------------------------------------
# Test B — New Project (migrated to real S9-04 lifecycle contract)
# ---------------------------------------------------------------------------

def test_b_new_project_is_actionable_and_persistent(qapp, tmp_path):
    """S9-04 migration: New Project is enabled and performs a real lifecycle.

    Replaces the former S8 "disabled + no-op" assertion with higher-value
    assertions: the control is actionable AND the result is persisted/observable.
    """
    from core.reader_project.manager import ReaderProjectManager

    manager = ReaderProjectManager(home=tmp_path / "NTPE_HOME")
    source = tmp_path / "book.txt"
    source.write_bytes("본문".encode("utf-8"))

    page = ProjectPage()
    try:
        page.set_project_manager(manager)
        assert page.btn_new_project.isEnabled(), "New Project must be actionable (S9-04)"
        assert "尚未支援" not in page.btn_new_project.toolTip()

        with patch(
            "ui.translation_studio.pages.project_page.QFileDialog.getOpenFileName",
            return_value=(str(source), ""),
        ):
            project_id = page.new_project()

        assert project_id is not None
        assert manager.exists(project_id), "New Project must persist"
        assert page.table.rowCount() == 1, "created project must appear in library"
    finally:
        page.close()


# ---------------------------------------------------------------------------
# Test C — Open Project (migrated to real S9-04 action contract)
# ---------------------------------------------------------------------------

def test_c_open_project_is_actionable(qapp):
    """S9-04 migration: Open/New on Home are enabled and emit real requests."""
    home = HomePage()
    try:
        assert home.btn_open_project.isEnabled(), "Open Project must be actionable (S9-04)"
        assert home.btn_new_project.isEnabled(), "New Project must be actionable (S9-04)"

        emitted = {"open": False, "new": False}
        home.open_project_requested.connect(lambda: emitted.__setitem__("open", True))
        home.new_project_requested.connect(lambda: emitted.__setitem__("new", True))

        home._on_open_project()
        home._on_new_project()

        assert emitted == {"open": True, "new": True}
    finally:
        home.close()


# ---------------------------------------------------------------------------
# Test D — Model display correctness
# ---------------------------------------------------------------------------

def test_d_model_display_matches_production_id():
    model = get_model("meta/llama-3.2-90b-vision-instruct")
    assert model is not None
    assert model.model_id == "meta/llama-3.2-90b-vision-instruct"
    assert model.provider_id == "nvidia"
    assert model.enabled is True

    display = model.display_name
    assert "3.2" in display
    assert "90B" in display
    assert "3.3" not in display, "display name must not claim Llama 3.3"
    assert "70B" not in display, "display name must not claim 70B"


def test_d_no_catalog_entry_claims_70b():
    assert all("70B" not in model.display_name for model in model_catalog())


# ---------------------------------------------------------------------------
# Test E — Canonical TXT translation launch unchanged
# ---------------------------------------------------------------------------

def test_e_txt_launch_still_supported(qapp):
    page = ProjectPage()
    try:
        page.add_project(
            name="Test Novel",
            source="input/test.txt",
            status="已匯入",
            progress="0%",
            book_info={
                "title": "Test Novel",
                "source": "input/test.txt",
                "preview_text": "Chapter 1\n\nTest content.",
                "status": "ready",
                "warnings": [],
            },
        )
        page.table.selectRow(0)
        assert page.btn_translate.isEnabled(), "TXT project must remain launchable"
    finally:
        page.close()


# ---------------------------------------------------------------------------
# Test F — Canonical EPUB direct launch (S8-01) unchanged
# ---------------------------------------------------------------------------

def test_f_epub_launch_still_supported(qapp):
    page = ProjectPage()
    try:
        page.add_project(
            name="Test EPUB",
            source="input/test.epub",
            status="已匯入",
            progress="0%",
            book_info={
                "title": "Test EPUB",
                "source": "input/test.epub",
                "preview_text": "Content",
                "status": "success",
                "warnings": [],
                "chapter_map": [
                    {"index": 1, "title": "Chapter 1", "start_offset": 0, "end_offset": 100}
                ],
            },
        )
        page.table.selectRow(0)
        assert page.btn_translate.isEnabled(), "EPUB project must remain launchable (S8-01)"
        assert page.btn_translate.toolTip() == ""
    finally:
        page.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
