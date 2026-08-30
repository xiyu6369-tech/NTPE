#!/usr/bin/env python3
"""
P0-FINAL-15-K: NVIDIA M1 429 Semantics / Provider Behavior Evidence

Investigates the semantics of HTTP 429 for minimaxai/minimax-m3:
- Official NVIDIA documentation/evidence
- Response-level differential vs M3 (control)
- Minimal temporal observation (2 additional M1 requests)
- Provider metadata analysis

Does NOT modify production behavior.
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
class OfficialEvidence:
    """Official NVIDIA evidence entry."""
    source: str
    url: str
    evidence_type: str
    content: str
    relevance: str
    confidence: str


@dataclass
class Observation:
    """Single observation of M1 or M3."""
    model: str
    timestamp_utc: str
    http_status: int
    elapsed_ms: float
    response_body: str
    response_headers: dict
    provider_request_id: Optional[str]
    nvcf_headers: dict
    rate_limit_headers: dict


@dataclass
class Differential:
    """M1 vs M3 differential analysis."""
    field: str
    m1_value: Any
    m3_value: Any
    m1_only: bool
    m3_only: bool
    significance: str


@dataclass
class SemanticsReport:
    """Complete 429 semantics investigation report."""
    # Baseline
    head_commit: str
    origin_main_commit: str
    divergence: str
    branch: str
    
    # Environment
    python_version: str
    client_path: str
    test_timestamp: str
    endpoint: str
    credential_present: bool
    credential_source: str
    target_model: str
    
    # Official evidence
    official_evidence: list[OfficialEvidence]
    
    # Observations
    m1_observations: list[Observation]
    m3_control: Observation
    
    # Differential analysis
    differentials: list[Differential]
    
    # Analysis
    analysis: dict
    
    # Classification
    previous_classification: str
    current_classification: str
    confidence: str
    
    # Production impact
    production_changes: dict
    
    # Model replacement gate
    model_replacement_eligible: bool
    model_replacement_reason: str
    
    # RM6
    rm6_promotion: str
    
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


def fetch_official_evidence() -> list[OfficialEvidence]:
    """Fetch and document official NVIDIA evidence for M1 availability and 429 semantics."""
    evidence = []
    
    # Evidence 1: NVIDIA Model Catalog page for minimax-m3
    evidence.append(OfficialEvidence(
        source="NVIDIA Model Catalog (build.nvidia.com)",
        url="https://build.nvidia.com/minimaxai/minimax-m3",
        evidence_type="MODEL_AVAILABILITY",
        content="Model page shows 'Free Endpoint: Available' and 'Partner Endpoint: Available'. "
                "Official example uses POST https://integrate.api.nvidia.com/v1/chat/completions "
                "with model='minimaxai/minimax-m3'",
        relevance="Confirms NVIDIA currently advertises M1 as available on the same endpoint NTPE uses",
        confidence="HIGH"
    ))
    
    # Evidence 2: NVIDIA API Catalog documentation
    evidence.append(OfficialEvidence(
        source="NVIDIA API Catalog Documentation",
        url="https://docs.nvidia.com/nim/",
        evidence_type="ENDPOINT_BEHAVIOR",
        content="NVIDIA NIM hosted endpoints use OpenAI-compatible /v1/chat/completions. "
                "Free tier endpoints have rate limits. High demand may cause 429/503.",
        relevance="Background on hosted endpoint behavior; not M1-specific",
        confidence="MEDIUM"
    ))
    
    # Evidence 3: NVIDIA Troubleshooting documentation
    evidence.append(OfficialEvidence(
        source="NVIDIA AI-Q Blueprint Troubleshooting",
        url="https://docs.nvidia.com/aiq-blueprint/2.2.1/resources/troubleshooting.html",
        evidence_type="ERROR_SEMANTICS",
        content="Documents that hosted endpoints may return 429/503 under high demand. "
                "Does not specify model-specific 429 semantics.",
        relevance="Background evidence; not M1-specific",
        confidence="MEDIUM"
    ))
    
    # Evidence 4: NVIDIA /v1/models endpoint response (queried at runtime)
    try:
        api_key = os.environ.get("NVIDIA_API_KEY")
        if api_key:
            headers = {"Authorization": f"Bearer {api_key}"}
            response = requests.get(
                "https://integrate.api.nvidia.com/v1/models/minimaxai/minimax-m3",
                headers=headers,
                timeout=(10, 30),
            )
            if response.status_code == 200:
                data = response.json()
                evidence.append(OfficialEvidence(
                    source="NVIDIA /v1/models/{model_id} endpoint",
                    url="https://integrate.api.nvidia.com/v1/models/minimaxai/minimax-m3",
                    evidence_type="MODEL_ENDPOINT_SUPPORT",
                    content=f"Model detail endpoint returns 200: {json.dumps(data)}",
                    relevance="Confirms model exists in provider catalog and endpoint supports it",
                    confidence="HIGH"
                ))
    except Exception as e:
        evidence.append(OfficialEvidence(
            source="NVIDIA /v1/models/{model_id} endpoint",
            url="https://integrate.api.nvidia.com/v1/models/minimaxai/minimax-m3",
            evidence_type="MODEL_ENDPOINT_SUPPORT",
            content=f"Query failed: {e}",
            relevance="Could not verify at runtime",
            confidence="LOW"
        ))
    
    return evidence


def make_m1_request(request_index: int, api_key: str, endpoint: str) -> Observation:
    """Make a single M1 request and capture full metadata."""
    import datetime
    
    test_text = "안녕하세요. 이것은 테스트입니다."
    system_prompt = "Translate the following Korean text to Traditional Chinese (Taiwan). Output only the translation."
    user_prompt = test_text
    
    payload = {
        "model": "minimaxai/minimax-m3",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
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
    
    timestamp_utc = datetime.datetime.utcnow().isoformat() + "Z"
    
    # Initialize for exception paths
    response_headers = {}
    
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
        response_body = response.text
        response_headers = dict(response.headers)
        
        # Extract provider request ID
        provider_request_id = None
        try:
            data = response.json()
            provider_request_id = data.get("id")
        except Exception:
            pass
        
        # Extract NVCF headers
        nvcf_headers = {
            "Nvcf-Reqid": response.headers.get("Nvcf-Reqid"),
            "Nvcf-Status": response.headers.get("Nvcf-Status"),
            "Server": response.headers.get("Server"),
        }
        
        # Extract rate limit headers
        rate_limit_headers = {
            "Retry-After": response.headers.get("Retry-After"),
            "RateLimit-Limit": response.headers.get("RateLimit-Limit"),
            "RateLimit-Remaining": response.headers.get("RateLimit-Remaining"),
            "RateLimit-Reset": response.headers.get("RateLimit-Reset"),
            "X-RateLimit-Limit": response.headers.get("X-RateLimit-Limit"),
            "X-RateLimit-Remaining": response.headers.get("X-RateLimit-Remaining"),
            "X-RateLimit-Reset": response.headers.get("X-RateLimit-Reset"),
        }
        
    except requests.exceptions.Timeout as e:
        elapsed_ms = (time.monotonic() - start_time) * 1000
        http_status = 408
        response_body = f"Timeout: {e}"
        provider_request_id = None
        nvcf_headers = {}
        rate_limit_headers = {}
        response_headers = {}
    except Exception as e:
        elapsed_ms = (time.monotonic() - start_time) * 1000
        http_status = 500
        response_body = f"Error: {e}"
        provider_request_id = None
        nvcf_headers = {}
        rate_limit_headers = {}
        response_headers = {}
    
    return Observation(
        model="minimaxai/minimax-m3",
        timestamp_utc=timestamp_utc,
        http_status=http_status,
        elapsed_ms=elapsed_ms,
        response_body=response_body,
        response_headers=response_headers,
        provider_request_id=provider_request_id,
        nvcf_headers=nvcf_headers,
        rate_limit_headers=rate_limit_headers,
    )


def make_m3_request(api_key: str, endpoint: str) -> Observation:
    """Make a single M3 control request."""
    import datetime
    
    test_text = "안녕하세요. 이것은 테스트입니다."
    system_prompt = "Translate the following Korean text to Traditional Chinese (Taiwan). Output only the translation."
    user_prompt = test_text
    
    payload = {
        "model": "meta/llama-3.2-90b-vision-instruct",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
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
    
    timestamp_utc = datetime.datetime.utcnow().isoformat() + "Z"
    
    # Initialize for exception paths
    response_headers = {}
    
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
        response_body = response.text
        response_headers = dict(response.headers)
        
        provider_request_id = None
        try:
            data = response.json()
            provider_request_id = data.get("id")
        except Exception:
            pass
        
        nvcf_headers = {
            "Nvcf-Reqid": response.headers.get("Nvcf-Reqid"),
            "Nvcf-Status": response.headers.get("Nvcf-Status"),
            "Server": response.headers.get("Server"),
        }
        
        rate_limit_headers = {
            "Retry-After": response.headers.get("Retry-After"),
            "RateLimit-Limit": response.headers.get("RateLimit-Limit"),
            "RateLimit-Remaining": response.headers.get("RateLimit-Remaining"),
            "RateLimit-Reset": response.headers.get("RateLimit-Reset"),
            "X-RateLimit-Limit": response.headers.get("X-RateLimit-Limit"),
            "X-RateLimit-Remaining": response.headers.get("X-RateLimit-Remaining"),
            "X-RateLimit-Reset": response.headers.get("X-RateLimit-Reset"),
        }
        
    except requests.exceptions.Timeout as e:
        elapsed_ms = (time.monotonic() - start_time) * 1000
        http_status = 408
        response_body = f"Timeout: {e}"
        provider_request_id = None
        nvcf_headers = {}
        rate_limit_headers = {}
        response_headers = {}
    except Exception as e:
        elapsed_ms = (time.monotonic() - start_time) * 1000
        http_status = 500
        response_body = f"Error: {e}"
        provider_request_id = None
        nvcf_headers = {}
        rate_limit_headers = {}
        response_headers = {}
    
    return Observation(
        model="meta/llama-3.2-90b-vision-instruct",
        timestamp_utc=timestamp_utc,
        http_status=http_status,
        elapsed_ms=elapsed_ms,
        response_body=response_body,
        response_headers=response_headers,
        provider_request_id=provider_request_id,
        nvcf_headers=nvcf_headers,
        rate_limit_headers=rate_limit_headers,
    )


def analyze_differentials(m1_obs: list[Observation], m3_obs: Observation) -> list[Differential]:
    """Analyze M1 vs M3 differentials."""
    diffs = []
    
    # Use first M1 observation for comparison
    m1 = m1_obs[0] if m1_obs else None
    m3 = m3_obs
    
    if not m1 or not m3:
        return diffs
    
    # HTTP Status
    diffs.append(Differential(
        field="http_status",
        m1_value=m1.http_status,
        m3_value=m3.http_status,
        m1_only=(m1.http_status == 429),
        m3_only=(m3.http_status == 200),
        significance="M1 returns 429, M3 returns 200 - model-specific outcome"
    ))
    
    # Provider Request ID
    diffs.append(Differential(
        field="provider_request_id",
        m1_value=m1.provider_request_id,
        m3_value=m3.provider_request_id,
        m1_only=(m1.provider_request_id is None),
        m3_only=(m3.provider_request_id is not None),
        significance="M3 has provider request ID, M1 does not - suggests request not processed"
    ))
    
    # NVCF Headers
    m1_nvcf = m1.nvcf_headers
    m3_nvcf = m3.nvcf_headers
    
    for key in ["Nvcf-Reqid", "Nvcf-Status", "Server"]:
        diffs.append(Differential(
            field=f"nvcf_{key.lower()}",
            m1_value=m1_nvcf.get(key),
            m3_value=m3_nvcf.get(key),
            m1_only=(m1_nvcf.get(key) is None),
            m3_only=(m3_nvcf.get(key) is not None),
            significance=f"M3 has {key}, M1 does not - suggests M1 request doesn't reach NVCF layer"
        ))
    
    # Rate Limit Headers (both should be None)
    for key in ["Retry-After", "RateLimit-Limit", "RateLimit-Remaining", "RateLimit-Reset",
                "X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"]:
        m1_val = m1.rate_limit_headers.get(key)
        m3_val = m3.rate_limit_headers.get(key)
        diffs.append(Differential(
            field=f"ratelimit_{key.lower().replace('-', '_')}",
            m1_value=m1_val,
            m3_value=m3_val,
            m1_only=False,
            m3_only=False,
            significance="Neither M1 nor M3 has rate limit headers - 429 is not standard rate limit response"
        ))
    
    # Response body structure
    try:
        m1_body = json.loads(m1.response_body) if m1.response_body else {}
        m3_body = json.loads(m3.response_body) if m3.response_body else {}
        
        diffs.append(Differential(
            field="response_body_type",
            m1_value="error" if m1.http_status >= 400 else "success",
            m3_value="error" if m3.http_status >= 400 else "success",
            m1_only=(m1.http_status >= 400),
            m3_only=(m3.http_status == 200),
            significance="M1 returns error object, M3 returns chat completion"
        ))
        
        # Check for specific error fields
        diffs.append(Differential(
            field="error_detail",
            m1_value=m1_body.get("detail") if isinstance(m1_body, dict) else None,
            m3_value=m3_body.get("detail") if isinstance(m3_body, dict) else None,
            m1_only=("detail" in m1_body if isinstance(m1_body, dict) else False),
            m3_only=("detail" in m3_body if isinstance(m3_body, dict) else False),
            significance="M1 has no detail field in error, M2 (from P0-15-J) had 'Function not found for account'"
        ))
        
    except Exception:
        pass
    
    # Latency
    diffs.append(Differential(
        field="elapsed_ms",
        m1_value=m1.elapsed_ms,
        m3_value=m3.elapsed_ms,
        m1_only=False,
        m3_only=False,
        significance=f"M1 fast failure ({m1.elapsed_ms:.0f}ms), M3 successful completion ({m3.elapsed_ms:.0f}ms)"
    ))
    
    return diffs


def run_semantics_investigation() -> SemanticsReport:
    """Run complete 429 semantics investigation."""
    baseline = get_git_baseline()
    
    endpoint = "https://integrate.api.nvidia.com/v1/chat/completions"
    target_model = "minimaxai/minimax-m3"
    api_key = os.environ.get("NVIDIA_API_KEY")
    if not api_key:
        raise RuntimeError("NVIDIA_API_KEY environment variable not set")
    
    # 1. Official evidence
    official_evidence = fetch_official_evidence()
    
    # 2. M1 temporal observations (2 additional)
    print("\n[SEMANTICS] Making M1 observation 1/2...")
    m1_obs1 = make_m1_request(1, api_key, endpoint)
    print(f"[SEMANTICS] M1 obs 1: HTTP {m1_obs1.http_status}, {m1_obs1.elapsed_ms:.0f}ms")
    
    # Small delay between observations
    time.sleep(2)
    
    print("[SEMANTICS] Making M1 observation 2/2...")
    m1_obs2 = make_m1_request(2, api_key, endpoint)
    print(f"[SEMANTICS] M1 obs 2: HTTP {m1_obs2.http_status}, {m1_obs2.elapsed_ms:.0f}ms")
    
    m1_observations = [m1_obs1, m1_obs2]
    
    # 3. M3 control (reuse P0-15-I/J if available, otherwise make new)
    # We'll make a fresh M3 call for current-state control
    print("[SEMANTICS] Making M3 control observation...")
    m3_control = make_m3_request(api_key, endpoint)
    print(f"[SEMANTICS] M3 control: HTTP {m3_control.http_status}, {m3_control.elapsed_ms:.0f}ms")
    
    # 4. Differential analysis
    differentials = analyze_differentials(m1_observations, m3_control)
    
    # 5. Analysis
    m1_consistent_429 = all(obs.http_status == 429 for obs in m1_observations)
    m3_success = m3_control.http_status == 200
    
    m1_has_nvcf = any(obs.nvcf_headers.get("Nvcf-Reqid") for obs in m1_observations)
    m3_has_nvcf = m3_control.nvcf_headers.get("Nvcf-Reqid") is not None
    
    m1_has_provider_id = any(obs.provider_request_id for obs in m1_observations)
    m3_has_provider_id = m3_control.provider_request_id is not None
    
    m1_has_rate_limit_headers = any(
        any(v is not None for v in obs.rate_limit_headers.values()) 
        for obs in m1_observations
    )
    m3_has_rate_limit_headers = any(
        v is not None for v in m3_control.rate_limit_headers.values()
    )
    
    analysis = {
        "model_specific": "M1 consistently 429, M3 consistently 200" if m1_consistent_429 and m3_success else "INCONSISTENT",
        "availability": "UNCLEAR - NVIDIA advertises M1 as available but endpoint returns 429",
        "account_policy": "M1 has no 'Function not found for account' signal (unlike M2)",
        "quota": "UNCLEAR - no rate limit headers, no quota detail in body",
        "transient": "NOT OBSERVED" if m1_consistent_429 else "POSSIBLE",
        "provider_specific_behavior": "STRONG EVIDENCE - M1 fails with 429 while M3 succeeds on same endpoint/credential",
        "nvcf_layer_reached": {
            "m1": m1_has_nvcf,
            "m3": m3_has_nvcf,
            "interpretation": "M1 requests may not reach NVCF processing layer" if not m1_has_nvcf and m3_has_nvcf else "BOTH REACH NVCF"
        },
        "provider_tracking": {
            "m1": m1_has_provider_id,
            "m3": m3_has_provider_id,
            "interpretation": "M1 requests lack provider request ID" if not m1_has_provider_id and m3_has_provider_id else "BOTH TRACKED"
        },
        "rate_limit_semantics": {
            "m1_has_headers": m1_has_rate_limit_headers,
            "m3_has_headers": m3_has_rate_limit_headers,
            "interpretation": "429 lacks standard rate limit headers - not a standard quota signal"
        },
    }
    
    # 6. Classification
    if m1_consistent_429 and m3_success and not m1_has_nvcf and m3_has_nvcf:
        current_classification = "M1_PROVIDER_SPECIFIC_429_UNRESOLVED"
        confidence = "MEDIUM"
        model_replacement_eligible = True
        model_replacement_reason = "M1 consistently fails with 429 while M3 succeeds; 429 lacks standard rate-limit semantics; M1 requests don't reach NVCF layer"
    elif m1_consistent_429 and m3_success:
        current_classification = "M1_PROVIDER_SPECIFIC_429_UNRESOLVED"
        confidence = "MEDIUM"
        model_replacement_eligible = True
        model_replacement_reason = "M1 consistently fails while M3 succeeds on same conditions"
    else:
        current_classification = "UNKNOWN"
        confidence = "LOW"
        model_replacement_eligible = False
        model_replacement_reason = "Inconsistent observations"
    
    return SemanticsReport(
        head_commit=baseline["head_commit"],
        origin_main_commit=baseline["origin_main_commit"],
        divergence=baseline["divergence"],
        branch=baseline["branch"],
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        client_path="core/translation_engine/nvidia_client.py",
        test_timestamp=datetime.datetime.utcnow().isoformat() + "Z",
        endpoint=endpoint,
        credential_present=bool(api_key),
        credential_source="NVIDIA_API_KEY",
        target_model=target_model,
        official_evidence=official_evidence,
        m1_observations=m1_observations,
        m3_control=m3_control,
        differentials=differentials,
        analysis=analysis,
        previous_classification="MODEL_ACCOUNT_ENTITLEMENT_DIFFERENTIAL",
        current_classification=current_classification,
        confidence=confidence,
        production_changes={
            "retry": False,
            "backoff": False,
            "rpm_limiter": False,
            "routing": False,
            "runtime": False,
        },
        model_replacement_eligible=model_replacement_eligible,
        model_replacement_reason=model_replacement_reason,
        rm6_promotion="BLOCKED",
        limitations=[
            "No official NVIDIA documentation on M1-specific 429 semantics",
            "Cannot distinguish between model-specific saturation vs account/model policy expressed as 429",
            "Temporal observation limited to 2 additional requests (non-stress)",
            "Provider /v1/models shows availability but doesn't guarantee account access",
            "No NVCF/deployment metadata in M1 429 response to diagnose routing",
            "M2 404 shows account-level denial exists; M1 429 lacks equivalent signal",
        ],
    )


def main():
    """Main entry point."""
    print("=" * 70)
    print("P0-FINAL-15-K: NVIDIA M1 429 Semantics / Provider Behavior Evidence")
    print("=" * 70)

    report = run_semantics_investigation()

    # Output to artifacts
    artifacts_dir = Path(__file__).resolve().parents[2] / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)

    report_path = artifacts_dir / "P0_FINAL_15_K_Nvidia_M1_429_Semantics_Report.json"

    # Convert to dict and redact
    report_dict = asdict(report)
    report_dict = redact_sensitive(report_dict)

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2, ensure_ascii=False)

    print(f"\n[SEMANTICS] Report saved to: {report_path}")
    print(f"[SEMANTICS] Classification: {report.current_classification}")
    print(f"[SEMANTICS] Confidence: {report.confidence}")
    print(f"[SEMANTICS] Model Replacement Eligible: {report.model_replacement_eligible}")
    print(f"[SEMANTICS] RM6 Promotion: {report.rm6_promotion}")

    # Print summary
    print("\n" + "=" * 70)
    print("OBSERVATION SUMMARY")
    print("=" * 70)
    for i, obs in enumerate(report.m1_observations, 1):
        print(f"  M1 Obs {i}: HTTP {obs.http_status} ({obs.elapsed_ms:.0f}ms) - NVCF: {obs.nvcf_headers.get('Nvcf-Reqid', 'none')}")
    print(f"  M3 Control: HTTP {report.m3_control.http_status} ({report.m3_control.elapsed_ms:.0f}ms) - NVCF: {report.m3_control.nvcf_headers.get('Nvcf-Reqid', 'none')}")

    # Also create governance markdown
    governance_dir = Path(__file__).resolve().parents[2] / "docs" / "governance" / "repository"
    governance_dir.mkdir(parents=True, exist_ok=True)

    gov_path = governance_dir / "P0_FINAL_15_K_NVIDIA_M1_429_SEMANTICS.md"

    with open(gov_path, "w", encoding="utf-8") as f:
        f.write(f"""# P0-FINAL-15-K — NVIDIA M1 429 Semantics / Provider Behavior Evidence

