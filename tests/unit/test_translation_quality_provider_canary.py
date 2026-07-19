from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path

import pytest

from core.translation_quality_provider_canary import AUTHORIZATION_TOKEN, CanaryExecutionConfig, execute_canary
from core.translation_quality_provider_canary.framework import ProviderOutcome


ROOT = Path(__file__).resolve().parents[2]


@dataclass
class RecordingTransport:
    provenance: str = "real"
    calls: list[tuple[str, str]] = field(default_factory=list)

    def invoke(self, *, system_prompt: str, user_prompt: str, config: CanaryExecutionConfig) -> ProviderOutcome:
        self.calls.append((system_prompt, user_prompt))
        return ProviderOutcome(True, f"translation-{len(self.calls)}", 1.0)


def _prepare(tmp_path: Path) -> None:
    target = tmp_path / "tests/fixtures/te_v72_canary"
    target.mkdir(parents=True)
    target.joinpath("golden_corpus.json").write_bytes(
        (ROOT / "tests/fixtures/te_v72_canary/golden_corpus.json").read_bytes()
    )


def _config(**changes: object) -> CanaryExecutionConfig:
    values = {"authorization_id": "stage1252-user-authorized", "authorization_token": AUTHORIZATION_TOKEN}
    values.update(changes)
    return CanaryExecutionConfig(**values)


@pytest.mark.parametrize("changes", [
    {"attempt_limit_per_arm": 2}, {"retry_count": 1}, {"fallback": True},
    {"parallel_jobs": 2}, {"excerpt_limit": 3}, {"model": "other"},
])
def test_forbidden_execution_shapes_fail_closed(changes: dict[str, object]) -> None:
    assert _config(**changes).validate()


def test_two_excerpt_ab_is_exactly_four_serial_single_attempts(tmp_path: Path) -> None:
    _prepare(tmp_path)
    transport = RecordingTransport()
    result = execute_canary(_config(), root=tmp_path, transport=transport)
    assert result.request_count == result.network_request_count == len(transport.calls) == 4
    metrics = json.loads((tmp_path / "artifacts/te_v72_canary_execution/provider_metrics.json").read_text(encoding="utf-8"))
    assert all(row["attempts"] == 1 and row["retry"] == 0 and row["fallback"] is False for row in metrics["rows"])
    assert metrics["parallel_jobs"] == 1


def test_each_pair_has_identical_system_and_only_user_prompt_integration_differs(tmp_path: Path) -> None:
    _prepare(tmp_path)
    transport = RecordingTransport()
    execute_canary(_config(), root=tmp_path, transport=transport)
    assert transport.calls[0][0] == transport.calls[1][0]
    assert transport.calls[2][0] == transport.calls[3][0]
    assert transport.calls[0][1] != transport.calls[1][1]
    assert transport.calls[2][1] != transport.calls[3][1]


def test_claim_prevents_replay(tmp_path: Path) -> None:
    _prepare(tmp_path)
    execute_canary(_config(), root=tmp_path, transport=RecordingTransport())
    with pytest.raises(ValueError, match="already-claimed"):
        execute_canary(_config(), root=tmp_path, transport=RecordingTransport())


def test_artifacts_exclude_prompts_payload_and_credentials(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _prepare(tmp_path)
    monkeypatch.setenv("NVIDIA_API_KEY", "never-persist-this-secret")
    execute_canary(_config(), root=tmp_path, transport=RecordingTransport())
    combined = "\n".join(path.read_text(encoding="utf-8") for path in (tmp_path / "artifacts").rglob("*") if path.is_file())
    assert "never-persist-this-secret" not in combined
    assert "Bearer " not in combined
    assert "system_prompt\"" not in combined and "user_prompt\"" not in combined
