from __future__ import annotations

import pytest

from ipan_optimizer.adapters.windows.backend import WindowsReadOnlyBackend
from ipan_optimizer.core.rules import resolve_operations


def test_windows_backend_rejects_direct_apply() -> None:
    backend = WindowsReadOnlyBackend()
    operation = resolve_operations(["windows.game_mode"])[0]
    with pytest.raises(RuntimeError, match="read-only"):
        backend.apply(operation)


def test_windows_backend_rejects_direct_rollback() -> None:
    backend = WindowsReadOnlyBackend()
    operation = resolve_operations(["windows.game_mode"])[0]
    snapshot = backend.snapshot(operation)
    with pytest.raises(RuntimeError, match="read-only"):
        backend.rollback(operation, snapshot)
