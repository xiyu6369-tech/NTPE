"""Atomic Stage 6.11 SQLite registry."""
from __future__ import annotations
import json,pathlib,sqlite3
from dataclasses import fields
from .errors import *
from .models import *
from .policy import *
from .serialization import canonical_json
TABLE="queue_admission_authorization_consumptions"
COLUMNS=("consumption_request_id","request_fingerprint","consumption_claim_id","claim_fingerprint","authorization_id","decision_fingerprint","request_payload_json","claim_payload_json")
def _path(database_path,allowed_root):
    if not isinstance(database_path,(str,pathlib.Path)) or not str(database_path).strip(): raise QueueAdmissionAuthorizationConsumptionPathError("database_path required")
    if not isinstance(allowed_root,(str,pathlib.Path)) or not str(allowed_root).strip(): raise QueueAdmissionAuthorizationConsumptionPathError("allowed_root required")
    text=str(database_path)
    if text.startswith(("\\\\","//")) or any(p==".." for p in pathlib.PurePath(text).parts) or text.lower().startswith(("file:","http:","sqlite:")): raise QueueAdmissionAuthorizationConsumptionPathError("unsafe path")
    root=pathlib.Path(allowed_root)
    if not root.is_absolute(): raise QueueAdmissionAuthorizationConsumptionPathError("allowed_root must be absolute")
    try: root=root.resolve(strict=True)
    except OSError as e: raise QueueAdmissionAuthorizationConsumptionPathError("allowed_root missing") from e
    candidate=pathlib.Path(database_path)
    if not candidate.is_absolute(): candidate=root/candidate
    try:
        resolved=candidate.parent.resolve(strict=True)/candidate.name
        resolved.relative_to(root)
        if candidate.exists(): resolved=candidate.resolve(strict=True);resolved.relative_to(root)
    except (OSError,ValueError) as e: raise QueueAdmissionAuthorizationConsumptionPathError("path escapes allowed_root") from e
    return resolved
class ControlledRuntimeQueueAdmissionAuthorizationConsumptionRegistry:
    def __init__(self,database_path,*,allowed_root,busy_timeout_ms=5000,failure_injector=None,connection_factory=sqlite3.connect):
        self.path=_path(database_path,allowed_root);self.busy_timeout_ms=busy_timeout_ms;self._injector=failure_injector;self._factory=connection_factory
    def _connect(self):
        c=self._factory(str(self.path),timeout=self.busy_timeout_ms/1000);c.row_factory=sqlite3.Row;c.execute(f"PRAGMA busy_timeout={self.busy_timeout_ms}");c.execute("PRAGMA synchronous=FULL");return c
    @staticmethod
    def _init(c):
        tables={r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
        if not tables:
            c.execute("CREATE TABLE registry_metadata(schema_name TEXT PRIMARY KEY,schema_version TEXT NOT NULL)")
            c.execute("INSERT INTO registry_metadata VALUES(?,?)",(REGISTRY_SCHEMA_NAME,REGISTRY_SCHEMA_VERSION))
            c.execute(f"CREATE TABLE {TABLE}(consumption_request_id TEXT PRIMARY KEY,request_fingerprint TEXT UNIQUE NOT NULL,consumption_claim_id TEXT UNIQUE NOT NULL,claim_fingerprint TEXT UNIQUE NOT NULL,authorization_id TEXT UNIQUE NOT NULL,decision_fingerprint TEXT UNIQUE NOT NULL,request_payload_json TEXT NOT NULL,claim_payload_json TEXT NOT NULL)")
        elif tables!={TABLE,"registry_metadata"}: raise QueueAdmissionAuthorizationConsumptionSchemaError("noncanonical tables")
    @staticmethod
    def _row(request,claim): return (request.consumption_request_id,request.request_fingerprint,claim.consumption_claim_id,claim.claim_fingerprint,claim.authorization_id,claim.decision_fingerprint,request.to_json(),claim.to_json())
    def claim(self,request,claim):
        c=None;committed=False
        try:
            c=self._connect();c.execute("BEGIN IMMEDIATE");self._init(c)
            if self._injector:self._injector("before_insert")
            try:c.execute(f"INSERT INTO {TABLE} VALUES(?,?,?,?,?,?,?,?)",self._row(request,claim))
            except sqlite3.IntegrityError as e:
                row=c.execute(f"SELECT authorization_id FROM {TABLE} WHERE authorization_id=? OR decision_fingerprint=?",(claim.authorization_id,claim.decision_fingerprint)).fetchone()
                if row: raise QueueAdmissionAuthorizationAlreadyConsumedError("authorization already consumed") from e
                raise QueueAdmissionAuthorizationConsumptionConflictError("identity conflict") from e
            if self._injector:self._injector("after_insert")
            c.commit();committed=True
            row=c.execute(f"SELECT * FROM {TABLE} WHERE consumption_request_id=?",(request.consumption_request_id,)).fetchone()
            if row is None or tuple(row[n] for n in COLUMNS)!=self._row(request,claim): raise QueueAdmissionAuthorizationConsumptionIntegrityError("readback mismatch")
            return self._from_payload(row["claim_payload_json"])
        except QueueAdmissionAuthorizationConsumptionError:
            if c and not committed:c.rollback()
            raise
        except Exception as e:
            if c and not committed:c.rollback()
            raise QueueAdmissionAuthorizationConsumptionCommitError("transaction failed") from e
        finally:
            if c:c.close()
    @staticmethod
    def _from_payload(text):
        try:
            p=json.loads(text);p.pop("consumption_claim_id",None);p.pop("claim_fingerprint",None)
            return ControlledRuntimeQueueAdmissionAuthorizationConsumptionClaim(**{f.name:(tuple(p[f.name]) if f.name=="canonical_chain" else p[f.name]) for f in fields(ControlledRuntimeQueueAdmissionAuthorizationConsumptionClaim) if f.init})
        except Exception as e: raise QueueAdmissionAuthorizationConsumptionIntegrityError("malformed row") from e
    def read(self,request_id):
        c=self._connect()
        try:self._init(c);r=c.execute(f"SELECT claim_payload_json FROM {TABLE} WHERE consumption_request_id=?",(request_id,)).fetchone();return None if r is None else self._from_payload(r[0])
        finally:c.close()
    def count_claims(self):
        c=self._connect()
        try:self._init(c);return int(c.execute(f"SELECT COUNT(*) FROM {TABLE}").fetchone()[0])
        finally:c.close()
