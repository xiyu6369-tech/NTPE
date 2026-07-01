from translation.segment_manager import TranslationSegmentManager
from translation.context_runtime import create_translation_context_runtime_adapter

job = {"job_id": "simple", "target_language": "zh-TW"}
segments = [{"segment_id": "s1", "index": 1, "source_text": "안녕하세요"}]
manager = TranslationSegmentManager(segments)
adapter = create_translation_context_runtime_adapter(job=job)
segment = manager.next()
print(adapter.build_context(segment, manager.queue["segments"]))
