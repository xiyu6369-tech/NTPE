"""Stage 7.1 durable controlled Runtime queue registry."""

from __future__ import annotations

import json
import pathlib
import sqlite3
from dataclasses import fields

from .errors import (
    ControlledRuntimeQueueAdmissionCommitError,
    ControlledRuntimeQueueAdmissionConflictError,
    ControlledRuntimeQueueAdmissionError,
    ControlledRuntimeQueueAdmissionIntegrityError,
    ControlledRuntimeQueueAdmissionPathError,
    ControlledRuntimeQueueAdmissionPolicyError,
    ControlledRuntimeQueueAdmissionSchemaError,
    ControlledRuntimeQueueAlreadyAdmittedError,
)
from .models import (
    ControlledRuntimeQueueAdmissionRequest,
    ControlledRuntimeQueueRecord,
)
from .policy import (
    REGISTRY_SCHEMA_NAME,
    REGISTRY_SCHEMA_VERSION,
    ControlledRuntimeQueueAdmissionPolicy,
)

METADATA_TABLE = "registry_metadata"
QUEUE_TABLE = "controlled_runtime_queue_records"
QUEUE_COLUMNS = (
    "admission_request_id",
    "request_fingerprint",
    "queue_record_id",
    "queue_record_fingerprint",
    "stage613_claim_id",
    "stage613_claim_fingerprint",
    "stage612_record_id",
    "stage612_record_fingerprint",
    "request_payload_json",
    "queue_record_payload_json",
)
_METADATA_COLUMNS = ("schema_name", "schema_version")
_UNIQUE_COLUMNS = frozenset(
    (
        ("admission_request_id",),
        ("request_fingerprint",),
        ("queue_record_id",),
        ("queue_record_fingerprint",),
        ("stage613_claim_id",),
        ("stage613_claim_fingerprint",),
        ("stage612_record_id",),
        ("stage612_record_fingerprint",),
    )
)


def _safe_path(database_path, allowed_root) -> pathlib.Path:
    if (
        not isinstance(database_path, (str, pathlib.Path))
        or not str(database_path).strip()
    ):
        raise ControlledRuntimeQueueAdmissionPathError(
            "database_path is required; no default database is permitted"
        )
    if (
        not isinstance(allowed_root, (str, pathlib.Path))
        or not str(allowed_root).strip()
    ):
        raise ControlledRuntimeQueueAdmissionPathError(
            "allowed_root is required"
        )
    text = str(database_path)
    lowered = text.lower()
    pure = pathlib.PurePath(text)
    if (
        text.startswith(("\\\\", "//"))
        or "://" in lowered
        or lowered.startswith(("file:", "http:", "https:", "sqlite:"))
        or any(part == ".." for part in pure.parts)
    ):
        raise ControlledRuntimeQueueAdmissionPathError("unsafe database path")
    root = pathlib.Path(allowed_root)
    if not root.is_absolute():
        raise ControlledRuntimeQueueAdmissionPathError(
            "allowed_root must be absolute"
        )
    try:
        resolved_root = root.resolve(strict=True)
    except OSError as error:
        raise ControlledRuntimeQueueAdmissionPathError(
            "allowed_root does not exist"
        ) from error
    candidate = pathlib.Path(database_path)
    if candidate.drive and not candidate.is_absolute():
        raise ControlledRuntimeQueueAdmissionPathError(
            "drive-relative database paths are forbidden"
        )
    if not candidate.is_absolute():
        candidate = resolved_root / candidate
    try:
        resolved = candidate.parent.resolve(strict=True) / candidate.name
        resolved.relative_to(resolved_root)
        if candidate.exists():
            resolved = candidate.resolve(strict=True)
            resolved.relative_to(resolved_root)
    except (OSError, ValueError) as error:
        raise ControlledRuntimeQueueAdmissionPathError(
            "database path escapes allowed_root"
        ) from error
    return resolved


