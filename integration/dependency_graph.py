"""Dependency graph validation for NTPE Stage-08.6."""
from __future__ import annotations

from typing import Dict, List, Set

from .service_registry import ServiceRegistry

class DependencyGraph:
    def __init__(self, registry: ServiceRegistry) -> None:
        self.registry = registry

    def graph(self) -> Dict[str, list[str]]:
        return {desc.name: list(desc.dependencies) for desc in self.registry.descriptors()}

    def missing_dependencies(self) -> Dict[str, list[str]]:
        names = set(self.registry.names())
        return {name: [dep for dep in deps if dep not in names] for name, deps in self.graph().items() if any(dep not in names for dep in deps)}

    def has_cycles(self) -> bool:
        graph = self.graph()
        visiting: Set[str] = set()
        visited: Set[str] = set()
        def visit(node: str) -> bool:
            if node in visiting:
                return True
            if node in visited:
                return False
            visiting.add(node)
            for dep in graph.get(node, []):
                if dep in graph and visit(dep):
                    return True
            visiting.remove(node)
            visited.add(node)
            return False
        return any(visit(node) for node in graph)

    def validate(self) -> dict:
        missing = self.missing_dependencies()
        cycles = self.has_cycles()
        return {"ok": not missing and not cycles, "missing": missing, "cycles": cycles, "graph": self.graph()}
