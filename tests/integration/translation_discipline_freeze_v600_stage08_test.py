from __future__ import annotations

import json
from pathlib import Path

from core.translation_discipline import (
    DISCIPLINE_FREEZE_VERSION,
    DISCIPLINE_FROZEN_STAGES,
    build_translation_discipline_freeze,
)


def test_translation_discipline_freeze_contract() -> None:
    root = Path(__file__).resolve().parents[2]
    path = root / "manifests" / "te_v600_stage08_translation_discipline_freeze_manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    freeze = build_translation_discipline_freeze()
    assert freeze.version == DISCIPLINE_FREEZE_VERSION
    assert freeze.frozen is True
    assert freeze.stages == DISCIPLINE_FROZEN_STAGES
    assert manifest["frozen"] is True
    assert manifest["version"] == freeze.version
    assert tuple(manifest["stages"]) == freeze.stages
    assert manifest["compatibility"]["provider_calls_added"] == 0
    assert manifest["compatibility"]["nvidia_rpm_ceiling"] == 40
