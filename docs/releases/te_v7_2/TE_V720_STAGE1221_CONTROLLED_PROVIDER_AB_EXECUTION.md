# TE v7.2 Stage 12.2.1 — Controlled Provider A/B Execution

## Result

The explicitly authorized execution used the frozen Stage 12.2 package and existing NVIDIA transport. Baseline was sent once with model `meta/llama-3.3-70b-instruct`, a 180-second timeout, zero retries, no fallback, an 800-token output limit and the exact `Golden_Set:1` source unit.

Baseline timed out after 180.305 seconds. The failure was preserved with `success=false`, `exception_category=timeout`, one network request and no translation. It was not retried.

Because the Stage 12.2 workflow requires a usable pair for human A/B comparison, Candidate was not sent after the Baseline failure. The final execution state is `ab_pair_incomplete`: Baseline requests 1, Candidate requests 0, total network requests 1.

## Artifact handling

Each arm has a request record, prompt profile, sanitized raw-response record, translation file and execution metadata. No raw prompt, API key, Authorization header or response header was persisted. The existing NVIDIA client exposes normalized translation text rather than the HTTP response envelope; the sanitized raw-response record therefore contains the normalized result, status and failure category.

Both `translation.txt` files are intentionally empty. No text was fabricated for the failed or unexecuted arm.

The manual review template remains unfilled. No automatic scoring, winner selection, comparison, quality claim or Candidate acceptance occurred.

## Frozen boundaries

Stage 12.1 Candidate and Stage 12.2 artifacts remain anchored by their original manifests. Prompt, Candidate, Runtime, Provider, model, timeout, retry and translation strategy were not modified. Stage 12.3 was not started.

Final boundary: `real_provider_executed=true`, `network_requests=1`, `new_translation_generated=false`, `comparison_executed=false`, `manual_review_completed=false`, `quality_improvement_verified=false`, and `quality_candidate_accepted=false`.
