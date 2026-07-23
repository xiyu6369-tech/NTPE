import sqlite3

import pytest

from core.controlled_runtime_atomic_authorization_consumption import (
    AtomicAuthorizationConsumer,
)
from core.controlled_runtime_atomic_authorization_consumption.errors import (
    AtomicConsumptionRegistryPathError,
)
from core.controlled_runtime_atomic_authorization_consumption.registry import (
    AtomicAuthorizationConsumptionRegistry,
)
from . import build_context


def test_path_must_be_explicit_and_beneath_root(tmp_path):
    with pytest.raises(AtomicConsumptionRegistryPathError):
        AtomicAuthorizationConsumptionRegistry("", tmp_path)
    with pytest.raises(AtomicConsumptionRegistryPathError):
        AtomicAuthorizationConsumptionRegistry(tmp_path / ".." / "escape.sqlite3", tmp_path)


def test_wrong_existing_schema_is_rejected(tmp_path):
    path = tmp_path / "wrong.sqlite3"
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE unrelated(value TEXT)")
    connection.commit()
    connection.close()
    registry = AtomicAuthorizationConsumptionRegistry(path, tmp_path)
    with pytest.raises(Exception):
        registry.count_claims()


@pytest.mark.parametrize(
    "point", ("after_begin", "before_insert", "after_insert", "before_commit")
)
def test_precommit_failures_roll_back_without_a_claim(tmp_path, point):
    context = build_context(tmp_path)

    def fail(actual):
        if actual == point:
            raise RuntimeError("injected pre-commit failure")

    context["registry"] = AtomicAuthorizationConsumptionRegistry(
        tmp_path / "claims.sqlite3", tmp_path, failure_injector=fail,
    )
    result = AtomicAuthorizationConsumer().consume(**context)
    assert result.status == "atomic_commit_failed"
    assert AtomicAuthorizationConsumptionRegistry(
        tmp_path / "claims.sqlite3", tmp_path
    ).count_claims() == 0


def test_postcommit_failure_preserves_claim_and_retry_is_duplicate(tmp_path):
    context = build_context(tmp_path)

    def fail_after_commit(point):
        if point == "after_commit":
            raise RuntimeError("injected post-commit failure")

    context["registry"] = AtomicAuthorizationConsumptionRegistry(
        tmp_path / "claims.sqlite3", tmp_path, failure_injector=fail_after_commit,
    )
    result = AtomicAuthorizationConsumer().consume(**context)
    assert result.status == "registry_integrity_failure"
    clean = AtomicAuthorizationConsumptionRegistry(
        tmp_path / "claims.sqlite3", tmp_path
    )
    assert clean.count_claims() == 1
    context["registry"] = clean
    assert AtomicAuthorizationConsumer().consume(**context).status == "already_consumed"
