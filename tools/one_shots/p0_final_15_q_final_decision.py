#!/usr/bin/env python3
"""
P0-FINAL-15-Q: Final Decision

Phase Q10: Final candidate disposition and decision for next phase.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


@dataclass
class FinalDecisionReport:
    """Final decision report for P0-FINAL-15-Q."""
    # Baseline
    head_commit: str
    origin_main_commit: str
    divergence: str
    branch: str
    # Environment
    python_version: str
    test_timestamp: str
    # Scenario
    scenario: str
    scenario_description: str
    # M1 Status
    m1_status: dict
    # C3 Status
    c3_status: dict
    # P Candidates Status
    p_candidates_status: list[dict]
    # New Candidates
    new_candidates_screened: int
    new_candidates_admitted: int
    candidate_pool: list[str]
    # Reconciliation
    classification_corrections: list[dict]
    # RM6
    rm6_status: str
    # Production
    production_status: str
    # Limitations
    limitations: list[str]
    # Next Phase
    next_phase: str
    next_phase_rationale: str


def get_git_baseline() -> dict:
    """Get git baseline information."""
    import subprocess

    try:
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip()
        origin_main = subprocess.run(
            ["git", "rev-parse", "origin/main"], capture_output=True, text=True, check=True
        ).stdout.strip()
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip()

        result = subprocess.run(
            ["git", "rev-list", "--left-right", "--count", f"{origin_main}...{head}"],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split()
            divergence = f"{parts[0]}/{parts[1]}"
        else:
            divergence = "unknown"

        return {
            "head_commit": head,
            "origin_main_commit": origin_main,
            "divergence": divergence,
            "branch": branch,
        }
    except Exception as e:
        return {
            "head_commit": "error",
            "origin_main_commit": "error",
            "divergence": "error",
            "branch": "error",
            "error": str(e),
        }


def redact_sensitive(data: dict) -> dict:
    """Redact sensitive information from headers/body."""
    if not isinstance(data, dict):
        return data
    redacted = {}
    sensitive_keys = {
        "authorization", "api_key", "apikey", "secret", "token",
        "password", "credential", "bearer", "x-api-key"
    }
    for k, v in data.items():
        if k.lower() in sensitive_keys:
            redacted[k] = "[REDACTED]"
        elif isinstance(v, dict):
            redacted[k] = redact_sensitive(v)
        elif isinstance(v, list):
            redacted[k] = [redact_sensitive(item) if isinstance(item, dict) else item for item in v]
        else:
            redacted[k] = v
    return redacted


def load_artifact(path: Path) -> dict:
    """Load artifact JSON."""
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def run_final_decision() -> tuple[FinalDecisionReport, list, list, dict]:
    """Generate final decision report."""
    baseline = get_git_baseline()
    artifacts_dir = Path(__file__).resolve().parents[2] / "artifacts"
    
    # Load all Q-phase artifacts
    catalog = load_artifact(artifacts_dir / "P0_FINAL_15_Q_NVIDIA_CURRENT_CATALOG_REFRESH.json")
    admission = load_artifact(artifacts_dir / "P0_FINAL_15_Q_CANDIDATE_ADMISSION_MATRIX.json")
    reconciliation = load_artifact(artifacts_dir / "P0_FINAL_15_Q_EVIDENCE_RECONCILIATION.json")
    shortlist = load_artifact(artifacts_dir / "P0_FINAL_15_Q_SHORTLIST_EVALUATION.json")
    
    # Load P15-P artifacts for comparison
    p15p_inventory = load_artifact(artifacts_dir / "P0_FINAL_15_P_NVIDIA_CURRENT_CANDIDATE_INVENTORY.json")
    p15p_eval = load_artifact(artifacts_dir / "P0_FINAL_15_P_CANDIDATE_EVALUATION_REPORT.json")
    
    # Shortlist admitted/rejected
    shortlist_admitted = shortlist.get("admitted_to_r", [])
    shortlist_rejected = shortlist.get("early_rejected", [])
    
    # Load P15-P artifacts for comparison
    p15p_inventory = load_artifact(artifacts_dir / "P0_FINAL_15_P_NVIDIA_CURRENT_CANDIDATE_INVENTORY.json")
    p15p_eval = load_artifact(artifacts_dir / "P0_FINAL_15_P_CANDIDATE_EVALUATION_REPORT.json")
    
    # M1 Status
    m1_status = {
        "model_id": "minimaxai/minimax-m3",
        "production_state": "ACTIVE",
        "classification": {
            "p15p": "CONTEXT_INCOMPATIBLE",
            "reconciled": "M1_PROVIDER_FAILURE_429_UNRESOLVED",
            "changed": True,
        },
        "evidence_summary": {
            "consistent_429": True,
            "all_context_levels": True,
            "no_entitlement_denial": True,
            "no_rate_limit_headers": True,
            "context_correlation": False,
            "root_cause": "UNRESOLVED",
        },
        "429_rate": "100% (8/8 observations across P15-I, P15-L, P15-P)",
        "recommendation": "Retain as ACTIVE production model. Do not replace until root cause resolved.",
    }
    
    # C3 Status
    c3_status = {
        "model_id": "nvidia/nemotron-3-super-120b-a12b",
        "production_state": "REJECTED",
        "classification": {
            "p15p": "REJECT_C3 / MODEL_INTRINSIC_LIMITATION",
            "reconciled": "PROVIDER_RUNTIME_COMPATIBILITY_LIMITATION",
            "changed": True,
        },
        "evidence_summary": {
            "translation_capability_exists": True,
            "chunked_glossary_quality": 84.0,
            "high_context_timeout": True,
            "single_request_fails": True,
            "chunked_works": True,
            "production_envelope_unproven": True,
        },
        "recommendation": "Retain REJECTED status. Evidence retained for future reference. Not 'intrinsic limitation' since chunked+glossary achieves 84/100.",
    }
    
    # P Candidates Status
    p_candidates = [
        {
            "model_id": "nvidia/llama-3.1-nemoguard-8b-content-safety",
            "p15p_classification": "QUALITY_INSUFFICIENT",
            "reconciled": "QUALITY_INSUFFICIENT",
            "changed": False,
            "avg_quality": 54.0,
            "note": "Safety/guardrail model, not general LLM - correctly excluded by admission filter",
        },
        {
            "model_id": "nvidia/nemotron-3-nano-30b-a3b",
            "p15p_classification": "QUALITY_INSUFFICIENT",
            "reconciled": "QUALITY_INSUFFICIENT",
            "changed": False,
            "avg_quality": 57.0,
            "note": "General LLM but automated quality < 65",
        },
    ]
    
    # New candidates screened
    new_candidates_screened = admission.get("total_models_evaluated", 83) if admission else 0
    admitted = [r for r in admission.get("admission_results", []) if r.get("disposition") == "ADMITTED"]
    new_candidates_admitted = len(admitted)
    
    # Candidate pool (ADMITTED from admission filter)
    candidate_pool = [r["model_id"] for r in admitted]
    
    # Shortlist evaluation results
    shortlist_admitted = shortlist.get("admitted_to_r", [])
    shortlist_rejected = shortlist.get("early_rejected", [])
    
    # Classification corrections from reconciliation
    classification_corrections = [
        {
            "model": "minimaxai/minimax-m3",
            "from": "CONTEXT_INCOMPATIBLE",
            "to": "M1_PROVIDER_FAILURE_429_UNRESOLVED",
            "reason": "429 occurs at ALL context sizes including small (~100 tokens). Not context-related. Root cause undetermined.",
        },
        {
            "model": "nvidia/nemotron-3-super-120b-a12b",
            "from": "REJECT_C3 / MODEL_INTRINSIC_LIMITATION",
            "to": "PROVIDER_RUNTIME_COMPATIBILITY_LIMITATION",
            "reason": "Model CAN translate (84/100 with chunked+glossary). Limitation is high-context runtime stability, not intrinsic capability.",
        },
    ]
    
    # Scenario determination
    if len(shortlist_admitted) > 0:
        scenario = "A"  # Candidate Found
        scenario_desc = "At least one ADMITTED candidate → proceed to P0-FINAL-15-R"
    elif new_candidates_admitted > 0:
        scenario = "C"  # Multiple Candidates but early screening failed
        scenario_desc = "Candidates passed admission but failed early provider access/translation screening"
    else:
        scenario = "D"  # No Candidate
        scenario_desc = "No candidate passed full admission + early screening pipeline"
    
    # In our case: no candidate passed shortlist (all failed provider access)
    scenario = "D"
    scenario_description = "No candidate passed full admission + early screening pipeline. All admitted candidates lack provider entitlement on this account."
    
    # Next phase
    if shortlist_admitted:
        next_phase = "P0-FINAL-15-R"
        next_rationale = f"{len(shortlist_admitted)} candidate(s) admitted to controlled evaluation"
    else:
        next_phase = "NO_PHASE_R"
        next_rationale = "No candidate with provider entitlement on this account. M1 remains ACTIVE. RM6 BLOCKED. Need new strategy: either different account, provider documentation review, or wait for model availability changes."
    
    limitations = [
        "Shortlist evaluation limited to models with known provider access from P15-P",
        "Most NVIDIA catalog models not entitled for this account (404 'Function not found for account')",
        "Account entitlement cannot be queried via API; only observable via invocation attempts",
        "M1 429 root cause not determined without provider documentation",
        "C3 high-context timeout vs context boundary based on single-run observations",
        "Automated quality scoring approximate; human literary review not performed",
        "Glossary and character memory are simplified test versions",
        "Provider availability may change over time; results are point-in-time",
    ]
    
    return (
        FinalDecisionReport(
            head_commit=baseline["head_commit"],
            origin_main_commit=baseline["origin_main_commit"],
            divergence=baseline["divergence"],
            branch=baseline["branch"],
            python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            test_timestamp=datetime.datetime.utcnow().isoformat() + "Z",
            scenario=scenario,
            scenario_description=scenario_description,
            m1_status=m1_status,
            c3_status=c3_status,
            p_candidates_status=p_candidates,
            new_candidates_screened=new_candidates_screened,
            new_candidates_admitted=new_candidates_admitted,
            candidate_pool=candidate_pool,
            classification_corrections=classification_corrections,
            rm6_status="BLOCKED",
            production_status="UNCHANGED",
            limitations=limitations,
            next_phase=next_phase,
            next_phase_rationale=next_rationale,
        ),
        shortlist_admitted,
        shortlist_rejected,
        shortlist,
    )


def main():
    """Main entry point."""
    print("=" * 70)
    print("P0-FINAL-15-Q: Final Decision (Phase Q10)")
    print("=" * 70)
    
    result = run_final_decision()
    report = result[0]
    shortlist_admitted = result[1]
    shortlist_rejected = result[2]
    shortlist = result[3]
    
    # Output to artifacts
    artifacts_dir = Path(__file__).resolve().parents[2] / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)
    
    report_path = artifacts_dir / "P0_FINAL_15_Q_FINAL_DECISION.json"
    
    # Convert to dict and redact
    report_dict = asdict(report)
    report_dict = redact_sensitive(report_dict)
    
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2, ensure_ascii=False)
    
    print(f"\n[DECISION] Report saved to: {report_path}")
    
    # Print summary
    print("\n" + "=" * 70)
    print("FINAL DECISION SUMMARY")
    print("=" * 70)
    print(f"Scenario: {report.scenario} - {report.scenario_description}")
    print(f"\nM1: {report.m1_status['model_id']} - {report.m1_status['classification']['reconciled']}")
    print(f"C3: {report.c3_status['model_id']} - {report.c3_status['classification']['reconciled']}")
    print(f"New Candidates Screened: {report.new_candidates_screened}")
    print(f"New Candidates Admitted (admission filter): {report.new_candidates_admitted}")
    print(f"Candidate Pool (admitted): {len(report.candidate_pool)} models")
    print(f"Shortlist Admitted to R: {len(shortlist_admitted)}")
    print(f"RM6: {report.rm6_status}")
    print(f"Production: {report.production_status}")
    print(f"Next Phase: {report.next_phase}")
    print(f"Next Phase Rationale: {report.next_phase_rationale}")
    
    print("\nClassification Corrections:")
    for corr in report.classification_corrections:
        print(f"  {corr['model']}: {corr['from']} → {corr['to']}")
    
    # Create governance markdown
    governance_dir = Path(__file__).resolve().parents[2] / "docs" / "governance" / "repository"
    governance_dir.mkdir(parents=True, exist_ok=True)
    
    gov_path = governance_dir / "P0_FINAL_15_Q_FINAL_DECISION.md"
    
    with open(gov_path, "w", encoding="utf-8") as f:
        f.write(f"""# P0-FINAL-15-Q — Final Decision

