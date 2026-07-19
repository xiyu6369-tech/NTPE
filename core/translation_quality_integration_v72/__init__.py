"""TE v7.2 Milestone A default-off translation-quality integration."""

from .adapter import ACTIVATION_GATE, INTEGRATION_VERSION, apply_to_prompt_package, integrate_prompt
from .budget import BudgetAllocation, allocate_prompt_budget
from .errors import TranslationQualityIntegrationError
from .flags import (
    CHARACTER_FLAG, CONTEXT_SCENE_FLAG, GLOBAL_FLAG, KILL_SWITCH_FLAG,
    NATURALNESS_FLAG, QualityIntegrationFlags,
)
from .models import PromptBudget, QualityIntegrationMetadata, QualityIntegrationRequest, QualityIntegrationResult
from .prompt_contract import PromptContractVerification, scan_dynamic_section, verify_candidate_prompt
from .renderer import NATURALNESS_POLICY

__all__ = [
    "ACTIVATION_GATE", "INTEGRATION_VERSION", "GLOBAL_FLAG", "CHARACTER_FLAG",
    "CONTEXT_SCENE_FLAG", "NATURALNESS_FLAG", "KILL_SWITCH_FLAG",
    "QualityIntegrationFlags", "PromptBudget", "QualityIntegrationRequest",
    "QualityIntegrationMetadata", "QualityIntegrationResult", "BudgetAllocation",
    "PromptContractVerification", "scan_dynamic_section", "verify_candidate_prompt",
    "TranslationQualityIntegrationError", "NATURALNESS_POLICY",
    "allocate_prompt_budget", "integrate_prompt", "apply_to_prompt_package",
]