def _column_spec(connection, table: str) -> tuple[tuple[object, ...], ...]:
    return tuple(
        (
            row["name"],
            row["type"].upper(),
            int(row["notnull"]),
            int(row["pk"]),
        )
        for row in connection.execute(f"PRAGMA table_info({table})")
    )


def _unique_columns(connection) -> frozenset[tuple[str, ...]]:
    indexes: set[tuple[str, ...]] = set()
    for row in connection.execute(f"PRAGMA index_list({QUEUE_TABLE})"):
        if not int(row["unique"]):
            continue
        indexes.add(
            tuple(
                item["name"]
                for item in connection.execute(
                    f"PRAGMA index_info({row['name']})"
                )
            )
        )
    return frozenset(indexes)


class ControlledRuntimeQueueRegistry:
    """Own the only Stage 7.1 SQLite persistence boundary."""

    def __init__(
        self,
        database_path,
        *,
        allowed_root,
        busy_timeout_ms: int = 5000,
        failure_injector=None,
        connection_factory=sqlite3.connect,
    ):
        self.path = _safe_path(database_path, allowed_root)
        if type(busy_timeout_ms) is not int or busy_timeout_ms <= 0:
            raise ValueError("busy_timeout_ms must be a positive integer")
        self.busy_timeout_ms = busy_timeout_ms
        self._failure_injector = failure_injector
        self._connection_factory = connection_factory
        self._policy = ControlledRuntimeQueueAdmissionPolicy()

    def _connect(self):
        connection = self._connection_factory(
            str(self.path),
            timeout=self.busy_timeout_ms / 1000,
        )
        connection.row_factory = sqlite3.Row
        connection.execute(f"PRAGMA busy_timeout={self.busy_timeout_ms}")
        connection.execute("PRAGMA synchronous=FULL")
        return connection

    @staticmethod
    def _initialize(connection) -> None:
        objects = tuple(
            tuple(row)
            for row in connection.execute(
                "SELECT type,name FROM sqlite_master "
                "WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name"
            )
        )
        if not objects:
            connection.execute(
                f"CREATE TABLE {METADATA_TABLE}("
                "schema_name TEXT PRIMARY KEY,"
                "schema_version TEXT NOT NULL)"
            )
            connection.execute(
                f"INSERT INTO {METADATA_TABLE} VALUES(?,?)",
                (REGISTRY_SCHEMA_NAME, REGISTRY_SCHEMA_VERSION),
            )
            connection.execute(
                f"CREATE TABLE {QUEUE_TABLE}("
                "admission_request_id TEXT PRIMARY KEY,"
                "request_fingerprint TEXT UNIQUE NOT NULL,"
                "queue_record_id TEXT UNIQUE NOT NULL,"
                "queue_record_fingerprint TEXT UNIQUE NOT NULL,"
                "stage613_claim_id TEXT UNIQUE NOT NULL,"
                "stage613_claim_fingerprint TEXT UNIQUE NOT NULL,"
                "stage612_record_id TEXT UNIQUE NOT NULL,"
                "stage612_record_fingerprint TEXT UNIQUE NOT NULL,"
                "request_payload_json TEXT NOT NULL,"
                "queue_record_payload_json TEXT NOT NULL)"
            )
        elif objects != (
            ("table", QUEUE_TABLE),
            ("table", METADATA_TABLE),
        ):
            raise ControlledRuntimeQueueAdmissionSchemaError(
                "registry contains noncanonical objects"
            )

        metadata = tuple(
            tuple(row)
            for row in connection.execute(
                f"SELECT schema_name,schema_version FROM {METADATA_TABLE}"
            )
        )
        if metadata != ((REGISTRY_SCHEMA_NAME, REGISTRY_SCHEMA_VERSION),):
            raise ControlledRuntimeQueueAdmissionSchemaError(
                "noncanonical registry metadata"
            )
        expected_metadata = (
            ("schema_name", "TEXT", 0, 1),
            ("schema_version", "TEXT", 1, 0),
        )
        expected_queue = (
            ("admission_request_id", "TEXT", 0, 1),
            ("request_fingerprint", "TEXT", 1, 0),
            ("queue_record_id", "TEXT", 1, 0),
            ("queue_record_fingerprint", "TEXT", 1, 0),
            ("stage613_claim_id", "TEXT", 1, 0),
            ("stage613_claim_fingerprint", "TEXT", 1, 0),
            ("stage612_record_id", "TEXT", 1, 0),
            ("stage612_record_fingerprint", "TEXT", 1, 0),
            ("request_payload_json", "TEXT", 1, 0),
            ("queue_record_payload_json", "TEXT", 1, 0),
        )
        if _column_spec(connection, METADATA_TABLE) != expected_metadata:
            raise ControlledRuntimeQueueAdmissionSchemaError(
                "noncanonical metadata-table schema"
            )
        if _column_spec(connection, QUEUE_TABLE) != expected_queue:
            raise ControlledRuntimeQueueAdmissionSchemaError(
                "noncanonical queue-table schema"
            )
        if _unique_columns(connection) != _UNIQUE_COLUMNS:
            raise ControlledRuntimeQueueAdmissionSchemaError(
                "noncanonical durable uniqueness constraints"
            )

    @staticmethod
    def _row(request, queue_record) -> tuple[str, ...]:
        return (
            request.admission_request_id,
            request.request_fingerprint,
            queue_record.queue_record_id,
            queue_record.queue_record_fingerprint,
            queue_record.stage613_claim_id,
            queue_record.stage613_claim_fingerprint,
            queue_record.stage612_record_id,
            queue_record.stage612_record_fingerprint,
            request.to_json(),
            queue_record.to_json(),
        )

    @staticmethod
    def _request_from_payload(text: str) -> ControlledRuntimeQueueAdmissionRequest:
        try:
            payload = json.loads(text)
            request = ControlledRuntimeQueueAdmissionRequest(
                **{
                    item.name: (
                        tuple(payload[item.name])
                        if item.name == "upstream_chain"
                        else payload[item.name]
                    )
                    for item in fields(ControlledRuntimeQueueAdmissionRequest)
                    if item.init
                }
            )
            if text != request.to_json():
                raise ValueError("request payload is noncanonical or inconsistent")
            return request
        except Exception as error:
            raise ControlledRuntimeQueueAdmissionIntegrityError(
                "malformed durable admission request"
            ) from error

    @staticmethod
    def _record_from_payload(text: str) -> ControlledRuntimeQueueRecord:
        try:
            payload = json.loads(text)
            record = ControlledRuntimeQueueRecord(
                **{
                    item.name: (
                        tuple(payload[item.name])
                        if item.name == "canonical_chain"
                        else payload[item.name]
                    )
                    for item in fields(ControlledRuntimeQueueRecord)
                    if item.init
                }
            )
            if text != record.to_json():
                raise ValueError("queue-record payload is noncanonical or inconsistent")
            return record
        except Exception as error:
            raise ControlledRuntimeQueueAdmissionIntegrityError(
                "malformed durable queue record"
            ) from error

    @classmethod
    def _validate_row(cls, row):
        request = cls._request_from_payload(row["request_payload_json"])
        record = cls._record_from_payload(row["queue_record_payload_json"])
        if tuple(row[name] for name in QUEUE_COLUMNS) != cls._row(
            request,
            record,
        ):
            raise ControlledRuntimeQueueAdmissionIntegrityError(
                "durable queue-row binding mismatch"
            )
        return record

    def _inject(self, point: str) -> None:
        if self._failure_injector is not None:
            self._failure_injector(point)

    def admit(
        self,
        request,
        queue_record,
        *,
        stage613_claim,
        stage613_request,
        stage613_result,
        stage613_verification_context,
    ) -> ControlledRuntimeQueueRecord:
        if not isinstance(request, ControlledRuntimeQueueAdmissionRequest):
            raise TypeError("request must be a Stage 7.1 admission request")
        if not isinstance(queue_record, ControlledRuntimeQueueRecord):
            raise TypeError("queue_record must be a Stage 7.1 queue record")
        connection = None
        committed = False
        try:
            connection = self._connect()
            connection.execute("BEGIN IMMEDIATE")
            self._initialize(connection)
            denials = self._policy.evaluate(
                request,
                stage613_claim=stage613_claim,
                stage613_request=stage613_request,
                stage613_result=stage613_result,
                stage613_verification_context=stage613_verification_context,
            )
            if denials:
                raise ControlledRuntimeQueueAdmissionPolicyError(denials)
            self._inject("before_insert")
            try:
                connection.execute(
                    f"INSERT INTO {QUEUE_TABLE} VALUES(?,?,?,?,?,?,?,?,?,?)",
                    self._row(request, queue_record),
                )
            except sqlite3.IntegrityError as error:
                matches = connection.execute(
                    f"SELECT * FROM {QUEUE_TABLE} WHERE "
                    "admission_request_id=? OR request_fingerprint=? OR "
                    "queue_record_id=? OR queue_record_fingerprint=? OR "
                    "stage613_claim_id=? OR stage613_claim_fingerprint=? OR "
                    "stage612_record_id=? OR stage612_record_fingerprint=?",
                    self._row(request, queue_record)[:8],
                ).fetchall()
                if any(
                    tuple(row[name] for name in QUEUE_COLUMNS)
                    == self._row(request, queue_record)
                    for row in matches
                ):
                    raise ControlledRuntimeQueueAlreadyAdmittedError(
                        "identical queue admission is a replay"
                    ) from error
                raise ControlledRuntimeQueueAdmissionConflictError(
                    "durable queue identity conflict"
                ) from error
            self._inject("after_insert")
            self._inject("before_commit")
            connection.commit()
            committed = True
            self._inject("after_commit")
            self._inject("before_readback")
            row = connection.execute(
                f"SELECT * FROM {QUEUE_TABLE} WHERE admission_request_id=?",
                (request.admission_request_id,),
            ).fetchone()
            if row is None:
                raise ControlledRuntimeQueueAdmissionIntegrityError(
                    "committed queue record is missing"
                )
            record = self._validate_row(row)
            if tuple(row[name] for name in QUEUE_COLUMNS) != self._row(
                request,
                queue_record,
            ):
                raise ControlledRuntimeQueueAdmissionIntegrityError(
                    "durable read-back mismatch"
                )
            return record
        except (
            ControlledRuntimeQueueAdmissionError,
            TypeError,
            ValueError,
        ):
            if connection is not None and not committed:
                connection.rollback()
            raise
        except Exception as error:
            if connection is not None and not committed:
                connection.rollback()
            raise ControlledRuntimeQueueAdmissionCommitError(
                "atomic queue admission failed"
            ) from error
        finally:
            if connection is not None:
                connection.close()

    def read(self, admission_request_id: str):
        if not isinstance(admission_request_id, str):
            raise TypeError("admission_request_id must be str")
        connection = self._connect()
        connection.execute("BEGIN IMMEDIATE")
        try:
            self._initialize(connection)
            row = connection.execute(
                f"SELECT * FROM {QUEUE_TABLE} WHERE admission_request_id=?",
                (admission_request_id,),
            ).fetchone()
            record = None if row is None else self._validate_row(row)
            connection.commit()
            return record
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def count_records(self) -> int:
        connection = self._connect()
        connection.execute("BEGIN IMMEDIATE")
        try:
            self._initialize(connection)
            count = int(
                connection.execute(
                    f"SELECT COUNT(*) FROM {QUEUE_TABLE}"
                ).fetchone()[0]
            )
            connection.commit()
            return count
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
