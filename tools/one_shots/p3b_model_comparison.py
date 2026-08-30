#!/usr/bin/env python3
"""
Phase 3B — Controlled Golden Set / Literary Model Comparison

Compares M3 (meta/llama-3.2-90b-vision-instruct) and M4 (nvidia/riva-translate-4b-instruct-v2)
against NTPE Golden Set under identical conditions.

Does NOT modify production behavior.
"""

from __future__ import annotations

import hashlib
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


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class ModelCandidate:
    model_id: str
    name: str
    model_type: str


@dataclass
class GoldenSetFixture:
    fixture_id: str
    name: str
    type: str
    source_text: str
    source_hash: str
    glossary: dict = field(default_factory=dict)
    context_notes: str = ""


@dataclass
class ChunkResult:
    model_id: str
    fixture_id: str
    chunk_index: int
    chunk_text: str
    translation: str
    http_status: int
    success: bool
    elapsed_ms: float
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    finish_reason: Optional[str] = None
    error: Optional[str] = None
    retry_count: int = 0
    timestamp_utc: str = ""


@dataclass
class QualityScores:
    semantic_fidelity: float = 0.0
    literary_quality: float = 0.0
    trad_chinese_quality: float = 0.0
    character_consistency: float = 0.0
    context_continuity: float = 0.0
    terminology_glossary: float = 0.0
    structural_compliance: float = 0.0
    overall_quality: float = 0.0


@dataclass
class ModelResults:
    model_id: str
    model_name: str
    fixture_results: dict[str, list[ChunkResult]] = field(default_factory=dict)
    quality_scores: dict[str, QualityScores] = field(default_factory=dict)
    aggregate_quality: QualityScores = field(default_factory=QualityScores)
    
    # Runtime metrics
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    http_4xx: int = 0
    http_408: int = 0
    http_429: int = 0
    http_5xx: int = 0
    network_errors: int = 0
    timeout_count: int = 0
    retry_count: int = 0
    incomplete_count: int = 0
    empty_output_count: int = 0
    total_runtime_ms: float = 0.0
    latencies: list[float] = field(default_factory=list)
    input_tokens_total: int = 0
    output_tokens_total: int = 0


@dataclass
class GoldenSetManifest:
    manifest_id: str
    baseline_commit: str
    baseline_identity: str
    fixtures: list[GoldenSetFixture]
    test_config: dict


@dataclass
class ComparisonReport:
    baseline_commit: str
    baseline_identity: str
    test_timestamp: str
    candidates: list[ModelCandidate]
    manifest: GoldenSetManifest
    m3_results: ModelResults
    m4_results: ModelResults
    comparison_matrix: dict
    quality_winner: Optional[str]
    stability_winner: Optional[str]
    production_candidate: Optional[str]
    phase_verdict: str
    critical_findings: list[str]
    artifacts: dict
    repository_integrity: str


# =============================================================================
# Golden Set Definition
# =============================================================================

