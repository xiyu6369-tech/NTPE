"""
Narrative Business Rules
RM-5.7.3B Business Rule Validation Engine

Implements NA-001 through NA-005:
- NA-001: event_type valid
- NA-002: impact_level valid
- NA-003: timeline ordering valid (single entity only)
- NA-004: affected_characters unique
- NA-005: world_rule immutable
"""

from core.knowledge_validation.rules.base import EntityRule, RuleContext
from core.knowledge_validation.validation_codes import BusinessRuleCode
from core.knowledge_validation.validation_result import ValidationErrorDetail


class NarrativeEventTypeValidRule(EntityRule):
    """NA-001: event_type valid for plot_point type."""

    @property
    def domain(self) -> str:
        return "narrative"

    VALID_PLOT_TYPES = {
        "inciting",
        "rising",
        "climax",
        "falling",
        "resolution",
        "revelation",
        "twist",
        "setup",
    }

    VALID_MILESTONE_TYPES = {
        "breakthrough",
        "relationship",
        "revelation",
        "loss",
        "achievement",
        "transformation",
    }

    VALID_WORLD_RULE_CATEGORIES = {
        "cultivation_system",
        "magic_system",
        "political_structure",
        "geography",
        "history",
        "technology",
        "social_custom",
    }

    def __init__(self):
        super().__init__(BusinessRuleCode.NA001, severity="error")

    def _validate_entity(self, entity: dict, context: RuleContext) -> list[ValidationErrorDetail]:
        errors = []
        attributes = entity.get("attributes", {})
        narrative_type = attributes.get("narrative_type")

        if narrative_type == "plot_point":
            plot_point = attributes.get("plot_point", {})
            plot_type = plot_point.get("type")
            if plot_type and plot_type not in self.VALID_PLOT_TYPES:
                errors.append(
                    self._create_error(
                        field="plot_point.type",
                        message=f"Invalid plot_point type '{plot_type}'. Must be one of: {', '.join(sorted(self.VALID_PLOT_TYPES))}",
                        value=plot_type,
                        instance_path="/attributes/plot_point/type",
                    )
                )

        elif narrative_type == "character_milestone":
            milestone = attributes.get("character_milestone", {})
            milestone_type = milestone.get("milestone_type")
            if milestone_type and milestone_type not in self.VALID_MILESTONE_TYPES:
                errors.append(
                    self._create_error(
                        field="character_milestone.milestone_type",
                        message=f"Invalid milestone_type '{milestone_type}'. Must be one of: {', '.join(sorted(self.VALID_MILESTONE_TYPES))}",
                        value=milestone_type,
                        instance_path="/attributes/character_milestone/milestone_type",
                    )
                )

        elif narrative_type == "world_rule":
            world_rule = attributes.get("world_rule", {})
            category = world_rule.get("category")
            if category and category not in self.VALID_WORLD_RULE_CATEGORIES:
                errors.append(
                    self._create_error(
                        field="world_rule.category",
                        message=f"Invalid world_rule category '{category}'. Must be one of: {', '.join(sorted(self.VALID_WORLD_RULE_CATEGORIES))}",
                        value=category,
                        instance_path="/attributes/world_rule/category",
                    )
                )

        return errors


class NarrativeImpactLevelValidRule(EntityRule):
    """NA-002: impact_level valid (1-10 for character_milestone)."""

    @property
    def domain(self) -> str:
        return "narrative"

    def __init__(self):
        super().__init__(BusinessRuleCode.NA002, severity="error")

    def _validate_entity(self, entity: dict, context: RuleContext) -> list[ValidationErrorDetail]:
        errors = []
        attributes = entity.get("attributes", {})
        narrative_type = attributes.get("narrative_type")

        if narrative_type == "character_milestone":
            milestone = attributes.get("character_milestone", {})
            impact_level = milestone.get("impact_level")

            if impact_level is not None:
                try:
                    level = int(impact_level)
                    if level < 1 or level > 10:
                        errors.append(
                            self._create_error(
                                field="character_milestone.impact_level",
                                message=f"Impact level must be between 1 and 10, got {level}",
                                value=impact_level,
                                instance_path="/attributes/character_milestone/impact_level",
                            )
                        )
                except (ValueError, TypeError):
                    errors.append(
                        self._create_error(
                            field="character_milestone.impact_level",
                            message=f"Impact level must be an integer, got {type(impact_level).__name__}",
                            value=impact_level,
                            instance_path="/attributes/character_milestone/impact_level",
                        )
                    )

        return errors


