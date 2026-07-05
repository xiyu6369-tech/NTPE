NTPE 1.0 Beta — Stage-14.6 Release Freeze

Goal
----
Freeze the NTPE 1.0 Beta Packaging / Release Layer.

Scope
-----
- Release freeze record model
- Release freezer
- Release freeze manifest writer / loader
- Final release validation recheck
- Final frozen component list
- Final packaging/release compatibility guard

Compatibility
-------------
This stage is additive only. It does not modify frozen Foundation, CLI,
Workflow, Platform Services, Runtime API, External API, Web UI, or packaging
public APIs from earlier Stage-14 milestones.

Test
----
python tests/beta_stage_14_6/launcher_release_freeze_test.py

Expected Result
---------------
PASS
