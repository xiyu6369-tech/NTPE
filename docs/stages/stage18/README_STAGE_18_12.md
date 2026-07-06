# NTPE 1.2 Stage-18.12 Translation Name Lock Hotfix

Fixes production translation name drift for locked glossary terms.

Primary verified case:

- `정태의 -> 鄭泰義`
- wrong variants such as `定泰義`, `正太義`, `鄭太義` are normalized back to `鄭泰義`.

## Test

```bat
python ntpe_stage18_12_name_lock_hotfix_test.py
python tests\integration\launcher_stage18_12_name_lock_hotfix_test.py
python tests\smoke\launcher_stage18_12_name_lock_hotfix_smoke_test.py
python ntpe_validate.py
```
