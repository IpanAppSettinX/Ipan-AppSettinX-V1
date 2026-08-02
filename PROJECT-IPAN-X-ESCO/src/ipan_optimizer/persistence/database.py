from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

MIGRATIONS: tuple[tuple[int, str], ...] = (
    (
        1,
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS machines (
            machine_id TEXT PRIMARY KEY, label TEXT NOT NULL, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS capability_scans (
            scan_id TEXT PRIMARY KEY, captured_at TEXT NOT NULL, payload_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS capabilities (
            scan_id TEXT NOT NULL, capability_key TEXT NOT NULL, state TEXT NOT NULL,
            value_json TEXT, reason TEXT NOT NULL,
            PRIMARY KEY (scan_id, capability_key)
        );
        CREATE TABLE IF NOT EXISTS games (
            game_id TEXT PRIMARY KEY, title TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS game_executables (
            executable_id TEXT PRIMARY KEY, game_id TEXT, path TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS emulator_products (
            product_id TEXT PRIMARY KEY, name TEXT NOT NULL, version TEXT
        );
        CREATE TABLE IF NOT EXISTS emulator_instances (
            instance_id TEXT PRIMARY KEY, product_id TEXT NOT NULL, payload_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS profiles (
            profile_id TEXT PRIMARY KEY, name TEXT NOT NULL, payload_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS profile_rules (
            profile_id TEXT NOT NULL, rule_id TEXT NOT NULL,
            PRIMARY KEY (profile_id, rule_id)
        );
        CREATE TABLE IF NOT EXISTS tweak_rules (
            rule_id TEXT PRIMARY KEY, revision INTEGER NOT NULL, payload_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id TEXT PRIMARY KEY, state TEXT NOT NULL, payload_json TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS transaction_operations (
            transaction_id TEXT NOT NULL, operation_id TEXT NOT NULL, payload_json TEXT NOT NULL,
            PRIMARY KEY (transaction_id, operation_id)
        );
        CREATE TABLE IF NOT EXISTS snapshots (
            transaction_id TEXT NOT NULL, operation_id TEXT NOT NULL, payload_json TEXT NOT NULL,
            PRIMARY KEY (transaction_id, operation_id)
        );
        CREATE TABLE IF NOT EXISTS game_sessions (
            session_id TEXT PRIMARY KEY, state TEXT NOT NULL, payload_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS benchmark_sessions (
            benchmark_id TEXT PRIMARY KEY, state TEXT NOT NULL, payload_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS benchmark_runs (
            run_id TEXT PRIMARY KEY, benchmark_id TEXT NOT NULL, payload_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS benchmark_metrics (
            run_id TEXT NOT NULL, metric TEXT NOT NULL, value REAL,
            PRIMARY KEY (run_id, metric)
        );
        CREATE TABLE IF NOT EXISTS recommendations (
            recommendation_id TEXT PRIMARY KEY, scan_id TEXT NOT NULL, payload_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS evidence_sources (
            evidence_id TEXT PRIMARY KEY, url TEXT NOT NULL, payload_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS activity_events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL,
            category TEXT NOT NULL, message TEXT NOT NULL, payload_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS application_settings (
            setting_key TEXT PRIMARY KEY, value_json TEXT NOT NULL
        );
        """,
    ),
)


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = FULL")
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def migrate(self) -> None:
        with self.connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS schema_migrations "
                "(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)"
            )
            applied = {
                int(row["version"])
                for row in connection.execute("SELECT version FROM schema_migrations")
            }
            for version, sql in MIGRATIONS:
                if version in applied:
                    continue
                connection.executescript(sql)
                connection.execute(
                    "INSERT INTO schema_migrations(version, applied_at) "
                    "VALUES (?, datetime('now'))",
                    (version,),
                )
