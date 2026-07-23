"""Explicit local SQLite registry and atomic uniqueness boundary."""

from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import fields
from pathlib import Path, PurePath
from typing import Callable

from .errors import (
    AtomicConsumptionAlreadyConsumedError,
    AtomicConsumptionCommitError,
    AtomicConsumptionRegistryIntegrityError,
    AtomicConsumptionRegistryPathError,
    AtomicConsumptionRegistrySchemaError,
)
from .models import AtomicAuthorizationConsumptionClaim, canonical_json

REGISTRY_SCHEMA_NAME = "ntpe.controlled_runtime_atomic_authorization_consumption_registry"
REGISTRY_SCHEMA_VERSION = "1.0"
REGISTRY_COMPONENT = "ntpe.stage6.3.atomic_authorization_consumption"
METADATA_TABLE = "atomic_consumption_registry_metadata"
CLAIMS_TABLE = "atomic_authorization_consumption_claims"

_CLAIM_COLUMNS = (
    "created_sequence", "claim_id", "consumption_id", "authorization_id",
    "authorization_request_fingerprint", "authorization_decision_fingerprint",
    "execution_plan_fingerprint", "selected_adapter_index", "consumed_unit_count",
    "stage62_request_fingerprint", "stage62_record_fingerprint",
    "upstream_chain_fingerprint", "claim_payload_json", "claim_fingerprint",
    "claim_state", "execution_started", "execution_completed",
)


def _safe_registry_path(registry_path: os.PathLike[str] | str, allowed_root: os.PathLike[str] | str) -> tuple[Path, Path]:
    if not isinstance(registry_path, (str, os.PathLike)) or not str(registry_path).strip():
        raise AtomicConsumptionRegistryPathError("registry_path is required")
    if not isinstance(allowed_root, (str, os.PathLike)) or not str(allowed_root).strip():
        raise AtomicConsumptionRegistryPathError("allowed_root is required")
    raw = str(registry_path)
    if "\x00" in raw or raw.lower().startswith(("file:", "http:", "https:", "sqlite:")):
        raise AtomicConsumptionRegistryPathError("URI and malformed registry paths are unsupported")
    if raw.startswith(("\\\\", "//")):
        raise AtomicConsumptionRegistryPathError("network registry paths are unsupported")
    if any(part == ".." for part in PurePath(raw).parts):
        raise AtomicConsumptionRegistryPathError("registry path traversal is unsupported")
    root = Path(allowed_root).resolve(strict=True)
    candidate = Path(registry_path)
    if not candidate.is_absolute():
        candidate = root / candidate
    resolved_parent = candidate.parent.resolve(strict=True)
    resolved = resolved_parent / candidate.name
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise AtomicConsumptionRegistryPathError("registry path must resolve beneath allowed_root") from exc
    if candidate.exists():
        actual = candidate.resolve(strict=True)
        try:
            actual.relative_to(root)
        except ValueError as exc:
            raise AtomicConsumptionRegistryPathError("registry symlink escapes allowed_root") from exc
        if actual.is_dir():
            raise AtomicConsumptionRegistryPathError("registry path must not be a directory")
        resolved = actual
    return resolved, root


