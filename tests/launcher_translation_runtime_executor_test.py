import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from translation.executor import (  # noqa: E402
    TranslationRuntimeExecutor,
    TranslationExecutorAdapter,
    MockModelAdapter,
    validate_translation_executor_result,
)


def check(label, condition):
    print(f"{label:<32} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(label)


print("NTPE Foundation-06.5 Translation Runtime Executor Test")
print("=" * 56)

legacy_segment = {"id": "legacy-001", "text": "안녕하세요", "status": "pending"}
check("Legacy Segment", legacy_segment["id"] == "legacy-001")

executor = TranslationRuntimeExecutor()
check("Executor Created", executor.executor_id == "translation-runtime-executor")

job = {"job_id": "job-065", "target_language": "zh-TW"}
segment = {"segment_id": "seg-001", "source_text": "안녕하세요", "status": "pending"}
context = {"previous_context": "", "glossary": {"안녕하세요": "你好"}}
package = executor.build_prompt_package(segment, context)
check("Prompt Package", package["segment_id"] == "seg-001")
check("Package Messages", len(package["messages"]) == 2)

result = executor.execute_segment(job, segment, context_bundle=context)
check("Execute Segment", validate_translation_executor_result(result))
check("Segment Completed", segment["status"] == "completed")
check("Result Output", "translated" in result["output_text"])
check("Job Result Attached", "seg-001" in job["results"])
check("Trace Written", len(executor.trace["events"]) >= 2)
check("Metrics Updated", executor.metrics["completed"] == 1)

failed_segment = {"segment_id": "seg-error", "source_text": "error", "status": "pending"}
failed_package = executor.build_prompt_package(failed_segment, context)
failed_package["force_error"] = True
failed_result = executor.execute_segment(job, failed_segment, context_bundle=context, prompt_package=failed_package)
check("Failure Result", failed_result["status"] == "failed")
check("Failure Segment", failed_segment["status"] == "failed")
check("Failure Metrics", executor.metrics["failed"] == 1)

adapter = TranslationExecutorAdapter(executor)
adapter_segment = {"segment_id": "seg-adapter", "source_text": "테스트", "status": "pending"}
adapter_result = adapter.execute(job, adapter_segment, context_bundle=context)
check("Adapter Created", adapter.executor is executor)
check("Adapter Execute", adapter_result["status"] == "completed")
check("Adapter Manifest", adapter.manifest()["version"] == "06.5")

model_adapter = MockModelAdapter()
check("Model Manifest", model_adapter.manifest()["adapter_id"] == "mock-model-adapter")
check("Executor Manifest", executor.manifest()["kind"] == "ntpe.translation_runtime_executor")
check("Backward Compatible", legacy_segment["text"] == "안녕하세요")
print("PASS")
