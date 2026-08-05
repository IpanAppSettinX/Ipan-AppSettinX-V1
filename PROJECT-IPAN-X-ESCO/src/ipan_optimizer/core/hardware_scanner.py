from __future__ import annotations

import platform
import subprocess
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class CpuInfo:
    brand: str = "Unknown"
    model: str = "Unknown"
    cores: int = 0
    threads: int = 0
    base_speed_ghz: float = 0.0
    max_speed_ghz: float = 0.0


@dataclass(frozen=True)
class GpuInfo:
    brand: str = "Unknown"
    model: str = "Unknown"
    vram_mb: int = 0
    driver_version: str = "Unknown"


@dataclass(frozen=True)
class RamModule:
    manufacturer: str = "Unknown"
    capacity_mb: int = 0
    speed_mhz: int = 0
    ddr_type: str = "Unknown"


@dataclass(frozen=True)
class RamInfo:
    total_mb: int = 0
    modules: tuple[RamModule, ...] = ()
    max_speed_mhz: int = 0
    ddr_type: str = "Unknown"


@dataclass(frozen=True)
class StorageDevice:
    device_type: str = "Unknown"
    brand: str = "Unknown"
    model: str = "Unknown"
    capacity_gb: float = 0.0
    interface_type: str = "Unknown"


@dataclass(frozen=True)
class NetworkInfo:
    adapter_name: str = "Unknown"
    link_speed_mbps: int = 0


@dataclass(frozen=True)
class WindowsInfo:
    version: str = "Unknown"
    build_number: str = "Unknown"
    edition: str = "Unknown"
    display_version: str = "Unknown"
    product_name: str = "Unknown"


@dataclass
class HardwareScanResult:
    cpu: CpuInfo = field(default_factory=CpuInfo)
    gpu: list[GpuInfo] = field(default_factory=list)
    ram: RamInfo = field(default_factory=RamInfo)
    storage: list[StorageDevice] = field(default_factory=list)
    network: list[NetworkInfo] = field(default_factory=list)
    windows: WindowsInfo = field(default_factory=WindowsInfo)

    def as_payload(self) -> dict[str, object]:
        result = asdict(self)
        return result


def _run_wmic(alias: str, fields: list[str]) -> list[dict[str, str]]:
    """Run a wmic query and return parsed rows."""
    try:
        cmd = ["wmic", alias, "get", ",".join(fields), "/format:csv"]
        output = subprocess.check_output(  # noqa: S603
            cmd,
            text=True,
            timeout=10,
            creationflags=0x08000000,
        )
        lines = [line.strip() for line in output.strip().splitlines() if line.strip()]
        if len(lines) < 2:
            return []
        headers = [h.strip().lower() for h in lines[0].split(",")]
        rows: list[dict[str, str]] = []
        for line in lines[1:]:
            values = line.split(",")
            if len(values) >= len(headers):
                row = dict(zip(headers, values, strict=False))
                rows.append(row)
        return rows
    except Exception:
        return []


def _run_powershell(script: str) -> str:
    """Run a PowerShell snippet and return stdout."""
    try:
        result = subprocess.check_output(  # noqa: S603
            ["powershell", "-NoProfile", "-Command", script],  # noqa: S607
            text=True,
            timeout=15,
            creationflags=0x08000000,
        )
        return result.strip()
    except Exception:
        return ""


# Cached batch result: one powershell call for GPU+storage+network+windows.
# Each standalone powershell call costs ~1.5-2 s on Windows; batching four
# queries into one drops total latency from ~8 s to ~2 s.
_BATCH_CACHE: dict[str, Any] | None = None


