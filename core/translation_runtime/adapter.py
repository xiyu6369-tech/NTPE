"""RM-6.2.2 Translation Runtime Adapter.

Bridges the Prompt Runtime and Translation Engine without
modifying either. The adapter consumes a PromptAssembly,
generates a deterministic prompt hash, and packages everything
into an immutable TranslationRequest.

Pipeline:
    MergedRuntime → PromptBuilder → PromptAssembly
    → TranslationRuntimeAdapter.prepare → TranslationRequest

    TranslationRequest is the sole handoff point to Translation Engine.

No provider imports. No network calls. No Translation Engine modifications.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.prompt_runtime.builder import PromptAssembly
from core.translation_runtime.models import (
    TranslationRequest,
    TranslationResponse,
    _deterministic_hash,
    _section_content_hash,
    utc_now_iso,
)


def _assemble_prompt(sections: List[Any]) -> str:
    """Flatten ordered prompt sections into a single prompt string.

    Each section's content is concatenated with section name headers.
    Empty sections are preserved to maintain structural integrity.
    """
    lines: List[str] = []
    for section in sections:
        name = getattr(section, "name", "Section")
        content = getattr(section, "content", "")
        lines.append(f"[{name}]\n{content}\n")
    return "\n".join(lines).strip()


def _compute_prompt_hash(
    assembly: PromptAssembly,
    snapshot_id: str,
    metadata: Dict[str, Any],
) -> str:
    """Compute deterministic prompt hash from assembly and runtime context.

    Hash components:
    - Section name + content (ordered) via _section_content_hash
    - Snapshot ID (knowledge identity)
    - Assembly version

    Same assembly + same snapshot → same hash.
    Different runtime content → different hash.
    """
    sections_data = [s.to_dict() for s in assembly.sections]
    content_hash = _section_content_hash(sections_data)
    return _deterministic_hash(
        content_hash,
        snapshot_id,
        assembly.version,
    )


def _count_tokens_approximate(text: str) -> int:
    """Approximate token count from text length.

    Uses a simple heuristic (~4 chars per token for CJK-heavy text).
    This is a budget-aware approximation — not a provider tokenizer.
    Provider-level tokenization happens in Translation Engine only.
    """
    if not text:
        return 0
    chars = len(text)
    return max(1, chars // 4)


class TranslationRuntimeAdapter:
    """Bridges Prompt Runtime output into Translation Engine input.

    Consumes a PromptAssembly and produces a TranslationRequest
    that Translation Engine can later consume without modification.
    This adapter owns prompt assembly, budget tracking, and metadata
    — keeping Translation Engine purely execution-focused.

    No provider imports. No network. No Translation Engine changes.
    """

    version = "rm-6.2.2"

    def __init__(self):
        self._requests: Dict[str, TranslationRequest] = {}

    def prepare(
        self,
        assembly: PromptAssembly,
        *,
        snapshot_id: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TranslationRequest:
        """Prepare a TranslationRequest from a PromptAssembly.

        This is the primary entry point. It:
        1. Flattens ordered sections into prompt text
        2. Computes deterministic prompt hash
        3. Computes approximate token count
        4. Packages runtime snapshot metadata
        5. Returns immutable TranslationRequest

        Args:
            assembly: PromptAssembly from PromptBuilder.build()
            snapshot_id: Knowledge snapshot identifier
            metadata: Additional runtime metadata

        Returns:
            Immutable TranslationRequest ready for Translation Engine
        """
        base_metadata: Dict[str, Any] = dict(assembly.metadata)
        if metadata:
            base_metadata.update(metadata)

        prompt = _assemble_prompt(assembly.sections)
        prompt_hash = _compute_prompt_hash(assembly, snapshot_id, base_metadata)
        token_count = _count_tokens_approximate(prompt)
        section_count = assembly.section_count
        build_timestamp = utc_now_iso()

        runtime_snapshot: Dict[str, Any] = {
            "prompt_section_count": section_count,
            "prompt_text_length": len(prompt),
            "token_count": token_count,
            "adapter_version": self.version,
            "prompt_hash": prompt_hash,
            "section_order": [s.name for s in assembly.sections],
            "section_versions": [s.version for s in assembly.sections],
        }

        request = TranslationRequest(
            prompt=prompt,
            metadata=base_metadata,
            runtime_snapshot=runtime_snapshot,
            snapshot_id=snapshot_id,
            prompt_hash=prompt_hash,
            section_count=section_count,
            token_count=token_count,
            build_timestamp=build_timestamp,
        )

        self._requests[prompt_hash] = request
        return request

    def prepare_response(
        self,
        request: TranslationRequest,
    ) -> TranslationResponse:
        """Create a response wrapper around a request.

        In RM-6.2.2, this wraps the request without invoking any
        provider or Translation Engine. The response simply carries
        the request forward as a placeholder.

        Args:
            request: The TranslationRequest to wrap

        Returns:
            TranslationResponse containing the request
        """
        return TranslationResponse(
            prompt=request.prompt,
            request=request,
        )

    def get_request(self, prompt_hash: str) -> Optional[TranslationRequest]:
        """Retrieve a previously prepared request by hash."""
        return self._requests.get(prompt_hash)

    def manifest(self) -> Dict[str, Any]:
        return {
            "name": "translation_runtime_adapter",
            "version": self.version,
            "stored_requests": len(self._requests),
            "enabled": True,
        }


__all__ = [
    "TranslationRuntimeAdapter",
]