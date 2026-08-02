from __future__ import annotations

import statistics
from dataclasses import dataclass


@dataclass(frozen=True)
class BenchmarkRun:
    run_id: str
    frame_times_ms: tuple[float, ...]
    valid: bool = True

    def median_frame_time(self) -> float:
        if not self.frame_times_ms:
            raise ValueError("Run tidak memiliki frame sample.")
        return float(statistics.median(self.frame_times_ms))


@dataclass(frozen=True)
class BenchmarkComparison:
    state: str
    message: str
    baseline_median_ms: float | None
    candidate_median_ms: float | None
    relative_change: float | None


def compare_run_groups(
    baseline: list[BenchmarkRun],
    candidate: list[BenchmarkRun],
    *,
    noise_threshold: float = 0.03,
) -> BenchmarkComparison:
    baseline_values = [run.median_frame_time() for run in baseline if run.valid]
    candidate_values = [run.median_frame_time() for run in candidate if run.valid]
    if len(baseline_values) < 3 or len(candidate_values) < 3:
        return BenchmarkComparison(
            state="INVALID",
            message="Minimal tiga run valid diperlukan untuk setiap kelompok.",
            baseline_median_ms=None,
            candidate_median_ms=None,
            relative_change=None,
        )
    baseline_median = float(statistics.median(baseline_values))
    candidate_median = float(statistics.median(candidate_values))
    if baseline_median <= 0:
        return BenchmarkComparison(
            state="INVALID",
            message="Baseline frame time tidak valid.",
            baseline_median_ms=baseline_median,
            candidate_median_ms=candidate_median,
            relative_change=None,
        )
    relative = (candidate_median - baseline_median) / baseline_median
    if abs(relative) <= noise_threshold:
        state = "INCONCLUSIVE"
        message = "Tidak ada perubahan bermakna."
    elif relative < 0:
        state = "IMPROVED"
        message = "Frame time membaik di luar ambang noise yang dikonfigurasi."
    else:
        state = "REGRESSED"
        message = "Frame time memburuk di luar ambang noise yang dikonfigurasi."
    return BenchmarkComparison(
        state=state,
        message=message,
        baseline_median_ms=baseline_median,
        candidate_median_ms=candidate_median,
        relative_change=relative,
    )