def _run_batch_wmi() -> dict[str, Any]:
    """Query CPU, GPU, storage, and network via WMI COM (no subprocess).

    Uses ``win32com`` to talk to the WMI service directly. This avoids the
    ~1.5 s PowerShell startup cost per call. Falls back to a single batched
    PowerShell script if COM init fails.
    """
    global _BATCH_CACHE
    if _BATCH_CACHE is not None:
        return _BATCH_CACHE

    # Primary path: WMI COM (instant, no subprocess).
    result: dict[str, Any] = {"cpu": [], "gpu": [], "storage": [], "net": []}
    try:
        import contextlib

        import win32com.client  # type: ignore[import-untyped]

        locator = win32com.client.Dispatch("WbemScripting.SWbemLocator")
        with contextlib.suppress(Exception):
            wmi = locator.ConnectServer(".", "root\\cimv2")
            cpu_set = wmi.ExecQuery(
                "Select Name,Manufacturer,NumberOfCores,NumberOfLogicalProcessors,"
                "MaxClockSpeed from Win32_Processor"
            )
            result["cpu"] = [
                {
                    "Name": item.Name,
                    "Manufacturer": getattr(item, "Manufacturer", "Unknown"),
                    "NumberOfCores": getattr(item, "NumberOfCores", 0),
                    "NumberOfLogicalProcessors": getattr(item, "NumberOfLogicalProcessors", 0),
                    "MaxClockSpeed": getattr(item, "MaxClockSpeed", 0),
                }
                for item in cpu_set
            ]
        with contextlib.suppress(Exception):
            wmi = locator.ConnectServer(".", "root\\cimv2")
            gpu_set = wmi.ExecQuery(
                "Select Name,DriverVersion,AdapterRAM,PNPDeviceID from Win32_VideoController"
            )
            result["gpu"] = [
                {
                    "Name": item.Name,
                    "DriverVersion": item.DriverVersion,
                    "AdapterRAM": item.AdapterRAM,
                    "PNPDeviceID": getattr(item, "PNPDeviceID", ""),
                }
                for item in gpu_set
            ]
        with contextlib.suppress(Exception):
            wmi = locator.ConnectServer(".", "root\\Microsoft\\Windows\\Storage")
            storage_set = wmi.ExecQuery(
                "Select FriendlyName,MediaType,Size,BusType,Manufacturer from MSFT_PhysicalDisk"
            )
            result["storage"] = [
                {
                    "FriendlyName": getattr(item, "FriendlyName", "Unknown"),
                    "MediaType": getattr(item, "MediaType", "Unknown"),
                    "Size": getattr(item, "Size", 0),
                    "BusType": getattr(item, "BusType", "Unknown"),
                    "Manufacturer": getattr(item, "Manufacturer", "Unknown"),
                }
                for item in storage_set
            ]
        with contextlib.suppress(Exception):
            wmi = locator.ConnectServer(".", "root\\cimv2")
            net_set = wmi.ExecQuery(
                "Select Name,Speed from Win32_NetworkAdapter Where NetEnabled=True"
            )
            result["net"] = [
                {
                    "Name": getattr(item, "Name", "Unknown"),
                    "Speed": getattr(item, "Speed", 0),
                }
                for item in net_set
            ]
        _BATCH_CACHE = result
        return _BATCH_CACHE
    except Exception:
        return _run_batch_wmi_powershell()


def _run_batch_wmi_powershell() -> dict[str, Any]:
    """Fallback: batched PowerShell (slower, ~3-4 s)."""
    global _BATCH_CACHE
    import json

    script = (
        "$cpu = @(Get-CimInstance Win32_Processor | "
        "Select-Object Name,Manufacturer,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed); "
        "$gpu = @(Get-CimInstance Win32_VideoController | "
        "Select-Object Name,DriverVersion,AdapterRAM,PNPDeviceID); "
        "$storage = @(Get-PhysicalDisk | "
        "Select-Object FriendlyName,MediaType,Size,BusType,Manufacturer); "
        "$net = @(Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | "
        "Select-Object Name,LinkSpeed); "
        "[ordered]@{cpu=$cpu;gpu=$gpu;storage=$storage;net=$net} "
        "| ConvertTo-Json -Compress -Depth 4"
    )
    output = _run_powershell(script)
    if not output:
        _BATCH_CACHE = {"cpu": [], "gpu": [], "storage": [], "net": []}
        return _BATCH_CACHE
    try:
        parsed = json.loads(output)
        _BATCH_CACHE = {
            "cpu": parsed.get("cpu") or [],
            "gpu": parsed.get("gpu") or [],
            "storage": parsed.get("storage") or [],
            "net": parsed.get("net") or [],
        }
    except (json.JSONDecodeError, TypeError):
        _BATCH_CACHE = {"cpu": [], "gpu": [], "storage": [], "net": []}
    return _BATCH_CACHE


def _safe_int(value: str, default: int = 0) -> int:
    try:
        return int(value.strip())
    except (ValueError, AttributeError):
        return default


def _safe_float(value: str, default: float = 0.0) -> float:
    try:
        return float(value.strip())
    except (ValueError, AttributeError):
        return default


