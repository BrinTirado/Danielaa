from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from mochi.memory.models import Memory


class MemoryStore:
    """SQLite-backed explicit memory store for Mochi v0.1."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self.initialize()

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as connection:
            self._ensure_schema(connection)

    def add_memory(
        self,
        person_id: str | None = None,
        content: str | None = None,
        importance: int = 1,
        *,
        kind: str | None = None,
    ) -> Memory:
        if kind is not None:
            person_id = kind
        if content is None:
            raise ValueError("content is required")
        if not content.strip():
            raise ValueError("content cannot be empty")

        memory = Memory(
            id=str(uuid4()),
            person_id=person_id,
            content=content,
            importance=importance,
            created_at=datetime.now(UTC),
        )

        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO memories (id, person_id, content, importance, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    memory.id,
                    memory.person_id,
                    memory.content,
                    memory.importance,
                    memory.created_at.isoformat(),
                ),
            )

        return memory

    def list_memories(self) -> list[Memory]:
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT id, person_id, content, importance, created_at
                FROM memories
                ORDER BY created_at ASC, id ASC
                """
            ).fetchall()

        return [self._row_to_memory(row) for row in rows]

    def search_memories(
        self,
        person_id: str | None = None,
        text: str | None = None,
    ) -> list[Memory]:
        clauses: list[str] = []
        parameters: list[str] = []

        if person_id is not None:
            clauses.append("person_id = ?")
            parameters.append(person_id)

        if text is not None:
            clauses.append("LOWER(content) LIKE ? ESCAPE '\\'")
            parameters.append(f"%{self._escape_like(text.lower())}%")

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._connection() as connection:
            rows = connection.execute(
                f"""
                SELECT id, person_id, content, importance, created_at
                FROM memories
                {where}
                ORDER BY created_at ASC, id ASC
                """,
                parameters,
            ).fetchall()

        return [self._row_to_memory(row) for row in rows]

    def delete_memory(self, memory_id: str) -> bool:
        with self._connection() as connection:
            cursor = connection.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            return cursor.rowcount > 0

    def delete_memories_for_person(self, person_id: str) -> int:
        with self._connection() as connection:
            cursor = connection.execute("DELETE FROM memories WHERE person_id = ?", (person_id,))
            return cursor.rowcount

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            yield connection
        except Exception:
            connection.rollback()
            raise
        else:
            connection.commit()
        finally:
            connection.close()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _escape_like(self, text: str) -> str:
        return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

    def _ensure_schema(self, connection: sqlite3.Connection) -> None:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                person_id TEXT,
                content TEXT NOT NULL,
                importance INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(memories)").fetchall()
        }
        if {"id", "person_id", "content", "importance", "created_at"}.issubset(columns):
            return

        connection.execute("ALTER TABLE memories RENAME TO memories_legacy")
        connection.execute(
            """
            CREATE TABLE memories (
                id TEXT PRIMARY KEY,
                person_id TEXT,
                content TEXT NOT NULL,
                importance INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        rows = connection.execute(
            "SELECT id, kind, content, created_at FROM memories_legacy ORDER BY id ASC"
        ).fetchall()
        for row in rows:
            connection.execute(
                """
                INSERT INTO memories (id, person_id, content, importance, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    str(row["id"]),
                    row["kind"],
                    row["content"],
                    1,
                    self._normalize_created_at(row["created_at"]),
                ),
            )
        connection.execute("DROP TABLE memories_legacy")

    def _row_to_memory(self, row: sqlite3.Row) -> Memory:
        return Memory(
            id=row["id"],
            person_id=row["person_id"],
            content=row["content"],
            importance=row["importance"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def _normalize_created_at(self, value: str) -> str:
        try:
            return datetime.fromisoformat(value).isoformat()
        except ValueError:
            return datetime.now(UTC).isoformat()
