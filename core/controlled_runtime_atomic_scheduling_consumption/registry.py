"""Dedicated Stage 6.7 SQLite registry with single-use semantics."""

from __future__ import annotations

import json
import pathlib
import sqlite3
from dataclasses import fields
from typing import Callable

from .errors import (
    AtomicSchedulingConsumptionAlreadyConsumedError,
    AtomicSchedulingConsumptionCommitError,
    AtomicSchedulingConsumptionRegistryIntegrityError,
    AtomicSchedulingConsumptionRegistryPathError,
    AtomicSchedulingConsumptionRegistrySchemaError,
)
from .models import (
    AtomicSchedulingAuthorizationConsumptionClaim,
    AtomicSchedulingAuthorizationConsumptionRequest,
    canonical_json,
)

REGISTRY_SCHEMA_NAME = "ntpe.atomic_scheduling_authorization_consumption_registry"
REGISTRY_SCHEMA_VERSION = "1.0"
REGISTRY_COMPONENT = "ntpe.stage6.7.atomic_scheduling_authorization_consumption"
METADATA_TABLE = "registry_metadata"
CLAIMS_TABLE = "atomic_scheduling_consumption_claims"

_METADATA_COLUMNS = ("schema_name", "schema_version", "component")
_CLAIM_COLUMNS = (
    "scheduling_consumption_id",
    "scheduling_authorization_id",
    "handoff_id",
    "envelope_id",
    "claim_id",
    "consumption_id",
    "authorization_id",
    "execution_plan_fingerprint",
    "execution_authorization_decision_fingerprint",
    "stage63_claim_fingerprint",
    "stage64_envelope_fingerprint",
    "stage65_handoff_receipt_fingerprint",
    "stage66_scheduling_request_fingerprint",
    "stage66_scheduling_decision_fingerprint",
    "scheduling_consumption_request_fingerprint",
    "claim_fingerprint",
    "selected_adapter_index",
    "consumed_schedule_unit_count",
    "runtime_boundary_id",
    "runtime_boundary_kind",
    "claim_state",
    "upstream_fingerprint_chain_json",
    "request_payload_json",
    "claim_payload_json",
)


def _safe_registry_path(
    database_path: str | pathlib.Path,
    allowed_root: str | pathlib.Path,
) -> tuple[pathlib.Path, pathlib.Path]:
    if not isinstance(allowed_root, (str, pathlib.Path)) or not str(allowed_root).strip():
        raise AtomicSchedulingConsumptionRegistryPathError(
            "allowed_root is required"
        )
    if not isinstance(database_path, (str, pathlib.Path)) or not str(database_path).strip():
        raise AtomicSchedulingConsumptionRegistryPathError(
            "database_path is required"
        )
    root_text = str(allowed_root)
    path_text = str(database_path)
    if "\x00" in root_text or "\x00" in path_text:
        raise AtomicSchedulingConsumptionRegistryPathError(
            "malformed registry paths are unsupported"
        )
    if path_text.lower().startswith(("file:", "http:", "https:", "sqlite:")):
        raise AtomicSchedulingConsumptionRegistryPathError(
            "URI registry paths are unsupported"
        )
    if path_text.startswith(("\\\\", "//")):
        raise AtomicSchedulingConsumptionRegistryPathError(
            "network registry paths are unsupported"
        )
    if any(part == ".." for part in pathlib.PurePath(path_text).parts):
        raise AtomicSchedulingConsumptionRegistryPathError(
            "registry parent traversal is unsupported"
        )
    root_input = pathlib.Path(root_text)
    if not root_input.is_absolute():
        raise AtomicSchedulingConsumptionRegistryPathError(
            "allowed_root must be absolute"
        )
    try:
        root = root_input.resolve(strict=True)
    except (FileNotFoundError, OSError) as exc:
        raise AtomicSchedulingConsumptionRegistryPathError(
            "allowed_root must be an existing directory"
        ) from exc
    if not root.is_dir():
        raise AtomicSchedulingConsumptionRegistryPathError(
            "allowed_root must be a directory"
        )
    candidate = pathlib.Path(path_text)
    if not candidate.is_absolute():
        candidate = root / candidate
    try:
        resolved_parent = candidate.parent.resolve(strict=True)
    except (FileNotFoundError, OSError) as exc:
        raise AtomicSchedulingConsumptionRegistryPathError(
            "registry parent directory must exist"
        ) from exc
    resolved = resolved_parent / candidate.name
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise AtomicSchedulingConsumptionRegistryPathError(
            "database path must resolve beneath allowed_root"
        ) from exc
    if candidate.exists():
        actual = candidate.resolve(strict=True)
        try:
            actual.relative_to(root)
        except ValueError as exc:
            raise AtomicSchedulingConsumptionRegistryPathError(
                "registry symlink escapes allowed_root"
            ) from exc
        if actual.is_dir():
            raise AtomicSchedulingConsumptionRegistryPathError(
                "database_path must not be a directory"
            )
        resolved = actual
    return resolved, root


