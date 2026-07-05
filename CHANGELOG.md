# NTPE 1.2 Professional Stage-14.2

Provider Credential / Config Layer.

- Added `core.ai_provider.config` with ProviderConfigLayer and ProviderProfile.
- Added `core.ai_provider.credentials` with credential registry, environment variable resolution, validation, and secret masking.
- Added `config/provider_config.json` with safe provider defaults and no committed API keys.
- Extended ProviderManager to accept config-backed registry/retry/rate-limit defaults.
- Extended TranslationRuntime with provider config manifest, credential validation, and config template export APIs.
- Preserved Stage-14 and Stage-14.1 compatibility surfaces.
- Added Stage-14.2 validation test.
