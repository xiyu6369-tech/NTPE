NTPE Foundation-06.0 Translation Runtime Contract
=================================================

Purpose:
- Introduce the first translation-specific runtime contract.
- Keep Foundation-05 Production Runtime unchanged.
- Provide a stable bridge from Translation Job to Production Runtime payload.

Added files:
- core/translation/runtime_contract.py
- core/translation/__init__.py
- adapters/translation_runtime_adapter.py
- manifests/translation_runtime_manifest.json
- docs/architecture/foundation/foundation-06-translation-runtime.md
- tests/launcher_translation_runtime_contract_test.py

Test:
cd /d D:\Python\NTPE
python tests\launcher_translation_runtime_contract_test.py

Expected:
PASS
