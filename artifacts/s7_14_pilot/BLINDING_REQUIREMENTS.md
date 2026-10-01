# NTPE S7-14 Blinding Requirements

**Dependency class**: `EVALUATION_INTERFACE` (blinding)
**Current status**: READY (presentation contract defined; offline check passes)

---

## 1. Fields Evaluators Must Never See

`model`, `provider`, `attempt_number`, `production_designation`, `reference_class`
(gold/silver/bronze), `prompt_version`, `condition` identity, `ps03_score`.

## 2. Presentation-Layer Transformation

- Strip all forbidden metadata before rendering.
- Present source + candidate only (and reference only under an explicit labeled
  "alternative translation" condition).
- Pairwise: present "A" / "B" with randomized order; hide which is which.

## 3. Verification

- `tools/one_shots/s7_13_pilot_preflight.py` `check_blinding` detects forbidden fields
  in a presentation payload (`BLINDING_LEAK`).
- `tools/one_shots/s7_14_pilot_readiness.py` re-checks the blinding transformation.

## 4. Deviation Handling

- If blinding cannot be achieved technically, record a `BLINDING_FAILURE` deviation,
  estimate impact, and do not claim "fully blinded".
