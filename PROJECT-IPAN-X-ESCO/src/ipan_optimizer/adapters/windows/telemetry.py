"""Read-only hardware telemetry providers.

Combines documented, non-mutating Windows sources that mirror what the
Windows Task Manager shows:

- PDH performance counters for CPU load and effective clock.
- PDH ``GPU Engine`` / ``GPU Adapter Memory`` counters for GPU utilization
  and dedicated memory usage (the same counters Task Manager reads; no MSI
  Afterburner required).
- PDH ``PhysicalDisk`` and ``Network Interface`` counters for disk active
  time and network throughput.
- MSI Afterburner Hardware Monitoring shared memory (``MAHMSharedMemory``)
  is only an optional extra for GPU/CPU temperature and GPU clock when
  Afterburner happens to be running; it is never required.
- ``MSFT_StorageReliabilityCounter`` for SSD temperature.

Every provider fails closed: when a sensor is unavailable the field is
``None`` and never represented as zero (SPEC.md invariant).
"""

from __future__ import annotations

import contextlib
import ctypes
import struct
from dataclasses import dataclass

_MAHM_SIGNATURE = 0x4D41484D  # "MAHM"
_MAHM_HEADER_FIELDS = 5  # dwSignature, dwVersion, dwHeaderSize, dwNumEntries, dwEntrySize
_MAHM_STRING_LEN = 260
_MAHM_STRING_COUNT = 5  # id, units, name, data, recommended format
_MAHM_DATA_OFFSET = _MAHM_STRING_LEN * _MAHM_STRING_COUNT  # fltData follows the 5 strings
_MAHM_ID_GPU_TEMP = "gpu temperature"
_MAHM_ID_GPU_CLOCK = "core clock"
_MAHM_ID_CPU_TEMP = "cpu temperature"
_MAHM_MAP_NAME = "MAHMSharedMemory"
_FILE_MAP_READ = 0x0004

_PDH_CPU_PERF = r"\Processor Information(_Total)\% Processor Performance"
_PDH_CPU_FREQ = r"\Processor Information(_Total)\Processor Frequency"
_PDH_CPU_TIME = r"\Processor Information(_Total)\% Processor Time"
_PDH_GPU_ENGINE_UTIL = r"\GPU Engine(*)\Utilization Percentage"
_PDH_GPU_ADAPTER_MEM = r"\GPU Adapter Memory(*)\Dedicated Usage"
_PDH_DISK_ACTIVE = r"\PhysicalDisk(_Total)\% Disk Time"
_PDH_DISK_BYTES = r"\PhysicalDisk(_Total)\Disk Bytes/sec"
_PDH_NET_BYTES = r"\Network Interface(*)\Bytes Total/sec"

# Effective-clock guard rails: anything outside 10%..200% of base frequency is
# treated as a transient counter glitch and discarded.
_EFF_FREQ_MIN_RATIO = 0.1
_EFF_FREQ_MAX_RATIO = 2.0

# SSD temperature changes slowly; querying Storage every tick is wasted work.
_SSD_REFRESH_TICKS = 5

# Slow sensors (powershell/nvidia-smi) are refreshed by a single background
# thread on this interval. The foreground read_telemetry() returns the cached
# values immediately, so the UI loop never blocks on subprocess startup.
_SLOW_REFRESH_SECONDS = 3.0


@dataclass(frozen=True)
class TelemetrySample:
    """One snapshot of read-only hardware telemetry.

    ``None`` means the sensor is unavailable on this machine right now.

    The GPU/disk/network fields come from the same PDH performance counters
    the Windows Task Manager reads, so they work on every Windows 10/11
    build (including custom/modded builds) without MSI Afterburner.
    """

    cpu_load_percent: float | None
    cpu_freq_mhz: float | None
    gpu_freq_mhz: float | None
    gpu_util_percent: float | None
    gpu_mem_used_mb: float | None
    ram_used_mb: float | None
    ram_percent: float | None
    disk_active_percent: float | None
    disk_bytes_per_sec: float | None
    net_bytes_per_sec: float | None
    cpu_temp_c: float | None
    gpu_temp_c: float | None
    ssd_temp_c: float | None


