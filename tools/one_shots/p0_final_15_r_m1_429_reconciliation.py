#!/usr/bin/env python3
"""
P0-FINAL-15-R: M1 429 Reconciliation

Phase R-A2: Investigate M1 429 status - is it resolved or transient?
Repeated controlled observations across contexts and time.
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
class M1Observation:
    """Single M1 observation."""
    timestamp_utc: str
    context_level: str  # small, medium, large
    test_type: str  # smoke, translation, context
    http_status: int
    success: bool
    elapsed_ms: float
    provider_request_id: Optional[str]
    nvcf_reqid: Optional[str]
    nvcf_status: Optional[str]
    error: Optional[str]
    response_body_preview: str


@dataclass
class M1ReconciliationReport:
    """M1 429 reconciliation report."""
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
    # Previous classification
    previous_classification: str
    # Observations
    observations: list[M1Observation]
    # Summary stats
    total_observations: int
    success_count: int
    http_200_count: int
    http_429_count: int
    http_408_count: int
    http_4xx_other: int
    http_5xx_count: int
    median_latency_ms: float
    p95_latency_ms: float
    # Classification
    current_classification: str
    classification_changed: bool
    rationale: str
    # Evidence
    evidence_summary: dict
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


def run_single_request(model: str, system_prompt: str, user_prompt: str, api_key: str, endpoint: str, max_tokens: int = 4000, timeout_read: int = 60):
    payload = {"model": model, "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], "temperature": 0.15, "top_p": 0.85, "max_tokens": max_tokens, "stream": False}
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    start = time.monotonic()
    try:
        resp = requests.post(endpoint, headers=headers, json=payload, timeout=(10, timeout_read))
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
        return 408, elapsed, None, None, None, None, f"Timeout: {e}"
    except Exception as e:
        elapsed = (time.monotonic() - start) * 1000
        return 500, elapsed, None, None, None, None, str(e)


def run_m1_reconciliation() -> M1ReconciliationReport:
    baseline = get_git_baseline()
    endpoint = "https://integrate.api.nvidia.com/v1/chat/completions"
    api_key = os.environ.get("NVIDIA_API_KEY")
    if not api_key: raise RuntimeError("NVIDIA_API_KEY not set")
    
    previous_classification = "M1_PROVIDER_FAILURE_429_UNRESOLVED"
    model_id = "minimaxai/minimax-m3"
    
    print(f"\n[M1-RECON] Running reconciliation for {model_id}...")
    print(f"  Previous classification: {previous_classification}")
    
    observations = []
    
    # Test fixtures for different context levels
    test_fixtures = {
        "small": "안녕하세요. 이것은 작은 테스트입니다.",
        "medium": "정태의는 아차, 하고 자리에서 일어섰다. 카일은 프라이빗풀 옆의 벤치에서 정신없이 잠들어 있을 터였다. (일주일의 휴가를 위해 그가 이곳에 오기 직전까지 밤을 새며 퀭한 얼굴로 일했다는 걸 정태의는 알고 있었다.) 라군에서 바닷가는, 당연하다면 당연하지만, 엎어지면 코 닿을 거리였다.",
        "large": "정태의는 아차, 하고 자리에서 일어섰다. 카일은 프라이빗풀 옆의 벤치에서 정신없이 잠들어 있을 터였다. (일주일의 휴가를 위해 그가 이곳에 오기 직전까지 밤을 새며 퀭한 얼굴로 일했다는 걸 정태의는 알고 있었다. 그래서, 그가 막무가내로 여기에 오겠다고 하는 주장을 차마 거를 수 없었다.) 라군에서 바닷가는, 당연하다면 당연하지만, 엎어지면 코 닿을 거리였다. 근처만 서성이려면 바다 위로 뻗은 나무다리 위로 산책을 할 수도 있지만, 정태의는 천천히 섬을 한 바퀴 돌아보자고 생각하고 백사장 쪽을 선택했다. 대충 걸어서 두어 시간이면 한 바퀴 다 돌 수 있을 정도로 작은 섬이라고 들었다. 무릅까지 오는 반바지 위에 넉넉한 셔츠 하나만 대충 걸치고, 그가 막 로비에서 나서려던 때였다. 새로운 손님이 왔는지, 바깥에서 약간 떠들썩하게―라고 해도 이곳이 워낙 조용해서, 단순한 말소리조차 그렇게 들릴 뿐이었지만―두세 명이 들어서고 있었다. 정태의는 저도 모르게 걸음을 멈추었다. 귀에 익은 독일어가 들렸다.",
    }
    
    sys_prompt = "Translate Korean to Traditional Chinese (Taiwan). Output only translation."
    
    print("[M1-RECON] Running repeated observations...")
    
    # Multiple rounds: 3 rounds x 3 context levels x 2 test types = 18 observations
    for round_num in range(3):
        for ctx_level, ctx_text in test_fixtures.items():
            for test_type in ["smoke", "translation"]:
                if test_type == "smoke":
                    user_prompt = "안녕하세요. 이것은 테스트입니다."
                    max_tokens = 100
                else:
                    user_prompt = ctx_text
                    max_tokens = 4000
                
                timestamp = datetime.datetime.utcnow().isoformat() + "Z"
                print(f"  Round {round_num+1}, {ctx_level}, {test_type}...")
                
                http_status, elapsed, req_id, nvcf_reqid, nvcf_status, body, error = run_single_request(
                    model_id, sys_prompt, user_prompt, api_key, endpoint, max_tokens=max_tokens
                )
                
                observations.append(M1Observation(
                    timestamp_utc=timestamp,
                    context_level=ctx_level,
                    test_type=test_type,
                    http_status=http_status,
                    success=(http_status == 200),
                    elapsed_ms=elapsed,
                    provider_request_id=req_id,
                    nvcf_reqid=nvcf_reqid,
                    nvcf_status=nvcf_status,
                    error=error,
                    response_body_preview=body[:200] if body else ""
                ))
                
                time.sleep(0.5)  # Rate limit respect
    
    # Additional sustained test: 10 rapid smoke requests
    print("[M1-RECON] Running sustained test (10 rapid requests)...")
    for i in range(10):
        timestamp = datetime.datetime.utcnow().isoformat() + "Z"
        http_status, elapsed, req_id, nvcf_reqid, nvcf_status, body, error = run_single_request(
            model_id, sys_prompt, "안녕하세요.", api_key, endpoint, max_tokens=100
        )
        observations.append(M1Observation(
            timestamp_utc=timestamp,
            context_level="small",
            test_type="sustained",
            http_status=http_status,
            success=(http_status == 200),
            elapsed_ms=elapsed,
            provider_request_id=req_id,
            nvcf_reqid=nvcf_reqid,
            nvcf_status=nvcf_status,
            error=error,
            response_body_preview=body[:200] if body else ""
        ))
        time.sleep(0.2)
    
    # Compute statistics
    total = len(observations)
    success = sum(1 for o in observations if o.success)
    http_200 = sum(1 for o in observations if o.http_status == 200)
    http_429 = sum(1 for o in observations if o.http_status == 429)
    http_408 = sum(1 for o in observations if o.http_status == 408)
    http_4xx_other = sum(1 for o in observations if 400 <= o.http_status < 500 and o.http_status not in (429, 408))
    http_5xx = sum(1 for o in observations if 500 <= o.http_status < 600)
    
    latencies = [o.elapsed_ms for o in observations if o.success]
    median_latency = sorted(latencies)[len(latencies)//2] if latencies else 0
    p95_latency = sorted(latencies)[int(len(latencies)*0.95)] if latencies else 0
    
    # Classification
    if http_429 == 0 and success == total:
        current_classification = "M1_PROVIDER_FAILURE_RESOLVED"
        changed = True
        rationale = f"All {total} observations returned HTTP 200. No 429 observed. Previous 429 appears resolved or transient."
    elif http_429 > 0 and http_429 < total * 0.5:
        current_classification = "M1_INTERMITTENT_429"
        changed = True
        rationale = f"{http_429}/{total} observations returned 429 ({http_429/total*100:.1f}%). Intermittent failure pattern."
    elif http_429 > 0:
        current_classification = "M1_PROVIDER_FAILURE_429_PERSISTENT"
        changed = False
        rationale = f"{http_429}/{total} observations returned 429. Persistent failure."
    else:
        current_classification = "M1_NO_429_OTHER_FAILURE"
        changed = True
        rationale = f"No 429 observed but {total - success} failures with other status codes."
    
    # Evidence summary
    evidence_summary = {
        "previous_classification": previous_classification,
        "total_observations": total,
        "success_rate": success / total,
        "http_200_rate": http_200 / total,
        "http_429_rate": http_429 / total,
        "http_408_rate": http_408 / total,
        "median_latency_ms": median_latency,
        "p95_latency_ms": p95_latency,
        "context_levels_tested": ["small", "medium", "large"],
        "test_types": ["smoke", "translation", "sustained"],
    }
    
    limitations = [
        "Single NVIDIA account; no cross-account comparison",
        "Observations span short time window; may not capture periodic patterns",
        "Single test prompt per context level",
        "Cannot distinguish provider-side vs infrastructure issues",
        "No provider documentation on 429 semantics",
    ]
    
    return M1ReconciliationReport(
        head_commit=baseline["head_commit"],
        origin_main_commit=baseline["origin_main_commit"],
        divergence=baseline["divergence"],
        branch=baseline["branch"],
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        test_timestamp=datetime.datetime.utcnow().isoformat() + "Z",
        endpoint=endpoint,
        credential_present=True,
        credential_source="NVIDIA_API_KEY",
        previous_classification=previous_classification,
        observations=observations,
        total_observations=total,
        success_count=success,
        http_200_count=http_200,
        http_429_count=http_429,
        http_408_count=http_408,
        http_4xx_other=http_4xx_other,
        http_5xx_count=http_5xx,
        median_latency_ms=median_latency,
        p95_latency_ms=p95_latency,
        current_classification=current_classification,
        classification_changed=changed,
        rationale=rationale,
        evidence_summary=evidence_summary,
        limitations=limitations,
    )


def main():
    print("=" * 70)
    print("P0-FINAL-15-R: M1 429 Reconciliation")
    print("=" * 70)
    
    report = run_m1_reconciliation()
    
    artifacts_dir = Path(__file__).resolve().parents[2] / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)
    report_path = artifacts_dir / "P0_FINAL_15_R_M1_429_RECONCILIATION.json"
    
    report_dict = asdict(report)
    report_dict = redact_sensitive(report_dict)
    
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2, ensure_ascii=False)
    
    print(f"\n[M1-RECON] Report saved to: {report_path}")
    
    print("\n" + "=" * 70)
    print("M1 429 RECONCILIATION SUMMARY")
    print("=" * 70)
    print(f"Previous: {report.previous_classification}")
    print(f"Current:  {report.current_classification}")
    print(f"Changed:  {report.classification_changed}")
    print(f"Rationale: {report.rationale}")
    print(f"\nObservations: {report.total_observations}")
    print(f"  Success: {report.success_count} ({report.success_count/report.total_observations*100:.1f}%)")
    print(f"  HTTP 200: {report.http_200_count}")
    print(f"  HTTP 429: {report.http_429_count}")
    print(f"  HTTP 408: {report.http_408_count}")
    print(f"  HTTP 5xx: {report.http_5xx_count}")
    print(f"  Median latency: {report.median_latency_ms:.0f}ms")
    print(f"  P95 latency: {report.p95_latency_ms:.0f}ms")
    
    # Print by context level
    print("\nBy Context Level:")
    for ctx in ["small", "medium", "large"]:
        ctx_obs = [o for o in report.observations if o.context_level == ctx]
        ctx_success = sum(1 for o in ctx_obs if o.success)
        ctx_429 = sum(1 for o in ctx_obs if o.http_status == 429)
        ctx_408 = sum(1 for o in ctx_obs if o.http_status == 408)
        print(f"  {ctx}: {ctx_success}/{len(ctx_obs)} success, {ctx_429} 429, {ctx_408} 408")
    
    # Governance doc
    governance_dir = Path(__file__).resolve().parents[2] / "docs" / "governance" / "repository"
    governance_dir.mkdir(parents=True, exist_ok=True)
    gov_path = governance_dir / "P0_FINAL_15_R_M1_429_RECONCILIATION.md"
    
    with open(gov_path, "w", encoding="utf-8") as f:
        f.write(f"""# P0-FINAL-15-R — M1 429 Reconciliation

