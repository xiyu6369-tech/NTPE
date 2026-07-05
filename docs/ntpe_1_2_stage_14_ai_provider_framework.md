# NTPE 1.2 Professional — Stage-14 AI Provider Framework

Stage-14 upgrades `core.ai_provider` from the earlier Beta provider boundary into the formal NTPE 1.2 Professional AI Provider Framework.

## Scope

Supported provider families:

- NVIDIA
- OpenAI
- Gemini
- Anthropic
- Ollama
- OpenRouter
- Custom Provider

## Framework Components

- Provider Registry: provider registration, default provider selection, model discovery, capability lookup.
- Provider Adapter: config-backed adapter base plus deterministic static adapters for offline validation.
- Model Discovery: provider/model metadata exposed through `discover_models()`.
- Capability Detection: serialisable `ProviderCapability` contract.
- Retry Policy: retryable/non-retryable provider error handling with optional backoff.
- Rate Limit: global and per-provider rolling-window limiter.
- Streaming: stable stream chunk interface and runtime bridge support.
- Token Usage: prompt/completion/total token accounting contract.
- Cost Statistics: provider/model-level cost contract and metrics aggregation.
- Health Check: provider health payload with models and capabilities.

## Compatibility

The following earlier APIs are preserved:

- `MockProvider`
- `ProviderRequest`
- `ProviderResponse`
- `ProviderError`
- `ProviderRegistry.register/get/list/default_name`
- `ProviderManager.complete`
- `RuntimeProviderBridge.execute_prompt`
- `build_ai_provider_manifest`

No Foundation v1.0 or NTPE 1.1 LTS frozen module is modified by this Stage.