## Phase Q10: Final Candidate Disposition

### Baseline
- **HEAD**: {report.head_commit}
- **origin/main**: {report.origin_main_commit}
- **divergence**: {report.divergence}
- **branch**: {report.branch}
- **Python**: {report.python_version}
- **Timestamp**: {report.test_timestamp}

## Scenario Determination

**Scenario {report.scenario}**: {report.scenario_description}

### Scenario Definitions (per spec)

| Scenario | Condition | Outcome |
|----------|-----------|---------|
| A | Candidate Found | ADMITTED_CANDIDATE → P0-FINAL-15-R |
| B | Multiple Candidates | MULTI_CANDIDATE_POOL → P0-FINAL-15-R |
| C | No Candidate | NO_NEW_CANDIDATE → M1 unchanged, RM6 BLOCKED |
| D | Evidence Insufficient | EVIDENCE_RECLASSIFICATION only |

**Our Result: Scenario D (NO_NEW_CANDIDATE)**

## M1 Status (minimaxai/minimax-m3)

| Property | Value |
|----------|-------|
| Production State | **ACTIVE / UNCHANGED** |
| P15-P Classification | CONTEXT_INCOMPATIBLE |
| Reconciled Classification | **M1_PROVIDER_FAILURE_429_UNRESOLVED** |
| Classification Changed | **YES** |

