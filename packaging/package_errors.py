"""Packaging error model for NTPE Stage-14.1."""
from __future__ import annotations


class PackagingError(Exception):
    """Base exception for packaging layer failures."""


class PackageLayoutError(PackagingError):
    """Raised when a release layout cannot be created or validated."""


class ArtifactError(PackagingError):
    """Raised when an artifact cannot be registered or resolved."""


class PackageBuildError(PackagingError):
    """Raised when package build validation fails."""
