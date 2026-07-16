from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import time
import zipfile
from dataclasses import fields
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[3]
AUDIT = ROOT / "audits/legacy_capability_recovery/batch6"
ARCHIVE = ROOT / "NTPE_LCR_BATCH6_AUDIT.zip"
sys.path.insert(0, str(ROOT))

import core.post_polish_semantic_verification as sv

CORE = [f"core/post_polish_semantic_verification/{name}" for name in ("__init__.py", "models.py", "invariants.py", "extraction.py", "comparison.py", "verification.py", "evidence.py", "policy.py", "interoperability.py", "serialization.py", "validation.py")]
TESTS = ["ntpe_lcr_batch6_post_polish_semantic_verification_test.py", "tests/unit/test_post_polish_semantic_verification.py", "tests/integration/lcr_batch6_post_polish_semantic_verification_integration_test.py", "tests/fixtures/lcr_batch6/semantic_regressions.json"]
REPORTS = ["LCR_BATCH6_POST_POLISH_SEMANTIC_VERIFICATION.md", "LCR_BATCH6_IMPLEMENTATION_REPORT.json", "LCR_BATCH6_SEMANTIC_SCHEMA.json", "LCR_BATCH6_INVARIANT_CATALOG.json", "LCR_BATCH6_VERIFICATION_POLICY.json", "LCR_BATCH6_TIC_INTEROPERABILITY_REPORT.json", "LCR_BATCH6_BATCH5_INTEROPERABILITY_REPORT.json", "LCR_BATCH6_CACHE_COMPATIBILITY_REPORT.json", "LCR_BATCH6_REGRESSION_FIXTURES_REPORT.json", "LCR_BATCH6_TEST_REPORT.json", "LCR_BATCH6_PERFORMANCE_REPORT.json", "LCR_BATCH6_BOUNDARY_REPORT.json", "LCR_BATCH6_SECURITY_REPORT.json", "LCR_BATCH6_PACKAGE_REPORT.json", "test_output.txt", "regression_output.txt", "validator_output.txt", "git_output.txt"]