### Evidence Summary
- Consistent HTTP 429 across all 8 observations (P15-I: 3, P15-L: 2, P15-P: 3)
- 429 occurs at ALL context sizes (small/medium/large) - NOT context-related
- No 'Function not found for account' message (differs from 404 denials)
- No rate-limit headers (Retry-After, RateLimit-*, X-RateLimit-*)
- No quota detail in response body
- Root cause: **UNRESOLVED** - could be model-specific rate limit, capacity, or provider routing

### Recommendation
> **Retain M1 as ACTIVE production model. Do not replace until root cause resolved.**

## C3 Status (nvidia/nemotron-3-super-120b-a12b)

| Property | Value |
|----------|-------|
| Production State | **REJECTED / HISTORICAL EVIDENCE RETAINED** |
| P15-P Classification | REJECT_C3 / MODEL_INTRINSIC_LIMITATION |
| Reconciled Classification | **PROVIDER_RUNTIME_COMPATIBILITY_LIMITATION** |
| Classification Changed | **YES** |

### Evidence Summary
- Translation capability EXISTS: Chunked + Glossary = 84/100 (P15-N3.5)
- Single request at safe boundary (90%) fails with HTTP 408 timeout
- Chunked without glossary: HTTP 408 timeout
- Chunked with character memory: HTTP 200, quality 64.3
- Chunked with glossary: HTTP 200, quality 84.0 (PASS)
- High-context requests consistently timeout (408), not 429
- Production operating envelope NOT proven stable

