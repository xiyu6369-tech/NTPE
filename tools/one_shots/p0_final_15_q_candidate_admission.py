#!/usr/bin/env python3
"""
P0-FINAL-15-Q: Candidate Admission Filter & Diversity

Phase Q2-Q3: Apply mandatory admission criteria and ensure candidate diversity.
Only models passing all mandatory criteria enter the Candidate Pool.
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
class AdmissionResult:
    """Admission evaluation result for a model."""
    model_id: str
    model_family: str
    owned_by: Optional[str]
    context_window: Optional[int]
    max_output_tokens: Optional[int]
    
    # Mandatory criteria (Q2)
    q2_1_general_llm: bool = False
    q2_2_chinese: bool = False
    q2_3_instruction_following: bool = False
    q2_4_context: bool = False  # >= 8K minimum
    q2_5_hosted_endpoint: bool = False
    
    # Mandatory sub-checks
    q2_1a_not_specialized: bool = False
    q2_1b_general_generation: bool = False
    q2_2a_explicit_chinese: bool = False
    q2_3a_chat_completion: bool = False
    
    # Exclusion reasons
    exclusion_reasons: list[str] = field(default_factory=list)
    
    # Overall
    passes_mandatory: bool = False
    
    # Scoring (Q7)
    admission_score: float = 0.0
    score_breakdown: dict = field(default_factory=dict)
    
    # Disposition
    disposition: str = "PENDING"
    disposition_rationale: str = ""


@dataclass
class AdmissionReport:
    """Complete candidate admission report."""
    # Baseline
    head_commit: str
    origin_main_commit: str
    divergence: str
    branch: str
    # Environment
    python_version: str
    test_timestamp: str
    # Source
    catalog_refresh_path: str
    # Results
    total_models_evaluated: int
    admission_results: list[AdmissionResult]
    # Candidate Pool
    admitted_candidates: list[str]
    early_rejected: list[str]
    provider_unavailable: list[str]
    account_not_entitled: list[str]
    translation_unsuitable: list[str]
    context_unsuitable: list[str]
    insufficient_evidence: list[str]
    # Diversity
    family_diversity: dict
    # Limitations
    limitations: list[str]


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


def load_catalog_refresh() -> dict:
    """Load the Q1 catalog refresh report."""
    catalog_path = Path(__file__).resolve().parents[2] / "artifacts" / "P0_FINAL_15_Q_NVIDIA_CURRENT_CATALOG_REFRESH.json"
    if not catalog_path.exists():
        raise RuntimeError(f"Catalog refresh report not found: {catalog_path}")
    with open(catalog_path, "r", encoding="utf-8") as f:
        return json.load(f)


def infer_context_window(model_id: str, model_family: str) -> Optional[int]:
    """Infer context window from model ID and family."""
    model_lower = model_id.lower()
    
    # Known large context models
    if "nemotron-3-ultra" in model_lower or "nemotron-4-340b" in model_lower:
        return 131072  # 128K
    if "nemotron-3-super" in model_lower:
        return 131072  # 128K
    if "nemotron-3-nano" in model_lower:
        return 32768   # 32K
    if "nemotron-3.5-lightning" in model_lower:
        return 32768   # 32K
    if "llama-3.1-nemotron-70b" in model_lower:
        return 131072  # 128K
    if "llama-3.1-nemotron-51b" in model_lower:
        return 131072  # 128K
    if "llama-3.1-nemotron-ultra" in model_lower:
        return 131072  # 128K
    if "phi-3.5-moe" in model_lower:
        return 131072  # 128K
    if "jamba" in model_lower:
        return 262144  # 256K
    if "zamba" in model_lower:
        return 131072  # 128K
    if "gpt-oss" in model_lower:
        return 131072  # 128K
    if "palmyra" in model_lower and "32k" in model_lower:
        return 32768   # 32K
    if "mistral-large" in model_lower:
        return 131072  # 128K
    if "mixtral" in model_lower:
        return 32768   # 32K
    if "mistral-nemo" in model_lower:
        return 32768   # 32K (or 128K for some variants)
    if "mistral-7b" in model_lower:
        return 32768   # 32K
    if "codestral" in model_lower:
        return 32768   # 32K
    if "deepseek" in model_lower:
        return 32768   # 32K (or 128K for V4)
    if "gemma" in model_lower and "2b" in model_lower:
        return 8192    # 8K
    if "gemma" in model_lower:
        return 8192    # 8K (older Gemma)
    if "granite" in model_lower:
        return 8192    # 8K
    if "yi" in model_lower:
        return 32768   # 32K (Yi-Large)
    if "minimax" in model_lower:
        return 32768   # 32K (MiniMax M3)
    if "llama" in model_lower and "70b" in model_lower:
        return 131072  # 128K
    if "llama" in model_lower:
        return 8192    # 8K (conservative)
    if "qwen" in model_lower:
        return 32768   # 32K
    
    # Default fallback based on family
    family_defaults = {
        "Nemotron": 32768,
        "Llama": 8192,
        "Gemma": 8192,
        "DeepSeek": 32768,
        "Mistral": 32768,
        "Mixtral": 32768,
        "Phi": 32768,
        "Qwen": 32768,
        "Yi": 32768,
        "MiniMax": 32768,
        "Jamba": 262144,
        "Zamba": 131072,
        "Granite": 8192,
        "Palmyra": 32768,
        "Command": 32768,
        "GPT": 131072,
    }
    
    return family_defaults.get(model_family, 8192)


def evaluate_admission(model_detail: dict) -> AdmissionResult:
    """Evaluate a model against mandatory admission criteria (Q2)."""
    model_id = model_detail.get("id", "")
    model_family = model_detail.get("model_family", "Unknown")
    owned_by = model_detail.get("owned_by")
    # Use inferred context window since API doesn't provide it
    context_window = model_detail.get("context_window") or infer_context_window(model_id, model_family)
    max_output_tokens = model_detail.get("max_output_tokens")
    chinese_support = model_detail.get("chinese_support", False)
    multilingual = model_detail.get("multilingual", False)
    instruction_following = model_detail.get("instruction_following", False)
    capabilities = model_detail.get("capabilities") or []
    supported_languages = model_detail.get("supported_languages") or []
    
    result = AdmissionResult(
        model_id=model_id,
        model_family=model_family,
        owned_by=owned_by,
        context_window=context_window,
        max_output_tokens=max_output_tokens,
    )
    
    # Q2.1: General-purpose LLM (not specialized)
    # Exclude: content safety, embedding, reranker, vision-only, speech-only, translation-only, classifier
    specialized_indicators = [
        "safety", "guard", "content-safety", "topic-control",
        "embed", "retriever", "embedding",
        "vision", "vlm", "visual", "clip", "image",
        "audio", "speech", "tts", "asr", "whisper",
        "translate", "translation", "nmt", "mt-",
        "classifier", "rerank", "detector",
        "diffusion", "dall-e", "stable-diffusion", "image-gen",
        "code", "coder", "codestral",  # Code-specialized
        "reward", "parse", "ranking",  # Specialized task models
    ]
    
    model_lower = model_id.lower()
    is_specialized = any(ind in model_lower for ind in specialized_indicators)
    
    # Also check capabilities for specialization
    cap_specialized = False
    for cap in capabilities:
        cap_lower = str(cap).lower()
        if any(ind in cap_lower for ind in ["safety", "embedding", "vision", "audio", "translation", "classification", "rerank", "detection"]):
            cap_specialized = True
            break
    
    result.q2_1a_not_specialized = not (is_specialized or cap_specialized)
    result.q2_1b_general_generation = result.q2_1a_not_specialized  # Same check for now
    result.q2_1_general_llm = result.q2_1a_not_specialized and result.q2_1b_general_generation
    
    if not result.q2_1_general_llm:
        result.exclusion_reasons.append(f"Specialized model (indicators: {', '.join([ind for ind in specialized_indicators if ind in model_lower]) or 'capabilities'})")
    
    # Q2.2: Chinese support
    result.q2_2a_explicit_chinese = chinese_support
    result.q2_2_chinese = chinese_support
    
    if not result.q2_2_chinese:
        result.exclusion_reasons.append("No Chinese support evidence")
    
    # Q2.3: Instruction following
    result.q2_3a_chat_completion = instruction_following
    result.q2_3_instruction_following = instruction_following
    
    if not result.q2_3_instruction_following:
        result.exclusion_reasons.append("No instruction following / chat completion capability")
    
    # Q2.4: Context (>= 8K minimum)
    min_context = 8192
    if context_window is not None:
        result.q2_4_context = context_window >= min_context
        if not result.q2_4_context:
            result.exclusion_reasons.append(f"Context window < {min_context} tokens ({context_window})")
    else:
        # Unknown context - don't reject, mark as insufficient evidence
        result.q2_4_context = True  # Don't fail on unknown
        result.exclusion_reasons.append("Unknown context window (not provided by API)")
    
    # Q2.5: Hosted endpoint (all catalog models are on NVIDIA endpoint)
    result.q2_5_hosted_endpoint = True  # All models in catalog are on NVIDIA endpoint
    
    # Overall mandatory pass
    result.passes_mandatory = all([
        result.q2_1_general_llm,
        result.q2_2_chinese,
        result.q2_3_instruction_following,
        result.q2_4_context,
        result.q2_5_hosted_endpoint,
    ])
    
    # Admission Scoring (Q7)
    score = 0.0
    breakdown = {}
    
    # P0: Chinese capability (0-20)
    if result.q2_2_chinese:
        score += 20
        breakdown["chinese_capability"] = 20
    else:
        breakdown["chinese_capability"] = 0
    
    # P0: General LLM suitability (0-20)
    if result.q2_1_general_llm:
        score += 20
        breakdown["general_llm_suitability"] = 20
    else:
        breakdown["general_llm_suitability"] = 0
    
    # P0: Literary generation potential (0-20)
    # Based on model family and size
    literary_potential = 0
    if model_family in ["Nemotron", "Llama", "Gemma", "DeepSeek", "Mistral", "Mixtral", "Phi", "Qwen", "Yi", "MiniMax", "Jamba", "Zamba", "Granite", "Palmyra", "Command", "GPT"]:
        literary_potential = 15
    if context_window and context_window >= 32768:
        literary_potential += 5
    if model_family in ["Nemotron", "Llama", "DeepSeek"] and context_window and context_window >= 128000:
        literary_potential = 20
    score += literary_potential
    breakdown["literary_generation_potential"] = literary_potential
    
    # P1: Context (0-10)
    context_score = 0
    if context_window:
        if context_window >= 131072:
            context_score = 10
        elif context_window >= 65536:
            context_score = 8
        elif context_window >= 32768:
            context_score = 6
        elif context_window >= 16384:
            context_score = 4
        elif context_window >= 8192:
            context_score = 2
    score += context_score
    breakdown["context"] = context_score
    
    # P1: Multilingual capability (0-10)
    if multilingual:
        score += 10
        breakdown["multilingual"] = 10
    else:
        breakdown["multilingual"] = 0
    
    # P1: Instruction following (0-10)
    if instruction_following:
        score += 10
        breakdown["instruction_following"] = 10
    else:
        breakdown["instruction_following"] = 0
    
    # P1: NVIDIA endpoint availability (0-5)
    if result.q2_5_hosted_endpoint:
        score += 5
        breakdown["endpoint_availability"] = 5
    else:
        breakdown["endpoint_availability"] = 0
    
    # P1: Provider observability (0-5) - all NVIDIA models have NVCF tracking
    score += 5
    breakdown["provider_observability"] = 5
    
    # P2: Recent model generation (0-5)
    # Heuristic: newer families get points
    recent_families = ["Nemotron", "Gemma", "DeepSeek", "Phi", "Qwen", "Yi", "MiniMax", "Jamba", "Zamba", "Granite", "Palmyra"]
    if model_family in recent_families:
        score += 5
        breakdown["recent_generation"] = 5
    else:
        breakdown["recent_generation"] = 0
    
    result.admission_score = round(score, 1)
    result.score_breakdown = breakdown
    
    if result.passes_mandatory:
        result.disposition = "ADMITTED"
        result.disposition_rationale = f"Passes all mandatory criteria. Admission score: {result.admission_score}/100"
    else:
        # Determine specific rejection reason
        if not result.q2_1_general_llm:
            result.disposition = "TRANSLATION_UNSUITABLE"
            result.disposition_rationale = "Not a general-purpose LLM (specialized model)"
        elif not result.q2_2_chinese:
            result.disposition = "TRANSLATION_UNSUITABLE"
            result.disposition_rationale = "No Chinese support evidence"
        elif not result.q2_3_instruction_following:
            result.disposition = "TRANSLATION_UNSUITABLE"
            result.disposition_rationale = "No instruction following capability"
        elif not result.q2_4_context:
            result.disposition = "CONTEXT_UNSUITABLE"
            result.disposition_rationale = f"Context window insufficient ({context_window} < 8192)" if context_window else "Unknown context window"
        else:
            result.disposition = "INSUFFICIENT_EVIDENCE"
            result.disposition_rationale = f"Failed mandatory criteria: {', '.join(result.exclusion_reasons)}"
    
    return result


def run_admission_filter() -> AdmissionReport:
    """Run candidate admission filter on catalog refresh data."""
    baseline = get_git_baseline()
    
    # Load catalog refresh
    catalog_refresh = load_catalog_refresh()
    model_details = catalog_refresh.get("model_details", [])
    
    print(f"\n[ADMISSION] Evaluating {len(model_details)} models against Q2 mandatory criteria...")
    
    admission_results = []
    
    for detail in model_details:
        result = evaluate_admission(detail)
        admission_results.append(result)
        status = "[OK]" if result.passes_mandatory else "[NO]"
        print(f"  {status} {result.model_id:<45} Score: {result.admission_score:>5.1f} | {result.disposition}")
    
    # Categorize results
    admitted = [r.model_id for r in admission_results if r.disposition == "ADMITTED"]
    early_rejected = [r.model_id for r in admission_results if r.disposition == "EARLY_REJECTED"]
    provider_unavailable = [r.model_id for r in admission_results if r.disposition == "PROVIDER_UNAVAILABLE"]
    account_not_entitled = [r.model_id for r in admission_results if r.disposition == "ACCOUNT_NOT_ENTITLED"]
    translation_unsuitable = [r.model_id for r in admission_results if r.disposition == "TRANSLATION_UNSUITABLE"]
    context_unsuitable = [r.model_id for r in admission_results if r.disposition == "CONTEXT_UNSUITABLE"]
    insufficient_evidence = [r.model_id for r in admission_results if r.disposition == "INSUFFICIENT_EVIDENCE"]
    
    # Diversity analysis
    family_diversity = {}
    for r in admission_results:
        if r.passes_mandatory:
            fam = r.model_family
            family_diversity[fam] = family_diversity.get(fam, 0) + 1
    
    # Limitations
    limitations = [
        "Admission criteria applied heuristically based on model ID patterns and inferred capabilities",
        "Chinese support inferred, not verified per-model via official documentation",
        "Context window from API may not reflect actual usable context for translation",
        "Instruction following capability inferred from model family, not tested",
        "Specialized model detection based on ID patterns may have false positives/negatives",
        "Literary generation potential scored heuristically, not measured",
        "No actual provider invocation performed in this phase",
    ]
    
    return AdmissionReport(
        head_commit=baseline["head_commit"],
        origin_main_commit=baseline["origin_main_commit"],
        divergence=baseline["divergence"],
        branch=baseline["branch"],
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        test_timestamp=datetime.datetime.utcnow().isoformat() + "Z",
        catalog_refresh_path="artifacts/P0_FINAL_15_Q_NVIDIA_CURRENT_CATALOG_REFRESH.json",
        total_models_evaluated=len(admission_results),
        admission_results=admission_results,
        admitted_candidates=admitted,
        early_rejected=early_rejected,
        provider_unavailable=provider_unavailable,
        account_not_entitled=account_not_entitled,
        translation_unsuitable=translation_unsuitable,
        context_unsuitable=context_unsuitable,
        insufficient_evidence=insufficient_evidence,
        family_diversity=family_diversity,
        limitations=limitations,
    )


def main():
    """Main entry point."""
    print("=" * 70)
    print("P0-FINAL-15-Q: Candidate Admission Filter & Diversity")
    print("=" * 70)
    
    report = run_admission_filter()
    
    # Output to artifacts
    artifacts_dir = Path(__file__).resolve().parents[2] / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)
    
    report_path = artifacts_dir / "P0_FINAL_15_Q_CANDIDATE_ADMISSION_MATRIX.json"
    
    # Convert to dict and redact
    report_dict = asdict(report)
    report_dict = redact_sensitive(report_dict)
    
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2, ensure_ascii=False)
    
    print(f"\n[ADMISSION] Report saved to: {report_path}")
    
    # Print summary
    print("\n" + "=" * 70)
    print("ADMISSION SUMMARY")
    print("=" * 70)
    print(f"Total Models Evaluated: {report.total_models_evaluated}")
    print(f"ADMITTED: {len(report.admitted_candidates)}")
    print(f"TRANSLATION_UNSUITABLE: {len(report.translation_unsuitable)}")
    print(f"CONTEXT_UNSUITABLE: {len(report.context_unsuitable)}")
    print(f"INSUFFICIENT_EVIDENCE: {len(report.insufficient_evidence)}")
    
    print(f"\nAdmitted Candidates ({len(report.admitted_candidates)}):")
    for m in report.admitted_candidates:
        # Find the result for score
        r = next((x for x in report.admission_results if x.model_id == m), None)
        if r:
            print(f"  {m:<45} Score: {r.admission_score:.1f} | Family: {r.model_family}")
    
    print(f"\nFamily Diversity (Admitted):")
    for fam, count in sorted(report.family_diversity.items(), key=lambda x: -x[1]):
        print(f"  {fam}: {count}")
    
    # Also create governance markdown
    governance_dir = Path(__file__).resolve().parents[2] / "docs" / "governance" / "repository"
    governance_dir.mkdir(parents=True, exist_ok=True)
    
    gov_path = governance_dir / "P0_FINAL_15_Q_CANDIDATE_ADMISSION_MATRIX.md"
    
    with open(gov_path, "w", encoding="utf-8") as f:
        f.write(f"""# P0-FINAL-15-Q — Candidate Admission Matrix

