# NTPE 1.2 Professional — Stage-15.5 Formatting / Structure Integrity Engine

Stage-15.5 adds deterministic formatting and structure validation to the Translation Quality Engine.

## Scope

- Paragraph count drift detection
- Dialogue marker drift detection
- Unbalanced delimiter detection for 「」, 『』, parentheses and brackets
- Placeholder preservation checks
- Chapter marker preservation checks
- Invalid control character detection
- Oversized line and paragraph-collapse warning
- TQE rule integration through `StructureIntegrityRule`
- Report output through `StructureIntegrityReport`

## Compatibility

This stage is additive only. It does not modify Foundation v1.0, NTPE 1.1 LTS Frozen, Stage-14 Provider Framework Freeze, or previous Stage-15 public APIs.

## Verification

Run:

```bash
python ntpe_stage15_5_structure_integrity_test.py
pytest tests/unit/test_stage15_5_structure_integrity.py
python ntpe_validate.py
```