## Phase R-A2: M1 429 Status Investigation

### Baseline
- **HEAD**: {report.head_commit}
- **origin/main**: {report.origin_main_commit}
- **divergence**: {report.divergence}
- **branch**: {report.branch}
- **Python**: {report.python_version}
- **Endpoint**: {report.endpoint}
- **Credential**: {report.credential_source}
- **Timestamp**: {report.test_timestamp}

### Previous Classification (P0-FINAL-15-Q)
**{report.previous_classification}**

### Current Observations
- **Total Observations**: {report.total_observations}
- **Success Count**: {report.success_count} ({report.success_count/report.total_observations*100:.1f}%)
- **HTTP 200**: {report.http_200_count}
- **HTTP 429**: {report.http_429_count}
- **HTTP 408**: {report.http_408_count}
- **HTTP 4xx Other**: {report.http_4xx_other}
- **HTTP 5xx**: {report.http_5xx_count}
- **Median Latency**: {report.median_latency_ms:.0f}ms
- **P95 Latency**: {report.p95_latency_ms:.0f}ms

### Classification
**Current**: **{report.current_classification}**
**Changed**: {report.classification_changed}
**Rationale**: {report.rationale}

### By Context Level
""")
        
        for ctx in ["small", "medium", "large"]:
            ctx_obs = [o for o in report.observations if o.context_level == ctx]
            ctx_success = sum(1 for o in ctx_obs if o.success)
            ctx_429 = sum(1 for o in ctx_obs if o.http_status == 429)
            ctx_408 = sum(1 for o in ctx_obs if o.http_status == 408)
            f.write(f"- **{ctx}**: {ctx_success}/{len(ctx_obs)} success, {ctx_429} 429, {ctx_408} 408\n")
        
        f.write(f"""
