NTPE 1.0 Beta — Stage-09.0 Workflow Core
================================================

Status: PASS
Mode: Additive update
Compatibility: Foundation v1.0 Frozen, CLI Freeze, SDK Stage-07, Integration v1.0 Frozen

Added:
- workflow/workflow_models.py
- workflow/workflow_context.py
- workflow/workflow_registry.py
- workflow/workflow_engine.py
- workflow/workflow_core.py
- workflow/workflow_events.py
- workflow/__init__.py
- tests/beta_stage_09_0/launcher_workflow_core_test.py

Purpose:
Stage-09.0 introduces the Workflow Core layer. It provides workflow definitions,
step registration, dependency-aware execution, context state, event bus bridge,
and service container bridge without modifying frozen Foundation, CLI, SDK, or
Integration contracts.

Test:
python tests\beta_stage_09_0\launcher_workflow_core_test.py
