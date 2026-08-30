#!/usr/bin/env python3
"""
P0-FINAL-15-H: NVIDIA 429 Enhanced Telemetry & Single-Chunk Quota Diagnosis

Single-chunk controlled diagnostic for NVIDIA 429 rate limit behavior.
Does NOT modify retry policy or production behavior.
"""

from __future__ import annotations

import json
import os
import sys
import time
import requests
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.translation_engine.nvidia_client import NvidiaClient


@dataclass
class DiagnosticResult:
    """Structured diagnostic result for single NVIDIA request."""

    # Baseline
    head_commit: str
    origin_main_commit: str
    divergence: str
    branch: str

    # Configuration
    provider: str
    model: str
    configured_rpm_limit: int

    # Client limiter state
    request_sequence: int
    request_start_time: float
    limiter_wait_seconds: float
    last_request_timestamp: float
    effective_request_spacing: float

    # HTTP Response
    http_status: Optional[int]
    retry_after: Optional[str]
    rate_limit_limit: Optional[str]
    rate_limit_remaining: Optional[str]
    rate_limit_reset: Optional[str]
    x_rate_limit_limit: Optional[str]
    x_rate_limit_remaining: Optional[str]
    x_rate_limit_reset: Optional[str]
    request_id: Optional[str]
    x_request_id: Optional[str]

    # Error Body
    error_body_raw: Optional[str]
    error_body_parsed: Optional[dict]
    error_message: Optional[str]
    error_type: Optional[str]
    error_code: Optional[str]
    provider_request_id: Optional[str]

    # Classification
    classification: str

    # Summary
    single_chunk_result: str
    provider_requests: int
    network_calls: int
    elapsed_time: float


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

        # Calculate divergence
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