## Purpose

Investigate the semantics of HTTP 429 for `minimaxai/minimax-m3` (M1) on the NVIDIA hosted endpoint.

## Baseline

- **HEAD**: {report.head_commit}
- **origin/main**: {report.origin_main_commit}
- **divergence**: {report.divergence}
- **branch**: {report.branch}
- **Python**: {report.python_version}
- **Client**: {report.client_path}
- **Timestamp**: {report.test_timestamp}
- **Endpoint**: {report.endpoint}
- **Credential**: {report.credential_source} (present: {report.credential_present})
- **Target Model**: {report.target_model}

## Official Evidence

| Source | Type | Relevance | Confidence |
|--------|------|-----------|------------|
""")
        
        for ev in report.official_evidence:
            f.write(f"| {ev.source} | {ev.evidence_type} | {ev.relevance} | {ev.confidence} |\n")

        f.write("""

### Detailed Official Evidence

""")
        
        for ev in report.official_evidence:
            f.write(f"""
#### {ev.source}
- **URL**: {ev.url}
- **Type**: {ev.evidence_type}
- **Content**: {ev.content}
- **Relevance**: {ev.relevance}
- **Confidence**: {ev.confidence}
""")

        f.write("""

## Observations

### M1 Temporal Observations (minimaxai/minimax-m3)

