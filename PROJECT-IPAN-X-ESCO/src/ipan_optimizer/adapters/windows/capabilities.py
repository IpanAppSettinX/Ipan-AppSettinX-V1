from __future__ import annotations

import json
import os
import platform
import sys
from typing import Any

import psutil

from ipan_optimizer.adapters.windows.common import run_fixed_command
from ipan_optimizer.adapters.windows.power import PowerReadAdapter
from ipan_optimizer.domain.models import (
    Capability,
    CapabilityState,
    EvidenceRef,
    MachineCapabilityVector,
)
from ipan_optimizer.domain.resources import calculate_resource_budget


def _capability(
    key: str,
    value: Any,
    reason: str,
    *,
    state: CapabilityState = CapabilityState.AVAILABLE,
    source: str = "local-detection",
) -> Capability:
    return Capability(
        key=key,
        state=state,
        value=value,
        reason=reason,
        evidence=[EvidenceRef(source=source, detail=reason)],
    )


def _detect_gpus() -> Capability:
    if sys.platform != "win32":
        return _capability(
            "gpu.adapters",
            None,
            "Deteksi GPU Windows tidak tersedia pada platform ini.",
            state=CapabilityState.UNSUPPORTED,
        )
    command = [
        "powershell.exe",
        "-NoProfile",
        "-NonInteractive",
        "-Command",
        (
            "Get-CimInstance Win32_VideoController | "
            "Select-Object Name,DriverVersion,AdapterRAM,PNPDeviceID | "
            "ConvertTo-Json -Compress"
        ),
    ]
    try:
        output = run_fixed_command(command, timeout=12)
        parsed = json.loads(output) if output else []
        adapters = parsed if isinstance(parsed, list) else [parsed]
        safe = [
            {
                "name": str(item.get("Name", "Tidak diketahui")),
                "driver_version": str(item.get("DriverVersion", "")),
                "adapter_ram": item.get("AdapterRAM"),
                "pnp_device_id": str(item.get("PNPDeviceID", "")),
            }
            for item in adapters
            if isinstance(item, dict)
        ]
        return _capability("gpu.adapters", safe, "GPU dibaca melalui CIM read-only.")
    except (RuntimeError, json.JSONDecodeError, OSError) as exc:
        return _capability(
            "gpu.adapters",
            None,
            f"GPU tidak dapat dibaca: {type(exc).__name__}.",
            state=CapabilityState.UNKNOWN,
        )


def _detect_webview2() -> Capability:
    if sys.platform != "win32":
        return _capability(
            "webview2.runtime",
            None,
            "WebView2 hanya berlaku pada Windows.",
            state=CapabilityState.UNSUPPORTED,
        )
    try:
        import winreg

        from ipan_optimizer.app.webview2_runtime import (
            WEBVIEW2_MACHINE_KEY,
            WEBVIEW2_USER_KEY,
            is_webview2_installed,
        )

        def _reader(hive: int, key_path: str, view: int) -> str | None:
            try:
                with winreg.OpenKey(hive, key_path, 0, winreg.KEY_QUERY_VALUE | view) as key:
                    value, _ = winreg.QueryValueEx(key, "pv")
                    return str(value)
            except FileNotFoundError:
                return None
            except OSError:
                return None

        installed = is_webview2_installed(reader=_reader)
        if installed:
            machine_pv = _reader(
                winreg.HKEY_LOCAL_MACHINE, WEBVIEW2_MACHINE_KEY, winreg.KEY_WOW64_32KEY
            )
            user_pv = _reader(winreg.HKEY_CURRENT_USER, WEBVIEW2_USER_KEY, 0)
            version = machine_pv or user_pv or ""
            return _capability(
                "webview2.runtime",
                version,
                "WebView2 Evergreen terdeteksi melalui EdgeUpdate.",
            )
    except OSError as exc:
        return _capability(
            "webview2.runtime",
            None,
            f"Pemeriksaan WebView2 gagal: {type(exc).__name__}.",
            state=CapabilityState.ERROR,
        )
    return _capability(
        "webview2.runtime",
        None,
        "WebView2 Evergreen tidak terdeteksi.",
        state=CapabilityState.UNAVAILABLE,
    )


