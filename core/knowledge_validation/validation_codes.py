"""
Business Rule Validation Codes
RM-5.7.3B Business Rule Validation Engine

Enumeration of all business rule validation codes.
Each domain has its own prefix:
- CH: Character rules
- GL: Glossary rules
- SC: Scene rules
- NA: Narrative rules
- ST: Style rules
"""

from enum import Enum


class BusinessRuleCode(str, Enum):
    """Business rule validation codes."""

    # Character Rules (CH)
    CH001 = "CH001"  # canonical_name required, cannot be empty
    CH002 = "CH002"  # aliases must not contain canonical_name
    CH003 = "CH003"  # duplicate aliases forbidden
    CH004 = "CH004"  # confidence must satisfy 0 ≤ confidence ≤ 1
    CH005 = "CH005"  # status must be one of schema enum

    # Glossary Rules (GL)
    GL001 = "GL001"  # source unique
    GL002 = "GL002"  # locked term immutable
    GL003 = "GL003"  # forbidden_forms cannot contain target
    GL004 = "GL004"  # alias duplicates forbidden
    GL005 = "GL005"  # confidence range

    # Scene Rules (SC)
    SC001 = "SC001"  # participants unique
    SC002 = "SC002"  # boundary_type valid
    SC003 = "SC003"  # tone required
    SC004 = "SC004"  # scene_id immutable
    SC005 = "SC005"  # plot_points unique

    # Narrative Rules (NA)
    NA001 = "NA001"  # event_type valid
    NA002 = "NA002"  # impact_level valid
    NA003 = "NA003"  # timeline ordering valid (single entity only)
    NA004 = "NA004"  # affected_characters unique
    NA005 = "NA005"  # world_rule immutable

    # Style Rules (ST)
    ST001 = "ST001"  # style_type valid
    ST002 = "ST002"  # pattern uniqueness
    ST003 = "ST003"  # confidence range
    ST004 = "ST004"  # priority non-negative
    ST005 = "ST005"  # duplicate conventions forbidden

    @classmethod
    def get_domain(cls, code: str) -> str | None:
        """Get domain prefix from code."""
        if code.startswith("CH"):
            return "character"
        elif code.startswith("GL"):
            return "glossary"
        elif code.startswith("SC"):
            return "scene"
        elif code.startswith("NA"):
            return "narrative"
        elif code.startswith("ST"):
            return "style"
        return None

    @classmethod
    def list_by_domain(cls, domain: str) -> list["BusinessRuleCode"]:
        """List all codes for a domain."""
        prefix_map = {
            "character": "CH",
            "glossary": "GL",
            "scene": "SC",
            "narrative": "NA",
            "style": "ST",
        }
        prefix = prefix_map.get(domain.lower())
        if not prefix:
            return []
        return [code for code in cls if code.value.startswith(prefix)]