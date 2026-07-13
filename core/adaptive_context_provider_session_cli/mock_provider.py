from __future__ import annotations

from .config import CLI_VERSION


class DeterministicMockProvider:
    def __init__(self, outcomes: tuple[str, ...], output_tokens: tuple[int, ...]) -> None:
        self.outcomes = outcomes
        self.output_tokens = output_tokens
        self.calls = 0

    def __call__(self, payload: dict[str, object], plan: object) -> dict[str, object]:
        index = self.calls
        self.calls += 1
        outcome = self.outcomes[min(index, len(self.outcomes) - 1)]
        tokens = self.output_tokens[min(index, len(self.output_tokens) - 1)]
        base: dict[str, object] = {
            "status": "success" if outcome == "success" else "failed",
            "usage": {"output_tokens": tokens},
            "mock_provider": True,
            "mock_version": CLI_VERSION,
        }
        if outcome == "timeout": base["error"] = "mock request timed out"
        elif outcome == "503": base.update({"error": "mock service unavailable", "http_status": 503})
        elif outcome == "failed": base["error"] = "mock provider failure"
        return base
