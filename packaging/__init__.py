"""NTPE packaging layer.

Stage-14.1 introduces the packaging core without changing frozen Runtime,
External API, Web UI, Workflow, Integration, CLI, SDK, or Foundation APIs.
"""
from .artifact_manager import Artifact, ArtifactManager
from .package_builder import PackageBuilder, PackageBuildResult, load_packaging_manifest
from .package_errors import ArtifactError, PackageBuildError, PackageLayoutError, PackagingError
from .package_layout import DEFAULT_RELEASE_DIRECTORIES, PackageLayout
from .package_metadata import PackageMetadata

PACKAGING_STAGE = "Stage-14.1"
PACKAGING_LAYER_FROZEN_DEPENDENCIES = (
    "Foundation v1.0",
    "CLI",
    "Integration",
    "Workflow",
    "Platform Services",
    "Runtime API",
    "External API",
    "Web UI",
)

__all__ = [
    "Artifact",
    "ArtifactManager",
    "PackageBuilder",
    "PackageBuildResult",
    "PackageMetadata",
    "PackageLayout",
    "DEFAULT_RELEASE_DIRECTORIES",
    "PackagingError",
    "PackageLayoutError",
    "ArtifactError",
    "PackageBuildError",
    "load_packaging_manifest",
    "PACKAGING_STAGE",
    "PACKAGING_LAYER_FROZEN_DEPENDENCIES",
]

# Stage-14.2 Release Manifest exports
from .component_manifest import ComponentManifest, ReleaseComponent
from .dependency_manifest import DependencyManifest, ReleaseDependency
from .manifest_schema import ManifestSchema, RELEASE_MANIFEST_REQUIRED_FIELDS
from .release_manifest import ReleaseManifest, build_release_manifest, load_release_manifest

PACKAGING_STAGE = "Stage-14.2"
__all__ += [
    "ReleaseComponent",
    "ComponentManifest",
    "ReleaseDependency",
    "DependencyManifest",
    "ManifestSchema",
    "RELEASE_MANIFEST_REQUIRED_FIELDS",
    "ReleaseManifest",
    "build_release_manifest",
    "load_release_manifest",
]

# Stage-14.3 Build Profiles exports
from .build_profile import BuildProfile
from .build_profiles import (
    DEFAULT_PROFILE_ORDER,
    BuildProfileRegistry,
    build_profile_manifest,
    default_build_profiles,
    load_build_profiles,
)

PACKAGING_STAGE = "Stage-14.3"
__all__ += [
    "BuildProfile",
    "BuildProfileRegistry",
    "DEFAULT_PROFILE_ORDER",
    "default_build_profiles",
    "build_profile_manifest",
    "load_build_profiles",
]
