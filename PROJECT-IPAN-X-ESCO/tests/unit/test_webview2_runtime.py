from __future__ import annotations

from pathlib import Path

import pytest

from ipan_optimizer.app.webview2_runtime import (
    WEBVIEW2_STAGING_VERSION,
    bootstrapper_path,
    ensure_webview2,
    install_webview2,
    is_webview2_installed,
)


def _reader_returning(machine_pv: str | None, user_pv: str | None):
    """Build a fake registry reader that returns fixed pv values per location."""
    calls: list[tuple[int, str, int]] = []

    def reader(hive: int, key_path: str, view: int) -> str | None:
        calls.append((hive, key_path, view))
        # The first call targets HKLM (machine), the second HKCU (user).
        if len(calls) == 1:
            return machine_pv
        return user_pv

    return reader


def test_is_installed_returns_false_on_non_windows(monkeypatch):
    monkeypatch.setattr("sys.platform", "linux")
    assert is_webview2_installed() is False


def test_is_installed_true_when_machine_pv_present():
    reader = _reader_returning("120.0.2210.91", None)
    assert is_webview2_installed(reader=reader) is True


def test_is_installed_true_when_only_user_pv_present():
    reader = _reader_returning(None, "118.0.2088.61")
    assert is_webview2_installed(reader=reader) is True


def test_is_installed_false_when_pv_missing_everywhere():
    reader = _reader_returning(None, None)
    assert is_webview2_installed(reader=reader) is False


def test_is_installed_false_when_only_staging_pv_present():
    reader = _reader_returning(WEBVIEW2_STAGING_VERSION, None)
    assert is_webview2_installed(reader=reader) is False


def test_bootstrapper_path_uses_explicit_bundle_root(tmp_path: Path):
    path = bootstrapper_path(bundle_root=tmp_path)
    assert path == tmp_path / "MicrosoftEdgeWebview2Setup.exe"


def test_install_raises_when_not_windows(monkeypatch):
    monkeypatch.setattr("sys.platform", "linux")
    with pytest.raises(RuntimeError):
        install_webview2(exe_path=Path("fake.exe"))


def test_install_raises_when_bootstrapper_missing(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("sys.platform", "win32")
    missing = tmp_path / "MicrosoftEdgeWebview2Setup.exe"
    with pytest.raises(FileNotFoundError):
        install_webview2(exe_path=missing)


def test_install_invokes_runner_with_absolute_path(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("sys.platform", "win32")
    exe = tmp_path / "MicrosoftEdgeWebview2Setup.exe"
    exe.write_bytes(b"fake-bootstrapper")

    captured: list[list[str]] = []

    def fake_runner(cmd: list[str]) -> int:
        captured.append(cmd)
        return 0

    exit_code = install_webview2(exe_path=exe, runner=fake_runner)
    assert exit_code == 0
    assert captured == [[str(exe)]]


def test_install_propagates_nonzero_exit(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("sys.platform", "win32")
    exe = tmp_path / "MicrosoftEdgeWebview2Setup.exe"
    exe.write_bytes(b"fake-bootstrapper")

    assert install_webview2(exe_path=exe, runner=lambda cmd: 1603) == 1603


def test_ensure_returns_true_when_already_installed():
    reader = _reader_returning("120.0.2210.91", None)
    assert ensure_webview2(reader=reader, headless=False) is True


def test_ensure_headless_returns_false_when_missing_without_installing():
    reader = _reader_returning(None, None)
    runner_calls: list[list[str]] = []

    def runner(cmd: list[str]) -> int:
        runner_calls.append(cmd)
        return 0

    assert ensure_webview2(reader=reader, runner=runner, headless=True) is False
    assert runner_calls == []


def test_ensure_runs_bootstrapper_then_rechecks_success(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("sys.platform", "win32")
    exe = tmp_path / "MicrosoftEdgeWebview2Setup.exe"
    exe.write_bytes(b"fake")

    call_count = {"n": 0}

    def reader(hive: int, key_path: str, view: int) -> str | None:
        call_count["n"] += 1
        # Before install: not installed. After install (3rd call onwards,
        # because is_webview2_installed iterates HKLM then HKCU per call):
        # return a real version so the recheck succeeds.
        if call_count["n"] <= 2:
            return None
        return "120.0.2210.91"

    def runner(cmd: list[str]) -> int:
        return 0

    result = ensure_webview2(
        reader=reader,
        runner=runner,
        bundle_root=tmp_path,
        headless=False,
    )
    assert result is True


def test_ensure_returns_false_when_bootstrapper_missing(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("sys.platform", "win32")
    reader = _reader_returning(None, None)
    # bundle_root points at an empty tmp dir -> bootstrapper_path is missing.
    result = ensure_webview2(
        reader=reader,
        bundle_root=tmp_path,
        headless=False,
    )
    assert result is False


def test_ensure_returns_false_when_bootstrapper_exits_nonzero(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("sys.platform", "win32")
    exe = tmp_path / "MicrosoftEdgeWebview2Setup.exe"
    exe.write_bytes(b"fake")
    reader = _reader_returning(None, None)

    def runner(cmd: list[str]) -> int:
        return 1603

    result = ensure_webview2(
        reader=reader,
        runner=runner,
        bundle_root=tmp_path,
        headless=False,
    )
    assert result is False


def test_ensure_returns_false_when_recheck_still_missing(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("sys.platform", "win32")
    exe = tmp_path / "MicrosoftEdgeWebview2Setup.exe"
    exe.write_bytes(b"fake")
    reader = _reader_returning(None, None)

    def runner(cmd: list[str]) -> int:
        return 0

    result = ensure_webview2(
        reader=reader,
        runner=runner,
        bundle_root=tmp_path,
        headless=False,
    )
    assert result is False
