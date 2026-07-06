# NTPE 1.2 Professional — Stage-15.3 Terminology / Character Consistency Engine

Stage-15.3 adds a deterministic terminology and character-name consistency layer to the Translation Quality Engine.

## Scope

- Glossary-driven terminology validation
- Character canonical-name locking
- Alias / drift detection
- Missing canonical translation detection
- Low canonical coverage warning
- Quality Engine rule integration
- Terminology report serialization

## Added modules

- `core/quality/terminology_consistency.py`
- `core/quality/terminology_rules.py`
- `core/quality/terminology_report.py`

## Added tests

- `tests/unit/test_stage15_3_terminology_consistency.py`
- `tests/stage_15_3/launcher_terminology_consistency_test.py`
- `ntpe_stage15_3_terminology_consistency_test.py`

## Compatibility

This stage only adds optional Stage-15.3 quality components. It does not modify Foundation v1.0, NTPE 1.1 LTS Frozen, or the Stage-14 Provider Framework Freeze contract.
