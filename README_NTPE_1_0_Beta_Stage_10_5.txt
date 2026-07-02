NTPE 1.0 Beta — Stage-10.5 Event Bus
=====================================

Status
------
Stage-10.5 adds an in-memory Platform Event Bus for Platform Services.

Scope
-----
- PlatformEvent immutable payload model
- PlatformEventSubscription with exact and wildcard matching
- PlatformEventDelivery records
- PlatformEventBus publish / subscribe / unsubscribe / history
- PlatformEventBridge helper for service-owned event emission
- Public exports from platform_services.__init__

Compatibility
-------------
Foundation v1.0: Frozen-compatible
CLI: Frozen-compatible
SDK: Complete-compatible
Integration: Frozen-compatible
Workflow: Frozen-compatible

Notes
-----
This stage is additive-only. It does not alter frozen runtime, CLI, SDK,
integration, or workflow contracts.

Test
----
python tests/beta_stage_10_5/launcher_event_bus_test.py
