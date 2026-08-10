# core/translation_release/polish.py

from __future__ import annotations

import re
from typing import Tuple, Dict

from core.translation_runtime.runtime_formatter import (
    clean_provider_output,
    normalize_punctuation_for_zh_tw,
    normalize_taiwan_traditional,
)


def normalize_paragraphs(text: str) -> Tuple[str, Dict]:
    """
    Normalize paragraph structure across full novel.

    Returns: (polished_text, metrics_dict)
    metrics_dict = {
        "paragraphs_before": int,
        "paragraphs_after": int,
        "empty_paragraphs_removed": int,
        "excessive_breaks_consolidated": int,
        "whitespace_normalized": int,
    }
    """
    if not text:
        return text, {
            "paragraphs_before": 0,
            "paragraphs_after": 0,
            "empty_paragraphs_removed": 0,
            "excessive_breaks_consolidated": 0,
            "whitespace_normalized": 0,
        }

    # Count paragraphs before (split on double newline, keep non-empty)
    paragraphs_before = len([p for p in text.split("\n\n") if p.strip()])

    # Count empty paragraphs BEFORE consolidation
    # Empty paragraphs are the empty strings resulting from consecutive \n\n
    empty_removed = len([p for p in text.split("\n\n") if not p.strip()])

    # 1. Consolidate 3+ consecutive newlines to exactly 2
    excessive_count = 0
    def _replace_excessive_newlines(match):
        nonlocal excessive_count
        excessive_count += 1
        return "\n\n"

    text = re.sub(r"\n{3,}", _replace_excessive_newlines, text)

    # 2. Remove empty paragraphs (paragraphs containing only whitespace)
    # Split on double newline, filter, rejoin
    paragraphs = [p for p in text.split("\n\n") if p.strip()]
    text = "\n\n".join(paragraphs)

    # 3. Normalize internal whitespace within paragraphs
    # Tabs -> spaces, multiple spaces -> single space
    whitespace_normalized = 0
    def _normalize_ws(match):
        nonlocal whitespace_normalized
        whitespace_normalized += 1
        return " "

    # Replace tabs and multiple spaces with single space, but not newlines
    lines = text.split("\n")
    normalized_lines = []
    for line in lines:
        # Only normalize spaces/tabs, preserve intentional spacing at line level
        new_line = re.sub(r"[ \t]{2,}", _normalize_ws, line)
        new_line = new_line.replace("\t", " ")
        if new_line != line:
            whitespace_normalized += 1
        normalized_lines.append(new_line)
    text = "\n".join(normalized_lines)

    # 4. Ensure single trailing newline at EOF
    if text and not text.endswith("\n"):
        text += "\n"
    elif text.endswith("\n\n"):
        # If we have double newline at end, reduce to single
        text = text.rstrip("\n") + "\n"

    paragraphs_after = len([p for p in text.split("\n\n") if p.strip()])

    return text, {
        "paragraphs_before": paragraphs_before,
        "paragraphs_after": paragraphs_after,
        "empty_paragraphs_removed": empty_removed,
        "excessive_breaks_consolidated": excessive_count,
        "whitespace_normalized": whitespace_normalized,
    }


