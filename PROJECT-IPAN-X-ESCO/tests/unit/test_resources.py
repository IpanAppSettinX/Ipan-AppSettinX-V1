from __future__ import annotations

import pytest

from ipan_optimizer.domain.resources import (
    calculate_resource_budget,
    ceil_to_512,
    floor_to_512,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [(0, 0), (1, 512), (511, 512), (512, 512), (513, 1024), (1536.1, 2048)],
)
def test_ceil_to_512(value: float, expected: int) -> None:
    assert ceil_to_512(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [(0, 0), (1, 0), (511, 0), (512, 512), (513, 512), (1536.9, 1536)],
)
def test_floor_to_512(value: float, expected: int) -> None:
    assert floor_to_512(value) == expected


def test_low_resource_budget_is_safe() -> None:
    budget = calculate_resource_budget(
        total_ram_mb=4096,
        available_ram_mb=2048,
        logical_processors=2,
        physical_cores=1,
        physical_cores_trustworthy=True,
    )
    assert budget.host_reserve_mb == 3072
    assert budget.safe_emulator_ram_cap_mb == 0
    assert budget.safe_emulator_cpu_cap == 0


def test_mainstream_budget_reserves_host() -> None:
    budget = calculate_resource_budget(
        total_ram_mb=16384,
        available_ram_mb=10240,
        logical_processors=12,
        physical_cores=6,
        physical_cores_trustworthy=True,
    )
    assert budget.host_reserve_mb == 5120
    assert budget.safe_emulator_ram_cap_mb == 8192
    assert budget.safe_emulator_cpu_cap == 6


def test_untrusted_physical_core_fallback() -> None:
    budget = calculate_resource_budget(
        total_ram_mb=8192,
        available_ram_mb=6000,
        logical_processors=8,
        physical_cores=None,
        physical_cores_trustworthy=False,
    )
    assert budget.physical_core_budget == 4
    assert budget.safe_emulator_cpu_cap == 4


def test_invalid_resource_values_are_rejected() -> None:
    with pytest.raises(ValueError):
        calculate_resource_budget(
            total_ram_mb=-1,
            available_ram_mb=0,
            logical_processors=1,
            physical_cores=None,
            physical_cores_trustworthy=False,
        )
