"""Foundation-07.4 SQLite persistence store."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..persistence_contract import IntelligencePersistenceContract
from .serializer import IntelligenceSnapshotSerializer


class SQLiteIntelligenceStore(IntelligencePersistenceContract):
    """SQLite implementation of the intelligence persistence contract."""

    version = "foundation-07.4"

    def __init__(self, db_path: str = "ntpe_intelligence.sqlite3", serializer: Optional[IntelligenceSnapshotSerializer] = None) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True) if self.db_path.parent != Path(".") else None
        self.serializer = serializer or IntelligenceSnapshotSerializer()
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.db_path))

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS intelligence_snapshots (
                    scope_key TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()

    def save_snapshot(self, scope_key: str, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        data = self.serializer.normalize(snapshot)
        payload = self.serializer.dumps(data)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO intelligence_snapshots(scope_key, payload, updated_at)
                VALUES(?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(scope_key) DO UPDATE SET
                    payload=excluded.payload,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (scope_key, payload),
            )
            conn.commit()
        return self.load_snapshot(scope_key) or data

    def load_snapshot(self, scope_key: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload FROM intelligence_snapshots WHERE scope_key = ?",
                (scope_key,),
            ).fetchone()
        if row is None:
            return None
        return self.serializer.loads(row[0])

    def list_scope_keys(self) -> List[str]:
        with self._connect() as conn:
            rows = conn.execute("SELECT scope_key FROM intelligence_snapshots ORDER BY scope_key").fetchall()
        return [row[0] for row in rows]

    def delete_snapshot(self, scope_key: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM intelligence_snapshots WHERE scope_key = ?", (scope_key,))
            conn.commit()
            return cursor.rowcount > 0
