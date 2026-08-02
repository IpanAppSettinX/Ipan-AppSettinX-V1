from __future__ import annotations

from pathlib import Path

import pytest

from ipan_optimizer.adapters.fake import FakeWindowsBackend, operation_target_key
from ipan_optimizer.core.journal import RecoveryJournal
from ipan_optimizer.core.transactions import TransactionManager
from ipan_optimizer.domain.models import TransactionState


def manager(tmp_path: Path, backend: FakeWindowsBackend) -> TransactionManager:
    return TransactionManager(backend, RecoveryJournal(tmp_path / "journal.jsonl"))


def test_preview_apply_verify_keep(tmp_path: Path) -> None:
    backend = FakeWindowsBackend()
    transactions = manager(tmp_path, backend)
    preview = transactions.preview(["windows.game_mode"])
    assert preview.state is TransactionState.PLANNED
    applied = transactions.apply(preview.transaction_id)
    assert applied.state is TransactionState.VERIFIED
    kept = transactions.keep(preview.transaction_id)
    assert kept.state is TransactionState.KEPT


@pytest.mark.parametrize(
    ("rule_id", "operation_count"),
    [
        ("mouse.linear_pointer", 4),
        ("gaming.background_capture_off", 2),
    ],
)
def test_restored_gaming_rules_are_typed_and_verified(
    tmp_path: Path,
    rule_id: str,
    operation_count: int,
) -> None:
    transactions = manager(tmp_path, FakeWindowsBackend())
    preview = transactions.preview([rule_id])
    assert len(preview.operations) == operation_count
    applied = transactions.apply(preview.transaction_id)
    assert applied.state is TransactionState.VERIFIED
    assert len(applied.snapshots) == operation_count


def test_preview_rejects_rule_without_typed_operations(tmp_path: Path) -> None:
    transactions = manager(tmp_path, FakeWindowsBackend())
    with pytest.raises(ValueError, match="tidak memiliki operasi typed"):
        transactions.preview(["analysis.apply_regedit"])


def test_apply_reports_monotonic_real_transaction_stages(tmp_path: Path) -> None:
    transactions = manager(tmp_path, FakeWindowsBackend())
    preview = transactions.preview(["windows.game_mode"])
    updates: list[tuple[int, str]] = []
    applied = transactions.apply(
        preview.transaction_id,
        lambda progress, message: updates.append((progress, message)),
    )
    assert applied.state is TransactionState.VERIFIED
    assert [progress for progress, _ in updates] == sorted(progress for progress, _ in updates)
    assert updates[0][0] == 8
    assert updates[-1][0] == 99
    assert any("Snapshot" in message for _, message in updates)
    assert any("diverifikasi" in message for _, message in updates)


def test_apply_is_idempotent_for_double_submit(tmp_path: Path) -> None:
    backend = FakeWindowsBackend()
    transactions = manager(tmp_path, backend)
    preview = transactions.preview(["windows.game_mode"])
    first = transactions.apply(preview.transaction_id)
    second = transactions.apply(preview.transaction_id)
    assert first.state is TransactionState.VERIFIED
    assert second.state is TransactionState.VERIFIED
    assert len([entry for entry in backend.operation_ledger if entry["action"] == "apply"]) == 1


def test_rollback_is_idempotent(tmp_path: Path) -> None:
    backend = FakeWindowsBackend()
    transactions = manager(tmp_path, backend)
    preview = transactions.preview(["windows.game_mode"])
    transactions.apply(preview.transaction_id)
    first = transactions.rollback(preview.transaction_id)
    second = transactions.rollback(preview.transaction_id)
    assert first.state is TransactionState.ROLLED_BACK
    assert second.state is TransactionState.ROLLED_BACK


def test_rollback_conflict_requires_recovery(tmp_path: Path) -> None:
    backend = FakeWindowsBackend()
    transactions = manager(tmp_path, backend)
    preview = transactions.preview(["windows.game_mode"])
    transactions.apply(preview.transaction_id)
    operation = preview.operations[0]
    target = operation_target_key(operation)
    backend._state[target] = {"type": "REG_DWORD", "data": 0}
    rolled = transactions.rollback(preview.transaction_id)
    assert rolled.state is TransactionState.RECOVERY_REQUIRED
    assert transactions.list_recovery_items()