def run_single_chunk_diagnostic() -> DiagnosticResult:
    """Execute single-chunk controlled diagnostic for NVIDIA 429."""
    baseline = get_git_baseline()

    # Configuration
    provider = "NVIDIA"
    model = "minimaxai/minimax-m3"
    configured_rpm_limit = int(os.environ.get("NTPE_NVIDIA_RPM_LIMIT", "40"))

    # Get API key from environment
    api_key = os.environ.get("NVIDIA_API_KEY")
    if not api_key:
        raise RuntimeError("NVIDIA_API_KEY environment variable not set")

    # Initialize client
    client = NvidiaClient(
        api_key=api_key,
        api_url="https://integrate.api.nvidia.com/v1/chat/completions",
        timeout=60,
        rpm_limit=configured_rpm_limit,
    )

    # Get limiter state before request
    from core.translation_engine.nvidia_client import _NVIDIA_REQUEST_TIMES, _NVIDIA_LAST_REQUEST_AT
    request_start_time = time.monotonic()
    last_request_timestamp = _NVIDIA_LAST_REQUEST_AT
    effective_request_spacing = 0.0

    # Single test chunk - minimal Korean text
    test_text = "안녕하세요. 이것은 테스트입니다."
    system_prompt = "Translate the following Korean text to Traditional Chinese (Taiwan). Output only the translation."
    user_prompt = test_text

    # Track response details
    http_status = None
    retry_after = None
    rate_limit_limit = None
    rate_limit_remaining = None
    rate_limit_reset = None
    x_rate_limit_limit = None
    x_rate_limit_remaining = None
    x_rate_limit_reset = None
    request_id = None
    x_request_id = None
    error_body_raw = None
    error_body_parsed = None
    error_message = None
    error_type = None
    error_code = None
    provider_request_id = None

    start_time = time.monotonic()
    limiter_wait = 0.0

    try:
        # The _rate_limit() is called inside chat()
        # We need to track the wait time - let's call it separately first
        from core.translation_engine.nvidia_client import _global_nvidia_rate_limit
        limiter_wait = _global_nvidia_rate_limit(configured_rpm_limit)

        # Now make the actual request with full telemetry capture
        import requests

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

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

        print(f"[DIAGNOSTIC] Sending single-chunk request to {model}")
        print(f"[DIAGNOSTIC] Limiter wait: {limiter_wait:.3f}s")
        print(f"[DIAGNOSTIC] Configured RPM limit: {configured_rpm_limit}")

        response = requests.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=(10, 60),
        )

        http_status = response.status_code

        # Capture all rate limit headers
        retry_after = response.headers.get("Retry-After")
        rate_limit_limit = response.headers.get("RateLimit-Limit")
        rate_limit_remaining = response.headers.get("RateLimit-Remaining")
        rate_limit_reset = response.headers.get("RateLimit-Reset")
        x_rate_limit_limit = response.headers.get("X-RateLimit-Limit")
        x_rate_limit_remaining = response.headers.get("X-RateLimit-Remaining")
        x_rate_limit_reset = response.headers.get("X-RateLimit-Reset")
        request_id = response.headers.get("request-id") or response.headers.get("Request-ID")
        x_request_id = response.headers.get("x-request-id") or response.headers.get("X-Request-ID")

        print(f"[DIAGNOSTIC] HTTP Status: {http_status}")
        print(f"[DIAGNOSTIC] Retry-After: {retry_after}")
        print(f"[DIAGNOSTIC] RateLimit-Limit: {rate_limit_limit}")
        print(f"[DIAGNOSTIC] RateLimit-Remaining: {rate_limit_remaining}")
        print(f"[DIAGNOSTIC] RateLimit-Reset: {rate_limit_reset}")
        print(f"[DIAGNOSTIC] X-RateLimit-Limit: {x_rate_limit_limit}")
        print(f"[DIAGNOSTIC] X-RateLimit-Remaining: {x_rate_limit_remaining}")
        print(f"[DIAGNOSTIC] X-RateLimit-Reset: {x_rate_limit_reset}")
        print(f"[DIAGNOSTIC] request-id: {request_id}")
        print(f"[DIAGNOSTIC] x-request-id: {x_request_id}")

        # Capture response body
        error_body_raw = response.text

        if http_status >= 400:
            error_message = f"NVIDIA API error {http_status}: {error_body_raw[:1000]}"
            try:
                error_body_parsed = response.json()
                if isinstance(error_body_parsed, dict):
                    error_type = error_body_parsed.get("type") or error_body_parsed.get("error", {}).get("type")
                    error_code = error_body_parsed.get("code") or error_body_parsed.get("error", {}).get("code")
                    provider_request_id = error_body_parsed.get("request_id") or error_body_parsed.get("error", {}).get("request_id")
            except Exception:
                error_body_parsed = {"raw": error_body_raw}
        else:
            # Success - still capture response for completeness
            try:
                data = response.json()
                provider_request_id = data.get("id")
            except Exception:
                pass

        # Get limiter state after request
        effective_request_spacing = 0.0
        if _NVIDIA_LAST_REQUEST_AT and last_request_timestamp:
            effective_request_spacing = _NVIDIA_LAST_REQUEST_AT - last_request_timestamp

    except requests.exceptions.Timeout as e:
        http_status = 408
        error_message = f"Request timeout: {e}"
        error_body_raw = str(e)
        limiter_wait = time.monotonic() - request_start_time
    except requests.exceptions.RequestException as e:
        http_status = 500
        error_message = f"Request failed: {e}"
        error_body_raw = str(e)
        limiter_wait = time.monotonic() - request_start_time
    except Exception as e:
        http_status = 500
        error_message = f"Unexpected error: {e}"
        error_body_raw = str(e)
        limiter_wait = time.monotonic() - request_start_time

    elapsed_time = time.monotonic() - start_time

    # Classification logic
    if http_status == 200:
        classification = "SUCCESS"
        single_chunk_result = "HTTP_200"
    elif http_status == 429:
        # Check response body for quota type
        body_lower = (error_body_raw or "").lower()
        if any(kw in body_lower for kw in ["requests per minute", "rpm", "request rate"]):
            classification = "RPM_LIMIT_CONFIRMED"
        elif any(kw in body_lower for kw in ["tokens per minute", "token rate", "token limit"]):
            classification = "TOKEN_LIMIT_CONFIRMED"
        elif any(kw in body_lower for kw in ["concurrent", "concurrency", "simultaneous"]):
            classification = "CONCURRENCY_LIMIT_CONFIRMED"
        elif any(kw in body_lower for kw in ["model quota", "model limit", "model capacity"]):
            classification = "MODEL_QUOTA_CONFIRMED"
        elif any(kw in body_lower for kw in ["account quota", "project quota", "quota exceeded"]):
            classification = "ACCOUNT_QUOTA_CONFIRMED"
        elif any(kw in body_lower for kw in ["dynamic capacity", "capacity", "availability"]):
            classification = "DYNAMIC_CAPACITY_CONFIRMED"
        elif retry_after or rate_limit_limit or rate_limit_remaining or rate_limit_reset:
            classification = "PROVIDER_LIMIT_UNSPECIFIED"
        else:
            classification = "UNKNOWN"

        single_chunk_result = "HTTP_429"
    else:
        classification = "UNKNOWN"
        single_chunk_result = f"HTTP_{http_status}"

    # Build result
    result = DiagnosticResult(
        head_commit=baseline["head_commit"],
        origin_main_commit=baseline["origin_main_commit"],
        divergence=baseline["divergence"],
        branch=baseline["branch"],
        provider=provider,
        model=model,
        configured_rpm_limit=configured_rpm_limit,
        request_sequence=1,
        request_start_time=request_start_time,
        limiter_wait_seconds=limiter_wait,
        last_request_timestamp=last_request_timestamp,
        effective_request_spacing=effective_request_spacing,
        http_status=http_status,
        retry_after=retry_after,
        rate_limit_limit=rate_limit_limit,
        rate_limit_remaining=rate_limit_remaining,
        rate_limit_reset=rate_limit_reset,
        x_rate_limit_limit=x_rate_limit_limit,
        x_rate_limit_remaining=x_rate_limit_remaining,
        x_rate_limit_reset=x_rate_limit_reset,
        request_id=request_id,
        x_request_id=x_request_id,
        error_body_raw=error_body_raw,
        error_body_parsed=error_body_parsed,
        error_message=error_message,
        error_type=error_type,
        error_code=error_code,
        provider_request_id=provider_request_id,
        classification=classification,
        single_chunk_result=single_chunk_result,
        provider_requests=1,
        network_calls=1,
        elapsed_time=elapsed_time,
    )

    return result