def _detect_cpu() -> CpuInfo:
    # Fast path: batch WMI gives the real marketing name (e.g. "AMD Ryzen 5
    # 5500") and core/thread counts without spawning a subprocess.
    import contextlib

    with contextlib.suppress(Exception):
        import psutil

        batch = _run_batch_wmi()
        cpu_rows = batch.get("cpu")
        cpu_rows = cpu_rows if isinstance(cpu_rows, list) else []
        name = "Unknown"
        manufacturer = "Unknown"
        wmi_cores = 0
        wmi_threads = 0
        max_mhz = 0
        for row in cpu_rows:
            if not isinstance(row, dict):
                continue
            candidate = str(row.get("Name", "")).strip()
            if candidate:
                name = candidate
            manufacturer = str(row.get("Manufacturer", "")).strip() or manufacturer
            wmi_cores = _safe_int(str(row.get("NumberOfCores", "0")))
            wmi_threads = _safe_int(str(row.get("NumberOfLogicalProcessors", "0")))
            max_mhz = _safe_int(str(row.get("MaxClockSpeed", "0")))
            break

        lowered = f"{name} {manufacturer}".lower()
        if "intel" in lowered:
            brand = "Intel"
        elif "amd" in lowered:
            brand = "AMD"
        elif name != "Unknown":
            brand = name.split()[0].strip() or "Unknown"
        else:
            brand = "Unknown"

        # Clock: psutil is instant; fall back to WMI MaxClockSpeed.
        freq = psutil.cpu_freq()
        base_ghz = round(freq.current / 1000, 2) if freq else 0.0
        max_ghz = round(freq.max / 1000, 2) if freq and freq.max > 0 else round(max_mhz / 1000, 2)
        cores = wmi_cores or (psutil.cpu_count(logical=False) or 0)
        threads = wmi_threads or (psutil.cpu_count(logical=True) or 0)
        return CpuInfo(
            brand=brand,
            model=name,
            cores=cores,
            threads=threads,
            base_speed_ghz=base_ghz,
            max_speed_ghz=max_ghz,
        )

    # Fallback: psutil + platform.processor() (CPUID string, less friendly).
    with contextlib.suppress(Exception):
        import psutil

        freq = psutil.cpu_freq()
        base_ghz = round(freq.current / 1000, 2) if freq else 0.0
        max_ghz = round(freq.max / 1000, 2) if freq and freq.max > 0 else base_ghz
        name = platform.processor() or "Unknown"
        lowered_name = name.lower()
        if "intel" in lowered_name:
            brand = "Intel"
        elif "amd" in lowered_name:
            brand = "AMD"
        else:
            brand = "Unknown"
        return CpuInfo(
            brand=brand,
            model=name,
            cores=psutil.cpu_count(logical=False) or 0,
            threads=psutil.cpu_count(logical=True) or 0,
            base_speed_ghz=base_ghz,
            max_speed_ghz=max_ghz,
        )

    # Last resort: wmic (slower, ~1-3 s).
    rows = _run_wmic(
        "cpu",
        [
            "Name",
            "Manufacturer",
            "NumberOfCores",
            "NumberOfLogicalProcessors",
            "CurrentClockSpeed",
            "MaxClockSpeed",
        ],
    )
    if not rows:
        return CpuInfo()
    row = rows[0]
    name = row.get("name", "Unknown")
    manufacturer = row.get("manufacturer", "Unknown")
    brand = (
        "Intel"
        if "intel" in manufacturer.lower()
        else ("AMD" if "amd" in manufacturer.lower() else manufacturer)
    )
    cores = _safe_int(row.get("numberofcores", "0"))
    threads = _safe_int(row.get("numberoflogicalprocessors", "0"))
    base_ghz = _safe_int(row.get("currentclockspeed", "0")) / 1000.0
    max_ghz = _safe_int(row.get("maxclockspeed", "0")) / 1000.0
    return CpuInfo(
        brand=brand,
        model=name,
        cores=cores,
        threads=threads,
        base_speed_ghz=round(base_ghz, 2),
        max_speed_ghz=round(max_ghz, 2),
    )


