from __future__ import annotations

import math

from ipan_optimizer.domain.models import ResourceBudget


def ceil_to_512(value_mb: float) -> int:
    if value_mb <= 0:
        return 0
    return math.ceil(value_mb / 512) * 512


def floor_to_512(value_mb: float) -> int:
    if value_mb <= 0:
        return 0
    return math.floor(value_mb / 512) * 512


def calculate_resource_budget(
    *,
    total_ram_mb: int,
    available_ram_mb: int,
    logical_processors: int,
    physical_cores: int | None,
    physical_cores_trustworthy: bool,
) -> ResourceBudget:
    if total_ram_mb < 0 or available_ram_mb < 0:
        raise ValueError("Nilai memori tidak boleh negatif.")
    if logical_processors < 1:
        raise ValueError("Minimal satu logical processor diperlukan.")

    host_reserve_mb = max(3072, ceil_to_512(0.30 * total_ram_mb))
    raw_ram_cap = max(
        0,
        min(total_ram_mb - host_reserve_mb, available_ram_mb - 2048),
    )
    safe_ram_cap = floor_to_512(raw_ram_cap)
    if physical_cores_trustworthy and physical_cores and physical_cores > 0:
        physical_budget = physical_cores
    else:
        physical_budget = max(1, logical_processors // 2)
    safe_cpu_cap = max(0, min(physical_budget, logical_processors - 2))

    return ResourceBudget(
        total_ram_mb=total_ram_mb,
        available_ram_mb=available_ram_mb,
        host_reserve_mb=host_reserve_mb,
        safe_emulator_ram_cap_mb=safe_ram_cap,
        logical_processors=logical_processors,
        physical_core_budget=physical_budget,
        safe_emulator_cpu_cap=safe_cpu_cap,
    )
