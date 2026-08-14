"""Contract tests for ProductionSubmissionAdapter."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.adapters.production_submission_adapter import (
    ProductionSubmissionAdapter,
    SourceIdentity,
    SubmissionResult,
    TranslationJobRequest,
)


class TestSourceIdentity:
    def test_compute_source_identity_deterministic(self, tmp_path: Path):
        source = tmp_path / "test.txt"
        source.write_text("Hello world")

        adapter = ProductionSubmissionAdapter()
        identity1 = adapter.compute_source_identity(source)
        identity2 = adapter.compute_source_identity(source)

        assert identity1.source_hash == identity2.source_hash
        assert identity1.file_size == identity2.file_size
        assert identity1.source_path == source

    def test_source_hash_is_sha256_truncated(self, tmp_path: Path):
        source = tmp_path / "test.txt"
        content = "Test content for hashing"
        source.write_text(content)

        adapter = ProductionSubmissionAdapter()
        identity = adapter.compute_source_identity(source)

        expected_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        assert identity.source_hash == expected_hash

    def test_source_identity_includes_metadata(self, tmp_path: Path):
        source = tmp_path / "test.txt"
        source.write_text("Content")

        adapter = ProductionSubmissionAdapter()
        identity = adapter.compute_source_identity(source)

        assert isinstance(identity, SourceIdentity)
        assert identity.source_path == source
        assert len(identity.source_hash) == 16
        assert identity.file_size > 0
        assert identity.modified_time > 0


class TestBuildCliArgv:
    def test_default_argv_construction(self, tmp_path: Path):
        adapter = ProductionSubmissionAdapter()
        request = TranslationJobRequest(
            input_path=tmp_path / "input.txt",
            output_dir=tmp_path / "output",
        )

        argv = adapter.build_cli_argv(request)

        assert argv[0] == adapter.python_executable
        assert argv[1] == str(adapter.cli_entry)
        assert argv[2] == "txt"
        assert argv[3] == str(request.input_path)
        assert argv[4] == str(request.output_dir)

    def test_custom_chunk_size(self, tmp_path: Path):
        adapter = ProductionSubmissionAdapter()
        request = TranslationJobRequest(
            input_path=tmp_path / "input.txt",
            output_dir=tmp_path / "output",
            chunk_size=500,
        )

        argv = adapter.build_cli_argv(request)
        assert "--chunk-size" in argv
        assert argv[argv.index("--chunk-size") + 1] == "500"

    def test_custom_speed(self, tmp_path: Path):
        adapter = ProductionSubmissionAdapter()
        request = TranslationJobRequest(
            input_path=tmp_path / "input.txt",
            output_dir=tmp_path / "output",
            speed="fast",
        )

        argv = adapter.build_cli_argv(request)
        assert "--speed" in argv
        assert argv[argv.index("--speed") + 1] == "fast"

    def test_custom_model(self, tmp_path: Path):
        adapter = ProductionSubmissionAdapter()
        request = TranslationJobRequest(
            input_path=tmp_path / "input.txt",
            output_dir=tmp_path / "output",
            model="custom/model",
        )

        argv = adapter.build_cli_argv(request)
        assert "--model" in argv
        assert argv[argv.index("--model") + 1] == "custom/model"

    def test_no_resume_flag(self, tmp_path: Path):
        adapter = ProductionSubmissionAdapter()
        request = TranslationJobRequest(
            input_path=tmp_path / "input.txt",
            output_dir=tmp_path / "output",
            resume=False,
        )

        argv = adapter.build_cli_argv(request)
        assert "--no-resume" in argv

    def test_dry_run_flag(self, tmp_path: Path):
        adapter = ProductionSubmissionAdapter()
        request = TranslationJobRequest(
            input_path=tmp_path / "input.txt",
            output_dir=tmp_path / "output",
            dry_run=True,
        )

        argv = adapter.build_cli_argv(request)
        assert "--dry-run" in argv

    def test_max_retries(self, tmp_path: Path):
        adapter = ProductionSubmissionAdapter()
        request = TranslationJobRequest(
            input_path=tmp_path / "input.txt",
            output_dir=tmp_path / "output",
            max_retries=5,
        )

        argv = adapter.build_cli_argv(request)
        assert "--max-retries" in argv
        assert argv[argv.index("--max-retries") + 1] == "5"

    def test_provider_attempts(self, tmp_path: Path):
        adapter = ProductionSubmissionAdapter()
        request = TranslationJobRequest(
            input_path=tmp_path / "input.txt",
            output_dir=tmp_path / "output",
            provider_attempts=2,
        )

        argv = adapter.build_cli_argv(request)
        assert "--provider-attempts" in argv
        assert argv[argv.index("--provider-attempts") + 1] == "2"

    def test_retry_base_seconds(self, tmp_path: Path):
        adapter = ProductionSubmissionAdapter()
        request = TranslationJobRequest(
            input_path=tmp_path / "input.txt",
            output_dir=tmp_path / "output",
            retry_base_seconds=10.0,
        )

        argv = adapter.build_cli_argv(request)
        assert "--retry-base-seconds" in argv
        assert argv[argv.index("--retry-base-seconds") + 1] == "10.0"

    def test_glossary_path(self, tmp_path: Path):
        adapter = ProductionSubmissionAdapter()
        glossary = tmp_path / "glossary.json"
        request = TranslationJobRequest(
            input_path=tmp_path / "input.txt",
            output_dir=tmp_path / "output",
            glossary_path=glossary,
        )

        argv = adapter.build_cli_argv(request)
        assert "--glossary" in argv
        assert argv[argv.index("--glossary") + 1] == str(glossary)

    def test_character_memory_path(self, tmp_path: Path):
        adapter = ProductionSubmissionAdapter()
        char_mem = tmp_path / "char_memory.json"
        request = TranslationJobRequest(
            input_path=tmp_path / "input.txt",
            output_dir=tmp_path / "output",
            character_memory_path=char_mem,
        )

        argv = adapter.build_cli_argv(request)
        assert "--character-memory" in argv
        assert argv[argv.index("--character-memory") + 1] == str(char_mem)

    def test_no_qa_flag(self, tmp_path: Path):
        adapter = ProductionSubmissionAdapter()
        request = TranslationJobRequest(
            input_path=tmp_path / "input.txt",
            output_dir=tmp_path / "output",
            qa_enabled=False,
        )

        argv = adapter.build_cli_argv(request)
        assert "--no-qa" in argv

    def test_qa_fail_policy(self, tmp_path: Path):
        adapter = ProductionSubmissionAdapter()
        request = TranslationJobRequest(
            input_path=tmp_path / "input.txt",
            output_dir=tmp_path / "output",
            qa_fail_policy="fail",
        )

        argv = adapter.build_cli_argv(request)
        assert "--qa-fail-policy" in argv
        assert argv[argv.index("--qa-fail-policy") + 1] == "fail"

    def test_min_length_ratio(self, tmp_path: Path):
        adapter = ProductionSubmissionAdapter()
        request = TranslationJobRequest(
            input_path=tmp_path / "input.txt",
            output_dir=tmp_path / "output",
            min_length_ratio=0.2,
        )

        argv = adapter.build_cli_argv(request)
        assert "--min-length-ratio" in argv
        assert argv[argv.index("--min-length-ratio") + 1] == "0.2"

    def test_max_korean_chars(self, tmp_path: Path):
        adapter = ProductionSubmissionAdapter()
        request = TranslationJobRequest(
            input_path=tmp_path / "input.txt",
            output_dir=tmp_path / "output",
            max_korean_chars=5,
        )

        argv = adapter.build_cli_argv(request)
        assert "--max-korean-chars" in argv
        assert argv[argv.index("--max-korean-chars") + 1] == "5"

    def test_max_repeated_lines(self, tmp_path: Path):
        adapter = ProductionSubmissionAdapter()
        request = TranslationJobRequest(
            input_path=tmp_path / "input.txt",
            output_dir=tmp_path / "output",
            max_repeated_lines=3,
        )

        argv = adapter.build_cli_argv(request)
        assert "--max-repeated-lines" in argv
        assert argv[argv.index("--max-repeated-lines") + 1] == "3"

    def test_quality_profile(self, tmp_path: Path):
        adapter = ProductionSubmissionAdapter()
        request = TranslationJobRequest(
            input_path=tmp_path / "input.txt",
            output_dir=tmp_path / "output",
            quality_profile="fast",
        )

        argv = adapter.build_cli_argv(request)
        assert "--profile" in argv
        assert argv[argv.index("--profile") + 1] == "fast"

    def test_simplified_chinese_policy(self, tmp_path: Path):
        adapter = ProductionSubmissionAdapter()
        request = TranslationJobRequest(
            input_path=tmp_path / "input.txt",
            output_dir=tmp_path / "output",
            simplified_chinese_policy="keep",
        )

        argv = adapter.build_cli_argv(request)
        assert "--simplified-chinese-policy" in argv
        assert argv[argv.index("--simplified-chinese-policy") + 1] == "keep"

    def test_no_progress_flag(self, tmp_path: Path):
        adapter = ProductionSubmissionAdapter()
        request = TranslationJobRequest(
            input_path=tmp_path / "input.txt",
            output_dir=tmp_path / "output",
            progress_enabled=False,
        )

        argv = adapter.build_cli_argv(request)
        assert "--no-progress" in argv

    def test_quality_v72_flags(self, tmp_path: Path):
        adapter = ProductionSubmissionAdapter()
        request = TranslationJobRequest(
            input_path=tmp_path / "input.txt",
            output_dir=tmp_path / "output",
            quality_integration_v72=True,
            quality_character_memory_v72=True,
            quality_context_scene_v72=True,
            quality_naturalness_v72=True,
            quality_integration_kill_switch_v72=True,
        )

        argv = adapter.build_cli_argv(request)
        assert "--quality-integration-v72" in argv
        assert "--quality-character-memory-v72" in argv
        assert "--quality-context-scene-v72" in argv
        assert "--quality-naturalness-v72" in argv
        assert "--quality-integration-kill-switch-v72" in argv

    def test_quality_v83_flags(self, tmp_path: Path):
        adapter = ProductionSubmissionAdapter()
        request = TranslationJobRequest(
            input_path=tmp_path / "input.txt",
            output_dir=tmp_path / "output",
            quality_delivery_v83=True,
            quality_delivery_formats_v83=("txt", "epub"),
        )

        argv = adapter.build_cli_argv(request)
        assert "--quality-delivery-v83" in argv
        assert "--quality-delivery-formats-v83" in argv
        assert "txt" in argv
        assert "epub" in argv


class TestSubmit:
    def test_submit_creates_job_id_with_source_hash_and_timestamp(self, tmp_path: Path):
        adapter = ProductionSubmissionAdapter()
        source = tmp_path / "input.txt"
        source.write_text("Test content")
        request = TranslationJobRequest(
            input_path=source,
            output_dir=tmp_path / "output",
        )

        with patch("subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.pid = 12345
            mock_popen.return_value = mock_proc

            result = adapter.submit(request)

        assert result.job_id.startswith("job_")
        assert result.status == "submitted"
        assert result.process_pid == 12345
        assert result.cli_command == adapter.build_cli_argv(request)
        assert result.output_dir == request.output_dir

    def test_submit_sets_ntpe_runtime_pipeline_env(self, tmp_path: Path):
        adapter = ProductionSubmissionAdapter()
        source = tmp_path / "input.txt"
        source.write_text("Test content")
        request = TranslationJobRequest(
            input_path=source,
            output_dir=tmp_path / "output",
        )

        with patch("subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.pid = 12345
            mock_popen.return_value = mock_proc

            adapter.submit(request)

        call_kwargs = mock_popen.call_args.kwargs
        assert call_kwargs["env"]["NTPE_RUNTIME_PIPELINE"] == "runtime"

    def test_submit_handles_exception(self, tmp_path: Path):
        adapter = ProductionSubmissionAdapter()
        source = tmp_path / "input.txt"
        source.write_text("Test content")
        request = TranslationJobRequest(
            input_path=source,
            output_dir=tmp_path / "output",
        )

        with patch("subprocess.Popen", side_effect=OSError("Permission denied")):
            result = adapter.submit(request)

        assert result.status == "failed"
        assert result.error == "Permission denied"


class TestSubmitSync:
    def test_submit_sync_completed(self, tmp_path: Path):
        adapter = ProductionSubmissionAdapter()
        source = tmp_path / "input.txt"
        source.write_text("Test content")
        request = TranslationJobRequest(
            input_path=source,
            output_dir=tmp_path / "output",
        )

        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            result = adapter.submit_sync(request)

        assert result.status == "completed"
        assert result.error is None

    def test_submit_sync_failed(self, tmp_path: Path):
        adapter = ProductionSubmissionAdapter()
        source = tmp_path / "input.txt"
        source.write_text("Test content")
        request = TranslationJobRequest(
            input_path=source,
            output_dir=tmp_path / "output",
        )

        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stderr = "Translation failed"
            mock_run.return_value = mock_result

            result = adapter.submit_sync(request)

        assert result.status == "failed"
        assert result.error == "Translation failed"

    def test_submit_sync_timeout(self, tmp_path: Path):
        import subprocess
        adapter = ProductionSubmissionAdapter()
        source = tmp_path / "input.txt"
        source.write_text("Test content")
        request = TranslationJobRequest(
            input_path=source,
            output_dir=tmp_path / "output",
        )

        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 30)):
            result = adapter.submit_sync(request, timeout=30)

        assert result.status == "timeout"
        assert result.error is not None
        assert "timed out after 30s" in result.error


class TestJobIdDeterministicIdentity:
    def test_same_source_same_config_same_identity(self, tmp_path: Path):
        """Same source + same config should produce identical job_id (deterministic)."""
        adapter = ProductionSubmissionAdapter()
        source = tmp_path / "input.txt"
        source.write_text("Test content")
        request = TranslationJobRequest(
            input_path=source,
            output_dir=tmp_path / "output",
        )

        with patch("subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.pid = 12345
            mock_popen.return_value = mock_proc

            result1 = adapter.submit(request)
            result2 = adapter.submit(request)

        # Same source + same config should produce same job_id
        assert result1.job_id == result2.job_id

        # Verify format
        parts = result1.job_id.split("_")
        assert len(parts) == 3
        assert parts[0] == "job"
        assert len(parts[1]) == 16  # source_hash
        assert len(parts[2]) == 16  # config_fingerprint

    def test_same_source_different_config_different_identity(self, tmp_path: Path):
        """Same source + different config should produce different job_id."""
        adapter = ProductionSubmissionAdapter()
        source = tmp_path / "input.txt"
        source.write_text("Test content")
        
        request1 = TranslationJobRequest(
            input_path=source,
            output_dir=tmp_path / "output",
            quality_profile="literary"
        )
        
        request2 = TranslationJobRequest(
            input_path=source,
            output_dir=tmp_path / "output",
            quality_profile="fast"  # Different config
        )

        with patch("subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.pid = 12345
            mock_popen.return_value = mock_proc

            result1 = adapter.submit(request1)
            result2 = adapter.submit(request2)

        # Same source + different config should produce different job_id
        assert result1.job_id != result2.job_id

    def test_rapid_submissions_no_collision(self, tmp_path: Path):
        """Rapid repeated submissions should not collide due to deterministic identity."""
        adapter = ProductionSubmissionAdapter()
        source = tmp_path / "input.txt"
        source.write_text("Test content")
        request = TranslationJobRequest(
            input_path=source,
            output_dir=tmp_path / "output",
        )

        with patch("subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.pid = 12345
            mock_popen.return_value = mock_proc

            # Submit multiple times rapidly
            results = [adapter.submit(request) for _ in range(10)]

        # All should have the same job_id (deterministic)
        job_ids = [r.job_id for r in results]
        assert len(set(job_ids)) == 1  # All identical
        assert all(job_id == results[0].job_id for job_id in job_ids)


class TestTranslationJobRequestDefaults:
    def test_default_values(self, tmp_path: Path):
        request = TranslationJobRequest(
            input_path=tmp_path / "input.txt",
            output_dir=tmp_path / "output",
        )

        assert request.quality_profile == "literary"
        assert request.speed == "balanced"
        assert request.model == "meta/llama-3.3-70b-instruct"
        assert request.chunk_size == 1000
        assert request.resume is True
        assert request.dry_run is False
        assert request.max_retries == 3
        assert request.provider_attempts is None
        assert request.retry_base_seconds == 5.0
        assert request.qa_enabled is True
        assert request.qa_fail_policy == "retry"
        assert request.min_length_ratio == 0.18
        assert request.max_korean_chars == 2
        assert request.max_repeated_lines == 2
        assert request.glossary_path is None
        assert request.character_memory_path is None
        assert request.quality_delivery_v83 is False
        assert request.quality_delivery_formats_v83 == ("txt",)
        assert request.quality_integration_v72 is False
        assert request.quality_character_memory_v72 is False
        assert request.quality_context_scene_v72 is False
        assert request.quality_naturalness_v72 is False
        assert request.quality_integration_kill_switch_v72 is False
        assert request.simplified_chinese_policy == "normalize"
        assert request.progress_enabled is True