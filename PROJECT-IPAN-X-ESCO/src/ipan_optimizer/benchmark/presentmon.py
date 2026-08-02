from __future__ import annotations

import csv
from pathlib import Path

from ipan_optimizer.benchmark.analysis import BenchmarkRun

_FRAME_COLUMNS = ("MsBetweenPresents", "msBetweenPresents", "FrameTime")


def import_presentmon_csv(path: Path, *, max_rows: int = 5_000_000) -> BenchmarkRun:
    if path.suffix.casefold() != ".csv":
        raise ValueError("Hanya file CSV yang dapat diimpor.")
    if not path.is_file():
        raise FileNotFoundError(path)
    values: list[float] = []
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        column = next(
            (candidate for candidate in _FRAME_COLUMNS if candidate in (reader.fieldnames or [])),
            None,
        )
        if column is None:
            raise ValueError("Kolom frame time PresentMon tidak ditemukan.")
        for index, row in enumerate(reader):
            if index >= max_rows:
                raise ValueError("CSV melebihi batas jumlah baris.")
            try:
                value = float(row[column])
            except (TypeError, ValueError):
                continue
            if value > 0:
                values.append(value)
    if not values:
        raise ValueError("CSV tidak memiliki frame time valid.")
    return BenchmarkRun(run_id=path.stem, frame_times_ms=tuple(values))
