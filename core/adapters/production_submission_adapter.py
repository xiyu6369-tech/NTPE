from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TranslationJobRequest:
    input_path: Path
    output_dir: Path
    quality_profile: str = "literary"
    speed: str = "balanced"
    model: str = "meta/llama-3.2-90b-vision-instruct"
    chunk_size: int = 1000
    resume: bool = True
    dry_run: bool = False
    max_retries: int = 3
    provider_attempts: int | None = None
    retry_base_seconds: float = 5.0
    qa_enabled: bool = True
    qa_fail_policy: str = "retry"
    min_length_ratio: float = 0.18
    max_korean_chars: int = 2
    max_repeated_lines: int = 2
    glossary_path: Path | None = None
    character_memory_path: Path | None = None
    quality_delivery_v83: bool = False
    quality_delivery_formats_v83: tuple[str, ...] = ("txt",)
    quality_integration_v72: bool = False
    quality_character_memory_v72: bool = False
    quality_context_scene_v72: bool = False
    quality_naturalness_v72: bool = False
    quality_integration_kill_switch_v72: bool = False
    simplified_chinese_policy: str = "normalize"
    progress_enabled: bool = True


@dataclass(frozen=True)
class SubmissionResult:
    job_id: str
    status: str
    cli_command: list[str]
    output_dir: Path
    process_pid: int | None = None
    error: str | None = None


@dataclass(frozen=True)
class SourceIdentity:
    source_path: Path
    source_hash: str
    file_size: int
    modified_time: float


