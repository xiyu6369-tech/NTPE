from __future__ import annotations

import hashlib
from typing import Any, Dict, Mapping, Set, Tuple

from .models import SeriesCharacterRecord, SeriesFactRecord


def compute_series_character_id(series_id: str, korean_name: str) -> str:
    """Namespace-isolated character ID."""
    return f"schar_{hashlib.sha256(f'{series_id}|{korean_name}'.encode()).hexdigest()[:16]}"


def compute_series_fact_id(series_id: str, fact_type: str, value: str) -> str:
    """Namespace-isolated fact ID for non-character facts."""
    return f"sfact_{hashlib.sha256(f'{series_id}|{fact_type}|{value}'.encode()).hexdigest()[:16]}"


class SeriesNamespaceMapping:
    """
    Maintains namespace-isolated mappings for Series Memory Store.

    Ensures Series A and Series B with same Korean character name
    have completely isolated canonical memory.
    """

    def __init__(self) -> None:
        self._korean_to_series_id: Dict[str, str] = {}
        self._series_id_to_book_ids: Dict[str, Set[str]] = {}
        self._series_character_id_to_record: Dict[str, SeriesCharacterRecord] = {}
        self._series_fact_id_to_record: Dict[str, SeriesFactRecord] = {}

    def register_character(
        self,
        series_id: str,
        korean_name: str,
        record: SeriesCharacterRecord,
    ) -> str:
        """Register a character and return the namespace-isolated ID."""
        series_character_id = compute_series_character_id(series_id, korean_name)

        if series_character_id in self._series_character_id_to_record:
            existing = self._series_character_id_to_record[series_character_id]
            if existing.korean_name != korean_name:
                raise ValueError(
                    f"series_character_id collision: {series_character_id} "
                    f"maps to {existing.korean_name} and {korean_name}"
                )

        self._series_character_id_to_record[series_character_id] = record
        self._korean_to_series_id[korean_name] = series_character_id

        if series_character_id not in self._series_id_to_book_ids:
            self._series_id_to_book_ids[series_character_id] = set()
        self._series_id_to_book_ids[series_character_id].update(record.source_books)

        return series_character_id

    def register_fact(self, series_id: str, record: SeriesFactRecord) -> str:
        """Register a non-character fact."""
        if record.series_fact_id in self._series_fact_id_to_record:
            existing = self._series_fact_id_to_record[record.series_fact_id]
            if existing.value != record.value or existing.fact_type != record.fact_type:
                raise ValueError(
                    f"series_fact_id collision: {record.series_fact_id} "
                    f"maps to different fact"
                )
        self._series_fact_id_to_record[record.series_fact_id] = record
        return record.series_fact_id

    def get_character(self, series_character_id: str) -> SeriesCharacterRecord | None:
        """Get character record by namespace-isolated ID."""
        return self._series_character_id_to_record.get(series_character_id)

    def get_fact(self, series_fact_id: str) -> SeriesFactRecord | None:
        """Get fact record by namespace-isolated ID."""
        return self._series_fact_id_to_record.get(series_fact_id)

    def get_series_character_id(self, korean_name: str) -> str | None:
        """Get series_character_id for a Korean name."""
        return self._korean_to_series_id.get(korean_name)

    def get_book_ids(self, series_character_id: str) -> Set[str]:
        """Get book identities that contributed to this character."""
        return self._series_id_to_book_ids.get(series_character_id, set())

    def get_all_characters(self) -> Tuple[SeriesCharacterRecord, ...]:
        """Get all character records."""
        return tuple(sorted(
            self._series_character_id_to_record.values(),
            key=lambda r: r.series_character_id
        ))

    def get_all_facts(self) -> Tuple[SeriesFactRecord, ...]:
        """Get all fact records."""
        return tuple(sorted(
            self._series_fact_id_to_record.values(),
            key=lambda r: r.series_fact_id
        ))

    def get_characters_by_fact_type(self, fact_type: Any) -> Tuple[SeriesCharacterRecord, ...]:
        """Get character records filtered by fact type."""
        return tuple(
            r for r in self._series_character_id_to_record.values()
            if r.fact_type == fact_type
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize mapping for persistence."""
        return {
            "korean_to_series_id": self._korean_to_series_id,
            "series_id_to_book_ids": {
                k: list(v) for k, v in self._series_id_to_book_ids.items()
            },
            "series_character_id_to_record": {
                k: v.to_dict() for k, v in self._series_character_id_to_record.items()
            },
            "series_fact_id_to_record": {
                k: v.to_dict() for k, v in self._series_fact_id_to_record.items()
            },
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SeriesNamespaceMapping":
        """Deserialize mapping from persistence."""
        mapping = cls()
        mapping._korean_to_series_id = dict(data.get("korean_to_series_id", {}))
        mapping._series_id_to_book_ids = {
            k: set(v) for k, v in data.get("series_id_to_book_ids", {}).items()
        }
        mapping._series_character_id_to_record = {
            k: SeriesCharacterRecord.from_dict(v)
            for k, v in data.get("series_character_id_to_record", {}).items()
        }
        mapping._series_fact_id_to_record = {
            k: SeriesFactRecord.from_dict(v)
            for k, v in data.get("series_fact_id_to_record", {}).items()
        }
        return mapping


def validate_namespace_isolation(
    series_id: str,
    mapping: SeriesNamespaceMapping,
) -> None:
    """
    Validate that all records in mapping belong to the correct series.

    Raises:
        ValueError: If any record has a mismatched series_id in its ID.
    """
    for series_character_id in mapping._series_character_id_to_record:
        if not series_character_id.startswith(f"schar_"):
            raise ValueError(f"Invalid series_character_id prefix: {series_character_id}")
        # Verify the ID was computed with this series_id
        record = mapping._series_character_id_to_record[series_character_id]
        expected_id = compute_series_character_id(series_id, record.korean_name)
        if series_character_id != expected_id:
            raise ValueError(
                f"series_character_id {series_character_id} does not match "
                f"expected {expected_id} for series {series_id}"
            )

    for series_fact_id in mapping._series_fact_id_to_record:
        if not series_fact_id.startswith(f"sfact_"):
            raise ValueError(f"Invalid series_fact_id prefix: {series_fact_id}")
        # Fact ID includes series_id in its computation
        record = mapping._series_fact_id_to_record[series_fact_id]
        expected_id = compute_series_fact_id(series_id, record.fact_type.value, record.value)
        if series_fact_id != expected_id:
            raise ValueError(
                f"series_fact_id {series_fact_id} does not match "
                f"expected {expected_id} for series {series_id}"
            )