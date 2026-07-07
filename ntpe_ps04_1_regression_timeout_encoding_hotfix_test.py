# =====================================================
# NTPE 1.2 Production Stabilization — PS-04.1
# Regression Timeout & Encoding Hotfix Test
# =====================================================
from ntpe_production_translate import _normalize_regression_sets
from core.translation_engine.nvidia_client import NvidiaClient


def main():
    assert _normalize_regression_sets(["Golden_Set"]) == ("Test_Set_A",)
    assert _normalize_regression_sets(["golden", "smoke"]) == ("Test_Set_A", "Test_Set_0")
    client = NvidiaClient(api_key="nvapi-test", timeout=60)
    assert client.timeout >= 1
    print("PS-04.1 Regression Timeout Encoding Hotfix PASS")
    print("PASS")


if __name__ == "__main__":
    main()