class NarrativeTimelineOrderingRule(EntityRule):
    """NA-003: timeline ordering valid (single entity only - events must have increasing position)."""

    @property
    def domain(self) -> str:
        return "narrative"

    def __init__(self):
        super().__init__(BusinessRuleCode.NA003, severity="error")

    def _validate_entity(self, entity: dict, context: RuleContext) -> list[ValidationErrorDetail]:
        errors = []
        attributes = entity.get("attributes", {})
        narrative_type = attributes.get("narrative_type")

        if narrative_type == "timeline":
            timeline = attributes.get("timeline", {})
            events = timeline.get("events", [])

            if events:
                last_position = None
                for i, event in enumerate(events):
                    if not isinstance(event, dict):
                        continue
                    position = event.get("position")
                    if position is None:
                        continue
                    try:
                        pos = float(position)
                        if last_position is not None and pos <= last_position:
                            errors.append(
                                self._create_error(
                                    field="timeline.events",
                                    message=f"Timeline event at index {i} has position {pos} which is not greater than previous position {last_position}",
                                    value=event,
                                    instance_path=f"/attributes/timeline/events/{i}/position",
                                )
                            )
                        last_position = pos
                    except (ValueError, TypeError):
                        errors.append(
                            self._create_error(
                                field="timeline.events",
                                message=f"Event position must be a number at index {i}",
                                value=position,
                                instance_path=f"/attributes/timeline/events/{i}/position",
                            )
                        )

        return errors


class NarrativeAffectedCharactersUniqueRule(EntityRule):
    """NA-004: affected_characters unique for plot_point."""

    @property
    def domain(self) -> str:
        return "narrative"

    def __init__(self):
        super().__init__(BusinessRuleCode.NA004, severity="error")

    def _validate_entity(self, entity: dict, context: RuleContext) -> list[ValidationErrorDetail]:
        errors = []
        attributes = entity.get("attributes", {})
        narrative_type = attributes.get("narrative_type")

        if narrative_type == "plot_point":
            plot_point = attributes.get("plot_point", {})
            affected = plot_point.get("affected_characters", [])

            if affected:
                seen = set()
                for i, char_id in enumerate(affected):
                    if char_id is None:
                        continue
                    normalized = str(char_id).strip()
                    if normalized in seen:
                        errors.append(
                            self._create_error(
                                field="plot_point.affected_characters",
                                message=f"Duplicate affected character_id: '{char_id}'",
                                value=char_id,
                                instance_path=f"/attributes/plot_point/affected_characters/{i}",
                            )
                        )
                    seen.add(normalized)

        return errors


class NarrativeWorldRuleImmutableRule(EntityRule):
    """NA-005: world_rule immutable (rule_id pattern WR-\\d+)."""

    @property
    def domain(self) -> str:
        return "narrative"

    def __init__(self):
        super().__init__(BusinessRuleCode.NA005, severity="error")

    def _validate_entity(self, entity: dict, context: RuleContext) -> list[ValidationErrorDetail]:
        errors = []
        attributes = entity.get("attributes", {})
        narrative_type = attributes.get("narrative_type")

        if narrative_type == "world_rule":
            world_rule = attributes.get("world_rule", {})
            rule_id = world_rule.get("rule_id")

            if rule_id is not None:
                import re
                if not re.match(r"^WR-\d+$", str(rule_id)):
                    errors.append(
                        self._create_error(
                            field="world_rule.rule_id",
                            message=f"world_rule rule_id must match pattern 'WR-\\d+', got '{rule_id}'",
                            value=rule_id,
                            instance_path="/attributes/world_rule/rule_id",
                        )
                    )

        return errors


# Export all narrative rules
NARRATIVE_RULES = [
    NarrativeEventTypeValidRule(),
    NarrativeImpactLevelValidRule(),
    NarrativeTimelineOrderingRule(),
    NarrativeAffectedCharactersUniqueRule(),
    NarrativeWorldRuleImmutableRule(),
]