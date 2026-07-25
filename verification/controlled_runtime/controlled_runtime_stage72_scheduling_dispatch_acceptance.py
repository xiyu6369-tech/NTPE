from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Barrier

from core.controlled_runtime_scheduling_dispatch import (
    ControlledRuntimeScheduler,
    ControlledRuntimeSchedulingRegistry,
)
from tests.unit.controlled_runtime_scheduling_dispatch import build_context


def main() -> int:
    with TemporaryDirectory() as directory:
        root = Path(directory)
        context = build_context(root)
        first = ControlledRuntimeScheduler().schedule(**context)
        replay = ControlledRuntimeScheduler().schedule(**context)
        checks = [
            ("authentic Stage 7.1 authority", first.upstream_verified),
            ("one queue record consumed", first.queue_record_consumed_count == 1),
            ("one durable schedule", first.runtime_schedule_count == 1),
            ("one dispatch package", first.dispatch_package_count == 1),
            ("38-layer canonical chain", len(first.dispatch_package.canonical_chain) == 38),
            ("execution not started", first.runtime_execution_count == 0),
            ("worker not started", first.worker_started_count == 0),
            ("provider network translation zero", (
                first.provider_execution_count,
                first.network_execution_count,
                first.translation_execution_count,
            ) == (0, 0, 0)),
            ("output resume cache zero", (
                first.output_write_count,
                first.resume_write_count,
                first.cache_write_count,
            ) == (0, 0, 0)),
            ("identical replay closed", replay.replay_detected),
            ("one of each durable row", ControlledRuntimeSchedulingRegistry(
                context["database_path"], allowed_root=root
            ).counts() == (1, 1, 1)),
        ]
        concurrent_root = root / "concurrent"
        concurrent_root.mkdir()
        concurrent_context = build_context(concurrent_root)
        barrier = Barrier(6)

        def attempt(_):
            barrier.wait()
            return ControlledRuntimeScheduler().schedule(**concurrent_context)

        with ThreadPoolExecutor(max_workers=6) as pool:
            results = list(pool.map(attempt, range(6)))
        checks.extend([
            ("six-way exactly one success", sum(item.verification_succeeded for item in results) == 1),
            ("six-way five replays", sum(item.replay_detected for item in results) == 5),
            ("six-way one consumption schedule dispatch", ControlledRuntimeSchedulingRegistry(
                concurrent_context["database_path"], allowed_root=concurrent_root
            ).counts() == (1, 1, 1)),
        ])
        for label, passed in checks:
            print(f"{'PASS' if passed else 'FAIL'}: {label}")
        return 0 if all(passed for _, passed in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