def effective_freq_mhz(base_mhz: float, perf_percent: float) -> float | None:
    """Compute effective clock from the PDH performance ratio.

    ``% Processor Performance`` is reported relative to the base clock, so the
    effective frequency is ``base * perf / 100``. Out-of-band values from a
    transient counter state are rejected.
    """
    if base_mhz <= 0 or perf_percent <= 0:
        return None
    ratio = perf_percent / 100.0
    if not (_EFF_FREQ_MIN_RATIO <= ratio <= _EFF_FREQ_MAX_RATIO):
        return None
    return base_mhz * ratio


def parse_mahm_entries(
    buffer: bytes,
    header_size: int,
    num_entries: int,
    entry_size: int,
) -> dict[str, float]:
    """Parse the MAHM shared-memory body into ``{entry_id: float_data}``.

    Each entry holds five 260-byte strings followed by ``fltData`` and other
    scalar fields. Only the identifier and ``fltData`` are needed here. This is
    a pure function so tests can feed a synthetic buffer without touching the
    host mapping.
    """
    entries: dict[str, float] = {}
    if header_size <= 0 or entry_size < _MAHM_DATA_OFFSET + 4 or num_entries <= 0:
        return entries
    for index in range(num_entries):
        offset = header_size + index * entry_size
        if offset + _MAHM_DATA_OFFSET + 4 > len(buffer):
            break
        raw_id = buffer[offset : offset + _MAHM_STRING_LEN]
        entry_id = raw_id.split(b"\0", 1)[0].decode("ascii", "ignore").strip().lower()
        if not entry_id:
            continue
        (value,) = struct.unpack_from("=f", buffer, offset + _MAHM_DATA_OFFSET)
        entries[entry_id] = float(value)
    return entries


class _MahmReader:
    """Read-only view over the MSI Afterburner shared memory section."""

    def __init__(self) -> None:
        kernel32 = ctypes.windll.kernel32
        kernel32.OpenFileMappingW.restype = ctypes.c_void_p
        kernel32.OpenFileMappingW.argtypes = [ctypes.c_uint32, ctypes.c_bool, ctypes.c_wchar_p]
        kernel32.MapViewOfFile.restype = ctypes.c_void_p
        kernel32.MapViewOfFile.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.c_uint32,
            ctypes.c_uint32,
            ctypes.c_size_t,
        ]
        kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
        kernel32.UnmapViewOfFile.argtypes = [ctypes.c_void_p]
        self._kernel32 = kernel32

    def read(self) -> dict[str, float]:
        kernel32 = self._kernel32
        handle = kernel32.OpenFileMappingW(_FILE_MAP_READ, False, _MAHM_MAP_NAME)
        if not handle:
            return {}
        try:
            view = kernel32.MapViewOfFile(handle, _FILE_MAP_READ, 0, 0, 0)
            if not view:
                return {}
            try:
                header = ctypes.string_at(view, _MAHM_HEADER_FIELDS * 4)
                signature, _version, header_size, num_entries, entry_size = struct.unpack_from(
                    f"={_MAHM_HEADER_FIELDS}I", header
                )
                if signature != _MAHM_SIGNATURE:
                    return {}
                # Bound the copy to the documented region so a hostile or
                # corrupted section cannot trigger over-reads.
                safe_entries = max(0, min(num_entries, 512))
                safe_size = min(entry_size, 4096)
                body_size = header_size + safe_entries * safe_size
                if body_size <= header_size:
                    return {}
                buffer = ctypes.string_at(view, body_size)
                return parse_mahm_entries(buffer, header_size, safe_entries, safe_size)
            finally:
                kernel32.UnmapViewOfFile(view)
        finally:
            kernel32.CloseHandle(handle)


class _PdhCpuSampler:
    """Open PDH query for CPU load and effective frequency."""

    def __init__(self) -> None:
        import win32pdh  # type: ignore[import-untyped]

        self._win32pdh = win32pdh
        self._query = win32pdh.OpenQuery()
        self._perf = win32pdh.AddCounter(self._query, _PDH_CPU_PERF)
        self._freq = win32pdh.AddCounter(self._query, _PDH_CPU_FREQ)
        self._time = win32pdh.AddCounter(self._query, _PDH_CPU_TIME)
        # Rate counters require two samples; prime the query once.
        win32pdh.CollectQueryData(self._query)

    def read(self) -> tuple[float | None, float | None]:
        pdh = self._win32pdh
        pdh.CollectQueryData(self._query)
        _, perf_value = pdh.GetFormattedCounterValue(self._perf, pdh.PDH_FMT_DOUBLE)
        _, freq_value = pdh.GetFormattedCounterValue(self._freq, pdh.PDH_FMT_DOUBLE)
        _, time_value = pdh.GetFormattedCounterValue(self._time, pdh.PDH_FMT_DOUBLE)
        load = float(time_value) if 0.0 <= time_value <= 100.0 else None
        freq = effective_freq_mhz(float(freq_value), float(perf_value))
        return load, freq


