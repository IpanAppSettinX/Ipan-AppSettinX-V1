from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_every_control_has_test_mapping() -> None:
    payload = json.loads((ROOT / "docs" / "control_matrix.source.json").read_text(encoding="utf-8"))
    controls = payload["controls"]
    assert len(controls) == 62
    assert all(item["test_ids"] for item in controls)
    assert len({item["control_id"] for item in controls}) == len(controls)


def test_control_matrix_is_current() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/check_control_matrix.py"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_frontend_policy_gate() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/check_frontend_policy.py"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_frontend_asset_budget() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/check_asset_budget.py"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
