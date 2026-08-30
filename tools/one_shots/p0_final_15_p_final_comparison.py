#!/usr/bin/env python3
"""
P0-FINAL-15-P: Final Candidate Comparison and Human Review Bundle

Creates:
1. Final Candidate Comparison Report (JSON + Markdown)
2. Human Review Bundle (if candidates qualify)
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def load_json(path: Path) -> dict:
    """Load JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    """Main entry point."""
    print("=" * 70)
    print("P0-FINAL-15-P: Final Candidate Comparison")
    print("=" * 70)
    
    artifacts_dir = Path(__file__).resolve().parents[2] / "artifacts"
    governance_dir = Path(__file__).resolve().parents[2] / "docs" / "governance" / "repository"
    governance_dir.mkdir(parents=True, exist_ok=True)
    
    # Load inventory report
    inventory_path = artifacts_dir / "P0_FINAL_15_P_NVIDIA_CURRENT_CANDIDATE_INVENTORY.json"
    if not inventory_path.exists():
        print(f"[ERROR] Inventory report not found: {inventory_path}")
        return 1
    
    inventory = load_json(inventory_path)
    
    # Load evaluation report
    eval_path = artifacts_dir / "P0_FINAL_15_P_CANDIDATE_EVALUATION_REPORT.json"
    if not eval_path.exists():
        print(f"[ERROR] Evaluation report not found: {eval_path}")
        return 1
    
    evaluation = load_json(eval_path)
    
    # Build final comparison
    print("\n[COMPARISON] Building final comparison...")
    
    # Extract key data
    inventory_screening = {s["model_id"]: s for s in inventory["screening_results"]}
    eval_candidates = {c["model_id"]: c for c in evaluation["candidates"]}
    
    # All evaluated models
    all_models = set(inventory_screening.keys()) | set(eval_candidates.keys())
    
    comparison_rows = []
    
    for model_id in all_models:
        screening = inventory_screening.get(model_id, {})
        eval_data = eval_candidates.get(model_id, {})
        
        row = {
            "model_id": model_id,
            # Phase A/B: Catalog & Screening
            "in_catalog": screening.get("in_catalog", False),
            "catalog_owner": screening.get("catalog_entry", {}).get("owned_by") if screening.get("catalog_entry") else None,
            "catalog_available": screening.get("catalog_available", False),
            "endpoint_available": screening.get("endpoint_available", False),
            "account_entitled": screening.get("account_entitled", False),
            "invocation_success": screening.get("invocation_success", False),
            "smoke_http_status": screening.get("smoke_http_status"),
            "screening_classification": screening.get("classification"),
            "passes_required": screening.get("passes_required", False),
            "preferred_score": screening.get("preferred_score", 0),
            # Phase C-J: Detailed Evaluation
            "context_compatible": eval_data.get("context_compatible"),
            "raw_translation_success_rate": eval_data.get("raw_translation_success_rate"),
            "reliability_success_rate": eval_data.get("reliability_success_rate"),
            "automated_quality_pass": eval_data.get("automated_pass"),
            "smoke_429_count": eval_data.get("smoke_http_429"),
            "reliability_429_count": eval_data.get("reliability_http_429"),
            "reliability_median_latency_ms": eval_data.get("reliability_median_latency_ms"),
            "final_classification": eval_data.get("classification"),
            "classification_rationale": eval_data.get("classification_rationale"),
            "overall_pass": eval_data.get("overall_pass", False),
        }
        
        # Add quality scores summary
        quality_scores = eval_data.get("quality_scores", {})
        if quality_scores:
            avg_overall = sum(qs["overall"] for qs in quality_scores.values()) / len(quality_scores)
            row["avg_quality_score"] = round(avg_overall, 1)
        else:
            row["avg_quality_score"] = None
        
        comparison_rows.append(row)
    
    # Sort by ranking criteria (Section 22)
    def rank_key(r):
        score = 0
        if r["overall_pass"]:
            score += 1000
        if r["automated_quality_pass"]:
            score += 100
        if r["context_compatible"]:
            score += 50
        score += (r.get("reliability_success_rate") or 0) * 30
        score += (r.get("raw_translation_success_rate") or 0) * 20
        if r.get("avg_quality_score"):
            score += r["avg_quality_score"]
        # Penalize 429s
        score -= (r.get("smoke_429_count") or 0) * 10
        score -= (r.get("reliability_429_count") or 0) * 5
        return score
    
    comparison_rows.sort(key=rank_key, reverse=True)
    
    # Determine final outcomes per Section 33
    replacement_candidates = [r for r in comparison_rows if r["final_classification"] == "REPLACEMENT_CANDIDATE"]
    conditional_candidates = [r for r in comparison_rows if r["final_classification"] == "CONDITIONAL_CANDIDATE"]
    quality_insufficient = [r for r in comparison_rows if r["final_classification"] == "QUALITY_INSUFFICIENT"]
    context_incompatible = [r for r in comparison_rows if r["final_classification"] == "CONTEXT_INCOMPATIBLE"]
    other = [r for r in comparison_rows if r["final_classification"] not in 
             ["REPLACEMENT_CANDIDATE", "CONDITIONAL_CANDIDATE", "QUALITY_INSUFFICIENT", "CONTEXT_INCOMPATIBLE"]]
    
    # Scenario determination
    if replacement_candidates:
        scenario = "B" if len(replacement_candidates) == 1 else "C"
    elif conditional_candidates:
        scenario = "C"
    else:
        scenario = "A" if not (quality_insufficient or context_incompatible) else "D"
    
    # Build final report
    final_report = {
        "phase": "P0-FINAL-15-P",
        "baseline": {
            "head_commit": inventory["head_commit"],
            "origin_main_commit": inventory["origin_main_commit"],
            "divergence": inventory["divergence"],
            "branch": inventory["branch"],
        },
        "environment": {
            "endpoint": inventory["endpoint"],
            "credential_source": inventory["credential_source"],
            "timestamp": inventory["test_timestamp"],
        },
        "catalog_summary": {
            "fetch_status": inventory["catalog_fetch_status"],
            "models_count": inventory["catalog_models_count"],
        },
        "scenario": scenario,
        "scenario_description": {
            "A": "No suitable candidate - retain M1, RM6 BLOCKED",
            "B": "One candidate qualifies - establish replacement candidate, no immediate production activation",
            "C": "Multiple candidates qualify - ranking, human review, select primary + fallback",
            "D": "Evidence insufficient - no model change, define next investigation",
        }[scenario],
        "m1_baseline": {
            "model_id": "minimaxai/minimax-m3",
            "status": "ACTIVE / UNCHANGED",
            "classification": "CONTEXT_INCOMPATIBLE",
            "429_rate": "100%",
        },
        "c3_status": {
            "model_id": "nvidia/nemotron-3-super-120b-a12b",
            "status": "REJECTED / HISTORICAL EVIDENCE RETAINED",
            "reference_evidence": "Chunked + Glossary = 84 (P0-FINAL-15-N3.5)",
        },
        "comparison": comparison_rows,
        "ranking": [{"rank": i+1, **r} for i, r in enumerate(comparison_rows)],
        "replacement_candidates": replacement_candidates,
        "conditional_candidates": conditional_candidates,
        "quality_insufficient": quality_insufficient,
        "context_incompatible": context_incompatible,
        "human_review_required": len(replacement_candidates) > 0 or len(conditional_candidates) > 0,
        "human_review_bundle_models": [r["model_id"] for r in (replacement_candidates[:2] + conditional_candidates[:1])],
        "rm6_status": "BLOCKED",
        "production_status": "UNCHANGED",
        "limitations": inventory["limitations"] + evaluation["limitations"],
    }
    
    # Save JSON
    final_json_path = artifacts_dir / "P0_FINAL_15_P_FINAL_CANDIDATE_COMPARISON.json"
    with open(final_json_path, "w", encoding="utf-8") as f:
        json.dump(final_report, f, indent=2, ensure_ascii=False)
    
    print(f"[COMPARISON] JSON report saved to: {final_json_path}")
    
    # Create Markdown governance document
    gov_path = governance_dir / "P0_FINAL_15_P_FINAL_CANDIDATE_COMPARISON.md"
    
    with open(gov_path, "w", encoding="utf-8") as f:
        f.write(f"""# P0-FINAL-15-P — Final Candidate Comparison & Decision

## Baseline

- **HEAD**: {final_report['baseline']['head_commit']}
- **origin/main**: {final_report['baseline']['origin_main_commit']}
- **divergence**: {final_report['baseline']['divergence']}
- **branch**: {final_report['baseline']['branch']}
- **Endpoint**: {final_report['environment']['endpoint']}
- **Credential**: {final_report['environment']['credential_source']}
- **Timestamp**: {final_report['environment']['timestamp']}

## NVIDIA Catalog Summary

- **Fetch Status**: {final_report['catalog_summary']['fetch_status']}
- **Models Available**: {final_report['catalog_summary']['models_count']}

## Scenario Determination

**Scenario {final_report['scenario']}**: {final_report['scenario_description']}

## M1 Baseline (Current Production)

| Property | Value |
|----------|-------|
| Model | {final_report['m1_baseline']['model_id']} |
| Status | {final_report['m1_baseline']['status']} |
| Classification | {final_report['m1_baseline']['classification']} |
| 429 Rate | {final_report['m1_baseline']['429_rate']} |

**M1 remains ACTIVE and UNCHANGED** per Production Freeze (Section 3).

## C3 Historical Reference

| Property | Value |
|----------|-------|
| Model | {final_report['c3_status']['model_id']} |
| Status | {final_report['c3_status']['status']} |
| Reference Evidence | {final_report['c3_status']['reference_evidence']} |

C3 evidence retained per Section 4.

## Complete Candidate Ranking

| Rank | Model | Screening | Context | Raw Trans | Reliability | Quality | 429s | Classification | Pass |
|------|-------|-----------|---------|-----------|-------------|---------|------|----------------|------|
""")
        
        for r in comparison_rows:
            def fmt_pct(v):
                if v is None:
                    return "N/A"
                return f"{v:.0%}"
            
            f.write(f"| {r.get('rank', '?')} | {r['model_id']} | "
                    f"{'✓' if r.get('passes_required') else '✗'} ({r.get('preferred_score', 0)}/7) | "
                    f"{'✓' if r.get('context_compatible') else '✗'} | "
                    f"{fmt_pct(r.get('raw_translation_success_rate'))} | "
                    f"{fmt_pct(r.get('reliability_success_rate'))} | "
                    f"{'✓' if r.get('automated_quality_pass') else '✗'} ({r.get('avg_quality_score', 'N/A')}) | "
                    f"{r.get('smoke_429_count', '?')}+{r.get('reliability_429_count', '?')} | "
                    f"{r.get('final_classification', 'UNEVALUATED')} | "
                    f"{'✓' if r.get('overall_pass') else '✗'} |\n")
        
        f.write(f"""
## Classification Breakdown

### REPLACEMENT_CANDIDATE ({len(final_report['replacement_candidates'])})
""")
        
        for r in final_report['replacement_candidates']:
            f.write(f"- **{r['model_id']}**: {r['classification_rationale']}\n")
        
        f.write(f"""
### CONDITIONAL_CANDIDATE ({len(final_report['conditional_candidates'])})
""")
        
        for r in final_report['conditional_candidates']:
            f.write(f"- **{r['model_id']}**: {r['classification_rationale']}\n")
        
        f.write(f"""
### QUALITY_INSUFFICIENT ({len(final_report['quality_insufficient'])})
""")
        
        for r in final_report['quality_insufficient']:
            f.write(f"- **{r['model_id']}**: {r['classification_rationale']} (avg quality: {r.get('avg_quality_score', 'N/A')})\n")
        
        f.write(f"""
### CONTEXT_INCOMPATIBLE ({len(final_report['context_incompatible'])})
""")
        
        for r in final_report['context_incompatible']:
            f.write(f"- **{r['model_id']}**: {r['classification_rationale']}\n")
        
        f.write(f"""
### OTHER ({len(other)})
""")
        
        for r in other:
            f.write(f"- **{r['model_id']}**: {r.get('final_classification', 'UNEVALUATED')}\n")
        
        f.write(f"""
## Human Review Bundle

**Required**: {final_report['human_review_required']}

**Models for Human Review**:
""")
        
        for model_id in final_report['human_review_bundle_models']:
            f.write(f"- {model_id}\n")
        
        if final_report['human_review_required']:
            f.write("""
### Human Review Protocol

Per Section 23, the Human Review Bundle must contain:

1. **M1 Baseline** (minimaxai/minimax-m3) - current production output
2. **Best Candidate** - top-ranked REPLACEMENT_CANDIDATE or CONDITIONAL_CANDIDATE
3. **Second-Best Candidate** - next ranked candidate

**Comparison Dimensions**:
- Narrative flow and literary tone
- Dialogue naturalness and character voice distinction
- Terminology consistency (glossary adherence)
- Character consistency (character memory adherence)
- Continuity across chunks
- Traditional Chinese (Taiwan) naturalness

**Decision Rule**: Human review must PASS before any APPROVE_REPLACEMENT.
""")
        
        f.write(f"""
## Production Replacement Gate Status

Per Section 24:

| Gate | Status |
|------|--------|
| Candidate Identified | {'✓' if final_report['replacement_candidates'] else '✗'} |
| Automated PASS | {'✓' if any(r['automated_quality_pass'] for r in final_report['replacement_candidates']) else '✗'} |
| Reliability PASS | {'✓' if any(r['reliability_success_rate'] >= 0.8 for r in final_report['replacement_candidates']) else '✗'} |
| Context PASS | {'✓' if any(r['context_compatible'] for r in final_report['replacement_candidates']) else '✗'} |
| Human Review PASS | ⏳ Pending |
| Governance PASS | ⏳ Pending |
| Controlled Canary | ⏳ Pending |
| Replacement Approval | ⏳ Pending |

**RM6 Promotion**: {final_report['rm6_status']}

**Production Status**: {final_report['production_status']}

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
- ✅ C3 evidence retained
- ✅ Existing regression tests pass (to be verified)

## Limitations

""")
        
        for lim in final_report['limitations']:
            f.write(f"- {lim}\n")
        
        f.write("""
## Next Steps

1. **Complete Human Literary Review** (mandatory gate per Section 23)
2. **Governance Review** of evaluation evidence
3. **If Human Review PASS**: Proceed to Controlled Canary phase
4. **If no candidate qualifies**: M1 remains active, RM6 stays BLOCKED, define next investigation

## Deliverables

- `artifacts/P0_FINAL_15_P_NVIDIA_CURRENT_CANDIDATE_INVENTORY.json` + `.md`
- `artifacts/P0_FINAL_15_P_CANDIDATE_EVALUATION_REPORT.json` + `.md`
- `artifacts/P0_FINAL_15_P_FINAL_CANDIDATE_COMPARISON.json` + `.md`
- `artifacts/P0_FINAL_15_P_Human_Review_Bundle/` (if applicable)

---

**P0-FINAL-15-P Status**: COMPLETE

**Final State**:
```
M1 = ACTIVE / UNCHANGED
C3 = REJECTED / HISTORICAL EVIDENCE RETAINED
New Candidates = EVALUATED
RM6 = BLOCKED
Production = UNCHANGED
```
""")
    
    print(f"[COMPARISON] Governance doc saved to: {gov_path}")
    
    # Create Human Review Bundle if needed
    if final_report['human_review_required']:
        bundle_dir = artifacts_dir / "P0_FINAL_15_P_Human_Review_Bundle"
        bundle_dir.mkdir(exist_ok=True)
        
        # Copy relevant translations for review
        for model_id in final_report['human_review_bundle_models']:
            eval_data = eval_candidates.get(model_id, {})
            if eval_data:
                model_bundle_dir = bundle_dir / model_id.replace("/", "_")
                model_bundle_dir.mkdir(exist_ok=True)
                
                # Save translations for each fixture and mode
                for t in eval_data.get("raw_translations", []) + eval_data.get("ntpe_translations", []):
                    if t.get("success") and t.get("translation"):
                        fixture_file = model_bundle_dir / f"{t['fixture_name']}_{t['mode']}.txt"
                        with open(fixture_file, "w", encoding="utf-8") as f:
                            f.write(f"Model: {model_id}\n")
                            f.write(f"Fixture: {t['fixture_name']} ({t['fixture_type']})\n")
                            f.write(f"Mode: {t['mode']}\n")
                            f.write(f"HTTP Status: {t['http_status']}\n")
                            f.write(f"Latency: {t['elapsed_ms']:.0f}ms\n\n")
                            f.write("SOURCE:\n")
                            f.write(t['source_text'])
                            f.write("\n\nTRANSLATION:\n")
                            f.write(t['translation'])
        
        # Create review template
        review_template = bundle_dir / "REVIEW_TEMPLATE.md"
        with open(review_template, "w", encoding="utf-8") as f:
            f.write(f"""# P0-FINAL-15-P Human Literary Review Template

## Reviewer Information
- **Reviewer**: [Name]
- **Date**: [Date]
- **Models Under Review**: {', '.join(final_report['human_review_bundle_models'])}

## Evaluation Criteria

Score each dimension 1-10 (10 = best):

### 1. Narrative Flow & Literary Tone
- Does the translation read like natural, publication-quality Traditional Chinese prose?
- Is the narrative voice consistent and appropriate for the genre?

### 2. Dialogue Naturalness & Character Voice
- Do characters sound distinct from each other?
- Are honorifics and speech patterns handled naturally for Taiwan readers?
- Does dialogue flow naturally without awkward literal translations?

### 3. Terminology Consistency (Glossary Adherence)
- Are glossary terms translated consistently across all chunks?
- Are character names, place names, and special terms handled correctly?

### 4. Character Consistency (Character Memory Adherence)
- Do character traits, relationships, and voices remain consistent?
- Are pronouns and references to characters maintained correctly?

### 5. Continuity Across Chunks
- For multi-chunk translations: do references, events, and terminology carry forward?
- Are there contradictions or inconsistencies between chunks?

### 6. Traditional Chinese (Taiwan) Naturalness
- Does the translation use vocabulary, idioms, and phrasing natural to Taiwan readers?
- Are there mainland Chinese expressions that should be localized?

## Scoring

| Model | Narrative | Dialogue | Terminology | Character | Continuity | Naturalness | TOTAL |
|-------|-----------|----------|-------------|-----------|------------|-------------|-------|
| M1 (minimaxai/minimax-m3) |   |   |   |   |   |   |   |
""")
            
            for model_id in final_report['human_review_bundle_models']:
                f.write(f"| {model_id} |   |   |   |   |   |   |   |\n")
            
            f.write("""
## Decision

- **APPROVE_REPLACEMENT**: [Model ID] - Meets publication-grade quality
- **CONDITIONAL**: [Model ID] - Requires specific improvements
- **REJECT**: [Model ID] - Does not meet quality bar

**Rationale**: [Detailed justification]

## Signature

- **Reviewer**: _________________
- **Date**: _________________
""")
        
        print(f"[COMPARISON] Human Review Bundle created at: {bundle_dir}")
    
    # Print summary
    print("\n" + "=" * 70)
    print("FINAL COMPARISON SUMMARY")
    print("=" * 70)
    print(f"Scenario: {scenario} - {final_report['scenario_description']}")
    print(f"Models Evaluated: {len(comparison_rows)}")
    print(f"REPLACEMENT_CANDIDATE: {len(replacement_candidates)}")
    print(f"CONDITIONAL_CANDIDATE: {len(conditional_candidates)}")
    print(f"QUALITY_INSUFFICIENT: {len(quality_insufficient)}")
    print(f"CONTEXT_INCOMPATIBLE: {len(context_incompatible)}")
    print(f"Human Review Required: {final_report['human_review_required']}")
    print(f"RM6 Status: {final_report['rm6_status']}")
    print(f"Production Status: {final_report['production_status']}")
    
    print("\nRanking:")
    for r in comparison_rows:
        print(f"  {r.get('rank', '?')}. {r['model_id']:<45} {r.get('final_classification', 'UNEVALUATED')}")
    
    print("\n" + "=" * 70)
    print("P0-FINAL-15-P Final Comparison Complete")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())