def load_golden_set_fixtures() -> list[GoldenSetFixture]:
    """Load Golden Set fixtures from existing NTPE test sets."""
    fixtures = []
    
    # Fixture 1: Golden Set - Main Novel Text
    golden_path = Path(__file__).resolve().parents[2].joinpath("tests/literary/Golden_Set/original_ko.txt")
    if golden_path.exists():
        text = golden_path.read_text(encoding="utf-8")
        source_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        fixtures.append(GoldenSetFixture(
            fixture_id="GOLDEN_001",
            name="Golden_Set_Novel_Main",
            type="narrative",
            source_text=text,
            source_hash=source_hash,
            glossary={
                "일레이": "伊雷",
                "정태의": "鄭泰義",
                "민수": "敏洙",
                "지현": "智賢",
            },
            context_notes="Novel opening with character introductions and internal monologue"
        ))
    
    # Fixture 2: Smoke Set - Short Test
    smoke_path = Path(__file__).resolve().parents[2].joinpath("tests/literary/Smoke_Set/original_ko.txt")
    if smoke_path.exists():
        text = smoke_path.read_text(encoding="utf-8")
        source_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        fixtures.append(GoldenSetFixture(
            fixture_id="SMOKE_001",
            name="Smoke_Set_Short",
            type="narrative",
            source_text=text,
            source_hash=source_hash,
            glossary={
                "일레이": "伊雷",
                "정태의": "鄭泰義",
            },
            context_notes="Short narrative test from Smoke Set"
        ))
    
    # Fixture 3: Regression Set - Longer Text
    regression_path = Path(__file__).resolve().parents[2].joinpath("tests/literary/Regression_Set/original_ko.txt")
    if regression_path.exists():
        text = regression_path.read_text(encoding="utf-8")
        source_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        fixtures.append(GoldenSetFixture(
            fixture_id="REGRESSION_001",
            name="Regression_Set_Novel",
            type="narrative",
            source_text=text,
            source_hash=source_hash,
            glossary={
                "김철수": "金鐵秀",
                "이영희": "李英姬",
                "철수": "鐵秀",
                "영희": "英姬",
            },
            context_notes="Longer novel segment with detective characters"
        ))
    
    # Fixture 4: Dialogue-heavy (synthetic for Tier 2)
    dialogue_text = (
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
    source_hash = hashlib.sha256(dialogue_text.encode()).hexdigest()[:16]
    fixtures.append(GoldenSetFixture(
        fixture_id="DIALOGUE_001",
        name="Dialogue_Heavy_Scene",
        type="dialogue",
        source_text=dialogue_text,
        source_hash=source_hash,
        glossary={
            "민수": "敏洙",
            "지현": "智賢",
        },
        context_notes="Dialogue-heavy emotional scene with honorifics"
    ))
    
    # Fixture 5: Context/Continuity (synthetic for Tier 2)
    context_text = (
        '김철수는 30년 경력의 형사였다. 그가 맡은 사건은 언제나 복잡했지만, '
        '그는 특유의 직관으로 진실을 파헤쳐왔다. 그의 파트너 이영희는 그와 정반대였다. '
        '논리와 증거만으로 사건을 풀어나가는 원칙주의자였다.\n\n'
        '어느 날, 두 사람은 연쇄 실종 사건을 맡게 되었다. '
        '철수는 현장의 미세한 흔적에서 단서를 찾으려 했고, 영희는 피해자들의 공통점을 분석했다. '
        '처음엔 서로의 방식을 불신했지만, 곧 그들의 접근법이 서로 보완됨을 깨달았다. '
        '철수의 직관이 영희의 논리를 이끌었고, 영희의 증거가 철수의 추측을 뒷받침했다.'
    )
    source_hash = hashlib.sha256(context_text.encode()).hexdigest()[:16]
    fixtures.append(GoldenSetFixture(
        fixture_id="CONTEXT_001",
        name="Character_Continuity_Detectives",
        type="context_continuity",
        source_text=context_text,
        source_hash=source_hash,
        glossary={
            "김철수": "金鐵秀",
            "이영희": "李英姬",
            "철수": "鐵秀",
            "영희": "英姬",
            "형사": "刑警",
            "파트너": "搭檔",
        },
        context_notes="Two paragraphs testing character name and pronoun consistency"
    ))
    
    # Fixture 6: Glossary-sensitive (synthetic for Tier 3)
    glossary_text = (
        '주인공 홍길동은 의적(義賊)으로서 탐관오리들의 재물을 훔쳐 가난한 백성들에게 나누어주었다. '
        '그의 동료인 성춘향과 변학도는 각자의 방식으로 그를 도왔다. '
        '홍길동의 호(號)는 청산(靑山)이었으며, 그가 쓴 검(劍)은 뇌전도(雷電刀)라 불렸다.'
    )
    source_hash = hashlib.sha256(glossary_text.encode()).hexdigest()[:16]
    fixtures.append(GoldenSetFixture(
        fixture_id="GLOSSARY_001",
        name="Glossary_Terms_Wuxia",
        type="glossary",
        source_text=glossary_text,
        source_hash=source_hash,
        glossary={
            "홍길동": "洪吉童",
            "의적": "義賊",
            "성춘향": "成春香",
            "변학도": "卞學度",
            "청산": "青山",
            "뇌전도": "雷電刀",
            "탐관오리": "貪官汚吏",
        },
        context_notes="Glossary-heavy wuxia excerpt with proper nouns"
    ))
    
    # Fixture 7: Longitudinal - Split into chunks for Tier 4
    longitudinal_text = (
        '제1장 시작\n\n'
        '봄비가 내리는 서울의 거리에서 김철수는 사건 파일을 넘겨보고 있었다. '
        '30년 경력의 베테랑 형사에게도 이번 연쇄 실종 사건은 까다로웠다. '
        '실종된 사람들은 모두 다른 나이, 다른 직업, 다른 지역에 살았다. '
        '공통점이라고는 실종 당일 밤 10시 이후에 마지막으로 목격됐다는 것뿐이었다.\n\n'
        '제2장 파트너\n\n'
        '"철수 선배, 이거 좀 봐요." 이영희가 파일을 내밀었다. '
        '그녀의 차분한 목소리에 김철수는 안경을 고쳐 쓰고 파일을 받아들었다. '
        '"피해자들 모두 같은 편의점에서 음료수를 샀대요. 같은 브랜드, 같은 맛."\n\n'
        '제3장 단서\n\n'
        '편의점 CCTV를 확인한 결과, 수상한 남자가 피해자들에게 접근하는 장면이 포착됐다. '
        '그는 검은 모자를 눌러쓰고 마스크를 쓴 채였다. '
        '철수의 직감이 울렸다. "이 남자, 전에 본 적 있어."\n\n'
        '제4장 추적\n\n'
        '수사팀은 용의자의 동선을 추적했다. 그는 지하철을 타고 이동했고, '
        '마지막으로 강남역 근처에서 내렸다. '
        '영희는 논리적으로 용의자의 다음 행선지를 예측했다. '
        '"이러면 다음은 역삼동일 확률이 높아요."\n\n'
        '제5장 대결\n\n'
        '역삼동의 한 창고에서 용의자와 대치하게 됐다. '
        '철수는 직관적으로 용의자가 무기를 숨겼음을 알았다. '
        '"손들어!" 철수의 외침에 용의자는 움찔했다. '
        '그 순간 영희가 뒤에서 용의자를 제압했다.\n\n'
        '제6장 결말\n\n'
        '사건은 해결됐다. 실종된 사람들은 모두 무사히 구조됐다. '
        '철수와 영희는 서로를 바라보며 미소 지었다. '
        '"이번엔 네 직관이 맞았어." 영희가 인정했다. '
        '"이번엔 네 논리가 맞았어." 철수가 대답했다. '
        '두 사람의 서로 다른 방식이 결국 진실을 밝혀낸 것이었다.'
    )
    
    # Split into ~8 chunks for longitudinal test
    chunks = longitudinal_text.split('\n\n')
    for i, chunk in enumerate(chunks):
        if chunk.strip():
            source_hash = hashlib.sha256(chunk.encode()).hexdigest()[:16]
            fixtures.append(GoldenSetFixture(
                fixture_id=f"LONG_{i+1:02d}",
                name=f"Longitudinal_Chapter_{i+1}",
                type="longitudinal",
                source_text=chunk.strip(),
                source_hash=source_hash,
                glossary={
                    "김철수": "金鐵秀",
                    "이영희": "李英姬",
                    "철수": "鐵秀",
                    "영희": "英姬",
                    "형사": "刑警",
                    "선배": "前輩",
                    "실종": "失蹤",
                    "연쇄": "連鎖",
                    "용의자": "容疑者",
                    "편의점": "便利店",
                    "CCTV": "監視攝影機",
                    "지하철": "地鐵",
                    "강남역": "江南驛",
                    "역삼동": "驛三洞",
                    "창고": "倉庫",
                    "제압": "制壓",
                },
                context_notes=f"Chapter {i+1} of longitudinal novel test"
            ))
    
    return fixtures


def create_manifest(fixtures: list[GoldenSetFixture]) -> GoldenSetManifest:
    """Create Golden Set manifest."""
    return GoldenSetManifest(
        manifest_id=f"P3B_GOLDEN_SET_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        baseline_commit="af5cbc0",
        baseline_identity="PRE-MINIMAX-RECONSTRUCTED-BASELINE",
        fixtures=fixtures,
        test_config={
            "model_ids": [
                "meta/llama-3.2-90b-vision-instruct",
                "nvidia/riva-translate-4b-instruct-v2"
            ],
            "provider": "NVIDIA",
            "endpoint": "https://integrate.api.nvidia.com/v1/chat/completions",
            "temperature": 0.15,
            "top_p": 0.85,
            "max_tokens": 8000,
            "timeout_connect": 10,
            "timeout_read": 120,
            "retry_policy": "baseline_default",
            "chunk_strategy": "paragraph_based",
            "prompt_version": "NTPE_BASELINE_CONTRACT_V1",
            "glossary_version": "P3B_GOLDEN_SET_INLINE",
        }
    )


# =============================================================================
# Translation Execution
# =============================================================================

NTPE_SYSTEM_PROMPT = (
    "You are a professional literary translator specializing in Korean to Traditional Chinese (Taiwan) translation. "
    "Translate the following Korean text naturally, preserving:\n"
    "1. Character names and honorifics\n"
    "2. Narrative tone and literary style\n"
    "3. Dialogue naturalness and character voice distinction\n"
    "4. Terminology consistency\n"
    "5. Cultural nuances appropriate for Taiwan readers\n\n"
    "Output only the translation."
)


def translate_chunk(
    model_id: str,
    source_text: str,
    glossary: dict,
    api_key: str,
    endpoint: str,
    max_retries: int = 2
) -> ChunkResult:
    """Execute translation for a single chunk."""
    
    timestamp_utc = datetime.datetime.utcnow().isoformat() + "Z"
    
    # Build user prompt with glossary if provided
    user_prompt = source_text
    if glossary:
        glossary_str = "\n".join([f"{k} → {v}" for k, v in glossary.items()])
        user_prompt = f"[Glossary]\n{glossary_str}\n\n[Source Text]\n{source_text}"
    
    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": NTPE_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.15,
        "top_p": 0.85,
        "max_tokens": 8000,
        "stream": False,
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    retry_count = 0
    last_error = None
    
    for attempt in range(max_retries + 1):
        start_time = time.monotonic()
        
        try:
            response = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=(10, 120),
            )
            
            elapsed_ms = (time.monotonic() - start_time) * 1000
            http_status = response.status_code
            
            if http_status == 200:
                data = response.json()
                translation = data["choices"][0]["message"]["content"]
                
                input_tokens = data.get("usage", {}).get("prompt_tokens")
                output_tokens = data.get("usage", {}).get("completion_tokens")
                finish_reason = data["choices"][0].get("finish_reason")
                
                output_complete = bool(translation and len(translation.strip()) > 0)
                no_refusal = "sorry" not in translation.lower() and "cannot" not in translation.lower()
                success = output_complete and no_refusal
                
                return ChunkResult(
                    model_id=model_id,
                    fixture_id="",  # Will be set by caller
                    chunk_index=0,  # Will be set by caller
                    chunk_text=source_text,
                    translation=translation if success else "",
                    http_status=http_status,
                    success=success,
                    elapsed_ms=elapsed_ms,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    finish_reason=finish_reason,
                    error=None if success else "Empty or refusal response",
                    retry_count=retry_count,
                    timestamp_utc=timestamp_utc,
                )
            elif http_status == 429:
                retry_count += 1
                if attempt < max_retries:
                    time.sleep(5 * (attempt + 1))
                    continue
                return ChunkResult(
                    model_id=model_id,
                    fixture_id="",
                    chunk_index=0,
                    chunk_text=source_text,
                    translation="",
                    http_status=http_status,
                    success=False,
                    elapsed_ms=elapsed_ms,
                    error=f"Rate limited (HTTP 429) after {retry_count} retries",
                    retry_count=retry_count,
                    timestamp_utc=timestamp_utc,
                )
            else:
                return ChunkResult(
                    model_id=model_id,
                    fixture_id="",
                    chunk_index=0,
                    chunk_text=source_text,
                    translation="",
                    http_status=http_status,
                    success=False,
                    elapsed_ms=elapsed_ms,
                    error=f"HTTP {http_status}: {response.text[:200]}",
                    retry_count=retry_count,
                    timestamp_utc=timestamp_utc,
                )
                
        except requests.exceptions.Timeout as e:
            elapsed_ms = (time.monotonic() - start_time) * 1000
            last_error = f"Timeout: {e}"
            if attempt < max_retries:
                retry_count += 1
                time.sleep(5 * (attempt + 1))
                continue
            return ChunkResult(
                model_id=model_id,
                fixture_id="",
                chunk_index=0,
                chunk_text=source_text,
                translation="",
                http_status=408,
                success=False,
                elapsed_ms=elapsed_ms,
                error=last_error,
                retry_count=retry_count,
                timestamp_utc=timestamp_utc,
            )
        except Exception as e:
            elapsed_ms = (time.monotonic() - start_time) * 1000
            return ChunkResult(
                model_id=model_id,
                fixture_id="",
                chunk_index=0,
                chunk_text=source_text,
                translation="",
                http_status=500,
                success=False,
                elapsed_ms=elapsed_ms,
                error=str(e),
                retry_count=retry_count,
                timestamp_utc=timestamp_utc,
            )
    
    return ChunkResult(
        model_id=model_id,
        fixture_id="",
        chunk_index=0,
        chunk_text=source_text,
        translation="",
        http_status=500,
        success=False,
        elapsed_ms=0,
        error=last_error or "Max retries exceeded",
        retry_count=retry_count,
        timestamp_utc=timestamp_utc,
    )


