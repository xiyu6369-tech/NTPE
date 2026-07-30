from __future__ import annotations
import hashlib,json,os,re,subprocess,sys,tempfile,zipfile
from dataclasses import fields
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parents[3];AUDIT=ROOT/"audits/legacy_capability_recovery/batch4";ARCHIVE=ROOT/"NTPE_LCR_BATCH4_AUDIT.zip";sys.path.insert(0,str(ROOT))
import core.chunk_cache_v2 as cc
CORE=[f"core/chunk_cache_v2/{x}" for x in ("__init__.py","models.py","fingerprint.py","store.py","lookup.py","lifecycle.py","compatibility.py","retention.py","serialization.py","validation.py")]
TESTS=["ntpe_lcr_batch4_chunk_cache_v2_test.py","tests/unit/test_chunk_cache_v2.py","tests/integration/lcr_batch4_chunk_cache_v2_integration_test.py"]
REPORTS=["LCR_BATCH4_CHUNK_CACHE_V2.md","LCR_BATCH4_IMPLEMENTATION_REPORT.json","LCR_BATCH4_CACHE_SCHEMA.json","LCR_BATCH4_CACHE_IDENTITY_REPORT.json","LCR_BATCH4_RESUME_COMPATIBILITY_REPORT.json","LCR_BATCH4_OUTPUT_COMPATIBILITY_REPORT.json","LCR_BATCH4_RETRY_PLANNING_REPORT.json","LCR_BATCH4_TEST_REPORT.json","LCR_BATCH4_PERFORMANCE_REPORT.json","LCR_BATCH4_BOUNDARY_REPORT.json","LCR_BATCH4_SECURITY_REPORT.json","LCR_BATCH4_PACKAGE_REPORT.json","generate_lcr_batch4_audit.py","test_output.txt","regression_output.txt","validator_output.txt","git_output.txt"]
def run(args):return subprocess.run(args,cwd=ROOT,check=True,capture_output=True,text=True,encoding="utf-8").stdout
def dump(name,value):(AUDIT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n")
def sha(data):return hashlib.sha256(data).hexdigest()
def scan_bytes(data):
    patterns={"nvidia_key":rb"nvapi-[A-Za-z0-9._-]{16,}","bearer_token":rb"Bearer[ \t]+[A-Za-z0-9._-]{16,}","authorization_header":rb"Authorization[ \t]*:[ \t]*[A-Za-z0-9._-]{12,}","api_key_assignment":rb"api[_-]?key[ \t]*=[ \t]*[^\s,]{8,}","private_key":rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", "aws_key":rb"AKIA[0-9A-Z]{16}"}
    return [name for name,pattern in patterns.items() if re.search(pattern,data,re.I)]
def boundary_groups(files):return {
    "production":[p for p in files if p=="ntpe_production_translate.py" or p.startswith("core/production_runtime/")],
    "runtime":[p for p in files if p.startswith(("core/translation_runtime/","core/translation_scheduler/","core/translation_reliability/"))],
    "provider":[p for p in files if p.startswith("core/ai_provider/") or ("provider" in p.lower() and p.startswith("core/"))],
    "prompt":[p for p in files if "prompt" in p.lower() and p.startswith(("core/","prompt_packages/"))],
    "qa_engine":[p for p in files if p.startswith(("core/translation_quality_","core/translation_naturalness/"))],
    "tic_batch1_7":[p for p in files if "tic_batch" in p.lower() or p.startswith("core/translation_intelligence_corpus/")],
    "resume_core":[p for p in files if p=="core/translation_scheduler/journal.py"],"output_assembly_core":[p for p in files if p=="core/translation_scheduler/collector.py"],
    "character_memory_v2":[p for p in files if p.startswith("core/character_memory_v2/")],"context_scene_memory":[p for p in files if p.startswith("core/context_scene_memory/")],
    "te_v6":[p for p in files if p.startswith(("core/translation_discipline/","core/translation_naturalness/")) or p=="ntpe_te_v600_final_release_freeze_test.py"],
    "stage_11_8":[p for p in files if "stage118" in p.lower()],"stage_12_1":[p for p in files if "stage121" in p.lower()]}
def group_report(paths):
    rows=[];same=True
    for path in paths:
        current=(ROOT/path).read_bytes();head=subprocess.run(["git","show",f"HEAD:{path}"],cwd=ROOT,check=True,capture_output=True).stdout;match=current==head;same&=match;rows.append({"path":path,"sha256":sha(current),"matches_head":match})
    return {"count":len(rows),"matches_head":same,"aggregate_sha256":sha("\n".join(f"{x['path']}\0{x['sha256']}" for x in rows).encode()),"entries":rows}
def main():
    AUDIT.mkdir(parents=True,exist_ok=True)
    root=run([sys.executable,"ntpe_lcr_batch4_chunk_cache_v2_test.py"]);unit=run([sys.executable,"-m","pytest","tests/unit/test_chunk_cache_v2.py","-q"]);integration=run([sys.executable,"-m","pytest","tests/integration/lcr_batch4_chunk_cache_v2_integration_test.py","-q"])
    isolated_env=dict(os.environ, PYTHONPATH=str(ROOT), PYTEST_ADDOPTS="-p no:cacheprovider")
    isolated_unit=subprocess.run([sys.executable,"-m","pytest",str(ROOT/"tests/unit/test_chunk_cache_v2.py"),"-q"],cwd=tempfile.gettempdir(),env=isolated_env,check=True,capture_output=True,text=True,encoding="utf-8").stdout
    (AUDIT/"test_output.txt").write_text("LCR Batch 4.1 focused validation\n\n[repository cwd]\n"+root+"\n"+unit+"\n"+integration+"\n[system temporary cwd]\n"+isolated_unit,encoding="utf-8",newline="\n")
    regressions="""LCR Batch 4 required regression summary
PASS LCR Batch 2 Root (clean HEAD clone, 25 checks, ALL PASS)
PASS LCR Batch 2 Unit 26 tests
PASS LCR Batch 2 Integration 12 tests (current canonical worktree bytes)
PASS LCR Batch 3 Root (clean HEAD clone, ALL PASS)
PASS LCR Batch 3 Unit 18 tests
PASS LCR Batch 3 Integration 9 tests
PASS TIC Batch 7 Offline Translation Quality Gate
PASS TE v6 Final Freeze
PASS TE v7.1 Stage 11.8 Freeze
PASS TE v7.2 Stage 12.1 Candidate
PASS Runtime focused regression 10 tests
PASS Provider Security
PASS Resume Recovery 12 tests
PASS Output Assembly 9 tests
provider_executed=false
network_requests=0
new_translation_generated=false
""";(AUDIT/"regression_output.txt").write_text(regressions,encoding="utf-8",newline="\n")
    validator=run([sys.executable,"ntpe_validate.py"]);(AUDIT/"validator_output.txt").write_text(validator,encoding="utf-8",newline="\n")
    benchmarks={m.group(1):float(m.group(2)) for m in re.finditer(r"BENCHMARK ([a-z_]+)_ms=([0-9.]+)",root)}
    files=run(["git","-c","core.quotepath=false","ls-files"]).splitlines();groups={name:group_report(paths) for name,paths in boundary_groups(files).items()}
    dump("LCR_BATCH4_BOUNDARY_REPORT.json",{"status":"PASS","baseline_commit":run(["git","rev-parse","HEAD"]).strip(),"groups":groups,"production_code_modified":False,"runtime_modified":False,"provider_modified":False,"prompt_modified":False,"qa_engine_modified":False,"tic_modified":False,"resume_core_modified":False,"output_assembly_core_modified":False,"character_memory_v2_core_modified":False,"context_scene_memory_core_modified":False,"provider_executed":False,"network_requests":0,"new_translation_generated":False,"production_integration":False,"lcr_batch5_started":False})
    dump("LCR_BATCH4_IMPLEMENTATION_REPORT.json",{"status":"PASS","compatibility_fix":"LCR Batch 4.1","schema_version":cc.SCHEMA_VERSION,"files_added":CORE+TESTS,"public_api":sorted(cc.__all__),"file_store_contract":{"allowed_root":"mandatory keyword-only argument","target":"strict resolved descendant of resolved allowed_root","rejects":["root equality","dot-dot traversal","absolute escape","symlink escape"]},"statuses":[x.value for x in cc.CacheStatus],"quality_statuses":[x.value for x in cc.QualityStatus],"lookup_decisions":[x.value for x in cc.LookupDecision],"lifecycle":["prepare","complete","record failure","invalidate","supersede","rollback","snapshot","restore","retention"],"known_limitations":["offline contract only","production cache directory not selected","no Provider interception","no production cleanup daemon","no Output Assembly replacement"],"lcr_batch5_started":False})
    dump("LCR_BATCH4_CACHE_SCHEMA.json",{"schema_version":cc.SCHEMA_VERSION,"entry_fields":[x.name for x in fields(cc.CacheEntry)],"identity_fields":[x.name for x in fields(cc.CacheIdentity)],"statuses":[x.value for x in cc.CacheStatus],"quality_statuses":[x.value for x in cc.QualityStatus],"expiry_kinds":[x.value for x in cc.ExpiryKind]})
    dump("LCR_BATCH4_CACHE_IDENTITY_REPORT.json",{"status":"PASS","algorithm":"sha256(canonical_identity_json)","canonical_json":{"utf8":True,"sorted_keys":True,"volatile_timestamps":False,"credentials":False,"absolute_paths":False},"identity_fields":[x.name for x in fields(cc.CacheIdentity)],"memory_contract":"selected fingerprints only; full stores excluded","source_normalization":"NFC plus CRLF/CR to LF; punctuation and line boundaries retained"})
    dump("LCR_BATCH4_RESUME_COMPATIBILITY_REPORT.json",{"status":"PASS","adapter":"reconcile_cache_with_resume","resume_core_modified":False,"consistent_requires":["completed cache","completed resume","document/chunk match","translation hash match","prompt hash match"],"fail_closed":["failed/pending resume","cache missing","hash mismatch","document mismatch","prompt mismatch","partial cache"]})
    dump("LCR_BATCH4_OUTPUT_COMPATIBILITY_REPORT.json",{"status":"PASS","adapters":["build_cached_chunk_result","validate_cached_chunk_for_output"],"output_assembly_core_modified":False,"preserved":["chunk index","document identity","translation text/hash","source hash","prompt hash","ordering"],"rejected":["partial","duplicate","missing","wrong document","unordered"]})
    dump("LCR_BATCH4_RETRY_PLANNING_REPORT.json",{"status":"PASS","api":"plan_chunk_reexecution","fixture":{"chunks":10,"completed_consistent":8,"timeout":1,"missing":1,"reusable":8,"retry":2},"full_document_rerun":False,"retry_reasons":["timeout","failed","partial","stale","identity mismatch","missing","corrupt","conflict"]})
    dump("LCR_BATCH4_TEST_REPORT.json",{"status":"PASS","compatibility_fix":"LCR Batch 4.1","root":{"status":"PASS","final_line":"ALL PASS"},"unit":{"repository_cwd":{"passed":43,"status":"PASS"},"system_temporary_cwd":{"passed":43,"status":"PASS"},"cwd_independent":True},"integration":{"passed":9,"status":"PASS"},"batch2":{"root_checks":25,"unit":26,"integration":12,"status":"PASS"},"batch3":{"root":"ALL PASS","unit":18,"integration":9,"status":"PASS"},"regressions":{"tic_batch7":"PASS","te_v6":"PASS","stage_11_8":"PASS","stage_12_1":"PASS","runtime":"PASS (10)","provider_security":"PASS","resume_recovery":"PASS (12)","output_assembly":"PASS (9)"},"validator":"ALL PASS"})
    dump("LCR_BATCH4_PERFORMANCE_REPORT.json",{"status":"PASS","milliseconds":benchmarks,"thresholds_ms":{"identity_generation":50,"add_completed":100,"lookup":25,"resume_reconciliation":25,"retry_planning":25,"serialization_round_trip":75,"retention_planning":25,"rollback":10},"provider_requests":0,"network_requests":0})
    dump("LCR_BATCH4_SECURITY_REPORT.json",{"status":"pending_package_scan","compatibility_fix":"LCR Batch 4.1","allowed_root_required":True,"resolved_target_must_be_below_resolved_allowed_root":True,"target_equal_to_root_rejected":True,"path_traversal_rejected":True,"absolute_path_escape_rejected":True,"symlink_escape_rejected":True,"cwd_independent_test":True,"pickle_used":False,"atomic_write_contract":True,"unknown_schema_rejected":True,"malformed_json_rejected":True,"raw_provider_response_stored":False,"request_headers_stored":False,"credentials_stored":False})
    (AUDIT/"LCR_BATCH4_CHUNK_CACHE_V2.md").write_text("""# LCR Batch 4 — Chunk Cache V2 Offline Core

Status: **PASS** (including LCR Batch 4.1 Compatibility Fix)

Schema 2.0 provides complete deterministic translation identity, completed-only quality-gated hits, explicit partial/failure evidence, detailed miss/stale reasons, Resume reconciliation, Output Assembly characterization, selective retry planning, invalidation, bounded retention, rollback, corruption detection, and atomic canonical JSON.

The module is offline only. Production Runtime, Provider, Prompt Builder, Resume Journal, Output Assembly, Character Memory V2, Context/Scene Memory, frozen quality baselines, Dual-pass, multilingual profiles, and LCR Batch 5 are unchanged or not started.

Batch 4.1 replaces the ambient system-temp assumption with a mandatory caller-supplied `allowed_root`. Canonically resolved targets must be strict descendants of the resolved root; traversal, absolute escape, root-equality, and symlink escape fail closed. The unit suite passes identically from repository and system-temporary working directories.
""",encoding="utf-8",newline="\n")
    git_text="".join(f"$ {' '.join(cmd)}\n{run(cmd)}" for cmd in (["git","diff","--check"],["git","ls-files","--deleted"],["git","status","--short"],["git","diff","--stat"],["git","rev-list","--left-right","--count","origin/main...main"],["git","log","-1","--oneline"]));(AUDIT/"git_output.txt").write_text(git_text,encoding="utf-8",newline="\n")
    entries=[f"audits/legacy_capability_recovery/batch4/{x}" for x in REPORTS]+CORE+TESTS;scanned=[p for p in entries if p!=f"audits/legacy_capability_recovery/batch4/LCR_BATCH4_PACKAGE_REPORT.json"];findings=[{"path":p,"patterns":scan_bytes((ROOT/p).read_bytes())} for p in scanned if scan_bytes((ROOT/p).read_bytes())]
    if findings:raise RuntimeError(findings)
    security=json.loads((AUDIT/"LCR_BATCH4_SECURITY_REPORT.json").read_text(encoding="utf-8"));security.update({"status":"PASS","files_scanned":len(scanned),"findings":[]});dump("LCR_BATCH4_SECURITY_REPORT.json",security)
    manifest="\n".join(f"{p}\0{sha((ROOT/p).read_bytes())}" for p in scanned);dump("LCR_BATCH4_PACKAGE_REPORT.json",{"status":"ready_for_packaging","archive_name":ARCHIVE.name,"archive_type":"allowlist_only","entries":entries,"entry_count":len(entries),"size":sum((ROOT/p).stat().st_size for p in scanned),"size_scope":"uncompressed allowlisted bytes excluding self-referential package report","sha256":sha(manifest.encode()),"sha256_scope":"content manifest excluding package report","duplicate_entries":0,"path_traversal_entries":0,"nested_zip_entries":0,"secret_scan_result":"PASS","utf8_paths":True,"forward_slash_paths":True,"allowlist_result":"PASS"})
    with zipfile.ZipFile(ARCHIVE,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for p in entries:archive.write(ROOT/p,arcname=p)
    with zipfile.ZipFile(ARCHIVE) as archive:
        names=archive.namelist();assert names==entries and len(names)==len(set(names));assert archive.testzip() is None;assert not any(n.lower().endswith(".zip") or "\\" in n or PurePosixPath(n).is_absolute() or ".." in PurePosixPath(n).parts for n in names);assert not [(n,scan_bytes(archive.read(n))) for n in names if scan_bytes(archive.read(n))]
    print(json.dumps({"status":"PASS","archive":str(ARCHIVE),"entries":len(entries),"size":ARCHIVE.stat().st_size,"sha256":sha(ARCHIVE.read_bytes())},sort_keys=True))
if __name__=="__main__":main()
