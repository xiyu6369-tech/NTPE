# Conflict-of-Interest Rules (Template — Specification Only)

## Hard rule
`Reference Creator ≠ Evaluator` for the same evidence unit.
An editor/generator must not evaluate their own candidate.

## Roles
Reference Creator · Evaluator · Study Administrator · Data Analyst.

## Multi-role
If one person holds several roles, an explicit conflict policy is required and logged.

## Enforcement
`creator_id` vs `evaluator_id` disjointness checked at intake.
Conflict → `PILOT RECORD INVALID` (never silently dropped to raise agreement).
