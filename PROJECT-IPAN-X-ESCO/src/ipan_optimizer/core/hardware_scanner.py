from __future__ import annotations

import platform
import subprocess
from dataclasses import asdict, dataclass, field


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
    rows = _run_wmic(
        "path",
        ["Name", "AdapterRAM", "DriverVersion"],
    )
    if not rows:
        ps_script = (
            "Get-CimInstance Win32_VideoController | "
            "Select-Object Name, AdapterRAM, DriverVersion | "
            "ConvertTo-Csv -NoTypeInformation"
        )
        output = _run_powershell(ps_script)
        if not output:
            return []
        lines = output.splitlines()
        if len(lines) < 2:
            return []
        headers = [h.strip().strip('"').lower() for h in lines[0].split(",")]
        rows = []
        for line in lines[1:]:
            values = [v.strip().strip('"') for v in line.split(",")]
            if len(values) >= len(headers):
                rows.append(dict(zip(headers, values, strict=False)))

    gpus: list[GpuInfo] = []
    for row in rows:
        name = row.get("name", "Unknown")
        brand = (
            "NVIDIA"
            if "nvidia" in name.lower()
            else (
                "AMD"
                if "amd" in name.lower() or "radeon" in name.lower()
                else ("Intel" if "intel" in name.lower() else "Unknown")
            )
        )
        vram_bytes = _safe_int(row.get("adapterram", "0"))
        vram_mb = vram_bytes // (1024 * 1024) if vram_bytes > 0 else 0
        driver = row.get("driverversion", "Unknown")
        gpus.append(GpuInfo(brand=brand, model=name, vram_mb=vram_mb, driver_version=driver))
    return gpus


def _detect_ram() -> RamInfo:
    rows = _run_wmic(
        "memorychip",
        ["Manufacturer", "Capacity", "Speed", "SMBIOSMemoryType"],
    )
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

    if not modules:
        import contextlib

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
    ps_script = (
        "Get-PhysicalDisk | "
        "Select-Object FriendlyName, MediaType, Size, BusType, Manufacturer | "
        "ConvertTo-Csv -NoTypeInformation"
    )
    output = _run_powershell(ps_script)
    devices: list[StorageDevice] = []
    if not output:
        return devices

    lines = output.splitlines()
    if len(lines) < 2:
        return devices

    headers = [h.strip().strip('"').lower() for h in lines[0].split(",")]
    for line in lines[1:]:
        values = [v.strip().strip('"') for v in line.split(",")]
        if len(values) < len(headers):
            continue
        row = dict(zip(headers, values, strict=False))
        name = row.get("friendlyname", "Unknown")
        media_type = row.get("mediatype", "Unspecified")
        size_bytes = _safe_float(row.get("size", "0"))
        size_gb = round(size_bytes / (1024**3), 1) if size_bytes > 0 else 0.0
        bus_type = row.get("bustype", "Unknown")
        manufacturer = row.get("manufacturer", "").strip() or "Unknown"

        device_type = (
            "SSD"
            if "ssd" in media_type.lower()
            else ("HDD" if "hdd" in media_type.lower() else media_type)
        )

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
    ps_script = (
        "Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | "
        "Select-Object Name, LinkSpeed | "
        "ConvertTo-Csv -NoTypeInformation"
    )
    output = _run_powershell(ps_script)
    adapters: list[NetworkInfo] = []
    if not output:
        return adapters

    lines = output.splitlines()
    if len(lines) < 2:
        return adapters

    headers = [h.strip().strip('"').lower() for h in lines[0].split(",")]
    for line in lines[1:]:
        values = [v.strip().strip('"') for v in line.split(",")]
        if len(values) < len(headers):
            continue
        row = dict(zip(headers, values, strict=False))
        name = row.get("name", "Unknown")
        link_speed_str = row.get("linkspeed", "0")
        speed_mbps = 0
        if "gbps" in link_speed_str.lower():
            speed_mbps = int(_safe_float(link_speed_str.split()[0]) * 1000)
        elif "mbps" in link_speed_str.lower():
            speed_mbps = _safe_int(link_speed_str.split()[0])

        adapters.append(NetworkInfo(adapter_name=name, link_speed_mbps=speed_mbps))

    return adapters


def _detect_windows() -> WindowsInfo:
    version = platform.version()
    release = platform.release()

    ps_script = (
        "(Get-ItemProperty "
        "'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion' "
        "| Select-Object ProductName, DisplayVersion, CurrentBuild, "
        "EditionID, InstallationType).PSObject.Properties | "
        "ForEach-Object { $_.Name + '=' + $_.Value }"
    )
    output = _run_powershell(ps_script)

    product_name = f"Windows {release}"
    display_version = ""
    build_number = version
    edition = "Unknown"

    for line in output.splitlines():
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip().lower()
        val = val.strip()
        if key == "productname":
            product_name = val
        elif key == "displayversion":
            display_version = val
        elif key == "currentbuild":
            build_number = val
        elif key == "editionid":
            edition = val

    is_ltsc = "ltsc" in product_name.lower() or "ltsb" in product_name.lower()
    if is_ltsc:
        edition = f"{edition} (LTSC)"

    custom_markers = ["Starter", "Lite", "Ghost", "Tiny", "Atlas", "Revi", "KernelOS"]
    for marker in custom_markers:
        if marker.lower() in product_name.lower():
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
    """Perform a full read-only hardware scan."""
    return HardwareScanResult(
        cpu=_detect_cpu(),
        gpu=_detect_gpu(),
        ram=_detect_ram(),
        storage=_detect_storage(),
        network=_detect_network(),
        windows=_detect_windows(),
    )
