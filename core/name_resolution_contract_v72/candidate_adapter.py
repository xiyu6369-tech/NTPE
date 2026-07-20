from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .models import NameResolutionRecord
from .renderer import RenderingEvidence, render_prompt_mappings


DEFAULT_ENABLED = False
UNRESOLVED_NAME_OUTPUT_STRATEGY = "blocked_pending_policy"


@dataclass(frozen=True)
class CandidateAdapterResult:
    prompt: str
    enabled: bool
    prompt_changed: bool
    rendering_evidence: dict[str, object] | None
    provider_payload_changed: bool = False
    production_hook_count_added: int = 0
    runtime_request_path_modified: bool = False


def apply_name_resolution_candidate(
    prompt: str,
    records: Iterable[NameResolutionRecord],
    *,
    enabled: bool = DEFAULT_ENABLED,
    token_budget: int = 128,
) -> CandidateAdapterResult:
    if not enabled:
        return CandidateAdapterResult(prompt, False, False, None)
    rendered, evidence = render_prompt_mappings(records, token_budget=token_budget)
    policy = (
        "【未解析人物姓名政策】\n"
        "- 不得保留 Hangul；不得輸出部分翻譯或混合 script 姓名；不得自行創造正式中文譯名。\n"
        f"- unresolved_name_output_strategy={UNRESOLVED_NAME_OUTPUT_STRATEGY}"
    )
    addition = "\n".join(item for item in (rendered, policy) if item)
    candidate = prompt if not addition else prompt + "\n" + addition
    return CandidateAdapterResult(candidate, True, candidate != prompt, evidence.to_dict())
