from contextlib import contextmanager
from pathlib import Path
import json
import sqlite3
from typing import Iterator


DB_PATH = Path(__file__).resolve().parent / "data" / "investigations.db"


@contextmanager
def _connection() -> Iterator[sqlite3.Connection]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db() -> None:
    with _connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS investigations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                status TEXT NOT NULL,
                observation TEXT,
                insight TEXT,
                error TEXT,
                progress INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                agent_results TEXT NOT NULL DEFAULT '{}'
            )
            """
        )
        columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(investigations)")
        }
        if "agent_results" not in columns:
            connection.execute(
                "ALTER TABLE investigations ADD COLUMN agent_results TEXT NOT NULL DEFAULT '{}'"
            )


def create_investigation(question: str) -> int:
    with _connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO investigations (question, status, progress, created_at)
            VALUES (?, 'Queued', 0, datetime('now'))
            """,
            (question,),
        )
        if cursor.lastrowid is None:
            raise RuntimeError("SQLite did not return an investigation ID.")
        return cursor.lastrowid


def update_investigation(
    investigation_id: int,
    *,
    status: str,
    progress: int | None = None,
    observation: str | None = None,
    insight: str | None = None,
    error: str | None = None,
    agent_results: str | None = None,
) -> None:
    with _connection() as connection:
        cursor = connection.execute(
            """
            UPDATE investigations
            SET status = ?,
                progress = COALESCE(?, progress),
                observation = COALESCE(?, observation),
                insight = COALESCE(?, insight),
                error = COALESCE(?, error),
                agent_results = COALESCE(?, agent_results)
            WHERE id = ?
            """,
            (status, progress, observation, insight, error, agent_results, investigation_id),
        )
        if cursor.rowcount != 1:
            raise LookupError(f"Investigation {investigation_id} was not found.")


def get_all_investigations() -> list[dict[str, object]]:
    with _connection() as connection:
        rows = connection.execute(
            """
            SELECT id, question, status, observation, insight, error, progress, created_at,
                   agent_results
            FROM investigations
            ORDER BY id DESC
            """
        ).fetchall()
        investigations = []
        for row in rows:
            investigation = dict(row)
            investigation["agent_results"] = json.loads(investigation["agent_results"])
            investigations.append(investigation)
        return investigations
