from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any

from ipan_optimizer.domain.models import (
    RegistrySetOperation,
    RegistryValueType,
    RegistryView,
    TypedSnapshot,
)


@dataclass(frozen=True)
class RegistryCatalogEntry:
    allowlist_id: str
    hive: str
    subkey: str
    value_name: str
    value_type: RegistryValueType
    writable: bool
    allowed_values: frozenset[Any] | None = None


REGISTRY_CATALOG: dict[str, RegistryCatalogEntry] = {
    "windows.game_mode.current_user": RegistryCatalogEntry(
        allowlist_id="windows.game_mode.current_user",
        hive="HKCU",
        subkey=r"Software\Microsoft\GameBar",
        value_name="AutoGameModeEnabled",
        value_type=RegistryValueType.REG_DWORD,
        writable=True,
        allowed_values=frozenset({0, 1}),
    ),
    "windows.hags.audit": RegistryCatalogEntry(
        allowlist_id="windows.hags.audit",
        hive="HKLM",
        subkey=r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers",
        value_name="HwSchMode",
        value_type=RegistryValueType.REG_DWORD,
        writable=False,
        allowed_values=frozenset({1, 2}),
    ),
    "mouse.sensitivity.current_user": RegistryCatalogEntry(
        allowlist_id="mouse.sensitivity.current_user",
        hive="HKCU",
        subkey=r"Control Panel\Mouse",
        value_name="MouseSensitivity",
        value_type=RegistryValueType.REG_SZ,
        writable=True,
        allowed_values=frozenset({"10"}),
    ),
    "mouse.speed.current_user": RegistryCatalogEntry(
        allowlist_id="mouse.speed.current_user",
        hive="HKCU",
        subkey=r"Control Panel\Mouse",
        value_name="MouseSpeed",
        value_type=RegistryValueType.REG_SZ,
        writable=True,
        allowed_values=frozenset({"0"}),
    ),
    "mouse.threshold1.current_user": RegistryCatalogEntry(
        allowlist_id="mouse.threshold1.current_user",
        hive="HKCU",
        subkey=r"Control Panel\Mouse",
        value_name="MouseThreshold1",
        value_type=RegistryValueType.REG_SZ,
        writable=True,
        allowed_values=frozenset({"0"}),
    ),
    "mouse.threshold2.current_user": RegistryCatalogEntry(
        allowlist_id="mouse.threshold2.current_user",
        hive="HKCU",
        subkey=r"Control Panel\Mouse",
        value_name="MouseThreshold2",
        value_type=RegistryValueType.REG_SZ,
        writable=True,
        allowed_values=frozenset({"0"}),
    ),
    "gaming.app_capture.current_user": RegistryCatalogEntry(
        allowlist_id="gaming.app_capture.current_user",
        hive="HKCU",
        subkey=r"Software\Microsoft\Windows\CurrentVersion\GameDVR",
        value_name="AppCaptureEnabled",
        value_type=RegistryValueType.REG_DWORD,
        writable=True,
        allowed_values=frozenset({0, 1}),
    ),
    "gaming.game_dvr.current_user": RegistryCatalogEntry(
        allowlist_id="gaming.game_dvr.current_user",
        hive="HKCU",
        subkey=r"System\GameConfigStore",
        value_name="GameDVR_Enabled",
        value_type=RegistryValueType.REG_DWORD,
        writable=True,
        allowed_values=frozenset({0, 1}),
    ),
    "gaming.game_dvr_fse_behavior.current_user": RegistryCatalogEntry(
        allowlist_id="gaming.game_dvr_fse_behavior.current_user",
        hive="HKCU",
        subkey=r"System\GameConfigStore",
        value_name="GameDVR_FSEBehavior",
        value_type=RegistryValueType.REG_DWORD,
        writable=True,
        allowed_values=frozenset({0, 1, 2}),
    ),
    "gaming.game_dvr_honor_fse.current_user": RegistryCatalogEntry(
        allowlist_id="gaming.game_dvr_honor_fse.current_user",
        hive="HKCU",
        subkey=r"System\GameConfigStore",
        value_name="GameDVR_HonorUserFSEBehaviorMode",
        value_type=RegistryValueType.REG_DWORD,
        writable=True,
        allowed_values=frozenset({0, 1}),
    ),
    "gaming.game_dvr_dxgi_honor.current_user": RegistryCatalogEntry(
        allowlist_id="gaming.game_dvr_dxgi_honor.current_user",
        hive="HKCU",
        subkey=r"System\GameConfigStore",
        value_name="GameDVR_DXGIHonorFSEWindowsCompatible",
        value_type=RegistryValueType.REG_DWORD,
        writable=True,
        allowed_values=frozenset({0, 1}),
    ),
    "privacy.webcam_consent.current_user": RegistryCatalogEntry(
        allowlist_id="privacy.webcam_consent.current_user",
        hive="HKCU",
        subkey=(
            r"SOFTWARE\Microsoft\Windows\CurrentVersion"
            r"\CapabilityAccessManager\ConsentStore\webcam"
        ),
        value_name="Value",
        value_type=RegistryValueType.REG_SZ,
        writable=True,
        allowed_values=frozenset({"Allow", "Deny"}),
    ),
}


