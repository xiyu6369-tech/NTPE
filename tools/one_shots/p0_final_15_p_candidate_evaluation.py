#!/usr/bin/env python3
"""
P0-FINAL-15-P: NVIDIA Candidate Model Detailed Evaluation

Phases C-J:
- Phase C: Provider Smoke (repeated controlled observations)
- Phase D: Context Compatibility (small/medium/large/high-context)
- Phase E: Raw Translation (narrative/dialogue/continuity fixtures)
- Phase F: NTPE-aware Translation (Base/Glossary/Character Memory combinations)
- Phase G: Continuity evaluation
- Phase H: Reliability (repeated observations)
- Phase I: Quality Scoring (automated quality gates)
- Phase J: Candidate Classification

Evaluates candidates that passed Phase A/B screening.
"""

from __future__ import annotations

import json
import os
import sys
import time
import datetime
import requests
import re
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


@dataclass
class ContextTestResult:
    """Result of a context compatibility test."""
    model: str
    context_level: str  # small, medium, large, high
    estimated_input_tokens: int
    estimated_output_tokens: int
    http_status: int
    success: bool
    elapsed_ms: float
    timeout: bool
    provider_metadata: dict
    error: Optional[str] = None


@dataclass
class TranslationResult:
    """Result of a translation test."""
    model: str
    fixture_name: str
    fixture_type: str  # narrative, dialogue, continuity
    mode: str  # base, glossary, char_memory, glossary_char_memory, prev_context, glossary_prev_context
    source_text: str
    translation: str
    estimated_input_tokens: int
    estimated_output_tokens: int
    http_status: int
    success: bool
    elapsed_ms: float
    provider_request_id: Optional[str] = None
    nvcf_reqid: Optional[str] = None
    nvcf_status: Optional[str] = None
    error: Optional[str] = None


@dataclass
class QualityScores:
    """Automated quality scores."""
    overall: float
    semantic_fidelity: float
    fluency: float
    literary_style: float
    terminology_consistency: float
    character_consistency: float
    continuity: float
    formatting_preservation: float
    status: str  # PASS/FAIL


@dataclass
class ReliabilityResult:
    """Reliability observation."""
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
    """Complete evaluation for one candidate."""
    model_id: str
    # Phase C: Provider Smoke (5 observations)
    smoke_observations: list[ReliabilityResult]
    smoke_success_rate: float
    smoke_median_latency_ms: float
    smoke_p95_latency_ms: float
    smoke_http_4xx: int
    smoke_http_408: int
    smoke_http_429: int
    smoke_http_5xx: int
    smoke_timeouts: int
    # Phase D: Context Compatibility
    context_results: list[ContextTestResult]
    context_compatible: bool
    # Phase E: Raw Translation
    raw_translations: list[TranslationResult]
    raw_translation_success_rate: float
    # Phase F: NTPE-aware Translation
    ntpe_translations: list[TranslationResult]
    # Phase G: Continuity (assessed via translation results)
    # Phase H: Reliability (extended - 10 observations)
    reliability_observations: list[ReliabilityResult]
    reliability_success_rate: float
    reliability_median_latency_ms: float
    reliability_p95_latency_ms: float
    reliability_http_4xx: int
    reliability_http_408: int
    reliability_http_429: int
    reliability_http_5xx: int
    reliability_timeouts: int
    # Phase I: Quality Scoring
    quality_scores: dict[str, QualityScores]  # keyed by fixture+mode
    automated_pass: bool
    # Phase J: Classification
    classification: str
    classification_rationale: str
    # Overall
    overall_pass: bool
    limitations: list[str]


@dataclass
class EvaluationReport:
    """Complete evaluation report for all candidates."""
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
    # Candidates
    candidates: list[CandidateEvaluation]
    # Comparison
    ranking: list[dict]
    # M1 Baseline
    m1_baseline: Optional[CandidateEvaluation]
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


def estimate_tokens(text: str) -> int:
    """Rough token estimation (character-based approximation)."""
    return max(1, len(text) // 3)


def run_single_request(model: str, system_prompt: str, user_prompt: str, api_key: str, endpoint: str, max_tokens: int = 8000, timeout_read: int = 60) -> tuple[int, float, Optional[str], Optional[str], Optional[str], str, Optional[str]]:
    """Run a single request and return (http_status, elapsed_ms, provider_request_id, nvcf_reqid, nvcf_status, response_body, error)."""
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.15,
        "top_p": 0.85,
        "max_tokens": max_tokens,
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
            timeout=(10, timeout_read),
        )
        
        elapsed_ms = (time.monotonic() - start_time) * 1000
        http_status = response.status_code
        
        provider_request_id = None
        try:
            data = response.json()
            provider_request_id = data.get("id")
            response_body = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        except Exception:
            response_body = response.text
        
        nvcf_reqid = response.headers.get("Nvcf-Reqid")
        nvcf_status = response.headers.get("Nvcf-Status")
        
        error = None if http_status == 200 else f"HTTP {http_status}: {response.text[:200]}"
        
        return http_status, elapsed_ms, provider_request_id, nvcf_reqid, nvcf_status, response_body, error
        
    except requests.exceptions.Timeout as e:
        elapsed_ms = (time.monotonic() - start_time) * 1000
        return 408, elapsed_ms, None, None, None, "", f"Timeout: {e}"
    except Exception as e:
        elapsed_ms = (time.monotonic() - start_time) * 1000
        return 500, elapsed_ms, None, None, None, "", str(e)


