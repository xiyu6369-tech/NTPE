from __future__ import annotations

from dataclasses import asdict

from core.launcher_product.model_catalog import model_catalog
from core.launcher_product.provider_catalog import provider_catalog


def test_provider_ids_are_unique_and_ordered() -> None:
    providers = provider_catalog({})
    assert [provider.provider_id for provider in providers] == ["nvidia", "gemini"]
    assert len({provider.provider_id for provider in providers}) == len(providers)


def test_model_ids_are_unique_and_belong_to_provider() -> None:
    providers = {provider.provider_id for provider in provider_catalog({})}
    models = model_catalog()
    assert len({model.model_id for model in models}) == len(models)
    assert all(model.provider_id in providers for model in models)


def test_catalog_does_not_expose_secret_values() -> None:
    secret = "do-not-expose-this-value"
    payload = repr([asdict(provider) for provider in provider_catalog({"NVIDIA_API_KEY": secret})])
    assert secret not in payload
    assert "configured': True" in payload


def test_catalog_order_is_deterministic() -> None:
    first = provider_catalog({"NVIDIA_API_KEY": "x"})
    second = provider_catalog({"NVIDIA_API_KEY": "y"})
    assert [item.provider_id for item in first] == [item.provider_id for item in second]
    assert model_catalog() == model_catalog()
