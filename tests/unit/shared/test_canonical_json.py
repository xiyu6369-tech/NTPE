from __future__ import annotations

import math
from pathlib import Path

import pytest

from core.shared.evidence.canonical_json import (
    canonical_json_bytes,
    canonical_json_text,
    read_json,
    write_canonical_json,
)


def test_canonical_json_is_sorted_compact_utf8_and_deterministic() -> None:
    first = {"繁體": "中文", "a": 1}
    second = {"a": 1, "繁體": "中文"}
    expected = '{"a":1,"繁體":"中文"}'
    assert canonical_json_text(first) == expected
    assert canonical_json_bytes(first) == canonical_json_bytes(second) == expected.encode("utf-8")
    assert not canonical_json_bytes(first).endswith(b"\n")


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_non_finite_numbers_are_rejected(value: float) -> None:
    with pytest.raises(ValueError):
        canonical_json_bytes({"value": value})


def test_unsupported_objects_are_not_coerced() -> None:
    with pytest.raises(TypeError):
        canonical_json_text({"path": Path("artifact.json")})


def test_atomic_write_and_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "證據.json"
    value = {"z": [3, 2, 1], "名稱": "測試"}
    write_canonical_json(path, value)
    assert path.read_bytes() == canonical_json_bytes(value)
    assert read_json(path) == value
    assert not list(tmp_path.glob(f".{path.name}.*.tmp"))


def test_failed_replace_preserves_existing_file_and_removes_temp(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import core.shared.evidence.canonical_json as module

    path = tmp_path / "report.json"
    path.write_bytes(b"original")

    def fail_replace(source: Path, destination: Path) -> None:
        raise OSError("injected replace failure")

    monkeypatch.setattr(module.os, "replace", fail_replace)
    with pytest.raises(OSError, match="injected"):
        write_canonical_json(path, {"new": True})
    assert path.read_bytes() == b"original"
    assert not list(tmp_path.glob(f".{path.name}.*.tmp"))