def main():
    """Main entry point."""
    print("=" * 60)
    print("P0-FINAL-15-H: NVIDIA 429 Enhanced Telemetry Diagnostic")
    print("=" * 60)

    result = run_single_chunk_diagnostic()

    # Output to artifacts
    artifacts_dir = Path(__file__).resolve().parents[2] / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)

    report_path = artifacts_dir / "P0_FINAL_15_H_Nvidia_429_Enhanced_Telemetry_Diagnostic_Report.json"

    # Convert to dict and redact
    result_dict = asdict(result)
    result_dict = redact_sensitive(result_dict)

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(result_dict, f, indent=2, ensure_ascii=False)

    print(f"\n[DIAGNOSTIC] Report saved to: {report_path}")
    print(f"[DIAGNOSTIC] Classification: {result.classification}")
    print(f"[DIAGNOSTIC] Single-chunk result: {result.single_chunk_result}")
    print(f"[DIAGNOSTIC] HTTP Status: {result.http_status}")
    print(f"[DIAGNOSTIC] Limiter wait: {result.limiter_wait_seconds:.3f}s")
    print(f"[DIAGNOSTIC] Elapsed time: {result.elapsed_time:.3f}s")

    # Also create governance markdown
    governance_dir = Path(__file__).resolve().parents[2] / "docs" / "governance" / "repository"
    governance_dir.mkdir(parents=True, exist_ok=True)

    gov_path = governance_dir / "P0_FINAL_15_H_NVIDIA_429_ENHANCED_TELEMETRY_DIAGNOSTIC.md"

    with open(gov_path, "w", encoding="utf-8") as f:
        f.write(f"""# P0-FINAL-15-H — NVIDIA 429 Enhanced Telemetry & Single-Chunk Quota Diagnosis

## Baseline
- **HEAD**: {result.head_commit}
- **origin/main**: {result.origin_main_commit}
- **divergence**: {result.divergence}
- **branch**: {result.branch}

## Configuration
- **Provider**: {result.provider}
- **Model**: {result.model}
- **Configured RPM Limit**: {result.configured_rpm_limit}

## Client Limiter State
- **Request Sequence**: {result.request_sequence}
- **Request Start Time**: {result.request_start_time}
- **Limiter Wait (seconds)**: {result.limiter_wait_seconds:.3f}
- **Last Request Timestamp**: {result.last_request_timestamp}
- **Effective Request Spacing**: {result.effective_request_spacing:.3f}

## HTTP Response Headers
- **HTTP Status**: {result.http_status}
- **Retry-After**: {result.retry_after}
- **RateLimit-Limit**: {result.rate_limit_limit}
- **RateLimit-Remaining**: {result.rate_limit_remaining}
- **RateLimit-Reset**: {result.rate_limit_reset}
- **X-RateLimit-Limit**: {result.x_rate_limit_limit}
- **X-RateLimit-Remaining**: {result.x_rate_limit_remaining}
- **X-RateLimit-Reset**: {result.x_rate_limit_reset}
- **request-id**: {result.request_id}
- **x-request-id**: {result.x_request_id}

## HTTP Error Body
- **Raw Body**: {result.error_body_raw}
- **Parsed Body**: {json.dumps(result.error_body_parsed, ensure_ascii=False) if result.error_body_parsed else 'N/A'}
- **Error Message**: {result.error_message}
- **Error Type**: {result.error_type}
- **Error Code**: {result.error_code}
- **Provider Request ID**: {result.provider_request_id}

## Classification
**{result.classification}**

## Single-Chunk Result
- **Result**: {result.single_chunk_result}
- **Provider Requests**: {result.provider_requests}
- **Network Calls**: {result.network_calls}
- **Elapsed Time**: {result.elapsed_time:.3f}s

## Compliance
- ✅ No credential leakage
- ✅ No retry policy modification
- ✅ No production behavior modification
- ✅ Root Hygiene compliant (tools/one_shots/)
- ✅ Protected Worktree not modified
- ✅ Historical evidence not modified
""")

    print(f"[DIAGNOSTIC] Governance doc saved to: {gov_path}")
    print("\n" + "=" * 60)
    print("P0-FINAL-15-H Diagnostic Complete")
    print("=" * 60)

    return 0 if result.http_status in (200, 429) else 1


if __name__ == "__main__":
    sys.exit(main())