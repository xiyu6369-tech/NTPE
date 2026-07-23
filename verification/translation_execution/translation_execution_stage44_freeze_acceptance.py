from __future__ import annotations

import hashlib
import sys
import tempfile
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from core.book_preparation import BookPreparationProcessor
from core.translation_execution_approval import (
    ExplicitHumanApprovalRequest,
    TranslationExecutionApprover,
    get_translation_execution_governance_freeze_metadata,
    validate_translation_execution_governance_freeze,
)
from core.translation_execution_authorization import (
    TranslationExecutionAuthorizationEvaluator,
)
from core.translation_execution_package import TranslationExecutionPackageBuilder


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    metadata = get_translation_execution_governance_freeze_metadata()
    result = validate_translation_execution_governance_freeze()
    _assert(result.valid, "freeze validation did not pass")
    _assert(result.frozen_file_count == 16, "frozen source count drifted")
    _assert(result.public_api_count == 34, "public API count drifted")
    _assert(result.invariant_count == 38, "invariant count drifted")
    _assert(
        metadata.activation_gate == "translation_execution_governance_frozen",
        "activation gate drifted",
    )
    _assert(
        not any(
            (
                metadata.provider_execution_authorized,
                metadata.translation_execution_authorized,
                metadata.runtime_submission_authorized,
                metadata.automatic_retry_authorized,
                metadata.automatic_fallback_authorized,
                metadata.output_replacement_authorized,
                metadata.production_integration_authorized,
            )
        ),
        "global authorization boundary drifted",
    )

    text = (
        "Chapter 1\r\n"
        + "English text. " * 160
        + "\r\nChapter 2\r\n"
        + "End. " * 160
    )
    with tempfile.TemporaryDirectory(prefix="ntpe-stage44-") as directory:
        source = Path(directory) / "acceptance.txt"
        source.write_bytes(text.encode("utf-8"))
        preparation = BookPreparationProcessor().prepare(source)
        package = TranslationExecutionPackageBuilder().build(preparation)
        decision = TranslationExecutionAuthorizationEvaluator().evaluate(package)
        statement = "APPROVE_CONTROLLED_TRANSLATION_EXECUTION\nfull_package"
        request = ExplicitHumanApprovalRequest(
            approval_type="full_package",
            approved_package_fingerprint=package.execution_package_fingerprint,
            approved_authorization_fingerprint=decision.authorization_fingerprint,
            approved_unit_indices=tuple(range(package.unit_count)),
            approve_provider_execution=True,
            approve_translation_execution=True,
            approve_runtime_submission=True,
            approve_automatic_retry=False,
            approve_automatic_fallback=False,
            approve_output_replacement=False,
            approval_statement=statement,
            approval_reference="stage44-standalone-acceptance",
        )
        record = TranslationExecutionApprover().approve(
            package=package,
            authorization_decision=decision,
            approval_request=request,
        )
        _assert(
            package.reconstruct_source_text() == text,
            "package reconstruction drifted",
        )
        _assert(decision.authorized is False, "default authorization was not denied")
        _assert(
            decision.package_fingerprint == package.execution_package_fingerprint,
            "package-to-decision fingerprint chain failed",
        )
        _assert(
            record.package_fingerprint == package.execution_package_fingerprint,
            "package-to-record fingerprint chain failed",
        )
        _assert(
            record.authorization_fingerprint == decision.authorization_fingerprint,
            "decision-to-record fingerprint chain failed",
        )
        _assert(
            record.approval_statement_fingerprint
            == hashlib.sha256(statement.encode("utf-8")).hexdigest(),
            "approval statement fingerprint drifted",
        )
        _assert(statement not in record.to_json(), "approval statement was persisted")
        _assert(
            all(unit.attempt_count == 0 for unit in package.units),
            "attempt counter changed",
        )
        _assert(
            all(unit.provider_request_count == 0 for unit in package.units),
            "provider counter changed",
        )
        _assert(
            all(not unit.translation_result_attached for unit in package.units),
            "translation result was attached",
        )
        _assert(
            not any(
                (
                    record.automatic_retry_authorized,
                    record.automatic_fallback_authorized,
                    record.output_replacement_authorized,
                )
            ),
            "prohibited approval capability was enabled",
        )

    print(
        "PASS: Stage 4.4 translation execution governance freeze "
        "(provider/network/translation/runtime/output/retry/fallback/hooks = 0)"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"FAIL: Stage 4.4 translation execution governance freeze: {error}")
        raise SystemExit(1) from error
