# NTPE 1.2 Translation Engine Refactoring v1

Focus: make translation usable before adding more features.

## Changes

- Renamed literary corpus canonical folders:
  - `Smoke_Set`
  - `Golden_Set`
  - `Regression_Set`
- Kept backward-compatible CLI aliases:
  - `Test_Set_0` => `Smoke_Set`
  - `Test_Set_A` => `Golden_Set`
  - `Test_Set_B` => `Regression_Set`
- Rebuilt Literary Prompt Engine as compact v3:
  - shorter fixed policy
  - dynamic glossary limited to terms present in current chunk
  - compact character and narrative hints
  - compact previous-context tail
- Added prompt profiler output in live progress:
  - total / system / policy / context / glossary / source token estimate
- Updated literary regression and evaluation to use canonical set names.

## Commands

```bat
python launcher_translate.py corpus list
python launcher_translate.py regression --set smoke --stage TER-v1 --profile literary --api-timeout 180 --overwrite
python launcher_translate.py regression --set golden --stage TER-v1 --profile literary --api-timeout 180 --overwrite
python launcher_translate.py regression --stage TER-v1 --profile literary --api-timeout 180 --overwrite
```

Legacy commands still work:

```bat
python launcher_translate.py regression --set Test_Set_A --stage TER-v1 --profile literary --api-timeout 180 --overwrite
```
