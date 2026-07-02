# NTPE 1.0 Beta - Stage-11.7 Runtime Middleware

## Added
- Runtime middleware descriptor and lifecycle state.
- Middleware registration, listing, enable / disable, remove, summary, and wrapped execution API.
- Before, after, and error hook support.
- Ordered middleware execution by priority.
- Stage-11.7 tests and compatibility guard.

## Changed
- `runtime_api/__init__.py` exports the additive middleware public surface.

## Compatibility
- Foundation v1.0: preserved.
- CLI: preserved.
- SDK: preserved.
- Integration: preserved.
- Workflow: preserved.
- Platform Services: preserved.
- Runtime API Core / Session / Job / Pipeline / Event / Resource APIs: preserved.

## Test Result
PASS
