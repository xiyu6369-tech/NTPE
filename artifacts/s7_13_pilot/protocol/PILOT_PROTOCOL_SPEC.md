# S7-13 Pilot Protocol Spec (derived from Calibration Design v1.1)

**Version**: protocol = v1.1 · rubric = v1.1 · pilot_dataset = v0.1 (unpopulated) · analysis = v0.1 (unpopulated)

This document records the protocol that WOULD be used once real evaluators are
available. No evaluation was executed.

## Scope
- Pilot size: 50 passages (`PILOT_ONLY`, not a calibration N).
- Evaluators: 3–5 (pilot design target, not a validated requirement).
- Unit: scene-level passage; chapter-aware; stratified.

## Rubric (v1.1)
7 dimensions × 7-point Likert + binary ACCEPT/REJECT + predefined failure tags:
Naturalness, Fidelity, Character Voice, Register/Tone, Coherence, Terminology,
Added/Missing Detail.

## Presentation contract (blinding)
Evaluators must NOT see: model, provider, attempt number, condition identity,
gold/silver/bronze, prompt version, PS-03 scores, production designation.
Verified by `tools/one_shots/s7_13_pilot_preflight.py` (blinding test).

## Randomization
Passage order, A/B order, and evaluator assignment must be randomized /
counterbalanced. A-first and B-first must both occur (order-balance check).

## Data integrity
- Raw responses immutable once submitted.
- missing / abstain / invalid retained as raw states (no zero/mean fill, no silent drop).
- Duplicate candidate detection required.

## Reference policy
Creator ≠ evaluator on the same evidence unit (reference-conflict check).
Reference classes GOLD / SILVER / BRONZE unchanged.
