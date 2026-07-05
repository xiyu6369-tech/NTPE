# NTPE 1.2 Professional Stage-14.2

Stage-14.2 adds the Provider Credential / Config Layer on top of the Stage-14 AI Provider Framework and Stage-14.1 runtime binding.

## Scope

- Provider config schema
- Provider profile loading
- Environment variable credential mapping
- Credential registry
- Credential validation
- Secret masking for logs/manifests
- Retry defaults from config
- Rate limit defaults from config
- Runtime config manifest APIs
- Runtime provider config template export

## Default credential environment variables

- NVIDIA: `NVIDIA_API_KEY`
- OpenAI: `OPENAI_API_KEY`
- Gemini: `GEMINI_API_KEY`
- Anthropic: `ANTHROPIC_API_KEY`
- OpenRouter: `OPENROUTER_API_KEY`
- Ollama: `OLLAMA_API_KEY`
- Custom Provider: `NTPE_CUSTOM_PROVIDER_API_KEY`

No secret value is stored in the committed default config.
