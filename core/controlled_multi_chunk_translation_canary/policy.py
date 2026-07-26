"""Frozen Stage 7.4 controlled multi-chunk canary policy."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

REQUEST_SCHEMA = "ntpe.controlled_multi_chunk_translation_request"
CHUNK_PLAN_SCHEMA = "ntpe.controlled_translation_chunk_plan"
CHUNK_EVIDENCE_SCHEMA = "ntpe.controlled_translation_chunk_evidence"
CHUNK_QUALITY_SCHEMA = "ntpe.controlled_translation_chunk_quality_assessment"
CHECKPOINT_SCHEMA = "ntpe.controlled_translation_checkpoint"
RESULT_SCHEMA = "ntpe.controlled_multi_chunk_translation_result"
VERIFICATION_SCHEMA = "ntpe.controlled_multi_chunk_translation_verification_result"
SCHEMA_VERSION = "1.0"

INTENT = (
    "translate_exactly_three_consecutive_authenticated_literary_chunks_"
    "sequentially_persist_each_successful_output_immediately_and_create_"
    "deterministic_checkpoints_without_formal_rollout"
)
SOURCE_FIXTURE_ID = "ntpe-stage74-golden-excerpt-ko-v1"
SOURCE_FIXTURE_PATH = (
    "tests/integration/controlled_multi_chunk_translation_canary/fixtures/"
    "stage74_original_ko.txt"
)
SOURCE_FINGERPRINT = (
    "53d96e78f7ce47c260185b55436844c1619a83d02c0feea11bef7793f28b9bea"
)
SOURCE_CHARACTER_COUNT = 1633
CHUNK_SIZE = 600
CHUNK_COUNT = 3
CHUNK_CHARACTER_COUNTS = (575, 540, 514)
CHUNK_FINGERPRINTS = (
    "5be537c45817ccc7aaf13de6c31fb4708c29a87e2e454949d60e33337feb726c",
    "542e4c34fccaac7a1a82692a584bc8a5203699d4b0821354387ba01807217dc2",
    "8527171c147f77e3715b3af9c040d9acf4b4318eb24b272d4051e363efff3791",
)
TARGET_LANGUAGE = "zh-TW"
PROFILE = "literary"
PROVIDER = "nvidia"
PROVIDER_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
PROVIDER_MODEL = "meta/llama-3.3-70b-instruct"
CREDENTIAL_ENV = "NVIDIA_API_KEY"
REAL_CANARY_GATE_ENV = "NTPE_STAGE74_REAL_PROVIDER_CANARY"
CONNECT_TIMEOUT_SECONDS = 10
READ_TIMEOUT_SECONDS = 180
REQUEST_CAP = 3
ATTEMPT_CAP = 3
OUTPUT_ROOT = "artifacts/controlled_multi_chunk_translation_stage743"
ARTIFACT_PARENT = "artifacts"
STAGE744_OUTPUT_ROOT = (
    "artifacts/controlled_multi_chunk_translation_stage744"
)
AUTHORIZED_ARTIFACT_ROOT_OVERRIDES = (STAGE744_OUTPUT_ROOT,)
PRIOR_CANARY_ROOTS = (OUTPUT_ROOT,)

CONTEXT_LIMIT = 160
COMBINED_BOUNDARY = "\n\n"
FIXED_NAMES = (("일레이", "伊萊"), ("정태의", "鄭泰義"))

DIALOGUE_PUNCTUATION_PROMPT_CONSTRAINT = """【Stage 7.4 對話標點約束】
- 人物說出口的對話一律使用成對的「」。
- 禁止用 ASCII 雙引號或彎雙引號 “ ” 表示人物對話。
- 保持敘述與句末標點自然；不得改寫撇號、度量符號或非對話引用。"""


class ArtifactRootValidationError(ValueError):
    """Raised before execution when a selected artifact root is unsafe."""


@dataclass(frozen=True)
class ArtifactRootSelection:
    repository_relative: str
    absolute_path: Path
    used_default: bool
    clean_root_required: bool
    root_exists: bool
    root_empty: bool


def select_artifact_root(
    repository_root: str | Path,
    override: str | None = None,
    *,
    clean_root_required: bool = False,
) -> ArtifactRootSelection:
    """Resolve the default or an allowlisted clean Stage 7.4 artifact root."""
    repository = Path(repository_root).resolve()
    artifacts = (repository / ARTIFACT_PARENT).resolve()
    if not artifacts.is_dir() or artifacts == repository:
        raise ArtifactRootValidationError("repository artifacts parent unavailable")

    used_default = override is None
    if used_default:
        raw = OUTPUT_ROOT
    elif not isinstance(override, str) or not override.strip():
        raise ArtifactRootValidationError("artifact root override must be non-empty")
    else:
        raw = override.strip()

    if "\x00" in raw:
        raise ArtifactRootValidationError("artifact root contains NUL")
    if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", raw):
        raise ArtifactRootValidationError("artifact root URI or drive path forbidden")
    if raw.startswith(("\\\\", "//", "\\?\\", "\\.\\")):
        raise ArtifactRootValidationError("network artifact root forbidden")

    relative_path = Path(raw)
    if relative_path.is_absolute():
        raise ArtifactRootValidationError(
            "artifact root must be repository-relative"
        )
    if any(part in {"", ".", ".."} for part in relative_path.parts):
        raise ArtifactRootValidationError("artifact root traversal forbidden")

    unresolved = repository / relative_path
    current = repository
    is_junction = getattr(os.path, "isjunction", lambda _path: False)
    for part in relative_path.parts:
        current = current / part
        if current.exists() and (
            current.is_symlink() or is_junction(str(current))
        ):
            raise ArtifactRootValidationError(
                "artifact root symlink or junction forbidden"
            )

    resolved = unresolved.resolve()
    try:
        canonical = resolved.relative_to(repository).as_posix()
    except ValueError as error:
        raise ArtifactRootValidationError(
            "artifact root outside repository forbidden"
        ) from error
    if resolved == artifacts or artifacts not in resolved.parents:
        raise ArtifactRootValidationError(
            "artifact root outside artifacts parent forbidden"
        )
    if any(part.lower() in {"input", "output"} for part in Path(canonical).parts):
        raise ArtifactRootValidationError("formal input/output path forbidden")
    if not used_default and canonical not in AUTHORIZED_ARTIFACT_ROOT_OVERRIDES:
        raise ArtifactRootValidationError("artifact root override not authorized")
    if clean_root_required and canonical in PRIOR_CANARY_ROOTS:
        raise ArtifactRootValidationError("prior canary root forbidden in clean mode")
    if resolved.exists() and not resolved.is_dir():
        raise ArtifactRootValidationError("artifact root must be a directory")

    root_exists = resolved.exists()
    root_empty = not root_exists or not any(resolved.iterdir())
    if clean_root_required and not root_empty:
        raise ArtifactRootValidationError(
            "clean artifact root must be nonexistent or empty"
        )
    return ArtifactRootSelection(
        repository_relative=canonical,
        absolute_path=resolved,
        used_default=used_default,
        clean_root_required=clean_root_required,
        root_exists=root_exists,
        root_empty=root_empty,
    )