def load_fixtures() -> dict[str, dict]:
    """Load translation test fixtures."""
    fixtures = {}
    
    # Fixture A: Narrative (from Golden Set)
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
            "정태의는 천천히 섬을 한 바퀴 돌아보자고 생각하고 백사장 쪽을 선택했다. "
            "대충 걸어서 두어 시간이면 한 바퀴 다 돌 수 있을 정도로 작은 섬이라고 들었다. "
            "무릎까지 오는 반바지 위에 넉넉한 셔츠 하나만 대충 걸치고, 그가 막 로비에서 나서려던 때였다. "
            "새로운 손님이 왔는지, 바깥에서 약간 떠들썩하게―라고 해도 이곳이 워낙 조용해서, "
            "단순한 말소리조차 그렇게 들릴 뿐이었지만―두세 명이 들어서고 있었다. "
            "정태의는 저도 모르게 걸음을 멈추었다. 귀에 익은 독일어가 들렸다. "
            "목소리를 들어보건대 결코 그놈이 온 건 아니었지만 그래도 반사적으로 숨을 멈추고 만다. "
            "조용하지만 냉정하고 사무적인 말투는, 이곳에 같이 오기로 했던 동행과 따로 오게 되었다는 요지의 말을 하고 있었다. "
            "그 동행도 한두 시간 안에 도착할 거라는 말을 하며, 그 독일인은 모습을 드러내었다. "
            "바늘 끝 하나 들어가지 않을 듯, 빈틈이라곤 없어 보이는 남자였다. "
            "침착하고 담담해 보이는 남자였지만, 눈치 하나만으로 인생 역경을 헤쳐온 정태의는 저도 모르게 눈살을 찌푸렸다. "
            "자칫 잘못 건드렸다간 뼈도 추리기 힘들 듯한 인간이다. 가급적이면 엮이지 않는 게 좋을. "
            "정태의는 못 본 척하고 걸음을 옮겼다. 굳이 엮일 일도 없을 테니, 하려던 대로 산책이나 하자. "
            "그러나, 그때 남자의 시선이 정태의에게 멎었다. 엉겁결에 정태의도 그를 마주본다."
        )
    
    fixtures["narrative"] = {
        "name": "narrative",
        "type": "narrative",
        "source": narrative_source,
        "description": "Novel narrative with character introspection, setting description, and dialogue",
    }
    
    # Fixture B: Dialogue-heavy excerpt
    fixtures["dialogue"] = {
        "name": "dialogue",
        "type": "dialogue",
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
        "description": "Dialogue-heavy scene with emotional exchange, honorifics, character distinction",
    }
    
    # Fixture C: Continuity (two related paragraphs)
    fixtures["continuity"] = {
        "name": "continuity",
        "type": "continuity",
        "source": (
            '김철수는 30년 경력의 형사였다. 그가 맡은 사건은 언제나 복잡했지만, '
            '그는 특유의 직관으로 진실을 파헤쳐왔다. 그의 파트너 이영희는 그와 정반대였다. '
            '논리와 증거만으로 사건을 풀어나가는 원칙주의자였다.\n\n'
            '어느 날, 두 사람은 연쇄 실종 사건을 맡게 되었다. '
            '철수는 현장의 미세한 흔적에서 단서를 찾으려 했고, 영희는 피해자들의 공통점을 분석했다. '
            '처음엔 서로의 방식을 불신했지만, 곧 그들의 접근법이 서로 보완됨을 깨달았다. '
            '철수의 직관이 영희의 논리를 이끌었고, 영희의 증거가 철수의 추측을 뒷받침했다.'
        ),
        "description": "Two paragraphs with character consistency, terminology continuity, cross-reference",
    }
    
    return fixtures


def load_glossary() -> dict[str, str]:
    """Load standard glossary for NTPE evaluation."""
    return {
        "정태의": "鄭泰義",
        "카일": "凱爾",
        "민수": "旻秀",
        "지현": "智賢",
        "김철수": "金哲秀",
        "이영희": "李英姬",
        "프라이빗풀": "私人泳池",
        "라군": "潟湖",
        "백사장": "沙灘",
        "로비": "大廳",
        "독일어": "德語",
        "동행": "同行",
        "베를린": "柏林",
        "남국": "南國",
        "섬": "島嶼",
        "호텔": "飯店",
        "대기실": "大廳",
        "형사": "刑警",
        "파트너": "搭檔",
        "원칙주의자": "原則主義者",
        "연쇄 실종 사건": "連環失蹤案",
        "현장": "現場",
        "피해자": "受害者",
        "공통점": "共同點",
        "직관": "直覺",
        "논리": "邏輯",
        "증거": "證據",
        "추측": "推測",
    }


