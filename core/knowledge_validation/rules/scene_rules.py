"""
Scene Business Rules
RM-5.7.3B Business Rule Validation Engine

Implements SC-001 through SC-005:
- SC-001: participants unique
- SC-002: boundary_type valid
- SC-003: tone required
- SC-004: scene_id immutable
- SC-005: plot_points unique
"""

from core.knowledge_validation.rules.base import EntityRule, RuleContext
from core.knowledge_validation.validation_codes import BusinessRuleCode
from core.knowledge_validation.validation_result import ValidationErrorDetail


class SceneParticipantsUniqueRule(EntityRule):
    """SC-001: participants unique (by character_id)."""

    @property
    def domain(self) -> str:
        return "scene"

    def __init__(self):
        super().__init__(BusinessRuleCode.SC001, severity="error")

    def _validate_entity(self, entity: dict, context: RuleContext) -> list[ValidationErrorDetail]:
        errors = []
        attributes = entity.get("attributes", {})
        participants = attributes.get("participants", [])

        if participants:
            seen = set()
            for i, participant in enumerate(participants):
                if not isinstance(participant, dict):
                    continue
                char_id = participant.get("character_id")
                if char_id is None:
                    continue
                if char_id in seen:
                    errors.append(
                        self._create_error(
                            field="participants",
                            message=f"Duplicate participant character_id: '{char_id}'",
                            value=participant,
                            instance_path=f"/attributes/participants/{i}",
                        )
                    )
                seen.add(char_id)

        return errors


class SceneBoundaryTypeValidRule(EntityRule):
    """SC-002: boundary_type valid enum."""

    @property
    def domain(self) -> str:
        return "scene"

    VALID_BOUNDARY_TYPES = {
        "same_scene",
        "scene_transition",
        "chapter_transition",
        "volume_transition",
        "time_skip",
        "perspective_shift",
    }

    def __init__(self):
        super().__init__(BusinessRuleCode.SC002, severity="error")

    def _validate_entity(self, entity: dict, context: RuleContext) -> list[ValidationErrorDetail]:
        errors = []
        attributes = entity.get("attributes", {})
        boundary_type = attributes.get("boundary_type")

        if boundary_type is not None and boundary_type not in self.VALID_BOUNDARY_TYPES:
            errors.append(
                self._create_error(
                    field="boundary_type",
                    message=f"Invalid boundary_type '{boundary_type}'. Must be one of: {', '.join(sorted(self.VALID_BOUNDARY_TYPES))}",
                    value=boundary_type,
                    instance_path="/attributes/boundary_type",
                )
            )

        return errors


class SceneToneRequiredRule(EntityRule):
    """SC-003: tone required."""

    @property
    def domain(self) -> str:
        return "scene"

    VALID_TONES = {
        "tense",
        "restrained",
        "heated",
        "atmospheric",
        "neutral",
        "melancholic",
        "joyful",
        "ominous",
        "other",
    }

    def __init__(self):
        super().__init__(BusinessRuleCode.SC003, severity="error")

    def _validate_entity(self, entity: dict, context: RuleContext) -> list[ValidationErrorDetail]:
        errors = []
        attributes = entity.get("attributes", {})
        tone = attributes.get("tone")

        if not tone or not str(tone).strip():
            errors.append(
                self._create_error(
                    field="tone",
                    message="Scene tone is required and cannot be empty",
                    value=tone,
                    instance_path="/attributes/tone",
                )
            )
        elif str(tone).strip() not in self.VALID_TONES:
            errors.append(
                self._create_error(
                    field="tone",
                    message=f"Scene tone must be one of {sorted(self.VALID_TONES)}, got '{tone}'",
                    value=tone,
                    instance_path="/attributes/tone",
                )
            )

        return errors


class SceneSceneIdImmutableRule(EntityRule):
    """SC-004: scene_id immutable (pattern SC-\\d+)."""

    @property
    def domain(self) -> str:
        return "scene"

    def __init__(self):
        super().__init__(BusinessRuleCode.SC004, severity="error")

    def _validate_entity(self, entity: dict, context: RuleContext) -> list[ValidationErrorDetail]:
        errors = []
        attributes = entity.get("attributes", {})
        scene_id = attributes.get("scene_id")

        if scene_id is not None:
            import re
            if not re.match(r"^SC-\d+$", str(scene_id)):
                errors.append(
                    self._create_error(
                        field="scene_id",
                        message=f"scene_id must match pattern 'SC-\\d+', got '{scene_id}'",
                        value=scene_id,
                        instance_path="/attributes/scene_id",
                    )
                )

        return errors


class ScenePlotPointsUniqueRule(EntityRule):
    """SC-005: plot_points unique."""

    @property
    def domain(self) -> str:
        return "scene"

    def __init__(self):
        super().__init__(BusinessRuleCode.SC005, severity="error")

    def _validate_entity(self, entity: dict, context: RuleContext) -> list[ValidationErrorDetail]:
        errors = []
        attributes = entity.get("attributes", {})
        plot_points = attributes.get("plot_points", [])

        if plot_points:
            seen = set()
            for i, plot_point in enumerate(plot_points):
                if plot_point is None:
                    continue
                normalized = str(plot_point).strip()
                if normalized in seen:
                    errors.append(
                        self._create_error(
                            field="plot_points",
                            message=f"Duplicate plot_point: '{plot_point}'",
                            value=plot_point,
                            instance_path=f"/attributes/plot_points/{i}",
                        )
                    )
                seen.add(normalized)

        return errors


# Export all scene rules
SCENE_RULES = [
    SceneParticipantsUniqueRule(),
    SceneBoundaryTypeValidRule(),
    SceneToneRequiredRule(),
    SceneSceneIdImmutableRule(),
    ScenePlotPointsUniqueRule(),
]