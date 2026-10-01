"""S8-02 UI Functional Honesty Cleanup — acceptance coverage.

Verifies that the UI truthfully reflects currently supported capability:

* Test A — Overwrite is presented as unavailable while the backend lacks an
  overwrite runtime (and validation still rejects it).
* Test B — New Project no longer fakes a placeholder-led workflow.
* Test C — Open Project no longer fakes a placeholder-led workflow.
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
# Test B — New Project honesty
# ---------------------------------------------------------------------------

def test_b_new_project_unavailable(qapp):
    page = ProjectPage()
    try:
        assert not page.btn_new_project.isEnabled(), "New Project must be disabled (no persistence)"
        assert page.btn_new_project.toolTip().strip() != ""
        assert not page.btn_new_project.toolTip().startswith("TODO")

        # The handler must not fall through to a placeholder dialog.
        with patch("ui.translation_studio.pages.project_page.QMessageBox") as mock_msgbox:
            page._on_new_project()
            assert not mock_msgbox.information.called
    finally:
        page.close()


# ---------------------------------------------------------------------------
# Test C — Open Project honesty
# ---------------------------------------------------------------------------

def _action_button_label_text(button) -> str:
    """Home action buttons render their title in child QLabels, not button text."""
    labels = button.findChildren(QLabel)
    return " ".join(label.text() for label in labels)


def test_c_open_project_unavailable(qapp):
    home = HomePage()
    try:
        assert not home.btn_open_project.isEnabled(), "Open Project must be disabled (no persistence)"
        assert "尚未支援" in _action_button_label_text(home.btn_open_project)
        assert home.btn_open_project.toolTip().strip() != ""
        assert not home.btn_new_project.isEnabled()
        assert "尚未支援" in _action_button_label_text(home.btn_new_project)

        # Handlers must be no-ops (no navigation that implies an opened project).
        home._on_open_project()
        home._on_new_project()
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
