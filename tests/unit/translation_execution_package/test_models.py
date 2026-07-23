from __future__ import annotations

import json
import re
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from core.book_preparation import BookPreparationProcessor
from core.translation_execution_package import (
    ExecutionPackageFinding,
    ExecutionSourceReference,
    TranslationExecutionPackageBuilder,
)


def _package(tmp_path: Path):
    text = "第一章\n" + "這是完整保留的小說內容。" * 180 + "\n第二章\n" + "另一段小說內容。" * 180
    path = tmp_path / "小說.txt"
    path.write_bytes(text.encode("utf-8"))
    preparation = BookPreparationProcessor().prepare(path)
    return TranslationExecutionPackageBuilder().build(preparation), text


def test_formal_models_and_all_collections_are_frozen_tuples(tmp_path: Path) -> None:
    package, _ = _package(tmp_path)
    unit = package.units[0]
    finding = package.findings[0]

    assert isinstance(package.units, tuple)
    assert isinstance(package.findings, tuple)
    assert isinstance(unit.section_indices, tuple)
    assert isinstance(package.source, ExecutionSourceReference)
    assert isinstance(finding, ExecutionPackageFinding)
    for target, attribute, value in (
        (package, "status", "blocked"),
        (unit, "status", "translated"),
        (package.source, "source_name", "changed.txt"),
        (finding, "message", "changed"),
    ):
        with pytest.raises(FrozenInstanceError):
            setattr(target, attribute, value)


def test_serialization_is_deterministic_detached_utf8_and_environment_free(
    tmp_path: Path,
) -> None:
    package, text = _package(tmp_path)
    first = package.to_dict()
    second = package.to_dict()
    encoded = package.to_json()

    assert first == second
    assert encoded == package.to_json()
    assert json.loads(encoded) == first
    assert "小說" in encoded and "\\u5c0f" not in encoded
    assert package.source.source_name == "小說.txt"
    assert str(tmp_path) not in encoded
    assert "datetime" not in encoded.lower()
    assert not re.search(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        encoded,
        re.IGNORECASE,
    )
    first["status"] = "changed"
    first["units"][0]["text"] = "changed"
    assert package.status != "changed"
    assert package.units[0].text != "changed"
    assert package.reconstruct_source_text() == text


def test_model_fingerprints_are_lowercase_sha256(tmp_path: Path) -> None:
    package, _ = _package(tmp_path)
    assert re.fullmatch(r"[0-9a-f]{64}", package.execution_package_fingerprint)
    assert all(
        re.fullmatch(r"[0-9a-f]{64}", unit.execution_unit_fingerprint)
        for unit in package.units
    )

