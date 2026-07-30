from __future__ import annotations

import os
from pathlib import Path

from core.translation_engine.nvidia_client import NvidiaClient
from lts.txt_translation_runtime import capacity_retry_delay_seconds
from ntpe_literary_regression import LiteraryRegressionOptions


def main() -> int:
    old = os.environ.get("NTPE_CAPACITY_RETRY_DELAYS")
    try:
        os.environ["NTPE_CAPACITY_RETRY_DELAYS"] = "60,120,180"
        assert capacity_retry_delay_seconds(1, 5.0) == 60.0
        assert capacity_retry_delay_seconds(2, 5.0) == 120.0
        assert capacity_retry_delay_seconds(3, 5.0) == 180.0
        assert capacity_retry_delay_seconds(4, 5.0) == 180.0

        opts = LiteraryRegressionOptions(root=Path("."))
        assert opts.resume is True

        os.environ["NVIDIA_API_KEY"] = "test-key"
        os.environ["NTPE_NVIDIA_RPM_LIMIT"] = "99"
        client = NvidiaClient()
        assert client.rpm_limit == 40

        os.environ["NTPE_NVIDIA_RPM_LIMIT"] = "20"
        client = NvidiaClient()
        assert client.rpm_limit == 20

        print("TE v5.2.3 Provider Backpressure and Regression Resume Test")
        print("=========================================================")
        print("NVIDIA RPM ceiling capped at 40       PASS")
        print("Lower configured RPM remains valid    PASS")
        print("Capacity delays 60/120/180             PASS")
        print("Regression resume enabled by default  PASS")
        print("ALL PASS")
        return 0
    finally:
        if old is None:
            os.environ.pop("NTPE_CAPACITY_RETRY_DELAYS", None)
        else:
            os.environ["NTPE_CAPACITY_RETRY_DELAYS"] = old


if __name__ == "__main__":
    raise SystemExit(main())
