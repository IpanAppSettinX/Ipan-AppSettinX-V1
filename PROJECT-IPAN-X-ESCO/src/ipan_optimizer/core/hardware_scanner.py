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
    """Query GPU, storage, and network via WMI COM (no subprocess).

    Uses ``win32com`` to talk to the WMI service directly. This avoids the
    ~1.5 s PowerShell startup cost per call. Falls back to a single batched
    PowerShell script if COM init fails.
    """
    global _BATCH_CACHE
    if _BATCH_CACHE is not None:
        return _BATCH_CACHE

    # Primary path: WMI COM (instant, no subprocess).
    result: dict[str, Any] = {"gpu": [], "storage": [], "net": []}
    try:
        import contextlib

        import win32com.client  # type: ignore[import-untyped]

        locator = win32com.client.Dispatch("WbemScripting.SWbemLocator")
        with contextlib.suppress(Exception):
            wmi = locator.ConnectServer(".", "root\\cimv2")
            gpu_set = wmi.ExecQuery(
                "Select Name,DriverVersion,AdapterRAM from Win32_VideoController"
            )
            result["gpu"] = [
                {
                    "Name": item.Name,
                    "DriverVersion": item.DriverVersion,
                    "AdapterRAM": item.AdapterRAM,
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
        "$gpu = @(Get-CimInstance Win32_VideoController | "
        "Select-Object Name,DriverVersion,AdapterRAM); "
        "$storage = @(Get-PhysicalDisk | "
        "Select-Object FriendlyName,MediaType,Size,BusType,Manufacturer); "
        "$net = @(Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | "
        "Select-Object Name,LinkSpeed); "
        "[ordered]@{gpu=$gpu;storage=$storage;net=$net} "
        "| ConvertTo-Json -Compress -Depth 4"
    )
    output = _run_powershell(script)
    if not output:
        _BATCH_CACHE = {"gpu": [], "storage": [], "net": []}
        return _BATCH_CACHE
    try:
        parsed = json.loads(output)
        _BATCH_CACHE = {
            "gpu": parsed.get("gpu") or [],
            "storage": parsed.get("storage") or [],
            "net": parsed.get("net") or [],
        }
    except (json.JSONDecodeError, TypeError):
        _BATCH_CACHE = {"gpu": [], "storage": [], "net": []}
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
    # Fast path: psutil gives us cores/threads/clock in <5 ms with no subprocess.
    import contextlib

    with contextlib.suppress(Exception):
        import psutil

        freq = psutil.cpu_freq()
        base_ghz = round(freq.current / 1000, 2) if freq else 0.0
        max_ghz = round(freq.max / 1000, 2) if freq and freq.max > 0 else base_ghz
        # Get brand string from platform.processor() or wmic (one-shot, cached).
        name = platform.processor() or "Unknown"
        if not name or name == "Unknown":
            rows = _run_wmic(
                "cpu",
                ["Name", "Manufacturer", "NumberOfCores", "NumberOfLogicalProcessors"],
            )
            if rows:
                row = rows[0]
                name = row.get("name", "Unknown")
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

    # Fallback: wmic (slower, ~1-3 s).
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


def _detect_gpu() -> list[GpuInfo]:
    # Fast path: batch WMI query (single powershell call, cached).
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
        vram_bytes = _safe_int(str(row.get("AdapterRAM", "0")))
        vram_mb = vram_bytes // (1024 * 1024) if vram_bytes > 0 else 0
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

    # wmic gives per-module detail (manufacturer, speed, DDR type).
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

    # Fallback to psutil if wmic returned nothing (Windows 11 deprecation).
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


def _detect_storage() -> list[StorageDevice]:
    # Fast path: batch WMI query (single powershell call, cached).
    batch = _run_batch_wmi()
    storage_data = batch.get("storage")
    storage_rows: list[Any] = storage_data if isinstance(storage_data, list) else []
    devices: list[StorageDevice] = []
    for row in storage_rows:
        if not isinstance(row, dict):
            continue
        name = str(row.get("FriendlyName", "Unknown"))
        media_type = str(row.get("MediaType", "Unspecified"))
        size_bytes = _safe_float(str(row.get("Size", "0")))
        size_gb = round(size_bytes / (1024**3), 1) if size_bytes > 0 else 0.0
        bus_type = str(row.get("BusType", "Unknown"))
        manufacturer = str(row.get("Manufacturer", "")).strip() or "Unknown"
        lowered_media = media_type.lower()
        if "ssd" in lowered_media:
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
    # in bits per second as an integer.
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
        if isinstance(speed_raw, (int, float)) and speed_raw > 0:
            speed_mbps = int(speed_raw / 1_000_000)
        adapters.append(NetworkInfo(adapter_name=name, link_speed_mbps=speed_mbps))
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
