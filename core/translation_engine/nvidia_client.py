from __future__ import annotations

import os
import time
import requests
from requests import Timeout, RequestException


class NvidiaClient:
    def __init__(
        self,
        api_key: str | None = None,
        api_url: str = "https://integrate.api.nvidia.com/v1/chat/completions",
        timeout: int = 60,
        rpm_limit: int = 40,
    ):
        self.api_key = api_key or os.environ.get("NVIDIA_API_KEY", "")
        self.api_url = api_url
        # TER-v2.0: honor per-attempt timeout first.
        # Earlier builds printed adaptive timeouts (e.g. 120s) but requests could
        # still wait NTPE_API_TIMEOUT (e.g. 180s), wasting time on saturated workers.
        current_timeout = os.environ.get("NTPE_CURRENT_API_TIMEOUT")
        self.timeout = int(current_timeout or os.environ.get("NTPE_API_TIMEOUT", timeout))
        self.connect_timeout = int(os.environ.get("NTPE_API_CONNECT_TIMEOUT", 10))
        self.debug = os.environ.get("NTPE_TRANSLATE_DEBUG", "").lower() in {"1", "true", "yes", "on"}
        self.rpm_limit = rpm_limit
        self.request_times: list[float] = []

        if not self.api_key:
            raise ValueError(
                "找不到 NVIDIA API Key。請先設定環境變數 NVIDIA_API_KEY，"
                "或在 launcher / 程式中傳入 api_key。"
            )

    def _rate_limit(self) -> None:
        now = time.time()
        self.request_times = [t for t in self.request_times if now - t < 60]

        if len(self.request_times) >= self.rpm_limit:
            wait = 60 - (now - self.request_times[0]) + 0.5
            if wait > 0:
                time.sleep(wait)

        self.request_times.append(time.time())

    def chat(
        self,
        *,
        model: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.15,
        top_p: float = 0.85,
        max_tokens: int = 4000,
    ) -> str:
        self._rate_limit()

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
            "stream": False,
        }

        if self.debug:
            print(
                f"[NTPE DEBUG] NVIDIA request start model={model} "
                f"connect_timeout={self.connect_timeout}s read_timeout={self.timeout}s "
                f"max_tokens={max_tokens} prompt_chars={len(system_prompt) + len(user_prompt)}",
                flush=True,
            )

        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=(self.connect_timeout, self.timeout),
            )
        except Timeout as e:
            raise RuntimeError(
                f"NVIDIA API timeout after connect={self.connect_timeout}s/read={self.timeout}s. "
                "The configured timeout was applied correctly; the provider did not respond in time. "
                "Retry later, increase --provider-attempts, configure NTPE_TIMEOUT_RETRY_DELAYS, "
                "or use --fallback-models with an available model."
            ) from e
        except RequestException as e:
            raise RuntimeError(f"NVIDIA API request failed: {e}") from e

        if self.debug:
            print(f"[NTPE DEBUG] NVIDIA response status={response.status_code}", flush=True)

        if response.status_code >= 400:
            raise RuntimeError(
                f"NVIDIA API error {response.status_code}: {response.text[:1000]}"
            )

        data = response.json()

        try:
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            raise RuntimeError(f"NVIDIA API response format error: {data}") from e
