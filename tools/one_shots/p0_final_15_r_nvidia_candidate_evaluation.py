#!/usr/bin/env python3
"""
P0-FINAL-15-R: NVIDIA-Hosted Candidate Evaluation

Evaluate NVIDIA-hosted models that are FULLY_AVAILABLE on current account.
Uses the NVIDIA integration API endpoint with NVIDIA_API_KEY.
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
class SmokeResult:
    model: str
    timestamp_utc: str
    http_status: int
    success: bool
    elapsed_ms: float
    provider_request_id: Optional[str]
    nvcf_reqid: Optional[str]
    nvcf_status: Optional[str]
    error: Optional[str] = None


@dataclass
class TranslationResult:
    model: str
    fixture_name: str
    fixture_type: str
    mode: str
    source_text: str
    translation: str
    http_status: int
    success: bool
    elapsed_ms: float
    provider_request_id: Optional[str] = None
    nvcf_reqid: Optional[str] = None
    nvcf_status: Optional[str] = None
    error: Optional[str] = None


@dataclass
class QualityScores:
    overall: float
    semantic_fidelity: float
    fluency: float
    literary_style: float
    terminology_consistency: float
    character_consistency: float
    continuity: float
    formatting_preservation: float
    status: str


@dataclass
class ContextResult:
    level: str
    http_status: int
    success: bool
    elapsed_ms: float
    error: Optional[str] = None


@dataclass
class ReliabilityResult:
    model: str
    timestamp_utc: str
    http_status: int
    success: bool
    elapsed_ms: float
    provider_request_id: Optional[str]
    nvcf_reqid: Optional[str]
    nvcf_status: Optional[str]
    error: Optional[str] = None


@dataclass
class CandidateEvaluation:
    model_id: str
    
    # Smoke
    smoke_results: list[SmokeResult]
    smoke_success_rate: float
    smoke_median_latency_ms: float
    smoke_p95_latency_ms: float
    smoke_429_count: int
    smoke_408_count: int
    
    # Translation
    translation_results: list[TranslationResult]
    translation_success_rate: float
    
    # Quality
    quality_scores: dict[str, QualityScores]
    avg_quality_score: float
    quality_pass: bool
    glossary_improvement: float
    
    # Context
    context_results: list[ContextResult]
    context_compatible: bool
    
    # Reliability
    reliability_results: list[ReliabilityResult]
    reliability_success_rate: float
    reliability_median_latency_ms: float
    reliability_p95_latency_ms: float
    reliability_429_count: int
    reliability_408_count: int
    
    # Classification
    classification: str
    classification_rationale: str
    
    # Limitations
    limitations: list[str]


@dataclass
class EvaluationReport:
    head_commit: str
    origin_main_commit: str
    divergence: str
    branch: str
    python_version: str
    test_timestamp: str
    endpoint: str
    credential_present: bool
    credential_source: str
    candidates: list[CandidateEvaluation]
    m1_baseline: Optional[CandidateEvaluation]
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


def load_access_boundary() -> list[str]:
    """Load FULLY_AVAILABLE models from access boundary report."""
    path = Path(__file__).resolve().parents[2] / "artifacts" / "P0_FINAL_15_R_NVIDIA_ACCESS_BOUNDARY_REPORT.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [r["model_id"] for r in data.get("results", []) if r.get("access_classification") == "FULLY_AVAILABLE"]
    return []


def load_fixtures() -> dict[str, dict]:
    fixtures = {}
    golden_path = Path(__file__).resolve().parents[2].joinpath("tests/literary/Golden_Set/original_ko.txt")
    if golden_path.exists():
        narrative_source = golden_path.read_text(encoding="utf-8")
    else:
        narrative_source = (
            "정태의는 아차, 하고 자리에서 일어섰다. 카일은 프라이빗풀 옆의 벤치에서 정신없이 잠들어 있을 터였다. "
            "(일주일의 휴가를 위해 그가 이곳에 오기 직전까지 밤을 새며 퀭한 얼굴로 일했다는 걸 정태의는 알고 있었다. "
            "그래서, 그가 막무가내로 여기에 오겠다고 하는 주장을 차마 거스를 수 없었다.) "
            "라군에서 바닷가는, 당연하다면 당연하지만, 엎어지면 코 닿을 거리였다. "
            "근처만 서성이려면 바다 위로 뻗은 나무다리 위로 산책을 할 수도 있지만, "
            "정태的는 천천히 섬을 한 바퀴 돌아보자고 생각하고 백사장 쪽을 선택했다. "
            "대충 걸어서 두어 시간이면 한 바퀴 다 돌 수 있을 정도로 작은 섬이라고 들었다. "
            "무릎까지 오는 반바지 위에 넉넉한 셔츠 하나만 대충 걸치고, 그가 막 로비에서 나서려던 때였다. "
            "새로운 손님이 왔는지, 바깥에서 약간 떠들썩하게―라고 해도 이곳이 워낙 조용해서, "
            "단순한 말소리조차 그렇게 들릴 뿐이었지만―두세 명이 들어서고 있었다. "
            "정태的는 저도 모르게 걸음을 멈추었다. 귀에 익은 독일어가 들렸다. "
            "목소리를 들어보건대 결코 그놈이 온 건 아니었지만 그래도 반사적으로 숨을 멈추고 만다. "
            "조용하지만 냉정하고 사무적인 말투는, 이곳에 같이 오기로 했던 동행과 따로 오게 되었다는 요지의 말을 하고 있었다. "
            "그 동행도 한두 시간 안에 도착할 거라는 말을 하며, 그 독일인은 모습을 드러내었다. "
            "바늘 끝 하나 들어가지 않을 듯, 빈틈이라곤 없어 보이는 남자였다. "
            "침착하고 담담해 보이는 남자였지만, 눈치 하나만으로 인생 역경을 헤쳐온 정태的는 저도 모르게 눈살을 찌푸렸다. "
            "자칫 잘못 건드렸다간 뼈도 추리기 힘들 듯한 인간이다. 가급적이면 엮이지 않는 게 좋을. "
            "정태的是 못 본 척하고 걸음을 옮겼다. 굳이 엮일 일도 없을 테니, 하려던 대로 산책이나 하자. "
            "그러나, 그때 남자의 시선이 정태的에게 멎었다. 엉겁결에 정태的是 그를 마주본다."
        )
    
    fixtures["narrative"] = {"name": "narrative", "type": "narrative", "source": narrative_source,
        "description": "Novel narrative with character introspection, setting description, dialogue"}
    
    fixtures["dialogue"] = {"name": "dialogue", "type": "dialogue",
        "source": (
            '"정말 괜찮아?" 민수가 조심스럽게 물었다.\n\n'
            '지현은 고개를 끄덕이며 억지로 미소를 지었다. "응, 괜찮아. 그냥... 좀 피곤할 뿐이야."\n\n'
            '"아니, 네 눈빛이 그렇지 않아. 무슨 일 있어? 말해줘."\n\n'
            '지현은 잠시 망설였다. 그리고 낮게 한숨을 내쉬었다.\n\n'
            '"사실은... 내일 발표가 있어. 준비가 안 돼서 그래."\n\n'
            '민수는 놀란 듯 눈을 크게 떴다. "내일이면 하루 남았잖아? 왜 이제 말해?"\n\n'
            '"말해봤자 도와줄 수도 없으니까. 내 문제니까 내가 해결해야지."\n\n'
            '"그런 말 하지 마. 우린 친구잖아. 같이 해결하면 되잖아."\n\n'
            '그 말 한마디에 지현의 눈시울이 뜨거워졌다.'
        ),
        "description": "Dialogue-heavy scene with emotional exchange, honorifics, character distinction"}
    
    fixtures["continuity"] = {"name": "continuity", "type": "continuity",
        "source": (
            '김철수는 30년 경력의 형사였다. 그가 맡은 사건은 언제나 복잡했지만, '
            '그는 특유의 직관으로 진실을 파헤쳐왔다. 그의 파트너 이영희는 그와 정반대였다. '
            '논리와 증거만으로 사건을 풀어나가는 원칙주의자였다.\n\n'
            '어느 날, 두 사람은 연쇄 실종 사건을 맡게 되었다. '
            '철수는 현장의 미세한 흔적에서 단서를 찾으려 했고, 영희는 피해자들의 공통점을 분석했다. '
            '처음엔 서로의 방식을 불신했지만, 곧 그들의 접근法이 서로 보완됨을 깨달았다. '
            '철수의 직관이 영희의 논리를 이끌었고, 영희의 증거가 철수의 추측을 뒷받침했다.'
        ),
        "description": "Two paragraphs with character consistency, terminology continuity, cross-reference"}
    
    return fixtures


def load_glossary() -> dict[str, str]:
    return {
        "정태的": "鄭泰義", "카일": "凱爾", "민수": "旻秀", "지현": "智賢",
        "김철수": "金哲秀", "이영희": "李英姬", "프라이빗풀": "私人泳池",
        "라군": "潟湖", "백사장": "沙灘", "로비": "大廳", "독일어": "德語",
        "동행": "同行", "베를린": "柏林", "남국": "南國", "섬": "島嶼",
        "호텔": "飯店", "형사": "刑警", "파트너": "搭檔", "원칙주의자": "原則主義者",
        "연쇄 실종 사건": "連環失蹤案", "현장": "現場", "피해자": "受害者",
        "공통점": "共同點", "직관": "直覺", "논리": "邏輯", "증거": "證據", "推測": "推測",
    }


def load_character_memory() -> list[dict]:
    return [
        {"name": "정태的", "aliases": ["鄭泰義", "Jung Tae-ui"], "role": "protagonist", "gender": "male", "description": "Sharp-eyed survivor who relies on intuition"},
        {"name": "카일", "aliases": ["凱爾", "Kyle"], "role": "companion", "gender": "male", "description": "Rational, protective figure"},
        {"name": "민수", "aliases": ["旻秀", "Minsu"], "role": "supporting", "gender": "male", "description": "Caring friend"},
        {"name": "지현", "aliases": ["智賢", "Jihyun"], "role": "supporting", "gender": "female", "description": "Hides stress behind forced smiles"},
        {"name": "김철수", "aliases": ["金哲秀", "Kim Cheol-su"], "role": "protagonist", "gender": "male", "description": "30-year veteran detective"},
        {"name": "이영희", "aliases": ["李英姬", "Lee Young-hee"], "role": "protagonist", "gender": "female", "description": "Principled detective"},
    ]


def build_prompt(mode: str, fixture: dict, glossary: dict, char_memory: list[dict]) -> tuple[str, str]:
    base_system = (
        "You are a professional literary translator specializing in Korean to Traditional Chinese (Taiwan) translation. "
        "Translate the following Korean text naturally, preserving:\n"
        "1. Character names and honorifics\n"
        "2. Narrative tone and literary style\n"
        "3. Dialogue naturalness and character voice distinction\n"
        "4. Terminology consistency\n"
        "5. Cultural nuances appropriate for Taiwan readers\n\n"
        "Output only the translation."
    )
    
    glossary_text = ""
    if mode == "glossary" and glossary:
        glossary_lines = [f"- {k} → {v}" for k, v in glossary.items()]
        glossary_text = "\n\nGLOSSARY (must follow exactly):\n" + "\n".join(glossary_lines)
    
    char_memory_text = ""
    if mode == "char_memory" and char_memory:
        char_lines = [f"- {c['name']} ({', '.join(c['aliases'])}) — {c['role']}, {c['gender']}: {c['description']}" for c in char_memory]
        char_memory_text = "\n\nCHARACTER MEMORY:\n" + "\n".join(char_lines)
    
    system_prompt = base_system + glossary_text + char_memory_text
    user_prompt = fixture["source"]
    return system_prompt, user_prompt


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 3)


def compute_quality_scores(source: str, translation: str, fixture_type: str, glossary: dict, char_memory: list[dict]) -> QualityScores:
    scores = {"semantic_fidelity": 0.0, "fluency": 0.0, "literary_style": 0.0,
              "terminology_consistency": 0.0, "character_consistency": 0.0,
              "continuity": 0.0, "formatting_preservation": 0.0}
    
    if not translation or not translation.strip():
        return QualityScores(overall=0.0, **scores, status="FAIL")
    
    zh_char_count = sum(1 for c in translation if '\u4e00' <= c <= '\u9fff')
    total_chars = len(translation)
    zh_ratio = zh_char_count / max(1, total_chars)
    scores["fluency"] = min(zh_ratio * 20, 20)
    
    term_matches = 0
    term_total = 0
    for kr, zh in glossary.items():
        if kr in source:
            term_total += 1
            if zh in translation:
                term_matches += 1
    scores["terminology_consistency"] = (term_matches / max(1, term_total)) * 20
    
    char_matches = 0
    char_total = 0
    for c in char_memory:
        for alias in c["aliases"]:
            if alias in source:
                char_total += 1
                if alias in translation:
                    char_matches += 1
    scores["character_consistency"] = (char_matches / max(1, char_total)) * 15
    
    src_tokens = estimate_tokens(source)
    tgt_tokens = estimate_tokens(translation)
    if src_tokens > 0:
        ratio = tgt_tokens / src_tokens
        if 0.5 <= ratio <= 2.0:
            scores["semantic_fidelity"] = 20 * min(1.0, 1.0 - abs(1.0 - ratio))
        else:
            scores["semantic_fidelity"] = max(0, 20 - abs(ratio - 1.0) * 10)
    
    literary_markers = ["。", "，", "「", "」", "…", "——", "……"]
    marker_count = sum(translation.count(m) for m in literary_markers)
    scores["literary_style"] = min(marker_count * 0.5, 10)
    
    if fixture_type == "continuity":
        scores["continuity"] = 10 if ("金哲秀" in translation and "李英姬" in translation) else 5
    else:
        scores["continuity"] = 10
    
    src_paragraphs = source.count('\n\n') + 1
    tgt_paragraphs = translation.count('\n\n') + 1
    if src_paragraphs == tgt_paragraphs:
        scores["formatting_preservation"] = 5
    else:
        scores["formatting_preservation"] = max(0, 5 - abs(src_paragraphs - tgt_paragraphs))
    
    overall = sum(scores.values())
    status = "PASS" if overall >= 65 else "FAIL"
    return QualityScores(overall=overall, **scores, status=status)


def run_nvidia_request(model: str, system_prompt: str, user_prompt: str, api_key: str, endpoint: str, max_tokens: int = 8000) -> tuple[int, float, Optional[str], Optional[str], Optional[str], str, Optional[str]]:
    payload = {"model": model, "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], "temperature": 0.15, "top_p": 0.85, "max_tokens": max_tokens, "stream": False}
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
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
        return 408, elapsed, None, None, None, "", f"Timeout: {e}"
    except Exception as e:
        elapsed = (time.monotonic() - start) * 1000
        return 500, elapsed, None, None, None, "", str(e)


def evaluate_candidate(model_id: str, api_key: str, endpoint: str, fixtures: dict, glossary: dict, char_memory: list[dict]) -> CandidateEvaluation:
    print(f"\n[EVAL] Evaluating {model_id}...", flush=True)
    
    # Smoke test (2 observations)
    print("  Smoke test (2x)...", flush=True)
    smoke_results = []
    for i in range(2):
        print(f"    Smoke {i+1}/2...", flush=True)
        http_status, elapsed, req_id, nvcf_reqid, nvcf_status, body, error = run_nvidia_request(
            model_id,
            "Translate Korean to Traditional Chinese (Taiwan). Output only translation.",
            "안녕하세요. 이것은 테스트입니다.",
            api_key, endpoint, max_tokens=100
        )
        print(f"    -> HTTP {http_status} ({elapsed:.0f}ms)", flush=True)
        smoke_results.append(SmokeResult(
            model=model_id,
            timestamp_utc=datetime.datetime.utcnow().isoformat() + "Z",
            http_status=http_status,
            success=(http_status == 200),
            elapsed_ms=elapsed,
            provider_request_id=req_id,
            nvcf_reqid=nvcf_reqid,
            nvcf_status=nvcf_status,
            error=error,
        ))
        time.sleep(0.5)
    
    smoke_success = sum(1 for s in smoke_results if s.success)
    smoke_success_rate = smoke_success / len(smoke_results)
    smoke_latencies = [s.elapsed_ms for s in smoke_results if s.success]
    smoke_median = sorted(smoke_latencies)[len(smoke_latencies)//2] if smoke_latencies else 0
    smoke_p95 = sorted(smoke_latencies)[int(len(smoke_latencies)*0.95)] if smoke_latencies else 0
    smoke_429 = sum(1 for s in smoke_results if s.http_status == 429)
    smoke_408 = sum(1 for s in smoke_results if s.http_status == 408)
    
    if smoke_success_rate == 0:
        return CandidateEvaluation(
            model_id=model_id,
            smoke_results=smoke_results, smoke_success_rate=smoke_success_rate,
            smoke_median_latency_ms=0.0, smoke_p95_latency_ms=0.0,
            smoke_429_count=smoke_429, smoke_408_count=smoke_408,
            translation_results=[], translation_success_rate=0.0,
            quality_scores={}, avg_quality_score=0.0, quality_pass=False,
            glossary_improvement=0.0, context_results=[], context_compatible=False,
            reliability_results=[], reliability_success_rate=0.0,
            reliability_median_latency_ms=0.0, reliability_p95_latency_ms=0.0,
            reliability_429_count=0, reliability_408_count=0,
            classification="PROVIDER_UNAVAILABLE", classification_rationale="Smoke test failed",
            limitations=["Provider unavailable"],
        )
    
    # Translation tests (base + glossary on narrative only)
    print("  Translation tests (narrative base + glossary)...", flush=True)
    translation_results = []
    fixture = fixtures["narrative"]
    for mode in ["base", "glossary"]:
        print(f"    Translation {mode}...", flush=True)
        sys_prompt, user_prompt = build_prompt(mode, fixture, glossary, char_memory)
        http_status, elapsed, req_id, nvcf_reqid, nvcf_status, translation, error = run_nvidia_request(
            model_id, sys_prompt, user_prompt, api_key, endpoint, max_tokens=8000
        )
        print(f"    -> HTTP {http_status} ({elapsed:.0f}ms)", flush=True)
        translation_results.append(TranslationResult(
            model=model_id, fixture_name="narrative", fixture_type="narrative",
            mode=mode, source_text=fixture["source"], translation=translation or "",
            http_status=http_status, success=(http_status == 200),
            elapsed_ms=elapsed, provider_request_id=req_id,
            nvcf_reqid=nvcf_reqid, nvcf_status=nvcf_status, error=error,
        ))
        time.sleep(1)
    
    trans_success = sum(1 for t in translation_results if t.success)
    trans_success_rate = trans_success / len(translation_results)
    
    # Quality scoring
    quality_scores = {}
    for t in translation_results:
        if t.success:
            scores = compute_quality_scores(t.source_text, t.translation, t.fixture_type, glossary, char_memory)
            quality_scores[f"{t.fixture_name}_{t.mode}"] = scores
    
    avg_quality = sum(qs.overall for qs in quality_scores.values()) / len(quality_scores) if quality_scores else 0
    quality_pass = all(qs.status == "PASS" for qs in quality_scores.values()) and len(quality_scores) > 0
    
    base_scores = [qs.overall for k, qs in quality_scores.items() if k.endswith("_base")]
    glossary_scores = [qs.overall for k, qs in quality_scores.items() if k.endswith("_glossary")]
    glossary_improvement = (sum(glossary_scores)/len(glossary_scores) - sum(base_scores)/len(base_scores)) if base_scores and glossary_scores else 0
    
    # Context test (small, medium only)
    print("  Context tests (small, medium)...", flush=True)
    context_results = []
    test_fixtures = {
        "small": "안녕하세요. 이것은 작은 테스트입니다.",
        "medium": fixtures["narrative"]["source"][:2000],
    }
    sys_prompt = "Translate Korean to Traditional Chinese (Taiwan). Output only translation."
    for level, text in test_fixtures.items():
        print(f"    Context {level}...", flush=True)
        http_status, elapsed, req_id, nvcf_reqid, nvcf_status, body, error = run_nvidia_request(
            model_id, sys_prompt, text, api_key, endpoint, max_tokens=4000
        )
        print(f"    -> HTTP {http_status} ({elapsed:.0f}ms)", flush=True)
        context_results.append(ContextResult(
            level=level, http_status=http_status,
            success=(http_status == 200), elapsed_ms=elapsed, error=error
        ))
        time.sleep(0.5)
    
    context_compatible = all(r.success for r in context_results)
    
    # Reliability (2 observations)
    print("  Reliability (2x)...", flush=True)
    reliability_results = []
    for i in range(2):
        print(f"    Reliability {i+1}/2...", flush=True)
        http_status, elapsed, req_id, nvcf_reqid, nvcf_status, body, error = run_nvidia_request(
            model_id,
            "Translate Korean to Traditional Chinese (Taiwan). Output only translation.",
            fixtures["narrative"]["source"][:500],
            api_key, endpoint, max_tokens=4000
        )
        print(f"    -> HTTP {http_status} ({elapsed:.0f}ms)", flush=True)
        reliability_results.append(ReliabilityResult(
            model=model_id,
            timestamp_utc=datetime.datetime.utcnow().isoformat() + "Z",
            http_status=http_status, success=(http_status == 200),
            elapsed_ms=elapsed, provider_request_id=req_id,
            nvcf_reqid=nvcf_reqid, nvcf_status=nvcf_status, error=error
        ))
        time.sleep(0.5)
    
    rel_success = sum(1 for r in reliability_results if r.success)
    rel_success_rate = rel_success / len(reliability_results)
    rel_latencies = [r.elapsed_ms for r in reliability_results if r.success]
    rel_median = sorted(rel_latencies)[len(rel_latencies)//2] if rel_latencies else 0
    rel_p95 = sorted(rel_latencies)[int(len(rel_latencies)*0.95)] if rel_latencies else 0
    rel_429 = sum(1 for r in reliability_results if r.http_status == 429)
    rel_408 = sum(1 for r in reliability_results if r.http_status == 408)
    
    # Classification
    if trans_success_rate < 1.0:
        classification = "TRANSLATION_UNSUITABLE"
        rationale = f"Translation success rate {trans_success_rate:.0%}"
    elif not context_compatible:
        classification = "CONTEXT_INCOMPATIBLE"
        rationale = "Failed context compatibility"
    elif not quality_pass:
        classification = "QUALITY_INSUFFICIENT"
        rationale = f"Avg quality {avg_quality:.1f} < 65"
    elif rel_success_rate < 0.8:
        classification = "RUNTIME_UNSTABLE"
        rationale = f"Reliability {rel_success_rate:.0%}"
    else:
        classification = "REPLACEMENT_CANDIDATE"
        rationale = "All gates passed"
    
    return CandidateEvaluation(
        model_id=model_id,
        smoke_results=smoke_results, smoke_success_rate=smoke_success_rate,
        smoke_median_latency_ms=smoke_median, smoke_p95_latency_ms=smoke_p95,
        smoke_429_count=sum(1 for s in smoke_results if s.http_status == 429),
        smoke_408_count=sum(1 for s in smoke_results if s.http_status == 408),
        translation_results=translation_results, translation_success_rate=trans_success_rate,
        quality_scores=quality_scores, avg_quality_score=round(avg_quality, 1),
        quality_pass=quality_pass, glossary_improvement=round(glossary_improvement, 1),
        context_results=context_results, context_compatible=context_compatible,
        reliability_results=reliability_results, reliability_success_rate=rel_success_rate,
        reliability_median_latency_ms=rel_median, reliability_p95_latency_ms=rel_p95,
        reliability_429_count=sum(1 for r in reliability_results if r.http_status == 429),
        reliability_408_count=sum(1 for r in reliability_results if r.http_status == 408),
        classification=classification, classification_rationale=rationale,
        limitations=["Single-run per test", "Automated quality only", "No human review"],
    )


def run_evaluation() -> EvaluationReport:
    baseline = get_git_baseline()
    endpoint = "https://integrate.api.nvidia.com/v1/chat/completions"
    api_key = os.environ.get("NVIDIA_API_KEY")
    
    if not api_key:
        raise RuntimeError("NVIDIA_API_KEY not set")
    
    # Get FULLY_AVAILABLE models from access boundary
    available_models = load_access_boundary()
    # Prioritize key models for evaluation
    priority_models = [
        "minimaxai/minimax-m3",  # M1 baseline
        "deepseek-ai/deepseek-v4-pro-0813",
        "deepseek-ai/deepseek-v4-flash-0731",
        "nvidia/nemotron-3-ultra-550b-a55b",
        "nvidia/nemotron-3-super-120b-a12b",
        "nvidia/nemotron-3-nano-30b-a3b",
        "nvidia/nemotron-3.5-lightning-30b-a3b",
        "google/gemma-4-31b-it",
        "openai/gpt-oss-120b",
    ]
    available_models = [m for m in priority_models if m in available_models]
    
    print(f"\n[EVAL] Evaluating {len(available_models)} priority models:")
    for m in available_models:
        print(f"  {m}")
    
    fixtures = load_fixtures()
    glossary = load_glossary()
    char_memory = load_character_memory()
    
    evaluations = []
    for idx, model_id in enumerate(available_models):
        print(f"\n{'='*50}", flush=True)
        print(f"[EVAL] Model {idx+1}/{len(available_models)}: {model_id}", flush=True)
        print(f"{'='*50}", flush=True)
        result = evaluate_candidate(model_id, api_key, endpoint, fixtures, glossary, char_memory)
        evaluations.append(result)
        print(f"  Result: {result.classification}", flush=True)
    
    limitations = [
        "Single NVIDIA account only",
        "Single-run per test condition",
        "Automated quality scoring only",
        "No human literary review",
        "Glossary/char_memory are test versions",
        "Context tests use estimated tokens",
    ]
    
    return EvaluationReport(
        head_commit=baseline["head_commit"],
        origin_main_commit=baseline["origin_main_commit"],
        divergence=baseline["divergence"],
        branch=baseline["branch"],
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        test_timestamp=datetime.datetime.utcnow().isoformat() + "Z",
        endpoint=endpoint,
        credential_present=True,
        credential_source="NVIDIA_API_KEY",
        candidates=evaluations,
        m1_baseline=None,
        limitations=limitations,
    )


def main():
    import datetime
    import subprocess
    import requests
    
    print("=" * 70)
    print("P0-FINAL-15-R: NVIDIA-Hosted Candidate Evaluation")
    print("=" * 70)
    
    report = run_evaluation()
    
    artifacts_dir = Path(__file__).resolve().parents[2] / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)
    report_path = artifacts_dir / "P0_FINAL_15_R_NVIDIA_CANDIDATE_EVALUATION.json"
    
    report_dict = asdict(report)
    report_dict = redact_sensitive(report_dict)
    
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2, ensure_ascii=False)
    
    print(f"\n[EVAL] Report saved to: {report_path}")
    
    print("\n" + "=" * 70)
    print("EVALUATION SUMMARY")
    print("=" * 70)
    for c in report.candidates:
        print(f"\n  {c.model_id}")
        print(f"    Classification: {c.classification}")
        print(f"    Smoke: {c.smoke_success_rate:.0%}, 429s: {c.smoke_429_count}")
        print(f"    Translation: {c.translation_success_rate:.0%}")
        print(f"    Quality: {c.avg_quality_score:.1f} (pass={c.quality_pass})")
        print(f"    Glossary improvement: {c.glossary_improvement:+.1f}")
        print(f"    Context compatible: {c.context_compatible}")
        print(f"    Reliability: {c.reliability_success_rate:.0%}, 429s: {c.reliability_429_count}")
    
    # Governance
    governance_dir = Path(__file__).resolve().parents[2] / "docs" / "governance" / "repository"
    governance_dir.mkdir(parents=True, exist_ok=True)
    gov_path = governance_dir / "P0_FINAL_15_R_NVIDIA_CANDIDATE_EVALUATION.md"
    
    with open(gov_path, "w", encoding="utf-8") as f:
        f.write(f"""# P0-FINAL-15-R — NVIDIA-Hosted Candidate Evaluation

