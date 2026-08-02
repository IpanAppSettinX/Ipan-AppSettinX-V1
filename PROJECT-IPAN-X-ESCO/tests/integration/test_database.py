from __future__ import annotations

from pathlib import Path

from ipan_optimizer.persistence.database import Database


def test_migrations_create_required_tables(tmp_path: Path) -> None:
    database = Database(tmp_path / "app.sqlite3")
    database.migrate()
    with database.connect() as connection:
        tables = {
            row["name"]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
    required = {
        "schema_migrations",
        "capability_scans",
        "transactions",
        "snapshots",
        "game_sessions",
        "benchmark_sessions",
        "application_settings",
    }
    assert required <= tables


def test_migrations_are_idempotent(tmp_path: Path) -> None:
    database = Database(tmp_path / "app.sqlite3")
    database.migrate()
    database.migrate()
    with database.connect() as connection:
        count = connection.execute("SELECT COUNT(*) AS count FROM schema_migrations").fetchone()[
            "count"
        ]
    assert count == 1
