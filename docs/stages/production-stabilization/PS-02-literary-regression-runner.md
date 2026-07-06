# PS-02 Literary Regression Runner

PS-02 separates daily translation input from literary regression testing.

## Commands

```bat
python launcher_translate.py corpus list
python launcher_translate.py regression --stage PS-02 --profile literary
python launcher_translate.py regression --set Test_Set_0 --stage PS-02-smoke --dry-run
```

## Rules

- `input/` is for real translation jobs only.
- `tests/literary/Test_Set_0` is the quick smoke corpus.
- `tests/literary/Test_Set_A` is the fixed golden corpus.
- `tests/literary/Test_Set_B` is the rotating regression corpus.
- Outputs are archived under `tests/literary/outputs/<stage>/`.
