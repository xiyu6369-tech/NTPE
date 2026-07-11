# TE v4.0 Stage-4.0.1 Translation Reliability Baseline

This stage adds a side-effect-free reliability classifier and report builder.

It records and classifies:
- HTTP 429/500/503
- read/connect timeout
- connection/SSL/JSON errors
- provider_attempts=0
- empty output
- too-short output
- Hangul residue
- retry exhaustion
- success

It does not modify or call Provider Runtime, Translation Runtime, launcher, HTTP clients, or API keys.

## Validation

```powershell
python apply_stage_401.py
python ntpe_te_v40_stage401_translation_reliability_baseline_test.py
python -m pytest tests\integration\translation_reliability_stage401_baseline_test.py -q
python ntpe_validate.py
```