class _PdhTaskManagerSampler:
    """Read Task Manager-style counters via PDH.

    CPU/disk/network use cheap persistent counters. GPU engine utilization and
    GPU adapter memory require enumerating the live ``GPU Engine`` instances
    (the same data Task Manager reads) and summing them, because the ``*``
    wildcard does not aggregate fraction counters. The GPU enumeration is
    comparatively expensive (~150-250 ms), so ``refresh()`` is called from a
    background thread and ``read()`` only returns the last snapshot.
    """

    def __init__(self) -> None:
        import win32pdh

        self._win32pdh = win32pdh
        self._query = win32pdh.OpenQuery()
        self._disk_time = win32pdh.AddCounter(self._query, _PDH_DISK_ACTIVE)
        self._disk_bytes = win32pdh.AddCounter(self._query, _PDH_DISK_BYTES)
        self._net_bytes = win32pdh.AddCounter(self._query, _PDH_NET_BYTES)
        self._lock = __import__("threading").Lock()
        self._gpu_util: float | None = None
        self._gpu_mem_mb: float | None = None
        self._disk_active: float | None = None
        self._disk_bps: float | None = None
        self._net_bps: float | None = None
        # Rate counters require two samples; prime once.
        win32pdh.CollectQueryData(self._query)

    def refresh(self) -> None:
        """Re-read every Task Manager counter and cache the snapshot."""
        pdh = self._win32pdh
        disk_active: float | None = None
        disk_bps: float | None = None
        net_bps: float | None = None
        with contextlib.suppress(Exception):
            pdh.CollectQueryData(self._query)
            _, raw = pdh.GetFormattedCounterValue(self._disk_time, pdh.PDH_FMT_DOUBLE)
            if 0.0 <= raw <= 100.0:
                disk_active = float(raw)
            _, raw = pdh.GetFormattedCounterValue(self._disk_bytes, pdh.PDH_FMT_DOUBLE)
            disk_bps = float(raw) if raw >= 0 else None
            _, raw = pdh.GetFormattedCounterValue(self._net_bytes, pdh.PDH_FMT_DOUBLE)
            net_bps = float(raw) if raw >= 0 else None

        gpu_util: float | None = None
        gpu_mem_mb: float | None = None
        with contextlib.suppress(Exception):
            _, instances = pdh.EnumObjectItems(None, None, "GPU Engine", pdh.PERF_DETAIL_WIZARD)
            if instances:
                query = pdh.OpenQuery()
                try:
                    counters = [
                        pdh.AddCounter(query, rf"\GPU Engine({inst})\Utilization Percentage")
                        for inst in instances
                    ]
                    pdh.CollectQueryData(query)
                    pdh.CollectQueryData(query)
                    total = 0.0
                    for handle in counters:
                        with contextlib.suppress(Exception):
                            _, value = pdh.GetFormattedCounterValue(handle, pdh.PDH_FMT_DOUBLE)
                            total += float(value)
                    if 0.0 <= total <= 100.0:
                        gpu_util = total
                finally:
                    pdh.CloseQuery(query)

        with contextlib.suppress(Exception):
            _, mem_instances = pdh.EnumObjectItems(
                None, None, "GPU Adapter Memory", pdh.PERF_DETAIL_WIZARD
            )
            if mem_instances:
                query = pdh.OpenQuery()
                try:
                    counters = [
                        pdh.AddCounter(
                            query,
                            rf"\GPU Adapter Memory({inst})\Dedicated Usage",
                        )
                        for inst in mem_instances
                    ]
                    pdh.CollectQueryData(query)
                    pdh.CollectQueryData(query)
                    total_bytes = 0.0
                    for handle in counters:
                        with contextlib.suppress(Exception):
                            _, value = pdh.GetFormattedCounterValue(handle, pdh.PDH_FMT_DOUBLE)
                            total_bytes += float(value)
                    if total_bytes > 0:
                        gpu_mem_mb = total_bytes / (1024 * 1024)
                finally:
                    pdh.CloseQuery(query)

        with self._lock:
            self._gpu_util = gpu_util
            self._gpu_mem_mb = gpu_mem_mb
            self._disk_active = disk_active
            self._disk_bps = disk_bps
            self._net_bps = net_bps

    def read(self) -> tuple[float | None, float | None, float | None, float | None, float | None]:
        """Return cached (gpu_util, gpu_mem_mb, disk_active, disk_bps, net_bps)."""
        with self._lock:
            return (
                self._gpu_util,
                self._gpu_mem_mb,
                self._disk_active,
                self._disk_bps,
                self._net_bps,
            )


