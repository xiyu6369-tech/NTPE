"""Stage 7.2 durable atomic scheduling registry."""

from __future__ import annotations

import json
import pathlib
import sqlite3
from dataclasses import fields

from .errors import (
    ControlledRuntimeAlreadyScheduledError,
    ControlledRuntimeSchedulingCommitError,
    ControlledRuntimeSchedulingConflictError,
    ControlledRuntimeSchedulingDispatchError,
    ControlledRuntimeSchedulingDispatchIntegrityError,
    ControlledRuntimeSchedulingDispatchPathError,
    ControlledRuntimeSchedulingDispatchPolicyError,
    ControlledRuntimeSchedulingDispatchSchemaError,
)
from .models import (
    ControlledRuntimeDispatchPackage,
    ControlledRuntimeExecutionSchedule,
    ControlledRuntimeSchedulingRequest,
)
from .policy import (
    REGISTRY_SCHEMA_NAME,
    REGISTRY_SCHEMA_VERSION,
    ControlledRuntimeSchedulingPolicy,
)

METADATA_TABLE = "registry_metadata"
CONSUMPTION_TABLE = "stage72_queue_consumptions"
SCHEDULE_TABLE = "controlled_runtime_execution_schedules"
DISPATCH_TABLE = "controlled_runtime_dispatch_packages"


