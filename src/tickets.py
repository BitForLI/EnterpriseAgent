"""持久化人工客服工单。"""

from __future__ import annotations

import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path

from src.config import settings


class TicketStore:
    def __init__(self, path: Path | str | None = None):
        self.path = Path(path or settings.ticket_db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS tickets (
                    id TEXT PRIMARY KEY,
                    summary TEXT NOT NULL,
                    user_id INTEGER,
                    priority TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def create(self, summary: str, user_id: int | None, priority: str) -> dict[str, object]:
        ticket = {
            "id": f"CS-{uuid.uuid4().hex[:8].upper()}",
            "summary": summary,
            "user_id": user_id,
            "priority": priority,
            "status": "open",
            "created_at": datetime.now(UTC).isoformat(),
        }
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO tickets VALUES (:id, :summary, :user_id, :priority, :status, :created_at)",
                ticket,
            )
        return ticket

    def get(self, ticket_id: str) -> dict[str, object] | None:
        with self._connect() as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                "SELECT * FROM tickets WHERE id = ?", (ticket_id,)
            ).fetchone()
        return dict(row) if row else None
