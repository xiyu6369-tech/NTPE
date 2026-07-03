from pathlib import Path
import sys
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from stable_release.completion import (
    REQUIRED_FINALIZATION_ARTIFACTS,
    REQUIRED_PREPARATION_ARTIFACTS,
    REQUIRED_RC_ARTIFACTS,
    StableCompletionValidator,
    build_stable_completion_artifacts,
)


def seed_required_artifacts(root: Path) -> None:
    for name in REQUIRED_RC_ARTIFACTS:
        (root / name).write_text("PASS\n", encoding="utf-8")
    for name in REQUIRED_PREPARATION_ARTIFACTS:
        if name == "Stable_Release_Preparation_Manifest_1_0_0.json":
            (root / name).write_text(
                '{"stage":"STABLE.1","version":"1.0.0","passed":true}\n',
                encoding="utf-8",
            )
        else:
            (root / name).write_text("PASS\n", encoding="utf-8")
    for name in REQUIRED_FINALIZATION_ARTIFACTS:
        if name == "Stable_Release_Finalization_Manifest_1_0_0.json":
            (root / name).write_text(
                '{"stage":"STABLE.2","version":"1.0.0","status":"FINALIZED","passed":true}\n',
                encoding="utf-8",
            )
        else:
            (root / name).write_text("PASS\n", encoding="utf-8")


def main() -> int:
    print("NTPE 1.0 Stable Release Completion Test")
    print("=" * 47)
    with TemporaryDirectory() as temp:
        root = Path(temp)
        seed_required_artifacts(root)
        build_stable_completion_artifacts(root)
        result = StableCompletionValidator(root).run()
        checks = [
            ("Completion Valid", result["passed"]),
            ("Finalization Artifacts", result["validation"]["required_finalization_artifacts_valid"]),
            ("Preparation Artifacts", result["validation"]["required_preparation_artifacts_valid"]),
            ("RC Freeze Artifacts", result["validation"]["required_rc_artifacts_valid"]),
            ("Finalization Manifest", result["validation"]["finalization_manifest_valid"]),
            ("Release Metadata", result["validation"]["release_metadata_valid"]),
            ("Public API Preserved", not result["validation"]["public_api_changed"]),
            ("No Feature Change", not result["validation"]["product_feature_added"]),
        ]
        for label, ok in checks:
            print(f"{label:<24} {'PASS' if ok else 'FAIL'}")
        if all(ok for _, ok in checks):
            print("PASS")
            return 0
        print("FAIL")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
