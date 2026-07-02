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
]
