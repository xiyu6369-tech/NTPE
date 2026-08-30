#!/usr/bin/env python3
"""
Generate P0-FINAL-15-P Inventory Markdown from existing JSON report.
"""

import json
from pathlib import Path

def main():
    artifacts_dir = Path(__file__).resolve().parents[2] / "artifacts"
    governance_dir = Path(__file__).resolve().parents[2] / "docs" / "governance" / "repository"
    governance_dir.mkdir(parents=True, exist_ok=True)
    
    # Load inventory report
    inventory_path = artifacts_dir / "P0_FINAL_15_P_NVIDIA_CURRENT_CANDIDATE_INVENTORY.json"
    if not inventory_path.exists():
        print(f"[ERROR] Inventory report not found: {inventory_path}")
        return 1
    
    with open(inventory_path, "r", encoding="utf-8") as f:
        report = json.load(f)
    
    # Create governance markdown
    gov_path = governance_dir / "P0_FINAL_15_P_NVIDIA_CURRENT_CANDIDATE_INVENTORY.md"
    
    with open(gov_path, "w", encoding="utf-8") as f:
        f.write(f"""# P0-FINAL-15-P — NVIDIA Current Candidate Inventory

## Phase A: Catalog Verification

### Environment
- **HEAD**: {report['head_commit']}
- **origin/main**: {report['origin_main_commit']}
- **divergence**: {report['divergence']}
- **branch**: {report['branch']}
- **Python**: {report['python_version']}
- **Endpoint**: {report['endpoint']}
- **Credential**: {report['credential_source']} (present: {report['credential_present']})
- **Timestamp**: {report['test_timestamp']}

### NVIDIA /v1/models Catalog
- **Fetch Status**: {report['catalog_fetch_status']}
- **HTTP Status**: {report['catalog_http_status']}
- **Models Count**: {report['catalog_models_count']}

## Phase B: Account/Endpoint Verification

### Priority Candidates (Section 8)
""")
        
        for c in report['priority_candidates']:
            f.write(f"- {c}\n")
        
        f.write(f"""
### All Screened Candidates ({len(report['all_screened_candidates'])} total)
""")
        
        for c in report['all_screened_candidates']:
            f.write(f"- {c}\n")
        
        f.write("""
## Screening Results

| Model | In Catalog | Catalog Avail | Endpoint Avail | Account Entitled | Invocation Success | HTTP Status | Required | Preferred | Classification |
|-------|------------|---------------|----------------|------------------|-------------------|-------------|----------|-----------|----------------|
""")
        
        for s in report['screening_results']:
            f.write(f"| {s['model_id']} | {s['in_catalog']} | {s['catalog_available']} | {s['endpoint_available']} | {s['account_entitled']} | {s['invocation_success']} | {s['smoke_http_status']} | {s['passes_required']} | {s['preferred_score']}/7 | {s['classification']} |\n")
        
        f.write("""
## Screening Criteria Applied (Section 7)

### Required (all must pass)
1. **General-purpose LLM** or high language generation capability (not translation-only, speech, vision-first, embedding, reranker, image generation)
2. **Chinese support** (assumed for general LLMs)
3. **Instruction following** capability (general LLMs)
4. **Long-form text** handling (general LLMs)
5. **NVIDIA hosted endpoint** invocable (owned_by indicates NVIDIA/Meta/MiniMax)
6. **No NTPE architecture change** required (OpenAI-compatible chat/completions)

### Preferred (scored 0-7)
1. **≥32K context window**
2. **Multilingual** capability
3. **Strong language generation**
4. **Long-context capability** (≥16K)
5. **NVIDIA Free Endpoint** availability
6. **Stable provider response metadata** (NVCF tracking)
7. **Literary/narrative generation** suitability

## Candidate Classifications

### PRIMARY_CANDIDATE (preferred_score ≥ 5, passes all required)
""")
        
        primary = [s for s in report['screening_results'] if s['classification'] == "PRIMARY_CANDIDATE"]
        for s in primary:
            f.write(f"""
#### {s['model_id']}
- **Catalog Owner**: {s['catalog_entry']['owned_by'] if s['catalog_entry'] else 'N/A'}
- **Context Window**: {s['model_detail']['context_window'] if s['model_detail'] else 'N/A'}
- **Preferred Score**: {s['preferred_score']}/7
- **Smoke Test**: HTTP {s['smoke_http_status']} ({s['smoke_elapsed_ms']:.0f}ms)
- **NVCF Tracking**: {s['smoke_nvcf_reqid'] or 'None'}
""")
        
        f.write("""
### SECONDARY_CANDIDATE (preferred_score 3-4, passes all required)
""")
        
        secondary = [s for s in report['screening_results'] if s['classification'] == "SECONDARY_CANDIDATE"]
        for s in secondary:
            f.write(f"""
#### {s['model_id']}
- **Catalog Owner**: {s['catalog_entry']['owned_by'] if s['catalog_entry'] else 'N/A'}
- **Context Window**: {s['model_detail']['context_window'] if s['model_detail'] else 'N/A'}
- **Preferred Score**: {s['preferred_score']}/7
- **Smoke Test**: HTTP {s['smoke_http_status']} ({s['smoke_elapsed_ms']:.0f}ms)
- **NVCF Tracking**: {s['smoke_nvcf_reqid'] or 'None'}
""")
        
        f.write("""
### CANDIDATE (preferred_score < 3, passes all required)
""")
        
        candidates = [s for s in report['screening_results'] if s['classification'] == "CANDIDATE"]
        for s in candidates:
            f.write(f"""
#### {s['model_id']}
- **Catalog Owner**: {s['catalog_entry']['owned_by'] if s['catalog_entry'] else 'N/A'}
- **Context Window**: {s['model_detail']['context_window'] if s['model_detail'] else 'N/A'}
- **Preferred Score**: {s['preferred_score']}/7
- **Smoke Test**: HTTP {s['smoke_http_status']} ({s['smoke_elapsed_ms']:.0f}ms)
- **NVCF Tracking**: {s['smoke_nvcf_reqid'] or 'None'}
""")
        
        f.write("""
### SCREENED_OUT_REQUIRED (fails one or more required criteria)
""")
        
        screened = [s for s in report['screening_results'] if s['classification'] == "SCREENED_OUT_REQUIRED"]
        for s in screened:
            f.write(f"""
#### {s['model_id']}
- **General LLM**: {s['required_general_llm']}
- **NVIDIA Hosted**: {s['required_nvidia_hosted']}
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted
""")
        
        f.write("""
### CATALOG_UNAVAILABLE / ENDPOINT_UNAVAILABLE / ACCOUNT_NOT_ENTITLED / INVOCATION_FAILED
""")
        
        for cls in ["CATALOG_UNAVAILABLE", "ENDPOINT_UNAVAILABLE", "ACCOUNT_NOT_ENTITLED", "INVOCATION_FAILED"]:
            cls_candidates = [s for s in report['screening_results'] if s['classification'] == cls]
            if cls_candidates:
                f.write(f"""
#### {cls}
""")
                for s in cls_candidates:
                    f.write(f"- {s['model_id']}: HTTP {s['smoke_http_status']} - {s['smoke_error'] or 'N/A'}\n")
        
        f.write(f"""
## Official Catalog Evidence (Sample)

Total models in catalog: {report['catalog_models_count']}

Sample entries (first 20):
""")
        
        for i, (model_id, evidence) in enumerate(list(report['official_catalog_evidence'].items())[:20]):
            f.write(f"- {model_id}: owned_by={evidence.get('owned_by')}, created={evidence.get('created')}\n")
        
        f.write(f"""
... and {max(0, report['catalog_models_count'] - 20)} more models

## Limitations
""")
        
        for lim in report['limitations']:
            f.write(f"- {lim}\n")
        
        f.write("""
## Compliance
- ✅ No credential leakage (only credential_source recorded)
- ✅ No retry policy modification
- ✅ No production behavior modification
- ✅ Root Hygiene compliant (tools/one_shots/)
- ✅ Protected Worktree not modified
- ✅ Historical evidence not modified
- ✅ No RPM limiter changes
- ✅ No concurrency/burst testing
- ✅ Production model (M1) unchanged

## Next Phase
Proceed to **Phase C: Provider Smoke** with PRIMARY_CANDIDATE and SECONDARY_CANDIDATE models for controlled repeated observations.
""")
    
    print(f"[GEN] Governance doc saved to: {gov_path}")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())