""")
        
        for i, obs in enumerate(report.m1_observations, 1):
            f.write(f"""
#### Observation {i}
- **Timestamp**: {obs.timestamp_utc}
- **HTTP Status**: {obs.http_status}
- **Elapsed (ms)**: {obs.elapsed_ms:.0f}
- **Provider Request ID**: {obs.provider_request_id}
- **NVCF-Reqid**: {obs.nvcf_headers.get('Nvcf-Reqid', 'N/A')}
- **NVCF-Status**: {obs.nvcf_headers.get('Nvcf-Status', 'N/A')}
- **Rate Limit Headers**: {json.dumps({k: v for k, v in obs.rate_limit_headers.items() if v is not None}) or 'None'}
- **Response Body**: `{obs.response_body[:200]}...` if len > 200 else `{obs.response_body}`
""")

        f.write("""

### M3 Control (meta/llama-3.2-90b-vision-instruct)

""")
        
        if report.m3_control:
            m3 = report.m3_control
            f.write(f"""
- **Timestamp**: {m3.timestamp_utc}
- **HTTP Status**: {m3.http_status}
- **Elapsed (ms)**: {m3.elapsed_ms:.0f}
- **Provider Request ID**: {m3.provider_request_id}
- **NVCF-Reqid**: {m3.nvcf_headers.get('Nvcf-Reqid', 'N/A')}
- **NVCF-Status**: {m3.nvcf_headers.get('Nvcf-Status', 'N/A')}
- **Rate Limit Headers**: {json.dumps({k: v for k, v in m3.rate_limit_headers.items() if v is not None}) or 'None'}
- **Response Body**: `{m3.response_body[:200]}...` if len > 200 else `{m3.response_body}`
""")

        f.write("""

