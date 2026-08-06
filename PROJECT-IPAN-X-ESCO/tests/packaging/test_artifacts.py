from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.packaging
def test_main_onedir_contains_required_files() -> None:
    dist = ROOT / "dist" / "IPANOptimizer"
    assert (dist / "IPANOptimizer.exe").is_file()
    assert any(path.name == "index.html" for path in dist.rglob("index.html"))
    assert (
        sum(path.stat().st_size for path in dist.rglob("*") if path.is_file()) < 250 * 1024 * 1024
    )


@pytest.mark.packaging
def test_packaged_main_smoke(tmp_path: Path) -> None:
    executable = ROOT / "dist" / "IPANOptimizer" / "IPANOptimizer.exe"
    environment = os.environ.copy()
    environment["IPAN_OPTIMIZER_DATA_DIR"] = str(tmp_path / "app-data")
    result = subprocess.run(
        [str(executable), "--no-window"],
        cwd=ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (tmp_path / "app-data" / "ipan-optimizer.sqlite3").is_file()


@pytest.mark.packaging
def test_manifests_exist() -> None:
    main_manifest = (ROOT / "installer" / "main.manifest").read_text(encoding="utf-8")
    assert 'level="requireAdministrator"' in main_manifest
    assert "{8e0f7a12-bfb3-4fe8-b9a5-48fd50a15a9a}" in main_manifest


@pytest.mark.packaging
def test_installer_auto_installs_webview2() -> None:
    source = (ROOT / "installer" / "IPANOptimizer.iss").read_text(encoding="utf-8")
    # Installer still runs at lowest privilege (no forced elevation for the
    # installer itself); the bundled EXE handles its own UAC via manifest.
    assert "PrivilegesRequired=lowest" in source
    # WebView2 detection is performed, and the official Microsoft bootstrapper
    # is launched (non-silent) when the runtime is missing — the installer no
    # longer hard-aborts when WebView2 is absent.
    assert "WebView2Installed" in source
    assert "MicrosoftEdgeWebview2Setup.exe" in source
    assert "ExtractTemporaryFile" in source
    # No silent install: the user always sees the Microsoft installer UI.
    assert "/silent" not in source
    assert "http://" not in source
