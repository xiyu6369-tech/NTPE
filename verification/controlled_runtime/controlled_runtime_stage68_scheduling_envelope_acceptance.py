"""Offline acceptance check for Stage 6.8."""

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.controlled_runtime_scheduling_envelope import (
    ControlledRuntimeSchedulingEnvelopeBuilder,
    verify_controlled_runtime_scheduling_envelope,
)
from tests.unit.controlled_runtime_scheduling_envelope import build_context


def main() -> int:
    with TemporaryDirectory(prefix="ntpe-stage68-") as folder:
        context = build_context(Path(folder))
        before = tuple(repr(value) for value in context.values())
        result = ControlledRuntimeSchedulingEnvelopeBuilder().build(**context)
        envelope = result.scheduling_envelope
        assert before == tuple(repr(value) for value in context.values())
        assert result.status == (
            "scheduling_envelope_prepared_not_admitted_not_scheduled"
        )
        assert result.recommended_action == (
            "retain_for_controlled_queue_admission_authorization"
        )
        assert result.builder_invoked
        assert envelope is not None
        assert len(envelope.upstream_fingerprint_chain) == 23
        assert envelope.scheduling_envelope_prepared
        assert not envelope.scheduling_envelope_consumed
        assert not envelope.scheduling_envelope_reusable
        assert not envelope.queue_admission_authorized
        assert not any(
            getattr(envelope, name)
            for name in (
                "runtime_execution_scheduled",
                "queue_record_created",
                "job_record_created",
                "worker_started",
                "execution_started",
                "execution_completed",
                "runtime_execution_enabled",
                "provider_execution_enabled",
                "network_execution_enabled",
                "translation_execution_enabled",
                "output_write_enabled",
                "resume_write_enabled",
                "cache_write_enabled",
                "retry_enabled",
                "fallback_enabled",
                "production_hook_enabled",
            )
        )
        assert not any(
            getattr(result, name)
            for name in (
                "stage67_registry_read",
                "stage67_registry_written",
                "scheduler_invoked",
                "queue_admission_invoked",
                "queue_written",
                "job_created",
                "worker_started",
                "runtime_invoked",
                "provider_invoked",
                "network_invoked",
                "translation_invoked",
                "output_written",
                "resume_written",
                "cache_written",
                "retry_used",
                "fallback_used",
                "production_hook_invoked",
            )
        )
        assert verify_controlled_runtime_scheduling_envelope(
            envelope,
            request=context["request"],
            stage67_scheduling_consumption_request=
                context["stage67_scheduling_consumption_request"],
            stage67_scheduling_consumption_claim=
                context["stage67_scheduling_consumption_claim"],
        ).valid
    print("Stage 6.8 scheduling envelope acceptance: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
