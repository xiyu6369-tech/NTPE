import hashlib
import json
from pathlib import Path
import shutil

from core.adaptive_context_single_real_invocation import FakeSingleInvocationTransport
from core.controlled_multi_chunk_translation_canary.policy import (
    OUTPUT_ROOT,
    REAL_CANARY_GATE_ENV,
    SOURCE_FIXTURE_PATH,
    STAGE744_OUTPUT_ROOT,
)
from tests.unit.controlled_multi_chunk_translation_canary import FAKE_OUTPUTS
from verification.controlled_runtime import (
    controlled_multi_chunk_translation_stage74_real_canary as canary_cli,
)


def _repository(tmp_path: Path) -> Path:
    repository = tmp_path / "repository"
    (repository / "artifacts").mkdir(parents=True)
    source = Path(__file__).resolve().parents[3] / SOURCE_FIXTURE_PATH
    target = repository / SOURCE_FIXTURE_PATH
    target.parent.mkdir(parents=True)
    shutil.copy2(source, target)
    return repository


def _environment() -> dict[str, str]:
    return {
        REAL_CANARY_GATE_ENV: "1",
        "NVIDIA_API_KEY": "offline-test-key",
        "NTPE_API_CONNECT_TIMEOUT": "10",
        "NTPE_CURRENT_API_TIMEOUT": "180",
    }


def test_cli_stage744_fake_three_chunk_execution_is_isolated_and_zero_network(
    tmp_path, capsys,
):
    repository = _repository(tmp_path)
    prior = repository / OUTPUT_ROOT
    prior.mkdir(parents=True)
    sentinel = prior / "retained-prior-root.txt"
    sentinel.write_text("unchanged", encoding="utf-8")
    before = hashlib.sha256(sentinel.read_bytes()).hexdigest()
    transports = []

    def factory(index):
        transport = FakeSingleInvocationTransport(
            outputs=(FAKE_OUTPUTS[index - 1],)
        )
        transports.append(transport)
        return transport

    status = canary_cli.main(
        [
            "--authorize-real-provider",
            "--artifact-root",
            STAGE744_OUTPUT_ROOT,
        ],
        repository_root=repository,
        transport_factory_override=factory,
        environ=_environment(),
        execution_mode="fake",
    )
    output = capsys.readouterr().out
    selected = repository / STAGE744_OUTPUT_ROOT
    assert status == 0
    assert f"artifact_root: {STAGE744_OUTPUT_ROOT}" in output
    assert "artifact_root_validation: PASS" in output
    assert "clean_root_empty: true" in output
    assert "network_calls: 0" in output
    assert sum(item.calls for item in transports) == 3
    assert sum(item.network_requests for item in transports) == 0
    assert len(list(selected.glob("chunk-*.translated.txt"))) == 3
    assert len(list(selected.glob("checkpoint-*.json"))) == 3
    assert (selected / "combined.translated.txt").is_file()
    evidence_path = selected / "stage74-final-evidence.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert evidence["artifact_root"] == STAGE744_OUTPUT_ROOT
    assert evidence["result"]["chunks_completed"] == 3
    assert hashlib.sha256(sentinel.read_bytes()).hexdigest() == before
    assert sorted(path.name for path in prior.iterdir()) == [sentinel.name]


def test_selected_stage744_root_is_used_for_quality_diagnostics(tmp_path):
    repository = _repository(tmp_path)
    prior = repository / OUTPUT_ROOT
    prior.mkdir(parents=True)
    sentinel = prior / "retained-prior-root.txt"
    sentinel.write_text("unchanged", encoding="utf-8")
    bad = FAKE_OUTPUTS[1].replace("「", "“", 1)
    outputs = (FAKE_OUTPUTS[0], bad, FAKE_OUTPUTS[2])
    transports = []

    def factory(index):
        transport = FakeSingleInvocationTransport(outputs=(outputs[index - 1],))
        transports.append(transport)
        return transport

    status = canary_cli.main(
        [
            "--authorize-real-provider",
            "--artifact-root",
            STAGE744_OUTPUT_ROOT,
        ],
        repository_root=repository,
        transport_factory_override=factory,
        environ=_environment(),
        execution_mode="fake",
    )
    selected = repository / STAGE744_OUTPUT_ROOT
    assert status == 1
    assert len(transports) == 2
    assert sum(item.network_requests for item in transports) == 0
    assert (selected / "chunk-001.translated.txt").is_file()
    assert (selected / "checkpoint-001.json").is_file()
    assert (selected / "chunk-002.quality-diagnostic.json").is_file()
    assert (selected / "chunk-002.invalid-candidate.txt").is_file()
    assert not (selected / "chunk-002.translated.txt").exists()
    assert not (selected / "checkpoint-002.json").exists()
    assert not (selected / "combined.translated.txt").exists()
    assert sentinel.read_text(encoding="utf-8") == "unchanged"


def test_invalid_cli_override_fails_before_transport_or_default_fallback(
    tmp_path, capsys,
):
    repository = _repository(tmp_path)
    calls = []

    def factory(index):
        calls.append(index)
        return FakeSingleInvocationTransport()

    status = canary_cli.main(
        ["--authorize-real-provider", "--artifact-root", "../stage744"],
        repository_root=repository,
        transport_factory_override=factory,
        environ=_environment(),
        execution_mode="fake",
    )
    output = capsys.readouterr().out
    assert status == 1
    assert calls == []
    assert "network_calls: 0" in output
    assert not (repository / OUTPUT_ROOT).exists()
    assert not (repository / STAGE744_OUTPUT_ROOT).exists()


def test_non_empty_stage744_cli_root_fails_before_provider(tmp_path, capsys):
    repository = _repository(tmp_path)
    selected = repository / STAGE744_OUTPUT_ROOT
    selected.mkdir(parents=True)
    (selected / "stale.json").write_text("{}", encoding="utf-8")
    calls = []
    status = canary_cli.main(
        [
            "--authorize-real-provider",
            "--artifact-root",
            STAGE744_OUTPUT_ROOT,
        ],
        repository_root=repository,
        transport_factory_override=lambda index: calls.append(index),
        environ=_environment(),
        execution_mode="fake",
    )
    output = capsys.readouterr().out
    assert status == 1
    assert calls == []
    assert "network_calls: 0" in output
    assert (selected / "stale.json").is_file()
