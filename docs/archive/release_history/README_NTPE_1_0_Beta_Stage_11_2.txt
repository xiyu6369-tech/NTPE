NTPE 1.0 Beta — Stage-11.2 Runtime Session API

Summary
-------
Stage-11.2 adds an additive Runtime Session API on top of the Stage-11.1
Runtime API Core.

Added
-----
- runtime_api/runtime_session.py
- runtime_api/session_api.py
- tests/beta_stage_11_2/

Capabilities
------------
- Session creation
- Session lookup
- Session listing
- Session lifecycle state transitions
- Session resume-state snapshot
- Runtime API operation registration
- Backward compatibility with Stage-11.1 Runtime API Core

Compatibility
-------------
- Foundation v1.0: preserved
- CLI: preserved
- SDK: preserved
- Integration: preserved
- Workflow: preserved
- Platform Services: preserved
- Stage-11.1 Runtime API Core: preserved

No frozen surface is modified.
