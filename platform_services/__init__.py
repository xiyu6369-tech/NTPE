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
]

from .health_status import (
    PLATFORM_HEALTH_VERSION,
    PLATFORM_HEALTH_STAGE,
    PlatformHealthLevel,
    PlatformHealthCheckResult,
    PlatformHealthSnapshot,
)
from .health_monitor import PlatformServiceHealthMonitor, create_health_monitor