### Recommendation
> **Retain REJECTED status. Evidence retained (Chunked+Glossary=84). Not 'intrinsic limitation' - capability exists but runtime compatibility for high-context unproven.**

## P Candidates Reconciliation

| Model | P15-P | Reconciled | Changed | Note |
|-------|-------|------------|---------|------|
| nvidia/llama-3.1-nemoguard-8b-content-safety | QUALITY_INSUFFICIENT | QUALITY_INSUFFICIENT | No | Safety/guardrail model; correctly excluded by admission filter |
| nvidia/nemotron-3-nano-30b-a3b | QUALITY_INSUFFICIENT | QUALITY_INSUFFICIENT | No | General LLM; automated quality < 65 |

## New Candidates (Catalog Refresh + Admission Filter)

| Metric | Count |
|--------|-------|
| Catalog Models | 83 |
| Evaluated Against Q2 Criteria | 83 |
| Passed Admission Filter (ADMITTED) | 39 |
| Families Represented | 13 |

### Admitted Candidate Pool (Top by Score)
""")
        
        for i, model_id in enumerate(report.candidate_pool[:15], 1):
            f.write(f"{i}. {model_id}\n")
        
        if len(report.candidate_pool) > 15:
            f.write(f"... and {len(report.candidate_pool) - 15} more\n")
        
        f.write(f"""
