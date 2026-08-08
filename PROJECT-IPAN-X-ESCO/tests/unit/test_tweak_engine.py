from __future__ import annotations

import sys
from typing import Any

from ipan_optimizer.core import tweak_engine


def test_debloat_summary_surfaces_real_package_count(monkeypatch):
    """Debloat Windows is one step but removes many packages; the summary
    message must show the actual count from the step stdout, not a
    step-only \"1 operasi\"."""
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(tweak_engine, "is_modded_windows", lambda: False)

    def _fake_run_step(step: Any) -> dict[str, Any]:
        return {
            "description": step.description,
            "success": True,
            "stdout": "22 aplikasi bawaan dihapus.",
            "requires_admin": False,
        }

    monkeypatch.setattr(tweak_engine, "run_step", _fake_run_step)
    result = tweak_engine.execute_tweak("adv.debloat_windows", "Debloat Windows")
    assert result.success is True
    assert result.applied == 1
    assert result.message == "Debloat Windows: 22 aplikasi bawaan dihapus."


def test_debloat_summary_falls_back_when_stdout_empty(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(tweak_engine, "is_modded_windows", lambda: False)
    monkeypatch.setattr(
        tweak_engine,
        "run_step",
        lambda step: {"description": step.description, "success": True, "requires_admin": False},
    )
    result = tweak_engine.execute_tweak("adv.debloat_windows", "Debloat Windows")
    assert result.message == "Debloat Windows: 1 operasi berhasil diterapkan."


def test_multi_step_tweak_still_counts_operations(monkeypatch):
    """Registry-based tweaks (no debloat step) keep the step-based wording."""
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(tweak_engine, "is_modded_windows", lambda: False)

    def _fake_run_step(step: Any) -> dict[str, Any]:
        return {"description": step.description, "success": True, "requires_admin": False}

    def _fake_run_elevated(_steps: Any, _tweak_id: str) -> list[dict[str, Any]]:
        return [
            {"description": s.description, "success": True, "requires_admin": True}
            for s in _steps
        ]

    monkeypatch.setattr(tweak_engine, "run_step", _fake_run_step)
    monkeypatch.setattr(tweak_engine, "run_elevated_steps", _fake_run_elevated)
    result = tweak_engine.execute_tweak("adv.boost_all_games", "Boost Semua Game")
    assert result.success is True
    assert result.applied > 1
    assert result.message.endswith(f"{result.applied} operasi berhasil diterapkan.")