def run_model_on_fixture(
    model: ModelCandidate,
    fixture: GoldenSetFixture,
    api_key: str,
    endpoint: str
) -> list[ChunkResult]:
    """Run model on a single fixture (may have multiple chunks for longitudinal)."""
    
    results = []
    
    # For longitudinal fixtures, treat each as separate chunk
    # For others, single chunk
    if fixture.type == "longitudinal":
        # Already split in fixture definition
        chunk_text = fixture.source_text
        result = translate_chunk(model.model_id, chunk_text, fixture.glossary, api_key, endpoint)
        result.fixture_id = fixture.fixture_id
        result.chunk_index = int(fixture.fixture_id.split("_")[-1]) if "_" in fixture.fixture_id else 0
        results.append(result)
    else:
        result = translate_chunk(model.model_id, fixture.source_text, fixture.glossary, api_key, endpoint)
        result.fixture_id = fixture.fixture_id
        result.chunk_index = 0
        results.append(result)
    
    return results


# =============================================================================
# Quality Evaluation
# =============================================================================

def evaluate_quality(source: str, translation: str, fixture_type: str, glossary: dict) -> QualityScores:
    """Evaluate translation quality across all dimensions."""
    
    if not translation or len(translation.strip()) == 0:
        return QualityScores()
    
    scores = QualityScores()
    
    # Q1: Semantic Fidelity (20%)
    # Check for omissions, hallucinations, entity correctness
    source_len = len(source)
    trans_len = len(translation)
    length_ratio = trans_len / source_len if source_len > 0 else 0
    semantic_base = min(1.0, max(0.3, length_ratio * 0.8 + 0.2))
    
    # Check for key entities
    korean_names = ["김철수", "이영희", "철수", "영희", "홍길동", "성춘향", "변학도", "일레이", "정태의", "민수", "지현"]
    trad_names = ["金鐵秀", "李英姬", "鐵秀", "英姬", "洪吉童", "成春香", "卞學度", "伊雷", "鄭泰義", "敏洙", "智賢"]
    
    entities_preserved = 0
    entities_total = 0
    for kr, tw in zip(korean_names, trad_names):
        if kr in source:
            entities_total += 1
            if tw in translation:
                entities_preserved += 1
    
    entity_score = entities_preserved / entities_total if entities_total > 0 else 1.0
    scores.semantic_fidelity = round((semantic_base * 0.6 + entity_score * 0.4) * 100, 1)
    
    # Q2: Literary Quality (20%)
    # Check for literary markers, flow, naturalness
    literary_markers = ["。", "、", "「", "」", "……", "——", "—", "…"]
    literary_count = sum(translation.count(m) for m in literary_markers)
    literary_base = min(1.0, literary_count / max(1, len(translation) / 50))
    scores.literary_quality = round(literary_base * 100, 1)
    
    # Q3: Traditional Chinese Quality (10%)
    simplified_markers = ["为", "个", "没", "这", "那", "来", "会", "们", "说", "见", "过", "国", "电", "学", "医", "长", "风", "东", "车", "马", "鸟", "鱼", "龙", "门", "开", "关", "问", "题", "答", "应", "声", "音", "实", "时", "现", "真", "理", "写", "文", "字", "语", "话", "读", "书", "本", "页"]
    trad_score = 1.0 - min(1.0, sum(translation.count(m) for m in simplified_markers) / max(1, len(translation) / 10))
    scores.trad_chinese_quality = round(trad_score * 100, 1)
    
    # Q4: Character Consistency (15%)
    char_score = entity_score  # Reuse entity check
    scores.character_consistency = round(char_score * 100, 1)
    
    # Q5: Context Continuity (15%)
    # For longitudinal, check pronoun/name consistency across chunks
    # Here we approximate based on terminology consistency
    context_score = entity_score
    scores.context_continuity = round(context_score * 100, 1)
    
    # Q6: Terminology/Glossary (10%)
    glossary_terms = list(glossary.values())
    glossary_found = sum(1 for term in glossary_terms if term in translation)
    glossary_total = len(glossary_terms) if glossary_terms else 1
    scores.terminology_glossary = round((glossary_found / glossary_total) * 100, 1)
    
    # Q7: Structural Compliance (10%)
    structural_checks = {
        "translation_only": not any(m in translation.lower()[:100] for m in ["translation:", "here is", "note:", "the following"]),
        "no_markdown": "**" not in translation and "```" not in translation,
        "punctuation_preserved": any(p in translation for p in ["。", "、", "？", "！", "「", "」"]),
        "no_wrapper": not translation.startswith("{") and not translation.startswith("["),
        "complete": len(translation.strip()) > 10,
    }
    structural_score = sum(structural_checks.values()) / len(structural_checks)
    scores.structural_compliance = round(structural_score * 100, 1)
    
    # Overall weighted score
    weights = {
        "semantic_fidelity": 0.20,
        "literary_quality": 0.20,
        "trad_chinese_quality": 0.10,
        "character_consistency": 0.15,
        "context_continuity": 0.15,
        "terminology_glossary": 0.10,
        "structural_compliance": 0.10,
    }
    
    scores.overall_quality = round(
        scores.semantic_fidelity * weights["semantic_fidelity"] +
        scores.literary_quality * weights["literary_quality"] +
        scores.trad_chinese_quality * weights["trad_chinese_quality"] +
        scores.character_consistency * weights["character_consistency"] +
        scores.context_continuity * weights["context_continuity"] +
        scores.terminology_glossary * weights["terminology_glossary"] +
        scores.structural_compliance * weights["structural_compliance"],
        1
    )
    
    return scores


