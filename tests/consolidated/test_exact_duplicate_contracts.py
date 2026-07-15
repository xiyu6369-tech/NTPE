from __future__ import annotations

import hashlib
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]

CASES = [
    ("v3.2-stage-3.2.2", "bbf082862a4b154529f50121c5260ecbd0bb5019fc9edae602ded3725c8ea4cb", "ntpe_te_v32_stage322_runtime_adapter_dry_run_test.py", "tests/integration/translation_scheduler_stage322_runtime_adapter_dry_run_test.py", False),
    ("v5.2.1", "c940258652de122344f042177e06b8da04a730f92e7bcf0ca120fdc7979734b3", "ntpe_te_v521_timeout_propagation_fix_test.py", "tests/integration/translation_timeout_propagation_fix_test.py", False),
    ("v5.3.0", "2ba3aa9b1d93eb03afec373bd846d6821099db78af0b7058093cb18c60766a70", "ntpe_te_v530_quality_runtime_integration_phase1_test.py", "tests/integration/translation_quality_runtime_integration_phase1_test.py", False),
    ("v5.3.1.1", "5a2d1fef5cdc7376b5c499b48a348092b61ebd603527f2aa64e310c3d329fd3c", "ntpe_te_v5311_paragraph_coverage_corroboration_test.py", "tests/integration/translation_quality_paragraph_coverage_corroboration_v5311_test.py", False),
    ("v5.3.1.2", "3dad6ca3d53c7b70ba2954be9bf4436f4d4e9e2ba39cc6525d0b193da59f6c82", "ntpe_te_v5312_unified_nonblocking_issue_mapping_test.py", "tests/integration/translation_quality_unified_nonblocking_issue_mapping_v5312_test.py", True),
    ("v5.3.2", "0cb8faf504d1dce01822d46f05439b22e74a89a71be530b345d1c4c72952e1c1", "ntpe_te_v532_semantic_repetition_guard_test.py", "tests/integration/translation_quality_semantic_repetition_guard_v532_test.py", False),
    ("v5.4.0", "b05ae9f4a1ccad4ea6291e1ad74532680a5b85c94433ebe0b4dea2f4608431a0", "ntpe_te_v540_smart_local_repair_pipeline_test.py", "tests/integration/translation_quality_smart_local_repair_v540_test.py", False),
    ("v5.5.3.2", "0389acbd25150e81043e5a956dee53ff46805793ad933decbf18c9360564a31a", "ntpe_te_v5532_adaptive_retry_failure_fallback_test.py", "tests/integration/translation_adaptive_retry_failure_fallback_v5532_test.py", False),
]


def digest(relative_path: str) -> str:
    return hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest()


@pytest.mark.parametrize(
    "stage_id,baseline_sha256,root_path,integration_path,root_is_wrapper",
    CASES,
    ids=[case[0] for case in CASES],
)
def test_exact_duplicate_contract(
    stage_id: str,
    baseline_sha256: str,
    root_path: str,
    integration_path: str,
    root_is_wrapper: bool,
) -> None:
    assert digest(integration_path) == baseline_sha256, f"{stage_id}: formal integration implementation changed"
    if root_is_wrapper:
        assert digest(root_path) != baseline_sha256, f"{stage_id}: Root compatibility path still duplicates assertions"
    else:
        assert digest(root_path) == baseline_sha256, f"{stage_id}: protected Root implementation changed"
