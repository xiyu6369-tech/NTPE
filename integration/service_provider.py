"""Service provider facade for NTPE Stage-08.6."""
from __future__ import annotations

from typing import Any

from .service_resolver import ServiceResolver
from .service_scope import ServiceScope

class ServiceProvider:
    def __init__(self, resolver: ServiceResolver, *, scope: ServiceScope | None = None) -> None:
        self.resolver = resolver
        self.scope = scope

    def get(self, name: str) -> Any:
        return self.resolver.resolve(name, scope=self.scope)

    def try_get(self, name: str):
        return self.resolver.try_resolve(name, scope=self.scope)

    def create_scope(self) -> "ServiceProvider":
        return ServiceProvider(self.resolver, scope=ServiceScope())