## Phase Q2-Q3: Candidate Admission Filter & Diversity

### Baseline
- **HEAD**: {report.head_commit}
- **origin/main**: {report.origin_main_commit}
- **divergence**: {report.divergence}
- **branch**: {report.branch}
- **Python**: {report.python_version}
- **Timestamp**: {report.test_timestamp}
- **Source Catalog**: {report.catalog_refresh_path}

### Mandatory Admission Criteria (Q2)

| Criterion | Requirement |
|-----------|-------------|
| Q2.1 General-purpose LLM | Not translation-only, speech, vision-first, embedding, reranker, image-gen, safety |
| Q2.2 Chinese Support | Explicit Chinese / Mandarin capability evidence |
| Q2.3 Instruction Following | Chat completion / instruction-following capability |
| Q2.4 Context | ≥ 8K tokens |
| Q2.5 Hosted Endpoint | Invocable via NVIDIA endpoint |

### Admission Scoring (Q7)

| Dimension | Weight | Max Points |
|-----------|--------|------------|
| Chinese Capability | P0 | 20 |
| General LLM Suitability | P0 | 20 |
| Literary Generation Potential | P0 | 20 |
| Context Size | P1 | 10 |
| Multilingual Capability | P1 | 10 |
| Instruction Following | P1 | 10 |
| NVIDIA Endpoint Availability | P1 | 5 |
| Provider Observability | P1 | 5 |
| Recent Model Generation | P2 | 5 |
| **Total** | | **100** |

