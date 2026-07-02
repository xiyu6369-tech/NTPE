"""NTPE Stage-08 Integration public surface."""
from .manifest import INTEGRATION_VERSION, INTEGRATION_STAGE, build_integration_manifest
from .contracts import IntegrationComponent, IntegrationResult
from .registry import IntegrationRegistry
from .context import IntegrationContext
from .core import IntegrationCore, create_integration_core

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
]
