"""NTPE Stage-10 Platform Services public surface."""
from .platform_models import (
    PLATFORM_SERVICES_VERSION,
    PLATFORM_SERVICES_STAGE,
    PlatformServiceStatus,
    PlatformServiceDescriptor,
    PlatformServiceResult,
)
from .platform_events import PLATFORM_EVENTS
from .service_registry import PlatformServiceRegistry
from .service_manager import PlatformServiceManager
from .service_host import PlatformServiceHost, create_platform_service_host
from .service_discovery import (
    PLATFORM_DISCOVERY_VERSION,
    PLATFORM_DISCOVERY_STAGE,
    ServiceDiscoveryQuery,
    ServiceDiscoveryResult,
    PlatformServiceDiscovery,
    create_service_discovery,
)
from .platform_config import (
    PLATFORM_CONFIG_VERSION,
    PLATFORM_CONFIG_STAGE,
    PlatformConfigEntry,
    PlatformConfigStore,
    PlatformServiceConfig,
    create_platform_config,
    create_service_config,
)
from .health_status import (
    PLATFORM_HEALTH_VERSION,
    PLATFORM_HEALTH_STAGE,
    PlatformHealthLevel,
    PlatformHealthCheckResult,
    PlatformHealthSnapshot,
)
from .health_monitor import PlatformServiceHealthMonitor, create_health_monitor
from .metrics_snapshot import (
    PLATFORM_METRICS_VERSION,
    PLATFORM_METRICS_STAGE,
    PlatformMetricPoint,
    PlatformMetricsSnapshot,
)
from .telemetry import (
    PLATFORM_TELEMETRY_VERSION,
    PLATFORM_TELEMETRY_STAGE,
    PlatformTelemetryEvent,
    PlatformTelemetryBuffer,
)
from .metrics import PlatformMetricsRegistry, create_metrics_registry

from .event_bus import (
    PLATFORM_EVENT_BUS_VERSION,
    PLATFORM_EVENT_BUS_STAGE,
    PlatformEvent,
    PlatformEventDelivery,
    PlatformEventSubscription,
    PlatformEventBus,
    create_event_bus,
)
from .event_bridge import PlatformEventBridge, create_event_bridge

from .lifecycle_hooks import (
    PLATFORM_LIFECYCLE_VERSION,
    PLATFORM_LIFECYCLE_STAGE,
    PlatformLifecyclePhase,
    PlatformLifecycleContext,
    PlatformLifecycleHook,
    PlatformLifecycleExecution,
    PlatformLifecycleHooks,
    create_lifecycle_hooks,
)
from .service_lifecycle import PlatformServiceLifecycle, create_service_lifecycle

__all__ = [
    "PLATFORM_SERVICES_VERSION",
    "PLATFORM_SERVICES_STAGE",
    "PlatformServiceStatus",
    "PlatformServiceDescriptor",
    "PlatformServiceResult",
    "PLATFORM_EVENTS",
    "PlatformServiceRegistry",
    "PlatformServiceManager",
    "PlatformServiceHost",
    "create_platform_service_host",
    "PLATFORM_CONFIG_VERSION",
    "PLATFORM_CONFIG_STAGE",
    "PlatformConfigEntry",
    "PlatformConfigStore",
    "PlatformServiceConfig",
    "create_platform_config",
    "create_service_config",
    "PLATFORM_DISCOVERY_VERSION",
    "PLATFORM_DISCOVERY_STAGE",
    "ServiceDiscoveryQuery",
    "ServiceDiscoveryResult",
    "PlatformServiceDiscovery",
    "create_service_discovery",
    "PLATFORM_HEALTH_VERSION",
    "PLATFORM_HEALTH_STAGE",
    "PlatformHealthLevel",
    "PlatformHealthCheckResult",
    "PlatformHealthSnapshot",
    "PlatformServiceHealthMonitor",
    "create_health_monitor",
    "PLATFORM_METRICS_VERSION",
    "PLATFORM_METRICS_STAGE",
    "PlatformMetricPoint",
    "PlatformMetricsSnapshot",
    "PLATFORM_TELEMETRY_VERSION",
    "PLATFORM_TELEMETRY_STAGE",
    "PlatformTelemetryEvent",
    "PlatformTelemetryBuffer",
    "PlatformMetricsRegistry",
    "create_metrics_registry",
    "PLATFORM_EVENT_BUS_VERSION",
    "PLATFORM_EVENT_BUS_STAGE",
    "PlatformEvent",
    "PlatformEventDelivery",
    "PlatformEventSubscription",
    "PlatformEventBus",
    "create_event_bus",
    "PlatformEventBridge",
    "create_event_bridge",
    "PLATFORM_LIFECYCLE_VERSION",
    "PLATFORM_LIFECYCLE_STAGE",
    "PlatformLifecyclePhase",
    "PlatformLifecycleContext",
    "PlatformLifecycleHook",
    "PlatformLifecycleExecution",
    "PlatformLifecycleHooks",
    "create_lifecycle_hooks",
    "PlatformServiceLifecycle",
    "create_service_lifecycle",
]
