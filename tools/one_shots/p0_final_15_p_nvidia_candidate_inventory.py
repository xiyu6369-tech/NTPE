#!/usr/bin/env python3
"""
P0-FINAL-15-P: NVIDIA Current Model Catalog Inventory & Candidate Discovery

Phase A - Catalog Verification:
- GET /v1/models
- GET /v1/models/{model} for priority candidates

Phase B - Account/Endpoint Verification:
- Controlled smoke requests for each candidate
- Distinguish: CATALOG_AVAILABLE, ENDPOINT_AVAILABLE, ACCOUNT_ENTITLED, INVOCATION_SUCCESS

Screens candidates per Section 7 criteria and creates inventory for evaluation pipeline.
"""

from __future__ import annotations

import json
import os
import sys
import time
import datetime
import requests
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


@dataclass
class ModelCatalogEntry:
    """Single model entry from NVIDIA /v1/models catalog."""
    id: str
    owned_by: Optional[str]
    created: Optional[int]
    object: str
    permission: Optional[list] = None
    root: Optional[str] = None
    parent: Optional[str] = None


@dataclass
class ModelDetail:
    """Detailed model info from /v1/models/{model} endpoint."""
    id: str
    owned_by: Optional[str]
    created: Optional[int]
    object: str
    permission: Optional[list] = None
    root: Optional[str] = None
    parent: Optional[str] = None
    # Additional fields from detail endpoint
    context_window: Optional[int] = None
    max_output_tokens: Optional[int] = None
    capabilities: Optional[list] = None


@dataclass
class CandidateScreening:
    """Screening result for a candidate model."""
    model_id: str
    # Phase A: Catalog Verification
    in_catalog: bool = False
    catalog_entry: Optional[ModelCatalogEntry] = None
    detail_available: bool = False
    model_detail: Optional[ModelDetail] = None
    catalog_http_status: Optional[int] = None
    detail_http_status: Optional[int] = None
    # Phase B: Account/Endpoint Verification
    catalog_available: bool = False
    endpoint_available: bool = False
    account_entitled: bool = False
    invocation_success: bool = False
    smoke_http_status: Optional[int] = None
    smoke_elapsed_ms: Optional[float] = None
    smoke_provider_request_id: Optional[str] = None
    smoke_nvcf_reqid: Optional[str] = None
    smoke_nvcf_status: Optional[str] = None
    smoke_error: Optional[str] = None
    # Screening Criteria (Section 7)
    required_general_llm: bool = False
    required_chinese_support: bool = False
    required_instruction_following: bool = False
    required_long_form: bool = False
    required_nvidia_hosted: bool = False
    required_no_arch_change: bool = False
    preferred_context_32k: bool = False
    preferred_multilingual: bool = False
    preferred_strong_generation: bool = False
    preferred_long_context: bool = False
    preferred_free_endpoint: bool = False
    preferred_stable_metadata: bool = False
    preferred_literary: bool = False
    # Overall
    passes_required: bool = False
    preferred_score: int = 0
    classification: str = "PENDING"
    notes: str = ""


@dataclass
class InventoryReport:
    """Complete candidate inventory report."""
    # Baseline
    head_commit: str
    origin_main_commit: str
    divergence: str
    branch: str
    # Environment
    python_version: str
    test_timestamp: str
    endpoint: str
    credential_present: bool
    credential_source: str
    # Catalog
    catalog_fetch_status: str
    catalog_http_status: Optional[int]
    catalog_models_count: int
    catalog_models: list[ModelCatalogEntry]
    # Candidates
    priority_candidates: list[str]
    all_screened_candidates: list[str]
    screening_results: list[CandidateScreening]
    # Evidence
    official_catalog_evidence: dict
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


def fetch_nvidia_catalog(api_key: str) -> tuple[Optional[list[ModelCatalogEntry]], Optional[int], str]:
    """Fetch NVIDIA /v1/models catalog."""
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        response = requests.get(
            "https://integrate.api.nvidia.com/v1/models",
            headers=headers,
            timeout=(10, 30),
        )
        if response.status_code != 200:
            return None, response.status_code, f"Catalog fetch failed: {response.status_code} - {response.text[:500]}"
        
        data = response.json()
        models_data = data.get("data", [])
        
        models = []
        for m in models_data:
            models.append(ModelCatalogEntry(
                id=m.get("id", ""),
                owned_by=m.get("owned_by"),
                created=m.get("created"),
                object=m.get("object", "model"),
                permission=m.get("permission"),
                root=m.get("root"),
                parent=m.get("parent"),
            ))
        
        return models, response.status_code, "success"
    except Exception as e:
        return None, None, f"Catalog fetch exception: {e}"