def validate_registry_operation(operation: RegistrySetOperation) -> RegistryCatalogEntry:
    entry = REGISTRY_CATALOG.get(operation.allowlist_id)
    if entry is None:
        raise ValueError("Target Registry tidak berada dalam katalog allowlist.")
    actual = (
        operation.hive.casefold(),
        operation.subkey.casefold(),
        operation.value_name.casefold(),
        operation.value_type,
    )
    expected = (
        entry.hive.casefold(),
        entry.subkey.casefold(),
        entry.value_name.casefold(),
        entry.value_type,
    )
    if actual != expected:
        raise ValueError("Target Registry tidak cocok dengan allowlist ID.")
    if not entry.writable:
        raise ValueError("Target Registry hanya boleh diaudit.")
    if entry.allowed_values is not None and operation.data not in entry.allowed_values:
        raise ValueError("Nilai Registry berada di luar batas katalog.")
    return entry


class RegistryReadAdapter:
    def snapshot(self, operation: RegistrySetOperation) -> TypedSnapshot:
        entry = validate_registry_operation(operation)
        if sys.platform != "win32":
            return TypedSnapshot(
                operation_id=operation.operation_id,
                provider="registry",
                target_key=operation.allowlist_id,
                existed=False,
            )
        import winreg

        hives = {"HKCU": winreg.HKEY_CURRENT_USER, "HKLM": winreg.HKEY_LOCAL_MACHINE}
        views = {
            RegistryView.NATIVE: 0,
            RegistryView.VIEW_32: winreg.KEY_WOW64_32KEY,
            RegistryView.VIEW_64: winreg.KEY_WOW64_64KEY,
        }
        target = (
            f"registry:{operation.hive}:{operation.registry_view}:"
            f"{operation.subkey}:{operation.value_name}"
        ).casefold()
        try:
            with winreg.OpenKey(
                hives[entry.hive],
                entry.subkey,
                0,
                winreg.KEY_QUERY_VALUE | views[operation.registry_view],
            ) as key:
                value, native_type = winreg.QueryValueEx(key, entry.value_name)
        except FileNotFoundError:
            return TypedSnapshot(
                operation_id=operation.operation_id,
                provider="registry",
                target_key=target,
                existed=False,
            )
        type_names = {
            winreg.REG_DWORD: RegistryValueType.REG_DWORD.value,
            winreg.REG_QWORD: RegistryValueType.REG_QWORD.value,
            winreg.REG_SZ: RegistryValueType.REG_SZ.value,
            winreg.REG_EXPAND_SZ: RegistryValueType.REG_EXPAND_SZ.value,
            winreg.REG_MULTI_SZ: RegistryValueType.REG_MULTI_SZ.value,
            winreg.REG_BINARY: RegistryValueType.REG_BINARY.value,
        }
        value_type = type_names.get(native_type, f"UNSUPPORTED_{native_type}")
        return TypedSnapshot(
            operation_id=operation.operation_id,
            provider="registry",
            target_key=target,
            existed=True,
            value_type=value_type,
            raw_value={"type": value_type, "data": value},
        )
