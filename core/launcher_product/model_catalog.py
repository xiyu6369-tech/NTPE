from __future__ import annotations

from .models import ModelDefinition


MODELS = (
    ModelDefinition(
        model_id="meta/llama-3.2-90b-vision-instruct",
        provider_id="nvidia",
        display_name="Llama 3.3 70B Instruct",
        enabled=True,
        experimental=False,
        recommended_for=("literary", "balanced"),
        context_notes="Static catalog entry used by the existing NVIDIA CLI.",
    ),
    ModelDefinition(
        model_id="gemini-2.5-flash",
        provider_id="gemini",
        display_name="Gemini 2.5 Flash",
        enabled=False,
        experimental=True,
        recommended_for=("planned",),
        context_notes="Catalogued only; launcher execution is not integrated in Stage 1.",
    ),
)


def model_catalog() -> tuple[ModelDefinition, ...]:
    return MODELS


def get_model(model_id: str) -> ModelDefinition | None:
    return next((model for model in MODELS if model.model_id == model_id), None)
