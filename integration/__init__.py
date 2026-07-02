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

from .bridge_models import BRIDGE_INTEGRATION_VERSION, BRIDGE_INTEGRATION_STAGE, BridgeCommand, BridgeResult, BridgeEndpoint
from .bridge_context import BridgeContext
from .bridge_events import BridgeEvent, BridgeEventBus
from .bridge_registry import BridgeRegistry
from .bridge_dispatcher import BridgeDispatcher
from .sdk_cli_bridge import SDKCLIBridge
from .bridge_manager import BridgeManager

from .plugin_models import PLUGIN_INTEGRATION_VERSION, PLUGIN_INTEGRATION_STAGE, IntegratedPluginDescriptor, PluginCommand, PluginIntegrationResult
from .plugin_events import PluginIntegrationEvent, PluginEventBus
from .plugin_context import PluginIntegrationContext
from .plugin_registry import PluginIntegrationRegistry
from .plugin_dispatcher import PluginDispatcher
from .plugin_bridge import PluginIntegrationBridge
from .plugin_manager import PluginIntegrationManager

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
    "BRIDGE_INTEGRATION_VERSION",
    "BRIDGE_INTEGRATION_STAGE",
    "BridgeCommand",
    "BridgeResult",
    "BridgeEndpoint",
    "BridgeContext",
    "BridgeEvent",
    "BridgeEventBus",
    "BridgeRegistry",
    "BridgeDispatcher",
    "SDKCLIBridge",
    "BridgeManager",
    "PLUGIN_INTEGRATION_VERSION",
    "PLUGIN_INTEGRATION_STAGE",
    "IntegratedPluginDescriptor",
    "PluginCommand",
    "PluginIntegrationResult",
    "PluginIntegrationEvent",
    "PluginEventBus",
    "PluginIntegrationContext",
    "PluginIntegrationRegistry",
    "PluginDispatcher",
    "PluginIntegrationBridge",
    "PluginIntegrationManager",
]
