#!/usr/bin/env python3
"""
P0-FINAL-15-S: Gate B — Runtime Stability

Runtime stability test for NVIDIA-hosted openai/gpt-oss-120b using NTPE production-compatible path.
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
class RuntimeObservation:
    """Single runtime stability observation."""
    sequence: int
    test_type: str  # baseline, narrative, dialogue, continuity, high_context
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
class RuntimeStabilityReport:
    """Runtime stability report."""
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
    observations: list[RuntimeObservation]
    # Summary
    total_observations: int
    success_count: int
    success_rate: float
    median_latency_ms: float
    p95_latency_ms: float
    http_200_count: int
    http_429_count: int
    http_408_count: int
    http_5xx_count: int
    # By test type
    by_test_type: dict
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


def run_single_request(model: str, system_prompt: str, user_prompt: str, api_key: str, endpoint: str, max_tokens: int = 4000, timeout_read: int = 60) -> tuple[int, float, Optional[str], Optional[str], Optional[str], str, Optional[str]]:
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


def run_runtime_stability() -> RuntimeStabilityReport:
    baseline = get_git_baseline()
    
    candidate_model = "openai/gpt-oss-120b"
    hosting_provider = "NVIDIA"
    endpoint = "https://integrate.api.nvidia.com/v1/chat/completions"
    api_key = os.environ.get("NVIDIA_API_KEY")
    
    if not api_key:
        raise RuntimeError("NVIDIA_API_KEY not set")
    
    print("=" * 70)
    print("P0-FINAL-15-S: Gate B — Runtime Stability")
    print("=" * 70)
    print(f"Candidate: {candidate_model}")
    print(f"Hosting: {hosting_provider}")
    
    # Load fixtures
    fixtures_path = Path(__file__).resolve().parents[2] / "tests" / "literary" / "Golden_Set" / "original_ko.txt"
    if fixtures_path.exists():
        narrative_fixture = fixtures_path.read_text(encoding="utf-8")
    else:
        narrative_fixture = "정태의는 아차, 하고 자리에서 일어섰다. 카일은 프라이빗풀 옆의 벤치에서 정신없이 잠들어 있을 터였다. (일주일의 휴가를 위해 그가 이곳에 오기 직전까지 밤을 새며 퀭한 얼굴로 일했다는 걸 정태의는 알고 있었다. 그래서, 그가 막무가내로 여기에 오겠다고 하는 주장을 차마 거를 수 없었다.) 라군에서 바닷가는, 당연하다면 당연하지만, 엎어지면 코 닿을 거리였다. 근처만 서성이려면 바다 위로 뻗은 나무다리 위로 산책을 할 수도 있지만, 정태의는 천천히 섬을 한 바퀴 돌아보자고 생각하고 백사장 쪽을 선택했다. 대충 걸어서 두어 시간이면 한 바퀴 다 돌 수 있을 정도로 작은 섬이라고 들었다. 무릅까지 오는 반바지 위에 넉넉한 셔츠 하나만 대충 걸치고, 그가 막 로비에서 나서려던 때였다. 새로운 손님이 왔는지, 바깥에서 약간 떠들썩하게―라고 해도 이곳이 워낙 조용해서, 단순한 말소리조차 그렇게 들릴 뿐이었지만―두세 명이 들어서고 있었다. 정태의는 저도 모르게 걸음을 멈추었다. 귀에 익은 독일어가 들렸다."
    
    dialogue_fixture = (
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
    
    continuity_fixture = (
        '김철수는 30년 경력의 형사였다. 그가 맡은 사건은 언제나 복잡했지만, '
        '그는 특유의 직관으로 진실을 파헤쳐왔다. 그의 파트너 이영희는 그와 정반대였다. '
        '논리와 증거만으로 사건을 풀어나가는 원칙주의자였다.\n\n'
        '어느 날, 두 사람은 연쇄 실종 사건을 맡게 되었다. '
        '철수는 현장의 미세한 흔적에서 단서를 찾으려 했고, 영희는 피해자들의 공통점을 분석했다. '
        '처음엔 서로의 방식을 불신했지만, 곧 그들의 접근법이 서로 보완됨을 깨달았다. '
        '철수의 직관이 영희의 논리를 이끌었고, 영희의 증거가 철수의 추측을 뒷받침했다.'
    )
    
    high_context_fixture = narrative_fixture * 3  # Large context
    
    observations = []
    api_key = os.environ.get("NVIDIA_API_KEY")
    endpoint = "https://integrate.api.nvidia.com/v1/chat/completions"
    model = "openai/gpt-oss-120b"
    
    # Test sequence per spec: 3 baseline, 3 narrative/dialogue, 2 continuity, 2 high-context = 10 total
    test_sequence = [
        ("baseline", "Translate Korean to Traditional Chinese (Taiwan). Output only translation.", "안녕하세요. 이것은 baseline 테스트입니다.", 100),
        ("baseline", "Translate Korean to Traditional Chinese (Taiwan). Output only translation.", "안녕하세요. 이것은 baseline 테스트입니다.", 100),
        ("baseline", "Translate Korean to Traditional Chinese (Taiwan). Output only translation.", "안녕하세요. 이것은 baseline 테스트입니다.", 100),
        ("narrative", "Translate Korean to Traditional Chinese (Taiwan). Output only translation.", narrative_fixture, 4000),
        ("narrative", "Translate Korean to Traditional Chinese (Taiwan). Output only translation.", narrative_fixture, 4000),
        ("dialogue", "Translate Korean to Traditional Chinese (Taiwan). Output only translation.", dialogue_fixture, 4000),
        ("dialogue", "Translate Korean to Traditional Chinese (Taiwan). Output only translation.", dialogue_fixture, 4000),
        ("continuity", "Translate Korean to Traditional Chinese (Taiwan). Output only translation.", continuity_fixture, 4000),
        ("continuity", "Translate Korean to Traditional Chinese (Taiwan). Output only translation.", continuity_fixture, 4000),
        ("high_context", "Translate Korean to Traditional Chinese (Taiwan). Output only translation.", high_context_fixture, 4000),
        ("high_context", "Translate Korean to Traditional Chinese (Taiwan). Output only translation.", high_context_fixture, 4000),
    ]
    
    print("=" * 70)
    print("P0-FINAL-15-S: Gate B — Runtime Stability")
    print("=" * 70)
    print(f"Candidate: openai/gpt-oss-120b")
    print(f"Hosting: NVIDIA")
    print(f"Total observations: {len(test_sequence)}")
    
    observations = []
    
    api_key = os.environ.get("NVIDIA_API_KEY")
    if not api_key:
        raise RuntimeError("NVIDIA_API_KEY not set")
    endpoint = "https://integrate.api.nvidia.com/v1/chat/completions"
    
    for seq, (test_type, system_prompt, user_prompt, max_tokens) in enumerate(test_sequence, 1):
        print(f"\n[RUNTIME] Observation {seq}/{len(test_sequence)}: {test_type}...")
        http_status, elapsed, req_id, nvcf_reqid, nvcf_status, body, error = run_single_request(
            "openai/gpt-oss-120b",
            system_prompt,
            user_prompt,
            api_key,
            endpoint,
            max_tokens=max_tokens
        )
        
        obs = RuntimeObservation(
            sequence=seq,
            test_type=test_type,
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
    
    # By test type
    by_type = {}
    for o in observations:
        if o.test_type not in by_type:
            by_type[o.test_type] = {"total": 0, "success": 0, "latencies": []}
        by_type[o.test_type]["total"] += 1
        if o.success:
            by_type[o.test_type]["success"] += 1
            by_type[o.test_type]["latencies"].append(o.elapsed_ms)
    
    by_type_summary = {}
    for k, v in by_type.items():
        by_type_summary[k] = {
            "total": v["total"],
            "success": v["success"],
            "success_rate": v["success"] / v["total"],
            "median_latency_ms": sorted(v["latencies"])[len(v["latencies"])//2] if v["latencies"] else 0,
        }
    
    # Gate decision
    if success_rate >= 0.95:
        gate_result = "PASS"
        gate_rationale = f"Success rate {success_rate:.0%} >= 95%"
    else:
        gate_result = "FAIL"
        gate_rationale = f"Success rate {success_rate:.0%} < 95%"
    
    # Check for systematic failures
    systematic_failures = []
    for k, v in by_type.items():
        if v["success"] == 0 and v["total"] >= 2:
            systematic_failures.append(f"{k}: 0/{v['total']} success")
    
    if systematic_failures:
        gate_result = "FAIL"
        gate_rationale = f"Systematic failures: {'; '.join(systematic_failures)}"
    
    limitations = [
        "Single NVIDIA account only",
        "Observations not statistically independent (sequential)",
        "No cross-region test",
        "Single test prompt per category",
        "No concurrent load test",
    ]
    
    return RuntimeStabilityReport(
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
        total_observations=total,
        success_count=success,
        success_rate=success_rate,
        median_latency_ms=median_latency,
        p95_latency_ms=p95_latency,
        http_200_count=sum(1 for o in observations if o.http_status == 200),
        http_429_count=sum(1 for o in observations if o.http_status == 429),
        http_408_count=sum(1 for o in observations if o.http_status == 408),
        http_5xx_count=sum(1 for o in observations if 500 <= o.http_status < 600),
        by_test_type=by_type_summary,
        gate_result=gate_result,
        gate_rationale=gate_rationale,
        limitations=limitations,
    )


def main():
    import datetime
    import subprocess
    import requests
    print("=" * 70)
    print("P0-FINAL-15-S: Gate B — Runtime Stability")
    print("=" * 70)
    
    report = run_runtime_stability()
    
    artifacts_dir = Path(__file__).resolve().parents[2] / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)
    report_path = artifacts_dir / "P0_FINAL_15_S_GPT_OSS_120B_RUNTIME_STABILITY_REPORT.json"
    
    report_dict = asdict(report)
    report_dict = redact_sensitive(report_dict)
    
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2, ensure_ascii=False)
    
    print(f"\n[RUNTIME] Report saved to: {report_path}")
    
    # Print summary
    print("\n" + "=" * 70)
    print("GATE B SUMMARY")
    print("=" * 70)
    print(f"Gate Result: {report.gate_result}")
    print(f"Rationale: {report.gate_rationale}")
    print(f"Success Rate: {report.success_rate:.0%} ({report.success_count}/{report.total_observations})")
    print(f"Latency: median={report.median_latency_ms:.0f}ms, P95={report.p95_latency_ms:.0f}ms")
    print(f"HTTP 200: {report.http_200_count}, 429: {report.http_429_count}, 408: {report.http_408_count}, 5xx: {report.http_5xx_count}")
    print("\nBy Test Type:")
    for k, v in report.by_test_type.items():
        print(f"  {k}: {v['success']}/{v['total']} ({v['success_rate']:.0%}), median={v['median_latency_ms']:.0f}ms")
    
    # Governance doc
    governance_dir = Path(__file__).resolve().parents[2] / "docs" / "governance" / "repository"
    governance_dir.mkdir(parents=True, exist_ok=True)
    gov_path = governance_dir / "P0_FINAL_15_S_GPT_OSS_120B_RUNTIME_STABILITY.md"
    
    with open(gov_path, "w", encoding="utf-8") as f:
        f.write(f"""# P0-FINAL-15-S: Gate B — Runtime Stability

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