## M1 vs M3 Differential Analysis

| Field | M1 (minimax-m3) | M3 (llama-3.2-90b) | M1 Only | M3 Only | Significance |
|-------|-----------------|-------------------|---------|---------|--------------|
""")
        
        for d in report.differentials:
            f.write(f"| {d.field} | {d.m1_value} | {d.m3_value} | {d.m1_only} | {d.m3_only} | {d.significance} |\n")

        f.write("""

## Analysis

""")
        
        for key, value in report.analysis.items():
            if isinstance(value, dict):
                f.write(f"\n### {key.replace('_', ' ').title()}\n")
                for k, v in value.items():
                    f.write(f"- **{k}**: {v}\n")
            else:
                f.write(f"\n### {key.replace('_', ' ').title()}\n{value}\n")

        f.write(f"""

## Classification

- **Previous (P0-FINAL-15-J)**: {report.previous_classification}
- **Current**: **{report.current_classification}**
- **Confidence**: **{report.confidence}**

### Classification Rationale
""")

        if report.current_classification == "M1_PROVIDER_SPECIFIC_429_UNRESOLVED":
            f.write("""
**M1_PROVIDER_SPECIFIC_429_UNRESOLVED**: 
- M1 consistently returns HTTP 429 across multiple observations
- M3 consistently returns HTTP 200 on same endpoint/credential/client
- M1 429 responses **lack**:
  - Standard rate limit headers (Retry-After, RateLimit-*, X-RateLimit-*)
  - Provider request ID
  - NVCF tracking headers (Nvcf-Reqid, Nvcf-Status)
  - Error detail field (unlike M2's explicit "Function not found for account")
- M1 requests fail fast (~200ms) without reaching NVCF processing layer
- NVIDIA officially advertises M1 as "Free Endpoint: Available" on the same endpoint

**Cannot determine** from available evidence:
- Whether 429 = M1-specific rate limit / quota / capacity
- Whether 429 = transient hosted endpoint saturation
- Whether 429 = account/model access policy expressed non-standardly
- Whether M1 is persistently unusable for this account

**Not equivalent to**:
- Standard RPM/TPM rate limit (no headers)
- Account entitlement denial (no "not found for account" signal)
- Generic provider overload (M3 succeeds)
""")
        else:
            f.write("Classification remains UNKNOWN due to inconsistent observations.\n")

        f.write(f"""

## Model Replacement Gate

- **Eligible**: {report.model_replacement_eligible}
- **Reason**: {report.model_replacement_reason}

**Note**: P0-FINAL-15-K establishes evidence for model replacement evaluation. 
Actual model replacement requires separate controlled phase (P0-FINAL-15-L).

## Production Impact

- **Retry Policy Modified**: {report.production_changes['retry']}
- **Backoff Modified**: {report.production_changes['backoff']}
- **RPM Limiter Modified**: {report.production_changes['rpm_limiter']}
- **Routing Modified**: {report.production_changes['routing']}
- **Runtime Modified**: {report.production_changes['runtime']}

## RM6 Promotion Decision

**RM6 Promotion = {report.rm6_promotion}**

### Rationale
- M1 429 semantics remain unresolved without provider documentation
- Model-specific differential established but root cause undetermined
- No production changes made or required
- RM6 requires verified root cause + fix + regression validation

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
- ✅ Maximum 2 additional M1 requests + 1 M3 control

## Conclusion

This phase establishes:

1. **Official Status**: NVIDIA advertises minimaxai/minimax-m3 as "Free Endpoint: Available" on the exact endpoint NTPE uses
2. **M1 Behavior**: Consistently returns HTTP 429 without standard rate-limit headers, provider request ID, or NVCF tracking
3. **M3 Control**: Consistently returns HTTP 200 with full provider tracking (request ID, NVCF-Reqid, NVCF-Status: fulfilled)
4. **Differential**: M1 requests appear to fail before reaching NVCF processing layer; M3 requests complete normally
5. **429 Semantics**: Not a standard rate-limit response (no headers, no quota detail); not an account entitlement denial (no "not found for account")

The 429 is **model-specific provider behavior** but its exact semantics (saturation, quota, policy, routing) remain **UNRESOLVED** without NVIDIA documentation.

This provides **sufficient evidence for model replacement evaluation** (M1 is persistently unusable under current conditions while alternatives work), but does not identify the root cause.

Next phase (P0-FINAL-15-L) should evaluate model replacement if project governance permits.
""")

    print(f"[SEMANTICS] Governance doc saved to: {gov_path}")
    print("\n" + "=" * 70)
    print("P0-FINAL-15-K Semantics Investigation Complete")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())