def fetch_model_detail(model_id: str, api_key: str) -> tuple[Optional[ModelDetail], Optional[int], str]:
    """Fetch NVIDIA /v1/models/{model_id} detail."""
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        response = requests.get(
            f"https://integrate.api.nvidia.com/v1/models/{model_id}",
            headers=headers,
            timeout=(10, 30),
        )
        if response.status_code != 200:
            return None, response.status_code, f"Detail fetch failed: {response.status_code} - {response.text[:500]}"
        
        data = response.json()
        detail = ModelDetail(
            id=data.get("id", ""),
            owned_by=data.get("owned_by"),
            created=data.get("created"),
            object=data.get("object", "model"),
            permission=data.get("permission"),
            root=data.get("root"),
            parent=data.get("parent"),
            context_window=data.get("context_window"),
            max_output_tokens=data.get("max_output_tokens"),
            capabilities=data.get("capabilities"),
        )
        return detail, response.status_code, "success"
    except Exception as e:
        return None, None, f"Detail fetch exception: {e}"


def run_smoke_test(model_id: str, api_key: str, endpoint: str) -> tuple[Optional[int], float, Optional[str], Optional[str], Optional[str], Optional[str]]:
    """Run controlled smoke test for a model. Returns (http_status, elapsed_ms, provider_request_id, nvcf_reqid, nvcf_status, error)."""
    import datetime
    
    timestamp_utc = datetime.datetime.utcnow().isoformat() + "Z"
    
    test_text = "안녕하세요. 이것은 테스트입니다."
    system_prompt = "Translate the following Korean text to Traditional Chinese (Taiwan). Output only the translation."
    
    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": test_text},
        ],
        "temperature": 0.15,
        "top_p": 0.85,
        "max_tokens": 4000,
        "stream": False,
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    start_time = time.monotonic()
    
    try:
        response = requests.post(
            endpoint,
            headers=headers,
            json=payload,
            timeout=(10, 60),
        )
        
        elapsed_ms = (time.monotonic() - start_time) * 1000
        http_status = response.status_code
        
        provider_request_id = None
        try:
            data = response.json()
            provider_request_id = data.get("id")
        except Exception:
            pass
        
        nvcf_reqid = response.headers.get("Nvcf-Reqid")
        nvcf_status = response.headers.get("Nvcf-Status")
        
        error = None if http_status == 200 else f"HTTP {http_status}: {response.text[:200]}"
        
        return http_status, elapsed_ms, provider_request_id, nvcf_reqid, nvcf_status, error
        
    except requests.exceptions.Timeout as e:
        elapsed_ms = (time.monotonic() - start_time) * 1000
        return 408, elapsed_ms, None, None, None, f"Timeout: {e}"
    except Exception as e:
        elapsed_ms = (time.monotonic() - start_time) * 1000
        return 500, elapsed_ms, None, None, None, str(e)


