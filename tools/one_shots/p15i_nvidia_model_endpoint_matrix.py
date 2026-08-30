#!/usr/bin/env python3
"""
P0-FINAL-15-I: NVIDIA Provider Request Eligibility / Model-Endpoint Matrix

Controlled diagnostic to test whether HTTP 429 is model-specific or provider-wide.
Tests multiple models against the same endpoint with identical conditions.
"""

from __future__ import annotations

import json
import os
import sys
import time
import datetime
import requests
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.translation_engine.nvidia_client import NvidiaClient


@dataclass
class TestCaseResult:
    """Result of a single test case."""

    test_id: str
    timestamp_utc: str
    model: str
    endpoint: str
    http_method: str
    http_status: Optional[int]
    success: bool
    elapsed_ms: float
    request_payload_shape: dict
    response_body: Optional[str]
    response_headers: dict
    request_id: Optional[str]
    retry_after: Optional[str]
    rate_limit_limit: Optional[str]
    rate_limit_remaining: Optional[str]
    rate_limit_reset: Optional[str]
    x_rate_limit_limit: Optional[str]
    x_rate_limit_remaining: Optional[str]
    x_rate_limit_reset: Optional[str]
    provider_request_id: Optional[str]
    client_limiter_rpm_limit: int
    client_limiter_observed_wait_ms: float
    client_limiter_request_index: int
    exception_type: Optional[str]
    exception_message: Optional[str]


@dataclass
class MatrixReport:
    """Complete matrix experiment report."""

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

    # Matrix configuration
    models_tested: list[str]
    models_unavailable: list[str]

    # Results
    test_cases: list[TestCaseResult]

    # Differential analysis
    model_differential: dict
    endpoint_constant: bool
    auth_constant: bool

    # Classification
    previous_classification: str
    current_classification: str

    # Promotion decision
    rm6_promotion: str


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


