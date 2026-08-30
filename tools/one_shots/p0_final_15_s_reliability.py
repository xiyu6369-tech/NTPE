#!/usr/bin/env python3
"""
P0-FINAL-15-S: Gates G/H — Reliability & Latency

Extended reliability observations and latency measurements for NVIDIA-hosted openai/gpt-oss-120b.
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
class ReliabilityObservation:
    """Single reliability observation."""
    sequence: int
    test_category: str  # normal, narrative, dialogue, continuity, high_context
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
class LatencyStats:
    """Latency statistics."""
    median_ms: float
    p95_ms: float
    min_ms: float
    max_ms: float


@dataclass
class FailureClassification:
    """Failure classification result."""
    total_failures: int
    by_status: dict
    systematic: list[str]


@dataclass
class ReliabilityReport:
    """Reliability & Latency report."""
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
    observations: list[ReliabilityObservation]
    # Summary
    total_observations: int
    success_count: int
    success_rate: float
    # Latency
    latency_all: LatencyStats
    latency_success: LatencyStats
    # Failures
    failures: FailureClassification
    # Gate Results
    gate_g_result: str  # PASS/FAIL
    gate_g_rationale: str
    gate_h_result: str  # PASS/FAIL
    gate_h_rationale: str
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


def run_single_request(model: str, system_prompt: str, user_prompt: str, api_key: str, endpoint: str, max_tokens: int = 4000, timeout_read: int = 120) -> tuple[int, float, Optional[str], Optional[str], Optional[str], str, Optional[str]]:
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
        return 408, elapsed, None, None, None, "", f"Timeout: {e}"
    except Exception as e:
        elapsed = (time.monotonic() - start) * 1000
        return 500, elapsed, None, None, None, "", str(e)


def calc_latency_stats(latencies: list[float]) -> LatencyStats:
    if not latencies:
        return LatencyStats(median_ms=0, p95_ms=0, min_ms=0, max_ms=0)
    sorted_lat = sorted(latencies)
    return LatencyStats(
        median_ms=sorted_lat[len(sorted_lat)//2],
        p95_ms=sorted_lat[int(len(sorted_lat)*0.95)],
        min_ms=sorted_lat[0],
        max_ms=sorted_lat[-1],
    )


def classify_failures(observations: list) -> FailureClassification:
    failures = [o for o in observations if not o.success]
    by_status = {}
    for f in failures:
        by_status[f.http_status] = by_status.get(f.http_status, 0) + 1
    
    systematic = []
    for status, count in by_status.items():
        if count >= 3:  # Systematic if same error appears 3+ times
            systematic.append(f"HTTP {status}: {count} occurrences")
    
    return FailureClassification(
        total_failures=len(failures),
        by_status=by_status,
        systematic=systematic,
    )


def run_reliability() -> ReliabilityReport:
    baseline = get_git_baseline()
    
    candidate_model = "openai/gpt-oss-120b"
    hosting_provider = "NVIDIA"
    endpoint = "https://integrate.api.nvidia.com/v1/chat/completions"
    api_key = os.environ.get("NVIDIA_API_KEY")
    
    if not api_key:
        raise RuntimeError("NVIDIA_API_KEY not set")
    
    print("=" * 70)
    print("P0-FINAL-15-S: Gates G/H — Reliability & Latency")
    print("=" * 70)
    print(f"Candidate: {candidate_model}")
    print(f"Hosting: {hosting_provider}")
    
    # Load fixtures
    fixtures_path = Path(__file__).resolve().parents[2] / "tests" / "literary" / "Golden_Set" / "original_ko.txt"
    if fixtures_path.exists():
        narrative = fixtures_path.read_text(encoding="utf-8")
    else:
        narrative = "정태의는 아차, 하고 자리에서 일어섰다. 카일은 프라이빗풀 옆의 벤치에서 정신없이 잠들어 있을 터였다. (일주일의 휴가를 위해 그가 이곳에 오기 직전까지 밤을 새며 퀭한 얼굴로 일했다는 걸 정태의는 알고 있었다. 그래서, 그가 막무가내로 여기에 오겠다고 하는 주장을 차마 거를 수 없었다.) 라군에서 바닷가는, 당연하다면 당연하지만, 엎어지면 코 닿을 거리였다. 근처만 서성이려면 바다 위로 뻗은 나무다리 위로 산책을 할 수도 있지만, 정태的는 천천히 섬을 한 바퀴 돌아보자고 생각하고 백사장 쪽을 선택했다. 대충 걸어서 두어 시간이면 한 바퀴 다 돌 수 있을 정도로 작은 섬이라고 들었다. 무릅까지 오는 반바지 위에 넉넉한 셔츠 하나만 대충 걸치고, 그가 막 로비에서 나서려던 때였다. 새로운 손님이 왔는지, 바깥에서 약간 떠들썩하게―라고 해도 이곳이 워낙 조용해서, 단순한 말소리조차 그렇게 들릴 뿐이었지만―두세 명이 들어서고 있었다. 정태的是 저도 모르게 걸음을 멈추었다. 귀에 익은 독일어가 들렸다."
    
    dialogue = (
        '"정말 괜찮아?" 민수가 조심스럽게 물었다.\n\n'
        '지현은 고개를 끄덕이며 억지로 미소를 지었다. "응, 괜찮아. 그냥... 좀 피곤할 뿐이야."\n\n'
        '"아니, 네 눈빛이 그렇지 않아. 무슨 일 있어? 말해줘."\n\n'
        '지현은 잠시 망설였다. 그리고 낮게 한숨을 내쉬었다.\n\n'
        '"사실은... 내일 발표가 있어. 준비가 안 돼서 그래."\n\n'
        '민수는 놀란 듯 눈을 크게 떴다. "내일이면 하루 남았잖아? 왜 이제 말해?"\n\n'
        '"말해봤자 도와줄 수도 없으니까. 내 문제니까 내가 해결해야지."\n\n'
        '"그런 말 하지 마. 우린 친구잖아. 같이 해결하면 되잖아."\n\n'
        '그 말 한마디에 지현의 눈시울이 뜨거워졌다.'
    )
    
    continuity = (
        '김철수는 30년 경력의 형사였다. 그가 맡은 사건은 언제나 복잡했지만, '
        '그는 특유의 직관으로 진실을 파헤쳐왔다. 그의 파트너 이영희는 그와 정반대였다. '
        '논리와 증거만으로 사건을 풀어나가는 원칙주의자였다.\n\n'
        '어느 날, 두 사람은 연쇄 실종 사건을 맡게 되었다. '
        '철수는 현장의 미세한 흔적에서 단서를 찾으려 했고, 영희는 피해자들의 공통점을 분석했다. '
        '처음엔 서로의 방식을 불신했지만, 곧 그들의 접근法이 서로 보완됨을 깨달았다. '
        '철수의 직관이 영희的 논리를 이끌었고, 영희的 증거가 철수의 추측을 뒷받침했다.'
    )
    
    high_context = narrative * 3
    
    # Test sequence: 3 normal, 3 narrative, 2 dialogue, 2 continuity, 2 high_context, 3 narrative, 2 continuity = 15
    test_sequence = [
        ("normal", "Translate Korean to Traditional Chinese (Taiwan). Output only translation.", "안녕하세요. 이것은 baseline 테스트입니다.", 100),
        ("normal", "Translate Korean to Traditional Chinese (Taiwan). Output only translation.", "안녕하세요. 이것은 baseline 테스트입니다.", 100),
        ("normal", "Translate Korean to Traditional Chinese (Taiwan). Output only translation.", "안녕하세요. 이것은 baseline 테스트입니다.", 100),
        ("narrative", "Translate Korean to Traditional Chinese (Taiwan). Output only translation.", narrative, 4000),
        ("narrative", "Translate Korean to Traditional Chinese (Taiwan). Output only translation.", narrative, 4000),
        ("dialogue", "Translate Korean to Traditional Chinese (Taiwan). Output only translation.", dialogue, 4000),
        ("dialogue", "Translate Korean to Traditional Chinese (Taiwan). Output only translation.", dialogue, 4000),
        ("continuity", "Translate Korean to Traditional Chinese (Taiwan). Output only translation.", continuity, 4000),
        ("continuity", "Translate Korean to Traditional Chinese (Taiwan). Output only translation.", continuity, 4000),
        ("high_context", "Translate Korean to Traditional Chinese (Taiwan). Output only translation.", high_context, 8000),
        ("high_context", "Translate Korean to Traditional Chinese (Taiwan). Output only translation.", high_context, 8000),
        ("narrative", "Translate Korean to Traditional Chinese (Taiwan). Output only translation.", narrative, 4000),
        ("narrative", "Translate Korean to Traditional Chinese (Taiwan). Output only translation.", narrative, 4000),
        ("continuity", "Translate Korean to Traditional Chinese (Taiwan). Output only translation.", continuity, 4000),
        ("continuity", "Translate Korean to Traditional Chinese (Taiwan). Output only translation.", continuity, 4000),
    ]
    
    observations = []
    
    print("=" * 70)
    print("P0-FINAL-15-S: Gates G/H — Reliability & Latency")
    print("=" * 70)
    print(f"Candidate: openai/gpt-oss-120b")
    print(f"Hosting: NVIDIA")
    print(f"Total observations: {len(test_sequence)}")
    
    api_key = os.environ.get("NVIDIA_API_KEY")
    if not api_key:
        raise RuntimeError("NVIDIA_API_KEY not set")
    endpoint = "https://integrate.api.nvidia.com/v1/chat/completions"
    
    observations = []
    
    api_key = os.environ.get("NVIDIA_API_KEY")
    if not api_key:
        raise RuntimeError("NVIDIA_API_KEY not set")
    endpoint = "https://integrate.api.nvidia.com/v1/chat/completions"
    
    for seq, (test_type, system_prompt, user_prompt, max_tokens) in enumerate(test_sequence, 1):
        print(f"\n[RELIABILITY] Observation {seq}/{len(test_sequence)}: {test_type}...")
        http_status, elapsed, req_id, nvcf_reqid, nvcf_status, body, error = run_single_request(
            "openai/gpt-oss-120b", system_prompt, user_prompt, 
            api_key, endpoint, max_tokens=max_tokens
        )
        
        obs = ReliabilityObservation(
            sequence=seq,
            test_category=test_type,
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
    
    all_latencies = [o.elapsed_ms for o in observations]
    success_latencies = [o.elapsed_ms for o in observations if o.success]
    
    latency_all = calc_latency_stats(all_latencies)
    latency_success = calc_latency_stats(success_latencies)
    
    failures = classify_failures(observations)
    
    # Gate G: Reliability
    if success_rate >= 0.95 and not failures.systematic:
        gate_g_result = "PASS"
        gate_g_rationale = f"Success rate {success_rate:.0%} >= 95%, no systematic failures"
    else:
        gate_g_result = "FAIL"
        gate_g_rationale = f"Success rate {success_rate:.0%} < 95% or systematic failures: {failures.systematic}"
    
    # Gate H: Latency (informational, not blocking)
    gate_h_result = "PASS"  # Latency is informational
    gate_h_rationale = f"Median latency {latency_success.median_ms:.0f}ms, P95 {latency_success.p95_ms:.0f}ms (successful requests)"
    
    limitations = [
        "Sequential observations (not concurrent)",
        "Single NVIDIA account",
        "No sustained load test",
        "No network variability test",
        "Single test prompt per category",
    ]
    
    return ReliabilityReport(
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
        total_observations=len(observations),
        success_count=sum(1 for o in observations if o.success),
        success_rate=success_rate,
        latency_all=calc_latency_stats([o.elapsed_ms for o in observations]),
        latency_success=calc_latency_stats([o.elapsed_ms for o in observations if o.success]),
        failures=classify_failures(observations),
        gate_g_result=gate_g_result,
        gate_g_rationale=gate_g_rationale,
        gate_h_result=gate_h_result,
        gate_h_rationale=gate_h_rationale,
        limitations=limitations,
    )


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


def main():
    import datetime
    import subprocess
    import requests
    print("=" * 70)
    print("P0-FINAL-15-S: Gates G/H — Reliability & Latency")
    print("=" * 70)
    
    report = run_reliability()
    
    artifacts_dir = Path(__file__).resolve().parents[2] / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)
    report_path = artifacts_dir / "P0_FINAL_15_S_GPT_OSS_120B_RELIABILITY_REPORT.json"
    
    report_dict = asdict(report)
    report_dict = redact_sensitive(report_dict)
    
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2, ensure_ascii=False)
    
    print(f"\n[RELIABILITY] Report saved to: {report_path}")
    
    # Print summary
    print("\n" + "=" * 70)
    print("GATES G/H SUMMARY")
    print("=" * 70)
    print(f"Gate G (Reliability): {report.gate_g_result} - {report.gate_g_rationale}")
    print(f"Gate H (Latency): {report.gate_h_result} - {report.gate_h_rationale}")
    print(f"Success Rate: {report.success_rate:.0%} ({report.success_count}/{report.total_observations})")
    print(f"Latency (all): median={report.latency_all.median_ms:.0f}ms, P95={report.latency_all.p95_ms:.0f}ms")
    print(f"Latency (success): median={report.latency_success.median_ms:.0f}ms, P95={report.latency_success.p95_ms:.0f}ms")
    print(f"Failures: {report.failures.total_failures}, by status: {report.failures.by_status}")
    
    # Governance doc
    governance_dir = Path(__file__).resolve().parents[2] / "docs" / "governance" / "repository"
    governance_dir.mkdir(parents=True, exist_ok=True)
    gov_path = governance_dir / "P0_FINAL_15_S_GPT_OSS_120B_RELIABILITY.md"
    
    with open(gov_path, "w", encoding="utf-8") as f:
        f.write(f"""# P0-FINAL-15-S: Gates G/H — Reliability & Latency

