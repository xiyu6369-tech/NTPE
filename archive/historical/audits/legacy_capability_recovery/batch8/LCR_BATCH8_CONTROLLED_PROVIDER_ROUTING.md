# LCR Batch 8 — Controlled Provider Routing Offline Core

Status: **PASS**

Schema 1.0 defines two experimental, credential-free Provider profiles and a deterministic bounded routing policy. Failure classification separates network retry eligibility from quality, semantic, policy, authentication, and invalid-request failures. Retry and cross-Provider fallback require explicit request/timeout budget, compatibility, semantic verification, and manual approval evidence. Academic degraded fallback remains forbidden.

Provider/model/prompt/quality/language-profile identities are separated for cache correctness. Historical 180-second timeout, 503, failed invocation and partial A/B evidence is explicitly historical and never treated as current health. Every execution plan is prepare-only, executed=false, network_requests=0. No SDK, HTTP client, Provider execution, Production integration, or Batch 9 work occurred.
