from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import time

@dataclass
class ProviderRequest:
    prompt: str
    model: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ProviderResponse:
    text: str
    provider: str
    model: Optional[str] = None
    success: bool = True
    latency_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ProviderError(Exception):
    message: str
    provider: Optional[str] = None
    retryable: bool = True
    def __str__(self) -> str:
        return self.message

class AIProvider:
    name = "base"
    def complete(self, request: ProviderRequest) -> ProviderResponse:
        raise NotImplementedError
    def health(self) -> Dict[str, Any]:
        return {"provider": self.name, "healthy": True}

class MockProvider(AIProvider):
    def __init__(self, name: str = "mock", response_text: str = "mock translation", fail_times: int = 0, retryable: bool = True):
        self.name = name
        self.response_text = response_text
        self.fail_times = fail_times
        self.retryable = retryable
        self.calls = 0
    def complete(self, request: ProviderRequest) -> ProviderResponse:
        self.calls += 1
        start = time.time()
        if self.calls <= self.fail_times:
            raise ProviderError(f"{self.name} simulated failure", self.name, self.retryable)
        text = self.response_text
        if "{prompt}" in text:
            text = text.replace("{prompt}", request.prompt)
        return ProviderResponse(text=text, provider=self.name, model=request.model, latency_ms=(time.time()-start)*1000, metadata={"calls": self.calls})
