import pathlib

# Read current file
content = pathlib.Path('d:/Python/NTPE/core/knowledge_validation/rules/narrative_rules.py').read_text(encoding='utf-8')

# Find and replace the incomplete NarrativeImpactLevelValidRule class
old = '''class NarrativeImpactLevelValidRule(EntityRule):
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

class NarrativeTimelineOrderingRule(EntityRule):'''

new = '''class NarrativeImpactLevelValidRule(EntityRule):
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


class NarrativeTimelineOrderingRule(EntityRule):'''

content = content.replace(old, new)
pathlib.Path('d:/Python/NTPE/core/knowledge_validation/rules/narrative_rules.py').write_text(content, encoding='utf-8')
print('Done')