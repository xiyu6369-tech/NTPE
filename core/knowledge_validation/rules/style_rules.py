"""
Style Business Rules
RM-5.7.3B Business Rule Validation Engine

Implements ST-001 through ST-005:
- ST-001: style_type valid
- ST-002: pattern uniqueness
- ST-003: confidence range
- ST-004: priority non-negative
- ST-005: duplicate conventions forbidden
"""

from core.knowledge_validation.rules.base import EntityRule, RuleContext
from core.knowledge_validation.validation_codes import BusinessRuleCode
from core.knowledge_validation.validation_result import ValidationErrorDetail


class StyleStyleTypeValidRule(EntityRule):
    """ST-001: style_type valid enum."""

    @property
    def domain(self) -> str:
        return "style"

    VALID_STYLE_TYPES = {
        "author_fingerprint",
        "genre_profile",
        "register_rules",
        "collocation_patterns",
        "translation_preferences",
        "forbidden_patterns",
        "positive_patterns",
    }

    def __init__(self):
        super().__init__(BusinessRuleCode.ST001, severity="error")

    def _validate_entity(self, entity: dict, context: RuleContext) -> list[ValidationErrorDetail]:
        errors = []
        attributes = entity.get("attributes", {})
        style_type = attributes.get("style_type")

        if style_type and style_type not in self.VALID_STYLE_TYPES:
            errors.append(
                self._create_error(
                    field="style_type",
                    message=f"Invalid style_type '{style_type}'. Must be one of: {', '.join(sorted(self.VALID_STYLE_TYPES))}",
                    value=style_type,
                    instance_path="/attributes/style_type",
                )
            )

        return errors


class StylePatternUniquenessRule(EntityRule):
    """ST-002: pattern uniqueness within rules (forbidden_patterns, positive_patterns)."""

    @property
    def domain(self) -> str:
        return "style"

    def __init__(self):
        super().__init__(BusinessRuleCode.ST002, severity="error")

    def _validate_entity(self, entity: dict, context: RuleContext) -> list[ValidationErrorDetail]:
        errors = []
        attributes = entity.get("attributes", {})

        for pattern_field in ["forbidden_patterns", "positive_patterns"]:
            patterns = attributes.get(pattern_field, [])
            if patterns:
                seen = set()
                for i, pattern_obj in enumerate(patterns):
                    if not isinstance(pattern_obj, dict):
                        continue
                    pattern = pattern_obj.get("pattern")
                    if pattern is None:
                        continue
                    normalized = str(pattern).strip()
                    if normalized in seen:
                        errors.append(
                            self._create_error(
                                field=pattern_field,
                                message=f"Duplicate pattern in {pattern_field}: '{pattern}'",
                                value=pattern_obj,
                                instance_path=f"/attributes/{pattern_field}/{i}",
                            )
                        )
                    seen.add(normalized)

        return errors


class StyleConfidenceRangeRule(EntityRule):
    """ST-003: confidence range 0 ≤ confidence ≤ 1."""

    @property
    def domain(self) -> str:
        return "style"

    def __init__(self):
        super().__init__(BusinessRuleCode.ST003, severity="error")

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


class StylePriorityNonNegativeRule(EntityRule):
    """ST-004: priority non-negative (0-100)."""

    @property
    def domain(self) -> str:
        return "style"

    def __init__(self):
        super().__init__(BusinessRuleCode.ST004, severity="error")

    def _validate_entity(self, entity: dict, context: RuleContext) -> list[ValidationErrorDetail]:
        errors = []
        attributes = entity.get("attributes", {})
        priority = attributes.get("priority")

        if priority is not None:
            try:
                prio = int(priority)
                if prio < 0 or prio > 100:
                    errors.append(
                        self._create_error(
                            field="priority",
                            message=f"Priority must be between 0 and 100, got {prio}",
                            value=priority,
                            instance_path="/attributes/priority",
                        )
                    )
            except (ValueError, TypeError):
                errors.append(
                    self._create_error(
                        field="priority",
                        message=f"Priority must be an integer, got {type(priority).__name__}",
                        value=priority,
                        instance_path="/attributes/priority",
                    )
                )

        return errors


class StyleDuplicateConventionsRule(EntityRule):
    """ST-005: duplicate conventions forbidden (rules dict keys unique)."""

    @property
    def domain(self) -> str:
        return "style"

    def __init__(self):
        super().__init__(BusinessRuleCode.ST005, severity="error")

    def _validate_entity(self, entity: dict, context: RuleContext) -> list[ValidationErrorDetail]:
        errors = []
        attributes = entity.get("attributes", {})
        rules = attributes.get("rules", {})

        if rules and isinstance(rules, dict):
            seen = set()
            for key in rules.keys():
                normalized = str(key).strip()
                if normalized in seen:
                    errors.append(
                        self._create_error(
                            field="rules",
                            message=f"Duplicate convention key in rules: '{key}'",
                            value=key,
                            instance_path=f"/attributes/rules/{key}",
                        )
                    )
                seen.add(normalized)

        return errors


# Export all style rules
STYLE_RULES = [
    StyleStyleTypeValidRule(),
    StylePatternUniquenessRule(),
    StyleConfidenceRangeRule(),
    StylePriorityNonNegativeRule(),
    StyleDuplicateConventionsRule(),
]