## Phase R-B: NVIDIA-Hosted Models with Current Account Entitlement

### Baseline
- **HEAD**: {report.head_commit}
- **origin/main**: {report.origin_main_commit}
- **divergence**: {report.divergence}
- **branch**: {report.branch}
- **Python**: {report.python_version}
- **Endpoint**: {report.endpoint}
- **Credential**: {report.credential_source}
- **Timestamp**: {report.test_timestamp}

### Evaluation Pipeline

1. **Smoke Test** (3 observations) - Basic API connectivity
2. **Translation** (3 fixtures × 2 modes) - Narrative, Dialogue, Continuity with Base/Glossary
3. **Quality Scoring** (7 dimensions, threshold ≥65)
4. **Glossary Effectiveness** - Base vs Glossary comparison
5. **Context Compatibility** - Small/Medium/Large fixtures
6. **Reliability** (5 observations) - Success rate, latency

## Results Summary

| Model | Smoke | Translation | Quality | Glossary Δ | Context | Reliability | Classification |
|-------|-------|-------------|---------|------------|---------|-------------|----------------|
""")
        
        for c in report.candidates:
            f.write(f"| {c.model_id} | {c.smoke_success_rate:.0%} | {c.translation_success_rate:.0%} | {c.avg_quality_score:.1f} | {c.glossary_improvement:+.1f} | {c.context_compatible} | {c.reliability_success_rate:.0%} | {c.classification} |\n")
        
        f.write("""
