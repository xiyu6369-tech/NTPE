# NTPE 1.2 Translation Engine Refactoring v1.1

## Translation Quality Foundation

Focus: improve actual translation quality before adding any non-core features.

### Added / Changed

- Added stricter Name Lock v2 behavior for currently matched glossary terms.
- Added `일레이 -> 伊萊` to locked character dictionary.
- Added common wrong-name alias correction:
  - `伊蕾 -> 伊萊`
  - `伊雷 -> 伊萊`
  - `伊来/伊莱 variants -> 伊萊`
- Improved Dynamic Glossary prompt wording:
  - matched terms are marked as mandatory exact locks.
  - forbidden aliases are explicitly shown only when relevant.
- Improved QA retry prompt:
  - includes exact locked-term failures.
  - tells provider to preserve locked names exactly.
- Kept TER-v1 compact prompt and prompt profiler intact.

### Validation

- `python ntpe_ter_v11_translation_quality_foundation_test.py`
- `python tests\integration\launcher_ter_v11_translation_quality_foundation_test.py`
- `python tests\smoke\launcher_ter_v11_translation_quality_foundation_smoke_test.py`
- `python ntpe_validate.py`

Result: ALL PASS.
