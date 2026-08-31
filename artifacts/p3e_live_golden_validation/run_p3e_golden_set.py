#!/usr/bin/env python3
"""
Phase 3E Live Golden Set Validation

Executes the P3B Golden Set fixtures through the canonical production path
and compares results against the P3B baseline.

P3B Baseline:
- Completion: 100%
- Timeout: 0
- Quality: 80.0/100
- Average Latency: 19.2s
"""

import json
import os
import sys
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from ntpe_production_translate import run_txt, build_parser
from lts.txt_translation_runtime import TxtTranslationOptions, translate_txt
from core.translation_runtime import TranslationRuntime

@dataclass
class FixtureResult:
    fixture_id: str
    name: str
    type: str
    success: bool
    translation: str
    latency_seconds: float
    error: str = ""
    http_status: int = 0
    quality_score: float = 0.0
    word_count: int = 0
    char_count: int = 0

@dataclass
class GoldenSetResults:
    total_fixtures: int
    successful_fixtures: int
    failed_fixtures: int
    completion_rate: float
    timeout_count: int
    http_errors: Dict[str, int]
    average_latency: float
    median_latency: float
    p95_latency: float
    average_quality: float
    fixture_results: List[FixtureResult]

def load_golden_set_manifest() -> Dict:
    """Load the P3B Golden Set manifest."""
    manifest_path = PROJECT_ROOT / "artifacts" / "p3b_model_comparison" / "P3B_GOLDEN_SET_MANIFEST.json"
    with open(manifest_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def run_fixture(fixture: Dict, temp_dir: Path) -> FixtureResult:
    """Run a single fixture through the canonical production path."""
    fixture_id = fixture["fixture_id"]
    name = fixture["name"]
    fixture_type = fixture["type"]
    source_text = fixture["source_text"]
    glossary = fixture.get("glossary", {})
    
    print(f"\n{'='*60}")
    print(f"Running fixture: {fixture_id} ({name})")
    print(f"Type: {fixture_type}")
    print(f"Source length: {len(source_text)} chars")
    print(f"{'='*60}")
    
    # Ensure temp directory exists
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # Create temp input file
    input_file = temp_dir / f"{fixture_id}_input.txt"
    with open(input_file, 'w', encoding='utf-8') as f:
        f.write(source_text)
    
    # Create glossary file if needed
    glossary_file = None
    if glossary:
        glossary_file = temp_dir / f"{fixture_id}_glossary.json"
        with open(glossary_file, 'w', encoding='utf-8') as f:
            json.dump(glossary, f, ensure_ascii=False, indent=2)
    
    # Output directory
    output_dir = temp_dir / f"{fixture_id}_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Build translation options matching P3B test config
    options = TxtTranslationOptions(
        input_path=input_file,
        output_dir=output_dir,
        chunk_size=600,  # P3B used 600 chunk size
        chunk_size_explicit=True,
        model="meta/llama-3.2-90b-vision-instruct",
        project_name=f"P3E_Golden_Set_{name}",
        resume=False,
        dry_run=False,
        max_retries=3,
        retry_base_seconds=5.0,
        glossary_path=glossary_file,
        character_memory_path=None,
        strict_lock_terms=True,
        qa_enabled=True,
        qa_fail_policy="retry",
        min_length_ratio=0.25,
        max_korean_chars=2,
        max_repeated_lines=2,
        output_formatter_enabled=True,
        taiwan_traditional_normalization=True,
        quality_profile="literary",
        speed="balanced",
        simplified_chinese_policy="normalize",
        progress_enabled=True,
        quality_integration_v72=False,
        quality_character_memory_v72=False,
        quality_context_scene_v72=False,
        quality_naturalness_v72=False,
        quality_integration_kill_switch_v72=False,
        quality_delivery_v83=False,
        quality_delivery_formats_v83=("txt",),
    )
    
    start_time = time.time()
    error = ""
    http_status = 0
    translation = ""
    success = False
    elapsed = 0.0
    
    try:
        # Run through canonical production path
        # Using TranslationRuntime directly for clean execution
        runtime = TranslationRuntime(root=PROJECT_ROOT)
        result = runtime.translate_txt(options)
        
        elapsed = time.time() - start_time
        
        if result.get("status") == "success":
            success = True
            # Read the translated output
            output_files = list(output_dir.glob("*_zh.txt"))
            if output_files:
                with open(output_files[0], 'r', encoding='utf-8') as f:
                    translation = f.read()
            
            # Extract latency from result
            latency = elapsed
            
            print(f"[SUCCESS] Latency: {latency:.1f}s")
            print(f"  Output length: {len(translation)} chars")
            
        else:
            error = result.get("error", "Unknown error")
            elapsed = time.time() - start_time
            print(f"[FAILED] - {error}")
            print(f"  Elapsed: {elapsed:.1f}s")
            
            # Try to extract HTTP status from error
            if "408" in error:
                http_status = 408
            elif "429" in error:
                http_status = 429
            elif "400" in error:
                http_status = 400
            elif "503" in error:
                http_status = 503
            elif "500" in error:
                http_status = 500
                
    except Exception as e:
        elapsed = time.time() - start_time
        error = str(e)
        http_status = 0
        print(f"[EXCEPTION] - {error}")
        print(f"  Elapsed: {elapsed:.1f}s")
    
    # Calculate basic quality metrics
    word_count = len(translation.split()) if translation else 0
    char_count = len(translation) if translation else 0
    
    return FixtureResult(
        fixture_id=fixture_id,
        name=name,
        type=fixture_type,
        success=success,
        translation=translation,
        latency_seconds=elapsed,
        error=error,
        http_status=http_status,
        word_count=word_count,
        char_count=char_count
    )

def compute_quality_score(translation: str, source: str, glossary: Dict) -> float:
    """Compute a basic quality score based on various metrics."""
    if not translation:
        return 0.0
    
    score = 100.0
    
    # Length ratio check
    source_chars = len(source)
    trans_chars = len(translation)
    ratio = trans_chars / max(1, source_chars)
    if ratio < 0.5 or ratio > 2.0:
        score -= 20
    
    # Glossary adherence
    glossary_terms = list(glossary.keys())
    if glossary_terms:
        found = sum(1 for term in glossary_terms if term in translation)
        adherence = found / len(glossary_terms)
        score *= (0.7 + 0.3 * adherence)
    
    # Basic completeness (not empty, not just whitespace)
    if not translation.strip():
        return 0.0
    
    # Korean residue check (should be minimal in target language)
    korean_chars = sum(1 for c in translation if '\uac00' <= c <= '\ud7a3' or '\u1100' <= c <= '\u11ff')
    if korean_chars > 10:
        score -= min(20, korean_chars)
    
    # Repeated lines check
    lines = translation.split('\n')
    from collections import Counter
    line_counts = Counter(line.strip() for line in lines if line.strip())
    max_repeats = max(line_counts.values()) if line_counts else 1
    if max_repeats > 3:
        score -= min(15, (max_repeats - 3) * 3)
    
    return max(0.0, min(100.0, score))

def run_golden_set() -> GoldenSetResults:
    """Run the complete Golden Set validation."""
    manifest = load_golden_set_manifest()
    fixtures = manifest["fixtures"]
    
    # Create temp directory
    temp_dir = Path(PROJECT_ROOT) / "artifacts" / "p3e_live_golden_validation" / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Phase 3E Live Golden Set Validation")
    print(f"Total fixtures: {len(fixtures)}")
    print(f"Model: meta/llama-3.2-90b-vision-instruct")
    print(f"Provider: NVIDIA")
    print(f"Started at: {datetime.now().isoformat()}")
    
    fixture_results = []
    latencies = []
    http_errors = {}
    timeout_count = 0
    
    for i, fixture in enumerate(fixtures, 1):
        print(f"\n[{i}/{len(fixtures)}] Processing {fixture['fixture_id']}...")
        result = run_fixture(fixture, temp_dir / fixture["fixture_id"])
        
        # Compute quality score
        source_text = fixture["source_text"]
        glossary = fixture.get("glossary", {})
        quality_score = compute_quality_score(result.translation, source_text, fixture.get("glossary", {}))
        result.quality_score = quality_score
        
        fixture_results.append(result)
        
        # Collect metrics
        if result.success:
            latencies.append(result.latency_seconds)
        else:
            if result.http_status == 408 or "timeout" in result.error.lower():
                timeout_count += 1
            if result.http_status:
                http_errors[str(result.http_status)] = http_errors.get(str(result.http_status), 0) + 1
    
    # Calculate aggregate metrics
    total = len(fixture_results)
    successful = sum(1 for r in fixture_results if r.success)
    failed = total - successful
    completion_rate = (successful / total * 100) if total > 0 else 0
    
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    sorted_latencies = sorted(latencies)
    median_latency = sorted_latencies[len(sorted_latencies) // 2] if sorted_latencies else 0
    p95_idx = int(len(sorted_latencies) * 0.95)
    p95_latency = sorted_latencies[p95_idx] if sorted_latencies else 0
    
    avg_quality = sum(r.quality_score for r in fixture_results) / len(fixture_results) if fixture_results else 0
    
    return GoldenSetResults(
        total_fixtures=total,
        successful_fixtures=successful,
        failed_fixtures=failed,
        completion_rate=completion_rate,
        timeout_count=timeout_count,
        http_errors=http_errors,
        average_latency=avg_latency,
        median_latency=median_latency,
        p95_latency=p95_latency,
        average_quality=avg_quality,
        fixture_results=fixture_results
    )

def main():
    print("=" * 70)
    print("Phase 3E - Live Golden Set Validation")
    print("=" * 70)
    
    results = run_golden_set()
    
    # Save detailed results
    output_dir = Path(PROJECT_ROOT) / "artifacts" / "p3e_live_golden_validation"
    
    # Save fixture results
    with open(output_dir / "P3E_FIXTURE_RESULTS.json", 'w', encoding='utf-8') as f:
        json.dump([asdict(r) for r in results.fixture_results], f, ensure_ascii=False, indent=2)
    
    # Save summary
    with open(output_dir / "P3E_LIVE_GOLDEN_VALIDATION_REPORT.json", 'w', encoding='utf-8') as f:
        json.dump(asdict(results), f, ensure_ascii=False, indent=2)
    
    # Print summary
    print("\n" + "=" * 70)
    print("PHASE 3E LIVE GOLDEN SET VALIDATION - SUMMARY")
    print("=" * 70)
    print(f"Total Fixtures:       {results.total_fixtures}")
    print(f"Successful:           {results.successful_fixtures}")
    print(f"Failed:               {results.failed_fixtures}")
    print(f"Completion Rate:      {results.completion_rate:.1f}%")
    print(f"Timeout Count:        {results.timeout_count}")
    print(f"HTTP Errors:          {results.http_errors}")
    print(f"Average Latency:      {results.average_latency:.1f}s")
    print(f"Median Latency:       {results.median_latency:.1f}s")
    print(f"P95 Latency:          {results.p95_latency:.1f}s")
    print(f"Average Quality:      {results.average_quality:.1f}/100")
    
    # P3B Baseline comparison
    print("\n" + "-" * 70)
    print("P3B BASELINE COMPARISON")
    print("-" * 70)
    print(f"P3B Completion:       100%      -> P3E: {results.completion_rate:.1f}%")
    print(f"P3B Timeout:          0         -> P3E: {results.timeout_count}")
    print(f"P3B Quality:          80.0/100  -> P3E: {results.average_quality:.1f}/100")
    print(f"P3B Avg Latency:      19.2s     -> P3E: {results.average_latency:.1f}s")
    
    # Determine verdict
    regression = False
    if results.completion_rate < 95:
        regression = True
    if results.average_quality < 70:
        regression = True
    if results.timeout_count > 0:
        regression = True
    
    if regression:
        print("\n[REGRESSION DETECTED]")
    else:
        print("\n[NO MATERIAL REGRESSION]")
    
    print("\n" + "=" * 70)
    
    return results

if __name__ == "__main__":
    main()