class WindowsCapabilityScanner:
    def scan(self) -> MachineCapabilityVector:
        memory = psutil.virtual_memory()
        logical = psutil.cpu_count(logical=True) or 1
        physical = psutil.cpu_count(logical=False)
        system_drive = os.environ.get("SYSTEMDRIVE", "C:") + "\\"
        try:
            disk = psutil.disk_usage(system_drive if sys.platform == "win32" else "/")
            disk_value: Any = {
                "path": system_drive if sys.platform == "win32" else "/",
                "total_bytes": disk.total,
                "free_bytes": disk.free,
                "percent": disk.percent,
            }
            disk_state = CapabilityState.AVAILABLE
            disk_reason = "Kapasitas volume sistem dibaca melalui psutil."
        except OSError as exc:
            disk_value = None
            disk_state = CapabilityState.ERROR
            disk_reason = f"Volume sistem tidak dapat dibaca: {type(exc).__name__}."

        items = {
            "os.platform": _capability(
                "os.platform",
                platform.platform(),
                "Platform dibaca dari runtime Python.",
            ),
            "os.architecture": _capability(
                "os.architecture",
                platform.machine(),
                "Arsitektur proses dibaca dari runtime Python.",
            ),
            "os.windows_supported": _capability(
                "os.windows_supported",
                sys.platform == "win32" and platform.machine().upper() in {"AMD64", "X86_64"},
                "V1 mutation support memerlukan Windows x64.",
                state=(
                    CapabilityState.AVAILABLE
                    if sys.platform == "win32"
                    else CapabilityState.UNSUPPORTED
                ),
            ),
            "cpu.vendor_model": _capability(
                "cpu.vendor_model",
                platform.processor() or "Tidak diketahui",
                "Identitas CPU bersifat diagnostik dan bukan preset.",
            ),
            "cpu.logical_processors": _capability(
                "cpu.logical_processors",
                logical,
                "Logical processor dibaca melalui psutil.",
            ),
            "cpu.physical_cores": _capability(
                "cpu.physical_cores",
                physical,
                (
                    "Physical core dibaca melalui psutil."
                    if physical
                    else "Physical core tidak dapat dipercaya."
                ),
                state=CapabilityState.AVAILABLE if physical else CapabilityState.UNKNOWN,
            ),
            "memory.total_mb": _capability(
                "memory.total_mb",
                memory.total // (1024 * 1024),
                "Total RAM dibaca melalui psutil.",
            ),
            "memory.available_mb": _capability(
                "memory.available_mb",
                memory.available // (1024 * 1024),
                "Available RAM dibaca melalui psutil.",
            ),
            "memory.pressure_percent": _capability(
                "memory.pressure_percent",
                memory.percent,
                "Memory pressure dibaca melalui psutil.",
            ),
            "storage.system": _capability(
                "storage.system",
                disk_value,
                disk_reason,
                state=disk_state,
            ),
            "gpu.adapters": _detect_gpus(),
            "webview2.runtime": _detect_webview2(),
        }
        budget = calculate_resource_budget(
            total_ram_mb=memory.total // (1024 * 1024),
            available_ram_mb=memory.available // (1024 * 1024),
            logical_processors=logical,
            physical_cores=physical,
            physical_cores_trustworthy=physical is not None,
        )
        items["emulator.resource_budget"] = _capability(
            "emulator.resource_budget",
            budget.model_dump(mode="json"),
            "Safe cap dihitung dari headroom host saat pemindaian.",
        )
        battery = psutil.sensors_battery()
        items["power.source"] = _capability(
            "power.source",
            ("AC" if battery is None or battery.power_plugged else "battery"),
            (
                "Tidak ada baterai terdeteksi atau perangkat memakai AC."
                if battery is None
                else "Status daya dibaca melalui psutil."
            ),
        )
        try:
            active_scheme = PowerReadAdapter().active_scheme()
            items["power.active_scheme"] = _capability(
                "power.active_scheme",
                active_scheme,
                (
                    "Power scheme aktif dibaca melalui powercfg."
                    if active_scheme
                    else "Power scheme aktif tidak tersedia."
                ),
                state=CapabilityState.AVAILABLE if active_scheme else CapabilityState.UNKNOWN,
            )
        except (RuntimeError, OSError):
            items["power.active_scheme"] = _capability(
                "power.active_scheme",
                None,
                "Power scheme aktif tidak dapat dibaca.",
                state=CapabilityState.ERROR,
            )
        warnings: list[str] = []
        if sys.platform == "win32" and platform.release() == "10":
            warnings.append("Dukungan reguler Windows 10 berakhir pada 14 Oktober 2025.")
        if platform.machine().upper() == "ARM64":
            warnings.append("Windows on ARM64 bersifat read-only pada versi ini.")
        return MachineCapabilityVector(capabilities=items, warnings=warnings)