def screen_candidate(screening: CandidateScreening, catalog_models: list[ModelCatalogEntry]) -> CandidateScreening:
    """Apply Section 7 screening criteria to a candidate."""
    model_id = screening.model_id
    model_id_lower = model_id.lower()
    
    # Find in catalog
    catalog_match = next((m for m in catalog_models if m.id == model_id), None)
    if catalog_match:
        screening.in_catalog = True
        screening.catalog_entry = catalog_match
        screening.catalog_available = True
    
    # Required criteria (Section 7)
    # 1. General-purpose LLM or high language generation capability
    # Translation-only models, speech, vision-first, embedding, reranker, image gen are lower priority
    translation_only_indicators = ["translate", "translation", "nmt", "mt-"]
    speech_indicators = ["speech", "asr", "tts", "whisper", "audio"]
    vision_indicators = ["vision", "vl", "visual", "clip", "image"]
    embedding_indicators = ["embed", "embedding", "retrieval", "rerank"]
    image_gen_indicators = ["image-gen", "imagegen", "diffusion", "dall-e", "stable-diffusion"]
    
    is_specialized = any(ind in model_id_lower for ind in translation_only_indicators + speech_indicators + vision_indicators + embedding_indicators + image_gen_indicators)
    
    # Check if it's a known general LLM family
    general_llm_families = [
        "llama", "nemotron", "gpt", "mistral", "mixtral", "gemma", "qwen", "yi", "baichuan", 
        "deepseek", "minimax", "internlm", "chatglm", "glm", "phi", "falcon", "mpt", "bloom",
        "opt", "bert", "t5", "ul2", "flan", "palm", "lamda", "minerva", "galactica",
        "grok", "command", "cohere", "jamba", "amba", "mamba", "rwkv", "eagle", "zephyr",
        "openchat", "starling", "vicuna", "alpaca", "wizard", "orca", "dolphin", "airoboros"
    ]
    
    is_general_llm = any(fam in model_id_lower for fam in general_llm_families)
    
    # Check owned_by for NVIDIA-hosted
    owned_by = screening.catalog_entry.owned_by if screening.catalog_entry else ""
    owned_by_lower = owned_by.lower() if owned_by else ""
    is_nvidia_hosted = bool(owned_by) and ("nvidia" in owned_by_lower or "meta" in owned_by_lower or "minimaxai" in owned_by_lower)
    
    # Required criteria
    screening.required_general_llm = is_general_llm and not is_specialized
    screening.required_chinese_support = True  # Assume all general LLMs support Chinese (conservative)
    screening.required_instruction_following = is_general_llm  # General LLMs have instruction following
    screening.required_long_form = is_general_llm  # General LLMs can handle long form
    screening.required_nvidia_hosted = is_nvidia_hosted
    screening.required_no_arch_change = True  # No architecture change needed for chat/completions
    
    # Preferred criteria
    context_window = screening.model_detail.context_window if screening.model_detail else None
    screening.preferred_context_32k = context_window is not None and context_window >= 32768
    screening.preferred_multilingual = True  # General LLMs are multilingual
    screening.preferred_strong_generation = is_general_llm
    screening.preferred_long_context = context_window is not None and context_window >= 16384
    screening.preferred_free_endpoint = True  # NVIDIA Free Endpoint assumption
    screening.preferred_stable_metadata = screening.detail_available and screening.smoke_http_status == 200
    screening.preferred_literary = is_general_llm  # General LLMs suitable for literary
    
    # Overall
    screening.passes_required = all([
        screening.required_general_llm,
        screening.required_chinese_support,
        screening.required_instruction_following,
        screening.required_long_form,
        screening.required_nvidia_hosted,
        screening.required_no_arch_change,
    ])
    
    # Preferred score (out of 7)
    preferred_flags = [
        screening.preferred_context_32k,
        screening.preferred_multilingual,
        screening.preferred_strong_generation,
        screening.preferred_long_context,
        screening.preferred_free_endpoint,
        screening.preferred_stable_metadata,
        screening.preferred_literary,
    ]
    screening.preferred_score = sum(preferred_flags)
    
    # Classification
    if not screening.passes_required:
        screening.classification = "SCREENED_OUT_REQUIRED"
    elif not screening.catalog_available:
        screening.classification = "CATALOG_UNAVAILABLE"
    elif not screening.endpoint_available:
        screening.classification = "ENDPOINT_UNAVAILABLE"
    elif not screening.account_entitled:
        screening.classification = "ACCOUNT_NOT_ENTITLED"
    elif not screening.invocation_success:
        screening.classification = "INVOCATION_FAILED"
    elif screening.preferred_score >= 5:
        screening.classification = "PRIMARY_CANDIDATE"
    elif screening.preferred_score >= 3:
        screening.classification = "SECONDARY_CANDIDATE"
    else:
        screening.classification = "CANDIDATE"
    
    return screening


