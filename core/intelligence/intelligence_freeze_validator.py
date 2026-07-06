# =====================================================
# NTPE 1.2 Professional
# Stage-16.8 Advanced Translation Intelligence Freeze
# =====================================================

from __future__ import annotations

from .intelligence_contract import IntelligenceRuntimeContract
from .intelligence_freeze_events import (
    INTELLIGENCE_FREEZE_COMPLETED,
    INTELLIGENCE_FREEZE_STARTED,
    INTELLIGENCE_FREEZE_VALIDATED,
    IntelligenceFreezeEventBus,
)
from .intelligence_freeze_manifest import IntelligenceFreezeManifest
from .intelligence_freeze_result import IntelligenceFreezeResult
from .intelligence_runtime import IntelligenceRuntime
from .intelligence_runtime_context import IntelligenceRuntimeContext
from core.translation.intelligence_bridge import TranslationIntelligenceBridge


class IntelligenceFreezeValidator:
    """Validates the frozen Stage-16 intelligence layer without mutating runtime APIs."""

    stage = "Stage-16.8"
    name = "Advanced Translation Intelligence Freeze Validator"

    def __init__(self, *, event_bus: IntelligenceFreezeEventBus | None = None) -> None:
        self.event_bus = event_bus or IntelligenceFreezeEventBus()
        self.manifest = IntelligenceFreezeManifest()
        self.contract = IntelligenceRuntimeContract()

    def validate(self) -> IntelligenceFreezeResult:
        self.event_bus.emit(INTELLIGENCE_FREEZE_STARTED, manifest=self.manifest.to_dict())
        runtime = IntelligenceRuntime()
        runtime_result = runtime.analyze(
            IntelligenceRuntimeContext(
                source_text="鄭泰義沉默片刻，確認前後語境後才回答。",
                previous_texts=["伊萊站在門邊，語氣很平靜。"],
                terminology={"정태의": "鄭泰義"},
                character_refs=["鄭泰義", "伊萊"],
            )
        )
        bridge = TranslationIntelligenceBridge(runtime)
        hints = bridge.build_translation_hints(runtime_result)
        checks = {
            "manifest_frozen": self.manifest.frozen,
            "runtime_contract_present": hasattr(runtime, "analyze") and hasattr(runtime, "analyze_text"),
            "required_engines_present": set(self.contract.required_engines()).issubset(set(runtime.registry.names())),
            "runtime_result_schema_present": callable(getattr(runtime_result, "to_dict", None)),
            "selected_strategy_present": bool(runtime_result.selected_strategy),
            "bridge_hints_present": "selected_strategy" in hints and hints.get("stage") == "Stage-16.7",
            "compatibility_level_locked": self.contract.compatibility_level == "backward-compatible",
        }
        status = "PASS" if all(checks.values()) else "FAIL"
        self.event_bus.emit(INTELLIGENCE_FREEZE_VALIDATED, checks=checks, status=status)
        result = IntelligenceFreezeResult(
            status=status,
            frozen_modules=self.manifest.frozen_modules,
            contracts={k: str(v) for k, v in self.contract.to_dict().items()},
            checks=checks,
            notes=[
                "Stage-16 public API frozen through compatibility wrappers.",
                "Future stages must extend via new modules or registries, not by breaking frozen contracts.",
            ],
        )
        self.event_bus.emit(INTELLIGENCE_FREEZE_COMPLETED, result=result.to_dict())
        return result
