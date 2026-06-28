from __future__ import annotations

import os
import time
import requests


class NvidiaClient:
    def __init__(
        self,
        api_key: str | None = None,
        api_url: str = "https://integrate.api.nvidia.com/v1/chat/completions",
        timeout: int = 180,
        rpm_limit: int = 40,
    ):
        self.api_key = api_key or os.environ.get("NVIDIA_API_KEY", "")
        self.api_url = api_url
        self.timeout = timeout
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

        response = requests.post(
            self.api_url,
            headers=headers,
            json=payload,
            timeout=self.timeout,
        )

        if response.status_code >= 400:
            raise RuntimeError(
                f"NVIDIA API error {response.status_code}: {response.text[:1000]}"
            )

        data = response.json()

        try:
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            raise RuntimeError(f"NVIDIA API response format error: {data}") from e