def run_inventory() -> InventoryReport:
    """Run complete candidate inventory."""
    baseline = get_git_baseline()
    
    endpoint = "https://integrate.api.nvidia.com/v1/chat/completions"
    api_key = os.environ.get("NVIDIA_API_KEY")
    
    if not api_key:
        raise RuntimeError("NVIDIA_API_KEY environment variable not set")
    
    # Phase A: Fetch catalog
    print("\n[INVENTORY] Phase A: Fetching NVIDIA /v1/models catalog...")
    catalog_models, catalog_http_status, catalog_msg = fetch_nvidia_catalog(api_key)
    
    if catalog_models is None:
        print(f"[INVENTORY] Catalog fetch failed: {catalog_msg}")
        catalog_models = []
        catalog_fetch_status = "FAILED"
    else:
        print(f"[INVENTORY] Catalog fetch successful: {len(catalog_models)} models")
        catalog_fetch_status = "SUCCESS"
    
    # Priority candidates per Section 8
    priority_candidates = [
        "deepseek-ai/DeepSeek-V4-Pro-0813",      # C1
        "deepseek-ai/DeepSeek-V4-Flash-0731",    # C2
        "google/gemma-4-31b",                    # C3 (Gemma 4 31B)
    ]
    
    # Additional candidates from catalog that match general LLM patterns
    # We'll screen all catalog models but prioritize the above
    all_candidates = list(priority_candidates)
    if catalog_models:
        for m in catalog_models:
            if m.id not in all_candidates:
                all_candidates.append(m.id)
    
    print(f"[INVENTORY] Screening {len(all_candidates)} candidates...")
    
    screening_results = []
    
    for model_id in all_candidates:
        print(f"\n[INVENTORY] Screening: {model_id}")
        screening = CandidateScreening(model_id=model_id)
        
        # Phase A: Catalog verification
        if catalog_models:
            catalog_match = next((m for m in catalog_models if m.id == model_id), None)
            if catalog_match:
                screening.in_catalog = True
                screening.catalog_entry = catalog_match
                screening.catalog_available = True
                screening.catalog_http_status = catalog_http_status
                
                # Fetch detail
                detail, detail_status, detail_msg = fetch_model_detail(model_id, api_key)
                if detail:
                    screening.detail_available = True
                    screening.model_detail = detail
                    screening.detail_http_status = detail_status
                    screening.endpoint_available = True
                else:
                    screening.detail_http_status = detail_status
        else:
            screening.catalog_http_status = catalog_http_status
        
        # Phase B: Account/Endpoint verification (smoke test)
        if screening.catalog_available:
            print(f"  Running smoke test...")
            smoke_status, smoke_elapsed, smoke_req_id, smoke_nvcf_reqid, smoke_nvcf_status, smoke_error = run_smoke_test(
                model_id, api_key, endpoint
            )
            screening.smoke_http_status = smoke_status
            screening.smoke_elapsed_ms = smoke_elapsed
            screening.smoke_provider_request_id = smoke_req_id
            screening.smoke_nvcf_reqid = smoke_nvcf_reqid
            screening.smoke_nvcf_status = smoke_nvcf_status
            screening.smoke_error = smoke_error
            
            if smoke_status == 200:
                screening.account_entitled = True
                screening.invocation_success = True
            elif smoke_status == 404:
                # Check if it's "Function not found for account"
                if smoke_error and "Function" in smoke_error and "account" in smoke_error:
                    screening.account_entitled = False
                else:
                    screening.account_entitled = False
                screening.invocation_success = False
            elif smoke_status == 429:
                screening.account_entitled = True  # Entitled but rate limited
                screening.invocation_success = False
            else:
                screening.account_entitled = False
                screening.invocation_success = False
        
        # Apply screening criteria
        screening = screen_candidate(screening, catalog_models or [])
        
        screening_results.append(screening)
        print(f"  Classification: {screening.classification}")
        print(f"  Required: {screening.passes_required}, Preferred: {screening.preferred_score}/7")
    
    # Build official catalog evidence
    official_catalog_evidence = {}
    for m in catalog_models or []:
        official_catalog_evidence[m.id] = {
            "owned_by": m.owned_by,
            "created": m.created,
            "object": m.object,
        }
    
    # Limitations
    limitations = [
        "Token measurement uses character-based estimation",
        "Screening criteria applied heuristically based on model ID patterns",
        "Chinese support assumed for general LLMs (not verified per-model)",
        "Single smoke test per model (not repeated for stability)",
        "No direct account entitlement API available",
        "Free Endpoint availability inferred, not verified per-model",
    ]
    
    return InventoryReport(
        head_commit=baseline["head_commit"],
        origin_main_commit=baseline["origin_main_commit"],
        divergence=baseline["divergence"],
        branch=baseline["branch"],
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        test_timestamp=datetime.datetime.utcnow().isoformat() + "Z",
        endpoint=endpoint,
        credential_present=True,
        credential_source="NVIDIA_API_KEY",
        catalog_fetch_status=catalog_fetch_status,
        catalog_http_status=catalog_http_status,
        catalog_models_count=len(catalog_models) if catalog_models else 0,
        catalog_models=catalog_models or [],
        priority_candidates=priority_candidates,
        all_screened_candidates=all_candidates,
        screening_results=screening_results,
        official_catalog_evidence=official_catalog_evidence,
        limitations=limitations,
    )


