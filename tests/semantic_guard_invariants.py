from __future__ import annotations

import re


_ONLY_REPLY_PATTERN = re.compile(
    r"伊萊[^。]{0,20}只(?:答了一句|說了句)「當然」"
)


def assert_ambiguous_reply_semantics(text: str) -> None:
    """Assert the frozen TER v1.6 short-reply semantic invariant."""
    compact = re.sub(r"\s+", "", text or "")
    assert compact.count("「") == compact.count("」"), "unbalanced corner quotes"
    quoted_replies = re.findall(r"「([^」]*)」", compact)
    assert quoted_replies == ["當然"], "quoted reply content changed or expanded"
    assert "伊萊" in compact, "reply subject was dropped"
    assert _ONLY_REPLY_PATTERN.search(compact), "only-replied predicate was dropped"
    reply_clause = compact[: compact.find("」") + 1]
    assert not any(mark in reply_clause for mark in ("不", "沒", "未")), (
        "negation was introduced into the reply"
    )