class AtomicSchedulingAuthorizationConsumptionRegistry:
    """One explicitly located, immutable-claim scheduling registry."""

    def __init__(
        self,
        database_path: str | pathlib.Path,
        *,
        allowed_root: str | pathlib.Path,
        busy_timeout_ms: int = 5000,
        failure_injector: Callable[[str], None] | None = None,
        connection_factory: Callable[..., sqlite3.Connection] = sqlite3.connect,
    ) -> None:
        self.path, self.allowed_root = _safe_registry_path(
            database_path, allowed_root
        )
        if type(busy_timeout_ms) is not int or busy_timeout_ms < 1:
            raise ValueError("busy_timeout_ms must be a positive integer")
        self.busy_timeout_ms = busy_timeout_ms
        self._failure_injector = failure_injector
        self._connection_factory = connection_factory

    def _inject(self, point: str) -> None:
        if self._failure_injector is not None:
            self._failure_injector(point)

    def _connect(self) -> sqlite3.Connection:
        connection = self._connection_factory(
            str(self.path), timeout=self.busy_timeout_ms / 1000
        )
        connection.row_factory = sqlite3.Row
        try:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute(f"PRAGMA busy_timeout = {self.busy_timeout_ms}")
            connection.execute("PRAGMA synchronous = FULL")
        except sqlite3.DatabaseError as exc:
            connection.close()
            raise AtomicSchedulingConsumptionRegistrySchemaError(
                "registry database is malformed or incompatible"
            ) from exc
        return connection

    @staticmethod
    def _initialize_or_validate(connection: sqlite3.Connection) -> None:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
        }
        if not tables:
            connection.execute(
                f"CREATE TABLE {METADATA_TABLE} ("
                "schema_name TEXT PRIMARY KEY NOT NULL,"
                "schema_version TEXT NOT NULL,"
                "component TEXT NOT NULL)"
            )
            connection.execute(
                f"INSERT INTO {METADATA_TABLE} VALUES (?, ?, ?)",
                (
                    REGISTRY_SCHEMA_NAME,
                    REGISTRY_SCHEMA_VERSION,
                    REGISTRY_COMPONENT,
                ),
            )
            connection.execute(
                f"CREATE TABLE {CLAIMS_TABLE} ("
                "scheduling_consumption_id TEXT PRIMARY KEY NOT NULL,"
                "scheduling_authorization_id TEXT NOT NULL UNIQUE,"
                "handoff_id TEXT NOT NULL,"
                "envelope_id TEXT NOT NULL,"
                "claim_id TEXT NOT NULL,"
                "consumption_id TEXT NOT NULL,"
                "authorization_id TEXT NOT NULL,"
                "execution_plan_fingerprint TEXT NOT NULL,"
                "execution_authorization_decision_fingerprint TEXT NOT NULL,"
                "stage63_claim_fingerprint TEXT NOT NULL,"
                "stage64_envelope_fingerprint TEXT NOT NULL,"
                "stage65_handoff_receipt_fingerprint TEXT NOT NULL,"
                "stage66_scheduling_request_fingerprint TEXT NOT NULL,"
                "stage66_scheduling_decision_fingerprint TEXT NOT NULL UNIQUE,"
                "scheduling_consumption_request_fingerprint TEXT NOT NULL UNIQUE,"
                "claim_fingerprint TEXT NOT NULL UNIQUE,"
                "selected_adapter_index INTEGER NOT NULL,"
                "consumed_schedule_unit_count INTEGER NOT NULL "
                "CHECK(consumed_schedule_unit_count = 1),"
                "runtime_boundary_id TEXT NOT NULL,"
                "runtime_boundary_kind TEXT NOT NULL "
                "CHECK(runtime_boundary_kind = 'controlled_offline_acceptance_boundary'),"
                "claim_state TEXT NOT NULL "
                "CHECK(claim_state = 'scheduling_authorization_consumed_not_scheduled'),"
                "upstream_fingerprint_chain_json TEXT NOT NULL,"
                "request_payload_json TEXT NOT NULL,"
                "claim_payload_json TEXT NOT NULL)"
            )
            return
        if tables != {METADATA_TABLE, CLAIMS_TABLE}:
            raise AtomicSchedulingConsumptionRegistrySchemaError(
                "registry table set is not canonical"
            )
        metadata_columns = tuple(
            row[1]
            for row in connection.execute(
                f"PRAGMA table_info({METADATA_TABLE})"
            )
        )
        if metadata_columns != _METADATA_COLUMNS:
            raise AtomicSchedulingConsumptionRegistrySchemaError(
                "registry metadata columns are not canonical"
            )
        metadata = connection.execute(
            f"SELECT schema_name, schema_version, component FROM {METADATA_TABLE}"
        ).fetchall()
        if len(metadata) != 1 or tuple(metadata[0]) != (
            REGISTRY_SCHEMA_NAME,
            REGISTRY_SCHEMA_VERSION,
            REGISTRY_COMPONENT,
        ):
            raise AtomicSchedulingConsumptionRegistrySchemaError(
                "registry metadata is not canonical"
            )
        claim_columns = tuple(
            row[1]
            for row in connection.execute(f"PRAGMA table_info({CLAIMS_TABLE})")
        )
        if claim_columns != _CLAIM_COLUMNS:
            raise AtomicSchedulingConsumptionRegistrySchemaError(
                "claim table columns are not canonical"
            )
        unique_sets = {
            tuple(
                info[2]
                for info in connection.execute(
                    f"PRAGMA index_info({index_row[1]})"
                )
            )
            for index_row in connection.execute(
                f"PRAGMA index_list({CLAIMS_TABLE})"
            )
            if index_row[2]
        }
        required_unique = (
            ("scheduling_consumption_id",),
            ("scheduling_authorization_id",),
            ("stage66_scheduling_decision_fingerprint",),
            ("scheduling_consumption_request_fingerprint",),
            ("claim_fingerprint",),
        )
        if any(item not in unique_sets for item in required_unique):
            raise AtomicSchedulingConsumptionRegistrySchemaError(
                "required registry uniqueness constraint is missing"
            )

    @staticmethod
    def _row_values(
        request: AtomicSchedulingAuthorizationConsumptionRequest,
        claim: AtomicSchedulingAuthorizationConsumptionClaim,
    ) -> tuple[object, ...]:
        return (
            claim.scheduling_consumption_id,
            claim.scheduling_authorization_id,
            claim.handoff_id,
            claim.envelope_id,
            claim.claim_id,
            claim.consumption_id,
            claim.authorization_id,
            claim.execution_plan_fingerprint,
            claim.execution_authorization_decision_fingerprint,
            claim.stage63_claim_fingerprint,
            claim.stage64_envelope_fingerprint,
            claim.stage65_handoff_receipt_fingerprint,
            claim.stage66_scheduling_request_fingerprint,
            claim.stage66_scheduling_decision_fingerprint,
            claim.scheduling_consumption_request_fingerprint,
            claim.claim_fingerprint,
            claim.selected_adapter_index,
            claim.consumed_schedule_unit_count,
            claim.runtime_boundary_id,
            claim.runtime_boundary_kind,
            claim.claim_state,
            canonical_json(list(claim.upstream_fingerprint_chain)),
            request.to_json(),
            claim.to_json(),
        )

    def claim(
        self,
        request: AtomicSchedulingAuthorizationConsumptionRequest,
        claim: AtomicSchedulingAuthorizationConsumptionClaim,
    ) -> AtomicSchedulingAuthorizationConsumptionClaim:
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
                placeholders = ",".join("?" for _ in _CLAIM_COLUMNS)
                connection.execute(
                    f"INSERT INTO {CLAIMS_TABLE} ({','.join(_CLAIM_COLUMNS)}) "
                    f"VALUES ({placeholders})",
                    self._row_values(request, claim),
                )
            except sqlite3.IntegrityError as exc:
                authorization_row = connection.execute(
                    f"SELECT scheduling_consumption_id FROM {CLAIMS_TABLE} "
                    "WHERE scheduling_authorization_id=? OR "
                    "stage66_scheduling_decision_fingerprint=?",
                    (
                        claim.scheduling_authorization_id,
                        claim.stage66_scheduling_decision_fingerprint,
                    ),
                ).fetchone()
                if authorization_row is not None:
                    raise AtomicSchedulingConsumptionAlreadyConsumedError(
                        "scheduling authorization is already durably consumed"
                    ) from exc
                consumption_row = connection.execute(
                    f"SELECT scheduling_authorization_id FROM {CLAIMS_TABLE} "
                    "WHERE scheduling_consumption_id=?",
                    (claim.scheduling_consumption_id,),
                ).fetchone()
                if consumption_row is not None:
                    raise AtomicSchedulingConsumptionRegistryIntegrityError(
                        "scheduling consumption identifier conflicts with registry"
                    ) from exc
                raise AtomicSchedulingConsumptionRegistryIntegrityError(
                    "claim identity conflicts with registry"
                ) from exc
            self._inject("after_insert")
            self._inject("before_commit")
            connection.commit()
            committed = True
            self._inject("after_commit")
            self._inject("before_readback")
            row = connection.execute(
                f"SELECT * FROM {CLAIMS_TABLE} "
                "WHERE scheduling_consumption_id=?",
                (claim.scheduling_consumption_id,),
            ).fetchone()
            if row is None:
                raise AtomicSchedulingConsumptionRegistryIntegrityError(
                    "committed claim could not be read back"
                )
            self._verify_row(row, request, claim)
            self._inject("after_readback")
            return self._claim_from_payload(row["claim_payload_json"])
        except (
            AtomicSchedulingConsumptionAlreadyConsumedError,
            AtomicSchedulingConsumptionRegistrySchemaError,
            AtomicSchedulingConsumptionRegistryIntegrityError,
        ):
            if connection is not None and not committed:
                connection.rollback()
            raise
        except sqlite3.DatabaseError as exc:
            if connection is not None and not committed:
                connection.rollback()
            if committed:
                raise AtomicSchedulingConsumptionRegistryIntegrityError(
                    "claim committed but registry read-back failed"
                ) from exc
            if "locked" in str(exc).lower() or "busy" in str(exc).lower():
                raise AtomicSchedulingConsumptionCommitError(
                    "atomic transaction could not acquire the registry"
                ) from exc
            raise AtomicSchedulingConsumptionRegistrySchemaError(
                "registry database is malformed or incompatible"
            ) from exc
        except Exception as exc:
            if connection is not None and not committed:
                connection.rollback()
            if committed:
                raise AtomicSchedulingConsumptionRegistryIntegrityError(
                    "claim committed but post-commit verification failed"
                ) from exc
            raise AtomicSchedulingConsumptionCommitError(
                "atomic claim transaction failed and was rolled back"
            ) from exc
        finally:
            if connection is not None:
                connection.close()

    @staticmethod
    def _verify_row(
        row: sqlite3.Row,
        request: AtomicSchedulingAuthorizationConsumptionRequest,
        claim: AtomicSchedulingAuthorizationConsumptionClaim,
    ) -> None:
        actual = tuple(row[name] for name in _CLAIM_COLUMNS)
        expected = AtomicSchedulingAuthorizationConsumptionRegistry._row_values(
            request, claim
        )
        if actual != expected:
            raise AtomicSchedulingConsumptionRegistryIntegrityError(
                "stored claim row does not equal supplied claim"
            )
        if canonical_json(json.loads(row["request_payload_json"])) != request.to_json():
            raise AtomicSchedulingConsumptionRegistryIntegrityError(
                "stored request payload is not canonical"
            )
        if canonical_json(json.loads(row["claim_payload_json"])) != claim.to_json():
            raise AtomicSchedulingConsumptionRegistryIntegrityError(
                "stored claim payload is not canonical"
            )

    @staticmethod
    def _claim_from_payload(
        payload_json: str,
    ) -> AtomicSchedulingAuthorizationConsumptionClaim:
        payload = json.loads(payload_json)
        payload.pop("claim_fingerprint", None)
        return AtomicSchedulingAuthorizationConsumptionClaim(
            **{
                item.name: (
                    tuple(payload[item.name])
                    if item.name == "upstream_fingerprint_chain"
                    else payload[item.name]
                )
                for item in fields(AtomicSchedulingAuthorizationConsumptionClaim)
                if item.init
            }
        )

    def read(
        self,
        scheduling_consumption_id: str,
    ) -> AtomicSchedulingAuthorizationConsumptionClaim | None:
        connection = self._connect()
        try:
            connection.execute("BEGIN")
            self._initialize_or_validate(connection)
            row = connection.execute(
                f"SELECT claim_payload_json FROM {CLAIMS_TABLE} "
                "WHERE scheduling_consumption_id=?",
                (scheduling_consumption_id,),
            ).fetchone()
            connection.commit()
            if row is None:
                return None
            return self._claim_from_payload(row[0])
        except sqlite3.DatabaseError as exc:
            connection.rollback()
            raise AtomicSchedulingConsumptionRegistrySchemaError(
                "registry database is malformed or incompatible"
            ) from exc
        finally:
            connection.close()

    def count_claims(self) -> int:
        connection = self._connect()
        try:
            connection.execute("BEGIN")
            self._initialize_or_validate(connection)
            count = int(
                connection.execute(
                    f"SELECT COUNT(*) FROM {CLAIMS_TABLE}"
                ).fetchone()[0]
            )
            connection.commit()
            return count
        except sqlite3.DatabaseError as exc:
            connection.rollback()
            raise AtomicSchedulingConsumptionRegistrySchemaError(
                "registry database is malformed or incompatible"
            ) from exc
        finally:
            connection.close()