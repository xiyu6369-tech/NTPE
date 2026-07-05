# NTPE 1.2 Professional Stage-14.6

Provider Security / Secret Protection layer.

## Scope

Stage-14.6 adds a provider security boundary on top of Stage-14.5 without changing existing Provider, Runtime Binding, Config, Execution Policy, Load Balancer, or Observability APIs.

## Added

- Secret protection runtime
- Secret protection policy manifest
- Log-safe text redaction
- Nested payload redaction
- Secret fingerprinting for audits
- Environment variable name allow-list validation
- Plaintext secret scanner for config/log files
- Stage-14.6 launcher and pytest coverage

## Compatibility

- Stage-14 Provider Framework preserved
- Stage-14.1 Runtime Binding preserved
- Stage-14.2 Config Layer preserved
- Stage-14.3 Execution Policy preserved
- Stage-14.4 Load Balancer preserved
- Stage-14.5 Observability preserved
- NTPE 1.0 Stable and NTPE 1.1 LTS remain frozen
