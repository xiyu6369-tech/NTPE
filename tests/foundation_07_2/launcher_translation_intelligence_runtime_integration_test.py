from __future__ import annotations

import os
import sys
from dataclasses import dataclass

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.intelligence import (  # noqa: E402
    IntelligenceMemoryStore,
    TranslationIntelligenceEngine,
    TranslationIntelligenceRuntimeIntegration,
)


def check(name: str, condition: bool) -> None:
    print(f"{name:<34} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


@dataclass
class RuntimeSegment:
    segment_id: str
    source_text: str
    metadata: dict


def main() -> None:
    store = IntelligenceMemoryStore()
    engine = TranslationIntelligenceEngine(store=store)
    integration = TranslationIntelligenceRuntimeIntegration(engine=engine)

    engine.characters.remember("정태의", "鄭泰義", aliases=["태의"])
    engine.glossary.remember("군부대", "軍隊基地", category="location", locked=True)
    engine.narrative.remember("relationship:정태의", "主角目前正在適應新環境", weight=5)
    engine.scenes.remember("scene-001", "抵達軍隊基地", location="基地", participants=["鄭泰義"])

    segment = {
        "id": "seg-001",
        "text": "정태의는 군부대에 도착했다.",
        "metadata": {"chapter": 1},
    }

    before = integration.before_segment(
        segment,
        prompt_package={"context_components": []},
        runtime_manifest={"components": []},
        metadata={"runtime": "test"},
    )
    check("Before Segment", before.segment_id == "seg-001")
    check("Prompt Context Attached", len(before.prompt_package["context_components"]) >= 1)
    check("Runtime Manifest Attached", len(before.runtime_manifest["components"]) >= 2)
    check("Integration Manifest", before.snapshot["manifest"]["foundation"] == "07.2")
    check("Metadata Merged", before.metadata["chapter"] == 1 and before.metadata["runtime"] == "test")

    after = integration.after_segment(segment, "鄭泰義抵達軍隊基地。")
    check("After Segment", after["runtime_integration"]["stage"] == "after_segment")
    check("Consistency Passed", after["consistency"]["passed"] is True)
    check("After Snapshot", after["snapshot"]["manifest"]["last_segment_id"] == "seg-001")

    issue_result = integration.after_segment(segment, "他抵達那裡。")
    check("Consistency Issues", issue_result["consistency"]["issue_count"] >= 1)

    processed = integration.process_runtime_segment(segment, output_text="鄭泰義抵達軍隊基地。")
    check("Process Runtime Segment", processed["segment_id"] == "seg-001")
    check("Process Consistency", processed["consistency"]["passed"] is True)

    payload = integration.attach_to_runtime_payload({"metadata": {"mode": "payload"}}, segment)
    check("Runtime Payload", "intelligence" in payload)
    check("Payload Prompt Package", "prompt_package" in payload and payload["prompt_package"]["context_components"])

    object_segment = RuntimeSegment(
        segment_id="seg-002",
        source_text="태의는 군부대 안으로 걸어갔다.",
        metadata={"chapter": 1},
    )
    object_before = integration.before_segment(object_segment)
    check("Object Segment", object_before.segment_id == "seg-002")

    wrapped = integration.wrap_executor(lambda seg: "鄭泰義走進軍隊基地。")
    wrapped_result = wrapped(object_segment)
    check("Wrapped Executor", wrapped_result["output_text"] == "鄭泰義走進軍隊基地。")
    check("Wrapped Consistency", wrapped_result["consistency"]["passed"] is True)

    check("Backward Engine", engine.build_snapshot()["manifest"]["foundation"] == "07.1")
    check("Backward Store", store.build_snapshot().to_dict()["manifest"]["foundation"] == "07.0")
    print("PASS")


if __name__ == "__main__":
    main()
