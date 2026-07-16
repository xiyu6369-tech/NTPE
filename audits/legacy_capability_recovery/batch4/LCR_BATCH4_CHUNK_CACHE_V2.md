# LCR Batch 4 — Chunk Cache V2 Offline Core

Status: **PASS** (including LCR Batch 4.1 Compatibility Fix)

Schema 2.0 provides complete deterministic translation identity, completed-only quality-gated hits, explicit partial/failure evidence, detailed miss/stale reasons, Resume reconciliation, Output Assembly characterization, selective retry planning, invalidation, bounded retention, rollback, corruption detection, and atomic canonical JSON.

The module is offline only. Production Runtime, Provider, Prompt Builder, Resume Journal, Output Assembly, Character Memory V2, Context/Scene Memory, frozen quality baselines, Dual-pass, multilingual profiles, and LCR Batch 5 are unchanged or not started.

Batch 4.1 replaces the ambient system-temp assumption with a mandatory caller-supplied `allowed_root`. Canonically resolved targets must be strict descendants of the resolved root; traversal, absolute escape, root-equality, and symlink escape fail closed. The unit suite passes identically from repository and system-temporary working directories.
