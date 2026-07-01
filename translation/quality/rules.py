from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class QualityRuleSet:
    locale: str = "zh-TW"
    require_no_korean_residue: bool = True
    require_locked_terms: bool = True
    min_score: float = 0.72
    custom_rules: Dict[str, str] = field(default_factory=dict)

    def list_rules(self) -> List[str]:
        rules = ["semantic", "consistency", "style", "repair", "scoring"]
        rules.extend(self.custom_rules.keys())
        return rules
