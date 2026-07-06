from __future__ import annotations

import os
from typing import Iterable


class EnvironmentManager:
    VALID_ENVIRONMENTS = ("development", "staging", "production")

    def __init__(self, env_var: str = "NTPE_ENV") -> None:
        self.env_var = env_var

    def current(self, fallback: str = "development") -> str:
        value = os.environ.get(self.env_var, fallback).strip().lower()
        return value if value in self.VALID_ENVIRONMENTS else fallback

    def normalize(self, environment: str | None) -> str:
        env = (environment or self.current()).strip().lower()
        if env not in self.VALID_ENVIRONMENTS:
            raise ValueError(f"unsupported NTPE environment: {environment}")
        return env
