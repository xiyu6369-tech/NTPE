AI_PROVIDER_MANIFEST = {
    "name": "NTPE AI Provider Framework",
    "stage": "NTPE 1.2 Professional Stage-14",
    "version": "1.0-beta-stage-03",
    "framework_version": "1.2-professional-stage-14.2",
    "frozen_dependencies": ["NTPE 1.0 Stable", "NTPE 1.1 LTS Stable"],
    "features": [
        "provider_registry",
        "provider_adapter",
        "model_discovery",
        "capability_detection",
        "retry_policy",
        "rate_limit",
        "streaming",
        "token_usage",
        "cost_statistics",
        "health_check",
        "runtime_bridge",
        "custom_provider",
        "provider_config_schema",
        "credential_registry",
        "environment_variable_credentials",
        "provider_profiles",
        "secret_masking",
        "credential_validation",
    ],
    "standard_providers": ["nvidia", "openai", "gemini", "anthropic", "ollama", "openrouter", "custom"],
    "compatibility": {
        "stage_03_api_preserved": True,
        "mock_provider_preserved": True,
        "runtime_bridge_execute_prompt_preserved": True,
        "stage_14_1_runtime_binding_preserved": True,
    },
}


def build_ai_provider_manifest(extra=None):
    data = dict(AI_PROVIDER_MANIFEST)
    if extra:
        data.update(extra)
    return data
