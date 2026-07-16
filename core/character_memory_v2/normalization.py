from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from typing import Iterable


_WHITESPACE = re.compile(r"\s+")


def normalize_text(value: str) -> str:
    return _WHITESPACE.sub(" ", unicodedata.normalize("NFKC", value).strip())


def normalized_identity(value: str) -> str:
    return normalize_text(value).casefold()


def canonical_hash(parts: Iterable[str]) -> str:
    payload = json.dumps(list(parts), ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def stable_evidence_id(
    evidence_type: str,
    source_case_id: str,
    source_segment_id: str,
    source_text_hash: str,
    excerpt: str,
) -> str:
    return "ev_" + canonical_hash((
        evidence_type,
        normalize_text(source_case_id),
        normalize_text(source_segment_id),
        source_text_hash.lower(),
        normalized_identity(excerpt),
    ))[:24]


def stable_memory_id(
    character_id: str,
    fact_type: str,
    value: str,
    primary_evidence_id: str,
) -> str:
    return "cm2_" + canonical_hash((
        normalize_text(character_id),
        fact_type,
        normalized_identity(value),
        primary_evidence_id,
    ))[:32]


def canonical_fact_key(character_id: str, fact_type: str, value: str) -> tuple[str, str, str]:
    return normalize_text(character_id), fact_type, normalized_identity(value)


def canonical_conflict_key(character_id: str, fact_type: str) -> tuple[str, str]:
    return normalize_text(character_id), fact_type
