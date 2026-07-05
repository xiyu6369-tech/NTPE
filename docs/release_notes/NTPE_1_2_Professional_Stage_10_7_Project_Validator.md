# NTPE 1.2 Professional — Stage-10.7 Project Validator

## Purpose

Add a root-level automated project validator for checking NTPE project health after cleanup, archive, and structure reorganization stages.

## Added

- `ntpe_validate.py`
- `tests/validation/test_ntpe_validate.py`

## Validation Coverage

- Required project directories
- Legacy entrypoints
- Core imports
- Optional imports
- Python compile pass
- Python cache artifacts
- Pytest-style test inventory
- Root Python layout sanity check

## Usage

```bat
python ntpe_validate.py
```

Optional full pytest run:

```bat
python ntpe_validate.py --pytest
```

Optional JSON report:

```bat
python ntpe_validate.py --json reports/validation_report.json
```
