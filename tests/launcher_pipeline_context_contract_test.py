"""
NTPE Foundation-04.3 Pipeline Context Contract Test
Run:
    python tests\launcher_pipeline_context_contract_test.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.context_contract import (
    normalize_context_payload,
    validate_context_payload,
    merge_context_payload,
)
from core.pipeline_contract_adapter import PipelineContextContractAdapter


def check(label: str, condition: bool) -> None:
    status = "PASS" if condition else "FAIL"
    print(f"{label:<20} {status}")
    if not condition:
        raise AssertionError(label)


def main() -> None:
    print("NTPE Foundation-04.3 Pipeline Context Contract Test")
    print("=" * 54)

    legacy_payload = {
        "text": "안녕하세요.",
        "language": "繁體中文",
    }

    normalized = normalize_context_payload(legacy_payload)
    check("Legacy Normalize", normalized["source_text"] == "안녕하세요.")
    check("Target Language", normalized["target_language"] == "繁體中文")
    check("Context Created", isinstance(normalized["context"], dict))
    check("Metadata Created", normalized["metadata"]["foundation"] == "04.3")

    result = validate_context_payload(normalized)
    check("Validate Payload", result.ok is True)

    adapter = PipelineContextContractAdapter()
    adapted = adapter.before_stage(legacy_payload)
    check("Adapter Before", adapted["source_text"] == "안녕하세요.")

    after = adapter.after_stage(adapted)
    check("Adapter After", after["context"]["previous_text"] == "")

    merged = merge_context_payload(
        adapted,
        {
            "source_text": "새 문장입니다.",
            "context": {"previous_text": "이전 문장"},
            "metadata": {"stage": "unit_test"},
        },
    )
    check("Merge Source", merged["source_text"] == "새 문장입니다.")
    check("Merge Context", merged["context"]["previous_text"] == "이전 문장")
    check("Merge Metadata", merged["metadata"]["stage"] == "unit_test")

    print("PASS")


if __name__ == "__main__":
    main()
