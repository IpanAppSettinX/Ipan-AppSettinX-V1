from __future__ import annotations

from typing import Any, Protocol

from ipan_optimizer.adapters.fake import FakeWindowsBackend, operation_target_key
from ipan_optimizer.domain.models import MachineCapabilityVector, Operation, TypedSnapshot


class ReadOnlySource(Protocol):
    def scan_capabilities(self) -> MachineCapabilityVector: ...

    def snapshot(self, operation: Operation) -> TypedSnapshot: ...


class DryRunWindowsBackend(FakeWindowsBackend):
    """Copy-on-write backend that cannot mutate the Windows host."""

    def __init__(
        self,
        *,
        capabilities: MachineCapabilityVector,
        initial_state: dict[str, Any] | None = None,
        source: ReadOnlySource | None = None,
    ) -> None:
        self._source = source
        self._loaded_targets: set[str] = set()
        super().__init__(
            capabilities=capabilities,
            state=initial_state,
            dry_run=True,
        )

    def snapshot(self, operation: Operation) -> TypedSnapshot:
        target = operation_target_key(operation)
        if self._source is not None and target not in self._loaded_targets:
            source_snapshot = self._source.snapshot(operation)
            if source_snapshot.existed:
                self._state[target] = source_snapshot.raw_value
            self._loaded_targets.add(target)
            return source_snapshot
        return super().snapshot(operation)