class AtomicAuthorizationConsumptionRegistry:
    """One explicitly located registry; no hidden connection or default path.

    Registry identity is canonicalized as ``registry:<relative-posix-path>``
    after both the allowed root and registry parent have been resolved.  This
    binds requests to one exact root-relative database identity while keeping
    machine-specific absolute paths out of semantic fingerprints.
    """

    def __init__(
        self,
        registry_path: os.PathLike[str] | str,
        allowed_root: os.PathLike[str] | str,
        *,
        busy_timeout_ms: int = 5000,
        failure_injector: Callable[[str], None] | None = None,
        connection_factory: Callable[..., sqlite3.Connection] = sqlite3.connect,
    ) -> None:
        self.path, self.allowed_root = _safe_registry_path(registry_path, allowed_root)
        self.busy_timeout_ms = busy_timeout_ms
        self._failure_injector = failure_injector
        self._connection_factory = connection_factory

    @property
    def registry_scope(self) -> str:
        return "registry:" + self.path.relative_to(self.allowed_root).as_posix()

    def _inject(self, point: str) -> None:
        if self._failure_injector:
            self._failure_injector(point)

    def _connect(self) -> sqlite3.Connection:
        connection = self._connection_factory(str(self.path), timeout=self.busy_timeout_ms / 1000)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(f"PRAGMA busy_timeout = {int(self.busy_timeout_ms)}")
        connection.execute("PRAGMA synchronous = FULL")
        return connection

    @staticmethod
    def _initialize_or_validate(connection: sqlite3.Connection) -> None:
        tables = {
            row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
        }
        if not tables:
            connection.execute(
                f"CREATE TABLE {METADATA_TABLE} ("
                "schema_name TEXT PRIMARY KEY NOT NULL, schema_version TEXT NOT NULL, "
                "created_by_component TEXT NOT NULL)"
            )
            connection.execute(
                f"INSERT INTO {METADATA_TABLE} VALUES (?, ?, ?)",
                (REGISTRY_SCHEMA_NAME, REGISTRY_SCHEMA_VERSION, REGISTRY_COMPONENT),
            )
            connection.execute(
                f"CREATE TABLE {CLAIMS_TABLE} ("
                "created_sequence INTEGER PRIMARY KEY AUTOINCREMENT,"
                "claim_id TEXT NOT NULL UNIQUE,"
                "consumption_id TEXT NOT NULL UNIQUE,"
                "authorization_id TEXT NOT NULL,"
                "authorization_request_fingerprint TEXT NOT NULL,"
                "authorization_decision_fingerprint TEXT NOT NULL UNIQUE,"
                "execution_plan_fingerprint TEXT NOT NULL,"
                "selected_adapter_index INTEGER NOT NULL,"
                "consumed_unit_count INTEGER NOT NULL CHECK(consumed_unit_count = 1),"
                "stage62_request_fingerprint TEXT NOT NULL,"
                "stage62_record_fingerprint TEXT NOT NULL,"
                "upstream_chain_fingerprint TEXT NOT NULL,"
                "claim_payload_json TEXT NOT NULL,"
                "claim_fingerprint TEXT NOT NULL,"
                "claim_state TEXT NOT NULL CHECK(claim_state = 'durably_consumed_not_executed'),"
                "execution_started INTEGER NOT NULL CHECK(execution_started = 0),"
                "execution_completed INTEGER NOT NULL CHECK(execution_completed = 0))"
            )
            return
        if tables != {METADATA_TABLE, CLAIMS_TABLE}:
            raise AtomicConsumptionRegistrySchemaError("registry table set is not canonical")
        metadata = connection.execute(
            f"SELECT schema_name, schema_version, created_by_component FROM {METADATA_TABLE}"
        ).fetchall()
        if len(metadata) != 1 or tuple(metadata[0]) != (
            REGISTRY_SCHEMA_NAME, REGISTRY_SCHEMA_VERSION, REGISTRY_COMPONENT
        ):
            raise AtomicConsumptionRegistrySchemaError("registry metadata is not canonical")
        columns = tuple(row[1] for row in connection.execute(f"PRAGMA table_info({CLAIMS_TABLE})"))
        if columns != _CLAIM_COLUMNS:
            raise AtomicConsumptionRegistrySchemaError("claim table columns are not canonical")
        unique_sets = {
            tuple(info[2] for info in connection.execute(f"PRAGMA index_info({row[1]})"))
            for row in connection.execute(f"PRAGMA index_list({CLAIMS_TABLE})")
            if row[2]
        }
        for required in (("claim_id",), ("consumption_id",), ("authorization_decision_fingerprint",)):
            if required not in unique_sets:
                raise AtomicConsumptionRegistrySchemaError("required registry uniqueness constraint is missing")

    @staticmethod
    def _row_values(claim: AtomicAuthorizationConsumptionClaim) -> tuple[object, ...]:
        chain_fp = claim.upstream_fingerprint_chain[-1]
        return (
            claim.claim_id, claim.consumption_id, claim.authorization_id,
            claim.authorization_request_fingerprint, claim.authorization_decision_fingerprint,
            claim.execution_plan_fingerprint, claim.selected_adapter_index, claim.consumed_unit_count,
            claim.stage62_request_fingerprint, claim.stage62_record_fingerprint, chain_fp,
            claim.to_json(), claim.claim_fingerprint, claim.claim_state, 0, 0,
        )

    def claim(self, claim: AtomicAuthorizationConsumptionClaim) -> AtomicAuthorizationConsumptionClaim:
        connection: sqlite3.Connection | None = None
        committed = False
        try:
            self._inject("before_connection")
            connection = self._connect()
            self._inject("before_begin")
            connection.execute("BEGIN IMMEDIATE")
            self._inject("after_begin")
            self._initialize_or_validate(connection)
            self._inject("before_insert")
            try:
                connection.execute(
                    f"INSERT INTO {CLAIMS_TABLE} ("
                    "claim_id,consumption_id,authorization_id,authorization_request_fingerprint,"
                    "authorization_decision_fingerprint,execution_plan_fingerprint,selected_adapter_index,"
                    "consumed_unit_count,stage62_request_fingerprint,stage62_record_fingerprint,"
                    "upstream_chain_fingerprint,claim_payload_json,claim_fingerprint,claim_state,"
                    "execution_started,execution_completed) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    self._row_values(claim),
                )
            except sqlite3.IntegrityError as exc:
                existing = connection.execute(
                    f"SELECT 1 FROM {CLAIMS_TABLE} WHERE authorization_decision_fingerprint=?",
                    (claim.authorization_decision_fingerprint,),
                ).fetchone()
                if existing:
                    raise AtomicConsumptionAlreadyConsumedError("authorization is already durably consumed") from exc
                raise AtomicConsumptionRegistryIntegrityError("claim identifier conflicts with registry") from exc
            self._inject("after_insert")
            self._inject("before_commit")
            connection.commit()
            committed = True
            self._inject("after_commit")
            self._inject("before_readback")
            row = connection.execute(
                f"SELECT * FROM {CLAIMS_TABLE} WHERE authorization_decision_fingerprint=?",
                (claim.authorization_decision_fingerprint,),
            ).fetchone()
            if row is None:
                raise AtomicConsumptionRegistryIntegrityError("committed claim could not be read back")
            self._verify_row(row, claim)
            self._inject("after_readback")
            return claim
        except (AtomicConsumptionAlreadyConsumedError, AtomicConsumptionRegistrySchemaError,
                AtomicConsumptionRegistryIntegrityError):
            if connection is not None and not committed:
                connection.rollback()
            raise
        except sqlite3.DatabaseError as exc:
            if connection is not None and not committed:
                connection.rollback()
            if committed:
                raise AtomicConsumptionRegistryIntegrityError(
                    "claim committed but registry read-back failed"
                ) from exc
            if "locked" not in str(exc).lower() and "busy" not in str(exc).lower():
                raise AtomicConsumptionRegistryIntegrityError("registry database is malformed") from exc
            raise AtomicConsumptionCommitError("atomic claim transaction could not acquire the registry") from exc
        except Exception as exc:
            if connection is not None and not committed:
                connection.rollback()
            if committed:
                raise AtomicConsumptionRegistryIntegrityError(
                    "claim committed but post-commit verification failed"
                ) from exc
            raise AtomicConsumptionCommitError("atomic claim transaction failed and was rolled back") from exc
        finally:
            if connection is not None:
                connection.close()

    @staticmethod
    def _verify_row(row: sqlite3.Row, claim: AtomicAuthorizationConsumptionClaim) -> None:
        expected = AtomicAuthorizationConsumptionRegistry._row_values(claim)
        actual = tuple(row[name] for name in _CLAIM_COLUMNS[1:])
        if actual != expected:
            raise AtomicConsumptionRegistryIntegrityError("stored claim row does not equal supplied claim")
        if canonical_json(json.loads(row["claim_payload_json"])) != claim.to_json():
            raise AtomicConsumptionRegistryIntegrityError("stored claim payload is not canonical")

    def read_claim(self, authorization_decision_fingerprint: str) -> AtomicAuthorizationConsumptionClaim | None:
        connection = self._connect()
        try:
            connection.execute("BEGIN")
            self._initialize_or_validate(connection)
            row = connection.execute(
                f"SELECT claim_payload_json FROM {CLAIMS_TABLE} WHERE authorization_decision_fingerprint=?",
                (authorization_decision_fingerprint,),
            ).fetchone()
            connection.commit()
            if row is None:
                return None
            payload = json.loads(row[0])
            payload.pop("claim_fingerprint", None)
            return AtomicAuthorizationConsumptionClaim(
                **{item.name: payload[item.name] if item.name != "upstream_fingerprint_chain"
                   else tuple(payload[item.name])
                   for item in fields(AtomicAuthorizationConsumptionClaim)
                   if item.init}
            )
        finally:
            connection.close()

    def count_claims(self) -> int:
        connection = self._connect()
        try:
            connection.execute("BEGIN")
            self._initialize_or_validate(connection)
            value = int(connection.execute(f"SELECT COUNT(*) FROM {CLAIMS_TABLE}").fetchone()[0])
            connection.commit()
            return value
        finally:
            connection.close()
