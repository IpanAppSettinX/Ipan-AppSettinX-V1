from __future__ import annotations

from copy import deepcopy
from typing import Any

from ipan_optimizer.domain.models import (
    Capability,
    CapabilityState,
    EvidenceRef,
    MachineCapabilityVector,
    Operation,
    OperationResult,
    TypedSnapshot,
    VerificationResult,
)


def operation_target_key(operation: Operation) -> str:
    if operation.operation == "registry_set":
        return (
            f"registry:{operation.hive}:{operation.registry_view}:"
            f"{operation.subkey}:{operation.value_name}"
        ).casefold()
    if operation.operation == "service_start":
        return f"service:{operation.service_name}".casefold()
    return f"power:{operation.scheme_guid}".casefold()


def operation_value(operation: Operation) -> Any:
    if operation.operation == "registry_set":
        return {"type": operation.value_type.value, "data": deepcopy(operation.data)}
    if operation.operation == "service_start":
        return "running"
    return operation.scheme_guid


class FakeWindowsBackend:
    def __init__(
        self,
        *,
        capabilities: MachineCapabilityVector | None = None,
        state: dict[str, Any] | None = None,
        dry_run: bool = True,
    ) -> None:
        self._dry_run = dry_run
        self._capabilities = capabilities or self._default_capabilities()
        self._state = deepcopy(state or {})
        self.operation_ledger: list[dict[str, Any]] = []

    @property
    def dry_run(self) -> bool:
        return self._dry_run

    @staticmethod
    def _default_capabilities() -> MachineCapabilityVector:
        evidence = [EvidenceRef(source="fixture", detail="Deterministic fake backend")]
        items = {
            "os.platform": Capability(
                key="os.platform",
                state=CapabilityState.AVAILABLE,
                value="Windows 11",
                reason="Fixture Windows 11 24H2.",
                evidence=evidence,
            ),
            "os.architecture": Capability(
                key="os.architecture",
                state=CapabilityState.AVAILABLE,
                value="AMD64",
                reason="Fixture x64.",
                evidence=evidence,
            ),
            "cpu.logical_processors": Capability(
                key="cpu.logical_processors",
                state=CapabilityState.AVAILABLE,
                value=8,
                reason="Fixture mempunyai delapan logical processor.",
                evidence=evidence,
            ),
            "cpu.physical_cores": Capability(
                key="cpu.physical_cores",
                state=CapabilityState.AVAILABLE,
                value=4,
                reason="Fixture mempunyai empat physical core.",
                evidence=evidence,
            ),
            "memory.total_mb": Capability(
                key="memory.total_mb",
                state=CapabilityState.AVAILABLE,
                value=16384,
                reason="Fixture memori.",
                evidence=evidence,
            ),
            "memory.available_mb": Capability(
                key="memory.available_mb",
                state=CapabilityState.AVAILABLE,
                value=10240,
                reason="Fixture memori tersedia.",
                evidence=evidence,
            ),
            "webview2.runtime": Capability(
                key="webview2.runtime",
                state=CapabilityState.AVAILABLE,
                value="fixture",
                reason="Runtime tersedia pada fixture.",
                evidence=evidence,
            ),
        }
        return MachineCapabilityVector(capabilities=items)

    def scan_capabilities(self) -> MachineCapabilityVector:
        return self._capabilities.model_copy(deep=True)

    def snapshot(self, operation: Operation) -> TypedSnapshot:
        target = operation_target_key(operation)
        exists = target in self._state
        value = deepcopy(self._state.get(target))
        return TypedSnapshot(
            operation_id=operation.operation_id,
            provider=operation.operation,
            target_key=target,
            existed=exists,
            value_type=value.get("type") if isinstance(value, dict) else type(value).__name__,
            raw_value=value,
        )

    def apply(self, operation: Operation) -> OperationResult:
        target = operation_target_key(operation)
        value = operation_value(operation)
        self._state[target] = deepcopy(value)
        self.operation_ledger.append(
            {"action": "apply", "target": target, "value": deepcopy(value)}
        )
        return OperationResult(
            operation_id=operation.operation_id,
            success=True,
            dry_run=self.dry_run,
            message="Perubahan disimulasikan." if self.dry_run else "Perubahan diterapkan.",
            resulting_value=value,
        )

    def verify(self, operation: Operation) -> VerificationResult:
        target = operation_target_key(operation)
        expected = operation_value(operation)
        current = self._state.get(target)
        verified = current == expected
        return VerificationResult(
            operation_id=operation.operation_id,
            verified=verified,
            message="State sesuai rencana." if verified else "State tidak sesuai rencana.",
            current_value=deepcopy(current),
        )

    def rollback(
        self,
        operation: Operation,
        snapshot: TypedSnapshot,
    ) -> OperationResult:
        target = operation_target_key(operation)
        expected = operation_value(operation)
        if self._state.get(target) != expected:
            return OperationResult(
                operation_id=operation.operation_id,
                success=False,
                dry_run=self.dry_run,
                message="Rollback dihentikan karena state telah berubah.",
                resulting_value=deepcopy(self._state.get(target)),
            )
        if snapshot.existed:
            self._state[target] = deepcopy(snapshot.raw_value)
        else:
            self._state.pop(target, None)
        self.operation_ledger.append(
            {"action": "rollback", "target": target, "value": deepcopy(snapshot.raw_value)}
        )
        return OperationResult(
            operation_id=operation.operation_id,
            success=True,
            dry_run=self.dry_run,
            message="State awal dipulihkan.",
            resulting_value=deepcopy(snapshot.raw_value),
        )

    def state_copy(self) -> dict[str, Any]:
        return deepcopy(self._state)
