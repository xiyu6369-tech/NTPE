from __future__ import annotations
import socket

import pytest

from core.literary import normalize_literary_style
from tests.semantic_guard_invariants import assert_ambiguous_reply_semantics


SOURCE_TRANSLATION = (
    "伊萊輕笑著說：「當然。」說完便轉身離去，"
    "留下了鄭泰義一個簡短的回答。"
)


def test_frozen_ter_v16_reply_semantics_are_preserved_in_one_pass():
    normalized = normalize_literary_style(SOURCE_TRANSLATION)

    assert_ambiguous_reply_semantics(normalized)
    assert "留下了鄭泰義一個" not in normalized


def test_normalization_is_idempotent_for_the_ter_v16_regression():
    normalized = normalize_literary_style(SOURCE_TRANSLATION)

    assert normalize_literary_style(normalized) == normalized


def test_whitespace_and_newlines_do_not_change_the_semantic_verdict():
    assert_ambiguous_reply_semantics(
        "\n 伊萊輕笑著只答了一句\n「當然」，便轉身離去。 "
    )


@pytest.mark.parametrize(
    "candidate",
    (
        "伊萊輕笑著便轉身離去。",
        "輕笑著只答了一句「當然」，便轉身離去。",
        "伊萊輕笑著「當然」，便轉身離去。",
        "伊萊輕笑著沒有只答了一句「當然」，便轉身離去。",
        "伊萊輕笑著只答了一句「當然，也許」，便轉身離去。",
        "伊萊輕笑著只答了一句「也許」，便轉身離去。",
        "伊萊輕笑著只答了一句「當然，便轉身離去。",
    ),
)
def test_semantic_loss_quote_drift_and_unmatched_quotes_are_rejected(candidate):
    with pytest.raises(AssertionError):
        assert_ambiguous_reply_semantics(candidate)


def test_normalization_never_opens_a_network_socket(monkeypatch):
    def reject_network(*args, **kwargs):
        raise AssertionError("network access is forbidden")

    monkeypatch.setattr(socket, "socket", reject_network)
    normalized = normalize_literary_style(SOURCE_TRANSLATION)

    assert_ambiguous_reply_semantics(normalized)
