NTPE 1.0 Beta — Stage-14.5 Release Validation

Goal
----
Add the release validation layer for NTPE Packaging / Release Layer.

Scope
-----
- Release validation check model
- Release validator
- Release validation JSON report writer / loader
- Artifact layout validation
- Manifest validation
- Distribution package validation
- Frozen API compatibility validation

Compatibility
-------------
This stage is additive only. It does not modify frozen Foundation, CLI,
Workflow, Platform Services, Runtime API, External API, or Web UI public APIs.

Test
----
python tests/beta_stage_14_5/launcher_release_validation_test.py

Expected Result
---------------
PASS