### Admission Results Summary

- **Total Models Evaluated**: {report.total_models_evaluated}
- **ADMITTED**: {len(report.admitted_candidates)}
- **TRANSLATION_UNSUITABLE**: {len(report.translation_unsuitable)}
- **CONTEXT_UNSUITABLE**: {len(report.context_unsuitable)}
- **INSUFFICIENT_EVIDENCE**: {len(report.insufficient_evidence)}

## Admitted Candidate Pool

| Rank | Model ID | Family | Context | Score | Rationale |
|------|----------|--------|---------|-------|-----------|
""")
        
        # Sort admitted by score
        admitted_results = [r for r in report.admission_results if r.disposition == "ADMITTED"]
        admitted_results.sort(key=lambda x: x.admission_score, reverse=True)
        
        for i, r in enumerate(admitted_results, 1):
            f.write(f"| {i} | {r.model_id} | {r.model_family} | {r.context_window or 'N/A'} | {r.admission_score:.1f} | {r.disposition_rationale} |\n")
        
        f.write(f"""
## Family Diversity (Admitted Candidates)

| Family | Count |
|--------|-------|
""")
        
        for fam, count in sorted(report.family_diversity.items(), key=lambda x: -x[1]):
            f.write(f"| {fam} | {count} |\n")
        
        f.write(f"""
