from __future__ import annotations

from ipan_optimizer.adapters.windows.capabilities import WindowsCapabilityScanner
from ipan_optimizer.adapters.windows.power import PowerReadAdapter
from ipan_optimizer.adapters.windows.registry import RegistryReadAdapter
from ipan_optimizer.adapters.windows.services import ServiceReadAdapter
from ipan_optimizer.domain.models import (
    MachineCapabilityVector,
    Operation,
    OperationResult,
    TypedSnapshot,
    VerificationResult,
)


class WindowsReadOnlyBackend:
    @property
    def dry_run(self) -> bool:
        return True

    def scan_capabilities(self) -> MachineCapabilityVector:
        return WindowsCapabilityScanner().scan()

    def snapshot(self, operation: Operation) -> TypedSnapshot:
        if operation.operation == "registry_set":
            return RegistryReadAdapter().snapshot(operation)
        if operation.operation == "service_start":
            return ServiceReadAdapter().snapshot(operation)
        return PowerReadAdapter().snapshot(operation)

    def apply(self, operation: Operation) -> OperationResult:
        raise RuntimeError("Backend Windows ini read-only; gunakan Dry Run overlay.")

    def verify(self, operation: Operation) -> VerificationResult:
        raise RuntimeError("Backend Windows ini read-only; gunakan Dry Run overlay.")

    def rollback(
        self,
        operation: Operation,
        snapshot: TypedSnapshot,
    ) -> OperationResult:
        raise RuntimeError("Backend Windows ini read-only; gunakan Dry Run overlay.")