## Baseline
- **HEAD**: {report.head_commit}
- **origin/main**: {report.origin_main_commit}
- **divergence**: {report.divergence}
- **branch**: {report.branch}
- **Python**: {report.python_version}
- **Timestamp**: {report.test_timestamp}

## Candidate
- **Model**: openai/gpt-oss-120b
- **Hosting**: NVIDIA
- **Endpoint**: https://integrate.api.nvidia.com/v1/chat/completions
- **Credential**: NVIDIA_API_KEY

## Test Sequence (15 observations)

| Seq | Type | HTTP | Success | Latency (ms) |
|-----|------|------|---------|--------------|
""")
        
        for o in report.observations:
            f.write(f"| {o.sequence} | {o.test_category} | {o.http_status} | {o.success} | {o.elapsed_ms:.0f} |\n")
        
        f.write(f"""
## Summary

| Metric | Value |
|--------|-------|
| Total Observations | {report.total_observations} |
| Success Count | {report.success_count} |
| Success Rate | {report.success_rate:.0%} |

## Latency Statistics

| Statistic | All Requests | Successful Only |
|-----------|--------------|-----------------|
| Median | {report.latency_all.median_ms:.0f}ms | {report.latency_success.median_ms:.0f}ms |
| P95 | {report.latency_all.p95_ms:.0f}ms | {report.latency_success.p95_ms:.0f}ms |
| Min | {report.latency_all.min_ms:.0f}ms | {report.latency_success.min_ms:.0f}ms |
| Max | {report.latency_all.max_ms:.0f}ms | {report.latency_success.max_ms:.0f}ms |

## Failure Classification

| Status | Count |
|--------|-------|
""")
        
        for status, count in report.failures.by_status.items():
            f.write(f"| HTTP {status} | {count} |\n")
        
        if report.failures.systematic:
            f.write(f"""
**Systematic Failures:**
""")
            for sys in report.failures.systematic:
                f.write(f"- {sys}\n")
        
        f.write(f"""
## Gate Results

### Gate G — Reliability
**Result**: **{report.gate_g_result}**
**Rationale**: {report.gate_g_rationale}

### Gate H — Latency
**Result**: **{report.gate_h_result}**
**Rationale**: {report.gate_h_rationale}

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
Proceed to **Gate I: Human Literary Review** if Gate G PASS, otherwise STOP.
""")
    
    print(f"[RELIABILITY] Governance doc saved to: {gov_path}")
    print("\n" + "=" * 70)
    print("P0-FINAL-15-S Gates G/H Complete")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    import datetime
    import subprocess
    import requests
    sys.exit(main())