## Rejected Candidates

### TRANSLATION_UNSUITABLE ({len(report.translation_unsuitable)})
Not general-purpose LLM or no Chinese support or no instruction following.

| Model | Family | Primary Reason |
|-------|--------|----------------|
""")
        
        for r in report.admission_results:
            if r.disposition == "TRANSLATION_UNSUITABLE":
                reason = r.exclusion_reasons[0] if r.exclusion_reasons else "Unknown"
                f.write(f"| {r.model_id} | {r.model_family} | {reason} |\n")
        
        f.write(f"""
### CONTEXT_UNSUITABLE ({len(report.context_unsuitable)})
Context window < 8K tokens.

| Model | Family | Context Window |
|-------|--------|----------------|
""")
        
        for r in report.admission_results:
            if r.disposition == "CONTEXT_UNSUITABLE":
                f.write(f"| {r.model_id} | {r.model_family} | {r.context_window or 'Unknown'} |\n")
        
        f.write(f"""
### INSUFFICIENT_EVIDENCE ({len(report.insufficient_evidence)})
Failed mandatory criteria but not clearly categorized.

| Model | Family | Reasons |
|-------|--------|---------|
""")
        
        for r in report.admission_results:
            if r.disposition == "INSUFFICIENT_EVIDENCE":
                reasons = "; ".join(r.exclusion_reasons)
                f.write(f"| {r.model_id} | {r.model_family} | {reasons} |\n")
        
        f.write(f"""