def unify_quote_style(text: str) -> Tuple[str, Dict]:
    """
    Unify quotation marks to CJK corner brackets CONSERVATIVELY.

    Rules:
    - Only convert ASCII double quotes "..." that form clear quotation pairs
    - Only convert ASCII single quotes '...' that form clear quotation pairs
    - Do NOT convert apostrophes in contractions (don't, won't, it's) or possessives
    - Do NOT convert quotes that are clearly code, measurement, or non-dialogue
    - Preserve already-correct CJK quotes 「...」 『...』

    Returns: (polished_text, metrics_dict)
    metrics_dict = {
        "double_quotes_converted": int,
        "single_quotes_converted": int,
        "mixed_quotes_resolved": int,
        "skipped_apostrophes": int,
    }
    """
    if not text:
        return text, {
            "double_quotes_converted": 0,
            "single_quotes_converted": 0,
            "mixed_quotes_resolved": 0,
            "skipped_apostrophes": 0,
        }

    double_converted = 0
    single_converted = 0
    mixed_resolved = 0
    skipped_apostrophes = 0

    # Pattern for contractions and possessives that should NOT be converted
    CONTRACTION_PATTERNS = [
        r"\bdon't\b", r"\bwon't\b", r"\bcan't\b", r"\bcan't\b",
        r"\bit's\b", r"\bit's\b", r"\bthat's\b", r"\bwhat's\b",
        r"\bwho's\b", r"\bwhere's\b", r"\bhow's\b", r"\bthere's\b",
        r"\bisn't\b", r"\baren't\b", r"\bwasn't\b", r"\bweren't\b",
        r"\bhasn't\b", r"\bhaven't\b", r"\bhadn't\b",
        r"\bdoesn't\b", r"\bdon't\b", r"\bdidn't\b",
        r"\bwon't\b", r"\bwouldn't\b", r"\bshouldn't\b", r"\bcouldn't\b",
        r"\bmustn't\b", r"\bneedn't\b", r"\bdaren't\b",
        r"\bi'm\b", r"\byou're\b", r"\bwe're\b", r"\bthey're\b",
        r"\bi've\b", r"\byou've\b", r"\bwe've\b", r"\bthey've\b",
        r"\bi'll\b", r"\byou'll\b", r"\bwe'll\b", r"\bthey'll\b",
        r"\bi'd\b", r"\byou'd\b", r"\bwe'd\b", r"\bthey'd\b",
        r"\blet's\b", r"\bhere's\b", r"\bthere're\b",
        # Possessives
        r"\w+'s\b",
    ]
    contraction_regex = re.compile("|".join(CONTRACTION_PATTERNS), re.IGNORECASE)

    # First, protect contractions/apostrophes by temporarily replacing them
    protected = {}
    protect_counter = 0

    def _protect_contractions(match):
        nonlocal protect_counter, skipped_apostrophes
        key = f"__PROTECTED_{protect_counter}__"
        protected[key] = match.group(0)
        protect_counter += 1
        skipped_apostrophes += 1
        return key

    # Protect contractions
    text = contraction_regex.sub(_protect_contractions, text)

    # Also protect measurement-like patterns: 5" (inches), 10' (feet), etc.
    # Use lookbehind/lookahead to ensure it's a number followed by quote at word boundary
    measurement_double = re.compile(r'(?<=\d)"(?=\s|\b|$)')
    measurement_single = re.compile(r"(?<=\d)'(?=\s|\b|$)")

    def _protect_measurement_double(match):
        nonlocal protect_counter, skipped_apostrophes
        key = f"__PROTECTED_{protect_counter}__"
        protected[key] = match.group(0)
        protect_counter += 1
        skipped_apostrophes += 1
        return key

    def _protect_measurement_single(match):
        nonlocal protect_counter, skipped_apostrophes
        key = f"__PROTECTED_{protect_counter}__"
        protected[key] = match.group(0)
        protect_counter += 1
        skipped_apostrophes += 1
        return key

    text = measurement_double.sub(_protect_measurement_double, text)
    text = measurement_single.sub(_protect_measurement_single, text)

    # Protect code-like structures: {...}, [...], {...:...}, [...,...], etc.
    # These contain braces, brackets, colons, equals within quote context
    # We'll protect the entire structure by finding balanced braces/brackets
    code_like_pattern = re.compile(r'(\{.*?\}|\[.*?\])', re.DOTALL)

    def _protect_code_like(match):
        nonlocal protect_counter, skipped_apostrophes
        key = f"__PROTECTED_{protect_counter}__"
        protected[key] = match.group(0)
        protect_counter += 1
        skipped_apostrophes += 1
        return key

    text = code_like_pattern.sub(_protect_code_like, text)

    # Now convert double quotes "..." -> 「...」
    # Only convert balanced pairs that don't contain unpaired quotes inside
    def _convert_double_quotes(match):
        nonlocal double_converted
        content = match.group(1)
        # Check if content looks like code/measurement (has =, :, {, }, digits+units)
        if re.search(r'[{}:=]', content) or re.search(r'\d+\s*(cm|mm|km|kg|g|ml|l|px|%)\b', content):
            return match.group(0)  # Don't convert
        double_converted += 1
        return f"「{content}」"

    # Pattern: "..." where content doesn't contain unescaped "
    text = re.sub(r'"([^"\n]{1,500})"', _convert_double_quotes, text)

    # Convert single quotes '...' -> 『...』 (for dialogue/quotation)
    # But be more conservative - only if it looks like a quotation, not apostrophe
    def _convert_single_quotes(match):
        nonlocal single_converted
        content = match.group(1)
        # Skip if it looks like a contraction (already protected) or possessive
        if re.search(r'[{}:=]', content):
            return match.group(0)
        single_converted += 1
        return f"『{content}』"

    # Pattern: '...' where content doesn't contain unescaped '
    text = re.sub(r"'([^'\n]{1,200})'", _convert_single_quotes, text)

    # Restore protected contractions/measurements
    for key, value in protected.items():
        text = text.replace(key, value)

    # Count mixed quotes resolved (where both " and ' were present in overlapping regions)
    # This is a rough estimate
    mixed_resolved = min(double_converted, single_converted)

    return text, {
        "double_quotes_converted": double_converted,
        "single_quotes_converted": single_converted,
        "mixed_quotes_resolved": mixed_resolved,
        "skipped_apostrophes": skipped_apostrophes,
    }


