"""
Failure Classifier (RM-5.8.4)

Unified error classification engine that categorizes every comparison
failure into a standard FailureCategory. Operates on ExtractionComparison
results and EntityMatchResult data.

Fully offline. Determinisitic. No external dependencies.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .models import (
    FailureCategory,
    FailureDetail,
    FailureSummary,
)
from ..models import (
    EntityType,
    ExtractionComparison,
    EntityMatchResult,
)


_EXTRACTOR_FAILURE_RULES: Dict[str, Dict[str, FailureCategory]] = {
    "character": {
        "missing_entity": FailureCategory.MISSING_ENTITY,
        "hallucination": FailureCategory.HALLUCINATION,
        "wrong_alias": FailureCategory.WRONG_ALIAS,
        "wrong_relationship": FailureCategory.WRONG_RELATIONSHIP,
        "duplicate": FailureCategory.DUPLICATE,
        "over_merge": FailureCategory.OVER_MERGE,
        "under_merge": FailureCategory.UNDER_MERGE,
        "low_confidence": FailureCategory.LOW_CONFIDENCE,
        "schema_failure": FailureCategory.SCHEMA_FAILURE,
        "business_rule_failure": FailureCategory.BUSINESS_RULE_FAILURE,
    },
    "glossary": {
        "missing_entity": FailureCategory.MISSING_ENTITY,
        "hallucination": FailureCategory.HALLUCINATION,
        "wrong_glossary": FailureCategory.WRONG_GLOSSARY,
        "duplicate": FailureCategory.DUPLICATE,
        "over_merge": FailureCategory.OVER_MERGE,
        "under_merge": FailureCategory.UNDER_MERGE,
        "low_confidence": FailureCategory.LOW_CONFIDENCE,
        "schema_failure": FailureCategory.SCHEMA_FAILURE,
        "business_rule_failure": FailureCategory.BUSINESS_RULE_FAILURE,
    },
    "scene": {
        "missing_entity": FailureCategory.MISSING_ENTITY,
        "hallucination": FailureCategory.HALLUCINATION,
        "wrong_scene_boundary": FailureCategory.WRONG_SCENE_BOUNDARY,
        "duplicate": FailureCategory.DUPLICATE,
        "over_merge": FailureCategory.OVER_MERGE,
        "under_merge": FailureCategory.UNDER_MERGE,
        "low_confidence": FailureCategory.LOW_CONFIDENCE,
        "schema_failure": FailureCategory.SCHEMA_FAILURE,
        "business_rule_failure": FailureCategory.BUSINESS_RULE_FAILURE,
    },
    "narrative": {
        "missing_entity": FailureCategory.MISSING_ENTITY,
        "hallucination": FailureCategory.HALLUCINATION,
        "wrong_timeline": FailureCategory.WRONG_TIMELINE,
        "wrong_relationship": FailureCategory.WRONG_RELATIONSHIP,
        "duplicate": FailureCategory.DUPLICATE,
        "over_merge": FailureCategory.OVER_MERGE,
        "under_merge": FailureCategory.UNDER_MERGE,
        "low_confidence": FailureCategory.LOW_CONFIDENCE,
        "schema_failure": FailureCategory.SCHEMA_FAILURE,
        "business_rule_failure": FailureCategory.BUSINESS_RULE_FAILURE,
    },
    "style": {
        "missing_entity": FailureCategory.MISSING_ENTITY,
        "hallucination": FailureCategory.HALLUCINATION,
        "wrong_style": FailureCategory.WRONG_STYLE,
        "duplicate": FailureCategory.DUPLICATE,
        "over_merge": FailureCategory.OVER_MERGE,
        "under_merge": FailureCategory.UNDER_MERGE,
        "low_confidence": FailureCategory.LOW_CONFIDENCE,
        "schema_failure": FailureCategory.SCHEMA_FAILURE,
        "business_rule_failure": FailureCategory.BUSINESS_RULE_FAILURE,
    },
}


class FailureClassifier:
    """Classifies comparison failures into standard FailureCategories.

    For each entity match result that is not a correct match, determines
    what kind of failure occurred: missing entity, hallucination, wrong
    alias, wrong relationship, duplicate, schema failure, etc.
    """

    def classify_comparison(
        self,
        comparison: ExtractionComparison,
    ) -> List[FailureDetail]:
        extractor_name = comparison.extractor_type.value
        failures: List[FailureDetail] = []

        failures.extend(self._classify_missing(comparison))
        failures.extend(self._classify_hallucinated(comparison))
        failures.extend(self._classify_unmatched_in_matches(comparison))
        failures.extend(self._classify_duplicates(comparison))

        return failures

    def _classify_missing(
        self,
        comparison: ExtractionComparison,
    ) -> List[FailureDetail]:
        failures: List[FailureDetail] = []
        extractor_name = comparison.extractor_type.value

        for entity in comparison.missing_entities:
            eid = entity.get("id", entity.get("entity_id", ""))
            failures.append(FailureDetail(
                failure_category=FailureCategory.MISSING_ENTITY,
                extractor_type=extractor_name,
                entity_id=eid,
                actual_entity=entity,
                similarity_score=0.0,
                confidence=float(entity.get("confidence", 0.0)),
                description=f"Entity '{eid}' present in golden but missing from prediction",
            ))
        return failures

    def _classify_hallucinated(
        self,
        comparison: ExtractionComparison,
    ) -> List[FailureDetail]:
        failures: List[FailureDetail] = []
        extractor_name = comparison.extractor_type.value

        for entity in comparison.hallucinated_entities:
            eid = entity.get("id", entity.get("entity_id", ""))
            failures.append(FailureDetail(
                failure_category=FailureCategory.HALLUCINATION,
                extractor_type=extractor_name,
                entity_id=eid,
                expected_entity=entity,
                similarity_score=0.0,
                confidence=float(entity.get("confidence", 0.0)),
                description=f"Entity '{eid}' predicted but not present in golden",
            ))
        return failures

    def _classify_unmatched_in_matches(
        self,
        comparison: ExtractionComparison,
    ) -> List[FailureDetail]:
        failures: List[FailureDetail] = []
        extractor_name = comparison.extractor_type.value
        rules = _EXTRACTOR_FAILURE_RULES.get(extractor_name, {})

        for match in comparison.matches:
            if match.matched:
                continue

            if not match.predicted_entity_id and not match.golden_entity_id:
                continue

            category = FailureCategory.MISSING_ENTITY

            if not match.predicted_entity_id and match.golden_entity_id:
                category = FailureCategory.MISSING_ENTITY
            elif match.predicted_entity_id and not match.golden_entity_id:
                category = FailureCategory.HALLUCINATION
            else:
                match_label = self._classify_match_label(match, extractor_name)
                category = rules.get(match_label, FailureCategory.MISSING_ENTITY)

                if match.confidence_predicted < 0.5:
                    category = FailureCategory.LOW_CONFIDENCE

            entity_id = match.golden_entity_id or match.predicted_entity_id or ""
            failures.append(FailureDetail(
                failure_category=category,
                extractor_type=extractor_name,
                entity_id=entity_id,
                similarity_score=match.similarity_score,
                field_mismatches=dict(match.field_matches) if hasattr(match, 'field_matches') else {},
                confidence=match.confidence_predicted,
                description=f"Unmatched entity: golden={match.golden_entity_id}, predicted={match.predicted_entity_id}, similarity={match.similarity_score:.4f}",
            ))
        return failures

    def _classify_duplicates(
        self,
        comparison: ExtractionComparison,
    ) -> List[FailureDetail]:
        failures: List[FailureDetail] = []
        extractor_name = comparison.extractor_type.value

        for entity in comparison.duplicate_entities:
            eid = entity.get("id", entity.get("entity_id", ""))
            failures.append(FailureDetail(
                failure_category=FailureCategory.DUPLICATE,
                extractor_type=extractor_name,
                entity_id=eid,
                expected_entity=entity,
                similarity_score=0.0,
                confidence=float(entity.get("confidence", 0.0)),
                description=f"Duplicate entity detected: '{eid}' appears multiple times in prediction",
            ))
        return failures

    def _classify_match_label(
        self,
        match: EntityMatchResult,
        extractor_name: str,
    ) -> str:
        """Determine a semantic failure label from a match result."""
        if match.similarity_score == 0.0:
            return "missing_entity"

        field_matches = getattr(match, 'field_matches', {})
        if not field_matches:
            return "missing_entity"

        for field_name, is_match in field_matches.items():
            if not is_match:
                if extractor_name == "character":
                    if field_name in ("aliases", "name"):
                        return "wrong_alias"
                    if field_name == "relationships":
                        return "wrong_relationship"
                elif extractor_name == "scene":
                    if field_name in ("location", "time_of_day"):
                        return "wrong_scene_boundary"
                elif extractor_name == "narrative":
                    if field_name in ("arc", "plot_point"):
                        return "wrong_timeline"
                elif extractor_name == "style":
                    if field_name in ("tone", "category"):
                        return "wrong_style"
                elif extractor_name == "glossary":
                    if field_name in ("term", "translation", "definition"):
                        return "wrong_glossary"

        return "missing_entity"

    def build_summary(
        self,
        comparisons: List[ExtractionComparison],
    ) -> FailureSummary:
        """Build a full FailureSummary from a list of comparisons."""
        summary = FailureSummary()

        for comparison in comparisons:
            failures = self.classify_comparison(comparison)
            for failure in failures:
                summary.add_failure(failure)

        return summary

    def classify_batch(
        self,
        comparisons_by_extractor: Dict[str, List[ExtractionComparison]],
    ) -> Dict[str, FailureSummary]:
        results: Dict[str, FailureSummary] = {}
        for extractor_name, comparisons in comparisons_by_extractor.items():
            results[extractor_name] = self.build_summary(comparisons)
        return results


def create_failure_classifier() -> FailureClassifier:
    return FailureClassifier()