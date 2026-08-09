"""Traditional Chinese Unicode variant normalization for entity consistency.

This module provides variant-aware string normalization for comparison purposes ONLY.
It does NOT modify the original translation output or knowledge base entries.

The normalization maps CJK Compatibility Ideographs and other known Traditional Chinese
variants to their standard forms for consistent entity matching.
"""

from __future__ import annotations

# Variant mapping: maps variant codepoints to standard codepoints
# Source: Unicode CJK Compatibility Ideographs + known Traditional Chinese variants
_VARIANT_TO_STANDARD: dict[int, int] = {
    # 鄭 (U+9109) variants
    0x912D: 0x9109,  # CJK Compatibility Ideograph variant
    # Add more mappings as discovered
    # Format: variant_codepoint: standard_codepoint
}

# Reverse mapping for reference (not used in normalization)
_STANDARD_TO_VARIANTS: dict[int, list[int]] = {}
for var, std in _VARIANT_TO_STANDARD.items():
    _STANDARD_TO_VARIANTS.setdefault(std, []).append(var)


def _normalize_char(ch: str) -> str:
    """Normalize a single character to its standard form."""
    cp = ord(ch)
    if cp in _VARIANT_TO_STANDARD:
        return chr(_VARIANT_TO_STANDARD[cp])
    return ch


def normalize_for_comparison(text: str) -> str:
    """Normalize text for variant-aware comparison.

    Args:
        text: Input text that may contain variant characters.

    Returns:
        Normalized text with variants mapped to standard forms.
        Original text is unchanged; this returns a new string.
    """
    if not text:
        return text
    return "".join(_normalize_char(ch) for ch in text)


def are_variants_equal(a: str, b: str) -> bool:
    """Check if two strings are equal under variant normalization.

    Args:
        a: First string.
        b: Second string.

    Returns:
        True if strings match after variant normalization.
    """
    return normalize_for_comparison(a) == normalize_for_comparison(b)


def find_normalized(text: str, pattern: str) -> int:
    """Find pattern in text using variant-aware comparison.

    Args:
        text: Text to search in (e.g., translation output).
        pattern: Pattern to find (e.g., canonical entity form).

    Returns:
        Character index of first match, or -1 if not found.
    """
    if not pattern:
        return -1

    norm_text = normalize_for_comparison(text)
    norm_pattern = normalize_for_comparison(pattern)

    pos = norm_text.find(norm_pattern)
    if pos == -1:
        return -1

    # Map normalized position back to original text position
    # Since normalization is 1:1 char mapping, positions are preserved
    return pos


def find_all_normalized(text: str, pattern: str) -> list[int]:
    """Find all occurrences of pattern in text using variant-aware comparison.

    Args:
        text: Text to search in.
        pattern: Pattern to find.

    Returns:
        List of character indices where pattern matches.
    """
    if not pattern:
        return []

    norm_text = normalize_for_comparison(text)
    norm_pattern = normalize_for_comparison(pattern)

    positions = []
    start = 0
    while True:
        pos = norm_text.find(norm_pattern, start)
        if pos == -1:
            break
        positions.append(pos)
        start = pos + 1

    return positions