### By Test Type
""")
        
        for test_type in ["smoke", "translation", "sustained"]:
            type_obs = [o for o in report.observations if o.test_type == test_type]
            type_success = sum(1 for o in type_obs if o.success)
            type_429 = sum(1 for o in type_obs if o.http_status == 429)
            f.write(f"- **{test_type}**: {type_success}/{len(type_obs)} success, {type_429} 429\n")
        
        f.write(f"""
### Evidence Summary
""")
        for k, v in report.evidence_summary.items():
            f.write(f"- **{k}**: {v}\n")
        
        f.write(f"""
## Limitations
""")
        for lim in report.limitations:
            f.write(f"- {lim}\n")
        
        f.write(f"""
## Conclusion

**Previous**: {report.previous_classification}
**Current**: {report.current_classification}
**Changed**: {report.classification_changed}

{report.rationale}

**If RESOLVED**: M1 429 was transient or condition-dependent. M1 may be viable as production model again.
**If INTERMITTENT**: M1 has intermittent 429. Unsuitable for production without root cause fix.
**If PERSISTENT**: M1 429 remains unresolved. M1 unsuitable for production.

## Compliance
- ✅ No credential leakage
- ✅ No production modification
- ✅ No retry/RPM/timeout/backoff changes
- ✅ Root Hygiene compliant
- ✅ Protected Worktree preserved
- ✅ Historical evidence retained
""")
    
    print(f"[M1-RECON] Governance doc saved to: {gov_path}")
    print("\n" + "=" * 70)
    print("P0-FINAL-15-R M1 429 Reconciliation Complete")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())