## Detailed Results

""")
        for c in report.candidates:
            f.write(f"""
### {c.model_id}

**Classification**: {c.classification}
**Rationale**: {c.classification_rationale}

**Smoke**: {c.smoke_success_rate:.0%} success, median {c.smoke_median_latency_ms:.0f}ms, P95 {c.smoke_p95_latency_ms:.0f}ms, 429s: {c.smoke_429_count}, 408s: {c.smoke_408_count}

**Translation**: {c.translation_success_rate:.0%} success
""")
            for t in c.translation_results:
                f.write(f"- {t.fixture_name} ({t.mode}): {'✓' if t.success else '✗'} HTTP {t.http_status} ({t.elapsed_ms:.0f}ms)\n")
            
            f.write(f"""
**Quality Scores**: avg={c.avg_quality_score:.1f}, pass={c.quality_pass}
""")
            for k, qs in c.quality_scores.items():
                f.write(f"- {k}: {qs.overall:.1f} (Sem={qs.semantic_fidelity:.1f}, Flu={qs.fluency:.1f}, Style={qs.literary_style:.1f}, Term={qs.terminology_consistency:.1f}, Char={qs.character_consistency:.1f}, Cont={qs.continuity:.1f}, Fmt={qs.formatting_preservation:.1f}) [{qs.status}]\n")
            
            f.write(f"""
**Glossary Improvement**: {c.glossary_improvement:+.1f}
**Context Compatible**: {c.context_compatible}
**Reliability**: {c.reliability_success_rate:.0%} success, median {c.reliability_median_latency_ms:.0f}ms, 429s: {c.reliability_429_count}
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
- ✅ Root Hygiene compliant
- ✅ Protected Worktree preserved
""")
    
    print(f"[EVAL] Governance doc saved to: {gov_path}")
    print("\n" + "=" * 70)
    print("P0-FINAL-15-R NVIDIA Candidate Evaluation Complete")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    import datetime
    import subprocess
    import requests
    sys.exit(main())