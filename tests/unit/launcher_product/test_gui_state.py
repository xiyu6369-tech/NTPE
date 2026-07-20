from __future__ import annotations

import pytest

from ui.translation_launcher.controller import LauncherController
from ui.translation_launcher.state import build_window_model


def test_window_model_initializes_with_start_disabled() -> None:
    model = build_window_model()
    assert model.validate_enabled is True
    assert model.preview_enabled is True
    assert model.start_enabled is False
    assert model.start_disabled_reason == "Translation execution is not enabled in Stage 1."


def test_controller_never_starts_translation() -> None:
    with pytest.raises(RuntimeError, match="not enabled"):
        LauncherController.start_translation()
