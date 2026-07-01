# NTPE Foundation-04.3 Context Contract Stabilization

## Purpose

Foundation-04.3 stabilizes the payload/context contract after Foundation-04.2 Context Migration.

This update is additive and backward-compatible.

## Added Files

- `core/context_contract.py`
- `core/pipeline_contract_adapter.py`
- `tests/launcher_pipeline_context_contract_test.py`

## Contract

The normalized pipeline payload guarantees these top-level keys:

- `source_text`
- `target_language`
- `context`
- `metadata`

Legacy compatibility:

- `text` is migrated to `source_text`
- `language` is migrated to `target_language`
- missing `context` is created
- missing `metadata` is created
- unknown existing keys are preserved

## Test

```bat
python tests\launcher_pipeline_context_contract_test.py
```

Expected result:

```text
NTPE Foundation-04.3 Pipeline Context Contract Test
======================================================
Legacy Normalize     PASS
Target Language      PASS
Context Created      PASS
Metadata Created     PASS
Validate Payload     PASS
Adapter Before       PASS
Adapter After        PASS
Merge Source         PASS
Merge Context        PASS
Merge Metadata       PASS
PASS
```
