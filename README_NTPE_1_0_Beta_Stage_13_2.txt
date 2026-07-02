NTPE 1.0 Beta — Stage-13.2 Web UI Dashboard

Purpose
-------
Adds a framework-neutral dashboard model and dashboard renderer to the Web UI
layer. The dashboard consumes WebUiState from the REST-backed UI client only.
It does not access Runtime, Workflow, Translation Engine, or Platform Services
internals directly.

Added
-----
- web_ui/dashboard_models.py
- web_ui/dashboard.py
- dashboard integration in web_ui/web_app.py
- tests/beta_stage_13_2/

Compatibility
-------------
Foundation v1.0: Frozen compatible
CLI: Frozen compatible
Integration: Frozen compatible
Workflow: Frozen compatible
Platform Services: Frozen compatible
Runtime API: Frozen compatible
External API / REST: Frozen compatible

Tests
-----
python tests/beta_stage_13_2/launcher_web_ui_dashboard_test.py
python tests/beta_stage_13_2/launcher_translation_validation_stage_13_2_test.py
