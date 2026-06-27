import requests


class NvidiaEngine:
    def __init__(self, config):
        self.api_key = config.get("api_key", "")
        self.model = config.get("model", "meta/llama-3.3-70b-instruct")
        self.api_url = config.get(
            "api_url",
            "https://integrate.api.nvidia.com/v1/chat/completions",
        )
        self.timeout = config.get("timeout", 180)

        if not self.api_key:
            raise RuntimeError("尚未設定 NVIDIA API Key")

    def chat(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "top_p": 0.7,
            "max_tokens": 4096,
        }

        response = requests.post(
            self.api_url,
            headers=headers,
            json=payload,
            timeout=self.timeout,
        )

        if response.status_code != 200:
            raise RuntimeError(f"NVIDIA API 錯誤 {response.status_code}: {response.text}")

        data = response.json()
        return data["choices"][0]["message"]["content"].strip()

    def translate(self, prompt: str) -> str:
        return self.chat(prompt)