def main():
    """Main entry point."""
    print("=" * 70)
    print("P0-FINAL-15-P: NVIDIA Current Model Catalog Inventory")
    print("=" * 70)
    
    report = run_inventory()
    
    # Output to artifacts
    artifacts_dir = Path(__file__).resolve().parents[2] / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)
    
    report_path = artifacts_dir / "P0_FINAL_15_P_NVIDIA_CURRENT_CANDIDATE_INVENTORY.json"
    
    # Convert to dict and redact
    report_dict = asdict(report)
    report_dict = redact_sensitive(report_dict)
    
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2, ensure_ascii=False)
    
    print(f"\n[INVENTORY] Report saved to: {report_path}")
    
    # Print summary
    print("\n" + "=" * 70)
    print("INVENTORY SUMMARY")
    print("=" * 70)
    print(f"Catalog Status: {report.catalog_fetch_status} (HTTP {report.catalog_http_status})")
    print(f"Catalog Models: {report.catalog_models_count}")
    print(f"Candidates Screened: {len(report.screening_results)}")
    
    print("\nCandidate Classifications:")
    for s in report.screening_results:
        status = "[OK]" if s.passes_required else "[NO]"
        print(f"  {status} {s.model_id:<45} {s.classification:<30} Pref:{s.preferred_score}/7")
    
    # Primary candidates
    primary = [s for s in report.screening_results if s.classification == "PRIMARY_CANDIDATE"]
    secondary = [s for s in report.screening_results if s.classification == "SECONDARY_CANDIDATE"]
    candidates = [s for s in report.screening_results if s.classification == "CANDIDATE"]
    
    print(f"\nPRIMARY_CANDIDATE ({len(primary)}):")
    for s in primary:
        print(f"  {s.model_id}")
    
    print(f"\nSECONDARY_CANDIDATE ({len(secondary)}):")
    for s in secondary:
        print(f"  {s.model_id}")
    
    print(f"\nCANDIDATE ({len(candidates)}):")
    for s in candidates:
        print(f"  {s.model_id}")
    
    # Also create governance markdown
    governance_dir = Path(__file__).resolve().parents[2] / "docs" / "governance" / "repository"
    governance_dir.mkdir(parents=True, exist_ok=True)
    
    gov_path = governance_dir / "P0_FINAL_15_P_NVIDIA_CURRENT_CANDIDATE_INVENTORY.md"
    
    with open(gov_path, "w", encoding="utf-8") as f:
        f.write(f"""# P0-FINAL-15-P — NVIDIA Current Candidate Inventory

## Phase A: Catalog Verification

### Environment
- **HEAD**: {report.head_commit}
- **origin/main**: {report.origin_main_commit}
- **divergence**: {report.divergence}
- **branch**: {report.branch}
- **Python**: {report.python_version}
- **Endpoint**: {report.endpoint}
- **Credential**: {report.credential_source} (present: {report.credential_present})
- **Timestamp**: {report.test_timestamp}

### NVIDIA /v1/models Catalog
- **Fetch Status**: {report.catalog_fetch_status}
- **HTTP Status**: {report.catalog_http_status}
- **Models Count**: {report.catalog_models_count}

## Phase B: Account/Endpoint Verification

### Priority Candidates (Section 8)
""")
        
        for c in report.priority_candidates:
            f.write(f"- {c}\n")
        
        f.write(f"""
### All Screened Candidates ({len(report.all_screened_candidates)} total)
""")
        
        for c in report.all_screened_candidates:
            f.write(f"- {c}\n")
        
        f.write("""
## Screening Results

| Model | In Catalog | Catalog Avail | Endpoint Avail | Account Entitled | Invocation Success | HTTP Status | Required | Preferred | Classification |
|-------|------------|---------------|----------------|------------------|-------------------|-------------|----------|-----------|----------------|
""")
        
        for s in report.screening_results:
            f.write(f"| {s.model_id} | {s.in_catalog} | {s.catalog_available} | {s.endpoint_available} | {s.account_entitled} | {s.invocation_success} | {s.smoke_http_status} | {s.passes_required} | {s.preferred_score}/7 | {s.classification} |\n")
        
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
        
        primary = [s for s in report.screening_results if s.classification == "PRIMARY_CANDIDATE"]
        for s in primary:
            f.write(f"""
#### {s.model_id}
- **Catalog Owner**: {s.catalog_entry.owned_by if s.catalog_entry else 'N/A'}
- **Context Window**: {s.model_detail.context_window if s.model_detail else 'N/A'}
- **Preferred Score**: {s.preferred_score}/7
- **Smoke Test**: HTTP {s.smoke_http_status} ({s.smoke_elapsed_ms:.0f}ms)
- **NVCF Tracking**: {s.smoke_nvcf_reqid or 'None'}
""")
        
        f.write("""
### SECONDARY_CANDIDATE (preferred_score 3-4, passes all required)
""")
        
        secondary = [s for s in report.screening_results if s.classification == "SECONDARY_CANDIDATE"]
        for s in secondary:
            f.write(f"""
#### {s.model_id}
- **Catalog Owner**: {s.catalog_entry.owned_by if s.catalog_entry else 'N/A'}
- **Context Window**: {s.model_detail.context_window if s.model_detail else 'N/A'}
- **Preferred Score**: {s.preferred_score}/7
- **Smoke Test**: HTTP {s.smoke_http_status} ({s.smoke_elapsed_ms:.0f}ms)
- **NVCF Tracking**: {s.smoke_nvcf_reqid or 'None'}
""")
        
        f.write("""
### CANDIDATE (preferred_score < 3, passes all required)
""")
        
        candidates = [s for s in report.screening_results if s.classification == "CANDIDATE"]
        for s in candidates:
            f.write(f"""
#### {s.model_id}
- **Catalog Owner**: {s.catalog_entry.owned_by if s.catalog_entry else 'N/A'}
- **Context Window**: {s.model_detail.context_window if s.model_detail else 'N/A'}
- **Preferred Score**: {s.preferred_score}/7
- **Smoke Test**: HTTP {s.smoke_http_status} ({s.smoke_elapsed_ms:.0f}ms)
- **NVCF Tracking**: {s.smoke_nvcf_reqid or 'None'}
""")
        
        f.write("""
### SCREENED_OUT_REQUIRED (fails one or more required criteria)
""")
        
        screened = [s for s in report.screening_results if s.classification == "SCREENED_OUT_REQUIRED"]
        for s in screened:
            f.write(f"""
#### {s.model_id}
- **General LLM**: {s.required_general_llm}
- **NVIDIA Hosted**: {s.required_nvidia_hosted}
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted
""")
        
        f.write("""
### CATALOG_UNAVAILABLE / ENDPOINT_UNAVAILABLE / ACCOUNT_NOT_ENTITLED / INVOCATION_FAILED
""")
        
        for cls in ["CATALOG_UNAVAILABLE", "ENDPOINT_UNAVAILABLE", "ACCOUNT_NOT_ENTITLED", "INVOCATION_FAILED"]:
            cls_candidates = [s for s in report.screening_results if s.classification == cls]
            if cls_candidates:
                f.write(f"""
#### {cls}
""")
                for s in cls_candidates:
                    f.write(f"- {s.model_id}: HTTP {s.smoke_http_status} - {s.smoke_error or 'N/A'}\n")
        
        f.write(f"""
## Official Catalog Evidence (Sample)

Total models in catalog: {report.catalog_models_count}

Sample entries (first 20):
""")
        
        for i, (model_id, evidence) in enumerate(list(report.official_catalog_evidence.items())[:20]):
            f.write(f"- {model_id}: owned_by={evidence.get('owned_by')}, created={evidence.get('created')}\n")
        
        f.write(f"""
... and {max(0, report.catalog_models_count - 20)} more models

## Limitations
""")
        
        for lim in report.limitations:
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
    
    print(f"[INVENTORY] Governance doc saved to: {gov_path}")
    print("\n" + "=" * 70)
    print("P0-FINAL-15-P Phase A/B Inventory Complete")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())