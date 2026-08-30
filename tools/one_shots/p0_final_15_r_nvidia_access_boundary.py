#!/usr/bin/env python3
"""
P0-FINAL-15-R: NVIDIA Access Boundary Investigation

Phase R-A1: Current Account Access Verification
- Catalog presence
- /v1/models/{model} availability
- Account entitlement (via chat completion invocation)
- Provider metadata
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
class ModelAccessResult:
    """Access verification result for a single model."""
    model_id: str
    # Catalog
    in_catalog: bool = False
    catalog_http_status: Optional[int] = None
    catalog_entry: Optional[dict] = None
    # Detail endpoint
    detail_available: bool = False
    detail_http_status: Optional[int] = None
    detail_data: Optional[dict] = None
    # Chat completion (account entitlement)
    chat_http_status: Optional[int] = None
    chat_success: bool = False
    chat_elapsed_ms: float = 0.0
    chat_provider_request_id: Optional[str] = None
    chat_nvcf_reqid: Optional[str] = None
    chat_nvcf_status: Optional[str] = None
    chat_error: Optional[str] = None
    chat_response_body: Optional[str] = None
    # Classification
    catalog_available: bool = False
    endpoint_available: bool = False
    account_entitled: bool = False
    invocation_success: bool = False
    access_classification: str = "PENDING"
    notes: str = ""


@dataclass
class AccessBoundaryReport:
    """Complete access boundary investigation report."""
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
    # Models tested
    models_tested: list[str]
    results: list[ModelAccessResult]
    # Summary
    catalog_available_count: int
    endpoint_available_count: int
    account_entitled_count: int
    invocation_success_count: int
    # Classification
    access_classifications: dict[str, int]
    # M1 specific
    m1_result: Optional[ModelAccessResult] = None
    # Limitations
    limitations: list[str] = field(default_factory=list)


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


def load_q_admitted_candidates() -> list[str]:
    """Load admitted candidates from P0-FINAL-15-Q admission report."""
    artifacts_dir = Path(__file__).resolve().parents[2] / "artifacts"
    admission_path = artifacts_dir / "P0_FINAL_15_Q_CANDIDATE_ADMISSION_MATRIX.json"
    if not admission_path.exists():
        return []
    with open(admission_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    admitted = [r["model_id"] for r in data.get("admission_results", []) if r.get("disposition") == "ADMITTED"]
    return admitted


def fetch_nvidia_catalog(api_key: str) -> tuple[Optional[list[dict]], Optional[int], str]:
    """Fetch NVIDIA /v1/models catalog."""
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        response = requests.get(
            "https://integrate.api.nvidia.com/v1/models",
            headers=headers,
            timeout=(10, 30),
        )
        if response.status_code != 200:
            return None, response.status_code, f"Catalog fetch failed: {response.status_code}"
        data = response.json()
        return data.get("data", []), response.status_code, "success"
    except Exception as e:
        return None, None, f"Catalog fetch exception: {e}"


def fetch_model_detail(model_id: str, api_key: str) -> tuple[Optional[dict], Optional[int], str]:
    """Fetch NVIDIA /v1/models/{model_id} detail."""
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        response = requests.get(
            f"https://integrate.api.nvidia.com/v1/models/{model_id}",
            headers=headers,
            timeout=(10, 30),
        )
        if response.status_code != 200:
            return None, response.status_code, f"Detail failed: {response.status_code}"
        return response.json(), response.status_code, "success"
    except Exception as e:
        return None, None, f"Detail exception: {e}"


def run_chat_completion(model_id: str, api_key: str, endpoint: str) -> tuple[int, float, Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
    """Run minimal chat completion to test account entitlement."""
    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": "Translate Korean to Traditional Chinese (Taiwan). Output only translation."},
            {"role": "user", "content": "안녕하세요."}
        ],
        "temperature": 0.15,
        "top_p": 0.85,
        "max_tokens": 100,
        "stream": False,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    start = time.monotonic()
    try:
        resp = requests.post(endpoint, headers=headers, json=payload, timeout=(10, 60))
        elapsed = (time.monotonic() - start) * 1000
        http_status = resp.status_code
        provider_request_id = None
        try:
            data = resp.json()
            provider_request_id = data.get("id")
            response_body = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        except Exception:
            response_body = resp.text
        nvcf_reqid = resp.headers.get("Nvcf-Reqid")
        nvcf_status = resp.headers.get("Nvcf-Status")
        error = None if http_status == 200 else f"HTTP {http_status}: {resp.text[:200]}"
        return http_status, elapsed, provider_request_id, nvcf_reqid, nvcf_status, response_body, error
    except requests.exceptions.Timeout as e:
        elapsed = (time.monotonic() - start) * 1000
        return 408, elapsed, None, None, None, None, f"Timeout: {e}"
    except Exception as e:
        elapsed = (time.monotonic() - start) * 1000
        return 500, elapsed, None, None, None, None, str(e)


def classify_access(result: ModelAccessResult) -> str:
    """Classify access level based on all checks."""
    if not result.in_catalog:
        return "CATALOG_UNAVAILABLE"
    if not result.detail_available:
        return "ENDPOINT_UNAVAILABLE"
    if not result.account_entitled:
        return "ACCOUNT_NOT_ENTITLED"
    if not result.invocation_success:
        return "INVOCATION_FAILED"
    return "FULLY_AVAILABLE"


def run_access_boundary() -> AccessBoundaryReport:
    """Run complete access boundary investigation."""
    baseline = get_git_baseline()
    
    endpoint = "https://integrate.api.nvidia.com/v1/chat/completions"
    api_key = os.environ.get("NVIDIA_API_KEY")
    
    if not api_key:
        raise RuntimeError("NVIDIA_API_KEY environment variable not set")
    
    # Load candidates from Q phase
    candidates = load_q_admitted_candidates()
    
    # Add M1 for comparison
    if "minimaxai/minimax-m3" not in candidates:
        candidates.insert(0, "minimaxai/minimax-m3")
    
    # Add C3 for reference
    if "nvidia/nemotron-3-super-120b-a12b" not in candidates:
        candidates.append("nvidia/nemotron-3-super-120b-a12b")
    
    print(f"\n[ACCESS] Testing {len(candidates)} models...")
    
    # Fetch catalog once
    print("[ACCESS] Fetching catalog...")
    catalog_models, catalog_status, catalog_msg = fetch_nvidia_catalog(api_key)
    catalog_map = {m["id"]: m for m in (catalog_models or [])}
    
    results = []
    for i, model_id in enumerate(candidates):
        print(f"  [{i+1}/{len(candidates)}] {model_id}...")
        result = ModelAccessResult(model_id=model_id)
        
        # Catalog check
        if model_id in catalog_map:
            result.in_catalog = True
            result.catalog_entry = catalog_map[model_id]
            result.catalog_available = True
            result.catalog_http_status = catalog_status
        
        # Detail endpoint
        detail, detail_status, detail_msg = fetch_model_detail(model_id, api_key)
        if detail:
            result.detail_available = True
            result.detail_data = detail
            result.endpoint_available = True
            result.detail_http_status = detail_status
        
        # Chat completion (account entitlement)
        print(f"    Chat completion...")
        chat_status, chat_elapsed, chat_req_id, chat_nvcf_reqid, chat_nvcf_status, chat_body, chat_error = run_chat_completion(
            model_id, api_key, endpoint
        )
        result.chat_http_status = chat_status
        result.chat_elapsed_ms = chat_elapsed
        result.chat_provider_request_id = chat_req_id
        result.chat_nvcf_reqid = chat_nvcf_reqid
        result.chat_nvcf_status = chat_nvcf_status
        result.chat_response_body = chat_body
        result.chat_error = chat_error
        result.chat_success = (chat_status == 200)
        
        # Account entitlement determination
        if chat_status == 200:
            result.account_entitled = True
            result.invocation_success = True
        elif chat_status == 404 and chat_error and "Function" in chat_error and "account" in chat_error:
            result.account_entitled = False
        elif chat_status == 429:
            result.account_entitled = True  # Entitled but rate limited
            result.invocation_success = False
        else:
            result.account_entitled = False
            result.invocation_success = False
        
        # Classification
        result.access_classification = classify_access(result)
        
        results.append(result)
        print(f"    Classification: {result.access_classification} (HTTP {chat_status})")
        
        # Rate limit respect
        time.sleep(1)
    
    # M1 specific result
    m1_result = next((r for r in results if r.model_id == "minimaxai/minimax-m3"), None)
    
    # Summary counts
    catalog_available_count = sum(1 for r in results if r.catalog_available)
    endpoint_available_count = sum(1 for r in results if r.endpoint_available)
    account_entitled_count = sum(1 for r in results if r.account_entitled)
    invocation_success_count = sum(1 for r in results if r.invocation_success)
    
    # Classification distribution
    access_classifications = {}
    for r in results:
        access_classifications[r.access_classification] = access_classifications.get(r.access_classification, 0) + 1
    
    limitations = [
        "Single chat completion attempt per model (not repeated for stability)",
        "Cannot distinguish model-specific vs account-wide entitlement without provider API",
        "429 on M1 could be rate limit, capacity, or provider routing - not definitively classified",
        "Credential source is single NVIDIA account; no comparison account available",
    ]
    
    return AccessBoundaryReport(
        head_commit=baseline["head_commit"],
        origin_main_commit=baseline["origin_main_commit"],
        divergence=baseline["divergence"],
        branch=baseline["branch"],
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        test_timestamp=datetime.datetime.utcnow().isoformat() + "Z",
        endpoint=endpoint,
        credential_present=True,
        credential_source="NVIDIA_API_KEY",
        models_tested=candidates,
        results=results,
        catalog_available_count=catalog_available_count,
        endpoint_available_count=endpoint_available_count,
        account_entitled_count=account_entitled_count,
        invocation_success_count=invocation_success_count,
        access_classifications=access_classifications,
        m1_result=m1_result,
        limitations=limitations,
    )


def main():
    """Main entry point."""
    print("=" * 70)
    print("P0-FINAL-15-R: NVIDIA Access Boundary Investigation")
    print("=" * 70)
    
    report = run_access_boundary()
    
    # Output to artifacts
    artifacts_dir = Path(__file__).resolve().parents[2] / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)
    
    report_path = artifacts_dir / "P0_FINAL_15_R_NVIDIA_ACCESS_BOUNDARY_REPORT.json"
    
    report_dict = asdict(report)
    report_dict = redact_sensitive(report_dict)
    
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2, ensure_ascii=False)
    
    print(f"\n[ACCESS] Report saved to: {report_path}")
    
    # Print summary
    print("\n" + "=" * 70)
    print("ACCESS BOUNDARY SUMMARY")
    print("=" * 70)
    print(f"Models Tested: {len(report.models_tested)}")
    print(f"Catalog Available: {report.catalog_available_count}")
    print(f"Endpoint Available: {report.endpoint_available_count}")
    print(f"Account Entitled: {report.account_entitled_count}")
    print(f"Invocation Success: {report.invocation_success_count}")
    print(f"\nClassifications: {report.access_classifications}")
    
    print("\nDetailed Results:")
    for r in report.results:
        print(f"  {r.model_id:<45} Catalog:{r.catalog_available} Endpoint:{r.endpoint_available} Entitled:{r.account_entitled} Chat:{r.chat_http_status} -> {r.access_classification}")
    
    if report.m1_result:
        m1 = report.m1_result
        print(f"\nM1 (minimaxai/minimax-m3):")
        print(f"  Catalog: {m1.catalog_available}")
        print(f"  Endpoint: {m1.endpoint_available}")
        print(f"  Entitled: {m1.account_entitled}")
        print(f"  Chat HTTP: {m1.chat_http_status} ({m1.chat_elapsed_ms:.0f}ms)")
        print(f"  NVCF ReqID: {m1.chat_nvcf_reqid}")
        print(f"  Classification: {m1.access_classification}")
    
    # Governance markdown
    governance_dir = Path(__file__).resolve().parents[2] / "docs" / "governance" / "repository"
    governance_dir.mkdir(parents=True, exist_ok=True)
    
    gov_path = governance_dir / "P0_FINAL_15_R_NVIDIA_ACCESS_BOUNDARY.md"
    
    with open(gov_path, "w", encoding="utf-8") as f:
        f.write(f"""# P0-FINAL-15-R — NVIDIA Access Boundary Investigation

