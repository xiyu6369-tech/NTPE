# NTPE 1.2 Professional — Stage-11 Plugin Marketplace Interface

Stage-11 adds a package/repository/installer interface for NTPE plugins.

## Architecture Boundary

- Marketplace manages plugin packages and metadata.
- Registry governs enabled runtime plugins.
- Runtime executes plugins.
- Session/Pipeline/Runtime imports remain unchanged.

## Gate Review

- Build: PASS
- Unit Test: PASS
- Integration Test: PASS
- Regression Test: PASS
- Architecture Review: PASS
- Backward Compatibility: PASS

## Compatibility

Legacy entrypoints remain unchanged. Foundation v1.0 and NTPE 1.1 LTS are not modified.
