import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from translation.job_manager import (
    SEGMENT_COMPLETED,
    SEGMENT_FAILED,
    SEGMENT_PENDING,
    SEGMENT_RUNNING,
    TranslationJobManager,
    create_job,
    create_translation_job_manager_adapter,
    export_job_manifest,
    normalize_job,
    normalize_segment,
    validate_job,
    validate_segment,
)


def check(name, condition):
    print(f"{name:<28} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


print("NTPE Foundation-06.1 Translation Job Manager Test")
print("===================================================")

legacy = {"id": "legacy-1", "text": "안녕"}
seg = normalize_segment(legacy, 0)
check("Legacy Segment", seg["segment_id"] == "legacy-1")
check("Segment Created", seg["source_text"] == "안녕")
check("Validate Segment", validate_segment(seg))

job = create_job("job-1", [{"source_text": "A"}, {"source_text": "B"}], target_language="zh-TW")
check("Job Created", job["job_id"] == "job-1")
check("Validate Job", validate_job(job))
check("Job Progress", job["progress"]["total"] == 2)

manager = TranslationJobManager(job)
check("Manager Created", manager.job["job_id"] == "job-1")
first = manager.next_pending()
check("Next Pending", first is not None and first["status"] == SEGMENT_PENDING)
manager.update_segment(first["segment_id"], SEGMENT_RUNNING)
check("Segment Running", first["status"] == SEGMENT_RUNNING)
manager.update_segment(first["segment_id"], SEGMENT_COMPLETED, target_text="甲")
check("Segment Completed", first["target_text"] == "甲")
progress = manager.progress()
check("Progress Completed", progress["completed"] == 1)
check("Progress Percent", progress["percent"] == 50.0)

second = manager.next_pending()
manager.update_segment(second["segment_id"], SEGMENT_FAILED, error={"message": "test"})
check("Segment Failed", second["status"] == SEGMENT_FAILED)
check("Job Partial", manager.job["status"] == "partial")

manifest = manager.manifest()
check("Manifest Created", manifest["type"] == "translation_job_manifest")
check("Manifest Progress", manifest["progress"]["failed"] == 1)
check("Manifest Segment IDs", len(manifest["segment_ids"]) == 2)

adapter = create_translation_job_manager_adapter(manager.job)
check("Adapter Created", adapter.validate())
adapter_manifest = adapter.manifest()
check("Adapter Manifest", adapter_manifest["job_id"] == "job-1")
adapter.update(first["segment_id"], SEGMENT_COMPLETED, target_text="甲2")
check("Adapter Update", adapter.manager.job["segments"][0]["target_text"] == "甲2")

legacy_job = normalize_job({"id": "legacy-job", "segments": [{"id": "s1", "text": "K"}]})
check("Legacy Job", legacy_job["job_id"] == "legacy-job")
check("Backward Compatible", validate_job(legacy_job))

print("PASS")
