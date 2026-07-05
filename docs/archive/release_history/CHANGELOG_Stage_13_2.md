# NTPE 1.0 Beta — Stage-13.2 Web UI Dashboard

## Added
- Framework-neutral DashboardMetric, DashboardSection, and DashboardView models.
- WebUiDashboard builder for dashboard metrics and sections.
- Dashboard component integration in WebUiApp.render("/").
- Dashboard manifest metadata.
- Stage-13.2 dashboard tests and translation validation guard.

## Changed
- web_ui/__init__.py exports dashboard public surface.
- web_ui/web_app.py includes dashboard view generation.

## Compatibility
- Uses External API / REST only.
- Uses frozen Runtime API only through the frozen REST surface.
- Does not modify Runtime, Workflow, Translation Engine, Provider, or Platform Services internals.

## Tests
- Stage-13.2 Web UI Dashboard: PASS
- Translation Validation Stage-13.2: PASS
- Stage-13.1 Web UI Core: PASS
- Stage-12.8 External API Freeze: PASS
