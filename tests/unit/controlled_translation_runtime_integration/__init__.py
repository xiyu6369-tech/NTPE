from pathlib import Path

from core.adaptive_context_single_real_invocation import FakeSingleInvocationTransport
from core.controlled_runtime_scheduling_dispatch import ControlledRuntimeScheduler
from core.controlled_translation_runtime_integration import (
    ControlledTranslationExecutionRequest,
)
from core.controlled_translation_runtime_integration.policy import (
    SOURCE_FIXTURE_FINGERPRINT, SOURCE_FIXTURE_ID, TARGET_LANGUAGE,
    TRANSLATION_PROFILE,
)
from tests.unit.controlled_runtime_scheduling_dispatch import (
    build_context as build72_context,
)


FAKE_TRANSLATION = """「伊萊！」

正要轉身離去的男人被鄭泰義下意識叫住。伊萊微微挑起眉，只轉過頭看他。鄭泰義心情沉重地瞪了他片刻，才鬱鬱地開口。

「要是你敢用強硬的手段，……我絕不會坐視不管。」

伊萊愉快地笑了，只留下一句無論怎麼解讀都說得通的簡短回答——「當然。」隨即再次邁開腳步。

鄭泰義呆站在原地，直到那道身影轉過街角、徹底消失。他靠著牆緩緩滑坐下來，彷彿幾十年份的疲憊突然一口氣壓上肩頭。

事情已經糟得不能再糟。反正他大概也無法拒絕那項提議；若堅持抗拒，誰也不能保證對方不會乾脆撕破臉。雖然他連拒絕的理由都沒有，卻從未希望局面變成這樣。"""


def build_context(tmp_path, *, output=FAKE_TRANSLATION, **request_overrides):
    upstream_root = tmp_path / "stage72"
    upstream_root.mkdir(parents=True, exist_ok=True)
    context72 = build72_context(upstream_root)
    result72 = ControlledRuntimeScheduler().schedule(**context72)
    dispatch = result72.dispatch_package
    assert dispatch is not None
    request_values = dict(
        dispatch_package_id=dispatch.dispatch_package_id,
        dispatch_fingerprint=dispatch.dispatch_fingerprint,
        schedule_id=dispatch.schedule_id,
        schedule_fingerprint=dispatch.schedule_fingerprint,
        scheduling_request_id=dispatch.scheduling_request_id,
        scheduling_request_fingerprint=dispatch.scheduling_request_fingerprint,
        queue_record_id=dispatch.queue_record_id,
        queue_record_fingerprint=dispatch.queue_record_fingerprint,
        stage613_claim_id=dispatch.stage613_claim_id,
        stage613_claim_fingerprint=dispatch.stage613_claim_fingerprint,
        stage612_record_id=dispatch.stage612_record_id,
        stage612_record_fingerprint=dispatch.stage612_record_fingerprint,
        stage611_claim_id=dispatch.stage611_claim_id,
        stage611_claim_fingerprint=dispatch.stage611_claim_fingerprint,
        stage610_authorization_id=dispatch.stage610_authorization_id,
        stage610_decision_fingerprint=dispatch.stage610_decision_fingerprint,
        stage69_consumption_claim_id=dispatch.stage69_consumption_claim_id,
        stage69_claim_fingerprint=dispatch.stage69_claim_fingerprint,
        stage68_scheduling_envelope_id=dispatch.stage68_scheduling_envelope_id,
        stage68_envelope_fingerprint=dispatch.stage68_envelope_fingerprint,
        stage67_consumption_claim_id=dispatch.stage67_consumption_claim_id,
        stage67_claim_fingerprint=dispatch.stage67_claim_fingerprint,
        stage66_scheduling_authorization_id=(
            dispatch.stage66_scheduling_authorization_id
        ),
        stage66_decision_fingerprint=dispatch.stage66_decision_fingerprint,
        runtime_boundary_id=dispatch.runtime_boundary_id,
        runtime_boundary_kind=dispatch.runtime_boundary_kind,
        selected_adapter_index=dispatch.selected_adapter_index,
        capability_state_fingerprint=dispatch.capability_state_fingerprint,
        dispatch_key=dispatch.dispatch_key,
        execution_plan_reference_fingerprint=(
            dispatch.execution_plan_reference_fingerprint
        ),
        work_package_reference_fingerprint=(
            dispatch.work_package_reference_fingerprint
        ),
        source_fixture_id=SOURCE_FIXTURE_ID,
        source_fingerprint=SOURCE_FIXTURE_FINGERPRINT,
        target_language=TARGET_LANGUAGE,
        translation_profile=TRANSLATION_PROFILE,
        unit_scope=1,
        upstream_chain=dispatch.canonical_chain,
    )
    request_values.update(request_overrides)
    request = ControlledTranslationExecutionRequest(**request_values)
    authority = {
        key: context72[key]
        for key in (
            "queue_record", "stage71_request", "stage71_result",
            "stage613_claim", "stage613_request", "stage613_result",
            "stage613_verification_context",
        )
    }
    return dict(
        request=request,
        dispatch_package=dispatch,
        schedule=result72.schedule,
        stage72_request=context72["request"],
        stage72_result=result72,
        repository_root=Path(__file__).resolve().parents[3],
        artifact_root=tmp_path / "artifacts",
        execution_mode="fake",
        transport=FakeSingleInvocationTransport(outputs=(output,)),
        environ={},
        **authority,
    )