def _gpu_vram_from_registry(pnp_device_id: str) -> int:
    """Return true VRAM (MB) by matching the GPU PNPDeviceID to the driver
    registry key ``HardwareInformation.qwMemorySize``.

    ``Win32_VideoController.AdapterRAM`` is a signed 32-bit value that caps at
    4 GB and is often wrong on AMD/NVIDIA. The display-driver registry keeps
    the real value as a QWORD under
    ``HKLM\\SYSTEM\\CurrentControlSet\\Control\\Class\\{4d36e968-...}\\####``.
    """
    import contextlib
    import winreg

    if not pnp_device_id:
        return 0
    class_root = (
        r"SYSTEM\CurrentControlSet\Control\Class"
        r"\{4d36e968-e325-11ce-bfc1-08002be10318}"
    )
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, class_root) as parent:
            index = 0
            while True:
                try:
                    subkey = winreg.EnumKey(parent, index)
                except OSError:
                    return 0
                index += 1
                try:
                    with winreg.OpenKey(
                        winreg.HKEY_LOCAL_MACHINE,
                        class_root + "\\" + subkey,
                    ) as key:
                        with contextlib.suppress(OSError):
                            value, _ = winreg.QueryValueEx(key, "HardwareInformation.qwMemorySize")
                            if value and int(value) > 0:
                                return int(value) // (1024 * 1024)
                        with contextlib.suppress(OSError):
                            value, _ = winreg.QueryValueEx(key, "HardwareInformation.MemorySize")
                            if value and int(value) > 0:
                                return int(value) // (1024 * 1024)
                except OSError:
                    continue
    except OSError:
        return 0


def _detect_gpu() -> list[GpuInfo]:
    # Fast path: batch WMI query (single WMI COM call, cached).
    batch = _run_batch_wmi()
    gpu_data = batch.get("gpu")
    gpu_rows: list[Any] = gpu_data if isinstance(gpu_data, list) else []
    gpus: list[GpuInfo] = []
    for row in gpu_rows:
        if not isinstance(row, dict):
            continue
        name = str(row.get("Name", "Unknown"))
        lowered = name.lower()
        if "nvidia" in lowered:
            brand = "NVIDIA"
        elif "amd" in lowered or "radeon" in lowered:
            brand = "AMD"
        elif "intel" in lowered:
            brand = "Intel"
        else:
            brand = "Unknown"
        # True VRAM from the driver registry, then AdapterRAM as fallback.
        pnp = str(row.get("PNPDeviceID", ""))
        vram_mb = _gpu_vram_from_registry(pnp)
        if vram_mb <= 0:
            vram_bytes = _safe_int(str(row.get("AdapterRAM", "0")))
            vram_mb = abs(vram_bytes) // (1024 * 1024) if vram_bytes != 0 else 0
        driver = str(row.get("DriverVersion", "Unknown"))
        gpus.append(GpuInfo(brand=brand, model=name, vram_mb=vram_mb, driver_version=driver))
    if gpus:
        return gpus

    # Fallback: wmic path query (slower, ~1-2 s).
    rows = _run_wmic(
        "path",
        ["Name", "AdapterRAM", "DriverVersion"],
    )
    if not rows:
        return []
    for row in rows:
        name = row.get("name", "Unknown")
        lowered = name.lower()
        if "nvidia" in lowered:
            brand = "NVIDIA"
        elif "amd" in lowered or "radeon" in lowered:
            brand = "AMD"
        elif "intel" in lowered:
            brand = "Intel"
        else:
            brand = "Unknown"
        vram_bytes = _safe_int(row.get("adapterram", "0"))
        vram_mb = vram_bytes // (1024 * 1024) if vram_bytes > 0 else 0
        driver = row.get("driverversion", "Unknown")
        gpus.append(GpuInfo(brand=brand, model=name, vram_mb=vram_mb, driver_version=driver))
    return gpus