def _safe_path(database_path, allowed_root) -> pathlib.Path:
    if not isinstance(database_path, (str, pathlib.Path)) or not str(database_path).strip():
        raise ControlledRuntimeSchedulingDispatchPathError(
            "database_path is required; no default database is permitted"
        )
    if not isinstance(allowed_root, (str, pathlib.Path)) or not str(allowed_root).strip():
        raise ControlledRuntimeSchedulingDispatchPathError("allowed_root is required")
    text = str(database_path)
    lowered = text.lower()
    pure = pathlib.PurePath(text)
    if (
        text.startswith(("\\\\", "//"))
        or "://" in lowered
        or lowered.startswith(("file:", "http:", "https:", "sqlite:"))
        or any(part == ".." for part in pure.parts)
    ):
        raise ControlledRuntimeSchedulingDispatchPathError("unsafe database path")
    root = pathlib.Path(allowed_root)
    if not root.is_absolute():
        raise ControlledRuntimeSchedulingDispatchPathError(
            "allowed_root must be absolute"
        )
    try:
        resolved_root = root.resolve(strict=True)
    except OSError as error:
        raise ControlledRuntimeSchedulingDispatchPathError(
            "allowed_root does not exist"
        ) from error
    candidate = pathlib.Path(database_path)
    if candidate.drive and not candidate.is_absolute():
        raise ControlledRuntimeSchedulingDispatchPathError(
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
        raise ControlledRuntimeSchedulingDispatchPathError(
            "database path escapes allowed_root"
        ) from error
    return resolved


def _column_spec(connection, table):
    return tuple(
        (row["name"], row["type"].upper(), int(row["notnull"]), int(row["pk"]))
        for row in connection.execute(f"PRAGMA table_info({table})")
    )


def _unique_columns(connection, table):
    result = set()
    for row in connection.execute(f"PRAGMA index_list({table})"):
        if int(row["unique"]):
            result.add(
                tuple(
                    item["name"]
                    for item in connection.execute(
                        f"PRAGMA index_info({row['name']})"
                    )
                )
            )
    return frozenset(result)


class ControlledRuntimeSchedulingRegistry:
    """Persist consumption, schedule, and dispatch in one write transaction."""

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
        self._policy = ControlledRuntimeSchedulingPolicy()

    def _connect(self):
        connection = self._connection_factory(
            str(self.path), timeout=self.busy_timeout_ms / 1000
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
                "schema_name TEXT PRIMARY KEY,schema_version TEXT NOT NULL)"
            )
            connection.execute(
                f"INSERT INTO {METADATA_TABLE} VALUES(?,?)",
                (REGISTRY_SCHEMA_NAME, REGISTRY_SCHEMA_VERSION),
            )
            connection.execute(
                f"CREATE TABLE {CONSUMPTION_TABLE}("
                "queue_record_id TEXT PRIMARY KEY,"
                "queue_record_fingerprint TEXT UNIQUE NOT NULL,"
                "scheduling_request_id TEXT UNIQUE NOT NULL,"
                "request_fingerprint TEXT UNIQUE NOT NULL)"
            )
            connection.execute(
                f"CREATE TABLE {SCHEDULE_TABLE}("
                "schedule_id TEXT PRIMARY KEY,"
                "schedule_fingerprint TEXT UNIQUE NOT NULL,"
                "scheduling_request_id TEXT UNIQUE NOT NULL,"
                "request_fingerprint TEXT UNIQUE NOT NULL,"
                "queue_record_id TEXT UNIQUE NOT NULL,"
                "queue_record_fingerprint TEXT UNIQUE NOT NULL,"
                "request_payload_json TEXT NOT NULL,"
                "schedule_payload_json TEXT NOT NULL)"
            )
            connection.execute(
                f"CREATE TABLE {DISPATCH_TABLE}("
                "dispatch_package_id TEXT PRIMARY KEY,"
                "dispatch_fingerprint TEXT UNIQUE NOT NULL,"
                "schedule_id TEXT UNIQUE NOT NULL,"
                "schedule_fingerprint TEXT UNIQUE NOT NULL,"
                "dispatch_payload_json TEXT NOT NULL)"
            )
        elif objects != (
            ("table", DISPATCH_TABLE),
            ("table", SCHEDULE_TABLE),
            ("table", METADATA_TABLE),
            ("table", CONSUMPTION_TABLE),
        ):
            raise ControlledRuntimeSchedulingDispatchSchemaError(
                "registry contains noncanonical objects"
            )
        metadata = tuple(
            tuple(row)
            for row in connection.execute(
                f"SELECT schema_name,schema_version FROM {METADATA_TABLE}"
            )
        )
        if metadata != ((REGISTRY_SCHEMA_NAME, REGISTRY_SCHEMA_VERSION),):
            raise ControlledRuntimeSchedulingDispatchSchemaError(
                "noncanonical registry metadata"
            )
        expected = {
            METADATA_TABLE: (
                ("schema_name", "TEXT", 0, 1),
                ("schema_version", "TEXT", 1, 0),
            ),
            CONSUMPTION_TABLE: (
                ("queue_record_id", "TEXT", 0, 1),
                ("queue_record_fingerprint", "TEXT", 1, 0),
                ("scheduling_request_id", "TEXT", 1, 0),
                ("request_fingerprint", "TEXT", 1, 0),
            ),
            SCHEDULE_TABLE: (
                ("schedule_id", "TEXT", 0, 1),
                ("schedule_fingerprint", "TEXT", 1, 0),
                ("scheduling_request_id", "TEXT", 1, 0),
                ("request_fingerprint", "TEXT", 1, 0),
                ("queue_record_id", "TEXT", 1, 0),
                ("queue_record_fingerprint", "TEXT", 1, 0),
                ("request_payload_json", "TEXT", 1, 0),
                ("schedule_payload_json", "TEXT", 1, 0),
            ),
            DISPATCH_TABLE: (
                ("dispatch_package_id", "TEXT", 0, 1),
                ("dispatch_fingerprint", "TEXT", 1, 0),
                ("schedule_id", "TEXT", 1, 0),
                ("schedule_fingerprint", "TEXT", 1, 0),
                ("dispatch_payload_json", "TEXT", 1, 0),
            ),
        }
        uniques = {
            CONSUMPTION_TABLE: frozenset(
                {
                    ("queue_record_id",),
                    ("queue_record_fingerprint",),
                    ("scheduling_request_id",),
                    ("request_fingerprint",),
                }
            ),
            SCHEDULE_TABLE: frozenset(
                {
                    ("schedule_id",),
                    ("schedule_fingerprint",),
                    ("scheduling_request_id",),
                    ("request_fingerprint",),
                    ("queue_record_id",),
                    ("queue_record_fingerprint",),
                }
            ),
            DISPATCH_TABLE: frozenset(
                {
                    ("dispatch_package_id",),
                    ("dispatch_fingerprint",),
                    ("schedule_id",),
                    ("schedule_fingerprint",),
                }
            ),
        }
        for table, spec in expected.items():
            if _column_spec(connection, table) != spec:
                raise ControlledRuntimeSchedulingDispatchSchemaError(
                    f"noncanonical {table} schema"
                )
        for table, unique_spec in uniques.items():
            if _unique_columns(connection, table) != unique_spec:
                raise ControlledRuntimeSchedulingDispatchSchemaError(
                    f"noncanonical {table} uniqueness constraints"
                )

    @staticmethod
    def _from_payload(model_type, text, chain_field):
        try:
            payload = json.loads(text)
            model = model_type(
                **{
                    item.name: (
                        tuple(payload[item.name])
                        if item.name == chain_field
                        else payload[item.name]
                    )
                    for item in fields(model_type)
                    if item.init
                }
            )
            if text != model.to_json():
                raise ValueError("payload is noncanonical or inconsistent")
            return model
        except Exception as error:
            raise ControlledRuntimeSchedulingDispatchIntegrityError(
                f"malformed durable {model_type.__name__}"
            ) from error

    @classmethod
    def _validate_rows(cls, schedule_row, dispatch_row):
        request = cls._from_payload(
            ControlledRuntimeSchedulingRequest,
            schedule_row["request_payload_json"],
            "upstream_chain",
        )
        schedule = cls._from_payload(
            ControlledRuntimeExecutionSchedule,
            schedule_row["schedule_payload_json"],
            "canonical_chain",
        )
        dispatch = cls._from_payload(
            ControlledRuntimeDispatchPackage,
            dispatch_row["dispatch_payload_json"],
            "canonical_chain",
        )
        expected_schedule = (
            schedule.schedule_id,
            schedule.schedule_fingerprint,
            request.scheduling_request_id,
            request.request_fingerprint,
            request.queue_record_id,
            request.queue_record_fingerprint,
            request.to_json(),
            schedule.to_json(),
        )
        expected_dispatch = (
            dispatch.dispatch_package_id,
            dispatch.dispatch_fingerprint,
            schedule.schedule_id,
            schedule.schedule_fingerprint,
            dispatch.to_json(),
        )
        if tuple(schedule_row) != expected_schedule or tuple(dispatch_row) != expected_dispatch:
            raise ControlledRuntimeSchedulingDispatchIntegrityError(
                "durable row binding mismatch"
            )
        return request, schedule, dispatch

    def _inject(self, point):
        if self._failure_injector is not None:
            self._failure_injector(point)

    def schedule(
        self,
        request,
        schedule,
        dispatch,
        **authority,
    ):
        if not isinstance(request, ControlledRuntimeSchedulingRequest):
            raise TypeError("request must be a Stage 7.2 scheduling request")
        if not isinstance(schedule, ControlledRuntimeExecutionSchedule):
            raise TypeError("schedule must be a Stage 7.2 execution schedule")
        if not isinstance(dispatch, ControlledRuntimeDispatchPackage):
            raise TypeError("dispatch must be a Stage 7.2 dispatch package")
        connection = None
        committed = False
        try:
            connection = self._connect()
            connection.execute("BEGIN IMMEDIATE")
            self._initialize(connection)
            denials = self._policy.evaluate(request, **authority)
            if denials:
                raise ControlledRuntimeSchedulingDispatchPolicyError(denials)
            existing = connection.execute(
                f"SELECT * FROM {SCHEDULE_TABLE} WHERE "
                "scheduling_request_id=? OR request_fingerprint=? OR "
                "queue_record_id=? OR queue_record_fingerprint=? OR "
                "schedule_id=? OR schedule_fingerprint=?",
                (
                    request.scheduling_request_id,
                    request.request_fingerprint,
                    request.queue_record_id,
                    request.queue_record_fingerprint,
                    schedule.schedule_id,
                    schedule.schedule_fingerprint,
                ),
            ).fetchall()
            if existing:
                row = existing[0]
                dispatch_row = connection.execute(
                    f"SELECT * FROM {DISPATCH_TABLE} WHERE schedule_id=?",
                    (row["schedule_id"],),
                ).fetchone()
                if (
                    row["request_payload_json"] == request.to_json()
                    and row["schedule_payload_json"] == schedule.to_json()
                    and dispatch_row is not None
                    and dispatch_row["dispatch_payload_json"] == dispatch.to_json()
                ):
                    raise ControlledRuntimeAlreadyScheduledError(
                        "identical scheduling is a replay"
                    )
                raise ControlledRuntimeSchedulingConflictError(
                    "durable scheduling identity conflict"
                )
            self._inject("before_consumption_insert")
            connection.execute(
                f"INSERT INTO {CONSUMPTION_TABLE} VALUES(?,?,?,?)",
                (
                    request.queue_record_id,
                    request.queue_record_fingerprint,
                    request.scheduling_request_id,
                    request.request_fingerprint,
                ),
            )
            self._inject("after_consumption_insert")
            connection.execute(
                f"INSERT INTO {SCHEDULE_TABLE} VALUES(?,?,?,?,?,?,?,?)",
                (
                    schedule.schedule_id,
                    schedule.schedule_fingerprint,
                    request.scheduling_request_id,
                    request.request_fingerprint,
                    request.queue_record_id,
                    request.queue_record_fingerprint,
                    request.to_json(),
                    schedule.to_json(),
                ),
            )
            self._inject("after_schedule_insert")
            connection.execute(
                f"INSERT INTO {DISPATCH_TABLE} VALUES(?,?,?,?,?)",
                (
                    dispatch.dispatch_package_id,
                    dispatch.dispatch_fingerprint,
                    schedule.schedule_id,
                    schedule.schedule_fingerprint,
                    dispatch.to_json(),
                ),
            )
            self._inject("after_dispatch_insert")
            self._inject("before_commit")
            connection.commit()
            committed = True
            self._inject("after_commit")
            schedule_row = connection.execute(
                f"SELECT * FROM {SCHEDULE_TABLE} WHERE schedule_id=?",
                (schedule.schedule_id,),
            ).fetchone()
            dispatch_row = connection.execute(
                f"SELECT * FROM {DISPATCH_TABLE} WHERE dispatch_package_id=?",
                (dispatch.dispatch_package_id,),
            ).fetchone()
            if schedule_row is None or dispatch_row is None:
                raise ControlledRuntimeSchedulingDispatchIntegrityError(
                    "committed schedule or dispatch is missing"
                )
            stored_request, stored_schedule, stored_dispatch = self._validate_rows(
                schedule_row, dispatch_row
            )
            if (
                stored_request != request
                or stored_schedule != schedule
                or stored_dispatch != dispatch
            ):
                raise ControlledRuntimeSchedulingDispatchIntegrityError(
                    "durable read-back mismatch"
                )
            return stored_schedule, stored_dispatch
        except (
            ControlledRuntimeSchedulingDispatchError,
            TypeError,
            ValueError,
        ):
            if connection is not None and not committed:
                connection.rollback()
            raise
        except sqlite3.IntegrityError as error:
            if connection is not None and not committed:
                connection.rollback()
            raise ControlledRuntimeSchedulingConflictError(
                "durable scheduling uniqueness conflict"
            ) from error
        except Exception as error:
            if connection is not None and not committed:
                connection.rollback()
            raise ControlledRuntimeSchedulingCommitError(
                "atomic scheduling transaction failed"
            ) from error
        finally:
            if connection is not None:
                connection.close()

    def read(self, schedule_id: str):
        if not isinstance(schedule_id, str):
            raise TypeError("schedule_id must be str")
        connection = self._connect()
        connection.execute("BEGIN IMMEDIATE")
        try:
            self._initialize(connection)
            schedule_row = connection.execute(
                f"SELECT * FROM {SCHEDULE_TABLE} WHERE schedule_id=?",
                (schedule_id,),
            ).fetchone()
            if schedule_row is None:
                connection.commit()
                return None
            dispatch_row = connection.execute(
                f"SELECT * FROM {DISPATCH_TABLE} WHERE schedule_id=?",
                (schedule_id,),
            ).fetchone()
            if dispatch_row is None:
                raise ControlledRuntimeSchedulingDispatchIntegrityError(
                    "schedule has no dispatch package"
                )
            _, schedule, dispatch = self._validate_rows(schedule_row, dispatch_row)
            connection.commit()
            return schedule, dispatch
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def counts(self) -> tuple[int, int, int]:
        connection = self._connect()
        connection.execute("BEGIN IMMEDIATE")
        try:
            self._initialize(connection)
            counts = tuple(
                int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
                for table in (CONSUMPTION_TABLE, SCHEDULE_TABLE, DISPATCH_TABLE)
            )
            connection.commit()
            return counts
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
