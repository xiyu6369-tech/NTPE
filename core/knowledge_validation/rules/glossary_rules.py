"""
Glossary Business Rules
RM-5.7.3B Business Rule Validation Engine

Implements GL-001 through GL-005:
- GL-001: source unique
- GL-002: locked term immutable
- GL-003: forbidden_forms cannot contain target
- GL-004: alias duplicates forbidden
- GL-005: confidence range
"""

from core.knowledge_validation.rules.base import EntityRule, DomainRule, RuleContext
from core.knowledge_validation.validation_codes import BusinessRuleCode
from core.knowledge_validation.validation_result import ValidationErrorDetail


class GlossarySourceUniqueRule(DomainRule):
    """GL-001: source unique across all glossary entities."""

    @property
    def domain(self) -> str:
        return "glossary"

    def __init__(self):
        super().__init__(BusinessRuleCode.GL001, severity="error")

    def _validate_domain(self, entities: list[dict], context: RuleContext) -> list[ValidationErrorDetail]:
        errors = []
        seen_sources = {}

        for i, entity in enumerate(entities):
            source_term = entity.get("name", "").strip()
            if not source_term:
                continue

            if source_term in seen_sources:
                first_idx = seen_sources[source_term]
                errors.append(
                    self._create_error(
                        field="name",
                        message=f"Duplicate source term '{source_term}' found at index {i} (first at {first_idx})",
                        value=source_term,
                        instance_path=f"[{i}]/name",
                    )
                )
            else:
                seen_sources[source_term] = i

        return errors


class GlossaryLockedImmutableRule(EntityRule):
    """GL-002: locked term immutable (cannot modify canonical_translation if lock_status is locked)."""

    @property
    def domain(self) -> str:
        return "glossary"

    def __init__(self):
        super().__init__(BusinessRuleCode.GL002, severity="error")

    def _validate_entity(self, entity: dict, context: RuleContext) -> list[ValidationErrorDetail]:
        errors = []
        metadata = entity.get("metadata", {})
        lock_status = metadata.get("lock_status")
        attributes = entity.get("attributes", {})

        if lock_status == "locked":
            canonical_translation = attributes.get("canonical_translation")
            if canonical_translation is None:
                errors.append(
                    self._create_error(
                        field="canonical_translation",
                        message="Locked glossary term must have canonical_translation",
                        value=canonical_translation,
                        instance_path="/attributes/canonical_translation",
                    )
                )

        return errors


class GlossaryForbiddenFormsRule(EntityRule):
    """GL-003: forbidden_forms cannot contain target (canonical_translation)."""

    @property
    def domain(self) -> str:
        return "glossary"

    def __init__(self):
        super().__init__(BusinessRuleCode.GL003, severity="error")

    def _validate_entity(self, entity: dict, context: RuleContext) -> list[ValidationErrorDetail]:
        errors = []
        attributes = entity.get("attributes", {})
        canonical_translation = attributes.get("canonical_translation", "").strip()
        forbidden_forms = attributes.get("forbidden_forms", [])

        if canonical_translation and forbidden_forms:
            for i, forbidden in enumerate(forbidden_forms):
                if forbidden and forbidden.strip() == canonical_translation:
                    errors.append(
                        self._create_error(
                            field="forbidden_forms",
                            message=f"forbidden_forms at index {i} must not contain the canonical_translation",
                            value=forbidden,
                            instance_path=f"/attributes/forbidden_forms/{i}",
                        )
                )

        return errors


class GlossaryAliasDuplicatesRule(EntityRule):
    """GL-004: alias duplicates forbidden."""

    @property
    def domain(self) -> str:
        return "glossary"

    def __init__(self):
        super().__init__(BusinessRuleCode.GL004, severity="error")

    def _validate_entity(self, entity: dict, context: RuleContext) -> list[ValidationErrorDetail]:
        errors = []
        attributes = entity.get("attributes", {})
        aliases = attributes.get("aliases", [])

        if aliases:
            seen = set()
            for i, alias in enumerate(aliases):
                if alias is None:
                    continue
                normalized = alias.strip()
                if normalized in seen:
                    errors.append(
                        self._create_error(
                            field="aliases",
                            message=f"Duplicate alias found: '{alias}'",
                            value=alias,
                            instance_path=f"/attributes/aliases/{i}",
                        )
                    )
                seen.add(normalized)

        return errors


class GlossaryConfidenceRangeRule(EntityRule):
    """GL-005: confidence range 0 ≤ confidence ≤ 1."""

    @property
    def domain(self) -> str:
        return "glossary"

    def __init__(self):
        super().__init__(BusinessRuleCode.GL005, severity="error")

    def _validate_entity(self, entity: dict, context: RuleContext) -> list[ValidationErrorDetail]:
        errors = []
        confidence = entity.get("confidence")

        if confidence is not None:
            try:
                conf_value = float(confidence)
                if conf_value < 0.0 or conf_value > 1.0:
                    errors.append(
                        self._create_error(
                            field="confidence",
                            message=f"Confidence must be between 0 and 1, got {conf_value}",
                            value=confidence,
                            instance_path="/confidence",
                        )
                    )
            except (ValueError, TypeError):
                errors.append(
                    self._create_error(
                        field="confidence",
                        message=f"Confidence must be a number, got {type(confidence).__name__}",
                        value=confidence,
                        instance_path="/confidence",
                    )
                )

        return errors


# Export all glossary rules
GLOSSARY_RULES = [
    GlossarySourceUniqueRule(),
    GlossaryLockedImmutableRule(),
    GlossaryForbiddenFormsRule(),
    GlossaryAliasDuplicatesRule(),
    GlossaryConfidenceRangeRule(),
]