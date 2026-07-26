# PS-02 Literary Regression Runner

PS-02 separates daily translation input from literary regression testing.

## Commands

```bat
python launcher_translate.py corpus list
python launcher_translate.py regression --stage PS-02 --profile literary
python launcher_translate.py regression --set Smoke_Set --stage PS-02-smoke --dry-run
```

## Rules

- `input/` is for real translation jobs only.
- `tests/literary/Smoke_Set` is the quick smoke corpus.
- `tests/literary/Golden_Set` is the fixed golden corpus.
- `tests/literary/Regression_Set` is the rotating regression corpus.
- Legacy CLI aliases remain accepted for compatibility:
  `Test_Set_0` maps to `Smoke_Set`, `Test_Set_A` maps to `Golden_Set`, and
  `Test_Set_B` maps to `Regression_Set`. They are not separate corpus
  directories and are not advertised by `corpus list`.
- Outputs are archived under `tests/literary/outputs/<stage>/`.
