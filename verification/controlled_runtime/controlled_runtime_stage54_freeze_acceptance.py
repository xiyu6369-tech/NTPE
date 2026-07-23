from __future__ import annotations

import copy
import socket
import sys
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.book_preparation import BookPreparationProcessor
from core.controlled_runtime_adapter import (
    ControlledRuntimeAdapter,
    RuntimeAdapterCapabilityError,
)
from core.controlled_runtime_execution_plan import (
    ControlledRuntimeExecutionPlanner,
    ControlledRuntimeExecutionPolicyError,
    ControlledRuntimeExecutionScopeError,
    get_controlled_runtime_preparation_freeze_metadata,
    validate_controlled_runtime_preparation_freeze,
)
from core.controlled_runtime_execution_plan.policy import DEFAULT_POLICY
from core.controlled_runtime_submission import ControlledRuntimeSubmissionBuilder
from core.translation_execution_approval import (
    ExplicitHumanApprovalRequest,
    TranslationExecutionApprover,
)
from core.translation_execution_authorization import (
    TranslationExecutionAuthorizationEvaluator,
)
from core.translation_execution_package import TranslationExecutionPackageBuilder


def build_offline_chain(
    source: Path,
    *,
    approval_type: str = "full_package",
    approved_unit_indices: tuple[int, ...] | None = None,
    selected_adapter_unit_indices: tuple[int, ...] = (0,),
):
    package = TranslationExecutionPackageBuilder().build(
        BookPreparationProcessor().prepare(source)
    )
    decision = TranslationExecutionAuthorizationEvaluator().evaluate(package)
    indices = (
        tuple(range(package.unit_count))
        if approved_unit_indices is None
        else approved_unit_indices
    )
    statement = "APPROVE_CONTROLLED_TRANSLATION_EXECUTION: stage54 acceptance"
    if package.status == "prepared_with_warnings":
        statement += " ACKNOWLEDGE_PACKAGE_WARNINGS"
    request = ExplicitHumanApprovalRequest(
        approval_type=approval_type,
        approved_package_fingerprint=package.execution_package_fingerprint,
        approved_authorization_fingerprint=decision.authorization_fingerprint,
        approved_unit_indices=indices,
        approve_provider_execution=True,
        approve_translation_execution=True,
        approve_runtime_submission=True,
        approve_automatic_retry=False,
        approve_automatic_fallback=False,
        approve_output_replacement=False,
        approval_statement=statement,
        approval_reference="stage54-standalone",
    )
    approval = TranslationExecutionApprover().approve(
        package=package,
        authorization_decision=decision,
        approval_request=request,
    )
    submission = ControlledRuntimeSubmissionBuilder().build(
        package=package,
        authorization_decision=decision,
        approval_record=approval,
    )
    adapter_result = ControlledRuntimeAdapter().prepare(
        submission_package=submission
    )
    plan = ControlledRuntimeExecutionPlanner().plan(
        adapter_preparation_result=adapter_result,
        selected_adapter_unit_indices=selected_adapter_unit_indices,
    )
    return package, decision, approval, submission, adapter_result, plan