def _detect_ram() -> RamInfo:
    # Fast path: psutil gives total RAM in <5 ms.
    import contextlib

    modules: list[RamModule] = []
    total_mb = 0
    max_speed = 0
    ddr_type = "Unknown"

    ddr_map: dict[int, str] = {
        20: "DDR",
        21: "DDR2",
        24: "DDR3",
        26: "DDR4",
        34: "DDR5",
    }

    # Primary path: WMI COM (no subprocess, works on Win11 24H2 where wmic is
    # removed). Win32_PhysicalMemory exposes per-module detail.
    with contextlib.suppress(Exception):
        import win32com.client

        locator = win32com.client.Dispatch("WbemScripting.SWbemLocator")
        wmi = locator.ConnectServer(".", "root\\cimv2")
        mem_set = wmi.ExecQuery(
            "Select Manufacturer,Capacity,Speed,SMBIOSMemoryType from Win32_PhysicalMemory"
        )
        for item in mem_set:
            manufacturer = str(getattr(item, "Manufacturer", "")).strip() or "Unknown"
            capacity_bytes = _safe_int(str(getattr(item, "Capacity", "0")))
            capacity_mb = capacity_bytes // (1024 * 1024) if capacity_bytes > 0 else 0
            speed = _safe_int(str(getattr(item, "Speed", "0")))
            mem_type_id = _safe_int(str(getattr(item, "SMBIOSMemoryType", "0")))
            mem_type = ddr_map.get(mem_type_id, f"Type-{mem_type_id}" if mem_type_id else "Unknown")
            if capacity_mb > 0:
                modules.append(
                    RamModule(
                        manufacturer=manufacturer,
                        capacity_mb=capacity_mb,
                        speed_mhz=speed,
                        ddr_type=mem_type,
                    )
                )
                total_mb += capacity_mb
                if speed > max_speed:
                    max_speed = speed
                if mem_type != "Unknown":
                    ddr_type = mem_type

    # Fallback: wmic (older Windows where COM init failed).
    if not modules:
        rows = _run_wmic(
            "memorychip",
            ["Manufacturer", "Capacity", "Speed", "SMBIOSMemoryType"],
        )
        for row in rows:
            manufacturer = row.get("manufacturer", "Unknown").strip()
            capacity_bytes = _safe_int(row.get("capacity", "0"))
            capacity_mb = capacity_bytes // (1024 * 1024) if capacity_bytes > 0 else 0
            speed = _safe_int(row.get("speed", "0"))
            mem_type_id = _safe_int(row.get("smbiosmemorytype", "0"))
            mem_type = ddr_map.get(mem_type_id, f"Type-{mem_type_id}" if mem_type_id else "Unknown")
            if capacity_mb > 0:
                modules.append(
                    RamModule(
                        manufacturer=manufacturer,
                        capacity_mb=capacity_mb,
                        speed_mhz=speed,
                        ddr_type=mem_type,
                    )
                )
                total_mb += capacity_mb
                if speed > max_speed:
                    max_speed = speed
                if mem_type != "Unknown":
                    ddr_type = mem_type

    # Final fallback to psutil (total only, no per-module detail).
    if not modules:
        with contextlib.suppress(Exception):
            import psutil

            mem = psutil.virtual_memory()
            total_mb = int(mem.total / (1024 * 1024))

    return RamInfo(
        total_mb=total_mb,
        modules=tuple(modules),
        max_speed_mhz=max_speed,
        ddr_type=ddr_type,
    )


# MSFT_PhysicalDisk.MediaType enum -> label.
_MEDIA_TYPE_MAP = {
    0: "Unspecified",
    3: "HDD",
    4: "SSD",
    5: "SCM",
}

# MSFT_PhysicalDisk.BusType enum -> label.
_BUS_TYPE_MAP = {
    0: "Unknown",
    1: "SCSI",
    2: "ATAPI",
    3: "ATA",
    4: "IEEE 1394",
    5: "SSA",
    6: "Fibre Channel",
    7: "USB",
    8: "RAID",
    9: "iSCSI",
    10: "SAS",
    11: "SATA",
    12: "SD",
    13: "MMC",
    14: "Virtual",
    15: "File Backed Virtual",
    16: "Storage Spaces",
    17: "NVMe",
}


def _enum_label(mapping: dict[int, str], value: Any) -> str:
    """Map an integer enum to its label, falling back to the raw value."""
    try:
        return mapping.get(int(value), str(value))
    except (TypeError, ValueError):
        return str(value)


