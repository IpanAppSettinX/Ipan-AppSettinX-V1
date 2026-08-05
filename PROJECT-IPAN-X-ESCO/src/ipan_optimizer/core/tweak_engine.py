"""Real tweak execution engine.

Maps each tweak_id from the Tweak Menu and Advanced Tweak Menu to actual
Windows operations: Registry writes (reg add/delete), service configuration
(sc config), power plan changes (powercfg), and file cleanup.

Each tweak produces a list of commands that are executed sequentially. A
snapshot of the prior Registry state is recorded for rollback. Service and
powercfg changes are best-effort and may require admin elevation.
"""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Any

_CMD_INTERNAL_COMMANDS = frozenset(
    {
        "del",
        "rd",
        "rmdir",
        "start",
        "copy",
        "move",
        "md",
        "mkdir",
        "ren",
        "rename",
        "type",
        "echo",
        "set",
        "call",
        "for",
        "if",
        "pushd",
        "popd",
        "attrib",
        "cacls",
        "format",
        "label",
        "vol",
        "chdir",
        "cd",
        "cls",
        "color",
        "date",
        "time",
        "title",
        "ver",
        "verify",
    }
)


def _resolve_command(command: list[str]) -> list[str]:
    """Expand env vars and resolve CMD internal commands.

    ``subprocess.run(shell=False)`` cannot expand ``%TEMP%`` or run CMD
    builtins like ``del``/``rd``. This helper:
    1. Expands ``%VAR%`` patterns in every argument via ``os.path.expandvars``.
    2. Detects CMD internal commands (``del``, ``rd``, ``start``, ...) and
       wraps them as ``["cmd", "/c", *expanded]``.
    3. Leaves real executables (``reg.exe``, ``sc.exe``, ``bcdedit.exe``)
       unchanged; Windows ``CreateProcess`` resolves them via ``PATH`` even
       without the ``.exe`` suffix.
    """
    if not command:
        return command
    expanded = [os.path.expandvars(arg) for arg in command]
    if expanded[0].lower() in _CMD_INTERNAL_COMMANDS:
        return ["cmd", "/c", *expanded]
    return expanded


_PREFETCH = (
    r"SYSTEM\CurrentControlSet\Control\Session Manager"
    r"\Memory Management\PrefetchParameters"
)


@dataclass
class TweakStep:
    description: str
    command: list[str]
    requires_admin: bool = False


@dataclass
class TweakResult:
    tweak_id: str
    title: str
    success: bool
    applied: int = 0
    failed: int = 0
    steps: list[dict[str, Any]] = field(default_factory=list)
    message: str = ""


def _reg_add(
    subkey: str,
    value_name: str,
    value_type: str,
    data: str,
    *,
    hive: str = "HKLM",
    view: str = "",
) -> TweakStep:
    key = f"{hive}\\{subkey}"
    cmd = ["reg", "add", key, "/v", value_name, "/t", value_type, "/d", data, "/f"]
    if view:
        cmd.insert(2, view)
    return TweakStep(
        description=f"Set {hive}\\{subkey} \\{value_name} = {data}",
        command=cmd,
        requires_admin=(hive == "HKLM"),
    )


def _reg_delete_value(subkey: str, value_name: str, *, hive: str = "HKLM") -> TweakStep:
    key = f"{hive}\\{subkey}"
    return TweakStep(
        description=f"Delete {hive}\\{subkey} \\{value_name}",
        command=["reg", "delete", key, "/v", value_name, "/f"],
        requires_admin=(hive == "HKLM"),
    )


def _sc_config(service: str, start: str = "disabled") -> TweakStep:
    return TweakStep(
        description=f"Set service {service} -> {start}",
        command=["sc", "config", service, "start=", start],
        requires_admin=True,
    )


def _sc_stop(service: str) -> TweakStep:
    return TweakStep(
        description=f"Stop service {service}",
        command=["sc", "stop", service],
        requires_admin=True,
    )


def _powercfg(args: list[str], desc: str) -> TweakStep:
    return TweakStep(description=desc, command=["powercfg", *args], requires_admin=True)


def _run(cmd: list[str]) -> TweakStep:
    return TweakStep(description=" ".join(cmd), command=cmd, requires_admin=True)


# ── Advanced Tweak definitions ─────────────────────────────────

ADVANCED_TWEAK_COMMANDS: dict[str, list[TweakStep]] = {
    "adv.clean_all": [
        _run(["del", "/q", "/f", "/s", "%TEMP%\\*"]),
        _run(["del", "/q", "/f", "/s", r"C:\Windows\Temp\*"]),
        _run(["del", "/q", "/f", "/s", r"C:\Windows\Prefetch\*"]),
    ],
    "adv.regedit_optimize": [
        _reg_add(
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Internet Settings",
            "MaxConnectionsPerServer",
            "REG_DWORD",
            "16",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters",
            "TCPNoDelay",
            "REG_DWORD",
            "1",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters",
            "Tcp1323Opts",
            "REG_DWORD",
            "1",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Services\Dnscache\Parameters",
            "MaxCacheEntryTtlLimit",
            "REG_DWORD",
            "86400",
        ),
    ],
    "adv.optimize_cpu": [
        _reg_add(
            r"SOFTWARE\Policies\Microsoft\Windows\DataCollection",
            "AllowTelemetry",
            "REG_DWORD",
            "0",
        ),
        _reg_add(
            r"SOFTWARE\Microsoft\Windows\Windows Error Reporting",
            "Disabled",
            "REG_DWORD",
            "1",
        ),
        _reg_add(
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer",
            "SmartScreenEnabled",
            "REG_SZ",
            "Off",
        ),
    ],
    "adv.optimize_gpu": [
        _reg_add(
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile",
            "GPU Priority",
            "REG_DWORD",
            "18",
        ),
        _reg_add(
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games",
            "GPU Priority",
            "REG_DWORD",
            "18",
        ),
        _reg_add(
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games",
            "Priority",
            "REG_DWORD",
            "6",
        ),
        _reg_add(
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games",
            "Scheduling Category",
            "REG_SZ",
            "High",
        ),
    ],
    "adv.optimize_ram": [
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management",
            "DisablePagingExecutive",
            "REG_DWORD",
            "1",
        ),
        _reg_add(
            _PREFETCH,
            "EnablePrefetcher",
            "REG_DWORD",
            "0",
        ),
        _reg_add(
            _PREFETCH,
            "EnableSuperfetch",
            "REG_DWORD",
            "0",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\FileSystem",
            "NtfsDisableLastAccessUpdate",
            "REG_DWORD",
            "1",
        ),
    ],
    "adv.set_virtual_ram": [
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management",
            "PagingFiles",
            "REG_MULTI_SZ",
            r"C:\pagefile.sys 4096 5096",
        ),
    ],
    "adv.boost_fps": [
        _reg_add(
            _PREFETCH,
            "EnablePrefetcher",
            "REG_DWORD",
            "0",
        ),
        _reg_add(
            _PREFETCH,
            "EnableSuperfetch",
            "REG_DWORD",
            "0",
        ),
        _reg_add(
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
            "Hidden",
            "REG_DWORD",
            "1",
            hive="HKCU",
        ),
    ],
    "adv.high_performance": [
        _powercfg(
            ["/setactive", "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"],
            "Activate High Performance power plan",
        ),
    ],
    "adv.ultimate_performance": [
        _powercfg(
            ["-duplicatescheme", "e9a42b02-d5df-448d-aa00-03f14749eb61"],
            "Duplicate Ultimate Performance power plan",
        ),
    ],
    "adv.optimize_tweaks": [
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\PriorityControl",
            "IRQ8Priority",
            "REG_DWORD",
            "1",
        ),
        _reg_add(
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile",
            "NetworkThrottlingIndex",
            "REG_DWORD",
            str(0xFFFFFFFF),
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters",
            "LargeSystemCache",
            "REG_DWORD",
            "1",
        ),
    ],
    "adv.turn_off_defender": [
        _reg_add(
            r"SOFTWARE\Policies\Microsoft\Windows Defender",
            "DisableAntiSpyware",
            "REG_DWORD",
            "1",
        ),
        _sc_stop("WdNisSvc"),
        _sc_config("WdNisSvc"),
        _sc_stop("WinDefend"),
        _sc_config("WinDefend"),
    ],
    "adv.turn_off_update": [
        _reg_add(
            r"SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU",
            "NoAutoUpdate",
            "REG_DWORD",
            "1",
        ),
        _reg_add(
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\DeliveryOptimization\Config",
            "DODownloadMode",
            "REG_DWORD",
            "0",
        ),
        _sc_stop("wuauserv"),
        _sc_config("wuauserv"),
    ],
    "adv.turn_off_firewall": [
        _reg_add(
            r"SOFTWARE\Policies\Microsoft\WindowsFirewall\DomainProfile",
            "EnableFirewall",
            "REG_DWORD",
            "0",
        ),
        _reg_add(
            r"SOFTWARE\Policies\Microsoft\WindowsFirewall\StandardProfile",
            "EnableFirewall",
            "REG_DWORD",
            "0",
        ),
        _reg_add(
            r"SOFTWARE\Policies\Microsoft\WindowsFirewall\PublicProfile",
            "EnableFirewall",
            "REG_DWORD",
            "0",
        ),
        _sc_stop("mpssvc"),
        _sc_config("mpssvc"),
    ],
    "adv.turn_off_hyperv": [
        _sc_config("HvHost"),
        _sc_config("vmickvpexchange"),
        _sc_config("vmicshutdown"),
        _sc_config("vmicrdv"),
        _sc_config("vmicvmsession"),
        _sc_config("vmicguestinterface"),
    ],
    "adv.turn_off_notifications": [
        _sc_stop("WerSvc"),
        _sc_config("WerSvc"),
        _sc_stop("WpnService"),
        _sc_config("WpnService"),
    ],
    "adv.turn_off_search": [
        _reg_add(
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Search",
            "AllowCortana",
            "REG_DWORD",
            "0",
        ),
        _reg_add(
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Search",
            "DisableWebSearch",
            "REG_DWORD",
            "1",
        ),
        _reg_add(
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Search",
            "BingSearchEnabled",
            "REG_DWORD",
            "0",
        ),
    ],
    "adv.turn_off_telemetry": [
        _reg_add(
            r"SOFTWARE\Policies\Microsoft\Windows\DataCollection",
            "AllowTelemetry",
            "REG_DWORD",
            "0",
        ),
        _reg_add(
            r"SOFTWARE\Policies\Microsoft\Windows\DataCollection",
            "AllowDeviceNameInTelemetry",
            "REG_DWORD",
            "0",
        ),
        _sc_stop("DiagTrack"),
        _sc_config("DiagTrack"),
    ],
    "adv.turn_off_bluetooth": [
        _sc_stop("BTAGService"),
        _sc_config("BTAGService"),
        _sc_stop("bthserv"),
        _sc_config("bthserv"),
        _sc_stop("BthAvctpSvc"),
        _sc_config("BthAvctpSvc"),
    ],
    "adv.turn_off_diagnostic": [
        _reg_add(
            r"SOFTWARE\Microsoft\RemovalTools",
            "DontReportInfectionInformation",
            "REG_DWORD",
            "1",
        ),
    ],
    "adv.turn_off_visual": [
        _reg_add(
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects",
            "VisualFXSetting",
            "REG_DWORD",
            "2",
        ),
        _sc_stop("Themes"),
        _sc_config("Themes"),
    ],
    "adv.optimize_mouse": [
        _reg_add(
            r"Control Panel\Mouse",
            "MouseSpeed",
            "REG_SZ",
            "0",
            hive="HKCU",
        ),
        _reg_add(
            r"Control Panel\Mouse",
            "MouseThreshold1",
            "REG_SZ",
            "0",
            hive="HKCU",
        ),
        _reg_add(
            r"Control Panel\Mouse",
            "MouseThreshold2",
            "REG_SZ",
            "0",
            hive="HKCU",
        ),
        _reg_add(
            r"Control Panel\Mouse",
            "MouseSensitivity",
            "REG_SZ",
            "10",
            hive="HKCU",
        ),
        _reg_add(
            r"Control Panel\Mouse",
            "SmoothMouseXCurve",
            "REG_BINARY",
            "0000000000000000C0CC0C0000000000" * 5,
            hive="HKCU",
        ),
    ],
    "adv.debloat_windows": [
        _run(
            [
                "powershell",
                "-Command",
                (
                    "Get-AppxPackage -AllUsers | Where-Object "
                    "{$_.Name -match '3DBuilder|Sway|Bing|Zune|Reader|Maps"
                    "|Phone|Wallet|Camera|Mail|Calendar|People|Feedback|Hub"
                    "|Mixed|OneConnect|Print3D|Skype|Tips|Microsoft3DViewer"
                    "|MicrosoftOfficeHub|WindowsCommunicationsApps|WindowsMaps"
                    "|BingWeather|BingNews|GetHelp|Getstarted|MSPaint"
                    "|MicrosoftStickyNotes|Office.OneNote|SkypeApp"
                    "|WindowsAlarms|WindowsCamera|XboxApp|YourPhone"
                    "|ZuneMusic|ZuneVideo'} | "
                    "Remove-AppxPackage -ErrorAction SilentlyContinue"
                ),
            ]
        ),
    ],
    "adv.boost_all_games": [
        _reg_add(
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
            r"\Multimedia\SystemProfile\Tasks\Games",
            "GPU Priority",
            "REG_DWORD",
            "18",
        ),
        _reg_add(
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
            r"\Multimedia\SystemProfile\Tasks\Games",
            "Priority",
            "REG_DWORD",
            "6",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management",
            "DisablePagingExecutive",
            "REG_DWORD",
            "1",
        ),
        _reg_add(r"Control Panel\Mouse", "MouseSpeed", "REG_SZ", "0", hive="HKCU"),
        _reg_add(r"Control Panel\Mouse", "MouseThreshold1", "REG_SZ", "0", hive="HKCU"),
        _reg_add(r"Control Panel\Mouse", "MouseThreshold2", "REG_SZ", "0", hive="HKCU"),
    ],
    "adv.super_optimize_bcedit": [
        _run(["bcdedit", "/set", "useplatformtick", "yes"]),
        _run(["bcdedit", "/set", "disabledynamictick", "yes"]),
        _run(["bcdedit", "/set", "tscsyncpolicy", "enhanced"]),
    ],
    "adv.delete_onedrive": [
        _run(["taskkill", "/f", "/im", "OneDrive.exe"]),
        _run([r"C:\Windows\System32\OneDriveSetup.exe", "/uninstall"]),
        _run(["rd", "/s", "/q", r"%USERPROFILE%\OneDrive"]),
        _run(["rd", "/s", "/q", r"C:\OneDriveTemp"]),
    ],
    "adv.speed_up_device": [
        _reg_add(
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Internet Settings",
            "MaxConnectionsPerServer",
            "REG_DWORD",
            "16",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\FileSystem",
            "NtfsDisableLastAccessUpdate",
            "REG_DWORD",
            "1",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management",
            "DisablePagingExecutive",
            "REG_DWORD",
            "1",
        ),
    ],
    "adv.turn_off_store": [
        _sc_config("WSService"),
        _reg_add(
            r"SOFTWARE\Policies\Microsoft\WindowsStore",
            "RemoveWindowsStore",
            "REG_DWORD",
            "1",
        ),
        _reg_add(
            r"SOFTWARE\Policies\Microsoft\WindowsStore",
            "AutoDownload",
            "REG_DWORD",
            "2",
        ),
    ],
    "adv.turn_off_disk_mgmt": [
        _sc_config("VDS"),
        _sc_stop("VDS"),
        _run(["sc", "config", "defragsvc", "start=", "disabled"]),
        _run(["sc", "stop", "defragsvc"]),
    ],
    "adv.turn_off_xbox": [
        _sc_config("XblAuthManager"),
        _sc_config("XblGameSave"),
        _sc_config("XboxGipSvc"),
        _sc_config("XboxNetApiSvc"),
    ],
    "adv.reduce_latency": [
        _reg_add(
            r"Control Panel\Desktop\WindowMetrics",
            "MinAnimate",
            "REG_SZ",
            "0",
            hive="HKCU",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\PriorityControl",
            "IRQ8Priority",
            "REG_DWORD",
            "1",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\Power",
            "HibernateEnabled",
            "REG_DWORD",
            "0",
        ),
    ],
}


