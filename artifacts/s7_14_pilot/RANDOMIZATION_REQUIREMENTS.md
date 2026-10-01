# NTPE S7-14 Randomization Requirements

**Dependency class**: `EVALUATION_INTERFACE` (randomization)
**Current status**: READY (policy defined; offline check passes)

---

## 1. Randomized Elements

- Passage order
- A/B order (each pair should appear in both orders across evaluators)
- Evaluator assignment (avoid one evaluator seeing all samples)

## 2. Seed Policy & Reproducibility

- Fixed random seed recorded per study.
- Deterministic assignment log produced (split/order reproducible).
- Order-bias logged.

## 3. Counterbalancing

- A-first and B-first must both occur.
- Repeated related pairs limited; same source/variant not shown back-to-back.

## 4. Verification

- `tools/one_shots/s7_13_pilot_preflight.py` `check_order_balance` flags one-sided
  ordering (`ORDER_IMBALANCE`).
- `tools/one_shots/s7_14_pilot_readiness.py` re-checks balance policy presence.

## 5. Assignment Imbalance

- If full balance is impossible, record the assignment design and the imbalance.
