import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

import database
from agents.pipeline import run_agents


class AgentPipelineTests(unittest.TestCase):
    def test_runs_all_six_pillars_with_explicit_evidence_limits(self) -> None:
        results = run_agents("How should we build a reliable memory system?")

        self.assertEqual(
            list(results),
            ["Observer", "Strategist", "Wisdom", "Builder", "Compression", "Agency"],
        )
        self.assertEqual(results["Strategist"]["focus"], "decision")
        self.assertIn("evidence", results["Wisdom"]["evidence_limit"])
        self.assertEqual(results["Agency"]["approval_required"], "yes")
        self.assertIn("memory system", results["Builder"]["next_step"])

    def test_compression_limits_summary_length(self) -> None:
        results = run_agents("Investigate " + "persistent signals " * 30)

        self.assertLessEqual(len(results["Compression"]["summary"]), 160)


class InvestigationDatabaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_db_path = database.DB_PATH
        database.DB_PATH = Path(self.temp_dir.name) / "investigations.db"

    def tearDown(self) -> None:
        database.DB_PATH = self.original_db_path
        self.temp_dir.cleanup()

    def test_migrates_existing_database_and_persists_agent_results(self) -> None:
        with sqlite3.connect(database.DB_PATH) as connection:
            connection.execute(
                """
                CREATE TABLE investigations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question TEXT NOT NULL,
                    status TEXT NOT NULL,
                    observation TEXT,
                    insight TEXT,
                    error TEXT,
                    progress INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                INSERT INTO investigations (question, status, created_at)
                VALUES ('Legacy question', 'Complete', datetime('now'))
                """
            )

        database.init_db()
        investigation_id = database.create_investigation("What changed?")
        results = run_agents("What changed?")
        database.update_investigation(
            investigation_id,
            status="Complete",
            progress=100,
            agent_results=json.dumps(results),
        )

        investigation = database.get_all_investigations()[0]
        self.assertEqual(investigation["agent_results"], results)
        self.assertEqual(investigation["status"], "Complete")
        legacy_investigation = database.get_all_investigations()[1]
        self.assertEqual(legacy_investigation["question"], "Legacy question")
        self.assertEqual(legacy_investigation["agent_results"], {})


if __name__ == "__main__":
    unittest.main()
