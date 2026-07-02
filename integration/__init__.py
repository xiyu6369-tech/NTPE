"""NTPE Stage-08 Integration public surface."""
from .manifest import INTEGRATION_VERSION, INTEGRATION_STAGE, build_integration_manifest
from .contracts import IntegrationComponent, IntegrationResult
from .registry import IntegrationRegistry
from .context import IntegrationContext
from .core import IntegrationCore, create_integration_core
from .runtime_models import RUNTIME_INTEGRATION_VERSION, RUNTIME_INTEGRATION_STAGE, RuntimeMetadata, RuntimeCommand, RuntimeExecutionResult
from .runtime_events import RuntimeEvent, RuntimeEventBridge
from .runtime_context import RuntimeContext
from .runtime_registry import RuntimeRegistry
from .runtime_dispatcher import RuntimeDispatcher
from .runtime_bridge import RuntimeBridge
from .runtime_manager import RuntimeManager

__all__ = [
    "INTEGRATION_VERSION",
    "INTEGRATION_STAGE",
    "build_integration_manifest",
    "IntegrationComponent",
    "IntegrationResult",
    "IntegrationRegistry",
    "IntegrationContext",
    "IntegrationCore",
    "create_integration_core",
    "RUNTIME_INTEGRATION_VERSION",
    "RUNTIME_INTEGRATION_STAGE",
    "RuntimeMetadata",
    "RuntimeCommand",
    "RuntimeExecutionResult",
    "RuntimeEvent",
    "RuntimeEventBridge",
    "RuntimeContext",
    "RuntimeRegistry",
    "RuntimeDispatcher",
    "RuntimeBridge",
    "RuntimeManager",
]
