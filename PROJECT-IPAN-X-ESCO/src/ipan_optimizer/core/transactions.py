from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from threading import Lock

from ipan_optimizer.core.journal import RecoveryJournal
from ipan_optimizer.core.policy import validate_operation, validate_rule_id
from ipan_optimizer.core.rules import RULES, resolve_operations
from ipan_optimizer.domain.models import (
    Transaction,
    TransactionState,
)
from ipan_optimizer.ports.windows import WindowsBackend


class TransactionManager:
    def __init__(self, backend: WindowsBackend, journal: RecoveryJournal) -> None:
        self.backend = backend
        self.journal = journal
        self._transactions: dict[str, Transaction] = {}
        self._lock = Lock()

    def preview(self, rule_ids: list[str]) -> Transaction:
        for rule_id in rule_ids:
            validate_rule_id(rule_id)
            definition = RULES.get(rule_id)
            if definition is None:
                raise ValueError(f"Rule tidak dikenal: {rule_id}")
            for operation in definition.operations:
                validate_operation(operation, risk=definition.risk)
        operations = resolve_operations(rule_ids)
        if not operations:
            raise ValueError("Transaksi tidak memiliki operasi typed yang dapat diverifikasi.")
        transaction = Transaction(
            rule_ids=rule_ids,
            operations=operations,
            dry_run=self.backend.dry_run,
        )
        with self._lock:
            self._transactions[transaction.transaction_id] = transaction
        self.journal.append(
            transaction.transaction_id,
            "planned",
            transaction.model_dump(mode="json"),
        )
        return transaction.model_copy(deep=True)

    def get(self, transaction_id: str) -> Transaction:
        transaction = self._transactions.get(transaction_id)
        if transaction is None:
            raise KeyError("Transaksi tidak ditemukan.")
        return transaction.model_copy(deep=True)

    def apply(
        self,
        transaction_id: str,
        progress: Callable[[int, str], None] | None = None,
    ) -> Transaction:
        report = progress or (lambda value, message: None)
        report(8, "Memeriksa identitas dan status transaksi.")
        with self._lock:
            transaction = self._transactions.get(transaction_id)
            if transaction is None:
                raise KeyError("Transaksi tidak ditemukan.")
            if transaction.state is not TransactionState.PLANNED:
                return transaction.model_copy(deep=True)
            transaction.snapshots = [
                self.backend.snapshot(operation) for operation in transaction.operations
            ]
            transaction.state = TransactionState.SNAPSHOTTED
            transaction.updated_at = datetime.now(UTC)
        report(35, "Snapshot kondisi awal tersimpan.")
        self.journal.append(
            transaction_id,
            "snapshotted",
            {"snapshots": [item.model_dump(mode="json") for item in transaction.snapshots]},
        )
        try:
            transaction.state = TransactionState.APPLYING
            self.journal.append(transaction_id, "applying", {})
            report(48, "Menerapkan operasi typed pada backend aman.")
            operation_count = len(transaction.operations)
            for index, operation in enumerate(transaction.operations, start=1):
                result = self.backend.apply(operation)
                transaction.results.append(result)
                if not result.success:
                    raise RuntimeError(result.message)
                report(
                    48 + int((index / operation_count) * 30),
                    f"Operasi {index} dari {operation_count} selesai diterapkan.",
                )
            transaction.state = TransactionState.APPLIED
            self.journal.append(
                transaction_id,
                "applied",
                {"results": [item.model_dump(mode="json") for item in transaction.results]},
            )
            report(82, "Memverifikasi state hasil terhadap rencana transaksi.")
            verifications = []
            for index, operation in enumerate(transaction.operations, start=1):
                verifications.append(self.backend.verify(operation))
                report(
                    82 + int((index / operation_count) * 16),
                    f"Target {index} dari {operation_count} selesai diverifikasi.",
                )
            if not all(item.verified for item in verifications):
                raise RuntimeError("Verifikasi transaksi gagal.")
            transaction.state = TransactionState.VERIFIED
            transaction.updated_at = datetime.now(UTC)
            self.journal.append(
                transaction_id,
                "verified",
                {"verifications": [item.model_dump(mode="json") for item in verifications]},
            )
            report(99, "Semua target cocok dengan state yang diharapkan.")
        except Exception as exc:
            transaction.error = str(exc)
            self._rollback_internal(transaction)
            report(99, "Verifikasi gagal; kondisi awal telah dipulihkan.")
        return transaction.model_copy(deep=True)

    def keep(self, transaction_id: str) -> Transaction:
        transaction = self._transactions.get(transaction_id)
        if transaction is None:
            raise KeyError("Transaksi tidak ditemukan.")
        if transaction.state is not TransactionState.VERIFIED:
            raise ValueError("Hanya transaksi terverifikasi yang dapat disimpan.")
        transaction.state = TransactionState.KEPT
        transaction.updated_at = datetime.now(UTC)
        self.journal.append(transaction_id, "kept", {})
        return transaction.model_copy(deep=True)

    def rollback(self, transaction_id: str) -> Transaction:
        transaction = self._transactions.get(transaction_id)
        if transaction is None:
            raise KeyError("Transaksi tidak ditemukan.")
        if transaction.state is TransactionState.ROLLED_BACK:
            return transaction.model_copy(deep=True)
        self._rollback_internal(transaction)
        return transaction.model_copy(deep=True)

    def _rollback_internal(self, transaction: Transaction) -> None:
        transaction.state = TransactionState.ROLLING_BACK
        self.journal.append(transaction.transaction_id, "rolling_back", {})
        conflicts: list[str] = []
        pairs = list(zip(transaction.operations, transaction.snapshots, strict=False))
        for operation, snapshot in reversed(pairs):
            result = self.backend.rollback(operation, snapshot)
            if not result.success:
                conflicts.append(result.message)
        transaction.updated_at = datetime.now(UTC)
        if conflicts:
            transaction.state = TransactionState.RECOVERY_REQUIRED
            transaction.error = "; ".join(conflicts)
            self.journal.append(
                transaction.transaction_id,
                "recovery_required",
                {"conflicts": conflicts},
            )
        else:
            transaction.state = TransactionState.ROLLED_BACK
            self.journal.append(transaction.transaction_id, "rolled_back", {})

    def list_recovery_items(self) -> list[Transaction]:
        return [
            transaction.model_copy(deep=True)
            for transaction in self._transactions.values()
            if transaction.state
            in {
                TransactionState.RECOVERY_REQUIRED,
                TransactionState.APPLYING,
                TransactionState.APPLIED,
            }
        ]