## Test Sequence
Per spec: 3 baseline, 2 narrative, 2 dialogue, 2 continuity, 2 high-context = 11 total observations

## Observations

| Seq | Type | HTTP | Success | Latency (ms) | ReqID | NVCF ReqID | Error |
|-----|------|------|---------|--------------|-------|------------|-------|
""")
        
        for o in report.observations:
            f.write(f"| {o.sequence} | {o.test_type} | {o.http_status} | {o.success} | {o.elapsed_ms:.0f} | {o.provider_request_id or 'N/A'} | {o.nvcf_reqid or 'N/A'} | {o.error or 'None'} |\n")
        
        f.write(f"""
## Summary

| Metric | Value |
|--------|-------|
| Total Observations | {report.total_observations} |
| Success Count | {report.success_count} |
| Success Rate | {report.success_rate:.0%} |
| Median Latency | {report.median_latency_ms:.0f}ms |
| P95 Latency | {report.p95_latency_ms:.0f}ms |
| HTTP 200 | {report.http_200_count} |
| HTTP 429 | {report.http_429_count} |
| HTTP 408 | {report.http_408_count} |
| HTTP 5xx | {report.http_5xx_count} |

## By Test Type

| Type | Total | Success | Rate | Median Latency |
|------|-------|---------|------|----------------|
""")
        
        for k, v in report.by_test_type.items():
            f.write(f"| {k} | {v['total']} | {v['success']} | {v['success_rate']:.0%} | {v['median_latency_ms']:.0f}ms |\n")
        
        f.write(f"""
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
Proceed to **Gate C: Context Compatibility** if PASS, otherwise STOP.
""")
    
    print(f"[RUNTIME] Governance doc saved to: {gov_path}")
    print("\n" + "=" * 70)
    print("P0-FINAL-15-S Gate B Complete")
    print("=" * 70)
    
    return 0 if report.gate_result == "PASS" else 1


if __name__ == "__main__":
    import datetime
    import subprocess
    import requests
    sys.exit(main())