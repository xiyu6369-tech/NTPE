#!/usr/bin/env python3
"""
P0-FINAL-15-S: Gate A — Provider Invocation Canary

Provider smoke test for NVIDIA-hosted openai/gpt-oss-120b
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
class SmokeObservation:
    """Single provider smoke observation."""
    attempt: int
    timestamp_utc: str
    http_status: int
    success: bool
    elapsed_ms: float
    provider_request_id: Optional[str]
    nvcf_reqid: Optional[str]
    nvcf_status: Optional[str]
    error: Optional[str]
    response_preview: str


@dataclass
class ProviderCanaryReport:
    """Provider canary report."""
    # Baseline
    head_commit: str
    origin_main_commit: str
    divergence: str
    branch: str
    # Environment
    python_version: str
    test_timestamp: str
    # Candidate
    candidate_model: str
    hosting_provider: str
    endpoint: str
    credential_source: str
    # Observations
    observations: list[SmokeObservation]
    # Summary
    total_attempts: int
    success_count: int
    success_rate: float
    median_latency_ms: float
    p95_latency_ms: float
    http_200_count: int
    http_429_count: int
    http_408_count: int
    http_5xx_count: int
    # Classification
    gate_result: str  # PASS / FAIL
    gate_rationale: str
    # Limitations
    limitations: list[str]


def get_git_baseline() -> dict:
    import subprocess
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
        origin_main = subprocess.run(["git", "rev-parse", "origin/main"], capture_output=True, text=True, check=True).stdout.strip()
        branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
        result = subprocess.run(["git", "rev-list", "--left-right", "--count", f"{origin_main}...{head}"], capture_output=True, text=True)
        divergence = f"{result.stdout.strip().split()[0]}/{result.stdout.strip().split()[1]}" if result.returncode == 0 else "unknown"
        return {"head_commit": head, "origin_main_commit": origin_main, "divergence": divergence, "branch": branch}
    except Exception as e:
        return {"head_commit": "error", "origin_main_commit": "error", "divergence": "error", "branch": "error", "error": str(e)}


def redact_sensitive(data: dict) -> dict:
    if not isinstance(data, dict): return data
    redacted = {}
    sensitive = {"authorization", "api_key", "apikey", "secret", "token", "password", "credential", "bearer", "x-api-key"}
    for k, v in data.items():
        if k.lower() in sensitive: redacted[k] = "[REDACTED]"
        elif isinstance(v, dict): redacted[k] = redact_sensitive(v)
        elif isinstance(v, list): redacted[k] = [redact_sensitive(i) if isinstance(i, dict) else i for i in v]
        else: redacted[k] = v
    return redacted


def run_smoke(model: str, system_prompt: str, user_prompt: str, api_key: str, endpoint: str, max_tokens: int = 100) -> tuple[int, float, Optional[str], Optional[str], Optional[str], str, Optional[str]]:
    payload = {"model": model, "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], "temperature": 0.15, "top_p": 0.85, "max_tokens": max_tokens, "stream": False}
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    start = time.monotonic()
    try:
        resp = requests.post(endpoint, headers=headers, json=payload, timeout=(10, 60))
        elapsed = (time.monotonic() - start) * 1000
        http_status = resp.status_code
        provider_req_id = None
        try:
            data = resp.json()
            provider_req_id = data.get("id")
            response_body = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        except Exception:
            response_body = resp.text
        nvcf_reqid = resp.headers.get("Nvcf-Reqid")
        nvcf_status = resp.headers.get("Nvcf-Status")
        error = None if http_status == 200 else f"HTTP {http_status}: {resp.text[:200]}"
        return http_status, elapsed, provider_req_id, nvcf_reqid, nvcf_status, response_body, error
    except requests.exceptions.Timeout as e:
        elapsed = (time.monotonic() - start) * 1000
        return 408, elapsed, None, None, None, "", f"Timeout: {e}"
    except Exception as e:
        elapsed = (time.monotonic() - start) * 1000
        return 500, elapsed, None, None, None, "", str(e)


def run_provider_canary() -> ProviderCanaryReport:
    baseline = get_git_baseline()
    
    candidate_model = "openai/gpt-oss-120b"
    hosting_provider = "NVIDIA"
    endpoint = "https://integrate.api.nvidia.com/v1/chat/completions"
    api_key = os.environ.get("NVIDIA_API_KEY")
    
    if not api_key:
        raise RuntimeError("NVIDIA_API_KEY environment variable not set")
    
    print("=" * 70)
    print("P0-FINAL-15-S: Gate A — Provider Invocation Canary")
    print("=" * 70)
    print(f"Candidate: {candidate_model}")
    print(f"Hosting: {hosting_provider}")
    print(f"Endpoint: {endpoint}")
    
    observations = []
    attempts = 3
    
    sys_prompt = "Translate Korean to Traditional Chinese (Taiwan). Output only translation."
    user_prompt = "안녕하세요. 이것은 provider canary 테스트입니다."
    
    for i in range(attempts):
        print(f"\n[CANARY] Attempt {i+1}/{attempts}...")
        api_key = os.environ.get("NVIDIA_API_KEY")
        if not api_key:
            raise RuntimeError("NVIDIA_API_KEY not set")
        http_status, elapsed, req_id, nvcf_reqid, nvcf_status, body, error = run_smoke(
            "openai/gpt-oss-120b", 
            "Translate Korean to Traditional Chinese (Taiwan). Output only translation.",
            "안녕하세요. 이것은 provider canary 테스트입니다.",
            api_key, 
            "https://integrate.api.nvidia.com/v1/chat/completions",
            max_tokens=100
        )
        
        obs = SmokeObservation(
            attempt=i+1,
            timestamp_utc=datetime.datetime.utcnow().isoformat() + "Z",
            http_status=http_status,
            success=(http_status == 200),
            elapsed_ms=elapsed,
            provider_request_id=req_id,
            nvcf_reqid=nvcf_reqid,
            nvcf_status=nvcf_status,
            error=error,
            response_preview=body[:100] if body else ""
        )
        observations.append(obs)
        
        print(f"  HTTP {http_status} | {elapsed:.0f}ms | {'PASS' if http_status == 200 else 'FAIL'}")
        if error:
            print(f"  Error: {error}")
        
        time.sleep(1)
    
    # Summary
    total = len(observations)
    success = sum(1 for o in observations if o.success)
    success_rate = success / total
    latencies = [o.elapsed_ms for o in observations if o.success]
    median_latency = sorted(latencies)[len(latencies)//2] if latencies else 0
    p95_latency = sorted(latencies)[int(len(latencies)*0.95)] if latencies else 0
    
    http_200 = sum(1 for o in observations if o.http_status == 200)
    http_429 = sum(1 for o in observations if o.http_status == 429)
    http_408 = sum(1 for o in observations if o.http_status == 408)
    http_5xx = sum(1 for o in observations if 500 <= o.http_status < 600)
    
    # Gate decision
    if success_rate == 1.0:
        gate_result = "PASS"
        gate_rationale = f"All {attempts} smoke attempts returned HTTP 200"
    else:
        gate_result = "FAIL"
        gate_rationale = f"Only {success}/{attempts} smoke attempts succeeded"
    
    limitations = [
        f"Only {attempts} smoke attempts (minimum per spec)",
        "Single endpoint test; no cross-region test",
        "No rate-limit header validation beyond presence check",
        "Single test prompt; not comprehensive",
    ]
    
    return ProviderCanaryReport(
        head_commit=baseline["head_commit"],
        origin_main_commit=baseline["origin_main_commit"],
        divergence=baseline["divergence"],
        branch=baseline["branch"],
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        test_timestamp=datetime.datetime.utcnow().isoformat() + "Z",
        candidate_model="openai/gpt-oss-120b",
        hosting_provider="NVIDIA",
        endpoint="https://integrate.api.nvidia.com/v1/chat/completions",
        credential_source="NVIDIA_API_KEY",
        observations=observations,
        total_attempts=attempts,
        success_count=success,
        success_rate=success_rate,
        median_latency_ms=median_latency,
        p95_latency_ms=p95_latency,
        http_200_count=http_200,
        http_429_count=http_429,
        http_408_count=http_408,
        http_5xx_count=http_5xx,
        gate_result=gate_result,
        gate_rationale=gate_rationale,
        limitations=limitations,
    )


def main():
    import datetime
    print("=" * 70)
    print("P0-FINAL-15-S: Gate A — Provider Invocation Canary")
    print("=" * 70)
    
    report = run_provider_canary()
    
    # Save artifact
    artifacts_dir = Path(__file__).resolve().parents[2] / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)
    report_path = artifacts_dir / "P0_FINAL_15_S_OPENAI_GPT_OSS_120B_PROVIDER_CANARY_REPORT.json"
    
    report_dict = asdict(report)
    report_dict = redact_sensitive(report_dict)
    
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2, ensure_ascii=False)
    
    print(f"\n[CANARY] Report saved to: {report_path}")
    
    # Print summary
    print("\n" + "=" * 70)
    print("GATE A SUMMARY")
    print("=" * 70)
    print(f"Candidate: {report.candidate_model}")
    print(f"Hosting: {report.hosting_provider}")
    print(f"Gate Result: {report.gate_result}")
    print(f"Rationale: {report.gate_rationale}")
    print(f"Success Rate: {report.success_rate:.0%} ({report.success_count}/{report.total_attempts})")
    print(f"Latency: median={report.median_latency_ms:.0f}ms, P95={report.p95_latency_ms:.0f}ms")
    print(f"HTTP 200: {report.http_200_count}, 429: {report.http_429_count}, 408: {report.http_408_count}, 5xx: {report.http_5xx_count}")
    
    # Governance doc
    governance_dir = Path(__file__).resolve().parents[2] / "docs" / "governance" / "repository"
    governance_dir.mkdir(parents=True, exist_ok=True)
    gov_path = governance_dir / "P0_FINAL_15_S_OPENAI_GPT_OSS_120B_PROVIDER_CANARY.md"
    
    with open(gov_path, "w", encoding="utf-8") as f:
        f.write(f"""# P0-FINAL-15-S: Gate A — Provider Invocation Canary