def polish_full_novel(
    text: str,
    *,
    taiwan_traditional_normalization: bool = True,
    enabled: bool = True,
) -> Tuple[str, Dict]:
    """
    Main polish entry point — runs full pipeline on assembled novel.

    Pipeline order:
    1. clean_provider_output()          # remove preambles, normalize line endings
    2. normalize_paragraphs()           # paragraph structure
    3. unify_quote_style()              # quote consistency (conservative)
    4. normalize_punctuation_for_zh_tw() # ASCII -> CJK punctuation
    5. normalize_taiwan_traditional()   # if enabled
    6. clean_provider_output()          # final cleanup

    Returns: (final_text, aggregate_metrics)
    aggregate_metrics = {
        "paragraphs": {...},
        "quotes": {...},
        "punctuation": {...},
        "traditional_normalization": {...},
        "total_changes": int,
    }
    """
    if not enabled or not text:
        return text, {
            "paragraphs": {},
            "quotes": {},
            "punctuation": {},
            "traditional_normalization": {},
            "total_changes": 0,
        }

    aggregate_metrics = {}
    total_changes = 0

    # Step 1: clean_provider_output
    text = clean_provider_output(text)

    # Step 2: normalize_paragraphs
    text, para_metrics = normalize_paragraphs(text)
    aggregate_metrics["paragraphs"] = para_metrics
    total_changes += (
        para_metrics.get("empty_paragraphs_removed", 0) +
        para_metrics.get("excessive_breaks_consolidated", 0) +
        para_metrics.get("whitespace_normalized", 0)
    )

    # Step 3: unify_quote_style
    text, quote_metrics = unify_quote_style(text)
    aggregate_metrics["quotes"] = quote_metrics
    total_changes += (
        quote_metrics.get("double_quotes_converted", 0) +
        quote_metrics.get("single_quotes_converted", 0)
    )

    # Step 4: normalize_punctuation_for_zh_tw
    before_punct = text
    text = normalize_punctuation_for_zh_tw(text)
    # Count punctuation changes roughly
    punct_changes = sum(1 for a, b in zip(before_punct, text) if a != b)
    aggregate_metrics["punctuation"] = {"changes": punct_changes}
    total_changes += punct_changes

    # Step 5: normalize_taiwan_traditional
    if taiwan_traditional_normalization:
        before_trad = text
        text = normalize_taiwan_traditional(text)
        trad_changes = sum(1 for a, b in zip(before_trad, text) if a != b)
        aggregate_metrics["traditional_normalization"] = {"changes": trad_changes}
        total_changes += trad_changes
    else:
        aggregate_metrics["traditional_normalization"] = {"changes": 0, "skipped": True}

    # Step 6: final clean_provider_output
    text = clean_provider_output(text)

    aggregate_metrics["total_changes"] = total_changes

    return text, aggregate_metrics
