from __future__ import annotations

from pathlib import Path

import pytest

from ipan_optimizer.adapters.emulators.config_store import AtomicConfigStore


def test_atomic_config_round_trip(tmp_path: Path) -> None:
    root = tmp_path / "product"
    root.mkdir()
    path = root / "engine.conf"
    path.write_bytes(b"old")
    store = AtomicConfigStore(root)
    snapshot = store.snapshot(path)
    new_hash = store.atomic_write(path, b"new", expected_hash=snapshot.sha256)
    assert path.read_bytes() == b"new"
    assert new_hash != snapshot.sha256


def test_atomic_write_detects_toctou(tmp_path: Path) -> None:
    root = tmp_path / "product"
    root.mkdir()
    path = root / "engine.conf"
    path.write_bytes(b"old")
    store = AtomicConfigStore(root)
    snapshot = store.snapshot(path)
    path.write_bytes(b"actor-change")
    with pytest.raises(RuntimeError, match="berubah setelah preview"):
        store.atomic_write(path, b"new", expected_hash=snapshot.sha256)
    assert path.read_bytes() == b"actor-change"


def test_config_store_rejects_path_escape(tmp_path: Path) -> None:
    root = tmp_path / "product"
    root.mkdir()
    store = AtomicConfigStore(root)
    with pytest.raises(ValueError, match="di luar root"):
        store.snapshot(tmp_path / "outside.conf")