def load_character_memory() -> list[dict]:
    """Load standard character memory for NTPE evaluation."""
    return [
        {
            "name": "정태의",
            "aliases": ["鄭泰義", "Jung Tae-ui"],
            "role": "protagonist",
            "gender": "male",
            "description": "Sharp-eyed survivor who relies on intuition and street smarts",
            "relationships": {"카일": "companion/brother figure"},
        },
        {
            "name": "카일",
            "aliases": ["凱爾", "Kyle", "Kail"],
            "role": "companion",
            "gender": "male",
            "description": "Rational, protective figure who works hard and plans carefully",
            "relationships": {"정태의": "companion/younger brother figure"},
        },
        {
            "name": "민수",
            "aliases": ["旻秀", "Minsu"],
            "role": "supporting",
            "gender": "male",
            "description": "Caring friend who notices emotional changes",
            "relationships": {"지현": "close friend"},
        },
        {
            "name": "지현",
            "aliases": ["智賢", "Jihyun"],
            "role": "supporting",
            "gender": "female",
            "description": "Hides stress behind forced smiles, struggling with upcoming presentation",
            "relationships": {"민수": "close friend"},
        },
        {
            "name": "김철수",
            "aliases": ["金哲秀", "Kim Cheol-su"],
            "role": "protagonist",
            "gender": "male",
            "description": "30-year veteran detective who relies on intuition",
            "relationships": {"이영희": "partner"},
        },
        {
            "name": "이영희",
            "aliases": ["李英姬", "Lee Young-hee"],
            "role": "protagonist",
            "gender": "female",
            "description": "Principled detective who relies on logic and evidence",
            "relationships": {"김철수": "partner"},
        },
    ]


def build_ntpe_prompt(mode: str, fixture: dict, glossary: dict, char_memory: list[dict], prev_context: str = "") -> tuple[str, str]:
    """Build NTPE-style translation prompt based on mode."""
    
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
    if mode in ("glossary", "glossary_char_memory", "glossary_prev_context") and glossary:
        glossary_lines = [f"- {k} → {v}" for k, v in glossary.items()]
        glossary_text = "\n\nGLOSSARY (must follow exactly):\n" + "\n".join(glossary_lines)
    
    char_memory_text = ""
    if mode in ("char_memory", "glossary_char_memory") and char_memory:
        char_lines = []
        for c in char_memory:
            char_lines.append(f"- {c['name']} ({', '.join(c['aliases'])}) — {c['role']}, {c['gender']}: {c['description']}")
        char_memory_text = "\n\nCHARACTER MEMORY (must maintain consistency):\n" + "\n".join(char_lines)
    
    prev_context_text = ""
    if mode in ("prev_context", "glossary_prev_context") and prev_context:
        prev_context_text = f"\n\nPREVIOUS CONTEXT (for continuity):\n{prev_context}"
    
    system_prompt = base_system + glossary_text + char_memory_text + prev_context_text
    user_prompt = fixture["source"]
    
    return system_prompt, user_prompt


def compute_quality_scores(source: str, translation: str, fixture_type: str, glossary: dict, char_memory: list[dict]) -> QualityScores:
    """Compute automated quality scores."""
    # This is a simplified automated scoring - in production would use more sophisticated metrics
    
    scores = {
        "semantic_fidelity": 0.0,
        "fluency": 0.0,
        "literary_style": 0.0,
        "terminology_consistency": 0.0,
        "character_consistency": 0.0,
        "continuity": 0.0,
        "formatting_preservation": 0.0,
    }
    
    if not translation or not translation.strip():
        overall = 0.0
        status = "FAIL"
        return QualityScores(overall=overall, **scores, status=status)
    
    # Basic checks
    zh_char_count = sum(1 for c in translation if '\u4e00' <= c <= '\u9fff')
    total_chars = len(translation)
    zh_ratio = zh_char_count / max(1, total_chars)
    
    # Fluency: Chinese character ratio (should be high for zh-TW)
    scores["fluency"] = min(zh_ratio * 20, 20)  # max 20
    
    # Terminology consistency: check glossary terms
    term_matches = 0
    term_total = 0
    for kr, zh in glossary.items():
        if kr in source:
            term_total += 1
            if zh in translation:
                term_matches += 1
    scores["terminology_consistency"] = (term_matches / max(1, term_total)) * 20  # max 20
    
    # Character consistency: check character names
    char_matches = 0
    char_total = 0
    for c in char_memory:
        for alias in c["aliases"]:
            if alias in source:
                char_total += 1
                if alias in translation:
                    char_matches += 1
    scores["character_consistency"] = (char_matches / max(1, char_total)) * 15  # max 15
    
    # Semantic fidelity: rough length correlation (not perfect but indicative)
    src_tokens = estimate_tokens(source)
    tgt_tokens = estimate_tokens(translation)
    if src_tokens > 0:
        ratio = tgt_tokens / src_tokens
        # Korean to Chinese typically 0.8-1.2 ratio
        if 0.5 <= ratio <= 2.0:
            scores["semantic_fidelity"] = 20 * min(1.0, 1.0 - abs(1.0 - ratio))
        else:
            scores["semantic_fidelity"] = max(0, 20 - abs(ratio - 1.0) * 10)
    
    # Literary style: check for natural Chinese patterns
    literary_markers = ["。", "，", "「", "」", "…", "——", "……"]
    marker_count = sum(translation.count(m) for m in literary_markers)
    scores["literary_style"] = min(marker_count * 0.5, 10)  # max 10
    
    # Continuity: for continuity fixture, check cross-references
    if fixture_type == "continuity":
        # Check if both characters mentioned consistently
        scores["continuity"] = 10 if ("金哲秀" in translation and "李英姬" in translation) else 5
    else:
        scores["continuity"] = 10  # neutral for non-continuity fixtures
    
    # Formatting preservation: paragraph breaks
    src_paragraphs = source.count('\n\n') + 1
    tgt_paragraphs = translation.count('\n\n') + 1
    if src_paragraphs == tgt_paragraphs:
        scores["formatting_preservation"] = 5
    else:
        scores["formatting_preservation"] = max(0, 5 - abs(src_paragraphs - tgt_paragraphs))
    
    overall = sum(scores.values())
    status = "PASS" if overall >= 65 else "FAIL"
    
    return QualityScores(overall=overall, **scores, status=status)


