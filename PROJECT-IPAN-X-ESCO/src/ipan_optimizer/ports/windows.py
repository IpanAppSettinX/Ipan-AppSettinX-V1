from __future__ import annotations

from typing import Protocol

from ipan_optimizer.domain.models import (
    MachineCapabilityVector,
    Operation,
    OperationResult,
    TypedSnapshot,
    VerificationResult,
)


class WindowsBackend(Protocol):
    @property
    def dry_run(self) -> bool: ...

    def scan_capabilities(self) -> MachineCapabilityVector: ...

    def snapshot(self, operation: Operation) -> TypedSnapshot: ...

    def apply(self, operation: Operation) -> OperationResult: ...

    def verify(self, operation: Operation) -> VerificationResult: ...

    def rollback(
        self,
        operation: Operation,
        snapshot: TypedSnapshot,
    ) -> OperationResult: ...
