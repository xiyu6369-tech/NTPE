from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.prompt_contract_canary_readiness import evaluate_prompt_canary_readiness
from core.shared.evidence import canonical_json_bytes
from core.translation_quality_provider_canary.framework import _build_prompts


ARTIFACT_ROOT = ROOT / "artifacts/te_v72_prompt_canary_readiness"
CORPUS = ROOT / "tests/fixtures/te_v72_canary/golden_corpus.json"


def build_artifacts() -> dict[str, bytes]:
    case = json.loads(CORPUS.read_text(encoding="utf-8"))["cases"][0]
    first = _build_prompts(str(case["case_id"]), str(case["source_text"]))
    second = _build_prompts(str(case["case_id"]), str(case["source_text"]))
    if first != second:
        raise ValueError("candidate-prompt-nondeterministic")
    system, baseline, candidate, metadata = first
    result = evaluate_prompt_canary_readiness(
        system_prompt=system,
        baseline_prompt=baseline,
        candidate_prompt=candidate,
        source_text=str(case["source_text"]),
        integration_metadata=metadata,
    )
    return {name: canonical_json_bytes(payload) for name, payload in result.artifacts().items()}


def main() -> int:
    artifacts = build_artifacts()
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    for name, value in sorted(artifacts.items()):
        (ARTIFACT_ROOT / name).write_bytes(value)
    print(json.dumps({
        "artifact_count": len(artifacts),
        "prompt_canary_ready": json.loads(artifacts["readiness_summary.json"])["prompt_canary_ready"],
        "provider_requests_added": 0,
        "network_requests_added": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
