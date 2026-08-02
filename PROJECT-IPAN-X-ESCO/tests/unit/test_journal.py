from __future__ import annotations

from pathlib import Path

from ipan_optimizer.core.journal import RecoveryJournal


def test_journal_hash_chain_validates(tmp_path: Path) -> None:
    path = tmp_path / "journal.jsonl"
    journal = RecoveryJournal(path)
    journal.append("tx-1", "planned", {"value": 1})
    journal.append("tx-1", "verified", {"value": 2})
    assert journal.validate()


def test_journal_tamper_is_detected(tmp_path: Path) -> None:
    path = tmp_path / "journal.jsonl"
    journal = RecoveryJournal(path)
    journal.append("tx-1", "planned", {"value": 1})
    path.write_text(
        path.read_text(encoding="utf-8").replace('"value":1', '"value":9'),
        encoding="utf-8",
    )
    assert not journal.validate()
