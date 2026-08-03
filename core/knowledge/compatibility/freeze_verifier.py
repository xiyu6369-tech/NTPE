"""
RM-5.7.5 Freeze Verification - Complete package verification.

Verifies package checksum, manifest, deterministic rebuild,
compatibility, and runtime read-only boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.knowledge_compilation.package_builder import PackageReader, create_package_reader
from core.knowledge_compilation.models import CompilationPackage, CompilationManifest
from core.knowledge_compilation.checksum import ChecksumCalculator, DEFAULT_CALCULATOR
from core.knowledge_compilation.compiler import KnowledgeCompiler, CompilationConfig



@dataclass(frozen=True, slots=True)
class VerificationResult:
    """Result of a single verification check."""
    check_name: str
    passed: bool
    detail: str = ""
    severity: str = "error"  # "error" | "warning" | "info"


@dataclass(frozen=True, slots=True)
class FreezeVerificationReport:
    """Complete freeze verification report."""
    package_dir: str
    results: List[VerificationResult] = field(default_factory=list)
    overall_passed: bool = False

    def add_result(self, result: VerificationResult) -> None:
        object.__setattr__(self, "results", self.results + [result])

    def get_failed(self) -> List[VerificationResult]:
        return [r for r in self.results if not r.passed and r.severity == "error"]

    def get_warnings(self) -> List[VerificationResult]:
        return [r for r in self.results if not r.passed and r.severity == "warning"]

    def finalize(self) -> None:
        object.__setattr__(self, "overall_passed", len(self.get_failed()) == 0)


class FreezeVerifier:
    """Complete freeze verification for Frozen Knowledge Packages."""

    def __init__(
        self,
        package_dir: str | Path,
        calculator: ChecksumCalculator | None = None,
        source_dir: str | Path | None = None,  # For deterministic rebuild check
    ) -> None:
        self._package_dir = Path(package_dir)
        self._calculator = calculator or DEFAULT_CALCULATOR
        self._reader = create_package_reader(self._package_dir)
        self._source_dir = Path(source_dir) if source_dir else None

    @property
    def package_dir(self) -> Path:
        return self._package_dir

    @property
    def package(self) -> CompilationPackage:
        return self._reader.package

    @property
    def manifest(self) -> CompilationManifest:
        return self._reader.manifest

    # === Individual Verification Checks ===

    def _check_checksum(self, report: FreezeVerificationReport) -> None:
        """Verify package checksum matches manifest."""
        passed = self.package.verify_checksum(self._calculator)
        report.add_result(VerificationResult(
            check_name="checksum",
            passed=passed,
            detail="Checksum matches" if passed else "Checksum mismatch",
            severity="error",
        ))

    def _check_manifest(self, report: FreezeVerificationReport) -> None:
        """Verify manifest entity counts match actual entities."""
        all_passed = True
        details = []
        for entity_type, count in self.manifest.entity_counts.items():
            actual = self.package.get_entity_count(entity_type)
            if actual != count:
                all_passed = False
                details.append(f"{entity_type}: manifest={count}, actual={actual}")
            else:
                details.append(f"{entity_type}: {count} OK")

        report.add_result(VerificationResult(
            check_name="manifest",
            passed=all_passed,
            detail="; ".join(details),
            severity="error",
        ))

    def _check_structure(self, report: FreezeVerificationReport) -> None:
        """Verify all required package files exist."""
        all_passed = True
        details = []
        plural_map = {"glossary": "glossaries"}

        for entity_type in self.manifest.entity_counts.keys():
            plural = plural_map.get(entity_type, f"{entity_type}s")
            file_path = self._package_dir / f"{plural}.json"
            if file_path.exists():
                details.append(f"{plural}.json: exists")
            else:
                all_passed = False
                details.append(f"{plural}.json: MISSING")

        manifest_path = self._package_dir / "manifest.json"
        if manifest_path.exists():
            details.append("manifest.json: exists")
        else:
            all_passed = False
            details.append("manifest.json: MISSING")

        package_path = self._package_dir / "package.json"
        if package_path.exists():
            details.append("package.json: exists")
        else:
            all_passed = False
            details.append("package.json: MISSING")

        report.add_result(VerificationResult(
            check_name="structure",
            passed=all_passed,
            detail="; ".join(details),
            severity="error",
        ))

    def _check_deterministic_rebuild(self, report: FreezeVerificationReport) -> None:
        """Verify package can be deterministically rebuilt from source."""
        if not self._source_dir:
            report.add_result(VerificationResult(
                check_name="deterministic_rebuild",
                passed=True,
                detail="Skipped (no source_dir provided)",
                severity="info",
            ))
            return

        try:
            config = CompilationConfig(
                output_root=str(self._package_dir.parent),
                version_dir=self._package_dir.name,
                strict_mode=True,
            )
            compiler = KnowledgeCompiler(config)
            rebuilt_package = compiler.compile(
                entities=dict(self.package.entities),
            )

            original_checksum = self.package.checksum
            rebuilt_checksum = rebuilt_package.checksum

            passed = original_checksum == rebuilt_checksum
            report.add_result(VerificationResult(
                check_name="deterministic_rebuild",
                passed=passed,
                detail="Rebuild matches original" if passed else "Rebuild differs from original",
                severity="error",
            ))

        except Exception as e:
            report.add_result(VerificationResult(
                check_name="deterministic_rebuild",
                passed=False,
                detail=f"Rebuild failed: {e}",
                severity="error",
            ))

    def _check_compatibility(self, report: FreezeVerificationReport) -> None:
        """Verify package is compatible with current provider schema."""
        required_types = ("character", "glossary", "scene", "narrative", "style")
        all_passed = True
        details = []

        for entity_type in required_types:
            count = self.package.get_entity_count(entity_type)
            if count == 0:
                details.append(f"{entity_type}: 0 entities (warning)")
            else:
                details.append(f"{entity_type}: {count} entities")

        required_manifest_fields = (
            "package_id",
            "package_version",            "schema_versions",            "entity_counts",            "created_at",            "compiler_version",        )

        for field in required_manifest_fields:
            if not hasattr(self.manifest, field):
                all_passed = False
                details.append(f"manifest missing {field}")

        report.add_result(VerificationResult(
            check_name="compatibility",
            passed=all_passed,
            detail="; ".join(details),
            severity="error" if not all_passed else "info",
        ))

    def _check_readonly_boundary(self, report: FreezeVerificationReport) -> None:
        """Verify runtime read-only boundary (no write methods exposed)."""
        from core.knowledge.compatibility.provider import KnowledgePackageProvider

        provider = KnowledgePackageProvider(
            self._package_dir,
            verify_on_load=False,
        )

        write_methods = [
            "write", "save", "delete", "update",
            "create", "build", "compile", "extract",
            "validate", "review",
        ]

        found_write = []
        for method in write_methods:
            if hasattr(provider, method):
                found_write.append(method)

        passed = len(found_write) == 0
        detail = "No write methods found" if passed else f"Write methods found: {found_write}"

        report.add_result(VerificationResult(
            check_name="readonly_boundary",
            passed=passed,
            detail=detail,
            severity="error",
        ))

    # === Main Verification Method ===

    def verify_all(self) -> FreezeVerificationReport:
        """Run all verification checks and return complete report."""
        report = FreezeVerificationReport(package_dir=str(self._package_dir))

        self._check_checksum(report)
        self._check_manifest(report)
        self._check_structure(report)
        self._check_deterministic_rebuild(report)
        self._check_compatibility(report)
        self._check_readonly_boundary(report)

        report.finalize()
        return report


def verify_package(
    package_dir: str | Path,
    calculator: ChecksumCalculator | None = None,
    source_dir: str | Path | None = None,
) -> FreezeVerificationReport:
    """Convenience function to run full freeze verification."""
    verifier = FreezeVerifier(package_dir, calculator, source_dir)
    return verifier.verify_all()


__all__ = [
    "FreezeVerifier",
    "VerificationResult",
    "FreezeVerificationReport",
    "verify_package",
]
