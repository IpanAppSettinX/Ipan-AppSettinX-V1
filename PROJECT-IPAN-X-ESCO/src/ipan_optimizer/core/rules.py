from __future__ import annotations

from dataclasses import dataclass

from ipan_optimizer.domain.models import (
    Operation,
    RegistrySetOperation,
    RegistryValueType,
    RegistryView,
    RiskLevel,
)


@dataclass(frozen=True)
class RuleDefinition:
    rule_id: str
    title: str
    description: str
    risk: RiskLevel
    operations: tuple[Operation, ...]
    evidence_url: str


RULES: dict[str, RuleDefinition] = {
    "windows.game_mode": RuleDefinition(
        rule_id="windows.game_mode",
        title="Mode Game Windows",
        description="Simulasikan pengaktifan Mode Game untuk pengguna saat ini.",
        risk=RiskLevel.SAFE,
        operations=(
            RegistrySetOperation(
                operation_id="windows.game_mode.set",
                allowlist_id="windows.game_mode.current_user",
                hive="HKCU",
                subkey=r"Software\Microsoft\GameBar",
                value_name="AutoGameModeEnabled",
                registry_view=RegistryView.NATIVE,
                value_type=RegistryValueType.REG_DWORD,
                data=1,
            ),
        ),
        evidence_url="https://support.xbox.com/en-US/help/games-apps/game-setup-and-play/use-game-mode-gaming-on-pc",
    ),
    "mouse.linear_pointer": RuleDefinition(
        rule_id="mouse.linear_pointer",
        title="Pointer Linear Windows",
        description=("Nonaktifkan akselerasi pointer klasik dengan sensitivitas Windows standar."),
        risk=RiskLevel.CONDITIONAL,
        operations=(
            RegistrySetOperation(
                operation_id="mouse.linear_pointer.sensitivity",
                allowlist_id="mouse.sensitivity.current_user",
                hive="HKCU",
                subkey=r"Control Panel\Mouse",
                value_name="MouseSensitivity",
                registry_view=RegistryView.NATIVE,
                value_type=RegistryValueType.REG_SZ,
                data="10",
            ),
            RegistrySetOperation(
                operation_id="mouse.linear_pointer.speed",
                allowlist_id="mouse.speed.current_user",
                hive="HKCU",
                subkey=r"Control Panel\Mouse",
                value_name="MouseSpeed",
                registry_view=RegistryView.NATIVE,
                value_type=RegistryValueType.REG_SZ,
                data="0",
            ),
            RegistrySetOperation(
                operation_id="mouse.linear_pointer.threshold1",
                allowlist_id="mouse.threshold1.current_user",
                hive="HKCU",
                subkey=r"Control Panel\Mouse",
                value_name="MouseThreshold1",
                registry_view=RegistryView.NATIVE,
                value_type=RegistryValueType.REG_SZ,
                data="0",
            ),
            RegistrySetOperation(
                operation_id="mouse.linear_pointer.threshold2",
                allowlist_id="mouse.threshold2.current_user",
                hive="HKCU",
                subkey=r"Control Panel\Mouse",
                value_name="MouseThreshold2",
                registry_view=RegistryView.NATIVE,
                value_type=RegistryValueType.REG_SZ,
                data="0",
            ),
        ),
        evidence_url=(
            "https://learn.microsoft.com/en-us/windows/win32/api/winuser/"
            "nf-winuser-systemparametersinfoa"
        ),
    ),
    "gaming.background_capture_off": RuleDefinition(
        rule_id="gaming.background_capture_off",
        title="Background Capture Off",
        description="Nonaktifkan perekaman latar belakang untuk pengguna saat ini.",
        risk=RiskLevel.CONDITIONAL,
        operations=(
            RegistrySetOperation(
                operation_id="gaming.background_capture.app_capture",
                allowlist_id="gaming.app_capture.current_user",
                hive="HKCU",
                subkey=r"Software\Microsoft\Windows\CurrentVersion\GameDVR",
                value_name="AppCaptureEnabled",
                registry_view=RegistryView.NATIVE,
                value_type=RegistryValueType.REG_DWORD,
                data=0,
            ),
            RegistrySetOperation(
                operation_id="gaming.background_capture.game_dvr",
                allowlist_id="gaming.game_dvr.current_user",
                hive="HKCU",
                subkey=r"System\GameConfigStore",
                value_name="GameDVR_Enabled",
                registry_view=RegistryView.NATIVE,
                value_type=RegistryValueType.REG_DWORD,
                data=0,
            ),
        ),
        evidence_url=(
            "https://learn.microsoft.com/en-us/windows/client-management/mdm/"
            "policy-csp-applicationmanagement"
        ),
    ),
    "fix.game_dvr_restore": RuleDefinition(
        rule_id="fix.game_dvr_restore",
        title="Fix Obs Studio dan fitur Screen Shoot",
        description=(
            "Aktifkan kembali Game DVR dan perilaku FSE untuk pengguna saat ini "
            "agar OBS Studio dan screenshot berfungsi lagi."
        ),
        risk=RiskLevel.CONDITIONAL,
        operations=(
            RegistrySetOperation(
                operation_id="fix.game_dvr_restore.enabled",
                allowlist_id="gaming.game_dvr.current_user",
                hive="HKCU",
                subkey=r"System\GameConfigStore",
                value_name="GameDVR_Enabled",
                registry_view=RegistryView.NATIVE,
                value_type=RegistryValueType.REG_DWORD,
                data=1,
            ),
            RegistrySetOperation(
                operation_id="fix.game_dvr_restore.fse_behavior",
                allowlist_id="gaming.game_dvr_fse_behavior.current_user",
                hive="HKCU",
                subkey=r"System\GameConfigStore",
                value_name="GameDVR_FSEBehavior",
                registry_view=RegistryView.NATIVE,
                value_type=RegistryValueType.REG_DWORD,
                data=0,
            ),
            RegistrySetOperation(
                operation_id="fix.game_dvr_restore.honor_fse",
                allowlist_id="gaming.game_dvr_honor_fse.current_user",
                hive="HKCU",
                subkey=r"System\GameConfigStore",
                value_name="GameDVR_HonorUserFSEBehaviorMode",
                registry_view=RegistryView.NATIVE,
                value_type=RegistryValueType.REG_DWORD,
                data=1,
            ),
            RegistrySetOperation(
                operation_id="fix.game_dvr_restore.dxgi_honor",
                allowlist_id="gaming.game_dvr_dxgi_honor.current_user",
                hive="HKCU",
                subkey=r"System\GameConfigStore",
                value_name="GameDVR_DXGIHonorFSEWindowsCompatible",
                registry_view=RegistryView.NATIVE,
                value_type=RegistryValueType.REG_DWORD,
                data=1,
            ),
        ),
        evidence_url=(
            "https://learn.microsoft.com/en-us/windows/client-management/mdm/"
            "policy-csp-applicationmanagement"
        ),
    ),
    "fix.webcam_consent": RuleDefinition(
        rule_id="fix.webcam_consent",
        title="Fix Camera all windows",
        description=(
            "Kembalikan izin privasi webcam untuk pengguna saat ini agar kamera "
            "terdeteksi kembali setelah tweaking."
        ),
        risk=RiskLevel.CONDITIONAL,
        operations=(
            RegistrySetOperation(
                operation_id="fix.webcam_consent.allow",
                allowlist_id="privacy.webcam_consent.current_user",
                hive="HKCU",
                subkey=(
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion"
                    r"\CapabilityAccessManager\ConsentStore\webcam"
                ),
                value_name="Value",
                registry_view=RegistryView.NATIVE,
                value_type=RegistryValueType.REG_SZ,
                data="Allow",
            ),
        ),
        evidence_url=("https://support.microsoft.com/en-us/windows/camera-and-privacy-settings"),
    ),
    "analysis.apply_regedit": RuleDefinition(
        rule_id="analysis.apply_regedit",
        title="Apply Regedit",
        description="Optimasi registry untuk jaringan (Dry Run).",
        risk=RiskLevel.CONDITIONAL,
        operations=(),
        evidence_url="",
    ),
    "analysis.clean_temp_files": RuleDefinition(
        rule_id="analysis.clean_temp_files",
        title="Clean Temp Files",
        description="Menghapus file temporary (Dry Run).",
        risk=RiskLevel.SAFE,
        operations=(),
        evidence_url="",
    ),
    "analysis.apply_booster": RuleDefinition(
        rule_id="analysis.apply_booster",
        title="Apply Booster",
        description="Power plan dan prefetch (Dry Run).",
        risk=RiskLevel.CONDITIONAL,
        operations=(),
        evidence_url="",
    ),
    "analysis.revert_all_changes": RuleDefinition(
        rule_id="analysis.revert_all_changes",
        title="Revert All Changes",
        description="Mengembalikan registry (Dry Run).",
        risk=RiskLevel.SAFE,
        operations=(),
        evidence_url="",
    ),
    "analysis.clean_log_files": RuleDefinition(
        rule_id="analysis.clean_log_files",
        title="Clean Log Files",
        description="Menghapus event logs (Dry Run).",
        risk=RiskLevel.SAFE,
        operations=(),
        evidence_url="",
    ),
}


PROFILES: list[dict[str, object]] = []


def resolve_operations(rule_ids: list[str]) -> list[Operation]:
    operations: list[Operation] = []
    for rule_id in rule_ids:
        definition = RULES.get(rule_id)
        if definition is None:
            raise ValueError(f"Rule tidak dikenal: {rule_id}")
        operations.extend(operation.model_copy(deep=True) for operation in definition.operations)
    return operations
