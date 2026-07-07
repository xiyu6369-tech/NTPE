# NTPE Literary Regression Corpus

Canonical sets:

- `Smoke_Set`: short smoke corpus for quick API / prompt / name-lock checks.
- `Golden_Set`: fixed golden passage. Do not change after selection.
- `Regression_Set`: rotating passage to prevent overfitting to the golden text.

Legacy CLI names remain accepted for compatibility:

- `Smoke_Set` => `Smoke_Set`
- `Golden_Set` => `Golden_Set`
- `Regression_Set` => `Regression_Set`

Recommended commands:

```bat
python launcher_translate.py regression --set smoke --stage TER-v1 --profile literary --api-timeout 180 --overwrite
python launcher_translate.py regression --set golden --stage TER-v1 --profile literary --api-timeout 180 --overwrite
python launcher_translate.py regression --stage TER-v1 --profile literary --api-timeout 180 --overwrite
```