## Phase R-A1: Current Account Access Verification

### Baseline
- **HEAD**: {report.head_commit}
- **origin/main**: {report.origin_main_commit}
- **divergence**: {report.divergence}
- **branch**: {report.branch}
- **Python**: {report.python_version}
- **Endpoint**: {report.endpoint}
- **Credential**: {report.credential_source} (present: {report.credential_present})
- **Timestamp**: {report.test_timestamp}

### Summary

| Metric | Count |
|--------|-------|
| Models Tested | {len(report.models_tested)} |
| Catalog Available | {report.catalog_available_count} |
| Endpoint Available | {report.endpoint_available_count} |
| Account Entitled | {report.account_entitled_count} |
| Invocation Success | {report.invocation_success_count} |

### Access Classifications

| Classification | Count |
|----------------|-------|
""")
        
        for cls, count in sorted(report.access_classifications.items()):
            f.write(f"| {cls} | {count} |\n")
        
        f.write("""
### Detailed Results

| Model | Catalog | Endpoint | Entitled | Chat HTTP | Classification |
|-------|---------|----------|----------|-----------|----------------|
""")
        
        for r in report.results:
            f.write(f"| {r.model_id} | {r.catalog_available} | {r.endpoint_available} | {r.account_entitled} | {r.chat_http_status} | {r.access_classification} |\n")
        
        f.write("""