class _StorageTempSampler:
    """SSD temperature from Storage Reliability counters.

    ``MSFT_StorageReliabilityCounter`` is only reachable through CIM/WSMan
    associations, so a background daemon refreshes the value with the same
    documented PowerShell pipeline used by the rest of the scanner. The bridge
    never blocks on it: ``read()`` returns the last cached value. Some disks
    report a zero placeholder, so the highest positive temperature wins.
    """

    _COMMAND = (
        "Get-PhysicalDisk | Get-StorageReliabilityCounter | "
        "Select-Object -ExpandProperty Temperature"
    )

    def __init__(self) -> None:
        import threading

        self._cached: float | None = None
        self._stop = threading.Event()
        self._thread = threading.Thread(
            target=self._refresh_loop, name="ssd-telemetry", daemon=True
        )
        self._thread.start()

    @staticmethod
    def _pick_temperatures(values: list[float]) -> float | None:
        positive = [value for value in values if value > 0]
        return max(positive) if positive else None

    def _refresh_once(self) -> None:
        import subprocess

        result = subprocess.run(  # noqa: S603
            ["powershell", "-NoProfile", "-Command", self._COMMAND],  # noqa: S607
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=0x08000000,
        )
        if result.returncode != 0:
            return
        temperatures: list[float] = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                temperatures.append(float(line))
            except ValueError:
                continue
        picked = self._pick_temperatures(temperatures)
        if picked is not None:
            self._cached = picked

    def _refresh_loop(self) -> None:
        while not self._stop.is_set():
            with contextlib.suppress(Exception):
                self._refresh_once()
            self._stop.wait(_SSD_REFRESH_TICKS)

    def read(self) -> float | None:
        return self._cached


