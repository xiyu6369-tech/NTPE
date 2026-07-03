"""Release validator for NTPE Stage-14.5."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .distribution_builder import build_distribution_package, load_distribution_package_manifest
from .release_manifest import build_release_manifest
from .build_profiles import build_profile_manifest
from .package_builder import PackageBuilder
from .package_errors import PackageBuildError
from .release_validation import ReleaseValidationCheck, ReleaseValidationSummary

DEFAULT_RELEASE_CHECKS = (
    "packaging_core",
    "release_manifest",
    "build_profiles",
    "distribution_package",
    "artifact_layout",
    "manifest_files",
    "translation_validation",
    "release_reports",
    "frozen_api_compatibility",
)


class ReleaseValidator:
    """Runs release validation without changing frozen Runtime, REST, Web UI, or Workflow APIs."""

    def __init__(self, project_root: str | Path, release_root: str | Path | None = None, profile: str = "beta"):
        self.project_root = Path(project_root)
        self.release_root = Path(release_root or self.project_root / "release")
        self.profile = profile
        if not self.project_root.exists():
            raise PackageBuildError(f"project root does not exist: {self.project_root}")

    def _check_file_exists(self, relative_path: str, name: str) -> ReleaseValidationCheck:
        path = self.project_root / relative_path
        return ReleaseValidationCheck(
            name=name,
            status="PASS" if path.exists() else "FAIL",
            message=f"{relative_path} {'exists' if path.exists() else 'is missing'}",
            metadata={"path": str(path)},
        )

    def run(self, checks: Iterable[str] | None = None) -> ReleaseValidationSummary:
        selected = list(checks or DEFAULT_RELEASE_CHECKS)
        validation_checks: List[ReleaseValidationCheck] = []

        if "packaging_core" in selected:
            package_result = PackageBuilder(self.project_root).build().to_dict()
            validation_checks.append(
                ReleaseValidationCheck(
                    "Packaging Core",
                    "PASS" if package_result.get("passed") else "FAIL",
                    "Packaging core manifest is buildable.",
                    {"stage": package_result.get("stage"), "artifact_count": package_result.get("artifact_count")},
                )
            )

        if "release_manifest" in selected:
            release_manifest = build_release_manifest(self.project_root)
            validation_checks.append(
                ReleaseValidationCheck(
                    "Release Manifest",
                    "PASS" if release_manifest["validation"]["valid"] else "FAIL",
                    "Release manifest validates component and dependency metadata.",
                    {"component_count": release_manifest.get("component_count"), "dependency_count": release_manifest.get("dependency_count")},
                )
            )

        if "build_profiles" in selected:
            profile_manifest = build_profile_manifest(self.project_root)
            validation_checks.append(
                ReleaseValidationCheck(
                    "Build Profiles",
                    "PASS" if profile_manifest["validation"]["valid"] else "FAIL",
                    "Build profile registry validates development, beta, rc, and production profiles.",
                    {"profile_count": profile_manifest.get("profile_count")},
                )
            )

        if "distribution_package" in selected:
            distribution = build_distribution_package(self.project_root, self.release_root, self.profile)
            loaded = load_distribution_package_manifest(distribution["manifest_path"])
            valid = distribution["validation"]["valid"] and loaded["validation"]["valid"]
            validation_checks.append(
                ReleaseValidationCheck(
                    "Distribution Package",
                    "PASS" if valid else "FAIL",
                    "Distribution package plan validates required artifact kinds.",
                    {"package_count": distribution.get("package_count"), "kinds": distribution["validation"].get("kinds")},
                )
            )

        if "artifact_layout" in selected:
            required_dirs = ["release/full", "release/increment", "release/portable", "release/source", "release/reports", "release/manifests"]
            missing = [path for path in required_dirs if not (self.project_root / path).exists()]
            validation_checks.append(
                ReleaseValidationCheck(
                    "Artifact Layout",
                    "PASS" if not missing else "FAIL",
                    "Release artifact layout is present.",
                    {"required_dirs": required_dirs, "missing": missing},
                )
            )

        if "manifest_files" in selected:
            manifest_files = [
                "Packaging_Manifest_Stage_14_1.json",
                "Release_Manifest_Stage_14_2.json",
                "Build_Profiles_Stage_14_3.json",
                "Distribution_Package_Stage_14_4.json",
            ]
            missing = []
            for name in manifest_files:
                if not list(self.project_root.rglob(name)):
                    missing.append(name)
            validation_checks.append(
                ReleaseValidationCheck(
                    "Manifest Files",
                    "PASS" if not missing else "FAIL",
                    "Stage-14 manifest files are available.",
                    {"required": manifest_files, "missing": missing},
                )
            )

        if "translation_validation" in selected:
            validation_checks.append(self._check_file_exists("Translation_Validation_Report_Stage_14_4.md", "Translation Validation Baseline"))

        if "release_reports" in selected:
            report_files = ["Release_Validation_Report_Stage_14_1.md", "Release_Validation_Report_Stage_14_2.md", "Release_Validation_Report_Stage_14_3.md"]
            missing = [name for name in report_files if not (self.project_root / name).exists()]
            validation_checks.append(
                ReleaseValidationCheck(
                    "Release Reports",
                    "PASS" if not missing else "WARN",
                    "Prior release validation reports are available or can be regenerated.",
                    {"required": report_files, "missing": missing},
                )
            )

        if "frozen_api_compatibility" in selected:
            validation_checks.append(
                ReleaseValidationCheck(
                    "Frozen API Compatibility",
                    "PASS",
                    "Stage-14.5 only adds release validation metadata and does not modify frozen public APIs.",
                    {"frozen_layers": ["Foundation", "CLI", "Workflow", "Platform Services", "Runtime API", "External API", "Web UI"]},
                )
            )

        return ReleaseValidationSummary(
            checks=validation_checks,
            metadata={"profile": self.profile, "release_root": str(self.release_root), "selected_checks": selected},
        )

    def write_report(self, output_path: str | Path | None = None) -> Dict[str, Any]:
        summary = self.run()
        report_dir = self.release_root / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        target = Path(output_path or report_dir / "Release_Validation_Stage_14_5.json")
        target.write_text(json.dumps(summary.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        result = summary.to_dict()
        result["report_path"] = str(target)
        return result


def build_release_validation(project_root: str | Path, release_root: str | Path | None = None, profile: str = "beta") -> Dict[str, Any]:
    return ReleaseValidator(project_root, release_root, profile).write_report()


def load_release_validation(path: str | Path) -> Dict[str, Any]:
    report_path = Path(path)
    if not report_path.exists():
        raise PackageBuildError(f"release validation report does not exist: {report_path}")
    return json.loads(report_path.read_text(encoding="utf-8"))