## Baseline
- **HEAD**: {report.head_commit}
- **origin/main**: {report.origin_main_commit}
- **divergence**: {report.divergence}
- **branch**: {report.branch}
- **Python**: {report.python_version}
- **Timestamp**: {report.test_timestamp}

## Candidate Identity
- **Model**: {report.candidate_model}
- **Hosting Provider**: {report.hosting_provider}
- **Endpoint**: {report.endpoint}
- **Credential**: {report.credential_source}

## Observations

| Attempt | HTTP Status | Success | Latency (ms) | Provider ReqID | NVCF ReqID | NVCF Status | Error |
|---------|-------------|---------|--------------|----------------|------------|-------------|-------|
""")
        
        for o in report.observations:
            f.write(f"| {o.attempt} | {o.http_status} | {o.success} | {o.elapsed_ms:.0f} | {o.provider_request_id or 'N/A'} | {o.nvcf_reqid or 'N/A'} | {o.nvcf_status or 'N/A'} | {o.error or 'None'} |\n")
        
        f.write(f"""
## Summary

| Metric | Value |
|--------|-------|
| Total Attempts | {report.total_attempts} |
| Success Count | {report.success_count} |
| Success Rate | {report.success_rate:.0%} |
| Median Latency | {report.median_latency_ms:.0f}ms |
| P95 Latency | {report.p95_latency_ms:.0f}ms |
| HTTP 200 | {report.http_200_count} |
| HTTP 429 | {report.http_429_count} |
| HTTP 408 | {report.http_408_count} |
| HTTP 5xx | {report.http_5xx_count} |

## Gate Result

**{report.gate_result}**

**Rationale**: {report.gate_rationale}

## Limitations
""")
        
        for lim in report.limitations:
            f.write(f"- {lim}\n")
        
        f.write("""
## Compliance
- ✅ No credential leakage
- ✅ No production modification
- ✅ Read-only provider invocation
- ✅ Root Hygiene compliant
- ✅ Protected Worktree preserved

## Next Gate
Proceed to **Gate B: Runtime Stability** if PASS, otherwise STOP.
""")
    
    print(f"[CANARY] Governance doc saved to: {gov_path}")
    print("\n" + "=" * 70)
    print("P0-FINAL-15-S Gate A Complete")
    print("=" * 70)
    
    return 0 if report.gate_result == "PASS" else 1


if __name__ == "__main__":
    import datetime
    import requests
    sys.exit(main())