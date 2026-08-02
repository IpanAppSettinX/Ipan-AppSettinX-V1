from __future__ import annotations

from pathlib import Path

import pytest

from ipan_optimizer.benchmark.analysis import BenchmarkRun, compare_run_groups
from ipan_optimizer.benchmark.presentmon import import_presentmon_csv


def runs(prefix: str, values: list[float]) -> list[BenchmarkRun]:
    return [
        BenchmarkRun(run_id=f"{prefix}-{index}", frame_times_ms=(value,) * 100)
        for index, value in enumerate(values)
    ]


def test_comparison_detects_improvement() -> None:
    result = compare_run_groups(runs("a", [16.5, 16.6, 16.7]), runs("b", [14.0, 14.1, 14.2]))
    assert result.state == "IMPROVED"


def test_comparison_detects_regression() -> None:
    result = compare_run_groups(runs("a", [16.5, 16.6, 16.7]), runs("b", [20.0, 20.1, 20.2]))
    assert result.state == "REGRESSED"


def test_comparison_uses_honest_noise_wording() -> None:
    result = compare_run_groups(runs("a", [16.5, 16.6, 16.7]), runs("b", [16.4, 16.6, 16.8]))
    assert result.state == "INCONCLUSIVE"
    assert result.message == "Tidak ada perubahan bermakna."


def test_comparison_requires_three_valid_runs() -> None:
    result = compare_run_groups(runs("a", [16.5, 16.6]), runs("b", [15.0, 15.1]))
    assert result.state == "INVALID"


def test_import_presentmon_csv(tmp_path: Path) -> None:
    path = tmp_path / "run.csv"
    path.write_text(
        "Application,MsBetweenPresents\nGame.exe,16.7\nGame.exe,17.1\n",
        encoding="utf-8",
    )
    run = import_presentmon_csv(path)
    assert run.frame_times_ms == (16.7, 17.1)


def test_import_rejects_missing_frame_column(tmp_path: Path) -> None:
    path = tmp_path / "run.csv"
    path.write_text("Application,FPS\nGame.exe,60\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Kolom frame time"):
        import_presentmon_csv(path)
