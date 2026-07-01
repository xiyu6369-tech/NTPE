NTPE Foundation-05.4 Pipeline Lifecycle Manager
================================================

Purpose
-------
Adds the lifecycle layer used by Production Runtime after the Foundation-05.3
scheduler.  This layer standardizes initialization, start, stop, failure,
completion, cleanup, lifecycle counters, lifecycle events, and manifest export.

Files Added
-----------
core/pipeline/lifecycle_manager.py
adapters/pipeline_lifecycle_adapter.py
tests/launcher_pipeline_lifecycle_manager_test.py

Compatibility
-------------
This is an additive update.  It consumes the existing Stage Registry,
Dependency Resolver, and Scheduler contracts without modifying them.

Test
----
python tests\launcher_pipeline_lifecycle_manager_test.py

Expected final output:
PASS
