# TE v7.2 Stage 12.5.6: Authorized Prompt Verification Canary

This stage provides a one-shot, sequential NVIDIA verification harness for only `canary-001`.
It is disabled until a clean-worktree preflight, Stage 12.5.5 readiness evidence, a valid
Stage 12.5.4A artifact hash set, and explicit Stage 12.5.6 authorization all pass.

The budget is exactly two requests: baseline then candidate. Retry, rerun, fallback,
cross-provider fallback, and parallel operation are rejected. A claim is single-use. Candidate
structural findings fail closed for Korean residual/source echo, labels, bilingual or wrapped
output, empty/truncated/malformed output, timeout, and provider errors.

Automated output never makes a quality-improvement claim. Manual review is generated only when
both arms structurally pass. Production, rollout, and formal output replacement remain false.