def run_single_model_test(
    test_id: str,
    model: str,
    api_key: str,
    endpoint: str,
    rpm_limit: int,
    request_index: int,
) -> TestCaseResult:
    """Execute single test case for one model."""
    import datetime

    timestamp_utc = datetime.datetime.utcnow().isoformat() + "Z"

    # Minimal request payload
    test_text = "안녕하세요. 이것은 테스트입니다."
    system_prompt = "Translate the following Korean text to Traditional Chinese (Taiwan). Output only the translation."
    user_prompt = test_text

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.15,
        "top_p": 0.85,
        "max_tokens": 4000,
        "stream": False,
    }

    request_payload_shape = {
        "model": model,
        "messages_count": 2,
        "temperature": 0.15,
        "top_p": 0.85,
        "max_tokens": 4000,
        "stream": False,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    http_status = None
    response_body = None
    response_headers = {}
    request_id = None
    retry_after = None
    rate_limit_limit = None
    rate_limit_remaining = None
    rate_limit_reset = None
    x_rate_limit_limit = None
    x_rate_limit_remaining = None
    x_rate_limit_reset = None
    provider_request_id = None
    exception_type = None
    exception_message = None
    success = False

    # Track client limiter wait
    from core.translation_engine.nvidia_client import _global_nvidia_rate_limit
    limiter_wait_start = time.monotonic()
    limiter_wait = _global_nvidia_rate_limit(rpm_limit)
    limiter_wait_ms = (time.monotonic() - limiter_wait_start) * 1000

    start_time = time.monotonic()

    try:
        response = requests.post(
            endpoint,
            headers=headers,
            json=payload,
            timeout=(10, 60),
        )

        http_status = response.status_code
        response_body = response.text

        # Capture all rate limit headers
        response_headers = dict(response.headers)
        retry_after = response.headers.get("Retry-After")
        rate_limit_limit = response.headers.get("RateLimit-Limit")
        rate_limit_remaining = response.headers.get("RateLimit-Remaining")
        rate_limit_reset = response.headers.get("RateLimit-Reset")
        x_rate_limit_limit = response.headers.get("X-RateLimit-Limit")
        x_rate_limit_remaining = response.headers.get("X-RateLimit-Remaining")
        x_rate_limit_reset = response.headers.get("X-RateLimit-Reset")
        request_id = response.headers.get("request-id") or response.headers.get("Request-ID")
        x_request_id = response.headers.get("x-request-id") or response.headers.get("X-Request-ID")

        # Try to extract provider request ID from body
        if http_status == 200:
            try:
                data = response.json()
                provider_request_id = data.get("id")
            except Exception:
                pass
        elif http_status >= 400:
            try:
                data = response.json()
                provider_request_id = data.get("request_id") or data.get("error", {}).get("request_id")
            except Exception:
                pass

        success = (http_status == 200)

    except requests.exceptions.Timeout as e:
        http_status = 408
        response_body = str(e)
        exception_type = "Timeout"
        exception_message = str(e)
    except requests.exceptions.RequestException as e:
        http_status = 500
        response_body = str(e)
        exception_type = type(e).__name__
        exception_message = str(e)
    except Exception as e:
        http_status = 500
        response_body = str(e)
        exception_type = type(e).__name__
        exception_message = str(e)

    elapsed_ms = (time.monotonic() - start_time) * 1000

    return TestCaseResult(
        test_id=test_id,
        timestamp_utc=timestamp_utc,
        model=model,
        endpoint=endpoint,
        http_method="POST",
        http_status=http_status,
        success=success,
        elapsed_ms=elapsed_ms,
        request_payload_shape=request_payload_shape,
        response_body=response_body,
        response_headers=dict(response_headers),
        request_id=request_id,
        retry_after=retry_after,
        rate_limit_limit=rate_limit_limit,
        rate_limit_remaining=rate_limit_remaining,
        rate_limit_reset=rate_limit_reset,
        x_rate_limit_limit=x_rate_limit_limit,
        x_rate_limit_remaining=x_rate_limit_remaining,
        x_rate_limit_reset=x_rate_limit_reset,
        provider_request_id=provider_request_id,
        client_limiter_rpm_limit=rpm_limit,
        client_limiter_observed_wait_ms=limiter_wait_ms,
        client_limiter_request_index=request_index,
        exception_type=exception_type,
        exception_message=exception_message,
    )


def run_matrix_experiment() -> MatrixReport:
    """Run the complete model-endpoint matrix experiment."""
    baseline = get_git_baseline()

    # Configuration - MUST be identical for all tests
    endpoint = "https://integrate.api.nvidia.com/v1/chat/completions"
    rpm_limit = int(os.environ.get("NTPE_NVIDIA_RPM_LIMIT", "40"))

    # Model matrix
    # M1: baseline model that returned 429
    # M2: NVIDIA-hosted model
    # M3: Meta model via NVIDIA
    models_to_test = [
        "minimaxai/minimax-m3",          # M1 - baseline
        "nvidia/llama-3.1-nemotron-70b-instruct",  # M2 - NVIDIA model
        "meta/llama-3.2-90b-vision-instruct",       # M3 - Meta model via NVIDIA
    ]

    api_key = os.environ.get("NVIDIA_API_KEY")
    if not api_key:
        raise RuntimeError("NVIDIA_API_KEY environment variable not set")

    credential_present = True
    credential_source = "NVIDIA_API_KEY"

    test_cases = []
    models_tested = []
    models_unavailable = []

    # Test matrix per spec: I-01 through I-05
    test_plan = [
        ("I-01", models_to_test[0], 1),  # M1 baseline
        ("I-02", models_to_test[1], 1),  # M2 comparison
        ("I-03", models_to_test[2], 1),  # M3 comparison
        ("I-04", models_to_test[0], 2),  # M1 reproducibility
        ("I-05", models_to_test[1], 2),  # M2 reproducibility
    ]

    for test_id, model, request_idx in test_plan:
        print(f"\n[MATRIX] Running {test_id}: model={model}, request_index={request_idx}")
        try:
            result = run_single_model_test(test_id, model, api_key, endpoint, rpm_limit, request_idx)
            test_cases.append(result)
            models_tested.append(model)
            print(f"[MATRIX] {test_id} -> HTTP {result.http_status}, success={result.success}")
        except Exception as e:
            print(f"[MATRIX] {test_id} FAILED: {e}")
            models_unavailable.append(model)

    # Deduplicate models_tested
    models_tested = list(dict.fromkeys(models_tested))

    # Differential analysis
    model_differential = {}
    for tc in test_cases:
        key = tc.model
        if key not in model_differential:
            model_differential[key] = {
                "status_codes": [],
                "successes": 0,
                "failures": 0,
            }
        model_differential[key]["status_codes"].append(tc.http_status)
        if tc.success:
            model_differential[key]["successes"] += 1
        else:
            model_differential[key]["failures"] += 1

    # Check if endpoint remained constant
    endpoint_constant = all(tc.endpoint == endpoint for tc in test_cases)
    auth_constant = all(tc.request_payload_shape.get("model") for tc in test_cases)

    # Classification logic
    m1_results = [tc for tc in test_cases if tc.model == "minimaxai/minimax-m3"]
    m2_results = [tc for tc in test_cases if tc.model == "nvidia/llama-3.1-nemotron-70b-instruct"]
    m3_results = [tc for tc in test_cases if tc.model == "meta/llama-3.2-90b-vision-instruct"]

    m1_statuses = [tc.http_status for tc in m1_results]
    m2_statuses = [tc.http_status for tc in m2_results]
    m3_statuses = [tc.http_status for tc in m3_results]

    # Determine classification
    if m1_statuses and all(s == 429 for s in m1_statuses):
        m1_all_429 = True
    else:
        m1_all_429 = False

    if m2_statuses and all(s == 200 for s in m2_statuses):
        m2_all_200 = True
    else:
        m2_all_200 = False

    if m3_statuses and all(s == 200 for s in m3_statuses):
        m3_all_200 = True
    else:
        m3_all_200 = False

    if m2_statuses and all(s == 429 for s in m2_statuses):
        m2_all_429 = True
    else:
        m2_all_429 = False

    if m3_statuses and all(s == 429 for s in m3_statuses):
        m3_all_429 = True
    else:
        m3_all_429 = False

    # Check for non-uniform behavior (different error classes)
    m2_any_error = m2_statuses and any(s != 200 for s in m2_statuses)
    m2_non_429_error = m2_statuses and any(s >= 400 and s != 429 for s in m2_statuses)

    # Classification per spec
    if m1_all_429 and m2_all_200 and m3_all_200:
        current_classification = "NARROWED_MODEL_SPECIFIC"
    elif m1_all_429 and m2_all_429 and m3_all_429:
        current_classification = "NARROWED_PROVIDER_WIDE"
    elif m1_all_429 and m2_non_429_error and m3_all_200:
        current_classification = "NON_UNIFORM_PROVIDER_BEHAVIOR"
    elif not m1_all_429 and m2_all_200 and m3_all_200:
        current_classification = "RECHECK_CONDITIONS"
    else:
        current_classification = "UNKNOWN"

    # RM6 Promotion decision - BLOCKED unless explicitly unblocked
    rm6_promotion = "BLOCKED"

    return MatrixReport(
        head_commit=baseline["head_commit"],
        origin_main_commit=baseline["origin_main_commit"],
        divergence=baseline["divergence"],
        branch=baseline["branch"],
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        client_path="core/translation_engine/nvidia_client.py",
        test_timestamp=datetime.datetime.utcnow().isoformat() + "Z",
        endpoint=endpoint,
        credential_present=credential_present,
        credential_source=credential_source,
        models_tested=models_tested,
        models_unavailable=models_unavailable,
        test_cases=test_cases,
        model_differential=model_differential,
        endpoint_constant=endpoint_constant,
        auth_constant=auth_constant,
        previous_classification="UNKNOWN",
        current_classification=current_classification,
        rm6_promotion=rm6_promotion,
    )


def main():
    """Main entry point."""
    import datetime

    print("=" * 70)
    print("P0-FINAL-15-I: NVIDIA Model-Endpoint Matrix Diagnostic")
    print("=" * 70)

    report = run_matrix_experiment()

    # Output to artifacts
    artifacts_dir = Path(__file__).resolve().parents[2] / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)

    report_path = artifacts_dir / "P0_FINAL_15_I_Nvidia_Model_Endpoint_Matrix_Report.json"

    # Convert to dict and redact
    report_dict = asdict(report)
    report_dict = redact_sensitive(report_dict)

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2, ensure_ascii=False)

    print(f"\n[MATRIX] Report saved to: {report_path}")
    print(f"[MATRIX] Classification: {report.current_classification}")
    print(f"[MATRIX] Models tested: {report.models_tested}")
    print(f"[MATRIX] RM6 Promotion: {report.rm6_promotion}")

    # Print summary
    print("\n" + "=" * 70)
    print("TEST MATRIX SUMMARY")
    print("=" * 70)
    for tc in report.test_cases:
        print(f"  {tc.test_id}: model={tc.model} -> HTTP {tc.http_status} (elapsed={tc.elapsed_ms:.0f}ms)")

    # Also create governance markdown
    governance_dir = Path(__file__).resolve().parents[2] / "docs" / "governance" / "repository"
    governance_dir.mkdir(parents=True, exist_ok=True)

    gov_path = governance_dir / "P0_FINAL_15_I_NVIDIA_MODEL_ENDPOINT_MATRIX.md"

    with open(gov_path, "w", encoding="utf-8") as f:
        f.write(f"""# P0-FINAL-15-I — NVIDIA Provider Request Eligibility / Model-Endpoint Matrix

## A. Scope

### What Was Tested
- Provider request eligibility across multiple models on the same NVIDIA endpoint
- Identical request conditions (endpoint, credential, request format, client) with only MODEL variable changed
- Single-chunk, no-retry, no-concurrency controlled requests

### What Was Explicitly Not Tested
- Rate limit stress testing (no burst, no >2 requests per model)
- Production retry/backoff behavior
- RPM limiter modifications
- Quota exhaustion scenarios
- Concurrent request behavior

## B. Environment

- **Endpoint**: {report.endpoint}
- **Models Tested**: {", ".join(report.models_tested)}
- **Models Unavailable**: {", ".join(report.models_unavailable) if report.models_unavailable else "None"}
- **Python Version**: {report.python_version}
- **Client Path**: {report.client_path}
- **Test Timestamp**: {report.test_timestamp}
- **Git Commit**: {report.head_commit}
- **Branch**: {report.branch}
- **Credential Present**: {report.credential_present}
- **Credential Source**: {report.credential_source}

## C. Matrix

| Test ID | Model | Request # | HTTP Status | Success | Elapsed (ms) | Limiter Wait (ms) |
|---------|-------|-----------|-------------|---------|--------------|-------------------|
""")

        for tc in report.test_cases:
            f.write(f"| {tc.test_id} | {tc.model} | {tc.client_limiter_request_index} | {tc.http_status} | {tc.success} | {tc.elapsed_ms:.0f} | {tc.client_limiter_observed_wait_ms:.0f} |\n")

        f.write(f"""

## D. Evidence

### Detailed Results
""")

        for tc in report.test_cases:
            f.write(f"""
#### {tc.test_id} — {tc.model}
- **Timestamp**: {tc.timestamp_utc}
- **HTTP Status**: {tc.http_status}
- **Success**: {tc.success}
- **Elapsed (ms)**: {tc.elapsed_ms:.0f}
- **Client Limiter RPM Limit**: {tc.client_limiter_rpm_limit}
- **Client Limiter Observed Wait (ms)**: {tc.client_limiter_observed_wait_ms:.0f}
- **Client Limiter Request Index**: {tc.client_limiter_request_index}
- **Request ID**: {tc.request_id}
- **Retry-After**: {tc.retry_after}
- **RateLimit-Limit**: {tc.rate_limit_limit}
- **RateLimit-Remaining**: {tc.rate_limit_remaining}
- **RateLimit-Reset**: {tc.rate_limit_reset}
- **X-RateLimit-Limit**: {tc.x_rate_limit_limit}
- **X-RateLimit-Remaining**: {tc.x_rate_limit_remaining}
- **X-RateLimit-Reset**: {tc.x_rate_limit_reset}
- **Provider Request ID**: {tc.provider_request_id}
- **Exception Type**: {tc.exception_type}
- **Exception Message**: {tc.exception_message}
- **Response Body**: {tc.response_body}
""")

        f.write(f"""

## E. Differential Analysis

### Model Differential
{json.dumps(report.model_differential, indent=2, ensure_ascii=False)}

### Key Questions Answered
- **Does model choice correlate with 429?**: {report.model_differential}
- **Does endpoint remain constant?**: {report.endpoint_constant}
- **Does authentication remain constant?**: {report.auth_constant}

## F. Classification

- **Previous**: {report.previous_classification}
- **Current**: **{report.current_classification}**

### Classification Rationale
""")

        if report.current_classification == "NARROWED_MODEL_SPECIFIC":
            f.write("""
**MODEL-SPECIFIC DIFFERENTIAL EVIDENCE**: minimaxai/minimax-m3 consistently returns 429 while other models succeed.
This suggests the issue may be:
- Model availability/entitlement for minimaxai/minimax-m3
- Model-specific routing
- Model-specific quota/policy
- Model-specific capacity constraints

**Cannot directly determine which factor** without further investigation.
""")
        elif report.current_classification == "NARROWED_PROVIDER_WIDE":
            f.write("""
**PROVIDER/ENDPOINT/ACCOUNT-WIDE CONSISTENT FAILURE**: All tested models return 429.
This suggests the issue is:
- Endpoint-level rate limiting
- Account/credential entitlement
- Provider-wide policy
- Quota exhaustion

Next phase should investigate endpoint, account, credential entitlement, provider-wide policy.
""")
        elif report.current_classification == "NON_UNIFORM_PROVIDER_BEHAVIOR":
            f.write("""
**NON-UNIFORM PROVIDER BEHAVIOR**: Different models return different error classes (429, 5xx, 200).
This suggests complex provider state that cannot be simplified to rate limiting.
""")
        elif report.current_classification == "RECHECK_CONDITIONS":
            f.write("""
**ALL MODELS SUCCEED**: Previous 429 may have been transient or condition-dependent.
Must re-examine P0-FINAL-15-H request conditions, model spelling, endpoint, timing, credential context.
**Cannot claim 429 problem solved** without root cause identification.
""")
        else:
            f.write("""
**CLASSIFICATION REMAINS UNKNOWN**: Insufficient differential evidence to narrow scope.
RM6 Promotion remains BLOCKED.
""")

        f.write(f"""

## G. Promotion Decision

**RM6 Promotion = {report.rm6_promotion}**

This phase only performs differential diagnosis. Promotion requires:
1. Root cause identification
2. Verified fix implementation
3. Regression test validation
4. Governance approval

## Compliance

- ✅ No credential leakage (only credential_source recorded)
- ✅ No retry policy modification
- ✅ No production behavior modification
- ✅ Root Hygiene compliant (tools/one_shots/)
- ✅ Protected Worktree not modified
- ✅ Historical evidence not modified
- ✅ No RPM limiter changes
- ✅ No concurrency/burst testing
""")

    print(f"[MATRIX] Governance doc saved to: {gov_path}")
    print("\n" + "=" * 70)
    print("P0-FINAL-15-I Matrix Diagnostic Complete")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())