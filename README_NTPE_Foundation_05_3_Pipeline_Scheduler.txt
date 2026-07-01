NTPE Foundation-05.3 Pipeline Scheduler
======================================

Purpose
-------
Adds an incremental scheduler layer that converts Foundation-05.2 dependency
plans into stable execution schedules for future lifecycle/runtime modules.

Added files
-----------
core/pipeline/scheduler.py
adapters/pipeline_scheduler_adapter.py
tests/launcher_pipeline_scheduler_test.py
README_NTPE_Foundation_05_3_Pipeline_Scheduler.txt

Compatibility
-------------
- Does not remove or overwrite Foundation-04.x / 05.0 / 05.1 / 05.2 behavior.
- Accepts legacy schedule items as strings or dicts.
- Keeps disabled/blocked stage information in schedule manifests.

Test
----
python tests\launcher_pipeline_scheduler_test.py
