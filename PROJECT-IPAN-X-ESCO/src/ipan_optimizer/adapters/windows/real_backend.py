"""Release-gated real-write backend for HKCU typed Registry rules.

This backend is the narrow real-write adapter described in ARCHITECTURE.md.
It only supports ``registry_set`` operations whose target is an allowlisted
writable HKCU value. Everything else fails closed.

Construction is gated two ways:

- Without an injected ``store`` seam, the environment variable
  ``IPAN_ENABLE_REAL_WRITE=1`` must be present. Tests never set it, so tests
  cannot construct a host-mutating backend.
- With an injected ``store`` seam (tests), no Registry access ever happens,
  so the backend cannot touch the host either way.
"""

from __future__ import annotations

import os
import sys
from typing import Any, Protocol

from ipan_optimizer.adapters.windows.backend import WindowsReadOnlyBackend
from ipan_optimizer.adapters.windows.registry import (
    RegistryReadAdapter,
    validate_registry_operation,
)
from ipan_optimizer.domain.models import (
    MachineCapabilityVector,
    Operation,
    OperationResult,
    RegistrySetOperation,
    RegistryValueType,
    TypedSnapshot,
    VerificationResult,
)

REAL_WRITE_ENV = "IPAN_ENABLE_REAL_WRITE"


class RegistryStore(Protocol):
    """Low-level seam for Registry reads and writes."""

    def snapshot(self, operation: RegistrySetOperation) -> TypedSnapshot: ...

    def write(self, operation: RegistrySetOperation) -> None: ...

    def delete(self, operation: RegistrySetOperation) -> None: ...


class WinregStore:
    """Production seam backed by ``winreg``. Only HKCU values are writable."""

    def __init__(self) -> None:
        self._reader = RegistryReadAdapter()

    def snapshot(self, operation: RegistrySetOperation) -> TypedSnapshot:
        return self._reader.snapshot(operation)

    @staticmethod
    def _type_map() -> dict[RegistryValueType, int]:
        import winreg

        return {
            RegistryValueType.REG_DWORD: winreg.REG_DWORD,
            RegistryValueType.REG_SZ: winreg.REG_SZ,
            RegistryValueType.REG_EXPAND_SZ: winreg.REG_EXPAND_SZ,
        }

    @staticmethod
    def _reverse_type_map() -> dict[str, int]:
        import winreg

        return {
            RegistryValueType.REG_DWORD.value: winreg.REG_DWORD,
            RegistryValueType.REG_SZ.value: winreg.REG_SZ,
            RegistryValueType.REG_EXPAND_SZ.value: winreg.REG_EXPAND_SZ,
        }

    def _open_for_write(self, operation: RegistrySetOperation) -> Any:
        import winreg

        entry = validate_registry_operation(operation)
        return winreg.CreateKeyEx(
            winreg.HKEY_CURRENT_USER,
            entry.subkey,
            0,
            winreg.KEY_SET_VALUE,
        )

    def write(self, operation: RegistrySetOperation) -> None:
        if sys.platform != "win32":
            raise RuntimeError("Penulisan Registry hanya didukung pada Windows.")
        entry = validate_registry_operation(operation)
        import winreg

        with self._open_for_write(operation) as key:
            winreg.SetValueEx(
                key,
                entry.value_name,
                0,
                self._type_map()[entry.value_type],
                operation.data,
            )

    def write_raw(self, operation: RegistrySetOperation, raw_value: dict[str, Any]) -> None:
        """Restore a snapshot value using its recorded Registry type."""
        if sys.platform != "win32":
            raise RuntimeError("Penulisan Registry hanya didukung pada Windows.")
        entry = validate_registry_operation(operation)
        import winreg

        with self._open_for_write(operation) as key:
            winreg.SetValueEx(
                key,
                entry.value_name,
                0,
                self._reverse_type_map()[raw_value["type"]],
                raw_value["data"],
            )

    def delete(self, operation: RegistrySetOperation) -> None:
        if sys.platform != "win32":
            return
        entry = validate_registry_operation(operation)
        import winreg

        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                entry.subkey,
                0,
                winreg.KEY_SET_VALUE,
            ) as key:
                winreg.DeleteValue(key, entry.value_name)
        except FileNotFoundError:
            pass