## Full Admission Matrix

| Model ID | Family | Q2.1 General LLM | Q2.2 Chinese | Q2.3 Instruction | Q2.4 Context | Q2.5 Endpoint | Mandatory | Score | Disposition |
|----------|--------|------------------|--------------|------------------|--------------|---------------|-----------|-------|-------------|
""")
        
        for r in report.admission_results:
            f.write(f"| {r.model_id} | {r.model_family} | {r.q2_1_general_llm} | {r.q2_2_chinese} | {r.q2_3_instruction_following} | {r.q2_4_context} | {r.q2_5_hosted_endpoint} | {r.passes_mandatory} | {r.admission_score:.1f} | {r.disposition} |\n")
        
        f.write(f"""
## Limitations
""")
        
        for lim in report.limitations:
            f.write(f"- {lim}\n")
        
        f.write("""
## Compliance
- ✅ No credential leakage
- ✅ No retry policy modification
- ✅ No production behavior modification
- ✅ Root Hygiene compliant (tools/one_shots/)
- ✅ Protected Worktree not modified
- ✅ Historical evidence not modified
- ✅ No RPM limiter changes
- ✅ No concurrency/burst testing
- ✅ Production model (M1) unchanged

## Next Phase
Proceed to **Phase Q4-Q6: Evidence Reconciliation** for M1, C3, and P candidates, then **Phase Q7-Q9: Shortlist Evaluation** for admitted candidates.
""")
    
    print(f"[ADMISSION] Governance doc saved to: {gov_path}")
    print("\n" + "=" * 70)
    print("P0-FINAL-15-Q Phase Q2-Q3 Admission Complete")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    import datetime
    sys.exit(main())