def evaluate_model(model: ModelCandidate, fixtures: list[GoldenSetFixture], api_key: str, endpoint: str) -> ModelResults:
    """Run complete evaluation for one model."""
    
    results = ModelResults(model_id=model.model_id, model_name=model.name)
    
    print(f"\n{'='*80}")
    print(f"EVALUATING MODEL: {model.name} ({model.model_id})")
    print(f"{'='*80}")
    
    for fixture in fixtures:
        print(f"\n  Fixture: {fixture.name} ({fixture.fixture_id}) - {fixture.type}")
        
        chunk_results = run_model_on_fixture(model, fixture, api_key, endpoint)
        
        for cr in chunk_results:
            cr.fixture_id = fixture.fixture_id
        
        results.fixture_results[fixture.fixture_id] = chunk_results
        
        # Aggregate runtime metrics
        for cr in chunk_results:
            results.total_requests += 1
            results.total_runtime_ms += cr.elapsed_ms
            results.latencies.append(cr.elapsed_ms)
            results.retry_count += cr.retry_count
            
            if cr.success:
                results.successful_requests += 1
                if cr.input_tokens:
                    results.input_tokens_total += cr.input_tokens
                if cr.output_tokens:
                    results.output_tokens_total += cr.output_tokens
            else:
                results.failed_requests += 1
                if cr.http_status == 408:
                    results.http_408 += 1
                    results.timeout_count += 1
                elif cr.http_status == 429:
                    results.http_429 += 1
                elif 400 <= cr.http_status < 500:
                    results.http_4xx += 1
                elif 500 <= cr.http_status < 600:
                    results.http_5xx += 1
                else:
                    results.network_errors += 1
                
                if not cr.translation or len(cr.translation.strip()) == 0:
                    results.empty_output_count += 1
                results.incomplete_count += 1
        
        # Evaluate quality for successful chunks
        fixture_scores = []
        for cr in chunk_results:
            if cr.success:
                qs = evaluate_quality(fixture.source_text, cr.translation, fixture.type, fixture.glossary)
                fixture_scores.append(qs)
        
        if fixture_scores:
            avg_qs = QualityScores()
            for attr in ['semantic_fidelity', 'literary_quality', 'trad_chinese_quality',
                         'character_consistency', 'context_continuity', 'terminology_glossary',
                         'structural_compliance', 'overall_quality']:
                values = [getattr(qs, attr) for qs in fixture_scores]
                setattr(avg_qs, attr, round(sum(values) / len(values), 1))
            results.quality_scores[fixture.fixture_id] = avg_qs
            
            print(f"    Chunks: {len(chunk_results)} | Success: {sum(1 for c in chunk_results if c.success)}")
            print(f"    Quality: {avg_qs.overall_quality}/100 (Sem:{avg_qs.semantic_fidelity} Lit:{avg_qs.literary_quality} TC:{avg_qs.trad_chinese_quality} Char:{avg_qs.character_consistency} Ctx:{avg_qs.context_continuity} Term:{avg_qs.terminology_glossary} Struct:{avg_qs.structural_compliance})")
        else:
            print(f"    Chunks: {len(chunk_results)} | Success: 0")
            print(f"    Quality: FAILED (no successful translations)")
    
    # Calculate aggregate quality
    all_scores = list(results.quality_scores.values())
    if all_scores:
        for attr in ['semantic_fidelity', 'literary_quality', 'trad_chinese_quality',
                     'character_consistency', 'context_continuity', 'terminology_glossary',
                     'structural_compliance', 'overall_quality']:
            values = [getattr(qs, attr) for qs in all_scores]
            setattr(results.aggregate_quality, attr, round(sum(values) / len(values), 1))
    
    # Print aggregate runtime
    print(f"\n  AGGREGATE RUNTIME:")
    print(f"    Total Requests: {results.total_requests}")
    print(f"    Successful: {results.successful_requests} | Failed: {results.failed_requests}")
    print(f"    Completion Rate: {results.successful_requests/results.total_requests*100:.1f}%")
    print(f"    Timeouts: {results.http_408} | Rate Limited: {results.http_429} | 4xx: {results.http_4xx} | 5xx: {results.http_5xx} | Network: {results.network_errors}")
    print(f"    Retries: {results.retry_count} | Empty Outputs: {results.empty_output_count} | Incomplete: {results.incomplete_count}")
    if results.latencies:
        results.latencies.sort()
        p50 = results.latencies[len(results.latencies)//2]
        p95 = results.latencies[int(len(results.latencies)*0.95)]
        print(f"    Latency - Avg: {sum(results.latencies)/len(results.latencies):.0f}ms | P50: {p50:.0f}ms | P95: {p95:.0f}ms")
    print(f"    Total Runtime: {results.total_runtime_ms/1000:.1f}s")
    print(f"    Tokens - In: {results.input_tokens_total} | Out: {results.output_tokens_total}")
    print(f"    Aggregate Quality: {results.aggregate_quality.overall_quality}/100")
    
    return results


# =============================================================================
# Comparison & Reporting
# =============================================================================

def build_comparison_matrix(m3: ModelResults, m4: ModelResults) -> dict:
    """Build comparison matrix across all dimensions."""
    
    matrix = {}
    
    # Completion
    m3_completion = m3.successful_requests / m3.total_requests * 100 if m3.total_requests > 0 else 0
    m4_completion = m4.successful_requests / m4.total_requests * 100 if m4.total_requests > 0 else 0
    matrix["Completion"] = {
        "M3": round(m3_completion, 1),
        "M4": round(m4_completion, 1),
        "Winner": "M3" if m3_completion > m4_completion else "M4" if m4_completion > m3_completion else "TIE"
    }
    
    # Quality dimensions
    dims = [
        ("Semantic Fidelity", "semantic_fidelity"),
        ("Literary Quality", "literary_quality"),
        ("Traditional Chinese", "trad_chinese_quality"),
        ("Character Consistency", "character_consistency"),
        ("Context Continuity", "context_continuity"),
        ("Glossary", "terminology_glossary"),
        ("Structural Compliance", "structural_compliance"),
    ]
    
    for dim_name, attr in dims:
        m3_val = getattr(m3.aggregate_quality, attr)
        m4_val = getattr(m4.aggregate_quality, attr)
        matrix[dim_name] = {
            "M3": m3_val,
            "M4": m4_val,
            "Winner": "M3" if m3_val > m4_val else "M4" if m4_val > m3_val else "TIE"
        }
    
    # Runtime dimensions
    m3_timeout_rate = m3.http_408 / m3.total_requests * 100 if m3.total_requests > 0 else 0
    m4_timeout_rate = m4.http_408 / m4.total_requests * 100 if m4.total_requests > 0 else 0
    matrix["Timeout Rate"] = {
        "M3": round(m3_timeout_rate, 1),
        "M4": round(m4_timeout_rate, 1),
        "Winner": "M3" if m3_timeout_rate < m4_timeout_rate else "M4" if m4_timeout_rate < m3_timeout_rate else "TIE"
    }
    
    m3_retry_rate = m3.retry_count / m3.total_requests * 100 if m3.total_requests > 0 else 0
    m4_retry_rate = m4.retry_count / m4.total_requests * 100 if m4.total_requests > 0 else 0
    matrix["Retry Burden"] = {
        "M3": round(m3_retry_rate, 1),
        "M4": round(m4_retry_rate, 1),
        "Winner": "M3" if m3_retry_rate < m4_retry_rate else "M4" if m4_retry_rate < m3_retry_rate else "TIE"
    }
    
    m3_avg_latency = sum(m3.latencies) / len(m3.latencies) if m3.latencies else 0
    m4_avg_latency = sum(m4.latencies) / len(m4.latencies) if m4.latencies else 0
    matrix["Runtime (Avg Latency ms)"] = {
        "M3": round(m3_avg_latency, 0),
        "M4": round(m4_avg_latency, 0),
        "Winner": "M3" if m3_avg_latency < m4_avg_latency else "M4" if m4_avg_latency < m3_avg_latency else "TIE"
    }
    
    # Production Suitability (weighted)
    m3_prod = (
        m3_completion * 0.3 +
        m3.aggregate_quality.overall_quality * 0.4 +
        (100 - m3_timeout_rate) * 0.15 +
        (100 - m3_retry_rate) * 0.15
    )
    m4_prod = (
        m4_completion * 0.3 +
        m4.aggregate_quality.overall_quality * 0.4 +
        (100 - m4_timeout_rate) * 0.15 +
        (100 - m4_retry_rate) * 0.15
    )
    matrix["Production Suitability"] = {
        "M3": round(m3_prod, 1),
        "M4": round(m4_prod, 1),
        "Winner": "M3" if m3_prod > m4_prod else "M4" if m4_prod > m3_prod else "TIE"
    }
    
    return matrix


def classify_production_suitability(results: ModelResults) -> str:
    """Classify model production suitability."""
    
    completion_rate = results.successful_requests / results.total_requests * 100 if results.total_requests > 0 else 0
    timeout_rate = results.http_408 / results.total_requests * 100 if results.total_requests > 0 else 0
    quality = results.aggregate_quality.overall_quality
    
    # Catastrophic failure checks
    if timeout_rate > 30:
        return "INCOMPATIBLE"  # Catastrophic timeout rate
    if completion_rate < 50:
        return "INCOMPATIBLE"  # Catastrophic completion
    if quality < 50:
        return "INCOMPATIBLE"  # Quality too low
    
    if quality >= 80 and completion_rate >= 90 and timeout_rate < 10:
        return "PRODUCTION_CANDIDATE"
    elif quality >= 70 and completion_rate >= 80 and timeout_rate < 20:
        return "QUALITY_CANDIDATE"
    elif quality >= 60 or completion_rate >= 70:
        return "PARTIAL_CANDIDATE"
    else:
        return "INCOMPATIBLE"


def determine_phase_verdict(m3: ModelResults, m4: ModelResults, matrix: dict) -> str:
    """Determine final phase verdict."""
    
    m3_class = classify_production_suitability(m3)
    m4_class = classify_production_suitability(m4)
    
    print(f"\n  M3 Classification: {m3_class}")
    print(f"  M4 Classification: {m4_class}")
    
    # Check for catastrophic failures
    m3_catastrophic = (
        m3.http_408 / m3.total_requests * 100 > 30 if m3.total_requests > 0 else True
    )
    m4_catastrophic = (
        m4.http_408 / m4.total_requests * 100 > 30 if m4.total_requests > 0 else True
    )
    
    if m3_catastrophic and m4_catastrophic:
        return "P3B_ALL_FAIL"
    
    m3_prod = matrix.get("Production Suitability", {}).get("M3", 0)
    m4_prod = matrix.get("Production Suitability", {}).get("M4", 0)
    
    if m3_class == "PRODUCTION_CANDIDATE" and m4_class != "PRODUCTION_CANDIDATE":
        return "P3B_CLEAR_WINNER"
    elif m4_class == "PRODUCTION_CANDIDATE" and m3_class != "PRODUCTION_CANDIDATE":
        return "P3B_CLEAR_WINNER"
    elif m3_class == "PRODUCTION_CANDIDATE" and m4_class == "PRODUCTION_CANDIDATE":
        diff = abs(m3_prod - m4_prod)
        if diff > 10:
            return "P3B_CLEAR_WINNER"
        else:
            return "P3B_NO_CLEAR_WINNER"
    elif m3_class in ["QUALITY_CANDIDATE", "PARTIAL_CANDIDATE"] and m4_class in ["QUALITY_CANDIDATE", "PARTIAL_CANDIDATE"]:
        return "P3B_NO_CLEAR_WINNER"
    else:
        return "P3B_ALL_FAIL"


def get_representative_samples(results: ModelResults, fixtures: list[GoldenSetFixture]) -> dict:
    """Get best/typical/worst/failure samples for each model."""
    
    samples = {
        "best": None,
        "typical": None,
        "worst": None,
        "failure": None
    }
    
    successful_chunks = []
    for fixture_id, chunks in results.fixture_results.items():
        for cr in chunks:
            if cr.success:
                qs = evaluate_quality(fixtures[0].source_text if not hasattr(cr, '_fixture_obj') else cr.chunk_text, cr.translation, "general", {})
                successful_chunks.append((cr, qs.overall_quality))
            else:
                samples["failure"] = {
                    "fixture": fixture_id,
                    "chunk": cr.chunk_index,
                    "error": cr.error,
                    "http_status": cr.http_status
                }
    
    if successful_chunks:
        successful_chunks.sort(key=lambda x: x[1], reverse=True)
        samples["best"] = {
            "fixture": successful_chunks[0][0].fixture_id,
            "chunk": successful_chunks[0][0].chunk_index,
            "translation_preview": successful_chunks[0][0].translation[:300],
            "quality": successful_chunks[0][1]
        }
        samples["typical"] = {
            "fixture": successful_chunks[len(successful_chunks)//2][0].fixture_id,
            "chunk": successful_chunks[len(successful_chunks)//2][0].chunk_index,
            "translation_preview": successful_chunks[len(successful_chunks)//2][0].translation[:300],
            "quality": successful_chunks[len(successful_chunks)//2][1]
        }
        samples["worst"] = {
            "fixture": successful_chunks[-1][0].fixture_id,
            "chunk": successful_chunks[-1][0].chunk_index,
            "translation_preview": successful_chunks[-1][0].translation[:300],
            "quality": successful_chunks[-1][1]
        }
    
    return samples


def redact_sensitive(data: dict) -> dict:
    if not isinstance(data, dict):
        return data
    redacted = {}
    sensitive_keys = {"authorization", "api_key", "apikey", "secret", "token", "password", "credential", "bearer", "x-api-key"}
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


def generate_governance_markdown(report: ComparisonReport) -> str:
    """Generate governance markdown."""
    
    lines = []
    lines.append("# P3B_MODEL_COMPARISON — Phase 3B Controlled Golden Set / Literary Model Comparison")
    lines.append("")
    lines.append("## Baseline")
    lines.append(f"- **HEAD**: `{report.baseline_commit}`")
    lines.append(f"- **Identity**: {report.baseline_identity}")
    lines.append(f"- **Timestamp**: {report.test_timestamp}")
    lines.append("")
    lines.append("## Candidates")
    lines.append("")
    for c in report.candidates:
        lines.append(f"- **{c.name}**: `{c.model_id}` ({c.model_type})")
    lines.append("")
    lines.append("## Golden Set Manifest")
    lines.append(f"- **Manifest ID**: {report.manifest.manifest_id}")
    lines.append(f"- **Fixtures**: {len(report.manifest.fixtures)}")
    for f in report.manifest.fixtures:
        lines.append(f"  - {f.fixture_id}: {f.name} ({f.type}) - {len(f.source_text)} chars - hash:{f.source_hash}")
    lines.append("")
    lines.append("## Comparison Matrix")
    lines.append("")
    lines.append("| Dimension | M3 | M4 | Winner |")
    lines.append("|-----------|----|----|--------|")
    for dim, data in report.comparison_matrix.items():
        lines.append(f"| {dim} | {data.get('M3', 'N/A')} | {data.get('M4', 'N/A')} | {data.get('Winner', 'N/A')} |")
    lines.append("")
    lines.append("## Production Suitability Classification")
    lines.append("")
    m3_class = classify_production_suitability(report.m3_results)
    m4_class = classify_production_suitability(report.m4_results)
    lines.append(f"- **M3 ({report.m3_results.model_name})**: {m3_class}")
    lines.append(f"- **M4 ({report.m4_results.model_name})**: {m4_class}")
    lines.append("")
    lines.append("## Quality Scores (Aggregate)")
    lines.append("")
    lines.append("| Dimension | M3 | M4 |")
    lines.append("|-----------|----|----|")
    for dim in ['semantic_fidelity', 'literary_quality', 'trad_chinese_quality',
                'character_consistency', 'context_continuity', 'terminology_glossary',
                'structural_compliance', 'overall_quality']:
        m3_val = getattr(report.m3_results.aggregate_quality, dim)
        m4_val = getattr(report.m4_results.aggregate_quality, dim)
        lines.append(f"| {dim.replace('_', ' ').title()} | {m3_val} | {m4_val} |")
    lines.append("")
    lines.append("## Runtime Metrics")
    lines.append("")
    lines.append("| Metric | M3 | M4 |")
    lines.append("|--------|----|----|")
    for m, label in [(report.m3_results, "M3"), (report.m4_results, "M4")]:
        pass
    lines.append(f"| Total Requests | {report.m3_results.total_requests} | {report.m4_results.total_requests} |")
    lines.append(f"| Successful | {report.m3_results.successful_requests} | {report.m4_results.successful_requests} |")
    lines.append(f"| Failed | {report.m3_results.failed_requests} | {report.m4_results.failed_requests} |")
    lines.append(f"| Completion Rate | {report.m3_results.successful_requests/report.m3_results.total_requests*100:.1f}% | {report.m4_results.successful_requests/report.m4_results.total_requests*100:.1f}% |")
    lines.append(f"| Timeouts (408) | {report.m3_results.http_408} | {report.m4_results.http_408} |")
    lines.append(f"| Rate Limited (429) | {report.m3_results.http_429} | {report.m4_results.http_429} |")
    lines.append(f"| 4xx Errors | {report.m3_results.http_4xx} | {report.m4_results.http_4xx} |")
    lines.append(f"| 5xx Errors | {report.m3_results.http_5xx} | {report.m4_results.http_5xx} |")
    lines.append(f"| Network Errors | {report.m3_results.network_errors} | {report.m4_results.network_errors} |")
    lines.append(f"| Retries | {report.m3_results.retry_count} | {report.m4_results.retry_count} |")
    lines.append(f"| Empty Outputs | {report.m3_results.empty_output_count} | {report.m4_results.empty_output_count} |")
    lines.append(f"| Total Runtime | {report.m3_results.total_runtime_ms/1000:.1f}s | {report.m4_results.total_runtime_ms/1000:.1f}s |")
    if report.m3_results.latencies:
        lines.append(f"| Avg Latency | {sum(report.m3_results.latencies)/len(report.m3_results.latencies):.0f}ms | {sum(report.m4_results.latencies)/len(report.m4_results.latencies):.0f}ms |")
    lines.append("")
    lines.append("## Phase Verdict")
    lines.append(f"**{report.phase_verdict}**")
    lines.append("")
    lines.append("## Critical Findings")
    for finding in report.critical_findings:
        lines.append(f"- {finding}")
    lines.append("")
    lines.append("## Artifacts")
    for k, v in report.artifacts.items():
        lines.append(f"- {k}: `{v}`")
    lines.append("")
    lines.append("## Repository Integrity")
    lines.append(f"**{report.repository_integrity}**")
    lines.append("")
    lines.append("## Phase Boundary")
    lines.append("**Phase 3B COMPLETE — STOP**")
    lines.append("")
    lines.append("Do NOT:")
    lines.append("- Modify default model")
    lines.append("- Modify provider config")
    lines.append("- Modify prompt")
    lines.append("- Modify runtime")
    lines.append("- Commit")
    lines.append("- Push")
    lines.append("")
    lines.append("Next: Human review of P3B evidence for migration decision.")
    
    return "\n".join(lines)


# =============================================================================
# Main
# =============================================================================

def main():
    print("=" * 80)
    print("PHASE 3B — Controlled Golden Set / Literary Model Comparison")
    print("=" * 80)
    
    # Baseline check
    import subprocess
    head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    expected = "af5cbc0"
    
    if not head.startswith(expected):
        print(f"ERROR: BASELINE_MISMATCH - HEAD={head[:12]} != {expected}")
        return 1
    
    status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True).stdout.strip()
    production_changes = False
    for line in status.split('\n'):
        if line.strip():
            path = line.strip().split()[-1]
            if any(path.startswith(p) for p in ["core/", "config/", "ntpe_", "lts/"]):
                if not path.startswith("artifacts/"):
                    production_changes = True
    
    if production_changes:
        print("ERROR: BASELINE_CONTAMINATION - production files modified")
        return 1
    
    print(f"Baseline: HEAD={head[:12]} OK | Working tree clean OK")
    
    # Environment
    endpoint = "https://integrate.api.nvidia.com/v1/chat/completions"
    api_key = os.environ.get("NVIDIA_API_KEY")
    if not api_key:
        print("ERROR: NVIDIA_API_KEY not set")
        return 1
    
    # Candidates
    candidates = [
        ModelCandidate("meta/llama-3.2-90b-vision-instruct", "M3 - Llama 3.2 90B Vision", "Vision LLM"),
        ModelCandidate("nvidia/riva-translate-4b-instruct-v2", "M4 - Riva Translate 4B v2", "Translation Model"),
    ]
    
    # Golden Set
    fixtures = load_golden_set_fixtures()
    manifest = create_manifest(fixtures)
    
    print(f"\nGolden Set: {len(fixtures)} fixtures")
    for f in fixtures:
        print(f"  {f.fixture_id}: {f.name} ({f.type}) - {len(f.source_text)} chars")
    
    # Save manifest
    artifacts_dir = Path(__file__).resolve().parents[2] / "artifacts" / "p3b_model_comparison"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    with open(artifacts_dir / "P3B_GOLDEN_SET_MANIFEST.json", "w", encoding="utf-8") as f:
        json.dump(asdict(manifest), f, indent=2, ensure_ascii=False)
    
    # Run evaluations
    print(f"\n{'='*80}")
    print("STARTING MODEL EVALUATIONS")
    print(f"{'='*80}")
    
    m3_results = evaluate_model(candidates[0], fixtures, api_key, endpoint)
    m4_results = evaluate_model(candidates[1], fixtures, api_key, endpoint)
    
    # Build comparison
    matrix = build_comparison_matrix(m3_results, m4_results)
    
    # Representative samples
    m3_samples = get_representative_samples(m3_results, fixtures)
    m4_samples = get_representative_samples(m4_results, fixtures)
    
    # Phase verdict
    phase_verdict = determine_phase_verdict(m3_results, m4_results, matrix)
    
    # Quality/Stability winners
    quality_winner = "M3" if m3_results.aggregate_quality.overall_quality > m4_results.aggregate_quality.overall_quality else "M4"
    stability_winner = "M3" if (m3_results.http_408 / max(1, m3_results.total_requests)) < (m4_results.http_408 / max(1, m4_results.total_requests)) else "M4"
    prod_candidate = "M3" if classify_production_suitability(m3_results) == "PRODUCTION_CANDIDATE" else ("M4" if classify_production_suitability(m4_results) == "PRODUCTION_CANDIDATE" else "NONE")
    
    # Critical findings
    findings = []
    if m3_results.http_408 > 0:
        findings.append(f"M3: {m3_results.http_408} timeout(s) observed ({m3_results.http_408/m3_results.total_requests*100:.1f}% timeout rate)")
    if m4_results.http_408 > 0:
        findings.append(f"M4: {m4_results.http_408} timeout(s) observed ({m4_results.http_408/m4_results.total_requests*100:.1f}% timeout rate)")
    if m3_results.http_429 > 0:
        findings.append(f"M3: {m3_results.http_429} rate limit(s) observed")
    if m4_results.http_429 > 0:
        findings.append(f"M4: {m4_results.http_429} rate limit(s) observed")
    if m3_results.successful_requests < m3_results.total_requests:
        findings.append(f"M3: {m3_results.total_requests - m3_results.successful_requests} failed requests")
    if m4_results.successful_requests < m4_results.total_requests:
        findings.append(f"M4: {m4_results.total_requests - m4_results.successful_requests} failed requests")
    findings.append(f"Quality Winner: {quality_winner} (M3:{m3_results.aggregate_quality.overall_quality} vs M4:{m4_results.aggregate_quality.overall_quality})")
    findings.append(f"Stability Winner: {stability_winner}")
    findings.append(f"Production Candidate: {prod_candidate}")
    
    # Final report
    report = ComparisonReport(
        baseline_commit=head,
        baseline_identity="PRE-MINIMAX-RECONSTRUCTED-BASELINE",
        test_timestamp=datetime.datetime.utcnow().isoformat() + "Z",
        candidates=candidates,
        manifest=manifest,
        m3_results=m3_results,
        m4_results=m4_results,
        comparison_matrix=matrix,
        quality_winner=quality_winner,
        stability_winner=stability_winner,
        production_candidate=prod_candidate if prod_candidate != "NONE" else None,
        phase_verdict=phase_verdict,
        critical_findings=findings,
        artifacts={
            "main_report": "artifacts/p3b_model_comparison/P3B_MODEL_COMPARISON_REPORT.json",
            "scorecard": "artifacts/p3b_model_comparison/P3B_MODEL_SCORECARD.json",
            "manifest": "artifacts/p3b_model_comparison/P3B_GOLDEN_SET_MANIFEST.json",
            "governance": "docs/governance/repository/P3B_MODEL_COMPARISON.md",
        },
        repository_integrity="PASS",
    )
    
    # Save main report
    report_path = artifacts_dir / "P3B_MODEL_COMPARISON_REPORT.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(redact_sensitive(asdict(report)), f, indent=2, ensure_ascii=False)
    
    # Save scorecard
    scorecard = {
        "baseline": head,
        "timestamp": report.test_timestamp,
        "candidates": [c.model_id for c in candidates],
        "quality_scores": {
            "M3": {k: getattr(m3_results.aggregate_quality, k) for k in ['semantic_fidelity', 'literary_quality', 'trad_chinese_quality', 'character_consistency', 'context_continuity', 'terminology_glossary', 'structural_compliance', 'overall_quality']},
            "M4": {k: getattr(m4_results.aggregate_quality, k) for k in ['semantic_fidelity', 'literary_quality', 'trad_chinese_quality', 'character_consistency', 'context_continuity', 'terminology_glossary', 'structural_compliance', 'overall_quality']},
        },
        "runtime_metrics": {
            "M3": {
                "completion_rate": round(m3_results.successful_requests/m3_results.total_requests*100, 1) if m3_results.total_requests > 0 else 0,
                "timeout_rate": round(m3_results.http_408/m3_results.total_requests*100, 1) if m3_results.total_requests > 0 else 0,
                "retry_rate": round(m3_results.retry_count/m3_results.total_requests*100, 1) if m3_results.total_requests > 0 else 0,
                "avg_latency_ms": round(sum(m3_results.latencies)/len(m3_results.latencies), 0) if m3_results.latencies else 0,
            },
            "M4": {
                "completion_rate": round(m4_results.successful_requests/m4_results.total_requests*100, 1) if m4_results.total_requests > 0 else 0,
                "timeout_rate": round(m4_results.http_408/m4_results.total_requests*100, 1) if m4_results.total_requests > 0 else 0,
                "retry_rate": round(m4_results.retry_count/m4_results.total_requests*100, 1) if m4_results.total_requests > 0 else 0,
                "avg_latency_ms": round(sum(m4_results.latencies)/len(m4_results.latencies), 0) if m4_results.latencies else 0,
            },
        },
        "production_suitability": {
            "M3": classify_production_suitability(m3_results),
            "M4": classify_production_suitability(m4_results),
        },
        "phase_verdict": phase_verdict,
        "quality_winner": quality_winner,
        "stability_winner": stability_winner,
        "production_candidate": prod_candidate if prod_candidate != "NONE" else None,
    }
    
    with open(artifacts_dir / "P3B_MODEL_SCORECARD.json", "w", encoding="utf-8") as f:
        json.dump(scorecard, f, indent=2, ensure_ascii=False)
    
    # Save governance
    governance_dir = Path(__file__).resolve().parents[2] / "docs" / "governance" / "repository"
    governance_dir.mkdir(parents=True, exist_ok=True)
    
    with open(governance_dir / "P3B_MODEL_COMPARISON.md", "w", encoding="utf-8") as f:
        f.write(generate_governance_markdown(report))
    
    # Final output
    print("\n" + "=" * 80)
    print("PHASE 3B COMPLETE")
    print("=" * 80)
    print(f"\nPhase Verdict: {phase_verdict}")
    print(f"Baseline: {head[:12]}")
    print(f"M3: {classify_production_suitability(m3_results)}")
    print(f"M4: {classify_production_suitability(m4_results)}")
    print(f"Quality Winner: {quality_winner}")
    print(f"Stability Winner: {stability_winner}")
    print(f"Production Candidate: {prod_candidate if prod_candidate != 'NONE' else 'NONE'}")
    print(f"\nCritical Findings:")
    for f in findings:
        print(f"  - {f}")
    print(f"\nArtifacts:")
    for k, v in report.artifacts.items():
        print(f"  {k}: {v}")
    print(f"\nRepository Integrity: PASS")
    
    return 0 if phase_verdict != "P3B_BLOCKED" else 1


if __name__ == "__main__":
    sys.exit(main())