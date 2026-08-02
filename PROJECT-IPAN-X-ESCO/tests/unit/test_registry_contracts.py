from __future__ import annotations

import pytest
from pydantic import ValidationError

from ipan_optimizer.adapters.windows.registry import validate_registry_operation
from ipan_optimizer.core.rules import RULES
from ipan_optimizer.domain.models import (
    RegistrySetOperation,
    RegistryValueType,
    RegistryView,
)


def game_mode_operation(**overrides: object) -> RegistrySetOperation:
    values: dict[str, object] = {
        "operation_id": "op-1",
        "allowlist_id": "windows.game_mode.current_user",
        "hive": "HKCU",
        "subkey": r"Software\Microsoft\GameBar",
        "value_name": "AutoGameModeEnabled",
        "registry_view": RegistryView.NATIVE,
        "value_type": RegistryValueType.REG_DWORD,
        "data": 1,
    }
    values.update(overrides)
    return RegistrySetOperation.model_validate(values)


def test_game_mode_allowlist_accepts_exact_target() -> None:
    entry = validate_registry_operation(game_mode_operation())
    assert entry.allowlist_id == "windows.game_mode.current_user"


@pytest.mark.parametrize("data", [-1, 2, 100])
def test_game_mode_rejects_out_of_range(data: int) -> None:
    with pytest.raises(ValueError):
        validate_registry_operation(game_mode_operation(data=data))


def test_allowlist_id_cannot_alias_other_path() -> None:
    with pytest.raises(ValueError):
        validate_registry_operation(game_mode_operation(subkey=r"Software\Other"))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("subkey", "Software\x00Bad"),
        ("subkey", r"\\remote\HKLM"),
        ("subkey", r"Software\WOW6432Node\Bad"),
        ("value_name", "Bad*"),
    ],
)
def test_registry_text_rejects_injection(field: str, value: str) -> None:
    with pytest.raises(ValidationError):
        game_mode_operation(**{field: value})


def test_audit_only_hags_rejects_write() -> None:
    operation = RegistrySetOperation(
        operation_id="op-hags",
        allowlist_id="windows.hags.audit",
        hive="HKLM",
        subkey=r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers",
        value_name="HwSchMode",
        registry_view=RegistryView.NATIVE,
        value_type=RegistryValueType.REG_DWORD,
        data=2,
        requires_admin=True,
    )
    with pytest.raises(ValueError, match="hanya boleh diaudit"):
        validate_registry_operation(operation)


def test_every_registry_rule_uses_an_exact_writable_allowlist() -> None:
    for definition in RULES.values():
        for operation in definition.operations:
            if operation.operation == "registry_set":
                entry = validate_registry_operation(operation)
                assert entry.writable is True
