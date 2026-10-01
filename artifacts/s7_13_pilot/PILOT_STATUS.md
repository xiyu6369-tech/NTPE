# S7-13 Pilot Status

**Status**: `PILOT_BLOCKED`
**Reason**: No real human evaluators are available in this execution environment,
and no real human-evaluation dataset for the S7-11 v1.1 rubric exists in the repository.

**Governance rule applied**: S7-13 §13 — if no real evaluator is available, the pilot
must be reported as `PILOT_BLOCKED`. Fabricated evaluators, LLM-as-human,
developer self-rating, and synthetic labels are prohibited (S7-13 §5, §96).

## What was independently verified (preflight)

| Item | Finding |
|------|---------|
| Real evaluator records (`evaluator_id`) in repo | NONE |
| Filled `evaluation.md` files | NONE (all are identical empty 273-byte templates) |
| Rubric labels (Likert / ACCEPT / REJECT) | NONE |
| Reference translations (GOLD/SILVER/BRONZE) | NONE (sources only; `*_zh.txt` are machine outputs) |
| Approved offline pairwise candidate bundles | NONE |
| Source material available | YES (`tests/literary/**/original_ko.txt`) |
| Machine candidate outputs available | YES (PS-03 regression outputs) — machine, not human reference |

## Directory intent

- `raw/` — intended for immutable raw pilot responses (currently EMPTY; no fabricated data)
- `derived/` — intended for derived analysis tables (currently EMPTY)
- `protocol/` — pilot protocol spec derived from Calibration Design v1.1
- `provenance/` — required provenance/role-separation fields

No raw or derived pilot data exists because the human evaluation was not executed.
