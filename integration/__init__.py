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

from .extension_models import EXTENSION_FRAMEWORK_VERSION, EXTENSION_FRAMEWORK_STAGE, ExtensionManifest, ExtensionDescriptor, ExtensionCommand, ExtensionResult
from .extension_context import ExtensionContext
from .extension_events import ExtensionEvent, ExtensionEventBus
from .extension_registry import ExtensionRegistry
from .extension_dispatcher import ExtensionDispatcher
from .extension_loader import ExtensionLoader
from .extension_manifest import build_extension_manifest, load_extension_manifest
from .extension_manager import ExtensionManager

from .event_models import EVENT_BUS_VERSION, EVENT_BUS_STAGE, Event, EventSubscription, EventDispatchResult
from .event_context import EventContext
from .event_filters import EventFilter
from .event_registry import EventRegistry
from .event_dispatcher import EventDispatcher
from .event_publisher import EventPublisher
from .event_subscriber import EventSubscriber
from .event_bus import EventBus

from .service_models import SERVICE_CONTAINER_VERSION, SERVICE_CONTAINER_STAGE, ServiceLifetime, ServiceDescriptor, ServiceResolution
from .service_registry import ServiceRegistry
from .service_factory import ServiceFactory
from .service_scope import ServiceScope
from .service_resolver import ServiceResolver
from .service_provider import ServiceProvider
from .dependency_graph import DependencyGraph
from .service_container import ServiceContainer

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
    "EXTENSION_FRAMEWORK_VERSION",
    "EXTENSION_FRAMEWORK_STAGE",
    "ExtensionManifest",
    "ExtensionDescriptor",
    "ExtensionCommand",
    "ExtensionResult",
    "ExtensionContext",
    "ExtensionEvent",
    "ExtensionEventBus",
    "ExtensionRegistry",
    "ExtensionDispatcher",
    "ExtensionLoader",
    "build_extension_manifest",
    "load_extension_manifest",
    "ExtensionManager",
    "EVENT_BUS_VERSION",
    "EVENT_BUS_STAGE",
    "Event",
    "EventSubscription",
    "EventDispatchResult",
    "EventContext",
    "EventFilter",
    "EventRegistry",
    "EventDispatcher",
    "EventPublisher",
    "EventSubscriber",
    "EventBus",
    "SERVICE_CONTAINER_VERSION",
    "SERVICE_CONTAINER_STAGE",
    "ServiceLifetime",
    "ServiceDescriptor",
    "ServiceResolution",
    "ServiceRegistry",
    "ServiceFactory",
    "ServiceScope",
    "ServiceResolver",
    "ServiceProvider",
    "DependencyGraph",
    "ServiceContainer",
]