class ProductionSubmissionAdapter:
    def __init__(self, root: Path | None = None, python_executable: str | None = None):
        self.root = root or Path(__file__).resolve().parents[2]
        self.python_executable = python_executable or sys.executable
        self.cli_entry = self.root / "ntpe_production_translate.py"

    def compute_source_identity(self, source_path: Path) -> SourceIdentity:
        stat = source_path.stat()
        content = source_path.read_bytes()
        source_hash = hashlib.sha256(content).hexdigest()[:16]
        return SourceIdentity(
            source_path=source_path,
            source_hash=source_hash,
            file_size=stat.st_size,
            modified_time=stat.st_mtime,
        )

    def _compute_config_fingerprint(self, request: TranslationJobRequest) -> str:
        """Compute deterministic fingerprint from translation and delivery configuration.
        
        Only includes fields that affect the translation output, not execution behavior.
        Excludes: resume, dry_run, max_retries, provider_attempts, retry_base_seconds, progress_enabled
        """
        identity_fields = {
            "model": request.model,
            "speed": request.speed,
            "chunk_size": request.chunk_size,
            "quality_profile": request.quality_profile,
            "qa_enabled": request.qa_enabled,
            "qa_fail_policy": request.qa_fail_policy,
            "min_length_ratio": request.min_length_ratio,
            "max_korean_chars": request.max_korean_chars,
            "max_repeated_lines": request.max_repeated_lines,
            "simplified_chinese_policy": request.simplified_chinese_policy,
            "glossary_path": str(request.glossary_path) if request.glossary_path else None,
            "character_memory_path": str(request.character_memory_path) if request.character_memory_path else None,
            "quality_delivery_v83": request.quality_delivery_v83,
            "quality_delivery_formats_v83": request.quality_delivery_formats_v83,
            "quality_integration_v72": request.quality_integration_v72,
            "quality_character_memory_v72": request.quality_character_memory_v72,
            "quality_context_scene_v72": request.quality_context_scene_v72,
            "quality_naturalness_v72": request.quality_naturalness_v72,
            "quality_integration_kill_switch_v72": request.quality_integration_kill_switch_v72,
        }
        # Canonical JSON serialization for deterministic hashing
        canonical = json.dumps(identity_fields, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]

    def _compute_submission_identity(self, source_identity: SourceIdentity, request: TranslationJobRequest) -> str:
        """Compute stable submission identity from source + config fingerprint."""
        config_fp = self._compute_config_fingerprint(request)
        return f"job_{source_identity.source_hash}_{config_fp}"

    def build_cli_argv(self, request: TranslationJobRequest) -> list[str]:
        argv = [
            str(self.python_executable),
            str(self.cli_entry),
            "txt",
            str(request.input_path),
            str(request.output_dir),
        ]

        if request.chunk_size != 1000:
            argv.extend(["--chunk-size", str(request.chunk_size)])
        if request.speed != "balanced":
            argv.extend(["--speed", request.speed])
        if request.model != "meta/llama-3.2-90b-vision-instruct":
            argv.extend(["--model", request.model])
        if not request.resume:
            argv.append("--no-resume")
        if request.dry_run:
            argv.append("--dry-run")
        if request.max_retries != 3:
            argv.extend(["--max-retries", str(request.max_retries)])
        if request.provider_attempts is not None:
            argv.extend(["--provider-attempts", str(request.provider_attempts)])
        if request.retry_base_seconds != 5.0:
            argv.extend(["--retry-base-seconds", str(request.retry_base_seconds)])
        if request.glossary_path:
            argv.extend(["--glossary", str(request.glossary_path)])
        if request.character_memory_path:
            argv.extend(["--character-memory", str(request.character_memory_path)])
        if not request.qa_enabled:
            argv.append("--no-qa")
        if request.qa_fail_policy != "retry":
            argv.extend(["--qa-fail-policy", request.qa_fail_policy])
        if request.min_length_ratio != 0.18:
            argv.extend(["--min-length-ratio", str(request.min_length_ratio)])
        if request.max_korean_chars != 2:
            argv.extend(["--max-korean-chars", str(request.max_korean_chars)])
        if request.max_repeated_lines != 2:
            argv.extend(["--max-repeated-lines", str(request.max_repeated_lines)])
        if request.quality_profile != "literary":
            argv.extend(["--profile", request.quality_profile])
        if request.simplified_chinese_policy != "normalize":
            argv.extend(["--simplified-chinese-policy", request.simplified_chinese_policy])
        if not request.progress_enabled:
            argv.append("--no-progress")
        if request.quality_integration_v72:
            argv.append("--quality-integration-v72")
        if request.quality_character_memory_v72:
            argv.append("--quality-character-memory-v72")
        if request.quality_context_scene_v72:
            argv.append("--quality-context-scene-v72")
        if request.quality_naturalness_v72:
            argv.append("--quality-naturalness-v72")
        if request.quality_integration_kill_switch_v72:
            argv.append("--quality-integration-kill-switch-v72")
        if request.quality_delivery_v83:
            argv.append("--quality-delivery-v83")
        if request.quality_delivery_formats_v83 != ("txt",):
            argv.extend(["--quality-delivery-formats-v83", *request.quality_delivery_formats_v83])

        return argv

    def submit(self, request: TranslationJobRequest) -> SubmissionResult:
        source_identity = self.compute_source_identity(request.input_path)
        job_id = self._compute_submission_identity(source_identity, request)

        request.output_dir.mkdir(parents=True, exist_ok=True)

        argv = self.build_cli_argv(request)

        env = os.environ.copy()
        env["NTPE_RUNTIME_PIPELINE"] = "runtime"

        try:
            proc = subprocess.Popen(
                argv,
                cwd=self.root,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            return SubmissionResult(
                job_id=job_id,
                status="submitted",
                cli_command=argv,
                output_dir=request.output_dir,
                process_pid=proc.pid,
            )
        except Exception as e:
            return SubmissionResult(
                job_id=job_id,
                status="failed",
                cli_command=argv,
                output_dir=request.output_dir,
                error=str(e),
            )

    def submit_sync(self, request: TranslationJobRequest, timeout: float | None = None) -> SubmissionResult:
        source_identity = self.compute_source_identity(request.input_path)
        job_id = self._compute_submission_identity(source_identity, request)

        request.output_dir.mkdir(parents=True, exist_ok=True)

        argv = self.build_cli_argv(request)

        env = os.environ.copy()
        env["NTPE_RUNTIME_PIPELINE"] = "runtime"

        try:
            result = subprocess.run(
                argv,
                cwd=self.root,
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            status = "completed" if result.returncode == 0 else "failed"
            return SubmissionResult(
                job_id=job_id,
                status=status,
                cli_command=argv,
                output_dir=request.output_dir,
                error=result.stderr if result.returncode != 0 else None,
            )
        except subprocess.TimeoutExpired as e:
            return SubmissionResult(
                job_id=job_id,
                status="timeout",
                cli_command=argv,
                output_dir=request.output_dir,
                error=f"Process timed out after {timeout}s",
            )
        except Exception as e:
            return SubmissionResult(
                job_id=job_id,
                status="failed",
                cli_command=argv,
                output_dir=request.output_dir,
                error=str(e),
            )