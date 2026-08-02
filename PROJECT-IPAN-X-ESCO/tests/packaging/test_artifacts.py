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
def test_helper_and_manifests_exist() -> None:
    assert (ROOT / "dist" / "IPANOptimizerHelper.exe").is_file()
    main_manifest = (ROOT / "installer" / "main.manifest").read_text(encoding="utf-8")
    helper_manifest = (ROOT / "installer" / "helper.manifest").read_text(encoding="utf-8")
    assert 'level="asInvoker"' in main_manifest
    assert 'level="requireAdministrator"' in helper_manifest


@pytest.mark.packaging
def test_installer_source_has_safe_prerequisite_policy() -> None:
    source = (ROOT / "installer" / "IPANOptimizer.iss").read_text(encoding="utf-8")
    assert "PrivilegesRequired=lowest" in source
    assert "WebView2Installed" in source
    assert "tidak mengunduh komponen secara diam-diam" in source
    assert "http://" not in source
