# Policy: provider_policy

## Title
Provider Policy — AI Provider and Translation Execution Governance

## Purpose
This policy governs all interactions with external AI providers (e.g., OpenAI, Anthropic, DeepSeek) and the execution of translation pipeline runs. These operations are the most sensitive in NTPE—they consume API credits, produce translation outputs, and may affect production systems.

## Scope
- Applies to all agent profiles and all development stages
- Covers provider invocation, translation execution, and network requests
- Violations trigger immediate stop condition (per `.clinerules`)

## Provider Authorization

### Provider Execution is FORBIDDEN by default
AI agents must **never** invoke any AI provider API unless:
- The human user explicitly authorizes a specific provider call, per operation
- The authorization identifies which provider, which model, and the purpose
- The operation is scoped to a single, defined action (not a batch or loop)

### Permitted Provider Operations (with authorization)
- Single inference call for testing a prompt template
- Single translation chunk for quality verification
- Provider connectivity verification (non-inference health check)

### Forbidden Provider Operations (even with authorization)
- Batch translation runs
- Production pipeline execution
- Automated retry loops
- Provider benchmarking without explicit test plan authorization

## Translation Authorization

### Translation Execution is FORBIDDEN by default
AI agents must **never** execute a translation pipeline run unless:
- The human user explicitly authorizes a specific translation run
- The authorization defines: input file, scope (chunks), target language, provider
- The run is for testing/verification purposes, not production

### Permitted Translation Operations (with authorization)
- Single-chunk test translation for quality validation
- Dry-run pipeline execution (no actual API calls)
- Translation configuration validation

### Forbidden Translation Operations
- Production translation runs
- Full-novel translation without explicit per-chunk authorization plan
- Automated retranslation loops

## Network Requests

### Network Requests are FORBIDDEN by default
AI agents must **never** make outbound HTTP/API calls unless:
- The human user explicitly authorizes the specific request
- The request is to a known, project-sanctioned endpoint
- The request does not transmit sensitive data (API keys, tokens, secrets)

## Authorization Format
When authorizing, the human user should specify:
```
AUTHORIZED: [operation type] for [purpose]
Provider: [provider name]
Model: [model name] (if applicable)
Scope: [single call / defined batch / etc.]
```

## Future Update Notes
- May add provider cost tracking and budget enforcement
- Consider adding provider failover policy for production resilience
- Could integrate with provider audit logging