def run_acceptance() -> None:
    freeze_result = validate_controlled_runtime_preparation_freeze()
    metadata = get_controlled_runtime_preparation_freeze_metadata()
    assert freeze_result.valid
    assert freeze_result.frozen_file_count == 16
    assert freeze_result.public_api_count == 41
    assert metadata.activation_gate == "controlled_runtime_preparation_frozen"
    assert not any(
        value
        for name, value in vars(metadata).items()
        if name.endswith("_authorized")
        or name.endswith("_enabled")
        or name == "production_integration_authorized"
    )

    with TemporaryDirectory() as directory:
        source = Path(directory) / "acceptance.txt"
        text = (
            "Chapter 1\n"
            + "Sentence. " * 180
            + "\nChapter 2\n"
            + "Another sentence. " * 110
        )
        source.write_bytes(text.encode("utf-8"))
        original_connection = socket.create_connection

        def forbidden(*args: object, **kwargs: object) -> None:
            raise AssertionError("Network/provider/runtime boundary invoked")

        socket.create_connection = forbidden
        try:
            chains = tuple(build_offline_chain(source) for _ in range(3))
        finally:
            socket.create_connection = original_connection
        first = chains[0]
        assert first == chains[1] == chains[2]
        package, decision, approval, submission, adapter_result, plan = first
        assert (
            package.execution_package_fingerprint
            == decision.package_fingerprint
            == approval.package_fingerprint
            == submission.source.execution_package_fingerprint
        )
        assert (
            decision.authorization_fingerprint
            == approval.authorization_fingerprint
            == submission.source.authorization_fingerprint
        )
        assert (
            approval.approval_record_fingerprint
            == submission.source.approval_record_fingerprint
        )
        assert (
            submission.runtime_submission_package_fingerprint
            == adapter_result.request.source.runtime_submission_package_fingerprint
            == plan.source.runtime_submission_package_fingerprint
        )
        assert (
            adapter_result.request.runtime_adapter_request_fingerprint
            == plan.source.runtime_adapter_request_fingerprint
        )
        assert (
            adapter_result.preparation_fingerprint
            == plan.source.runtime_adapter_preparation_fingerprint
        )
        assert plan.execution_plan_fingerprint
        assert plan.reconstruct_planned_text() == adapter_result.request.units[0].text
        assert submission.provider_execution_authorized
        assert adapter_result.request.provider_execution_authorized
        assert plan.provider_execution_authorized
        assert not adapter_result.capability_profile.supports_provider_execution
        assert not adapter_result.capability_profile.supports_translation_execution
        assert not plan.runtime_execution_enabled
        assert not plan.provider_execution_enabled
        assert not plan.translation_execution_enabled
        assert not adapter_result.runtime_invoked
        assert not adapter_result.provider_invoked
        assert not adapter_result.translation_invoked
        assert not plan.execution_started and not plan.execution_completed
        assert plan.provider_requests_executed == 0
        assert plan.translation_executions_completed == 0

        with_approval = build_offline_chain(
            source,
            approval_type="single_unit",
            approved_unit_indices=(0,),
        )
        assert with_approval[3].approved_unit_indices == (0,)
        assert with_approval[5].covers_full_approved_scope

        try:
            ControlledRuntimeExecutionPlanner().plan(
                adapter_preparation_result=adapter_result
            )
        except ControlledRuntimeExecutionScopeError:
            pass
        else:
            raise AssertionError("Planner auto-selected a unit")

        relaxed_profile = replace(
            adapter_result.capability_profile,
            supports_provider_execution=True,
        )
        try:
            ControlledRuntimeAdapter(relaxed_profile)
        except RuntimeAdapterCapabilityError:
            pass
        else:
            raise AssertionError("Adapter capability relaxation was accepted")

        try:
            ControlledRuntimeExecutionPlanner(
                replace(DEFAULT_POLICY, allow_parallel_execution=True)
            )
        except ControlledRuntimeExecutionPolicyError:
            pass
        else:
            raise AssertionError("Execution policy relaxation was accepted")

        zero_policy = replace(
            DEFAULT_POLICY,
            maximum_provider_requests_per_unit=0,
            maximum_total_provider_requests=0,
        )
        try:
            ControlledRuntimeExecutionPlanner(zero_policy).plan(
                adapter_preparation_result=adapter_result,
                selected_adapter_unit_indices=(0,),
            )
        except ControlledRuntimeExecutionPolicyError:
            pass
        else:
            raise AssertionError("Zero-request policy pretended to be executable")

        original = copy.deepcopy(adapter_result)
        assert adapter_result == original

    print(
        "CONTROLLED_RUNTIME_STAGE54_FREEZE_ACCEPTANCE: PASS "
        "(runtime=0 provider=0 network=0 translation=0 writes=0)"
    )


if __name__ == "__main__":
    try:
        run_acceptance()
    except Exception as error:
        print(
            f"CONTROLLED_RUNTIME_STAGE54_FREEZE_ACCEPTANCE: FAIL: {error}",
            file=sys.stderr,
        )
        raise SystemExit(1) from error