# ── Tweak Menu definitions (the 5 original menu items) ────────
# Item 4 (recovery.revert_all_changes) uses action="restore" and is not listed
# here; it is handled by the restore flow rather than command execution.

TWEAK_MENU_COMMANDS: dict[str, list[TweakStep]] = {
    # Item 1 — APPLY REGEDIT: GPU/graphics/power/mouse registry tweaks.
    "system.apply_regedit": [
        # Power / session manager
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Power",
            "NoLazyMode",
            "REG_DWORD",
            "1",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\Power",
            "EnergyEstimationEnabled",
            "REG_DWORD",
            "0",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\Power",
            "CsEnabled",
            "REG_DWORD",
            "0",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\Power",
            "PerfCalculateActualUtilization",
            "REG_DWORD",
            "0",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\Power",
            "SleepReliabilityDetailedDiagnostics",
            "REG_DWORD",
            "0",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\Power",
            "EventProcessorEnabled",
            "REG_DWORD",
            "0",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\Power",
            "QosManagesIdleProcessors",
            "REG_DWORD",
            "0",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\Power",
            "DisableVsyncLatencyUpdate",
            "REG_DWORD",
            "1",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\Power",
            "DisableSensorWatchdog",
            "REG_DWORD",
            "1",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\Power",
            "ExitLatencyCheckEnabled",
            "REG_DWORD",
            "0",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\Power\PowerThrottling",
            "PowerThrottlingOff",
            "REG_DWORD",
            "1",
        ),
        # NVIDIA telemetry
        _reg_add(
            r"SOFTWARE\NVIDIA Corporation\NVIDIA GeForce Experience",
            "SendTelemetryData",
            "REG_DWORD",
            "0",
        ),
        _reg_add(
            r"SYSTEM\ControlSet001\Services\NvTelemetryContainer",
            "Start",
            "REG_DWORD",
            "4",
        ),
        _reg_add(
            r"SOFTWARE\NVIDIA Corporation\Global\FTS",
            "EnableFTS",
            "REG_DWORD",
            "0",
        ),
        _reg_add(
            r"SOFTWARE\NVIDIA Corporation\Global\FTS",
            "OptInOrOutPreference",
            "REG_DWORD",
            "0",
        ),
        # Direct3D
        _reg_add(
            r"SOFTWARE\Microsoft\Direct3D",
            "DisableVidMemBs",
            "REG_DWORD",
            "0",
        ),
        _reg_add(
            r"SOFTWARE\Microsoft\Direct3D",
            "FlipNoVsync",
            "REG_DWORD",
            "1",
        ),
        _reg_add(
            r"SOFTWARE\Microsoft\Direct3D",
            "SoftwareOnly",
            "REG_DWORD",
            "0",
        ),
        _reg_add(
            r"SOFTWARE\Microsoft\Direct3D\Drivers",
            "MMX Fast Path",
            "REG_DWORD",
            "1",
        ),
        # GraphicsDrivers / TDR
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers",
            "TdrLevel",
            "REG_DWORD",
            "0",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers",
            "TdrDebugMode",
            "REG_DWORD",
            "0",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers",
            "HwSchedMode",
            "REG_DWORD",
            "2",
        ),
        # Cursor latency
        _reg_add(
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
            r"CursorMagnetism\MagnetismUpdateIntervalInMilliseconds",
            "REG_DWORD",
            "1",
        ),
        _reg_add(
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
            r"CursorSpeed\CursorUpdateInterval",
            "REG_DWORD",
            "1",
        ),
        # Reliability
        _reg_add(
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Reliability",
            "TimeStampInterval",
            "REG_DWORD",
            "0",
        ),
        # DWM
        _reg_add(
            r"SOFTWARE\Microsoft\Windows\DWM",
            "CompositionPolicy",
            "REG_DWORD",
            "0",
        ),
        # AMD telemetry
        _reg_add(
            r"SYSTEM\ControlSet001\Services\amdlog",
            "Start",
            "REG_DWORD",
            "4",
        ),
        # GPU class / power management
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\Class"
            r"\{4d36e968-e325-11ce-bfc1-08002be10318}\0000",
            "DisableDMACopy",
            "REG_DWORD",
            "1",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\Class"
            r"\{4d36e968-e325-11ce-bfc1-08002be10318}\0000",
            "StutterMode",
            "REG_DWORD",
            "0",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\Class"
            r"\{4d36e968-e325-11ce-bfc1-08002be10318}\0000",
            "EnableUlps",
            "REG_DWORD",
            "0",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\Class"
            r"\{4d36e968-e325-11ce-bfc1-08002be10318}\0000",
            "PP_SclkDeepSleepDisable",
            "REG_DWORD",
            "1",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\Class"
            r"\{4d36e968-e325-11ce-bfc1-08002be10318}\0000",
            "PP_ThermalAutoThrottlingEnable",
            "REG_DWORD",
            "0",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\Class"
            r"\{4d36e968-e325-11ce-bfc1-08002be10318}\0000",
            "DisableDrmdmaPowerGating",
            "REG_DWORD",
            "1",
        ),
        # Games task scheduling
        _reg_add(
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
            r"\Multimedia\SystemProfile\Tasks\Games",
            "GPU Priority",
            "REG_DWORD",
            "8",
        ),
        _reg_add(
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
            r"\Multimedia\SystemProfile\Tasks\Games",
            "Priority",
            "REG_DWORD",
            "6",
        ),
        _reg_add(
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
            r"\Multimedia\SystemProfile\Tasks\Games",
            "Scheduling Category",
            "REG_SZ",
            "High",
        ),
        _reg_add(
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
            r"\Multimedia\SystemProfile\Tasks\Games",
            "SFIO Priority",
            "REG_SZ",
            "High",
        ),
        _reg_add(
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
            r"\Multimedia\SystemProfile\Tasks\Games",
            "Latency Sensitive",
            "REG_SZ",
            "True",
        ),
        # Mouse
        _reg_add(r"Control Panel\Mouse", "MouseHoverTime", "REG_SZ", "0", hive="HKCU"),
        _reg_add(
            r"Control Panel\Mouse",
            "MouseSensitivity",
            "REG_SZ",
            "10",
            hive="HKCU",
        ),
        _reg_add(
            r"Control Panel\Mouse",
            "SmoothMouseXCurve",
            "REG_BINARY",
            "0000000000000000C0CC0C000000000000"
            "0000C0CC0C0000000000"
            "00000000C0CC0C00000000000000"
            "0000C0CC0C00000000000000"
            "000000C0CC0C00000000000000",
            hive="HKCU",
        ),
        _reg_add(
            r"Control Panel\Mouse",
            "SmoothMouseYCurve",
            "REG_BINARY",
            "000000000000000000000000000000000000"
            "00000000000000000000"
            "0000000000000000000000000000"
            "00000000000000000000"
            "000000000000000000000000",
            hive="HKCU",
        ),
        _reg_add(
            r"Control Panel\Mouse",
            "TreatAbsolutePointerAsAbsolute",
            "REG_DWORD",
            "1",
            hive="HKCU",
        ),
        _reg_add(
            r"Control Panel\Mouse",
            "TreatAbsoluteAsRelative",
            "REG_DWORD",
            "0",
            hive="HKCU",
        ),
        # Mouse / keyboard buffers
        _reg_add(
            r"SYSTEM\CurrentControlSet\Services\mouclass\Parameters",
            "MouseDataQueueSize",
            "REG_DWORD",
            "16",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Services\kbdclass\Parameters",
            "KeyboardDataQueueSize",
            "REG_DWORD",
            "16",
        ),
        # Priority control
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\PriorityControl",
            "Win32PrioritySeparation",
            "REG_DWORD",
            "26",
        ),
        # Memory management
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management",
            "FeatureSettingsOverride",
            "REG_DWORD",
            "3",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management",
            "FeatureSettingsOverrideMask",
            "REG_DWORD",
            "3",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management",
            "LargeSystemCache",
            "REG_DWORD",
            "1",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management",
            "EnableCfg",
            "REG_DWORD",
            "0",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management",
            "FeatureSettings",
            "REG_DWORD",
            "1",
        ),
        # Prefetch / hibernate
        _reg_add(_PREFETCH, "EnablePrefetcher", "REG_DWORD", "0"),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\Power",
            "HibernateEnabled",
            "REG_DWORD",
            "0",
        ),
        # CSRSS priority
        _reg_add(
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options"
            r"\csrss.exe\PerfOptions",
            "CpuPriorityClass",
            "REG_DWORD",
            "4",
        ),
    ],
    # Item 2 — CLEAN TEMP FILES
    "cleanup.clean_temp_files": [
        _run(["del", "/q", "/f", "/s", "%TEMP%\\*"]),
    ],
    # Item 3 — APPLY BOOSTER: bcdedit + service Start=4 disables.
    "system.apply_booster": [
        # bcdedit commands
        _run(["bcdedit", "/deletevalue", "useplatformclock"]),
        _run(["bcdedit", "/set", "disabledynamictick", "Yes"]),
        _run(["bcdedit", "/set", "bootmenupolicy", "Legacy"]),
        _run(["bcdedit", "/set", "debug", "No"]),
        _run(["bcdedit", "/set", "isolatedcontext", "No"]),
        _run(["bcdedit", "/set", "pae", "ForceEnable"]),
        _run(["bcdedit", "/set", "bootux", "disabled"]),
        _run(["bcdedit", "/set", "sos", "Yes"]),
        _run(["bcdedit", "/set", "ems", "No"]),
        _run(["bcdedit", "/set", "hypervisorlaunchtype", "off"]),
        _run(["bcdedit", "/set", "quietboot", "yes"]),
        _run(["bcdedit", "/set", "uselegacyapicmode", "no"]),
        _run(["bcdedit", "/timeout", "3"]),
        _run(["bcdedit", "/set", "tpmbootentropy", "ForceDisable"]),
        _run(["bcdedit", "/set", "allowedinmemorysettings", "0x0"]),
        _run(["bcdedit", "/set", "usefirmwarepcisettings", "No"]),
        _run(["bcdedit", "/set", "tscsyncpolicy", "Enhanced"]),
        _run(["bcdedit", "/set", "x2apicpolicy", "Enable"]),
        _run(["bcdedit", "/set", "usephysicaldestination", "No"]),
        _run(["bcdedit", "/set", "IncreaseUserVA", "0"]),
        _run(["bcdedit", "/set", "useplatformtick", "yes"]),
        # Service disables (Start=4 via registry, matching Amber)
        _reg_add(r"SYSTEM\ControlSet001\Services\TapiSrv", "Start", "REG_DWORD", "4"),
        _reg_add(
            r"SYSTEM\ControlSet001\Services\FontCache3.0.0.0",
            "Start",
            "REG_DWORD",
            "4",
        ),
        _reg_add(r"SYSTEM\ControlSet001\Services\WpcMonSvc", "Start", "REG_DWORD", "4"),
        _reg_add(r"SYSTEM\ControlSet001\Services\SEMgrSvc", "Start", "REG_DWORD", "4"),
        _reg_add(r"SYSTEM\ControlSet001\Services\PNRPsvc", "Start", "REG_DWORD", "4"),
        _reg_add(r"SYSTEM\ControlSet001\Services\WEPHOSTSVC", "Start", "REG_DWORD", "4"),
        _reg_add(r"SYSTEM\ControlSet001\Services\p2psvc", "Start", "REG_DWORD", "4"),
        _reg_add(r"SYSTEM\ControlSet001\Services\p2pimsvc", "Start", "REG_DWORD", "4"),
        _reg_add(r"SYSTEM\ControlSet001\Services\PhoneSvc", "Start", "REG_DWORD", "4"),
        _reg_add(r"SYSTEM\ControlSet001\Services\Wecsvc", "Start", "REG_DWORD", "4"),
        _reg_add(r"SYSTEM\ControlSet001\Services\RmSvc", "Start", "REG_DWORD", "4"),
        _reg_add(
            r"SYSTEM\ControlSet001\Services\SensorDataService",
            "Start",
            "REG_DWORD",
            "4",
        ),
        _reg_add(r"SYSTEM\ControlSet001\Services\SensrSvc", "Start", "REG_DWORD", "4"),
        _reg_add(
            r"SYSTEM\ControlSet001\Services\perceptionsimulation",
            "Start",
            "REG_DWORD",
            "4",
        ),
        _reg_add(r"SYSTEM\ControlSet001\Services\StiSvc", "Start", "REG_DWORD", "4"),
        _reg_add(r"SYSTEM\ControlSet001\Services\WMPNetworkSvc", "Start", "REG_DWORD", "4"),
        _reg_add(r"SYSTEM\ControlSet001\Services\CaptureService", "Start", "REG_DWORD", "4"),
        _reg_add(r"SYSTEM\ControlSet001\Services\autotimesvc", "Start", "REG_DWORD", "4"),
        _reg_add(
            r"SYSTEM\ControlSet001\Services\MessagingService",
            "Start",
            "REG_DWORD",
            "4",
        ),
        _reg_add(r"SYSTEM\ControlSet001\Services\CDPUserSvc", "Start", "REG_DWORD", "4"),
        _reg_add(
            r"SYSTEM\ControlSet001\Services\PimIndexMaintenanceSvc",
            "Start",
            "REG_DWORD",
            "4",
        ),
        _reg_add(
            r"SYSTEM\ControlSet001\Services\BcastDVRUserService",
            "Start",
            "REG_DWORD",
            "4",
        ),
        _reg_add(r"SYSTEM\ControlSet001\Services\UserDataSvc", "Start", "REG_DWORD", "4"),
        _reg_add(r"SYSTEM\ControlSet001\Services\ALG", "Start", "REG_DWORD", "4"),
        _reg_add(r"SYSTEM\ControlSet001\Services\QWAVE", "Start", "REG_DWORD", "4"),
        _reg_add(r"SYSTEM\ControlSet001\Services\IpxlatCfgSvc", "Start", "REG_DWORD", "4"),
        _reg_add(r"SYSTEM\ControlSet001\Services\icssvc", "Start", "REG_DWORD", "4"),
        _reg_add(r"SYSTEM\ControlSet001\Services\DusmSvc", "Start", "REG_DWORD", "4"),
        _reg_add(r"SYSTEM\ControlSet001\Services\MapsBroker", "Start", "REG_DWORD", "4"),
        _reg_add(r"SYSTEM\ControlSet001\Services\SensorService", "Start", "REG_DWORD", "4"),
        _reg_add(r"SYSTEM\ControlSet001\Services\shpamsvc", "Start", "REG_DWORD", "4"),
        _reg_add(r"SYSTEM\ControlSet001\Services\svsvc", "Start", "REG_DWORD", "4"),
        _reg_add(r"SYSTEM\ControlSet001\Services\SysMain", "Start", "REG_DWORD", "4"),
        _reg_add(r"SYSTEM\ControlSet001\Services\MSiSCSI", "Start", "REG_DWORD", "4"),
        _reg_add(r"SYSTEM\ControlSet001\Services\Netlogon", "Start", "REG_DWORD", "4"),
        _reg_add(r"SYSTEM\ControlSet001\Services\CscService", "Start", "REG_DWORD", "4"),
        _reg_add(r"SYSTEM\ControlSet001\Services\ssh-agent", "Start", "REG_DWORD", "4"),
        _reg_add(r"SYSTEM\ControlSet001\Services\AppReadiness", "Start", "REG_DWORD", "4"),
        _reg_add(r"SYSTEM\ControlSet001\Services\tzautoupdate", "Start", "REG_DWORD", "4"),
        _reg_add(r"SYSTEM\ControlSet001\Services\NfsClnt", "Start", "REG_DWORD", "4"),
        _reg_add(r"SYSTEM\ControlSet001\Services\wisvc", "Start", "REG_DWORD", "4"),
        _reg_add(
            r"SYSTEM\ControlSet001\Services\SharedRealitySvc",
            "Start",
            "REG_DWORD",
            "4",
        ),
        _reg_add(r"SYSTEM\ControlSet001\Services\RetailDemo", "Start", "REG_DWORD", "4"),
        _reg_add(r"SYSTEM\ControlSet001\Services\lltdsvc", "Start", "REG_DWORD", "4"),
        _reg_add(r"SYSTEM\ControlSet001\Services\TrkWks", "Start", "REG_DWORD", "4"),
        _reg_add(r"SYSTEM\ControlSet001\Services\AppIDSvc", "Start", "REG_DWORD", "4"),
        _reg_add(r"SYSTEM\ControlSet001\Services\CryptSvc", "Start", "REG_DWORD", "4"),
        _reg_add(r"SYSTEM\ControlSet001\Services\edgeupdatem", "Start", "REG_DWORD", "4"),
        _reg_add(
            r"SYSTEM\ControlSet001\Services\MicrosoftEdgeElevationService",
            "Start",
            "REG_DWORD",
            "4",
        ),
        _reg_add(r"SYSTEM\ControlSet001\Services\edgeupdate", "Start", "REG_DWORD", "4"),
        # Telemetry services + settings
        _reg_add(r"SYSTEM\ControlSet001\Services\DiagTrack", "Start", "REG_DWORD", "4"),
        _reg_add(r"SYSTEM\ControlSet001\Services\diagsvc", "Start", "REG_DWORD", "4"),
        _reg_add(r"SYSTEM\ControlSet001\Services\DPS", "Start", "REG_DWORD", "4"),
        _reg_add(r"SYSTEM\ControlSet001\Services\WdiServiceHost", "Start", "REG_DWORD", "4"),
        _reg_add(r"SYSTEM\ControlSet001\Services\WdiSystemHost", "Start", "REG_DWORD", "4"),
        _reg_add(
            r"SOFTWARE\Policies\Microsoft\Windows\DataCollection",
            "AllowTelemetry",
            "REG_DWORD",
            "0",
        ),
        _reg_add(
            r"SYSTEM\ControlSet001\Services\dmwappushsvc",
            "Start",
            "REG_DWORD",
            "4",
        ),
        _reg_add(
            r"SYSTEM\ControlSet001\Services"
            r"\diagnosticshub.standardcollector.service",
            "Start",
            "REG_DWORD",
            "4",
        ),
        _reg_add(
            r"SYSTEM\ControlSet001\Services\TroubleshootingSvc",
            "Start",
            "REG_DWORD",
            "4",
        ),
        _reg_add(r"SYSTEM\ControlSet001\Services\DsSvc", "Start", "REG_DWORD", "4"),
        # Advertising
        _reg_add(
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\AdvertisingInfo",
            "Enabled",
            "REG_DWORD",
            "0",
        ),
        _reg_add(
            r"SOFTWARE\Policies\Microsoft\Windows\AdvertisingInfo",
            "DisabledByGroupPolicy",
            "REG_DWORD",
            "1",
        ),
        # Privacy
        _reg_add(
            r"SOFTWARE\Policies\Microsoft\InputPersonalization",
            "RestrictImplicitInkCollection",
            "REG_DWORD",
            "1",
        ),
        _reg_add(
            r"SOFTWARE\Policies\Microsoft\InputPersonalization",
            "RestrictImplicitTextCollection",
            "REG_DWORD",
            "1",
        ),
        _reg_add(
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\SettingSync",
            "HarvestContacts",
            "REG_DWORD",
            "0",
        ),
        _reg_add(
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\DataCollection",
            "MetricsReportingEnabled",
            "REG_DWORD",
            "0",
        ),
        _reg_add(
            r"SOFTWARE\Policies\Microsoft\Windows\HandwritingErrorReports",
            "PreventHandwritingErrorReports",
            "REG_DWORD",
            "1",
        ),
        _reg_add(
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Internet Settings",
            "HttpAcceptLanguageOptOut",
            "REG_DWORD",
            "1",
        ),
        _reg_add(
            r"SOFTWARE\Policies\Microsoft\Windows\LocationAndSensors",
            "DisableLocation",
            "REG_DWORD",
            "1",
        ),
        _reg_add(
            r"SOFTWARE\Policies\Microsoft\Windows\LocationAndSensors",
            "DisableSensors",
            "REG_DWORD",
            "1",
        ),
    ],
    # Item 5 — CLEAN LOG FILES
    "cleanup.clean_log_files": [
        _run(["del", "%homepath%\\*.log", "/Q", "/A", "/S", "/F"]),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management",
            "ClearPageFileAtShutdown",
            "REG_DWORD",
            "0",
        ),
    ],
}

