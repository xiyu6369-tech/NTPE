"""
RM-5.7.5 Knowledge Package Compatibility Layer.

This module provides the read-only interface for Translation Runtime
to access Frozen Knowledge Packages.
"""

from .provider import KnowledgePackageProvider, EntityQuery, create_provider
from .legacy_mapper import LegacyMapper, LegacyMapping, create_legacy_mapper
from .freeze_verifier import FreezeVerifier, VerificationResult, FreezeVerificationReport, verify_package

__all__ = [
    "KnowledgePackageProvider",
    "EntityQuery",
    "create_provider",
    "LegacyMapper",
    "LegacyMapping",
    "create_legacy_mapper",
    "FreezeVerifier",
    "VerificationResult",
    "FreezeVerificationReport",
    "verify_package",
]
