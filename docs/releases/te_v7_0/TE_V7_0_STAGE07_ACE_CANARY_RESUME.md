# TE v7.0 Stage 07 — ACE Canary Resume and Provider-Failure Decoupling

Adds opt-in resume seeding for completed chunks before the canary target. It copies only successful prior chunk outputs and matching resume metadata from an earlier regression stage. Missing or unsafe chunks fail closed. Provider, prompt, QA and frozen TE v6 code are unchanged.

CLI: `--ace-canary-resume-from-stage <stage>`.
