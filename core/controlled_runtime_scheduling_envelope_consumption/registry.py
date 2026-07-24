"""Dedicated atomic SQLite registry for Stage 6.9."""

from __future__ import annotations

import json
import pathlib
import sqlite3
from dataclasses import fields
from typing import Callable

from .errors import (
    SchedulingEnvelopeAlreadyConsumedError,
    SchedulingEnvelopeConsumptionCommitError,
    SchedulingEnvelopeConsumptionConflictError,
    SchedulingEnvelopeConsumptionRegistryIntegrityError,
    SchedulingEnvelopeConsumptionRegistryPathError,
    SchedulingEnvelopeConsumptionRegistrySchemaError,
)
from .models import (
    ControlledRuntimeSchedulingEnvelopeConsumptionClaim,
    ControlledRuntimeSchedulingEnvelopeConsumptionRequest,
)
from .policy import (
    REGISTRY_COMPONENT,
    REGISTRY_SCHEMA_NAME,
    REGISTRY_SCHEMA_VERSION,
)
from .serialization import canonical_json

METADATA_TABLE = "registry_metadata"
CLAIMS_TABLE = "scheduling_envelope_consumption_claims"
_METADATA_COLUMNS = ("schema_name", "schema_version", "component")
_CLAIM_COLUMNS = (
    "consumption_request_id",
    "request_fingerprint",
    "consumption_claim_id",
    "claim_fingerprint",
    "scheduling_envelope_id",
    "scheduling_envelope_fingerprint",
    "scheduling_envelope_request_id",
    "scheduling_envelope_request_fingerprint",
    "stage67_consumption_claim_id",
    "stage67_claim_fingerprint",
    "stage66_scheduling_authorization_id",
    "stage66_decision_fingerprint",
    "runtime_boundary_id",
    "runtime_boundary_kind",
    "selected_adapter_index",
    "unit_scope",
    "canonical_chain_json",
    "request_payload_json",
    "claim_payload_json",
)


def _safe_path(
    database_path: str | pathlib.Path,
    allowed_root: str | pathlib.Path,
) -> pathlib.Path:
    if not isinstance(database_path, (str, pathlib.Path)) or not str(
        database_path
    ).strip():
        raise SchedulingEnvelopeConsumptionRegistryPathError(
            "database_path is required"
        )
    if not isinstance(allowed_root, (str, pathlib.Path)) or not str(
        allowed_root
    ).strip():
        raise SchedulingEnvelopeConsumptionRegistryPathError(
            "allowed_root is required"
        )
    path_text = str(database_path)
    if "\x00" in path_text or path_text.lower().startswith(
        ("file:", "http:", "https:", "sqlite:")
    ):
        raise SchedulingEnvelopeConsumptionRegistryPathError(
            "malformed or URI database paths are unsupported"
        )
    if path_text.startswith(("\\\\", "//")) or any(
        part == ".." for part in pathlib.PurePath(path_text).parts
    ):
        raise SchedulingEnvelopeConsumptionRegistryPathError(
            "network paths and traversal are unsupported"
        )
    root_input = pathlib.Path(allowed_root)
    if not root_input.is_absolute():
        raise SchedulingEnvelopeConsumptionRegistryPathError(
            "allowed_root must be absolute"
        )
    try:
        root = root_input.resolve(strict=True)
    except OSError as exc:
        raise SchedulingEnvelopeConsumptionRegistryPathError(
            "allowed_root must exist"
        ) from exc
    if not root.is_dir():
        raise SchedulingEnvelopeConsumptionRegistryPathError(
            "allowed_root must be a directory"
        )
    candidate = pathlib.Path(database_path)
    if not candidate.is_absolute():
        candidate = root / candidate
    try:
        parent = candidate.parent.resolve(strict=True)
        resolved = parent / candidate.name
        resolved.relative_to(root)
        if candidate.exists():
            resolved = candidate.resolve(strict=True)
            resolved.relative_to(root)
            if resolved.is_dir():
                raise SchedulingEnvelopeConsumptionRegistryPathError(
                    "database_path must not be a directory"
                )
    except (OSError, ValueError) as exc:
        raise SchedulingEnvelopeConsumptionRegistryPathError(
            "database path must resolve beneath allowed_root"
        ) from exc
    return resolved


