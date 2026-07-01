# Foundation-06.4 Prompt Runtime

Prompt Runtime converts a validated Translation Context Bundle into a versioned Prompt Package.

Flow:

```text
Translation Segment
  -> Context Bundle
  -> Prompt Template
  -> Prompt Package
  -> Model Adapter
```

The runtime is non-destructive: it copies dictionaries, normalizes legacy prompt data, and attaches `prompt_package` to payloads without removing existing payload fields.

Core contracts:

- `translation_prompt_template`
- `translation_prompt_package`
- `prompt_runtime` manifest
- `PromptRuntimeAdapter`

The default prompt package contains OpenAI-compatible/NVIDIA-compatible `messages` with `system` and `user` roles.