# ── AppSensiX definitions ──────────────────────────────────────
# OneTap Vector X: SENSI X PRO folder (8 files)
GAMING_TWEAK_COMMANDS: dict[str, list[TweakStep]] = {
    "aim_smooth": [
        # raw input acceleration.reg
        _reg_add(r"Control Panel\Mouse", "MouseSpeed", "REG_SZ", "0", hive="HKCU"),
        _reg_add(r"Control Panel\Mouse", "MouseThreshold1", "REG_SZ", "0", hive="HKCU"),
        _reg_add(r"Control Panel\Mouse", "MouseThreshold2", "REG_SZ", "0", hive="HKCU"),
        _reg_add(r"Control Panel\Desktop", "MouseSensitivity", "REG_SZ", "10", hive="HKCU"),
        # Mouse class buffer.reg
        _reg_add(
            r"SYSTEM\CurrentControlSet\Services\mouclass\Parameters",
            "MouseDataQueueSize",
            "REG_DWORD",
            "54",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Services\mouhid\Parameters",
            "MouseDataQueueSize",
            "REG_DWORD",
            "54",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Services\kbdclass\Parameters",
            "KeyboardDataQueueSize",
            "REG_DWORD",
            "54",
        ),
        # CPU priority separation.reg
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\PriorityControl",
            "Win32PrioritySeparation",
            "REG_DWORD",
            "38",
        ),
        _reg_add(
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile",
            "SystemResponsiveness",
            "REG_DWORD",
            "0",
        ),
        _reg_add(
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile",
            "NetworkThrottlingIndex",
            "REG_DWORD",
            str(0xFFFFFFFF),
        ),
        # force gpu.reg
        _reg_add(
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
            r"\Multimedia\SystemProfile\Tasks\Games",
            "GPU Priority",
            "REG_DWORD",
            "8",
        ),
        _reg_add(
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
            r"\Multimedia\SystemProfile\Tasks\Games",
            "Priority",
            "REG_DWORD",
            "6",
        ),
        _reg_add(
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
            r"\Multimedia\SystemProfile\Tasks\Games",
            "Latency Sensitive",
            "REG_DWORD",
            "1",
        ),
        _reg_add(
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
            r"\Multimedia\SystemProfile\Tasks\Games",
            "Scheduling Category",
            "REG_SZ",
            "High",
        ),
        _reg_add(
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
            r"\Multimedia\SystemProfile\Tasks\Games",
            "SFIO Priority",
            "REG_SZ",
            "High",
        ),
        # Disable USB selective suspend.reg
        _reg_add(
            r"SYSTEM\CurrentControlSet\Services\USB\Parameters",
            "DisableSelectiveSuspend",
            "REG_DWORD",
            "1",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\Power\PowerThrottling",
            "PowerThrottlingOff",
            "REG_DWORD",
            "1",
        ),
        # tcpnodelay.reg
        _reg_add(
            r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters",
            "TcpAckFrequency",
            "REG_DWORD",
            "1",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters",
            "TcpNoDelay",
            "REG_DWORD",
            "1",
        ),
        # Kill latency processes (no delay latency processses.bat)
        _run(["taskkill", "/f", "/im", "msedge.exe"]),
        _run(["taskkill", "/f", "/im", "EpicGamesLauncher.exe"]),
        _run(["taskkill", "/f", "/im", "Teams.exe"]),
        _run(["taskkill", "/f", "/im", "OneDrive.exe"]),
        # Set HD-Player priority Realtime
        _run(
            [
                "wmic",
                "process",
                "where",
                "name='hd-player.exe'",
                "CALL",
                "setpriority",
                "Realtime",
            ]
        ),
    ],
    # Neural AimSync X: aim_optimizer.bat + AMD.bat
    "aim_stabilizer": [
        # Mouse (aim_optimizer.bat)
        _reg_add(r"Control Panel\Mouse", "MouseSensitivity", "REG_SZ", "10", hive="HKCU"),
        _reg_add(r"Control Panel\Mouse", "MouseSpeed", "REG_SZ", "0", hive="HKCU"),
        _reg_add(r"Control Panel\Mouse", "MouseThreshold1", "REG_SZ", "0", hive="HKCU"),
        _reg_add(r"Control Panel\Mouse", "MouseThreshold2", "REG_SZ", "0", hive="HKCU"),
        _reg_add(
            r"Control Panel\Mouse",
            "SmoothMouseXCurve",
            "REG_BINARY",
            "00" * 40,
            hive="HKCU",
        ),
        _reg_add(
            r"Control Panel\Mouse",
            "SmoothMouseYCurve",
            "REG_BINARY",
            "00" * 40,
            hive="HKCU",
        ),
        # Keyboard (aim_optimizer.bat)
        _reg_add(r"Control Panel\Keyboard", "KeyboardDelay", "REG_SZ", "0", hive="HKCU"),
        _reg_add(r"Control Panel\Keyboard", "KeyboardSpeed", "REG_SZ", "31", hive="HKCU"),
        # Mouse queue (AMD.bat uses 300)
        _reg_add(
            r"SYSTEM\CurrentControlSet\Services\mouclass\Parameters",
            "MouseDataQueueSize",
            "REG_DWORD",
            "300",
        ),
        # Power plans (aim_optimizer.bat)
        _powercfg(
            ["/setactive", "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"],
            "High Performance power plan",
        ),
        _powercfg(
            ["-duplicatescheme", "e9a42b02-d5df-448d-aa00-03f14749eb61"],
            "Ultimate Performance power plan",
        ),
        # Services (aim_optimizer.bat)
        _sc_config("DiagTrack"),
        _sc_stop("DiagTrack"),
        _sc_config("dmwappushservice"),
        _sc_stop("dmwappushservice"),
        _sc_config("SysMain"),
        _sc_stop("SysMain"),
        # Games Task (aim_optimizer.bat)
        _reg_add(
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
            r"\Multimedia\SystemProfile\Tasks\Games",
            "GPU Priority",
            "REG_DWORD",
            "8",
        ),
        _reg_add(
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
            r"\Multimedia\SystemProfile\Tasks\Games",
            "Priority",
            "REG_DWORD",
            "6",
        ),
        _reg_add(
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
            r"\Multimedia\SystemProfile\Tasks\Games",
            "Scheduling Category",
            "REG_SZ",
            "High",
        ),
        # Telemetry (aim_optimizer.bat)
        _reg_add(
            r"SOFTWARE\Policies\Microsoft\Windows\DataCollection",
            "AllowTelemetry",
            "REG_DWORD",
            "0",
        ),
        # Game DVR (AMD.bat)
        _reg_add(r"System\GameConfigStore", "GameDVR_Enabled", "REG_DWORD", "0", hive="HKCU"),
        _reg_add(
            r"SOFTWARE\Policies\Microsoft\Windows\GameDVR",
            "AllowGameDVR",
            "REG_DWORD",
            "0",
        ),
        # Network (AMD.bat)
        _reg_add(
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile",
            "NetworkThrottlingIndex",
            "REG_DWORD",
            str(0xFFFFFFFF),
        ),
        _reg_add(
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile",
            "SystemResponsiveness",
            "REG_DWORD",
            "0",
        ),
        # Power (AMD.bat)
        _run(
            [
                "powercfg",
                "/setacvalueindex",
                "SCHEME_CURRENT",
                "SUB_PROCESSOR",
                "PROCTHROTTLEMAX",
                "100",
            ]
        ),
        _run(["powercfg", "/setactive", "SCHEME_CURRENT"]),
        # Emulator priority (AMD.bat)
        _reg_add(
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
            r"\Image File Execution Options\HD-Player.exe\PerfOptions",
            "CpuPriorityClass",
            "REG_DWORD",
            "3",
        ),
        _reg_add(
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
            r"\Image File Execution Options\HD-Player.exe\PerfOptions",
            "IoPriority",
            "REG_DWORD",
            "3",
        ),
        _reg_add(
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
            r"\Image File Execution Options\MSIPlayer.exe\PerfOptions",
            "CpuPriorityClass",
            "REG_DWORD",
            "3",
        ),
        _reg_add(
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
            r"\Image File Execution Options\BlueStacks.exe\PerfOptions",
            "CpuPriorityClass",
            "REG_DWORD",
            "3",
        ),
        # CSRSS + DWM priority (AMD.bat)
        _reg_add(
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
            r"\Image File Execution Options\csrss.exe\PerfOptions",
            "CpuPriorityClass",
            "REG_DWORD",
            "3",
        ),
        _reg_add(
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
            r"\Image File Execution Options\dwm.exe\PerfOptions",
            "CpuPriorityClass",
            "REG_DWORD",
            "3",
        ),
        # Game Bar (AMD.bat)
        _reg_add(
            r"Software\Microsoft\GameBar",
            "ShowGameBadge",
            "REG_DWORD",
            "0",
            hive="HKCU",
        ),
        _reg_add(
            r"Software\Microsoft\GameBar",
            "UseNexusForGameBarEnabled",
            "REG_DWORD",
            "0",
            hive="HKCU",
        ),
        # Flush RAM (AMD.bat)
        _run(
            [
                "powershell",
                "-Command",
                "Get-Process | ForEach-Object { $_.WorkingSet64 = 0 }",
            ]
        ),
        # Restart Explorer (AMD.bat)
        _run(["taskkill", "/f", "/im", "explorer.exe"]),
        _run(["start", "explorer.exe"]),
    ],
    # DragShot Velocity X: INVI XD SENSI.bat + regedit_sensi.reg
    "easy_drag": [
        # Mouse (regedit_sensi.reg)
        _reg_add(r"Control Panel\Mouse", "MouseSpeed", "REG_SZ", "0", hive="HKCU"),
        _reg_add(r"Control Panel\Mouse", "MouseThreshold1", "REG_SZ", "0", hive="HKCU"),
        _reg_add(r"Control Panel\Mouse", "MouseThreshold2", "REG_SZ", "0", hive="HKCU"),
        _reg_add(r"Control Panel\Mouse", "MouseHoverTime", "REG_SZ", "10", hive="HKCU"),
        _reg_add(r"Control Panel\Mouse", "MouseHoverWidth", "REG_SZ", "2", hive="HKCU"),
        _reg_add(r"Control Panel\Mouse", "MouseHoverHeight", "REG_SZ", "2", hive="HKCU"),
        _reg_add(r"Control Panel\Mouse", "DoubleClickWidth", "REG_SZ", "2", hive="HKCU"),
        _reg_add(r"Control Panel\Mouse", "DoubleClickHeight", "REG_SZ", "2", hive="HKCU"),
        _reg_add(r"Control Panel\Mouse", "DoubleClickSpeed", "REG_SZ", "350", hive="HKCU"),
        _reg_add(r"Control Panel\Mouse", "MouseVanish", "REG_SZ", "0", hive="HKCU"),
        _reg_add(r"Control Panel\Mouse", "CursorShadow", "REG_SZ", "0", hive="HKCU"),
        _reg_add(r"Control Panel\Mouse", "MouseTrails", "REG_SZ", "0", hive="HKCU"),
        _reg_add(
            r"Control Panel\Mouse",
            "ScrollInactiveWindows",
            "REG_SZ",
            "0",
            hive="HKCU",
        ),
        _reg_add(r"Control Panel\Mouse", "MouseWheelRouting", "REG_DWORD", "0", hive="HKCU"),
        _reg_add(r"Control Panel\Mouse", "WheelScrollLines", "REG_SZ", "3", hive="HKCU"),
        _reg_add(
            r"Control Panel\Mouse",
            "SmoothMouseXCurve",
            "REG_BINARY",
            "00" * 24,
            hive="HKCU",
        ),
        _reg_add(
            r"Control Panel\Mouse",
            "SmoothMouseYCurve",
            "REG_BINARY",
            "00" * 24,
            hive="HKCU",
        ),
        # Desktop (regedit_sensi.reg)
        _reg_add(r"Control Panel\Desktop", "MouseSensitivity", "REG_SZ", "10", hive="HKCU"),
        _reg_add(
            r"Control Panel\Desktop",
            "ForegroundLockTimeout",
            "REG_DWORD",
            "0",
            hive="HKCU",
        ),
        _reg_add(
            r"Control Panel\Desktop",
            "ForegroundFlashCount",
            "REG_DWORD",
            "1",
            hive="HKCU",
        ),
        _reg_add(r"Control Panel\Desktop", "AutoEndTasks", "REG_SZ", "1", hive="HKCU"),
        _reg_add(
            r"Control Panel\Desktop",
            "WaitToKillAppTimeout",
            "REG_SZ",
            "1000",
            hive="HKCU",
        ),
        _reg_add(r"Control Panel\Desktop", "HungAppTimeout", "REG_SZ", "1000", hive="HKCU"),
        _reg_add(r"Control Panel\Desktop", "MenuShowDelay", "REG_SZ", "0", hive="HKCU"),
        _reg_add(r"Control Panel\Desktop", "DragFullWindows", "REG_SZ", "1", hive="HKCU"),
        _reg_add(
            r"Control Panel\Desktop",
            "LowLevelHooksTimeout",
            "REG_DWORD",
            "1000",
            hive="HKCU",
        ),
        _reg_add(
            r"Control Panel\Desktop",
            "UserPreferencesMask",
            "REG_BINARY",
            "9012038010000000",
            hive="HKCU",
        ),
        # Keyboard (regedit_sensi.reg)
        _reg_add(r"Control Panel\Keyboard", "KeyboardDelay", "REG_SZ", "0", hive="HKCU"),
        _reg_add(r"Control Panel\Keyboard", "KeyboardSpeed", "REG_SZ", "31", hive="HKCU"),
        # Accessibility (regedit_sensi.reg)
        _reg_add(
            r"Control Panel\Accessibility\StickyKeys",
            "Flags",
            "REG_SZ",
            "58",
            hive="HKCU",
        ),
        _reg_add(
            r"Control Panel\Accessibility\ToggleKeys",
            "Flags",
            "REG_SZ",
            "58",
            hive="HKCU",
        ),
        _reg_add(
            r"Control Panel\Accessibility\Keyboard Response",
            "Flags",
            "REG_SZ",
            "122",
            hive="HKCU",
        ),
        _reg_add(
            r"Control Panel\Accessibility\Keyboard Response",
            "AutoRepeatDelay",
            "REG_SZ",
            "300",
            hive="HKCU",
        ),
        _reg_add(
            r"Control Panel\Accessibility\Keyboard Response",
            "AutoRepeatRate",
            "REG_SZ",
            "506",
            hive="HKCU",
        ),
        _reg_add(
            r"Control Panel\Accessibility\Keyboard Response",
            "DelayBeforeAcceptance",
            "REG_SZ",
            "300",
            hive="HKCU",
        ),
        _reg_add(
            r"Control Panel\Accessibility\Keyboard Response",
            "BounceTime",
            "REG_SZ",
            "0",
            hive="HKCU",
        ),
        # Priority & IRQ (regedit_sensi.reg)
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\PriorityControl",
            "Win32PrioritySeparation",
            "REG_DWORD",
            "38",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\PriorityControl",
            "IRQ8Priority",
            "REG_DWORD",
            "1",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\PriorityControl",
            "IRQ16Priority",
            "REG_DWORD",
            "1",
        ),
        # Driver buffers (regedit_sensi.reg)
        _reg_add(
            r"SYSTEM\CurrentControlSet\Services\mouclass\Parameters",
            "MouseDataQueueSize",
            "REG_DWORD",
            "54",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Services\mouhid\Parameters",
            "MouseDataQueueSize",
            "REG_DWORD",
            "0",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Services\kbdclass\Parameters",
            "KeyboardDataQueueSize",
            "REG_DWORD",
            "54",
        ),
        # Multimedia & Games (regedit_sensi.reg)
        _reg_add(
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile",
            "NetworkThrottlingIndex",
            "REG_DWORD",
            str(0xFFFFFFFF),
        ),
        _reg_add(
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile",
            "SystemResponsiveness",
            "REG_DWORD",
            "0",
        ),
        _reg_add(
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
            r"\Multimedia\SystemProfile\Tasks\Games",
            "GPU Priority",
            "REG_DWORD",
            "8",
        ),
        _reg_add(
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
            r"\Multimedia\SystemProfile\Tasks\Games",
            "Priority",
            "REG_DWORD",
            "6",
        ),
        _reg_add(
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
            r"\Multimedia\SystemProfile\Tasks\Games",
            "Scheduling Category",
            "REG_SZ",
            "High",
        ),
        _reg_add(
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
            r"\Multimedia\SystemProfile\Tasks\Games",
            "SFIO Priority",
            "REG_SZ",
            "High",
        ),
        # Filesystem (regedit_sensi.reg)
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\FileSystem",
            "NtfsDisableLastAccessUpdate",
            "REG_DWORD",
            "1",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management",
            "LargeSystemCache",
            "REG_DWORD",
            "0",
        ),
        # QoS (regedit_sensi.reg)
        _reg_add(
            r"SOFTWARE\Policies\Microsoft\Windows\Psched",
            "NonBestEffortLimit",
            "REG_DWORD",
            "0",
        ),
        # Visual (regedit_sensi.reg)
        _reg_add(
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects",
            "VisualFXSetting",
            "REG_SZ",
            "2",
            hive="HKCU",
        ),
        _reg_add(
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
            "TaskbarAnimations",
            "REG_DWORD",
            "0",
            hive="HKCU",
        ),
        _reg_add(
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
            "DisallowShaking",
            "REG_DWORD",
            "1",
            hive="HKCU",
        ),
        # TCP/IP (regedit_sensi.reg)
        _reg_add(
            r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters",
            "TcpAckFrequency",
            "REG_DWORD",
            "1",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters",
            "TCPNoDelay",
            "REG_DWORD",
            "1",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters",
            "TcpDelAckTicks",
            "REG_DWORD",
            "0",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters",
            "TcpMaxDataRetransmissions",
            "REG_DWORD",
            "10",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters",
            "MaxUserPort",
            "REG_DWORD",
            "65534",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters",
            "DefaultTTL",
            "REG_DWORD",
            "64",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters",
            "TcpTimestamps",
            "REG_DWORD",
            "0",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters",
            "DisableTaskOffload",
            "REG_DWORD",
            "1",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters",
            "Tcp1323Opts",
            "REG_DWORD",
            "0",
        ),
        # DWM (regedit_sensi.reg)
        _reg_add(r"SOFTWARE\Microsoft\Windows\DWM", "Transitions", "REG_DWORD", "0"),
        _reg_add(
            r"SOFTWARE\Microsoft\Windows\DWM",
            "AnimationsShiftKey",
            "REG_DWORD",
            "0",
        ),
        _reg_add(
            r"SOFTWARE\Microsoft\Windows\DWM",
            "ColorizationOpaqueBlend",
            "REG_DWORD",
            "0",
        ),
        _reg_add(
            r"SOFTWARE\Microsoft\Windows\DWM",
            "AlwaysHibernateThumbnails",
            "REG_DWORD",
            "0",
        ),
        _reg_add(r"SOFTWARE\Microsoft\Windows\DWM", "EnableAeroPeek", "REG_DWORD", "0"),
        _reg_add(r"SOFTWARE\Microsoft\Windows\DWM", "Animations", "REG_DWORD", "0"),
        _reg_add(r"SOFTWARE\Microsoft\Windows\DWM", "Composition", "REG_DWORD", "0"),
        # Power (regedit_sensi.reg)
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\Power\PowerThrottling",
            "PowerThrottlingOff",
            "REG_DWORD",
            "1",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Power",
            "CoalescingTimerInterval",
            "REG_DWORD",
            "0",
        ),
        # System (regedit_sensi.reg)
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control",
            "WaitToKillServiceTimeout",
            "REG_DWORD",
            "1000",
        ),
        # Extreme: disable services (INVI XD SENSI.bat)
        _sc_config("SysMain"),
        _sc_stop("SysMain"),
        _sc_config("DiagTrack"),
        _sc_stop("DiagTrack"),
    ],
    # Emulator Overdrive X: tweaks_sensi.bat
    "boost_fps_menu": [
        # Mouse
        _reg_add(r"Control Panel\Mouse", "MouseSpeed", "REG_SZ", "0", hive="HKCU"),
        _reg_add(r"Control Panel\Mouse", "MouseThreshold1", "REG_SZ", "0", hive="HKCU"),
        _reg_add(r"Control Panel\Mouse", "MouseThreshold2", "REG_SZ", "0", hive="HKCU"),
        _reg_add(r"Control Panel\Mouse", "MouseHoverTime", "REG_SZ", "10", hive="HKCU"),
        _reg_add(r"Control Panel\Mouse", "MouseHoverWidth", "REG_SZ", "2", hive="HKCU"),
        _reg_add(r"Control Panel\Mouse", "MouseHoverHeight", "REG_SZ", "2", hive="HKCU"),
        _reg_add(r"Control Panel\Mouse", "DoubleClickWidth", "REG_SZ", "2", hive="HKCU"),
        _reg_add(r"Control Panel\Mouse", "DoubleClickHeight", "REG_SZ", "2", hive="HKCU"),
        _reg_add(
            r"Control Panel\Mouse",
            "ScrollInactiveWindows",
            "REG_SZ",
            "0",
            hive="HKCU",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Services\mouclass\Parameters",
            "MouseDataQueueSize",
            "REG_DWORD",
            "54",
        ),
        _reg_add(r"Control Panel\Desktop", "MouseSensitivity", "REG_SZ", "10", hive="HKCU"),
        # Keyboard
        _reg_add(r"Control Panel\Keyboard", "KeyboardDelay", "REG_SZ", "0", hive="HKCU"),
        _reg_add(r"Control Panel\Keyboard", "KeyboardSpeed", "REG_SZ", "31", hive="HKCU"),
        _reg_add(
            r"Control Panel\Accessibility\StickyKeys",
            "Flags",
            "REG_SZ",
            "58",
            hive="HKCU",
        ),
        _reg_add(
            r"Control Panel\Accessibility\ToggleKeys",
            "Flags",
            "REG_SZ",
            "58",
            hive="HKCU",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Services\kbdclass\Parameters",
            "KeyboardDataQueueSize",
            "REG_DWORD",
            "54",
        ),
        # Performance
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\PriorityControl",
            "Win32PrioritySeparation",
            "REG_DWORD",
            "38",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\PriorityControl",
            "IRQ8Priority",
            "REG_DWORD",
            "1",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\PriorityControl",
            "IRQ16Priority",
            "REG_DWORD",
            "1",
        ),
        _reg_add(r"Control Panel\Desktop", "MenuShowDelay", "REG_SZ", "0", hive="HKCU"),
        _reg_add(r"Control Panel\Desktop", "AutoEndTasks", "REG_SZ", "1", hive="HKCU"),
        _reg_add(
            r"Control Panel\Desktop",
            "ForegroundLockTimeout",
            "REG_DWORD",
            "0",
            hive="HKCU",
        ),
        _reg_add(
            r"Control Panel\Desktop",
            "LowLevelHooksTimeout",
            "REG_DWORD",
            "1000",
            hive="HKCU",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Control\Power\PowerThrottling",
            "PowerThrottlingOff",
            "REG_DWORD",
            "1",
        ),
        # Network
        _reg_add(
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile",
            "NetworkThrottlingIndex",
            "REG_DWORD",
            str(0xFFFFFFFF),
        ),
        _reg_add(
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile",
            "SystemResponsiveness",
            "REG_DWORD",
            "0",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters",
            "TcpAckFrequency",
            "REG_DWORD",
            "1",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters",
            "TCPNoDelay",
            "REG_DWORD",
            "1",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters",
            "TcpDelAckTicks",
            "REG_DWORD",
            "0",
        ),
        _reg_add(
            r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters",
            "MaxUserPort",
            "REG_DWORD",
            "65534",
        ),
        # Service
        _sc_config("SysMain"),
        _sc_stop("SysMain"),
        _sc_config("DiagTrack"),
        _sc_stop("DiagTrack"),
        _reg_add(r"SOFTWARE\Microsoft\Windows\DWM", "Transitions", "REG_DWORD", "0"),
        _reg_add(
            r"SOFTWARE\Microsoft\Windows\DWM",
            "AnimationsShiftKey",
            "REG_DWORD",
            "0",
        ),
        # Kill debug tools
        _run(["taskkill", "/f", "/im", "x64dbg.exe"]),
        _run(["taskkill", "/f", "/im", "ida64.exe"]),
        _run(["taskkill", "/f", "/im", "wireshark.exe"]),
        _run(["taskkill", "/f", "/im", "cheatengine-x86_64.exe"]),
    ],
}