def _detect_storage() -> list[StorageDevice]:
    # Fast path: batch WMI query (single WMI COM call, cached).
    batch = _run_batch_wmi()
    storage_data = batch.get("storage")
    storage_rows: list[Any] = storage_data if isinstance(storage_data, list) else []
    devices: list[StorageDevice] = []
    for row in storage_rows:
        if not isinstance(row, dict):
            continue
        name = str(row.get("FriendlyName", "Unknown"))
        media_type = _enum_label(_MEDIA_TYPE_MAP, row.get("MediaType", 0))
        size_bytes = _safe_float(str(row.get("Size", "0")))
        size_gb = round(size_bytes / (1024**3), 1) if size_bytes > 0 else 0.0
        bus_type = _enum_label(_BUS_TYPE_MAP, row.get("BusType", 0))
        manufacturer_raw = row.get("Manufacturer", "")
        manufacturer = (
            str(manufacturer_raw).strip() if manufacturer_raw not in (None, "") else "Unknown"
        )
        lowered_media = media_type.lower()
        if "ssd" in lowered_media or "scm" in lowered_media:
            device_type = "SSD"
        elif "hdd" in lowered_media:
            device_type = "HDD"
        else:
            device_type = media_type
        devices.append(
            StorageDevice(
                device_type=device_type,
                brand=manufacturer,
                model=name,
                capacity_gb=size_gb,
                interface_type=bus_type,
            )
        )
    return devices


def _detect_network() -> list[NetworkInfo]:
    # Fast path: WMI COM query (cached). Win32_NetworkAdapter returns Speed
    # in bits per second as an integer; use the up/adapter with the highest
    # speed as the primary link.
    batch = _run_batch_wmi()
    net_data = batch.get("net")
    net_rows: list[Any] = net_data if isinstance(net_data, list) else []
    adapters: list[NetworkInfo] = []
    for row in net_rows:
        if not isinstance(row, dict):
            continue
        name = str(row.get("Name", "Unknown"))
        speed_raw = row.get("Speed", 0)
        speed_mbps = 0
        if isinstance(speed_raw, (int, float)):
            numeric_speed = speed_raw
        elif isinstance(speed_raw, str) and speed_raw.strip().lstrip("-").isdigit():
            numeric_speed = int(speed_raw)
        else:
            numeric_speed = 0
        if numeric_speed > 0:
            speed_mbps = int(numeric_speed / 1_000_000)
        adapters.append(NetworkInfo(adapter_name=name, link_speed_mbps=speed_mbps))
    if adapters:
        return sorted(adapters, key=lambda a: a.link_speed_mbps, reverse=True)
    return adapters


def _detect_windows() -> WindowsInfo:
    # Fast path: read registry directly via winreg (no subprocess, <1 ms).
    import contextlib

    product_name = f"Windows {platform.release()}"
    display_version = ""
    build_number = platform.version()
    edition = "Unknown"

    with contextlib.suppress(Exception):
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion",
        ) as key:
            for name, setter in (
                ("ProductName", "product"),
                ("DisplayVersion", "display"),
                ("CurrentBuild", "build"),
                ("EditionID", "edition"),
            ):
                try:
                    value, _ = winreg.QueryValueEx(key, name)
                    value = str(value)
                    if setter == "product":
                        product_name = value
                    elif setter == "display":
                        display_version = value
                    elif setter == "build":
                        build_number = value
                    elif setter == "edition":
                        edition = value
                except FileNotFoundError:
                    pass

    lowered_product = product_name.lower()
    if "ltsc" in lowered_product or "ltsb" in lowered_product:
        edition = f"{edition} (LTSC)"

    custom_markers = ["Starter", "Lite", "Ghost", "Tiny", "Atlas", "Revi", "KernelOS"]
    for marker in custom_markers:
        if marker.lower() in lowered_product:
            edition = f"{edition} (Custom: {marker})"
            break

    win_version = "11" if _safe_int(build_number) >= 22000 else "10"

    return WindowsInfo(
        version=f"Windows {win_version}",
        build_number=build_number,
        edition=edition,
        display_version=display_version,
        product_name=product_name,
    )


def scan_hardware() -> HardwareScanResult:
    """Perform a full read-only hardware scan.

    Detectors run serially (ThreadPoolExecutor added ~5 s of overhead on
    cold WMI COM init; serial is faster in practice because the WMI COM
    objects are single-threaded). CPU/RAM use the instant psutil path;
    GPU/storage/network use one WMI COM batch (cached); Windows reads
    the registry directly via winreg (<1 ms).
    """
    global _BATCH_CACHE
    _BATCH_CACHE = None  # Invalidate cache for fresh scan.
    return HardwareScanResult(
        cpu=_detect_cpu(),
        gpu=_detect_gpu(),
        ram=_detect_ram(),
        storage=_detect_storage(),
        network=_detect_network(),
        windows=_detect_windows(),
    )
