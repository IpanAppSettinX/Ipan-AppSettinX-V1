from __future__ import annotations

import sys
import tempfile
import time
from pathlib import Path

import pytest

from ipan_optimizer.main import cleanup_orphan_meipass


@pytest.fixture(autouse=True)
def _windows_platform(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "platform", "win32")


def _make_stale_meipass(root: Path, name: str, age_hours: float) -> Path:
    folder = root / name
    folder.mkdir()
    (folder / "dummy.txt").write_text("x", encoding="utf-8")
    old = time.time() - age_hours * 3600
    for path in [folder, folder / "dummy.txt"]:
        import os

        os.utime(path, (old, old))
    return folder


def test_cleanup_removes_old_orphan(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
    stale = _make_stale_meipass(tmp_path, "_MEI11111", age_hours=48)
    removed = cleanup_orphan_meipass(max_age_hours=1)
    assert removed == 1
    assert not stale.exists()


def test_cleanup_keeps_fresh_folder(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
    fresh = _make_stale_meipass(tmp_path, "_MEI22222", age_hours=0.1)
    removed = cleanup_orphan_meipass(max_age_hours=24)
    assert removed == 0
    assert fresh.is_dir()


def test_cleanup_never_deletes_own_bundle(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
    own = _make_stale_meipass(tmp_path, "_MEI33333", age_hours=72)
    monkeypatch.setattr(sys, "_MEIPASS", str(own), raising=False)
    removed = cleanup_orphan_meipass(max_age_hours=1)
    assert removed == 0
    assert own.is_dir()


def test_cleanup_ignores_non_meipass(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
    other = _make_stale_meipass(tmp_path, "not-a-meipass", age_hours=72)
    removed = cleanup_orphan_meipass(max_age_hours=1)
    assert removed == 0
    assert other.is_dir()


def test_cleanup_noop_on_non_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    assert cleanup_orphan_meipass() == 0