# ── Emulator tweaks (from Viet bat fitur 1 & 3) ────────────────
# Fitur 1: Optimize BlueStacks 5 (BlueStacks_nxt registry)
# Fitur 3: Optimize MSI App Player (BlueStacks_msi2 registry)

EMULATOR_TWEAK_COMMANDS: dict[str, list[TweakStep]] = {
    "emulator.bluestacks5": [
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android",
            "BootParameters",
            "REG_SZ",
            (
                "ROOT=/dev/sda1 SRC=/android DATA=/dev/sdb1 HOST=WIN "
                "bstandroidport=9999 GlMode=1 VERSION=4.280.1.6309 OEM=nxt "
                "LANG=en-US country=VN caCode=704 pcode=custom "
                "OEMFEATURES=539180033 DNS=8.8.8.8 DNS2=10.0.2.3 "
                "GUID=a39928fa-1af4-4d1a-b6c3-692734c6f8fc EngineState=plus "
                "caSelector=se_45202 DPI=240 GlTransport=3 "
                "appsfeatures=16592382 "
                "installId=0bab0217-5abe-4c61-871a-fe1eac3ce2e6 "
                "machineId=a39928fa-1af4-4d1a-b6c3-692734c6f8fc "
                "versionMachineId=e49d8c78-305e-40bb-8002-532f69f9fef0 "
                "ApiToken=f7ce332d-ce3e-4837-8cbc-f4af39d0dbcf ssse3=1 "
                "abivalue=15 virttype=1 WINDOWSFRONTEND=10.0.2.2:2881 "
                "SF=Documents,Pictures,InputMapper,BstSharedFolder "
                "WINDOWSAGENT=10.0.2.2:2861 fps=450"
            ),
        ),
        _reg_add(r"SOFTWARE\BlueStacks_nxt\Guests\Android", "DisableRobustness", "REG_DWORD", "1"),
        _reg_add(r"SOFTWARE\BlueStacks_nxt\Guests\Android", "VirtType", "REG_SZ", "legacy"),
        _reg_add(r"SOFTWARE\BlueStacks_nxt\Guests\Android", "Memory", "REG_DWORD", "1024"),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android", "IsHardwareAstcSupported", "REG_DWORD", "0"
        ),
        _reg_add(r"SOFTWARE\BlueStacks_nxt\Guests\Android", "IsSidebarVisible", "REG_DWORD", "1"),
        _reg_add(r"SOFTWARE\BlueStacks_nxt\Guests\Android\BlockDevice\0", "Name", "REG_SZ", "sda1"),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\BlockDevice\0",
            "Path",
            "REG_SZ",
            r"E:\BlueStacks_nxt\Engine\Android\Root.vdi",
        ),
        _reg_add(r"SOFTWARE\BlueStacks_nxt\Guests\Android\BlockDevice\1", "Name", "REG_SZ", "sdb1"),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\BlockDevice\1",
            "Path",
            "REG_SZ",
            r"E:\BlueStacks_nxt\Engine\Android\Data.vdi",
        ),
        _reg_add(r"SOFTWARE\BlueStacks_nxt\Guests\Android\BlockDevice\2", "Name", "REG_SZ", "sdc1"),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\BlockDevice\2",
            "Path",
            "REG_SZ",
            r"E:\BlueStacks_nxt\Engine\Android\SDCard.vdi",
        ),
        _reg_add(r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config", "VCPUs", "REG_DWORD", "2"),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config", "GlRendermode", "REG_DWORD", "1"
        ),
        _reg_add(r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config", "GlMode", "REG_DWORD", "1"),
        _reg_add(r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config", "Camera", "REG_DWORD", "1"),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config", "ConfigSynced", "REG_DWORD", "1"
        ),
        _reg_add(r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config", "HScroll", "REG_DWORD", "1"),
        _reg_add(r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config", "GpsMode", "REG_DWORD", "1"),
        _reg_add(r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config", "FileSystem", "REG_DWORD", "1"),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config", "StopZygoteOnClose", "REG_DWORD", "0"
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config", "FenceSyncType", "REG_DWORD", "1"
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config", "FrontendNoClose", "REG_DWORD", "0"
        ),
        _reg_add(r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config", "GpsSource", "REG_DWORD", "0"),
        _reg_add(r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config", "GpsLatitude", "REG_SZ", ""),
        _reg_add(r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config", "GpsLongitude", "REG_SZ", ""),
        _reg_add(r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config", "GlPort", "REG_DWORD", "3901"),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config", "HostSensorPort", "REG_DWORD", "2921"
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config",
            "SoftControlBarHeightLandscape",
            "REG_DWORD",
            "0",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config",
            "SoftControlBarHeightPortrait",
            "REG_DWORD",
            "0",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config", "GrabKeyboard", "REG_DWORD", "0"
        ),
        _reg_add(r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config", "DisableDWM", "REG_DWORD", "0"),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config", "DisablePcIme", "REG_DWORD", "0"
        ),
        _reg_add(r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config", "EnableBSTVC", "REG_DWORD", "0"),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config", "IsGoogleSigninDone", "REG_DWORD", "0"
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config", "ForceVMLegacyMode", "REG_DWORD", "1"
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config",
            "FrontendServerPort",
            "REG_DWORD",
            "2881",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config", "BstAndroidPort", "REG_DWORD", "9999"
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config",
            "TriggerMemoryTrimThreshold",
            "REG_DWORD",
            "700",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config",
            "TriggerMemoryTrimTimerInterval",
            "REG_DWORD",
            "60000",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config", "BstAdbPort", "REG_DWORD", "5555"
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config",
            "HostForwardSensorPort",
            "REG_DWORD",
            "12000",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config", "GPSAvailable", "REG_DWORD", "0"
        ),
        _reg_add(r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config", "Locale", "REG_SZ", "en-US"),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config",
            "ImeSelected",
            "REG_SZ",
            "com.android.inputmethod.latin/.LatinIME",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config", "IsOneTimeSetupDone", "REG_DWORD", "1"
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config", "LastBootDate", "REG_SZ", "2/4/2022"
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config",
            "DisplayName",
            "REG_SZ",
            "Bluestacks App Player",
        ),
        _reg_add(r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config", "Volume", "REG_DWORD", "100"),
        _reg_add(r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config", "IsMuted", "REG_DWORD", "0"),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config",
            "IsGoogleSigninPopupShown",
            "REG_DWORD",
            "1",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config",
            "BstVmAId",
            "REG_SZ",
            "NjcwN2U4ZWEtZTE5OS00YTA1LWI4MTMtZTIwMDg4MjYwMjll",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config",
            "BstVmId",
            "REG_SZ",
            "NDk0NWIxNDE3ZTk4NWQwMA==",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config",
            "WindowPlacement",
            "REG_SZ",
            (
                '<?xml version="1.0" encoding="utf-8"?>'
                '<WINDOWPLACEMENT xmlns:xsd="http://www.w3.org/2001/XMLSchema" '
                'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
                "<length>44</length><flags>0</flags><showCmd>1</showCmd>"
                "<minPosition><X>-32000</X><Y>-32000</Y></minPosition>"
                "<maxPosition><X>-1</X><Y>-1</Y></maxPosition>"
                "<normalPosition><Left>91</Left><Top>33</Top>"
                "<Right>1177</Right><Bottom>651</Bottom></normalPosition>"
                "</WINDOWPLACEMENT>"
            ),
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config", "EnableHighFPS", "REG_DWORD", "1"
        ),
        _reg_add(r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config", "ShowFPS", "REG_DWORD", "1"),
        _reg_add(r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config", "FPS", "REG_DWORD", "450"),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config",
            "ShowSchemeDeletePopup",
            "REG_DWORD",
            "0",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config",
            "ShowBlueHighlighter",
            "REG_DWORD",
            "0",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config",
            "ShowMacroDeletePopup",
            "REG_DWORD",
            "0",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\Config",
            "LastNotificationEnabledAppLaunched",
            "REG_SZ",
            "com.dts.freefireth",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\FrameBuffer\0", "Depth", "REG_DWORD", "16"
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\FrameBuffer\0",
            "HideBootProgress",
            "REG_DWORD",
            "1",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\FrameBuffer\0",
            "WindowWidth",
            "REG_DWORD",
            "1072",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\FrameBuffer\0",
            "WindowHeight",
            "REG_DWORD",
            "603",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\FrameBuffer\0",
            "GuestWidth",
            "REG_DWORD",
            "960",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\FrameBuffer\0",
            "GuestHeight",
            "REG_DWORD",
            "540",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\Network\0",
            "InboundRules",
            "REG_MULTI_SZ",
            r"tcp:5555:5555\0tcp:6666:6666\0tcp:7777:7777\0tcp:9999:9999\0udp:12000:12000",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\Network\Redirect",
            "tcp/5555",
            "REG_DWORD",
            "5555",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\Network\Redirect",
            "tcp/6666",
            "REG_DWORD",
            "6666",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\Network\Redirect",
            "tcp/7777",
            "REG_DWORD",
            "7777",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\Network\Redirect",
            "tcp/9999",
            "REG_DWORD",
            "9999",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\Network\Redirect",
            "udp/12000",
            "REG_DWORD",
            "12000",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\SharedFolder\0",
            "Name",
            "REG_SZ",
            "BstSharedFolder",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\SharedFolder\0",
            "Path",
            "REG_SZ",
            r"E:\BlueStacks_nxt\Engine\UserData\SharedFolder\\",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\SharedFolder\0", "Writable", "REG_DWORD", "1"
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\SharedFolder\1", "Name", "REG_SZ", "Pictures"
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\SharedFolder\1",
            "Path",
            "REG_SZ",
            r"C:\Users\ADMIN\Pictures",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\SharedFolder\1", "Writable", "REG_DWORD", "1"
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\SharedFolder\2",
            "Name",
            "REG_SZ",
            "PublicPictures",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\SharedFolder\2",
            "Path",
            "REG_SZ",
            r"C:\Users\Public\Pictures",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\SharedFolder\2", "Writable", "REG_DWORD", "1"
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\SharedFolder\3",
            "Name",
            "REG_SZ",
            "Documents",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\SharedFolder\3",
            "Path",
            "REG_SZ",
            r"C:\Users\ADMIN\Documents",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\SharedFolder\3", "Writable", "REG_DWORD", "1"
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\SharedFolder\4",
            "Name",
            "REG_SZ",
            "PublicDocuments",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\SharedFolder\4",
            "Path",
            "REG_SZ",
            r"C:\Users\Public\Documents",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\SharedFolder\4", "Writable", "REG_DWORD", "1"
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\SharedFolder\5",
            "Name",
            "REG_SZ",
            "InputMapper",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\SharedFolder\5",
            "Path",
            "REG_SZ",
            r"E:\BlueStacks_nxt\Engine\UserData\InputMapper",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_nxt\Guests\Android\SharedFolder\5", "Writable", "REG_DWORD", "1"
        ),
    ],
    "emulator.msi_app_player": [
        _reg_add(r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config", "VCPUs", "REG_DWORD", "4"),
        _reg_add(
            r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config", "GlRendermode", "REG_DWORD", "1"
        ),
        _reg_add(r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config", "GlMode", "REG_DWORD", "1"),
        _reg_add(r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config", "Camera", "REG_DWORD", "1"),
        _reg_add(
            r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config", "ConfigSynced", "REG_DWORD", "1"
        ),
        _reg_add(r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config", "HScroll", "REG_DWORD", "1"),
        _reg_add(r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config", "GpsMode", "REG_DWORD", "1"),
        _reg_add(r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config", "FileSystem", "REG_DWORD", "1"),
        _reg_add(
            r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config", "StopZygoteOnClose", "REG_DWORD", "0"
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config", "FenceSyncType", "REG_DWORD", "1"
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config", "FrontendNoClose", "REG_DWORD", "0"
        ),
        _reg_add(r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config", "GpsSource", "REG_DWORD", "0"),
        _reg_add(r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config", "GpsLatitude", "REG_SZ", ""),
        _reg_add(r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config", "GpsLongitude", "REG_SZ", ""),
        _reg_add(r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config", "GlPort", "REG_DWORD", "3901"),
        _reg_add(
            r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config", "HostSensorPort", "REG_DWORD", "2921"
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config",
            "SoftControlBarHeightLandscape",
            "REG_DWORD",
            "0",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config",
            "SoftControlBarHeightPortrait",
            "REG_DWORD",
            "0",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config", "GrabKeyboard", "REG_DWORD", "0"
        ),
        _reg_add(r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config", "DisableDWM", "REG_DWORD", "0"),
        _reg_add(
            r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config", "DisablePcIme", "REG_DWORD", "0"
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config", "EnableBSTVC", "REG_DWORD", "0"
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config",
            "IsGoogleSigninDone",
            "REG_DWORD",
            "1",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config", "ForceVMLegacyMode", "REG_DWORD", "1"
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config",
            "FrontendServerPort",
            "REG_DWORD",
            "2881",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config", "BstAndroidPort", "REG_DWORD", "9999"
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config",
            "TriggerMemoryTrimThreshold",
            "REG_DWORD",
            "700",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config",
            "TriggerMemoryTrimTimerInterval",
            "REG_DWORD",
            "60000",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config", "GPSAvailable", "REG_DWORD", "0"
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config", "BstAdbPort", "REG_DWORD", "5555"
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config",
            "HostForwardSensorPort",
            "REG_DWORD",
            "12000",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config",
            "ImeSelected",
            "REG_SZ",
            "com.android.inputmethod.latin/.LatinIME",
        ),
        _reg_add(r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config", "Locale", "REG_SZ", "en-US"),
        _reg_add(
            r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config", "DisplayName", "REG_SZ", "App Player"
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config",
            "LastBootDate",
            "REG_SZ",
            "17/01/2022",
        ),
        _reg_add(r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config", "Volume", "REG_DWORD", "100"),
        _reg_add(r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config", "IsMuted", "REG_DWORD", "0"),
        _reg_add(
            r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config",
            "IsGoogleSigninPopupShown",
            "REG_DWORD",
            "1",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config",
            "BstVmAId",
            "REG_SZ",
            "NmJlMTlkOGMtZDQxZi00ODRkLWI1NjMtYWM1ZmM5NmNjNGQ2",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config",
            "BstVmId",
            "REG_SZ",
            "M2VkYjE5ZWVkZGYwZGYwMA==",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config",
            "WindowPlacement",
            "REG_SZ",
            (
                '<?xml version="1.0" encoding="utf-8"?>'
                '<WINDOWPLACEMENT xmlns:xsd="http://www.w3.org/2001/XMLSchema" '
                'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
                "<length>44</length><flags>0</flags><showCmd>1</showCmd>"
                "<minPosition><X>-1</X><Y>-1</Y></minPosition>"
                "<maxPosition><X>-1</X><Y>-1</Y></maxPosition>"
                "<normalPosition><Left>97</Left><Top>80</Top>"
                "<Right>1167</Right><Bottom>689</Bottom></normalPosition>"
                "</WINDOWPLACEMENT>"
            ),
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config", "EnableHighFPS", "REG_DWORD", "1"
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config", "EnableVSync", "REG_DWORD", "0"
        ),
        _reg_add(r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config", "ShowFPS", "REG_DWORD", "1"),
        _reg_add(r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config", "FPS", "REG_DWORD", "450"),
        _reg_add(
            r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config",
            "LastNotificationEnabledAppLaunched",
            "REG_SZ",
            "com.dts.freefireth",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config",
            "NotificationModePopupShownCount",
            "REG_DWORD",
            "3",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config",
            "IsMinimizeSelectedOnReceiveGameNotificationPopup",
            "REG_DWORD",
            "0",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config",
            "RunAppProcessId",
            "REG_DWORD",
            "3512",
        ),
        _reg_add(
            r"SOFTWARE\BlueStacks_msi2\Guests\Android\Config",
            "ShowSchemeDeletePopup",
            "REG_DWORD",
            "1",
        ),
    ],
}


# ── Fixes tweaks (from fix camera bat + fix obs bat) ────────────

FIXES_TWEAK_COMMANDS: dict[str, list[TweakStep]] = {
    "fixes.camera": [
        _sc_config("FrameServer", "auto"),
        _sc_config("FrameServerMonitor", "auto"),
        _sc_config("camsvc", "auto"),
        _sc_config("SensorService", "auto"),
        _run(["net", "start", "FrameServer"]),
        _run(["net", "start", "camsvc"]),
        _run(["net", "start", "SensorService"]),
        _reg_add(
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam",
            "Value",
            "REG_SZ",
            "Allow",
        ),
        _reg_add(
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam",
            "Value",
            "REG_SZ",
            "Allow",
            hive="HKCU",
        ),
        _reg_add(
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager"
            r"\ConsentStore\webcam\NonPackaged",
            "Value",
            "REG_SZ",
            "Allow",
        ),
        _run(
            [
                "powershell",
                "-Command",
                "Get-AppxPackage *WindowsCamera* | Reset-AppxPackage",
            ]
        ),
    ],
    "fixes.obs_screenshot": [
        _reg_add(r"SYSTEM\CurrentControlSet\Services\CaptureService", "Start", "REG_DWORD", "3"),
        _reg_add(r"System\GameConfigStore", "GameDVR_Enabled", "REG_DWORD", "1", hive="HKCU"),
        _reg_add(r"System\GameConfigStore", "GameDVR_FSEBehavior", "REG_DWORD", "0", hive="HKCU"),
        _reg_add(
            r"System\GameConfigStore",
            "GameDVR_HonorUserFSEBehaviorMode",
            "REG_DWORD",
            "1",
            hive="HKCU",
        ),
        _reg_add(
            r"System\GameConfigStore",
            "GameDVR_DXGIHonorFSEWindowsCompatible",
            "REG_DWORD",
            "1",
            hive="HKCU",
        ),
        _reg_add(r"SYSTEM\CurrentControlSet\Services\XboxNetApiSvc", "Start", "REG_DWORD", "3"),
        _reg_add(r"SYSTEM\CurrentControlSet\Services\XblGameSave", "Start", "REG_DWORD", "3"),
        _reg_add(r"SYSTEM\CurrentControlSet\Services\XblAuthManager", "Start", "REG_DWORD", "3"),
        _reg_add(
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\SnippingTool.exe",
            "",
            "REG_SZ",
            "",
        ),
        _run(["taskkill", "/f", "/im", "explorer.exe"]),
        _run(["explorer.exe"]),
    ],
}


def _run_step(step: TweakStep) -> dict[str, Any]:
    if sys.platform != "win32":
        return {
            "description": step.description,
            "success": False,
            "error": "Tweak hanya berjalan di Windows.",
        }
    try:
        resolved = _resolve_command(step.command)
        result = subprocess.run(  # noqa: S603 -- trusted local commands; env vars expanded, CMD internals wrapped.
            resolved,
            capture_output=True,
            text=True,
            timeout=30,
            shell=False,
        )
        ok = result.returncode == 0
        return {
            "description": step.description,
            "success": ok,
            "stdout": result.stdout.strip()[:500] if result.stdout else "",
            "stderr": result.stderr.strip()[:500] if result.stderr else "",
            "requires_admin": step.requires_admin,
        }
    except (OSError, subprocess.SubprocessError) as exc:
        return {
            "description": step.description,
            "success": False,
            "error": str(exc),
            "requires_admin": step.requires_admin,
        }


def execute_tweak(tweak_id: str, title: str) -> TweakResult:
    steps_def = (
        ADVANCED_TWEAK_COMMANDS.get(tweak_id)
        or TWEAK_MENU_COMMANDS.get(tweak_id)
        or GAMING_TWEAK_COMMANDS.get(tweak_id)
        or EMULATOR_TWEAK_COMMANDS.get(tweak_id)
        or FIXES_TWEAK_COMMANDS.get(tweak_id)
    )
    if not steps_def:
        raise ValueError(f"Tweak {tweak_id} tidak memiliki definisi operasi.")
    result = TweakResult(tweak_id=tweak_id, title=title, success=True)
    for step in steps_def:
        outcome = _run_step(step)
        result.steps.append(outcome)
        if outcome["success"]:
            result.applied += 1
        else:
            result.failed += 1
            result.success = False
    if result.applied == 0 and result.failed > 0:
        result.message = (
            f"{title}: semua operasi gagal. "
            "Jalankan aplikasi sebagai Administrator untuk tweak HKLM/service. "
            "Pada Windows custom (AtlasOS/ReviOS/Ghost Spectre/dll.) beberapa "
            "service mungkin sudah dihapus sehingga tweak terkait tidak bisa "
            "diterapkan."
        )
        result.success = False
    elif result.failed > 0:
        result.message = (
            f"{title}: {result.applied} operasi berhasil, {result.failed} gagal "
            "(kemungkinan butuh hak Administrator, atau service/target sudah "
            "dihapus pada Windows custom)."
        )
    else:
        result.message = f"{title}: {result.applied} operasi berhasil diterapkan."
    return result


def result_to_dict(result: TweakResult) -> dict[str, Any]:
    return {
        "tweak_id": result.tweak_id,
        "title": result.title,
        "success": result.success,
        "applied": result.applied,
        "failed": result.failed,
        "steps": result.steps,
        "message": result.message,
    }
