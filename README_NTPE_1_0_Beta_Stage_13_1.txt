NTPE 1.0 Beta — Stage-13.1 Web UI Core

Status
------
PASS

Purpose
-------
Stage-13.1 introduces the first Web UI layer for NTPE. The implementation is
framework-neutral and additive: it provides UI shell, route, state, page, and
REST-backed adapter primitives without binding NTPE to a specific web framework.

Added
-----
- web_ui/ui_models.py
- web_ui/ui_shell.py
- web_ui/rest_client.py
- web_ui/web_app.py
- web_ui/__init__.py
- tests/beta_stage_13_1/

Compatibility
-------------
- Foundation v1.0: compatible
- CLI Frozen: compatible
- Integration Frozen: compatible
- Workflow Frozen: compatible
- Platform Services Frozen: compatible
- Runtime API Frozen: compatible
- External API Frozen: compatible

Boundary
--------
The Web UI layer talks only to the External API / REST facade. It does not import
or mutate runtime, workflow, provider, or translation-engine internals.

Test
----
python tests/beta_stage_13_1/launcher_web_ui_core_test.py
python tests/beta_stage_13_1/launcher_translation_validation_stage_13_1_test.py
