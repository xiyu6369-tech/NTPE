"""Central Service Container for NTPE Stage-08.6."""
from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, Optional

from .dependency_graph import DependencyGraph
from .service_models import SERVICE_CONTAINER_STAGE, SERVICE_CONTAINER_VERSION, ServiceLifetime
from .service_provider import ServiceProvider
from .service_registry import ServiceRegistry
from .service_resolver import ServiceResolver
from .service_scope import ServiceScope

class ServiceContainer:
    version = SERVICE_CONTAINER_VERSION
    stage = SERVICE_CONTAINER_STAGE

    def __init__(self, *, registry: ServiceRegistry | None = None, metadata: Optional[Dict[str, Any]] = None) -> None:
        self.registry = registry or ServiceRegistry()
        self.resolver = ServiceResolver(self.registry)
        self.metadata = dict(metadata or {})
        self.runtime = None
        self.sdk = None
        self.cli = None
        self.plugin_manager = None
        self.extension_manager = None

    def register(self, name: str, factory: Callable[..., Any] | None = None, *, instance: Any | None = None, lifetime: ServiceLifetime | str = ServiceLifetime.TRANSIENT, dependencies: Optional[Iterable[str]] = None, metadata: Optional[Dict[str, Any]] = None) -> "ServiceContainer":
        self.registry.register(name, factory, instance=instance, lifetime=lifetime, dependencies=dependencies, metadata=metadata)
        return self

    def register_instance(self, name: str, instance: Any, *, metadata: Optional[Dict[str, Any]] = None) -> "ServiceContainer":
        self.registry.register_instance(name, instance, metadata=metadata)
        return self

    def resolve(self, name: str, *, scope: ServiceScope | None = None) -> Any:
        return self.resolver.resolve(name, scope=scope)

    def try_resolve(self, name: str, *, scope: ServiceScope | None = None):
        return self.resolver.try_resolve(name, scope=scope)

    def create_scope(self) -> ServiceScope:
        return ServiceScope()

    def provider(self) -> ServiceProvider:
        return ServiceProvider(self.resolver)

    def scoped_provider(self) -> ServiceProvider:
        return ServiceProvider(self.resolver, scope=self.create_scope())

    def validate(self) -> dict:
        return DependencyGraph(self.registry).validate()

    def bridge_runtime(self, runtime: Any) -> "ServiceContainer":
        self.runtime = runtime
        self.register_instance("runtime", runtime, metadata={"bridge": "runtime"})
        return self

    def bridge_sdk(self, sdk: Any) -> "ServiceContainer":
        self.sdk = sdk
        self.register_instance("sdk", sdk, metadata={"bridge": "sdk"})
        return self

    def bridge_cli(self, cli: Any) -> "ServiceContainer":
        self.cli = cli
        self.register_instance("cli", cli, metadata={"bridge": "cli"})
        return self

    def bridge_plugin_manager(self, plugin_manager: Any) -> "ServiceContainer":
        self.plugin_manager = plugin_manager
        self.register_instance("plugin_manager", plugin_manager, metadata={"bridge": "plugin"})
        return self

    def bridge_extension_manager(self, extension_manager: Any) -> "ServiceContainer":
        self.extension_manager = extension_manager
        self.register_instance("extension_manager", extension_manager, metadata={"bridge": "extension"})
        return self

    def manifest(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "stage": self.stage,
            "foundation_status": "frozen",
            "metadata": dict(self.metadata),
            "registry": self.registry.manifest(),
            "validation": self.validate(),
            "bridges": {
                "runtime_attached": self.runtime is not None,
                "sdk_attached": self.sdk is not None,
                "cli_attached": self.cli is not None,
                "plugin_attached": self.plugin_manager is not None,
                "extension_attached": self.extension_manager is not None,
            },
        }