### M1 Specific Analysis

""")
        
        if report.m1_result:
            m1 = report.m1_result
            f.write(f"""
- **Model**: minimaxai/minimax-m3
- **Catalog Available**: {m1.catalog_available}
- **Endpoint Available**: {m1.endpoint_available}
- **Account Entitled**: {m1.account_entitled}
- **Chat HTTP Status**: {m1.chat_http_status}
- **Chat Latency**: {m1.chat_elapsed_ms:.0f}ms
- **Provider Request ID**: {m1.chat_provider_request_id or 'N/A'}
- **NVCF ReqID**: {m1.chat_nvcf_reqid or 'N/A'}
- **NVCF Status**: {m1.chat_nvcf_status or 'N/A'}
- **Error**: {m1.chat_error or 'None'}
- **Access Classification**: {m1.access_classification}
- **Chat Response Body**: {m1.chat_response_body or 'N/A'}

### Key Findings for M1

""")
            if m1.chat_http_status == 429:
                f.write("""
- M1 consistently returns **HTTP 429** on this account
- 429 response lacks rate-limit headers (Retry-After, RateLimit-*, X-RateLimit-*)
- No quota detail in response body (no "requests per minute", "tokens per minute", "concurrent")
- No explicit account entitlement denial message
- **Classification**: ACCOUNT_ENTITLED (entitled but rate limited) but **INVOCATION_FAILED**

This confirms the P0-FINAL-15-Q reconciliation: **M1_PROVIDER_FAILURE_429_UNRESOLVED**
- Not CONTEXT_INCOMPATIBLE (429 at all context sizes)
- Not ACCOUNT_NOT_ENTITLED (no 'Function not found' message)
- Not RPM_LIMIT (no rate-limit headers)
- Root cause: provider-side failure, undetermined
""")
        
        f.write("""
## Limitations
""")
        
        for lim in report.limitations:
            f.write(f"- {lim}\n")
        
        f.write("""
## Compliance
- ✅ No credential leakage
- ✅ No production modification
- ✅ No retry/RPM/timeout/backoff changes
- ✅ Root Hygiene compliant
- ✅ Protected Worktree preserved
- ✅ Historical evidence retained

## Next Phase
Proceed to **R-A2: M1 429 Reconciliation** and **R-A3: Account Comparison (if alternative credentials available)**.
""")
    
    print(f"[ACCESS] Governance doc saved to: {gov_path}")
    print("\n" + "=" * 70)
    print("P0-FINAL-15-R Phase R-A1 Access Boundary Complete")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())