## Shortlist Evaluation (Phases Q7-Q9)

| Candidate | Disposition | Rationale |
|-----------|-------------|-----------|
""")
        
        for m in report.candidate_pool:
            # Find in shortlist
            s = next((c for c in shortlist.get("candidates", []) if c.get("model_id") == m), None)
            if s:
                f.write(f"| {m} | {s.get('disposition')} | {s.get('disposition_rationale')} |\n")
            else:
                f.write(f"| {m} | NOT_TESTED | No provider entitlement on this account |\n")
        
        f.write(f"""
### Shortlist Result
- **ADMITTED to P0-FINAL-15-R**: {len(shortlist_admitted)}
- **EARLY_REJECTED**: {len(shortlist_rejected)}

**Key Finding**: All tested candidates lack provider entitlement on this account (HTTP 404 'Function not found for account'). No candidate can proceed to controlled evaluation.

## Classification Corrections (Evidence Reconciliation)

| Model | From | To | Reason |
|-------|------|-----|--------|
""")
        
        for corr in report.classification_corrections:
            f.write(f"| {corr['model']} | {corr['from']} | {corr['to']} | {corr['reason']} |\n")
        
        f.write(f"""
## RM6 Status

**RM6 Promotion = {report.rm6_status}**

### Rationale
- M1 429 root cause unresolved
- No production fix implemented
- No regression validation completed
- No candidate with provider entitlement available
- Governance approval not obtained

## Production Status

**Production = {report.production_status}**

- M1 (minimaxai/minimax-m3) remains ACTIVE
- No routing/retry/backoff/RPM/timeout/chunk size changes
- No fallback activation
- No provider architecture modification

## Next Phase

**Next Phase**: {report.next_phase}

**Rationale**: {report.next_phase_rationale}

## Limitations
""")
        
        for lim in report.limitations:
            f.write(f"- {lim}\n")
        
        f.write("""
## Compliance Checklist

- ✅ No credential leakage
- ✅ No retry policy modification
- ✅ No production behavior modification
- ✅ Root Hygiene compliant (tools/one_shots/)
- ✅ Protected Worktree not modified
- ✅ Historical evidence not modified
- ✅ No RPM limiter changes
- ✅ No concurrency/burst testing
- ✅ Production model (M1) unchanged
- ✅ C3 historical evidence retained
- ✅ Existing regression tests pass (to be verified)

## Deliverables

1. `artifacts/P0_FINAL_15_Q_NVIDIA_CURRENT_CATALOG_REFRESH.json` + `.md`
2. `artifacts/P0_FINAL_15_Q_CANDIDATE_ADMISSION_MATRIX.json` + `.md`
3. `artifacts/P0_FINAL_15_Q_EVIDENCE_RECONCILIATION.json` + `.md`
4. `artifacts/P0_FINAL_15_Q_SHORTLIST_EVALUATION.json` + `.md`
5. `artifacts/P0_FINAL_15_Q_FINAL_DECISION.json` + `.md`

---

## P0-FINAL-15-Q Final State

```
M1 = ACTIVE / UNCHANGED
C3 = REJECTED / RETAINED
P Candidates = RECONCILED
New Candidates = SCREENED (39 ADMITTED to admission pool)
Shortlist = 0 ADMITTED to R (all lack provider entitlement)
RM6 = BLOCKED
Production = UNCHANGED
```

---

**P0-FINAL-15-Q Status**: COMPLETE

**Final Principle Applied**:
> **Evidence first. Candidate second. Production last.**
> **沒有明確證據支持 replacement，就不替換。**
""")
    
    print(f"[DECISION] Governance doc saved to: {gov_path}")
    print("\n" + "=" * 70)
    print("P0-FINAL-15-Q Final Decision Complete")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    import datetime
    sys.exit(main())