def expected_value(operation: RegistrySetOperation) -> dict[str, Any]:
    return {"type": operation.value_type.value, "data": operation.data}


class RealWindowsBackend:
    """Narrow real-write backend for allowlisted HKCU typed rules."""

    def __init__(
        self,
        *,
        read_only: Any,
        store: RegistryStore | None = None,
        environ: dict[str, str] | None = None,
    ) -> None:
        if store is None:
            env = environ if environ is not None else os.environ
            if env.get(REAL_WRITE_ENV) != "1":
                raise RuntimeError(
                    "Real write mode belum dibuka. Validasi matriks Sandbox dulu, "
                    f"lalu set {REAL_WRITE_ENV}=1 secara eksplisit."
                )
            store = WinregStore()
        self._read_only: WindowsReadOnlyBackend = read_only
        self._store = store

    @property
    def dry_run(self) -> bool:
        return False

    def scan_capabilities(self) -> MachineCapabilityVector:
        return self._read_only.scan_capabilities()

    @staticmethod
    def _require_registry_set(operation: Operation) -> RegistrySetOperation:
        if operation.operation != "registry_set":
            raise ValueError("Real backend hanya mendukung operasi registry_set typed.")
        if not isinstance(operation, RegistrySetOperation):
            raise ValueError("Operasi bukan RegistrySetOperation typed.")
        entry = validate_registry_operation(operation)
        if entry.hive != "HKCU":
            raise ValueError("Real backend pada tahap ini hanya menulis hive HKCU.")
        return operation

    def snapshot(self, operation: Operation) -> TypedSnapshot:
        registry_op = self._require_registry_set(operation)
        return self._store.snapshot(registry_op)

    def apply(self, operation: Operation) -> OperationResult:
        registry_op = self._require_registry_set(operation)
        self._store.write(registry_op)
        return OperationResult(
            operation_id=operation.operation_id,
            success=True,
            dry_run=False,
            message="Perubahan diterapkan pada Registry pengguna.",
            resulting_value=expected_value(registry_op),
        )

    def verify(self, operation: Operation) -> VerificationResult:
        registry_op = self._require_registry_set(operation)
        current = self._store.snapshot(registry_op)
        expected = expected_value(registry_op)
        verified = current.existed and current.raw_value == expected
        return VerificationResult(
            operation_id=operation.operation_id,
            verified=verified,
            message="State sesuai rencana." if verified else "State tidak sesuai rencana.",
            current_value=current.raw_value,
        )

    def rollback(
        self,
        operation: Operation,
        snapshot: TypedSnapshot,
    ) -> OperationResult:
        registry_op = self._require_registry_set(operation)
        current = self._store.snapshot(registry_op)
        if not current.existed or current.raw_value != expected_value(registry_op):
            return OperationResult(
                operation_id=operation.operation_id,
                success=False,
                dry_run=False,
                message="Rollback dihentikan karena state telah berubah.",
                resulting_value=current.raw_value,
            )
        if snapshot.existed:
            if not isinstance(snapshot.raw_value, dict) or "data" not in snapshot.raw_value:
                return OperationResult(
                    operation_id=operation.operation_id,
                    success=False,
                    dry_run=False,
                    message="Snapshot tidak memiliki nilai mentah yang dapat dipulihkan.",
                    resulting_value=current.raw_value,
                )
            write_raw = getattr(self._store, "write_raw", None)
            if write_raw is None:
                raise RuntimeError("Store tidak mendukung pemulihan nilai snapshot.")
            write_raw(registry_op, snapshot.raw_value)
        else:
            self._store.delete(registry_op)
        return OperationResult(
            operation_id=operation.operation_id,
            success=True,
            dry_run=False,
            message="State awal dipulihkan.",
            resulting_value=snapshot.raw_value,
        )