class ControlledRuntimeSchedulingEnvelopeConsumptionRegistry:
    """One explicitly located Stage 6.9 durable registry."""

    def __init__(
        self,
        database_path: str | pathlib.Path,
        *,
        allowed_root: str | pathlib.Path,
        busy_timeout_ms: int = 5000,
        failure_injector: Callable[[str], None] | None = None,
        connection_factory: Callable[..., sqlite3.Connection] = sqlite3.connect,
    ) -> None:
        self.path = _safe_path(database_path, allowed_root)
        if type(busy_timeout_ms) is not int or busy_timeout_ms < 1:
            raise ValueError("busy_timeout_ms must be a positive integer")
        self.allowed_root = pathlib.Path(allowed_root).resolve(strict=True)
        self.busy_timeout_ms = busy_timeout_ms
        self._failure_injector = failure_injector
        self._connection_factory = connection_factory

    def _connect(self) -> sqlite3.Connection:
        connection = self._connection_factory(
            str(self.path), timeout=self.busy_timeout_ms / 1000
        )
        connection.row_factory = sqlite3.Row
        connection.execute(f"PRAGMA busy_timeout={self.busy_timeout_ms}")
        connection.execute("PRAGMA synchronous=FULL")
        return connection

    def _inject(self, point: str) -> None:
        if self._failure_injector:
            self._failure_injector(point)

    @staticmethod
    def _initialize_or_validate(connection: sqlite3.Connection) -> None:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%'"
            )
        }
        if not tables:
            connection.execute(
                f"CREATE TABLE {METADATA_TABLE} ("
                "schema_name TEXT PRIMARY KEY NOT NULL,"
                "schema_version TEXT NOT NULL,component TEXT NOT NULL)"
            )
            connection.execute(
                f"INSERT INTO {METADATA_TABLE} VALUES (?,?,?)",
                (
                    REGISTRY_SCHEMA_NAME,
                    REGISTRY_SCHEMA_VERSION,
                    REGISTRY_COMPONENT,
                ),
            )
            connection.execute(
                f"CREATE TABLE {CLAIMS_TABLE} ("
                "consumption_request_id TEXT PRIMARY KEY NOT NULL,"
                "request_fingerprint TEXT UNIQUE NOT NULL,"
                "consumption_claim_id TEXT UNIQUE NOT NULL,"
                "claim_fingerprint TEXT UNIQUE NOT NULL,"
                "scheduling_envelope_id TEXT UNIQUE NOT NULL,"
                "scheduling_envelope_fingerprint TEXT UNIQUE NOT NULL,"
                "scheduling_envelope_request_id TEXT NOT NULL,"
                "scheduling_envelope_request_fingerprint TEXT NOT NULL,"
                "stage67_consumption_claim_id TEXT NOT NULL,"
                "stage67_claim_fingerprint TEXT NOT NULL,"
                "stage66_scheduling_authorization_id TEXT NOT NULL,"
                "stage66_decision_fingerprint TEXT NOT NULL,"
                "runtime_boundary_id TEXT NOT NULL,"
                "runtime_boundary_kind TEXT NOT NULL,"
                "selected_adapter_index INTEGER NOT NULL CHECK(selected_adapter_index>=0),"
                "unit_scope INTEGER NOT NULL CHECK(unit_scope=1),"
                "canonical_chain_json TEXT NOT NULL,"
                "request_payload_json TEXT NOT NULL,"
                "claim_payload_json TEXT NOT NULL)"
            )
            return
        if tables != {METADATA_TABLE, CLAIMS_TABLE}:
            raise SchedulingEnvelopeConsumptionRegistrySchemaError(
                "registry table set is not canonical"
            )
        metadata_columns = tuple(
            row[1] for row in connection.execute(f"PRAGMA table_info({METADATA_TABLE})")
        )
        claim_columns = tuple(
            row[1] for row in connection.execute(f"PRAGMA table_info({CLAIMS_TABLE})")
        )
        if metadata_columns != _METADATA_COLUMNS or claim_columns != _CLAIM_COLUMNS:
            raise SchedulingEnvelopeConsumptionRegistrySchemaError(
                "registry columns are not canonical"
            )
        metadata = connection.execute(
            f"SELECT schema_name,schema_version,component FROM {METADATA_TABLE}"
        ).fetchall()
        if len(metadata) != 1 or tuple(metadata[0]) != (
            REGISTRY_SCHEMA_NAME,
            REGISTRY_SCHEMA_VERSION,
            REGISTRY_COMPONENT,
        ):
            raise SchedulingEnvelopeConsumptionRegistrySchemaError(
                "registry metadata is not canonical"
            )
        unique_sets = {
            tuple(
                item[2]
                for item in connection.execute(
                    f"PRAGMA index_info({index_row[1]})"
                )
            )
            for index_row in connection.execute(f"PRAGMA index_list({CLAIMS_TABLE})")
            if index_row[2]
        }
        for required in (
            ("consumption_request_id",),
            ("request_fingerprint",),
            ("consumption_claim_id",),
            ("claim_fingerprint",),
            ("scheduling_envelope_id",),
            ("scheduling_envelope_fingerprint",),
        ):
            if required not in unique_sets:
                raise SchedulingEnvelopeConsumptionRegistrySchemaError(
                    "required uniqueness constraint is missing"
                )

    @staticmethod
    def _row_values(
        request: ControlledRuntimeSchedulingEnvelopeConsumptionRequest,
        claim: ControlledRuntimeSchedulingEnvelopeConsumptionClaim,
    ) -> tuple[object, ...]:
        return (
            request.consumption_request_id,
            request.request_fingerprint,
            claim.consumption_claim_id,
            claim.claim_fingerprint,
            claim.scheduling_envelope_id,
            claim.scheduling_envelope_fingerprint,
            claim.scheduling_envelope_request_id,
            claim.scheduling_envelope_request_fingerprint,
            claim.stage67_consumption_claim_id,
            claim.stage67_claim_fingerprint,
            claim.stage66_scheduling_authorization_id,
            claim.stage66_decision_fingerprint,
            claim.runtime_boundary_id,
            claim.runtime_boundary_kind,
            claim.selected_adapter_index,
            claim.unit_scope,
            canonical_json(claim.canonical_chain),
            request.to_json(),
            claim.to_json(),
        )

    def claim(
        self,
        request: ControlledRuntimeSchedulingEnvelopeConsumptionRequest,
        claim: ControlledRuntimeSchedulingEnvelopeConsumptionClaim,
    ) -> ControlledRuntimeSchedulingEnvelopeConsumptionClaim:
        connection: sqlite3.Connection | None = None
        committed = False
        try:
            connection = self._connect()
            connection.execute("BEGIN IMMEDIATE")
            self._initialize_or_validate(connection)
            self._inject("before_insert")
            try:
                connection.execute(
                    f"INSERT INTO {CLAIMS_TABLE} ({','.join(_CLAIM_COLUMNS)}) "
                    f"VALUES ({','.join('?' for _ in _CLAIM_COLUMNS)})",
                    self._row_values(request, claim),
                )
            except sqlite3.IntegrityError as exc:
                replay = connection.execute(
                    f"SELECT consumption_request_id FROM {CLAIMS_TABLE} "
                    "WHERE scheduling_envelope_id=? OR "
                    "scheduling_envelope_fingerprint=?",
                    (
                        request.scheduling_envelope_id,
                        request.scheduling_envelope_fingerprint,
                    ),
                ).fetchone()
                if replay is not None:
                    raise SchedulingEnvelopeAlreadyConsumedError(
                        "scheduling envelope is already durably consumed"
                    ) from exc
                raise SchedulingEnvelopeConsumptionConflictError(
                    "request or claim identity conflicts with durable state"
                ) from exc
            self._inject("after_insert")
            connection.commit()
            committed = True
            self._inject("after_commit")
            row = connection.execute(
                f"SELECT * FROM {CLAIMS_TABLE} WHERE consumption_request_id=?",
                (request.consumption_request_id,),
            ).fetchone()
            if row is None:
                raise SchedulingEnvelopeConsumptionRegistryIntegrityError(
                    "committed claim could not be read back"
                )
            self._verify_row(row, request, claim)
            return self._claim_from_payload(row["claim_payload_json"])
        except (
            SchedulingEnvelopeAlreadyConsumedError,
            SchedulingEnvelopeConsumptionConflictError,
            SchedulingEnvelopeConsumptionRegistryIntegrityError,
            SchedulingEnvelopeConsumptionRegistrySchemaError,
        ):
            if connection is not None and not committed:
                connection.rollback()
            raise
        except sqlite3.DatabaseError as exc:
            if connection is not None and not committed:
                connection.rollback()
            if committed:
                raise SchedulingEnvelopeConsumptionRegistryIntegrityError(
                    "claim committed but durable read-back failed"
                ) from exc
            if "locked" in str(exc).lower() or "busy" in str(exc).lower():
                raise SchedulingEnvelopeConsumptionCommitError(
                    "atomic transaction could not acquire registry"
                ) from exc
            raise SchedulingEnvelopeConsumptionRegistrySchemaError(
                "registry database is malformed"
            ) from exc
        except Exception as exc:
            if connection is not None and not committed:
                connection.rollback()
            if committed:
                raise SchedulingEnvelopeConsumptionRegistryIntegrityError(
                    "post-commit verification failed"
                ) from exc
            raise SchedulingEnvelopeConsumptionCommitError(
                "transaction failed and rolled back"
            ) from exc
        finally:
            if connection is not None:
                connection.close()

    @staticmethod
    def _verify_row(
        row: sqlite3.Row,
        request: ControlledRuntimeSchedulingEnvelopeConsumptionRequest,
        claim: ControlledRuntimeSchedulingEnvelopeConsumptionClaim,
    ) -> None:
        if tuple(row[name] for name in _CLAIM_COLUMNS) != (
            ControlledRuntimeSchedulingEnvelopeConsumptionRegistry._row_values(
                request, claim
            )
        ):
            raise SchedulingEnvelopeConsumptionRegistryIntegrityError(
                "stored row does not equal canonical claim"
            )
        try:
            request_json = canonical_json(json.loads(row["request_payload_json"]))
            claim_json = canonical_json(json.loads(row["claim_payload_json"]))
            chain_json = canonical_json(json.loads(row["canonical_chain_json"]))
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise SchedulingEnvelopeConsumptionRegistryIntegrityError(
                "stored payload is malformed"
            ) from exc
        if (
            request_json != request.to_json()
            or claim_json != claim.to_json()
            or chain_json != canonical_json(claim.canonical_chain)
        ):
            raise SchedulingEnvelopeConsumptionRegistryIntegrityError(
                "stored payload is not canonical"
            )

    @staticmethod
    def _claim_from_payload(
        payload_json: str,
    ) -> ControlledRuntimeSchedulingEnvelopeConsumptionClaim:
        try:
            payload = json.loads(payload_json)
            payload.pop("consumption_claim_id", None)
            payload.pop("claim_fingerprint", None)
            return ControlledRuntimeSchedulingEnvelopeConsumptionClaim(
                **{
                    item.name: (
                        tuple(payload[item.name])
                        if item.name == "canonical_chain"
                        else payload[item.name]
                    )
                    for item in fields(
                        ControlledRuntimeSchedulingEnvelopeConsumptionClaim
                    )
                    if item.init
                }
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise SchedulingEnvelopeConsumptionRegistryIntegrityError(
                "durable claim payload is malformed"
            ) from exc

    def read(
        self, consumption_request_id: str
    ) -> ControlledRuntimeSchedulingEnvelopeConsumptionClaim | None:
        connection = self._connect()
        try:
            connection.execute("BEGIN")
            self._initialize_or_validate(connection)
            row = connection.execute(
                f"SELECT claim_payload_json FROM {CLAIMS_TABLE} "
                "WHERE consumption_request_id=?",
                (consumption_request_id,),
            ).fetchone()
            connection.commit()
            return None if row is None else self._claim_from_payload(row[0])
        except sqlite3.DatabaseError as exc:
            connection.rollback()
            raise SchedulingEnvelopeConsumptionRegistrySchemaError(
                "registry database is malformed"
            ) from exc
        finally:
            connection.close()

    def count_claims(self) -> int:
        connection = self._connect()
        try:
            connection.execute("BEGIN")
            self._initialize_or_validate(connection)
            count = connection.execute(
                f"SELECT COUNT(*) FROM {CLAIMS_TABLE}"
            ).fetchone()[0]
            connection.commit()
            return int(count)
        finally:
            connection.close()
