NTPE 1.0 Beta — Stage-12.7 REST Middleware / Auth Hooks
========================================================

Status
------
PASS

Purpose
-------
Stage-12.7 adds an additive REST middleware and authentication hook layer on top
of the existing External API / REST facade.

Scope
-----
Added:
- external_api/rest_middleware.py
- external_api/rest_auth.py
- tests/beta_stage_12_7/
- CHANGELOG_Stage_12_7.md
- Translation_Validation_Report_Stage_12_7.md

Updated:
- external_api/rest_api.py
- external_api/__init__.py

Compatibility
-------------
- Foundation v1.0: compatible
- CLI Frozen: compatible
- SDK: compatible
- Integration Frozen: compatible
- Workflow Frozen: compatible
- Platform Services Frozen: compatible
- Runtime API Frozen: compatible
- REST Session/Job/Pipeline/Event/Resource APIs: compatible

Design Notes
------------
Authentication is opt-in. With no auth hook installed, REST behavior remains
unchanged for backward compatibility.

Middleware is opt-in. Before middleware may short-circuit a request, and after
middleware may annotate or transform the response envelope.

No hard-coded auth provider is introduced in this stage. Token, API key, RBAC,
ABAC, and OAuth integration remain future extension points.

Tests
-----
python tests/beta_stage_12_7/launcher_rest_middleware_auth_test.py
python tests/beta_stage_12_7/launcher_translation_validation_stage_12_7_test.py

Expected Result
---------------
PASS