class _SlowSensorCache:
    """Background-refreshed cache for expensive sensor reads.

    Subprocess spawns (powershell, nvidia-smi) take 100-500 ms each on
    Windows. Running them every UI tick (1 s) pegs the CPU. This cache
    refreshes them on a single daemon thread every ``_SLOW_REFRESH_SECONDS``
    and exposes a non-blocking ``read()`` that returns the last snapshot.
    """

    def __init__(self) -> None:
        import threading

        self._lock = threading.Lock()
        self._cached: dict[str, float | str | None] = {
            "cpu_temp": None,
            "gpu_temp": None,
            "gpu_freq": None,
            "amd_name": "",
        }
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._refresh_loop, name="slow-sensors", daemon=True)
        self._thread.start()

    def _refresh_once(self) -> None:
        import shutil

        powershell = shutil.which("powershell") or "powershell"
        nvidia_smi = shutil.which("nvidia-smi") or "nvidia-smi"
        cpu_temp: float | None = None
        gpu_temp: float | None = None
        gpu_freq: float | None = None
        amd_name = ""

        # Task Manager-style PDH counters (GPU util/memory, disk, network).
        _refresh_task_manager()

        # MSI Afterburner shared memory (no subprocess cost).
        with contextlib.suppress(Exception):
            entries = _PROVIDERS.mahm.read()
            gpu_temp = pick_sensor(entries, _MAHM_ID_GPU_TEMP)
            gpu_freq = pick_sensor(entries, _MAHM_ID_GPU_CLOCK)
            cpu_temp = pick_sensor(entries, _MAHM_ID_CPU_TEMP)

        # nvidia-smi only when MAHM did not provide GPU clock.
        if gpu_freq is None:
            with contextlib.suppress(Exception):
                import subprocess

                result = subprocess.run(  # noqa: S603
                    [
                        nvidia_smi,
                        "--query-gpu=clocks.current.graphics,temperature.gpu",
                        "--format=csv,noheader,nounits",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=3,
                )
                if result.returncode == 0 and result.stdout.strip():
                    parts = result.stdout.strip().split("\n")[0].split(",")
                    if parts[0].strip():
                        gpu_freq = float(parts[0].strip())
                    if gpu_temp is None and len(parts) >= 2 and parts[1].strip():
                        gpu_temp = float(parts[1].strip())

        # AMD name detection (cheap CIM call, cached).
        with contextlib.suppress(Exception):
            import subprocess

            amd_result = subprocess.run(  # noqa: S603
                [
                    powershell,
                    "-NoProfile",
                    "-Command",
                    "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name",
                ],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=0x08000000,
            )
            if amd_result.returncode == 0 and amd_result.stdout.strip():
                amd_name = amd_result.stdout.strip().lower()

        # CPU temperature via MSAcpi_ThermalZoneTemperature.
        if cpu_temp is None:
            with contextlib.suppress(Exception):
                import subprocess

                result = subprocess.run(  # noqa: S603
                    [
                        powershell,
                        "-NoProfile",
                        "-Command",
                        "Get-CimInstance -Namespace root/wmi -ClassName "
                        "MSAcpi_ThermalZoneTemperature | "
                        "Select-Object -ExpandProperty CurrentTemperature | "
                        "Select-Object -First 1",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    creationflags=0x08000000,
                )
                if result.returncode == 0 and result.stdout.strip():
                    raw = float(result.stdout.strip())
                    cpu_temp = raw / 10.0 - 273.15
                    if cpu_temp < 0 or cpu_temp > 150:
                        cpu_temp = None

        # OpenHardwareMonitor / LibreHardwareMonitor fallback.
        if cpu_temp is None or gpu_temp is None:
            with contextlib.suppress(Exception):
                import json
                import subprocess

                result = subprocess.run(  # noqa: S603
                    [
                        powershell,
                        "-NoProfile",
                        "-Command",
                        "Get-CimInstance -Namespace root/OpenHardwareMonitor -ClassName Sensor "
                        "| Where-Object {$_.SensorType -eq 'Temperature'} | "
                        "Select-Object Name,Value | ConvertTo-Json",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    creationflags=0x08000000,
                )
                if result.returncode == 0 and result.stdout.strip():
                    try:
                        sensors = json.loads(result.stdout)
                        if not isinstance(sensors, list):
                            sensors = [sensors]
                        for s in sensors:
                            name = str(s.get("Name", "")).lower()
                            val = float(s.get("Value", 0))
                            if "cpu" in name and cpu_temp is None and val > 0:
                                cpu_temp = val
                            elif (
                                ("gpu" in name or "video" in name) and gpu_temp is None and val > 0
                            ):
                                gpu_temp = val
                    except (json.JSONDecodeError, ValueError):
                        pass

        with self._lock:
            self._cached["cpu_temp"] = cpu_temp
            self._cached["gpu_temp"] = gpu_temp
            self._cached["gpu_freq"] = gpu_freq
            self._cached["amd_name"] = amd_name

    def _refresh_loop(self) -> None:
        while not self._stop.is_set():
            with contextlib.suppress(Exception):
                self._refresh_once()
            self._stop.wait(_SLOW_REFRESH_SECONDS)

    def read(self) -> dict[str, float | str | None]:
        with self._lock:
            return dict(self._cached)


def _refresh_task_manager() -> None:
    """Refresh Task Manager-style PDH counters on the background thread."""
    task = _PROVIDERS.task
    if task is not None:
        with contextlib.suppress(Exception):
            task.refresh()


def pick_sensor(entries: dict[str, float], entry_id: str) -> float | None:
    """Return a positive sensor value from parsed MAHM entries, else ``None``."""
    value = entries.get(entry_id)
    if value is None or value <= 0:
        return None
    return value


class _TelemetryProviders:
    """Lazily initialised singleton providers; each fails closed."""

    def __init__(self) -> None:
        self._mahm: _MahmReader | None = None
        self._pdh: _PdhCpuSampler | None = None
        self._task: _PdhTaskManagerSampler | None = None
        self._storage: _StorageTempSampler | None = None
        self._slow: _SlowSensorCache | None = None
        self._pdh_broken = False
        self._task_broken = False
        self._storage_broken = False

    @property
    def mahm(self) -> _MahmReader:
        if self._mahm is None:
            self._mahm = _MahmReader()
        return self._mahm

    @property
    def pdh(self) -> _PdhCpuSampler | None:
        if self._pdh is None and not self._pdh_broken:
            try:
                self._pdh = _PdhCpuSampler()
            except Exception:
                self._pdh_broken = True
        return self._pdh

    @property
    def task(self) -> _PdhTaskManagerSampler | None:
        if self._task is None and not self._task_broken:
            try:
                self._task = _PdhTaskManagerSampler()
            except Exception:
                self._task_broken = True
        return self._task

    @property
    def storage(self) -> _StorageTempSampler | None:
        if self._storage is None and not self._storage_broken:
            try:
                self._storage = _StorageTempSampler()
            except Exception:
                self._storage_broken = True
        return self._storage

    @property
    def slow(self) -> _SlowSensorCache | None:
        if self._slow is None:
            with contextlib.suppress(Exception):
                self._slow = _SlowSensorCache()
        return self._slow


_PROVIDERS = _TelemetryProviders()


def read_telemetry() -> TelemetrySample:
    """Collect one read-only telemetry snapshot from every available source.

    Fast path: PDH CPU counters, Task Manager-style PDH counters (GPU
    util/memory, disk, network), psutil RAM, and the cached slow-sensor
    values. No subprocess is spawned on this call path; the background daemon
    thread refreshes temperatures, GPU clock, and the GPU engine enumeration
    every few seconds.
    """
    cpu_load: float | None = None
    cpu_freq: float | None = None
    gpu_freq: float | None = None
    gpu_util: float | None = None
    gpu_mem_mb: float | None = None
    disk_active: float | None = None
    disk_bps: float | None = None
    net_bps: float | None = None
    cpu_temp: float | None = None
    gpu_temp: float | None = None
    ssd_temp: float | None = None
    ram_used: float | None = None
    ram_percent: float | None = None

    pdh = _PROVIDERS.pdh
    if pdh is not None:
        try:
            cpu_load, cpu_freq = pdh.read()
        except Exception:
            _PROVIDERS._pdh_broken = True

    task = _PROVIDERS.task
    if task is not None:
        try:
            gpu_util, gpu_mem_mb, disk_active, disk_bps, net_bps = task.read()
        except Exception:
            _PROVIDERS._task_broken = True

    # Slow sensors: non-blocking read of background cache.
    slow = _PROVIDERS.slow
    if slow is not None:
        with contextlib.suppress(Exception):
            cached = slow.read()
            cpu_val = cached.get("cpu_temp")
            if isinstance(cpu_val, (int, float)):
                cpu_temp = float(cpu_val)
            gpu_val = cached.get("gpu_temp")
            if isinstance(gpu_val, (int, float)):
                gpu_temp = float(gpu_val)
            freq_val = cached.get("gpu_freq")
            if isinstance(freq_val, (int, float)):
                gpu_freq = float(freq_val)

    storage = _PROVIDERS.storage
    if storage is not None:
        try:
            ssd_temp = storage.read()
        except Exception:
            _PROVIDERS._storage_broken = True

    with contextlib.suppress(Exception):
        import psutil

        mem = psutil.virtual_memory()
        ram_used = mem.used / (1024 * 1024)
        ram_percent = float(mem.percent)
        if cpu_load is None:
            fallback_load = psutil.cpu_percent(interval=None)
            cpu_load = float(fallback_load) if 0.0 <= fallback_load <= 100.0 else None

    return TelemetrySample(
        cpu_load_percent=cpu_load,
        cpu_freq_mhz=cpu_freq,
        gpu_freq_mhz=gpu_freq,
        gpu_util_percent=gpu_util,
        gpu_mem_used_mb=gpu_mem_mb,
        ram_used_mb=ram_used,
        ram_percent=ram_percent,
        disk_active_percent=disk_active,
        disk_bytes_per_sec=disk_bps,
        net_bytes_per_sec=net_bps,
        cpu_temp_c=cpu_temp,
        gpu_temp_c=gpu_temp,
        ssd_temp_c=ssd_temp,
    )
