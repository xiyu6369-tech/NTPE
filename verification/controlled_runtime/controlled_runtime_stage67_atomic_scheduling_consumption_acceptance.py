import sys
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.controlled_runtime_atomic_scheduling_consumption import (
    AtomicSchedulingAuthorizationConsumer,
    AtomicSchedulingAuthorizationConsumptionRegistry,
    verify_atomic_scheduling_consumption_claim,
)
from tests.unit.controlled_runtime_atomic_scheduling_consumption import build_context


def main() -> int:
    with TemporaryDirectory(prefix="ntpe-stage67-") as folder:
        root = Path(folder)
        context = build_context(root)
        before = tuple(repr(value) for value in context.values())
        result = AtomicSchedulingAuthorizationConsumer().consume(**context)
        assert before == tuple(repr(value) for value in context.values())
        assert result.status == "scheduling_authorization_consumed_not_scheduled"
        assert result.recommended_action == "retain_for_controlled_runtime_scheduling_envelope"
        assert result.consumer_invoked
        assert result.registry_read
        assert result.registry_written
        assert result.claim is not None
        assert len(result.claim.upstream_fingerprint_chain) == 21
        assert result.claim.scheduling_authorization_consumed
        assert not result.claim.scheduling_authorization_reusable
        assert result.claim.durable_scheduling_reuse_prevention_established
        assert result.claim.persistent_scheduling_registry_written
        assert not any(getattr(result.claim, name) for name in (
            "runtime_execution_scheduled", "queue_record_created",
            "job_record_created", "worker_started", "execution_started",
            "execution_completed", "runtime_execution_enabled",
            "provider_execution_enabled", "network_execution_enabled",
            "translation_execution_enabled", "output_write_enabled",
            "resume_write_enabled", "cache_write_enabled", "retry_enabled",
            "fallback_enabled", "production_hook_enabled",
        ))
        assert not any(getattr(result, name) for name in (
            "scheduler_invoked", "queue_written", "job_created", "worker_started",
            "runtime_invoked", "provider_invoked", "network_invoked",
            "translation_invoked", "output_written", "resume_written",
            "cache_written", "retry_used", "fallback_used",
            "production_hook_invoked",
        ))
        assert verify_atomic_scheduling_consumption_claim(
            result.claim, request=context["request"]
        ).valid
        registry = AtomicSchedulingAuthorizationConsumptionRegistry(
            context["database_path"], allowed_root=root
        )
        assert registry.count_claims() == 1
        replay = AtomicSchedulingAuthorizationConsumer().consume(**context)
        assert replay.status == "already_consumed"
        assert registry.count_claims() == 1
    print("Stage 6.7 acceptance: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())