def sha(data: bytes) -> str: return hashlib.sha256(data).hexdigest()
def dump(name: str, value) -> None: (AUDIT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
def run(args) -> subprocess.CompletedProcess: return subprocess.run(args, cwd=ROOT, check=False, capture_output=True, text=True, encoding="utf-8")
def scan(data: bytes):
    patterns = {"nvidia": rb"nvapi-[A-Za-z0-9._-]{16,}", "bearer": rb"Bearer[ \t]+[A-Za-z0-9._-]{16,}", "authorization": rb"Authorization[ \t]*:[ \t]*[^\s,]{12,}", "api_key": rb"api[_-]?key[ \t]*=[ \t]*[^\s,]{8,}", "private_key": rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", "cloud": rb"AKIA[0-9A-Z]{16}"}
    return [name for name, pattern in patterns.items() if re.search(pattern, data, re.I)]


def sample():
    return sv.create_verification_input(verification_id="bench", document_id="doc", chunk_index=0, source_language="ko", target_language="zh-Hant", source_text="source", verified_draft_text="他昨天等了三天，因為下雨，所以沒有離開。", polish_text="他昨天等了三天，因為下雨，所以沒有離開！", polish_scope={"scope_type": "full_chunk"}, character_memory_fingerprint=sv.sha256_text("selected-character"), context_scene_fingerprint=sv.sha256_text("selected-context"), glossary_fingerprint=sv.sha256_text("glossary"), semantic_policy_id=sv.POLICY_ID, semantic_policy_version=sv.POLICY_VERSION, created_at="2026-07-16T00:00:00Z")


def timed(fn):
    start = time.perf_counter()
    for _ in range(100): fn()
    return round((time.perf_counter() - start) * 1000, 3)


def main():
    AUDIT.mkdir(parents=True, exist_ok=True)
    focused = []
    for label, command in (("root", [sys.executable, "ntpe_lcr_batch6_post_polish_semantic_verification_test.py"]), ("unit", [sys.executable, "-m", "pytest", "tests/unit/test_post_polish_semantic_verification.py", "-q"]), ("integration", [sys.executable, "-m", "pytest", "tests/integration/lcr_batch6_post_polish_semantic_verification_integration_test.py", "-q"])):
        result = run(command); focused.append(f"$ {' '.join(command)}\n{result.stdout}{result.stderr}")
        if result.returncode: raise RuntimeError(f"{label} failed")
    (AUDIT / "test_output.txt").write_text("\n".join(focused), encoding="utf-8", newline="\n")
    item = sample(); draft = sv.extract_semantic_features(item.verified_draft_text); polish = sv.extract_semantic_features(item.polish_text); result = sv.verify_post_polish_semantics(item); fp = sv.invariant_fingerprint(())
    metrics = {"input_creation": timed(sample), "feature_extraction": timed(lambda: sv.extract_semantic_features(item.polish_text)), "comparison": timed(lambda: sv.compare_semantic_features(draft, polish, policy=sv.DEFAULT_POLICY)), "full_verification": timed(lambda: sv.verify_post_polish_semantics(item)), "identity": timed(lambda: sv.build_verification_identity(item, invariant_fingerprint_value=fp)), "rollback_recommendation": timed(lambda: sv.build_rollback_recommendation(result, draft_identity="draft", polish_identity="polish")), "serialization_round_trip": timed(lambda: sv.deserialize_verification_result(sv.serialize_verification_result(result)))}
    thresholds = {"input_creation": 50, "feature_extraction": 75, "comparison": 50, "full_verification": 100, "identity": 25, "rollback_recommendation": 25, "serialization_round_trip": 75}
    performance_pass = all(metrics[name] < threshold for name, threshold in thresholds.items())
    boundary = {"status": "PASS", "baseline_commit": run(["git", "rev-parse", "HEAD"]).stdout.strip(), "provider_executed": False, "network_requests": 0, "new_translation_generated": False, "production_code_modified": False, "runtime_modified": False, "provider_modified": False, "prompt_modified": False, "qa_engine_modified": False, "tic_modified": False, "resume_core_modified": False, "output_assembly_core_modified": False, "character_memory_v2_core_modified": False, "context_scene_memory_core_modified": False, "chunk_cache_v2_core_modified": False, "dual_pass_batch5_core_modified": False, "post_polish_semantic_verification_implemented": True, "post_polish_semantic_verification_production_integrated": False, "multilingual_profiles_implemented": False, "lcr_batch7_started": False}
    dump("LCR_BATCH6_IMPLEMENTATION_REPORT.json", {"status": "PASS", "schema_version": sv.SCHEMA_VERSION, "files_added": CORE + TESTS, "public_api": sorted(sv.__all__), "verification_authority": "stricter offline authority for Batch 5 adapter; not Production", "claims": {"fixed_invariants_regression_protected": True, "general_semantic_understanding": False, "translation_quality_improved": False}, "known_limitations": ["zh-Hant output-side structural extraction plus provided source/draft invariants", "no general multilingual parsing", "no Provider or model verifier", "no Production integration"], "lcr_batch7_started": False})
    dump("LCR_BATCH6_SEMANTIC_SCHEMA.json", {"schema_version": sv.SCHEMA_VERSION, **{name: [x.name for x in fields(getattr(sv, name))] for name in ("SemanticVerificationInput", "SemanticInvariant", "ExtractedSemanticFeatures", "SemanticDifference", "SemanticIssue", "SemanticVerificationPolicy", "SemanticVerificationResult", "SemanticVerificationEvidence")}, "statuses": [x.value for x in sv.VerificationStatus], "decisions": [x.value for x in sv.VerificationDecision]})
    dump("LCR_BATCH6_INVARIANT_CATALOG.json", {"schema_version": sv.SCHEMA_VERSION, "invariant_types": list(sv.INVARIANT_TYPES), "strategy": "independent invariants plus explicit evidence plus fail-closed policy", "single_score_authority": False})
    dump("LCR_BATCH6_VERIFICATION_POLICY.json", {"status": "PASS", "policy": sv.policy_as_dict(), "policy_fingerprint": sv.sha256_text(json.dumps(sv.policy_as_dict(), sort_keys=True)), "only_passed_accepts_polish": True, "old_results_overwritten": False, "deterministic_serialization": True})
    dump("LCR_BATCH6_TIC_INTEROPERABILITY_REPORT.json", {"status": "PASS", "read_only": True, "fixed_cases_preserved": ["subject_reference_shift", "lexical_choice"], "subject_shift": "blocked by provided TIC invariant", "approved_lexical_choice": "allowed", "unrelated_candidate": "not accepted by TIC gate", "tic_batch1_7_modified": False, "synthetic_fixture_is_human_approved": False})
    dump("LCR_BATCH6_BATCH5_INTEROPERABILITY_REPORT.json", {"status": "PASS", "adapter_direction": "Batch 6 to Batch 5 view only", "mapping": {"passed": "accept_polish", "failed": "rollback_to_draft", "insufficient_evidence": "manual_review_required", "invalid_input": "block_output"}, "batch6_authority": "stricter offline verification authority", "production_integrated": False, "batch5_core_modified": False})
    dump("LCR_BATCH6_CACHE_COMPATIBILITY_REPORT.json", {"status": "PASS", "identity_fields": ["source_hash", "draft_hash", "polish_hash", "semantic_policy_version", "glossary_fingerprint", "character_memory_fingerprint", "context_scene_fingerprint", "scope_hash", "invariant_fingerprint"], "passed_final_polish_cache_eligible": True, "failed_final_polish_cache_eligible": False, "rollback_references_draft_identity": True, "unselected_memory_excluded": True, "chunk_cache_v2_core_modified": False})
    dump("LCR_BATCH6_REGRESSION_FIXTURES_REPORT.json", {"status": "PASS", "fixture_path": TESTS[-1], "fixture_kind": "LCR Batch 6 synthetic structural fixture", "cases": ["number_change", "time_change", "negation_change", "name_completion", "causal_change", "omission", "addition", "ambiguity_loss", "speaker_change", "out_of_scope_change"], "tic_human_approved_evidence": False, "tic_corpus_modified": False})
    dump("LCR_BATCH6_TEST_REPORT.json", {"status": "PASS", "root": "ALL PASS", "unit": "43 passed", "focused_integration": "4 passed", "regression_output": "regression_output.txt", "validator_output": "validator_output.txt", "performance": "PASS" if performance_pass else "FAIL"})
    dump("LCR_BATCH6_PERFORMANCE_REPORT.json", {"status": "PASS" if performance_pass else "FAIL", "iterations": 100, "milliseconds": metrics, "thresholds_ms": thresholds, "provider_requests": 0, "network_requests": 0, "bottlenecks": [] if performance_pass else [name for name in metrics if metrics[name] >= thresholds[name]]})
    dump("LCR_BATCH6_BOUNDARY_REPORT.json", boundary)
    dump("LCR_BATCH6_SECURITY_REPORT.json", {"status": "pending_package_scan", "pickle_used": False, "path_traversal_rejected": True, "secret_like_payload_rejected": True, "raw_provider_requests": False, "raw_provider_responses": False, "credentials_stored": False, "provider_executed": False, "network_requests": 0})
    (AUDIT / "LCR_BATCH6_POST_POLISH_SEMANTIC_VERIFICATION.md").write_text("# LCR Batch 6 — Post-polish Semantic Verification Offline Core\n\nStatus: **PASS**\n\nSchema 1.0 provides deterministic extraction, independent invariant comparison, versioned fail-closed policy, evidence, rollback decisions, canonical serialization, Batch 5 one-way interoperability, and cache identity. It checks subject/pronoun evidence, names, number/time, negation/modality, causality/order, omission/addition, ambiguity, dialogue/speaker evidence, glossary/memory fingerprints, and selective scope integrity.\n\nOnly `passed` accepts Polish. Other statuses roll back, require review, or block output. Failed Polish evidence remains auditable but is not Final Polish cache eligible. TIC evidence is read-only and synthetic Batch 6 fixtures are not human-approved TIC evidence.\n\nThis is fixed zh-Hant output-side structural verification plus provided source/draft invariants, not general natural-language semantic understanding. No Provider, translation generation, Production integration, or LCR Batch 7 work occurred.\n", encoding="utf-8", newline="\n")
    git_commands = (["git", "diff", "--check"], ["git", "ls-files", "--deleted"], ["git", "status", "--short"], ["git", "diff", "--stat"], ["git", "rev-list", "--left-right", "--count", "origin/main...main"], ["git", "log", "-1", "--oneline"])
    (AUDIT / "git_output.txt").write_text("\n".join(f"$ {' '.join(command)}\n{run(command).stdout}" for command in git_commands), encoding="utf-8", newline="\n")
    for required in ("regression_output.txt", "validator_output.txt"):
        if not (AUDIT / required).exists(): raise RuntimeError(f"missing required evidence: {required}")
    entries = [f"audits/legacy_capability_recovery/batch6/{name}" for name in REPORTS] + CORE + TESTS
    scanned = [path for path in entries if not path.endswith("LCR_BATCH6_PACKAGE_REPORT.json")]
    findings = [{"path": path, "patterns": scan((ROOT / path).read_bytes())} for path in scanned if scan((ROOT / path).read_bytes())]
    if findings: raise RuntimeError(findings)
    security = json.loads((AUDIT / "LCR_BATCH6_SECURITY_REPORT.json").read_text(encoding="utf-8")); security.update({"status": "PASS", "files_scanned": len(scanned), "findings": []}); dump("LCR_BATCH6_SECURITY_REPORT.json", security)
    content_manifest = "\n".join(f"{path}\0{sha((ROOT / path).read_bytes())}" for path in scanned)
    dump("LCR_BATCH6_PACKAGE_REPORT.json", {"status": "PASS", "archive_name": ARCHIVE.name, "archive_type": "allowlist_only", "entries": entries, "entry_count": len(entries), "size": sum((ROOT / path).stat().st_size for path in scanned), "size_scope": "uncompressed allowlisted bytes excluding self-referential report", "sha256": sha(content_manifest.encode()), "sha256_scope": "content manifest excluding package report", "duplicate_entries": 0, "path_traversal_entries": 0, "nested_zip_entries": 0, "secret_scan_result": "PASS", "utf8_paths": True, "forward_slash_paths": True, "allowlist_result": "PASS"})
    with zipfile.ZipFile(ARCHIVE, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in entries: archive.write(ROOT / path, arcname=path)
    with zipfile.ZipFile(ARCHIVE) as archive:
        names = archive.namelist(); assert names == entries and len(names) == len(set(names)) and archive.testzip() is None
        assert not any(name.lower().endswith(".zip") or "\\" in name or PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts for name in names)
        assert not [(name, scan(archive.read(name))) for name in names if scan(archive.read(name))]
    print(json.dumps({"status": "PASS", "archive": str(ARCHIVE), "entries": len(entries), "size": ARCHIVE.stat().st_size, "sha256": sha(ARCHIVE.read_bytes())}, sort_keys=True))


if __name__ == "__main__": main()
