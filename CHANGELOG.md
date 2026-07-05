# Changelog — NTPE 1.2 Professional Stage-14.3

## Added

- `ProviderRuntimeExecutionPolicy`
- `ExecutionContext`
- `ExecutionResult`
- `ExecutionLimits`
- `ExecutionRetryPolicy` and `ExecutionRetryState`
- `ExecutionScheduler`
- `ExecutionStatistics`
- `ExecutionHookRegistry`
- `ExecutionEvent` and `ExecutionEventBus`
- Stage-14.3 launcher and pytest coverage

## Changed

- `ProviderManager` now delegates provider execution to the execution policy while preserving public return types.
- `core.ai_provider.__init__` exports the Stage-14.3 runtime policy APIs.

## Compatibility

No frozen Foundation v1.0 or NTPE 1.1 LTS files are modified.
