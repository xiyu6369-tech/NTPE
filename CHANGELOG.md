## NTPE 1.2 Professional Stage-15.1 - Translation Quality Engine Core

- Added formal Translation Quality Engine Core facade.
- Added quality context/result/rule/registry/pipeline/report/event modules.
- Added default core quality rules for empty output, length ratio, and placeholders.
- Added Stage-15.1 unit, integration, and launcher validation.
- Preserved Foundation v1.0, NTPE 1.1 LTS Frozen, and Stage-14 Provider Framework Freeze compatibility.

# NTPE 1.2 Professional Stage-14.7 Provider Framework Freeze

## Added
- Provider Framework freeze manifest.
- Frozen Provider component list for Stage-14 through Stage-14.6.
- Compatibility guard declarations for Foundation v1.0 and NTPE 1.1 LTS Stable.
- Freeze validation report and assertion helper.
- Stage-14.7 launcher and pytest coverage.

## Compatibility
- Additive-only update.
- Existing Stage-14 / 14.1 / 14.2 / 14.3 / 14.4 / 14.5 / 14.6 imports remain available.
- No Foundation v1.0 files modified.
- No NTPE 1.1 LTS Frozen behavior changed.

## NTPE 1.2 Professional Stage-15.2

- Added Translation Completeness / Missing Segment Detection.
- Added deterministic paragraph/sentence alignment for missing and short segment detection.
- Added completeness quality rules to the default Translation Quality Engine registry.
- Added completeness report export and Stage-15.2 validation launcher.
- Preserved Stage-14 Provider Framework Freeze and Stage-15.1 Quality Engine compatibility.

## NTPE 1.2 Professional — Stage-15.3 Terminology / Character Consistency Engine

- Added terminology and character-name consistency analyzer.
- Added canonical glossary entry model with alias support.
- Added missing canonical translation detection.
- Added alias / translation drift warnings.
- Added terminology quality rule integrated into the default Translation Quality Engine registry.
- Added terminology report serializer.
- Added Stage-15.3 launcher and unit tests.
- Preserved Stage-15.1 and Stage-15.2 backward compatibility.
