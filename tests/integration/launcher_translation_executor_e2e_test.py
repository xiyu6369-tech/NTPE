import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from translation.executor import TranslationRuntimeExecutor  # noqa: E402


def check(label, condition):
    print(f"{label:<30} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(label)


print("NTPE Foundation-06.5 Translation Executor E2E Test")
print("=" * 52)

job = {
    "job_id": "job-e2e-065",
    "target_language": "zh-TW",
    "segments": [
        {"segment_id": "s1", "source_text": "첫 문장", "status": "pending"},
        {"segment_id": "s2", "source_text": "두 번째 문장", "status": "pending"},
    ],
}
context = {"previous_context": "", "glossary": {"문장": "句子"}}
executor = TranslationRuntimeExecutor()
check("Job Ready", job["job_id"] == "job-e2e-065")

for segment in job["segments"]:
    result = executor.execute_segment(job, segment, context_bundle=context)
    check(f"Segment {segment['segment_id']}", result["status"] == "completed")

check("All Completed", all(s["status"] == "completed" for s in job["segments"]))
check("Results Attached", len(job.get("results", {})) == 2)
check("Trace Ready", len(executor.trace["events"]) >= 4)
check("Metrics Ready", executor.metrics["completed"] == 2)
check("Manifest Ready", executor.manifest()["metrics"]["success_rate"] == 1.0)
print("PASS")
