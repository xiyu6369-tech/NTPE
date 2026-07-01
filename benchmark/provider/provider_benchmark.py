from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, List

from benchmark.benchmark_context import BenchmarkContext
from benchmark.benchmark_result import BenchmarkResult
from core.ai_provider.contracts import MockProvider
from core.ai_provider.manager import ProviderManager
from core.ai_provider.registry import ProviderRegistry

from .health_benchmark import HealthBenchmark
from .latency_benchmark import LatencyBenchmark
from .throughput_benchmark import ThroughputBenchmark


@dataclass
class ProviderBenchmark:
    provider: Any | None = None
    manager: Any | None = None
    prompts: Iterable[str] | None = None
    name: str = "provider_benchmark"

    def _provider(self) -> Any:
        if self.provider is not None:
            return self.provider
        if self.manager is not None and hasattr(self.manager, "registry"):
            default = self.manager.registry.default_name()
            if default:
                return self.manager.registry.get(default)
        return MockProvider(name="benchmark_mock", response_text="benchmark response for {prompt}")

    def _manager(self) -> Any:
        if self.manager is not None:
            return self.manager
        registry = ProviderRegistry()
        registry.register(self._provider(), default=True)
        return ProviderManager(registry=registry)

    def run(self, context: BenchmarkContext | None = None) -> List[BenchmarkResult]:
        provider = self._provider()
        manager = self._manager()
        results: List[BenchmarkResult] = []
        results.extend(LatencyBenchmark(provider=provider, prompts=self.prompts).run(context))
        results.extend(ThroughputBenchmark(provider=provider, prompts=self.prompts).run())
        results.extend(HealthBenchmark(manager=manager).run())
        return results


def run_provider_benchmark(provider: Any | None = None, manager: Any | None = None, prompts: Iterable[str] | None = None) -> List[BenchmarkResult]:
    return ProviderBenchmark(provider=provider, manager=manager, prompts=prompts).run()
