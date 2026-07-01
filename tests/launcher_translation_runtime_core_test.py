import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from translation.runtime import (  # noqa: E402
    TranslationRuntimeCore,
    TranslationRuntimeCoreAdapter,
    create_translation_runtime,
    create_translation_session,
    normalize_runtime_job,
    update_session_progress,
    validate_runtime_result,
    validate_translation_session,
)


def check(label, condition):
    print(f"{label:<34} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(label)


print("NTPE Foundation-06.6 Translation Runtime Core Test")
print("=" * 56)

legacy_job = {"id": "legacy-job", "target": "zh-TW", "segments": [{"id": "legacy-seg", "text": "안녕"}]}
normalized = normalize_runtime_job(legacy_job)
check("Legacy Job", normalized["job_id"] == "legacy-job")
check("Legacy Segment", normalized["segments"][0]["segment_id"] == "legacy-seg")

session = create_translation_session(normalized)
check("Session Created", session["type"] == "translation_runtime_session")
check("Validate Session", validate_translation_session(session))
check("Session Progress", session["progress"]["total"] == 1)

runtime = TranslationRuntimeCore()
check("Runtime Created", runtime.runtime_id == "translation-runtime-core")
manifest = runtime.bootstrap()
check("Runtime Bootstrap", manifest["type"] == "translation_runtime_core")
check("Manifest Components", "components" in manifest)

job = {
    "job_id": "job-066",
    "source_language": "ko",
    "target_language": "zh-TW",
    "glossary": {"안녕하세요": "你好"},
    "segments": [
        {"segment_id": "seg-001", "index": 0, "source_text": "안녕하세요", "status": "pending"},
        {"segment_id": "seg-002", "index": 1, "source_text": "테스트", "status": "pending"},
    ],
}
result = runtime.execute(job)
check("Runtime Execute", validate_runtime_result(result))
check("Runtime Completed", result["status"] == "completed")
check("Result Count", len(result["results"]) == 2)
check("Job Results", "seg-001" in result["job"]["results"])
check("Segment Completed", result["job"]["segments"][0]["status"] == "completed")
check("Session Completed", result["session"]["status"] == "completed")
check("Progress Percent", result["session"]["progress"]["percent"] == 100.0)
check("Runtime Events", len(result["session"]["events"]) >= 4)
check("Runtime Manifest", result["manifest"]["version"] == "Foundation-06.6")

resume_session = create_translation_session(job, session_id="resume-001")
job_resume = normalize_runtime_job(job)
job_resume["segments"][0]["status"] = "completed"
update_session_progress(resume_session, job_resume["segments"])
resume_result = runtime.execute(job_resume, session=resume_session, resume=True)
check("Session Resume", resume_result["session"]["progress"]["completed"] >= 1)
check("Resume Status", resume_result["status"] == "completed")

adapter = TranslationRuntimeCoreAdapter(runtime)
adapter_result = adapter.run({"job_id": "job-adapter", "segments": [{"segment_id": "a", "source_text": "테스트"}]})
check("Adapter Created", adapter.runtime is runtime)
check("Adapter Run", adapter.validate(adapter_result))
check("Adapter Manifest", adapter.manifest()["type"] == "translation_runtime_core")
check("Backward Compatible", legacy_job["segments"][0]["text"] == "안녕")
print("PASS")
