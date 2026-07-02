NTPE 1.0 Beta — Stage-08.1 Runtime Integration
================================================

Status: PASS
Foundation v1.0: Frozen / Backward Compatible
CLI Freeze: Compatible
SDK Stage-07: Compatible

Added:
- integration/runtime_bridge.py
- integration/runtime_manager.py
- integration/runtime_context.py
- integration/runtime_registry.py
- integration/runtime_dispatcher.py
- integration/runtime_events.py
- integration/runtime_models.py
- tests/beta_stage_08_1/launcher_runtime_integration_test.py

Purpose:
Stage-08.1 adds an additive runtime integration layer that connects Runtime,
CLI, SDK, Plugin and Integration Core through a stable bridge/manager/registry
surface. It does not modify frozen Foundation contracts or CLI behavior.

Test:
python tests\beta_stage_08_1\launcher_runtime_integration_test.py
