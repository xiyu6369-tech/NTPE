"""
Character Business Rules
RM-5.7.3B Business Rule Validation Engine

Implements CH-001 through CH-005:
- CH-001: canonical_name required, cannot be empty
- CH-002: aliases must not contain canonical_name (case-insensitive)
- CH-003: duplicate aliases forbidden (case-insensitive)
- CH-004: confidence must satisfy 0 ≤ confidence ≤ 1
- CH-005: status must be one of schema enum
"""

from core.knowledge_validation.rules.base import EntityRule, RuleContext
from core.knowledge_validation.validation_codes import BusinessRuleCode
from core.knowledge_validation.validation_result import ValidationErrorDetail


class CharacterCanonicalNameRule(EntityRule):
    """CH-001: canonical_name required, cannot be empty."""

    @property
    def domain(self) -> str:
        return "character"

    def __init__(self):
        super().__init__(BusinessRuleCode.CH001, severity="error")

    def _validate_entity(self, entity: dict, context: RuleContext) -> list[ValidationErrorDetail]:
        errors = []
        attributes = entity.get("attributes", {})
        canonical_name = attributes.get("canonical_name")

        if not canonical_name or not str(canonical_name).strip():
            errors.append(
                self._create_error(
                    field="canonical_name",
                    message="Character canonical_name is required and cannot be empty",
                    value=canonical_name,
                    instance_path="/attributes/canonical_name",
                )
            )

        return errors
class CharacterAliasesNotCanonicalRule(EntityRule):
    """CH-002: aliases must not contain canonical_name (case-insensitive)."""

    @property
    def domain(self) -> str:
        return "character"

    def __init__(self):
        super().__init__(BusinessRuleCode.CH002, severity="error")

    def _validate_entity(self, entity: dict, context: RuleContext) -> list[ValidationErrorDetail]:
        errors = []
        attributes = entity.get("attributes", {})
        canonical_name = attributes.get("canonical_name", "").strip()
        aliases = attributes.get("aliases", [])

        if canonical_name and aliases:
            canonical_lower = canonical_name.lower()
            for i, alias in enumerate(aliases):
                if alias and alias.strip().lower() == canonical_lower:
                    errors.append(
                        self._create_error(
                            field="aliases",
                            message=f"Alias at index {i} must not be identical to canonical_name",
                            value=alias,
                            instance_path=f"/attributes/aliases/{i}",
                        )
                    )

        return errors


class CharacterDuplicateAliasesRule(EntityRule):
    """CH-003: duplicate aliases forbidden (case-insensitive)."""

    @property
    def domain(self) -> str:
        return "character"

    def __init__(self):
        super().__init__(BusinessRuleCode.CH003, severity="error")

    def _validate_entity(self, entity: dict, context: RuleContext) -> list[ValidationErrorDetail]:
        errors = []
        attributes = entity.get("attributes", {})
        aliases = attributes.get("aliases", [])

        if aliases:
            seen = set()
            for i, alias in enumerate(aliases):
                if alias is None:
                    continue
                normalized = alias.strip().lower()
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


class CharacterConfidenceRangeRule(EntityRule):
    """CH-004: confidence must satisfy 0 ≤ confidence ≤ 1."""

    @property
    def domain(self) -> str:
        return "character"

    def __init__(self):
        super().__init__(BusinessRuleCode.CH004, severity="error")

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


class CharacterStatusEnumRule(EntityRule):
    """CH-005: status must be one of schema enum (pending, approved, rejected, needs_review)."""

    @property
    def domain(self) -> str:
        return "character"

    VALID_STATUSES = {"pending", "approved", "rejected", "needs_review"}

    def __init__(self):
        super().__init__(BusinessRuleCode.CH005, severity="error")

    def _validate_entity(self, entity: dict, context: RuleContext) -> list[ValidationErrorDetail]:
        errors = []
        metadata = entity.get("metadata", {})
        status = metadata.get("review_status")

        if status is not None and status not in self.VALID_STATUSES:
            errors.append(
                self._create_error(
                    field="review_status",
                    message=f"Invalid review_status '{status}'. Must be one of: {', '.join(sorted(self.VALID_STATUSES))}",
                    value=status,
                    instance_path="/metadata/review_status",
                )
            )

        return errors


# Export all character rules
CHARACTER_RULES = [
    CharacterCanonicalNameRule(),
    CharacterAliasesNotCanonicalRule(),
    CharacterDuplicateAliasesRule(),
    CharacterConfidenceRangeRule(),
    CharacterStatusEnumRule(),
]