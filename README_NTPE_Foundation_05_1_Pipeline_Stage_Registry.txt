NTPE Foundation-05.1 Pipeline Stage Registry

Purpose
- Adds a production pipeline stage registry contract.
- Supports stage registration, lookup, enable/disable, priority sorting, handler query, manifest export/import, and adapter access.
- Designed as an incremental addition after Foundation-05.0.

Files
- core/pipeline/stage_registry.py
- adapters/pipeline_stage_registry_adapter.py
- tests/launcher_pipeline_stage_registry_test.py

Test
cd /d D:\Python\NTPE
python tests\launcher_pipeline_stage_registry_test.py

Expected result
PASS
