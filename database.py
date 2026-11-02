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
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS memory_nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                normalized_name TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS investigation_memory (
                investigation_id INTEGER NOT NULL,
                node_id INTEGER NOT NULL,
                PRIMARY KEY (investigation_id, node_id),
                FOREIGN KEY (investigation_id) REFERENCES investigations(id),
                FOREIGN KEY (node_id) REFERENCES memory_nodes(id)
            )
            """
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


def save_investigation_concepts(investigation_id: int, concepts: list[str]) -> None:
    with _connection() as connection:
        exists = connection.execute(
            "SELECT 1 FROM investigations WHERE id = ?", (investigation_id,)
        ).fetchone()
        if exists is None:
            raise LookupError(f"Investigation {investigation_id} was not found.")
        for concept in concepts:
            normalized_name = concept.casefold()
            connection.execute(
                """
                INSERT INTO memory_nodes (normalized_name, name)
                VALUES (?, ?)
                ON CONFLICT(normalized_name) DO NOTHING
                """,
                (normalized_name, concept),
            )
            node = connection.execute(
                "SELECT id FROM memory_nodes WHERE normalized_name = ?",
                (normalized_name,),
            ).fetchone()
            if node is None:
                raise RuntimeError(f"Memory node {concept!r} could not be retrieved.")
            connection.execute(
                """
                INSERT OR IGNORE INTO investigation_memory (investigation_id, node_id)
                VALUES (?, ?)
                """,
                (investigation_id, node["id"]),
            )


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
            investigation["concepts"] = []
            investigation["related_investigations"] = []
            investigations.append(investigation)
        memory_rows = connection.execute(
            """
            SELECT current.investigation_id, node.name,
                   previous.id AS related_id, previous.question AS related_question
            FROM investigation_memory AS current
            JOIN memory_nodes AS node ON node.id = current.node_id
            LEFT JOIN investigation_memory AS match
                ON match.node_id = current.node_id
                AND match.investigation_id < current.investigation_id
            LEFT JOIN investigations AS previous
                ON previous.id = match.investigation_id
                AND previous.status = 'Complete'
            ORDER BY current.investigation_id, node.normalized_name, previous.id
            """
        ).fetchall()
        by_id = {investigation["id"]: investigation for investigation in investigations}
        for row in memory_rows:
            current = by_id.get(row["investigation_id"])
            if current is None:
                continue
            if row["name"] not in current["concepts"]:
                current["concepts"].append(row["name"])
            related_id = row["related_id"]
            if related_id is None:
                continue
            related = next(
                (
                    item
                    for item in current["related_investigations"]
                    if item["id"] == related_id
                ),
                None,
            )
            if related is None:
                related = {
                    "id": related_id,
                    "question": row["related_question"],
                    "shared_concepts": [],
                }
                current["related_investigations"].append(related)
            if row["name"] not in related["shared_concepts"]:
                related["shared_concepts"].append(row["name"])
        return investigations
