from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
SOURCE = ROOT / "audits" / "legacy_capability_recovery" / "source_material"
DECISIONS = {
    "KEEP_CURRENT",
    "MERGE_WITH_CURRENT",
    "REIMPLEMENT_FROM_CONCEPT",
    "EXPERIMENT_ONLY",
    "DROP_UNSAFE",
    "LICENSE_OR_SECURITY_BLOCKED",
}


def write_json(name: str, value: object) -> None:
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(name: str, value: str) -> None:
    (OUT / name).write_text(value.rstrip() + "\n", encoding="utf-8")


def git_files() -> list[str]:
    result = subprocess.run(
        ["git", "-c", "core.quotepath=false", "ls-files"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]


def digest_paths(paths: list[str]) -> dict[str, object]:
    h = hashlib.sha256()
    included = []
    for rel in sorted(set(paths)):
        path = ROOT / rel
        if not path.is_file():
            continue
        data = path.read_bytes()
        item_hash = hashlib.sha256(data).hexdigest()
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        h.update(item_hash.encode("ascii"))
        h.update(b"\n")
        included.append({"path": rel, "sha256": item_hash})
    return {"aggregate_sha256": h.hexdigest(), "file_count": len(included), "files": included}


def baseline_hashes() -> dict[str, object]:
    files = git_files()
    groups = {
        "production": [p for p in files if p == "ntpe_production_translate.py" or p.startswith("core/workflow/production_")],
        "runtime": [p for p in files if p.startswith(("core/translation_runtime/", "core/translation_scheduler/", "core/translation_reliability/")) or (p.startswith("lts/") and "runtime" in p)],
        "provider": [p for p in files if p.startswith("core/ai_provider/") or p.startswith("core/adaptive_context_real_provider_") or p.startswith("core/adaptive_context_authorized_provider_") or p.startswith("ntpe_provider") or p == "core/translation_runtime/runtime_provider.py"],
        "prompt": [p for p in files if p.startswith(("core/prompt_builder/", "core/prompt_compiler/", "core/translation_prompt_improvement_planner/", "prompt_packages/"))],
        "tic_batch7": [p for p in files if "tic_batch7" in p.lower() or p == "docs/translation_intelligence/TIC_BATCH7_OFFLINE_TRANSLATION_QUALITY_GATE.md"],
    }
    return {name: digest_paths(paths) for name, paths in groups.items()}


CURRENT_MAP = [
    {"capability": "Runtime", "current_module": "core/translation_runtime; ntpe_production_translate.py", "production_connected": True, "frozen": True, "tested": True, "quality_value": "shared translation execution contract and runtime QA", "performance_cost": "provider and QA dependent", "known_limitations": "must preserve frozen interfaces"},
    {"capability": "Provider Layer", "current_module": "core/ai_provider; core/translation_runtime/runtime_provider.py", "production_connected": True, "frozen": True, "tested": True, "quality_value": "policy, retry, security, routing and observability", "performance_cost": "request and retry latency", "known_limitations": "real execution requires explicit authorization"},
    {"capability": "Resume/Recovery", "current_module": "core/translation_runtime/runtime_recovery.py; core/translation_scheduler/journal.py", "production_connected": True, "frozen": True, "tested": True, "quality_value": "prevents completed work loss", "performance_cost": "small checkpoint I/O", "known_limitations": "not a content-addressed chunk cache"},
    {"capability": "Chunking", "current_module": "core/translation_runtime/runtime_chunk.py; core/translation_scheduler", "production_connected": True, "frozen": True, "tested": True, "quality_value": "bounded long-form execution", "performance_cost": "more chunks can add requests", "known_limitations": "cache identity is outside the splitter"},
    {"capability": "Output Assembly", "current_module": "core/translation_runtime/runtime_output.py; core/translation_scheduler/collector.py", "production_connected": True, "frozen": True, "tested": True, "quality_value": "ordered, validated output", "performance_cost": "small disk I/O", "known_limitations": "does not validate legacy temp files"},
    {"capability": "Glossary", "current_module": "core/glossary.py; core/prompt_builder/glossary_selector.py", "production_connected": True, "frozen": True, "tested": True, "quality_value": "stable terminology and names", "performance_cost": "prompt tokens", "known_limitations": "unknown names still require governed evidence"},
    {"capability": "Character Memory", "current_module": "core/intelligence/character_memory.py; core/translation_resources/character_memory_resource.py", "production_connected": False, "frozen": True, "tested": True, "quality_value": "character continuity primitives", "performance_cost": "context and token cost", "known_limitations": "no evidence-governed V2 record or production injection"},
    {"capability": "Adaptive Context", "current_module": "core/adaptive_context", "production_connected": True, "frozen": True, "tested": True, "quality_value": "ranked, budgeted prior context", "performance_cost": "bounded token and selection cost", "known_limitations": "legacy fixed tail is not a first-class evidence record"},
    {"capability": "Narrative State", "current_module": "core/context; core/intelligence/narrative_*", "production_connected": False, "frozen": True, "tested": True, "quality_value": "scene, perspective and relationship analysis", "performance_cost": "analysis and storage", "known_limitations": "not automatically injected into production prompts"},
    {"capability": "Quality Engine", "current_module": "core/translation_quality_v5; core/quality", "production_connected": True, "frozen": True, "tested": True, "quality_value": "structured completeness, terminology, repetition and repair", "performance_cost": "local analysis plus gated retry", "known_limitations": "some semantic judgments need evidence"},
    {"capability": "TIC Failure Corpus", "current_module": "core/translation_intelligence_corpus; artifacts/tic_batch7", "production_connected": False, "frozen": True, "tested": True, "quality_value": "human-reviewed failure evidence", "performance_cost": "offline only", "known_limitations": "coverage follows approved corpus"},
    {"capability": "Active Regression", "current_module": "core/translation_intelligence_corpus/quality_regression.py", "production_connected": False, "frozen": True, "tested": True, "quality_value": "prevents known defect recurrence", "performance_cost": "offline test time", "known_limitations": "not a runtime repair mechanism"},
    {"capability": "Offline Quality Gate", "current_module": "core/translation_intelligence_corpus/offline_quality_gate.py", "production_connected": False, "frozen": True, "tested": True, "quality_value": "evidence-based candidate evaluation", "performance_cost": "offline only", "known_limitations": "does not itself generate translations"},
    {"capability": "Prompt Builder", "current_module": "core/prompt_builder; core/prompt_compiler", "production_connected": True, "frozen": True, "tested": True, "quality_value": "structured prompt composition and discipline", "performance_cost": "prompt tokens", "known_limitations": "Batch 1 cannot change prompt behavior"},
    {"capability": "Stage 11 Quality Framework", "current_module": "core/translation_quality_defects; core/translation_quality_metrics; core/translation_quality_framework_integration", "production_connected": False, "frozen": True, "tested": True, "quality_value": "defect taxonomy, metrics, review and governance", "performance_cost": "offline review", "known_limitations": "framework output is evidence, not automatic approval"},
    {"capability": "Stage 12 Candidate", "current_module": "core/literary_prompt_quality_candidate_v72", "production_connected": False, "frozen": True, "tested": True, "quality_value": "controlled evidence-based prompt candidate", "performance_cost": "candidate validation only", "known_limitations": "candidate_enabled=false; not production"},
]


def legacy(capability_id: str, legacy_file: str, legacy_symbol: str, description: str, inputs: list[str], outputs: list[str], side_effects: list[str], provider_calls: int | str, disk_writes: list[str], state_files: list[str], quality_intent: str, reliability_intent: str, performance_intent: str, risks: tuple[str, str, str, str], equivalent: str, gap: str) -> dict[str, object]:
    return {
        "capability_id": capability_id, "legacy_file": legacy_file, "legacy_symbol": legacy_symbol,
        "description": description, "inputs": inputs, "outputs": outputs, "side_effects": side_effects,
        "provider_calls": provider_calls, "disk_writes": disk_writes, "state_files": state_files,
        "quality_intent": quality_intent, "reliability_intent": reliability_intent, "performance_intent": performance_intent,
        "security_risk": risks[0], "quality_risk": risks[1], "runtime_risk": risks[2], "data_integrity_risk": risks[3],
        "current_ntpe_equivalent": equivalent, "feature_gap": gap,
    }


L = "v12_dynamic_memory_legacy.txt"
R = "translate_realtime_v2_legacy.txt"
LEGACY = [
    legacy("character_memory", L, "build_character_prompt; character_memory_v12.json", "Injects a mutable name-to-description memory into every prompt.", ["memory JSON"], ["character prompt text"], ["prompt growth"], 0, [], ["character_memory_v12.json"], "voice and persona continuity", "persist across chunks", "reuse learned descriptions", ("medium", "high: unverified traits can contaminate later output", "medium", "high: unbounded mutation"), "core/intelligence/character_memory.py", "no evidence/confidence/version/expiry governance"),
    legacy("dynamic_character_extraction", L, "update_character_memory_via_ai", "Calls OpenRouter after each successful chunk and merges AI-generated character descriptions.", ["source chunk", "translation", "current memory"], ["mutated memory"], ["network call", "in-place append"], "0 or 1 per successful chunk", ["character_memory_v12.json"], ["character_memory_v12.json"], "learn character traits", "carry inferred state forward", "automatic extraction", ("high: credential header", "high: inference treated as fact", "high: extra provider request per chunk", "high: append-only drift"), "character intelligence primitives", "no evidence-bound approved inference pipeline"),
    legacy("character_voice_memory", L, "build_character_prompt", "Uses personality and speaking-style descriptions as hard prompt rules.", ["character memory"], ["voice constraints"], ["prompt token use"], 0, [], ["character_memory_v12.json"], "consistent dialogue voice", "cross-chunk continuity", "reuse context", ("low", "high if memory is wrong", "low", "medium"), "core/voice; character memory resource", "needs evidence and prompt eligibility gates"),
    legacy("previous_translation_context", L, "build_context_prompt; previous_translation[-CONTEXT_LENGTH:]", "Adds the final 500 characters of the previous translation to the next prompt.", ["previous translation"], ["context prompt"], ["prompt token use"], 0, [], ["translate_progress_v12.json"], "subject, tone and dialogue continuity", "chunk-to-chunk continuity", "fixed bounded tail", ("low", "medium: arbitrary truncation", "low", "medium: stores translated text"), "core/adaptive_context; RuntimeContext.previous_chunk_tail", "fixed tail lacks ranking, evidence and semantic boundaries"),
    legacy("scene_memory", L, "previous_translation; current_memory", "Carries scene cues indirectly through the prior tail and mutable character descriptions.", ["last translation", "memory"], ["implicit scene context"], ["prompt growth"], 0, [], ["translate_progress_v12.json", "character_memory_v12.json"], "scene continuity", "long-form stability", "reuse prior state", ("low", "medium", "low", "medium"), "core/context/scene_state.py", "no explicit scene evidence or expiry"),
    legacy("narrative_memory", L, "build_context_prompt", "Uses only a recent translated tail as narrative memory.", ["previous translation"], ["prompt tail"], ["prompt growth"], 0, [], ["translate_progress_v12.json"], "narrative continuity", "reduce context loss", "constant-size tail", ("low", "medium", "low", "medium"), "core/intelligence/narrative_*; core/adaptive_context", "not structured or evidence-ranked"),
    legacy("chunk_splitting", R + "; " + L, "split_text", "Splits by paragraphs or nearby separators with fixed character thresholds.", ["source text", "max chars"], ["ordered chunks"], [], 0, [], [], "preserve usable boundaries", "bounded requests", "limit prompt size", ("low", "medium: character count is not token count", "medium", "low"), "core/translation_runtime/runtime_chunk.py", "legacy split has no stable content identity"),
    legacy("chunk_cache", R, "{name}_chunk_{index}.tmp", "Persists each completed translation in a temp file and skips any existing file.", ["translated chunk", "index"], ["cache file"], ["disk write", "existence-based cache hit"], 0, ["暫存區/*_chunk_N.tmp"], ["progress.json"], "retain completed translations", "rerun only missing chunks", "avoid provider calls", ("low", "high: stale cache accepted", "medium", "high: no source/prompt/provider hash"), "resume journal and collector", "no content-addressed V2 cache metadata"),
    legacy("resume_recovery", R + "; " + L, "load_progress; save_progress; translate_progress_v12.json", "Stores current chunk/file and resumes later.", ["file", "chunk index", "status"], ["progress JSON"], ["disk write"], 0, ["progress.json", "translate_progress_v12.json"], ["progress.json", "translate_progress_v12.json"], "avoid lost work", "resume after failure", "skip completed work", ("low", "low", "medium", "medium: weak atomicity/schema"), "runtime checkpoint; scheduler ResumeJournal", "current system is stronger; legacy schema not needed"),
    legacy("realtime_output_assembly", R, "realtime_compile", "Rebuilds output in numeric chunk order after each success.", ["chunk temp files"], ["combined UTF-8 text"], ["delete and rewrite output"], 0, ["繁體中文/*.txt"], ["chunk temp files"], "continuous visible output", "recover from partial work", "incremental assembly", ("low", "medium: missing chunks silently omitted", "medium: O(n) rewrite per chunk", "medium"), "runtime_output; TranslationCollector", "current ordered collector is safer"),
    legacy("glossary_enforcement", R + "; " + L, "GLOSSARY; system_prompt", "Embeds a fixed Korean-to-Traditional-Chinese glossary as hard instructions.", ["hard-coded glossary"], ["prompt rules"], ["prompt tokens"], 0, [], [], "name consistency", "repeatable terminology", "no lookup cost", ("low", "medium: domain hard-coded", "low", "medium"), "core/glossary.py; glossary selector", "legacy data is title-specific and ungovened"),
    legacy("unknown_name_handling", R, "translate_chunk_with_retry system_prompt rule 2", "Asks the model to auto-transliterate every unlisted Korean proper noun.", ["unlisted Korean token"], ["invented Traditional-Chinese name"], ["implicit glossary mutation in output"], 0, [], [], "avoid untranslated names", "avoid Korean residue", "single-request handling", ("low", "high: common nouns and partial names can be misclassified", "low", "high: inconsistent spellings"), "glossary and character resolver", "requires language profile and human/evidence governance"),
    legacy("provider_fallback", L, "engine three-defense flow", "Falls back from NVIDIA to degraded NVIDIA and then OpenRouter.", ["prompt", "two keys"], ["translation or failure"], ["multiple network requests", "quality-contract changes"], "up to 3 paths plus internal retries", [], [], "obtain some output", "provider availability", "continue after failures", ("high", "high: fallback changes style contract", "high", "medium"), "core/ai_provider", "must remain controlled and observable"),
    legacy("multi_provider_routing", L, "call_nvidia_api; call_gemini_api", "Hard-coded NVIDIA and OpenRouter routing without shared policy evidence.", ["keys", "prompt"], ["provider response"], ["network calls"], "variable", [], [], "provider diversity", "availability", "fallback", ("high", "high: inconsistent provider outputs", "high", "medium"), "core/ai_provider/router.py", "legacy routing bypasses current policy/security"),
    legacy("dual_model_workflow", R, "system_prompt steps 1-3", "Describes draft, editorial review and polish inside one provider request; it is not an observable dual-model workflow.", ["source chunk"], ["final text only"], ["opaque internal reasoning instruction"], 1, [], [], "draft plus polish", "single request", "one call", ("low", "high: no stage evidence", "low", "low"), "Stage 11 quality framework", "no separately observable draft/polish artifacts"),
    legacy("draft_translation", R, "精準初翻 instruction", "Draft is an internal prompt instruction and is never materialized.", ["source"], ["final response only"], [], 1, [], [], "complete first translation", "none", "single request", ("low", "medium", "low", "low"), "translation runtime", "no draft artifact or draft verification"),
    legacy("polish_workflow", R, "主編審查; 終極潤飾與修正", "Review and polish are internal prompt instructions with no gate or rollback.", ["implicit draft"], ["final response only"], [], 1, [], [], "natural literary prose", "none", "single request", ("low", "high: semantic drift is invisible", "low", "low"), "naturalness and quality framework", "needs selective gate and post-polish semantic verification"),
    legacy("semantic_verification", R + "; " + L, "prompt-only completeness rules", "Relies on model instructions rather than a separate semantic comparison.", ["source", "prompt"], ["unverified translation"], [], 0, [], [], "avoid omission and invention", "none", "none", ("low", "high", "low", "low"), "translation evidence and Stage 11", "legacy has no measurable semantic verification"),
    legacy("quality_retry", L, "QUALITY_RETRY; engine success checks", "Retries/falls back based mainly on length and provider errors.", ["translation", "error"], ["retry or fallback"], ["extra provider requests"], "variable", [], [], "recover poor output", "retry after failure", "bounded retry constants", ("medium", "high: weak trigger", "high", "low"), "translation_quality_v5 quality retry", "legacy trigger is not defect evidence"),
    legacy("basic_output_validation", L, "check_translation_basic", "Rejects blank/very short output and a few explanation phrases; engine also uses len > 100.", ["translation text"], ["boolean and reason"], [], 0, [], [], "basic output sanity", "stop obvious failures", "cheap local check", ("low", "high: misses subject shift, omission, additions, repetition, name and lexical errors", "low", "low"), "runtime QA; TIC offline gate", "length-only QA has no semantic coverage"),
    legacy("encoding_detection", R, "read_txt_with_auto_encoding", "Tries UTF-8 BOM, UTF-8, CP949 and EUC-KR in order.", ["text path"], ["decoded text"], ["file read"], 0, [], [], "read Korean sources", "avoid decode failure", "bounded local attempts", ("low", "low", "low", "medium: no confidence/report"), "core/translation_runtime/runtime_encoding.py", "current implementation should remain authoritative"),
    legacy("gui_workflow", L, "App", "Tkinter UI selects folders, accepts keys, starts a worker thread and supports pause.", ["folders", "credentials", "button actions"], ["logs", "files"], ["thread", "disk/network via engine"], "delegated", ["config_v12.json"], ["config_v12.json"], "accessible workflow", "manual control", "desktop interaction", ("high: key entry/persistence risk", "low", "high: direct engine coupling", "medium"), "current CLI/GUI layers", "legacy GUI cannot bypass frozen runtime/security"),
    legacy("batch_processing", R + "; " + L, "main; engine", "Sorts input text files and processes chunks sequentially.", ["input folder"], ["translated files"], ["file enumeration", "network", "disk"], "per chunk", ["output files", "progress"], ["progress JSON"], "translate multiple files", "skip completed files", "sequential bounded work", ("medium", "medium", "medium", "medium"), "lts/batch_translation_runtime.py", "current batch runtime is authoritative"),
    legacy("pause_resume", L, "pause_flag; App.toggle_pause", "In-memory pause flag plus persisted file/chunk cursor.", ["UI action", "progress"], ["paused/resumed worker"], ["shared mutable flag", "sleep loop"], 0, ["translate_progress_v12.json"], ["translate_progress_v12.json"], "operator control", "resume long runs", "avoid restart", ("low", "low", "medium: process-local flag", "medium"), "runtime checkpoints and scheduler journal", "UI pause should merge only through current runtime contracts"),
    legacy("configuration_persistence", L, "config_v12.json; load_json; save_json", "Persists folders and user settings in a local JSON file.", ["GUI config"], ["config JSON"], ["disk write"], 0, ["config_v12.json"], ["config_v12.json"], "reusable setup", "restart continuity", "avoid re-entry", ("high if credentials are persisted", "low", "medium", "medium"), "current config/resources", "must explicitly exclude credentials"),
    legacy("academic_degraded_fallback", L, "degraded_prompt; second defense", "Switches failed novel translation to neutral academic literal translation.", ["source chunk"], ["style-degraded translation"], ["extra provider request", "quality contract change"], "1 or more", [], [], "obtain output despite refusal/error", "fallback", "continue processing", ("medium", "critical: destroys literary voice", "high", "medium"), "none", "conflicts with literary quality contract"),
    legacy("embedded_provider_credentials", R, "NVIDIA_API_KEY; OpenAI(api_key=...)", "Places provider credential configuration directly in a legacy source file.", ["plaintext credential"], ["authenticated client"], ["credential exposure"], 0, [], [], "convenience", "direct execution", "none", ("critical", "low", "high", "critical"), "core/ai_provider/credentials.py", "legacy credential pattern is forbidden"),
]


DECISION_BY_ID = {
    "character_memory": "REIMPLEMENT_FROM_CONCEPT", "dynamic_character_extraction": "REIMPLEMENT_FROM_CONCEPT", "character_voice_memory": "MERGE_WITH_CURRENT",
    "previous_translation_context": "MERGE_WITH_CURRENT", "scene_memory": "MERGE_WITH_CURRENT", "narrative_memory": "MERGE_WITH_CURRENT",
    "chunk_splitting": "KEEP_CURRENT", "chunk_cache": "REIMPLEMENT_FROM_CONCEPT", "resume_recovery": "KEEP_CURRENT", "realtime_output_assembly": "KEEP_CURRENT",
    "glossary_enforcement": "KEEP_CURRENT", "unknown_name_handling": "DROP_UNSAFE", "provider_fallback": "EXPERIMENT_ONLY", "multi_provider_routing": "EXPERIMENT_ONLY",
    "dual_model_workflow": "REIMPLEMENT_FROM_CONCEPT", "draft_translation": "REIMPLEMENT_FROM_CONCEPT", "polish_workflow": "REIMPLEMENT_FROM_CONCEPT",
    "semantic_verification": "KEEP_CURRENT", "quality_retry": "KEEP_CURRENT", "basic_output_validation": "DROP_UNSAFE", "encoding_detection": "KEEP_CURRENT",
    "gui_workflow": "EXPERIMENT_ONLY", "batch_processing": "KEEP_CURRENT", "pause_resume": "MERGE_WITH_CURRENT", "configuration_persistence": "MERGE_WITH_CURRENT",
    "academic_degraded_fallback": "DROP_UNSAFE", "embedded_provider_credentials": "LICENSE_OR_SECURITY_BLOCKED",
}


def decision_rows() -> list[dict[str, object]]:
    rows = []
    for item in LEGACY:
        cid = str(item["capability_id"])
        decision = DECISION_BY_ID[cid]
        rows.append({
            "capability": cid, "legacy_value": item["quality_intent"], "current_ntpe_status": item["current_ntpe_equivalent"], "decision": decision,
            "reason": item["feature_gap"] if decision != "KEEP_CURRENT" else "Current NTPE already provides the safer tested equivalent; do not restore legacy implementation.",
            "quality_impact": "direct" if decision in {"MERGE_WITH_CURRENT", "REIMPLEMENT_FROM_CONCEPT"} else ("preserve current" if decision == "KEEP_CURRENT" else "risk containment"),
            "timeout_impact": "must pass bounded timeout gate" if decision in {"EXPERIMENT_ONLY", "REIMPLEMENT_FROM_CONCEPT"} else "no new provider work",
            "performance_impact": "benchmark required before activation" if decision in {"EXPERIMENT_ONLY", "REIMPLEMENT_FROM_CONCEPT", "MERGE_WITH_CURRENT"} else "none",
            "prompt_token_impact": "budget required" if cid in {"character_memory", "character_voice_memory", "previous_translation_context", "scene_memory", "narrative_memory"} else "none or unchanged",
            "provider_request_impact": "may add requests; default forbidden" if cid in {"dynamic_character_extraction", "provider_fallback", "multi_provider_routing", "dual_model_workflow", "polish_workflow"} else "0 added in Batch 1",
            "implementation_priority": "P1" if cid == "character_memory" else ("P2" if cid in {"dynamic_character_extraction", "previous_translation_context", "chunk_cache"} else "P3"),
            "dependencies": ["LCR Batch 1 freeze", "offline evidence"] + (["Character Memory V2"] if cid != "character_memory" and cid in {"dynamic_character_extraction", "character_voice_memory", "scene_memory"} else []),
            "tests_required": ["schema", "boundary", "quality regression", "performance/timeout gate"],
            "rollback_strategy": "disabled-by-default artifact rollback; preserve current NTPE path",
        })
    return rows


CHARACTER_V2 = {
    "status": "design_only", "implemented": False, "production_connected": False,
    "record_schema": ["character_id", "canonical_name", "aliases", "language", "speech_style", "personality_traits", "relationships", "current_emotion", "scene_state", "evidence", "confidence", "source_case_id", "source_offsets", "status", "version", "created_at", "updated_at", "expires_at", "human_approved", "prompt_eligible"],
    "evidence_types": {"observed_fact": "direct bounded source evidence", "ai_inference": "separate, never promoted automatically"},
    "rules": {"low_confidence_prompt_eligible": False, "human_approval_separate": True, "automatic_inference_separate": True, "unbounded_append": False, "compression": True, "deduplication": True, "token_budget_required": True, "rollback_required": True, "expiry_required_for_scene_state": True},
    "admission": {"minimum_confidence": 0.85, "requires_evidence": True, "requires_human_approval_for_personality": True, "prompt_budget_tokens": 256, "overflow": "rank, compress, then omit"},
    "quality_value": "evidence-backed voice/persona continuity without treating AI guesses as facts",
}

CHUNK_V2 = {
    "status": "design_only", "implemented": False, "production_connected": False,
    "record_schema": ["chunk_id", "source_sha256", "prompt_sha256", "provider", "model", "attempt", "status", "translation_sha256", "quality_status", "created_at", "completed_at", "resume_eligible"],
    "cache_hit": "exact source_sha256 + prompt_sha256 + provider + model + accepted quality_status + completed status",
    "invalidation": ["source hash change", "prompt hash change", "provider/model contract change", "quality policy version change"],
    "partial_output_completed": False, "timeout_behavior": "mark failed/timeout and retry only that chunk under existing retry budget",
    "assembly": "existing collector orders immutable chunk_id sequence and refuses gaps/duplicates",
    "duplicate_prevention": "atomic compare-and-set on chunk identity and attempt; idempotent collector write",
    "resume_integration": "store cache reference in existing ResumeJournal/checkpoint; do not create a second runtime",
    "quality_value": "reduce repeated provider cost while refusing stale or unverified translations",
}

DUAL_PASS = {
    "status": "design_only", "implemented": False, "production_connected": False,
    "shared_configuration": ["draft_provider", "draft_model", "polish_provider", "polish_model", "same_model_allowed", "provider_requests", "timeout_budget", "retry_policy", "fallback_policy", "quality_gate", "semantic_rollback"],
    "modes": {
        "single_pass": {"flow": ["Source", "Draft", "Semantic/Quality Verification", "Output"], "provider_requests": 1, "semantic_rollback": "reject output on blocking verification"},
        "dual_pass": {"flow": ["Source", "Draft Model", "Draft Verification", "Polish Model", "Post-polish Semantic Verification", "Output"], "provider_requests": 2, "semantic_rollback": "return verified draft if polish changes meaning"},
        "selective_polish": {"flow": ["Source", "Draft", "Quality assessment", "Polish only for naturalness/literary deficit", "Semantic Verification", "Output"], "provider_requests": "1 normally; 2 only when admitted", "semantic_rollback": "return verified draft"},
    },
    "defaults": {"same_model_allowed": True, "retry_policy": "no cross-stage retry amplification", "fallback_policy": "no style-degraded fallback", "quality_gate": "offline-first and explicit admission", "timeout_budget": "single bounded session budget"},
    "legacy_finding": "Legacy prompt described three internal steps but produced one opaque response; it was not a true dual pass.",
}

LANGUAGE_PROFILES = {
    "ko": ["omitted subjects and relationship inference", "Hangul name/ordinary-noun ambiguity", "speech level and honorifics"],
    "ja": ["omitted subjects", "keigo and register", "katakana proper-name policy"],
    "en": ["pronoun chains", "tense/aspect", "idiom and phrasal meaning"],
    "target": "zh-Hant",
    "shared_runtime_boundary": "Runtime/cache/resume/output remain language-agnostic; linguistic inference and name policies require versioned source-language profiles.",
}


def multilingual_rows() -> list[dict[str, object]]:
    ko_specific = {"unknown_name_handling", "glossary_enforcement"}
    reusable = {"character_memory", "character_voice_memory", "previous_translation_context", "scene_memory", "narrative_memory", "semantic_verification", "polish_workflow"}
    rows = []
    for item in LEGACY:
        cid = str(item["capability_id"])
        rows.append({
            "capability": cid,
            "language_agnostic": cid not in ko_specific and cid not in reusable,
            "ko_specific": cid in ko_specific,
            "ja_reusable": cid in reusable,
            "en_reusable": cid in reusable,
            "requires_language_profile": cid in ko_specific or cid in reusable,
            "zh_hant_target": True,
            "impact": "Use shared runtime mechanics but source-language-specific evidence/name/register rules." if cid in ko_specific or cid in reusable else "No language-specific runtime fork required.",
        })
    return rows


ROADMAP = [
    (2, "Character Memory V2", "Evidence-governed character/voice continuity", "token budget and local lookup benchmark", "network requests=0 in design and offline tests", "current regressions plus false-persona cases", "design/isolated module only; no prompt/runtime hookup"),
    (3, "Context/Scene Memory Integration", "merge approved character and scene evidence with Adaptive Context", "bounded context tokens", "no provider request increase", "ko/ja/en context regressions", "disabled integration adapter only"),
    (4, "Chunk Cache V2", "avoid retranslation of verified identical chunks", "cache lookup/write benchmark", "retry only failed chunk", "resume/output ordering and stale-cache rejection", "reuse current ResumeJournal and collector"),
    (5, "Dual-pass Draft/Polish Prototype", "observable draft and selective polish", "single vs selective vs dual benchmark", "hard session budget", "semantic rollback corpus", "offline/mock prototype only"),
    (6, "Post-polish Semantic Verification", "prevent polish omissions/additions", "local/offline gate cost", "no automatic provider retry", "TIC semantic defects", "no production activation"),
    (7, "Multilingual Profiles", "ko/ja/en-specific continuity and names", "profile token/latency budgets", "no routing changes", "language-specific golden cases", "profile data only"),
    (8, "Controlled Provider Routing", "evaluate availability without silent quality change", "routing benchmark", "bounded attempts and timeout", "provider consistency/secret safety", "explicit authorization; disabled by default"),
    (9, "Offline Golden/TIC Validation", "prove direct quality value", "offline evaluation budget", "network requests=0", "active regression and human-reviewed goldens", "offline only"),
    (10, "Production Integration", "only evidence-proven capabilities", "production latency gate", "bounded provider budget", "full freeze ladder and rollback drill", "separate explicit authorization required"),
]


def roadmap_rows() -> list[dict[str, object]]:
    return [{"batch": f"LCR Batch {n}", "scope": name, "direct_quality_value": q, "performance_gate": p, "timeout_gate": t, "regression_gate": r, "production_boundary": b} for n, name, q, p, t, r, b in ROADMAP]


def matrix_md(rows: list[dict[str, object]]) -> str:
    lines = ["# LCR Capability Decision Matrix", "", "Batch 1 is audit/design only. No legacy code is integrated.", "", "| Capability | Decision | Reason |", "|---|---|---|"]
    lines += [f"| {r['capability']} | {r['decision']} | {str(r['reason']).replace('|', '/')} |" for r in rows]
    return "\n".join(lines)


def design_md(title: str, payload: dict[str, object], bullets: list[str]) -> str:
    return "\n".join([f"# {title}", "", "Status: design-only; not implemented or production-connected.", ""] + [f"- {item}" for item in bullets] + ["", "Canonical machine-readable design: companion JSON file."])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    matrix = decision_rows()
    multilingual = {"profiles": LANGUAGE_PROFILES, "capabilities": multilingual_rows()}
    roadmap = roadmap_rows()
    security = {
        "credential_exposure_detected": True,
        "plaintext_api_key_detected": True,
        "affected_source": "user-provided translate_realtime_v2.txt: NVIDIA_API_KEY assignment",
        "redacted_copy_created": True,
        "redacted_copy": "audits/legacy_capability_recovery/source_material/translate_realtime_v2_legacy.txt",
        "key_value_saved": False, "key_tested": False, "rotation_recommended": True,
        "authorization_header_saved": False, "provider_response_saved": False,
        "recommendation": "Rotate/revoke the exposed NVIDIA credential and use the current credential manager; do not reuse the legacy file.",
    }
    boundaries = {
        "provider_executed": False, "network_requests": 0, "new_translation_generated": False,
        "production_code_modified": False, "runtime_modified": False, "provider_modified": False, "prompt_modified": False, "qa_engine_modified": False, "tic_modified": False,
        "legacy_source_code_integrated": False, "legacy_concepts_audited": True, "legacy_secrets_redacted": True,
        "character_memory_v2_implemented": False, "chunk_cache_v2_implemented": False, "dual_pass_implemented": False, "multilingual_profiles_implemented": False,
        "lcr_batch2_started": False,
    }
    hashes = baseline_hashes()
    audit = {
        "batch": "LCR Batch 1", "title": "Legacy Capability Recovery Audit and Recovery Plan", "status": "complete",
        "legacy_capability_count": len(LEGACY), "current_capability_count": len(CURRENT_MAP),
        "decision_counts": {d: sum(1 for row in matrix if row["decision"] == d) for d in sorted(DECISIONS)},
        "source_material": [
            {"review_copy": "audits/legacy_capability_recovery/source_material/v12_dynamic_memory_legacy.txt", "original_modified": False, "executable": False, "finding": "historical text has missing syntax punctuation and is evidence only"},
            {"review_copy": "audits/legacy_capability_recovery/source_material/translate_realtime_v2_legacy.txt", "original_modified": False, "credential_redacted": True},
        ],
        "baseline_hashes": hashes, "security": security, "boundaries": boundaries,
        "next_batch": "LCR Batch 2 — Character Memory V2 only; not started",
    }
    write_json("CURRENT_NTPE_CAPABILITY_MAP.json", CURRENT_MAP)
    write_json("LEGACY_CAPABILITY_INVENTORY.json", LEGACY)
    write_json("MULTILINGUAL_RECOVERY_IMPACT.json", multilingual)
    write_json("LCR_CAPABILITY_DECISION_MATRIX.json", matrix)
    write_text("LCR_CAPABILITY_DECISION_MATRIX.md", matrix_md(matrix))
    write_json("CHARACTER_MEMORY_V2_DESIGN.json", CHARACTER_V2)
    write_text("CHARACTER_MEMORY_V2_DESIGN.md", design_md("Character Memory V2 Design", CHARACTER_V2, ["Observed facts and AI inferences are separate records.", "Low-confidence or non-approved traits are not prompt-eligible.", "Evidence offsets, confidence, version, expiry, deduplication, compression, token budget and rollback are mandatory.", "No current Character Memory or Prompt code is modified in Batch 1."]))
    write_json("CHUNK_CACHE_V2_DESIGN.json", CHUNK_V2)
    write_text("CHUNK_CACHE_V2_DESIGN.md", design_md("Chunk Cache V2 Design", CHUNK_V2, ["Cache hits require exact source/prompt/provider/model identity and accepted quality status.", "Partial and timed-out output is never completed; retry only the failed chunk.", "Assembly refuses gaps and duplicates and preserves current collector ordering.", "ResumeJournal stores references; there is no second runtime."]))
    write_json("DUAL_PASS_RECOVERY_DESIGN.json", DUAL_PASS)
    write_text("DUAL_PASS_RECOVERY_DESIGN.md", design_md("Dual-pass Recovery Design", DUAL_PASS, ["Single-pass, dual-pass and selective-polish flows are separately observable.", "Selective polish is preferred when only naturalness/literary quality is deficient.", "Post-polish semantic verification rolls back to the verified draft.", "Provider requests and a single bounded timeout budget are explicit; no provider/runtime changes occur in Batch 1."]))
    write_json("LCR_IMPLEMENTATION_ROADMAP.json", roadmap)
    write_text("LCR_IMPLEMENTATION_ROADMAP.md", "# LCR Implementation Roadmap\n\n" + "\n".join(f"## {r['batch']} — {r['scope']}\n\n- Direct quality value: {r['direct_quality_value']}\n- Performance gate: {r['performance_gate']}\n- Timeout gate: {r['timeout_gate']}\n- Regression gate: {r['regression_gate']}\n- Production boundary: {r['production_boundary']}\n" for r in roadmap) + "\nBatch 1 implements none of these. The first implementation batch is Character Memory V2 only.")
    write_json("SECURITY_FINDINGS.json", security)
    write_json("LCR_BATCH1_AUDIT.json", audit)
    write_text("LCR_BATCH1_AUDIT.md", "\n".join([
        "# LCR Batch 1 — Legacy Capability Recovery Audit", "", "Status: COMPLETE (audit/design only).", "",
        f"Legacy capabilities inventoried: {len(LEGACY)}.", "",
        "## Findings", "",
        "- Legacy dynamic character extraction adds unverified AI traits to an append-only memory and can pollute later prompts.",
        "- The fixed previous-translation tail has continuity value but should merge into Adaptive Context, not become a parallel context engine.",
        "- Temp chunk files reduce reruns but accept stale output by existence alone; Chunk Cache V2 requires content and policy hashes.",
        "- Legacy three-step draft/review/polish is one opaque request, not a true dual pass.",
        "- Academic degraded fallback and automatic unknown-name transliteration violate the current literary/evidence quality contract.",
        "- Current Resume/Recovery, chunking, assembly, glossary, semantic verification, quality retry, encoding and batch flow remain authoritative.", "",
        "## Security", "", "Credential exposure was detected in the supplied legacy source. The review copy is redacted; the value was not tested or stored. Rotate/revoke the credential.", "",
        "## Boundary", "", "Provider executed: false; network requests: 0; new translation generated: false. Production, Runtime, Provider, Prompt, QA Engine and TIC are unchanged. LCR Batch 2 was not started.",
    ]))
    write_text("VALIDATION_REPORT.txt", "LCR Batch 1 artifacts generated.\nFinal test, regression, git, secret-scan, and package results are appended only after validation.\nprovider_executed=false\nnetwork_requests=0\nnew_translation_generated=false")
    print(f"generated {len(LEGACY)} legacy capabilities and {len(CURRENT_MAP)} current capabilities")


if __name__ == "__main__":
    main()
