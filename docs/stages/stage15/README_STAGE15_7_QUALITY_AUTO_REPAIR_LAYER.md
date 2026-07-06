# NTPE 1.2 Professional — Stage-15.7 Quality Auto Repair Layer

Stage-15.7 adds a deterministic Quality Auto Repair Layer to the Translation Quality Engine.

## Scope

- Safe whitespace and line-ending repair
- Excess blank-line normalization
- Consecutive duplicate line collapse
- Taiwanese dialogue quote normalization
- Explicit glossary replacement
- Placeholder preservation guard
- Repair report serialization
- TranslationQualityEngine repair facade

## Compatibility

This stage only adds new modules and APIs under `core.quality`. Existing Stage-14 Provider Framework Freeze and Stage-15.1–15.6 APIs remain backward compatible.