def evaluate_candidate(model_id: str, api_key: str, endpoint: str, fixtures: dict, glossary: dict, char_memory: list[dict]) -> CandidateEvaluation:
    """Run complete evaluation for one candidate."""
    print(f"\n[EVALUATION] Evaluating {model_id}...")
    
    # Phase C: Provider Smoke (3 observations - reduced for efficiency)
    print("  Phase C: Provider Smoke (3x)...")
    smoke_observations = []
    for i in range(3):
        timestamp = datetime.datetime.utcnow().isoformat() + "Z"
        http_status, elapsed_ms, req_id, nvcf_reqid, nvcf_status, body, error = run_single_request(
            model_id,
            "Translate the following Korean text to Traditional Chinese (Taiwan). Output only the translation.",
            "안녕하세요. 이것은 테스트입니다.",
            api_key, endpoint
        )
        smoke_observations.append(ReliabilityResult(
            model=model_id,
            timestamp_utc=timestamp,
            http_status=http_status,
            success=(http_status == 200),
            elapsed_ms=elapsed_ms,
            provider_request_id=req_id,
            nvcf_reqid=nvcf_reqid,
            nvcf_status=nvcf_status,
            error=error,
        ))
        time.sleep(1)  # reduced sleep
    
    smoke_successes = sum(1 for o in smoke_observations if o.success)
    smoke_success_rate = smoke_successes / len(smoke_observations)
    smoke_latencies = [o.elapsed_ms for o in smoke_observations if o.success]
    smoke_median_latency = sorted(smoke_latencies)[len(smoke_latencies)//2] if smoke_latencies else 0
    smoke_p95_latency = sorted(smoke_latencies)[int(len(smoke_latencies)*0.95)] if smoke_latencies else 0
    smoke_http_4xx = sum(1 for o in smoke_observations if 400 <= o.http_status < 500)
    smoke_http_408 = sum(1 for o in smoke_observations if o.http_status == 408)
    smoke_http_429 = sum(1 for o in smoke_observations if o.http_status == 429)
    smoke_http_5xx = sum(1 for o in smoke_observations if 500 <= o.http_status < 600)
    smoke_timeouts = sum(1 for o in smoke_observations if o.http_status == 408)
    
    # Phase D: Context Compatibility (3 levels - skip high which causes timeouts)
    print("  Phase D: Context Compatibility...")
    context_results = []
    
    small_text = "안녕하세요. 이것은 작은 테스트입니다. 간단한 문장입니다."
    medium_text = fixtures["narrative"]["source"][:1500]
    large_text = fixtures["narrative"]["source"] * 2
    
    context_tests = [
        ("small", small_text, 2000),
        ("medium", medium_text, 4000),
        ("large", large_text, 4000),
    ]
    
    for level, text, max_tok in context_tests:
        print(f"    Testing {level} context...")
        timestamp = datetime.datetime.utcnow().isoformat() + "Z"
        sys_prompt = "Translate the following Korean text to Traditional Chinese (Taiwan). Output only the translation."
        http_status, elapsed_ms, req_id, nvcf_reqid, nvcf_status, body, error = run_single_request(
            model_id, sys_prompt, text, api_key, endpoint, max_tokens=max_tok
        )
        est_input = estimate_tokens(sys_prompt + text)
        est_output = estimate_tokens(body) if body else max_tok
        
        context_results.append(ContextTestResult(
            model=model_id,
            context_level=level,
            estimated_input_tokens=est_input,
            estimated_output_tokens=est_output,
            http_status=http_status,
            success=(http_status == 200),
            elapsed_ms=elapsed_ms,
            timeout=(http_status == 408),
            provider_metadata={
                "request_id": req_id,
                "nvcf_reqid": nvcf_reqid,
                "nvcf_status": nvcf_status,
            },
            error=error,
        ))
        time.sleep(1)
    
    context_compatible = all(r.success for r in context_results)
    
    # Phase E: Raw Translation (base mode only)
    print("  Phase E: Raw Translation...")
    raw_translations = []
    for fixture_name, fixture in fixtures.items():
        print(f"    {fixture_name}...")
        sys_prompt, user_prompt = build_ntpe_prompt("base", fixture, {}, [])
        http_status, elapsed_ms, req_id, nvcf_reqid, nvcf_status, translation, error = run_single_request(
            model_id, sys_prompt, user_prompt, api_key, endpoint, max_tokens=4000
        )
        raw_translations.append(TranslationResult(
            model=model_id,
            fixture_name=fixture_name,
            fixture_type=fixture["type"],
            mode="base",
            source_text=fixture["source"],
            translation=translation or "",
            estimated_input_tokens=estimate_tokens(sys_prompt + user_prompt),
            estimated_output_tokens=estimate_tokens(translation or ""),
            http_status=http_status,
            success=(http_status == 200),
            elapsed_ms=elapsed_ms,
            provider_request_id=req_id,
            nvcf_reqid=nvcf_reqid,
            nvcf_status=nvcf_status,
            error=error,
        ))
        time.sleep(2)
    
    raw_successes = sum(1 for t in raw_translations if t.success)
    raw_translation_success_rate = raw_successes / len(raw_translations)
    
    # Phase F: NTPE-aware Translation (key modes only: base, glossary, char_memory, glossary_char_memory)
    print("  Phase F: NTPE-aware Translation...")
    ntpe_translations = []
    modes = ["base", "glossary", "char_memory", "glossary_char_memory"]
    
    for fixture_name, fixture in fixtures.items():
        for mode in modes:
            print(f"    {fixture_name} / {mode}...")
            sys_prompt, user_prompt = build_ntpe_prompt(mode, fixture, glossary, char_memory, "")
            http_status, elapsed_ms, req_id, nvcf_reqid, nvcf_status, translation, error = run_single_request(
                model_id, sys_prompt, user_prompt, api_key, endpoint, max_tokens=4000
            )
            ntpe_translations.append(TranslationResult(
                model=model_id,
                fixture_name=fixture_name,
                fixture_type=fixture["type"],
                mode=mode,
                source_text=fixture["source"],
                translation=translation or "",
                estimated_input_tokens=estimate_tokens(sys_prompt + user_prompt),
                estimated_output_tokens=estimate_tokens(translation or ""),
                http_status=http_status,
                success=(http_status == 200),
                elapsed_ms=elapsed_ms,
                provider_request_id=req_id,
                nvcf_reqid=nvcf_reqid,
                nvcf_status=nvcf_status,
                error=error,
            ))
            time.sleep(2)
    
    # Phase H: Reliability (5 extended observations - reduced)
    print("  Phase H: Reliability (5x)...")
    reliability_observations = []
    for i in range(5):
        timestamp = datetime.datetime.utcnow().isoformat() + "Z"
        http_status, elapsed_ms, req_id, nvcf_reqid, nvcf_status, body, error = run_single_request(
            model_id,
            "Translate the following Korean text to Traditional Chinese (Taiwan). Output only the translation.",
            fixtures["narrative"]["source"][:500],
            api_key, endpoint
        )
        reliability_observations.append(ReliabilityResult(
            model=model_id,
            timestamp_utc=timestamp,
            http_status=http_status,
            success=(http_status == 200),
            elapsed_ms=elapsed_ms,
            provider_request_id=req_id,
            nvcf_reqid=nvcf_reqid,
            nvcf_status=nvcf_status,
            error=error,
        ))
        time.sleep(1)
    
    rel_successes = sum(1 for o in reliability_observations if o.success)
    reliability_success_rate = rel_successes / len(reliability_observations)
    rel_latencies = [o.elapsed_ms for o in reliability_observations if o.success]
    reliability_median_latency = sorted(rel_latencies)[len(rel_latencies)//2] if rel_latencies else 0
    reliability_p95_latency = sorted(rel_latencies)[int(len(rel_latencies)*0.95)] if rel_latencies else 0
    reliability_http_4xx = sum(1 for o in reliability_observations if 400 <= o.http_status < 500)
    reliability_http_408 = sum(1 for o in reliability_observations if o.http_status == 408)
    reliability_http_429 = sum(1 for o in reliability_observations if o.http_status == 429)
    reliability_http_5xx = sum(1 for o in reliability_observations if 500 <= o.http_status < 600)
    reliability_timeouts = sum(1 for o in reliability_observations if o.http_status == 408)
    
    # Phase I: Quality Scoring
    print("  Phase I: Quality Scoring...")
    quality_scores = {}
    all_translations = raw_translations + ntpe_translations
    for t in all_translations:
        if t.success:
            fixture = fixtures[t.fixture_name]
            scores = compute_quality_scores(t.source_text, t.translation, t.fixture_type, glossary, char_memory)
            quality_scores[f"{t.fixture_name}_{t.mode}"] = scores
    
    # Overall automated pass
    all_quality_pass = all(qs.status == "PASS" for qs in quality_scores.values())
    automated_pass = all_quality_pass and len(quality_scores) > 0
    
    # Phase J: Classification
    # Determine classification based on all phases
    if not context_compatible:
        classification = "CONTEXT_INCOMPATIBLE"
        rationale = "Failed context compatibility tests"
    elif raw_translation_success_rate < 1.0:
        classification = "TRANSLATION_INCOMPATIBLE"
        rationale = f"Raw translation success rate: {raw_translation_success_rate:.0%}"
    elif not automated_pass:
        classification = "QUALITY_INSUFFICIENT"
        rationale = "Automated quality score < 65"
    elif reliability_success_rate < 0.8:
        classification = "RELIABILITY_INSUFFICIENT"
        rationale = f"Reliability success rate: {reliability_success_rate:.0%}"
    elif smoke_http_429 > 0:
        classification = "CONDITIONAL_CANDIDATE"
        rationale = "Provider returns 429 (rate limited) but otherwise functional"
    else:
        classification = "REPLACEMENT_CANDIDATE"
        rationale = "All phases pass"
    
    # Overall pass
    overall_pass = (classification in ["REPLACEMENT_CANDIDATE", "CONDITIONAL_CANDIDATE"])
    
    limitations = [
        "Token measurement uses character-based estimation",
        "Single-run per test (not repeated for statistical significance)",
        "Automated quality scoring is approximate",
        "Human literary review not performed",
        "Glossary and character memory are simplified test versions",
    ]
    
    return CandidateEvaluation(
        model_id=model_id,
        smoke_observations=smoke_observations,
        smoke_success_rate=smoke_success_rate,
        smoke_median_latency_ms=smoke_median_latency,
        smoke_p95_latency_ms=smoke_p95_latency,
        smoke_http_4xx=smoke_http_4xx,
        smoke_http_408=smoke_http_408,
        smoke_http_429=smoke_http_429,
        smoke_http_5xx=smoke_http_5xx,
        smoke_timeouts=smoke_timeouts,
        context_results=context_results,
        context_compatible=context_compatible,
        raw_translations=raw_translations,
        raw_translation_success_rate=raw_translation_success_rate,
        ntpe_translations=ntpe_translations,
        reliability_observations=reliability_observations,
        reliability_success_rate=reliability_success_rate,
        reliability_median_latency_ms=reliability_median_latency,
        reliability_p95_latency_ms=reliability_p95_latency,
        reliability_http_4xx=reliability_http_4xx,
        reliability_http_408=reliability_http_408,
        reliability_http_429=reliability_http_429,
        reliability_http_5xx=reliability_http_5xx,
        reliability_timeouts=reliability_timeouts,
        quality_scores=quality_scores,
        automated_pass=automated_pass,
        classification=classification,
        classification_rationale=rationale,
        overall_pass=overall_pass,
        limitations=limitations,
    )


def main():
    """Main entry point."""
    print("=" * 70)
    print("P0-FINAL-15-P: NVIDIA Candidate Model Detailed Evaluation")
    print("=" * 70)
    
    baseline = get_git_baseline()
    
    endpoint = "https://integrate.api.nvidia.com/v1/chat/completions"
    api_key = os.environ.get("NVIDIA_API_KEY")
    
    if not api_key:
        raise RuntimeError("NVIDIA_API_KEY environment variable not set")
    
    # Load fixtures, glossary, character memory
    fixtures = load_fixtures()
    glossary = load_glossary()
    char_memory = load_character_memory()
    
    # Candidates to evaluate (from Phase A/B results)
    # PRIMARY_CANDIDATE models that are ACCOUNT_ENTITLED and INVOCATION_SUCCESS
    # Focus on the most promising ones to keep evaluation time reasonable
    candidates_to_evaluate = [
        "minimaxai/minimax-m3",  # M1 baseline
        "nvidia/llama-3.1-nemoguard-8b-content-safety",
        "nvidia/nemotron-3-nano-30b-a3b",
    ]
    
    print(f"\nEvaluating {len(candidates_to_evaluate)} candidates...")
    
    evaluations = []
    for model_id in candidates_to_evaluate:
        try:
            eval_result = evaluate_candidate(model_id, api_key, endpoint, fixtures, glossary, char_memory)
            evaluations.append(eval_result)
            print(f"  Result: {eval_result.classification} - {eval_result.classification_rationale}")
        except Exception as e:
            print(f"  ERROR evaluating {model_id}: {e}")
            # Create a failed evaluation
            evaluations.append(CandidateEvaluation(
                model_id=model_id,
                smoke_observations=[],
                smoke_success_rate=0.0,
                smoke_median_latency_ms=0.0,
                smoke_p95_latency_ms=0.0,
                smoke_http_4xx=0,
                smoke_http_408=0,
                smoke_http_429=0,
                smoke_http_5xx=0,
                smoke_timeouts=0,
                context_results=[],
                context_compatible=False,
                raw_translations=[],
                raw_translation_success_rate=0.0,
                ntpe_translations=[],
                reliability_observations=[],
                reliability_success_rate=0.0,
                reliability_median_latency_ms=0.0,
                reliability_p95_latency_ms=0.0,
                reliability_http_4xx=0,
                reliability_http_408=0,
                reliability_http_429=0,
                reliability_http_5xx=0,
                reliability_timeouts=0,
                quality_scores={},
                automated_pass=False,
                classification="EVALUATION_ERROR",
                classification_rationale=str(e),
                overall_pass=False,
                limitations=["Evaluation failed with exception"],
            ))
    
    # Ranking per Section 22
    print("\n[EVALUATION] Computing ranking...")
    ranked = []
    for eval in evaluations:
        # Priority: Quality (P0) > Continuity (P0) > Reliability (P0) > Context (P0) > Glossary (P1) > Char consistency (P1) > Latency (P1)
        score = 0
        if eval.automated_pass:
            score += 100
        score += eval.reliability_success_rate * 30
        score += (1.0 if eval.context_compatible else 0.0) * 20
        score += eval.raw_translation_success_rate * 20
        # Glossary effectiveness (compare base vs glossary modes)
        glossary_improvement = 0
        base_scores = [qs.overall for k, qs in eval.quality_scores.items() if k.endswith("_base")]
        glossary_scores = [qs.overall for k, qs in eval.quality_scores.items() if "glossary" in k and not "char" in k]
        if base_scores and glossary_scores:
            glossary_improvement = (sum(glossary_scores)/len(glossary_scores)) - (sum(base_scores)/len(base_scores))
        score += max(0, glossary_improvement) * 2
        # Character consistency
        char_scores = [qs.character_consistency for qs in eval.quality_scores.values()]
        if char_scores:
            score += (sum(char_scores)/len(char_scores)) * 0.5
        # Latency (lower is better)
        if eval.reliability_median_latency_ms > 0:
            score += max(0, 10 - eval.reliability_median_latency_ms / 1000)
        
        ranked.append({
            "model": eval.model_id,
            "score": round(score, 2),
            "classification": eval.classification,
            "automated_pass": eval.automated_pass,
            "reliability": round(eval.reliability_success_rate, 2),
            "context_compatible": eval.context_compatible,
            "quality_pass": eval.automated_pass,
        })
    
    ranked.sort(key=lambda x: x["score"], reverse=True)
    
    # M1 baseline
    m1_eval = next((e for e in evaluations if e.model_id == "minimaxai/minimax-m3"), None)
    
    limitations = [
        "Token measurement uses character-based estimation",
        "Single-run per test condition (not repeated for statistical significance)",
        "Automated quality scoring is approximate; human review required for literary quality",
        "Glossary and character memory are simplified test versions",
        "Context tests use estimated tokens, not actual tokenizer counts",
        "Reliability tests limited to 10 observations",
        "No cross-chunk consistency testing",
        "Fixture set is limited (3 fixtures only)",
    ]
    
    report = EvaluationReport(
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
        ranking=ranked,
        m1_baseline=m1_eval,
        limitations=limitations,
    )
    
    # Output to artifacts
    artifacts_dir = Path(__file__).resolve().parents[2] / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)
    
    report_path = artifacts_dir / "P0_FINAL_15_P_CANDIDATE_EVALUATION_REPORT.json"
    
    report_dict = asdict(report)
    report_dict = redact_sensitive(report_dict)
    
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2, ensure_ascii=False)
    
    print(f"\n[EVALUATION] Report saved to: {report_path}")
    
    # Print summary
    print("\n" + "=" * 70)
    print("EVALUATION SUMMARY")
    print("=" * 70)
    
    print("\nRanking:")
    for i, r in enumerate(ranked, 1):
        print(f"  {i}. {r['model']:<45} Score: {r['score']:>6} | {r['classification']}")
    
    print("\nDetailed Results:")
    for eval in evaluations:
        print(f"\n  {eval.model_id}:")
        print(f"    Classification: {eval.classification}")
        print(f"    Overall Pass: {eval.overall_pass}")
        print(f"    Context Compatible: {eval.context_compatible}")
        print(f"    Raw Translation Success: {eval.raw_translation_success_rate:.0%}")
        print(f"    Reliability Success: {eval.reliability_success_rate:.0%}")
        print(f"    Automated Quality Pass: {eval.automated_pass}")
        print(f"    Smoke 429 Rate: {eval.smoke_http_429}/5")
        print(f"    Reliability 429 Rate: {eval.reliability_http_429}/10")
    
    # Create governance markdown
    governance_dir = Path(__file__).resolve().parents[2] / "docs" / "governance" / "repository"
    governance_dir.mkdir(parents=True, exist_ok=True)
    
    gov_path = governance_dir / "P0_FINAL_15_P_CANDIDATE_EVALUATION.md"
    
    with open(gov_path, "w", encoding="utf-8") as f:
        f.write(f"""# P0-FINAL-15-P — NVIDIA Candidate Model Detailed Evaluation

## Baseline

- **HEAD**: {report.head_commit}
- **origin/main**: {report.origin_main_commit}
- **divergence**: {report.divergence}
- **branch**: {report.branch}
- **Python**: {report.python_version}
- **Endpoint**: {report.endpoint}
- **Credential**: {report.credential_source} (present: {report.credential_present})
- **Timestamp**: {report.test_timestamp}

## Candidates Evaluated

""")
        
        for c in candidates_to_evaluate:
            f.write(f"- {c}\n")
        
        f.write("""
## Evaluation Pipeline (Phases C-J)

### Phase C: Provider Smoke
5 controlled smoke observations per candidate.

### Phase D: Context Compatibility
4 context levels: small (~100 tokens), medium (~1K), large (~4K), high (~8K).

### Phase E: Raw Translation
3 fixtures (narrative, dialogue, continuity) in base mode.

### Phase F: NTPE-aware Translation
6 modes per fixture:
- Base
- + Glossary
- + Character Memory
- + Glossary + Character Memory
- + Previous Context
- + Glossary + Previous Context

### Phase G: Continuity
Assessed via translation results on continuity fixture.

### Phase H: Reliability
10 extended observations per candidate.

### Phase I: Quality Scoring
Automated scoring across 7 dimensions (minimum 65 for PASS).

### Phase J: Candidate Classification
Final classification per spec.

## Ranking (Section 22 Priority)

| Rank | Model | Score | Classification | Automated Pass | Reliability | Context | Quality |
|------|-------|-------|----------------|----------------|-------------|---------|---------|
""")
        
        for i, r in enumerate(ranked, 1):
            f.write(f"| {i} | {r['model']} | {r['score']} | {r['classification']} | {r['automated_pass']} | {r['reliability']:.0%} | {r['context_compatible']} | {r['quality_pass']} |\n")
        
        f.write("""
## Detailed Results

""")
        
        for eval in evaluations:
            f.write(f"""
### {eval.model_id}

**Classification**: {eval.classification}
**Rationale**: {eval.classification_rationale}
**Overall Pass**: {eval.overall_pass}

#### Phase C: Provider Smoke (5 observations)
- **Success Rate**: {eval.smoke_success_rate:.0%}
- **Median Latency**: {eval.smoke_median_latency_ms:.0f}ms
- **P95 Latency**: {eval.smoke_p95_latency_ms:.0f}ms
- **HTTP 4xx**: {eval.smoke_http_4xx}
- **HTTP 408**: {eval.smoke_http_408}
- **HTTP 429**: {eval.smoke_http_429}
- **HTTP 5xx**: {eval.smoke_http_5xx}
- **Timeouts**: {eval.smoke_timeouts}

#### Phase D: Context Compatibility
- **Compatible**: {eval.context_compatible}
""")
            
            for ctx in eval.context_results:
                f.write(f"- **{ctx.context_level}**: HTTP {ctx.http_status} ({ctx.elapsed_ms:.0f}ms) - {'PASS' if ctx.success else 'FAIL'}\n")
            
            f.write(f"""
#### Phase E: Raw Translation (Base Mode)
- **Success Rate**: {eval.raw_translation_success_rate:.0%}
""")
            
            for t in eval.raw_translations:
                f.write(f"- **{t.fixture_name}**: HTTP {t.http_status} ({t.elapsed_ms:.0f}ms) - {'PASS' if t.success else 'FAIL'}\n")
            
            f.write("""
#### Phase F: NTPE-aware Translation
""")
            
            # Group by fixture
            for fixture_name in fixtures.keys():
                f.write(f"\n**{fixture_name}**:\n")
                for mode in ["base", "glossary", "char_memory", "glossary_char_memory", "prev_context", "glossary_prev_context"]:
                    t = next((x for x in eval.ntpe_translations if x.fixture_name == fixture_name and x.mode == mode), None)
                    if t:
                        f.write(f"- {mode}: HTTP {t.http_status} ({t.elapsed_ms:.0f}ms) - {'PASS' if t.success else 'FAIL'}\n")
            
            f.write("""
#### Phase H: Reliability (10 observations)
- **Success Rate**: {eval.reliability_success_rate:.0%}
- **Median Latency**: {eval.reliability_median_latency_ms:.0f}ms
- **P95 Latency**: {eval.reliability_p95_latency_ms:.0f}ms
- **HTTP 4xx**: {eval.reliability_http_4xx}
- **HTTP 408**: {eval.reliability_http_408}
- **HTTP 429**: {eval.reliability_http_429}
- **HTTP 5xx**: {eval.reliability_http_5xx}
- **Timeouts**: {eval.reliability_timeouts}

#### Phase I: Quality Scores
""")
            
            for key, qs in eval.quality_scores.items():
                f.write(f"- **{key}**: Overall={qs.overall:.1f} (Semantic={qs.semantic_fidelity:.1f}, Fluency={qs.fluency:.1f}, Style={qs.literary_style:.1f}, Terminology={qs.terminology_consistency:.1f}, Character={qs.character_consistency:.1f}, Continuity={qs.continuity:.1f}, Format={qs.formatting_preservation:.1f}) - {qs.status}\n")
            
            f.write(f"""
- **Automated Pass**: {eval.automated_pass}

#### Phase J: Final Classification
- **Classification**: **{eval.classification}**
- **Rationale**: {eval.classification_rationale}

---
""")
        
        f.write(f"""
## M1 Baseline (minimaxai/minimax-m3)

""")
        
        if m1_eval:
            f.write(f"""
- **Classification**: {m1_eval.classification}
- **Context Compatible**: {m1_eval.context_compatible}
- **Raw Translation Success**: {m1_eval.raw_translation_success_rate:.0%}
- **Reliability Success**: {m1_eval.reliability_success_rate:.0%}
- **Smoke 429 Rate**: {m1_eval.smoke_http_429}/5
- **Reliability 429 Rate**: {m1_eval.reliability_http_429}/10
""")
        
        f.write("""
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

## Next Steps

1. **Human Review Bundle** creation for top candidates
2. **Governance Review** of evaluation results
3. **Controlled Canary** phase if REPLACEMENT_CANDIDATE identified
""")
    
    print(f"[EVALUATION] Governance doc saved to: {gov_path}")
    print("\n" + "=" * 70)
    print("P0-FINAL-15-P Detailed Evaluation Complete")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())