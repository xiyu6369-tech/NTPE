# LCR Batch 11.0 — Legacy Capability Recovery Governance Freeze

## Release baseline

Batch 11.0 freezes the governance view of the completed LCR capabilities from Batch 2 through Batch 10.9. It adds no translation capability and does not modify any frozen child contract. The immutable registry records 18 capabilities, their real public contracts, evidence paths, rollback strategies, and acyclic dependencies.

## Completed capability chain

- Batch 2–4: Character Memory V2, Context / Scene Memory, and Chunk Cache V2.
- Batch 5–8: Dual-pass Draft / Polish, Post-polish Semantic Verification, Multilingual Profiles, and Controlled Provider Routing.
- Batch 9: Offline Golden / TIC validation.
- Batch 10–10.4: Production Shadow Planning, the single read-only Production Shadow Hook, Character Memory Shadow, Context / Scene Shadow, and Dual-pass Semantic Shadow.
- Batch 10.5–10.6: Explicit Pilot Authorization and Single-chunk Execution Review.
- Batch 10.7: one explicitly authorized real Provider validation attempt.
- Batch 10.8–10.9: Provider Failure Characterization and the frozen Provider Failure Policy.

## Capabilities that remain inactive

Active Production Integration, Production writes, formal translation replacement, automatic rollout, retry, fallback, reusable execution authorization, and any additional Provider execution remain disabled. The repository retains exactly one Production hook, and that hook remains read-only.

## Provider execution history

Batch 10.7 consumed its one-shot execution claim. One Provider request and one network request were attempted; the draft request timed out after the bounded read timeout, polish and semantic verification did not run, and no candidate was created. Formal output, Resume, Cache, Character Store, and Context Store remained unchanged. The consumed claim cannot be reused.

Batch 10.8 deterministically classifies that result as `timeout`, requires manual review, and globally forbids retry and fallback. Batch 10.9 freezes the 19-type taxonomy, policy table, decision engine, execution summary, and read-only review API.

## Responsibility and rollback boundaries

Memory, context, cache, candidate, and review artifacts remain isolated from production stores. A semantic failure rejects the candidate and retains the production translation. Insufficient evidence requires manual review. Shadow behavior can be disabled through the existing kill switch; no second hook is introduced. Policy or source drift is handled by restoring the corresponding frozen child baseline, never by silently relaxing a contract.

## Compatibility policy

The Batch 11.0 registry is additive and read-only. Existing public APIs, schemas, manifests, audits, fixtures, output formats, Resume data, Cache data, and stores remain authoritative and unchanged. Child manifest and source hashes provide transitive evidence for compatibility review.

## Future version rule

The activation gate is `lcr_governance_baseline_frozen`. It is governance evidence only.

Batch 11.0 does not authorize Active Integration. Any Production write, translation replacement, automatic rollout, Provider re-execution, or execution-policy relaxation must use a new version and separate explicit authorization.
