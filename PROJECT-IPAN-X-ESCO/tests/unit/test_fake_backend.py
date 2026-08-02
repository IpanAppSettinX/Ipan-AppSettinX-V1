from __future__ import annotations

from ipan_optimizer.adapters.fake import FakeWindowsBackend, operation_target_key
from ipan_optimizer.core.rules import resolve_operations


def test_absent_value_round_trip() -> None:
    backend = FakeWindowsBackend()
    operation = resolve_operations(["windows.game_mode"])[0]
    snapshot = backend.snapshot(operation)
    assert snapshot.existed is False
    assert backend.apply(operation).success
    assert backend.verify(operation).verified
    assert backend.rollback(operation, snapshot).success
    assert operation_target_key(operation) not in backend.state_copy()


def test_existing_value_round_trip_preserves_type() -> None:
    operation = resolve_operations(["windows.game_mode"])[0]
    target = operation_target_key(operation)
    backend = FakeWindowsBackend(state={target: {"type": "REG_DWORD", "data": 0}})
    snapshot = backend.snapshot(operation)
    backend.apply(operation)
    backend.rollback(operation, snapshot)
    assert backend.state_copy()[target] == {"type": "REG_DWORD", "data": 0}


def test_rollback_conflict_does_not_overwrite_actor_change() -> None:
    operation = resolve_operations(["windows.game_mode"])[0]
    backend = FakeWindowsBackend()
    snapshot = backend.snapshot(operation)
    backend.apply(operation)
    target = operation_target_key(operation)
    backend._state[target] = {"type": "REG_DWORD", "data": 0}
    result = backend.rollback(operation, snapshot)
    assert result.success is False
    assert backend.state_copy()[target]["data"] == 0
