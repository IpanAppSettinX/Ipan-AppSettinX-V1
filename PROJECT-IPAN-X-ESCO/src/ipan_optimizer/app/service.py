from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from ipan_optimizer.adapters.emulators.discovery import EmulatorDiscovery
from ipan_optimizer.app.jobs import JobManager
from ipan_optimizer.core.recommendations import build_recommendations
from ipan_optimizer.core.transactions import TransactionManager
from ipan_optimizer.domain.models import MachineCapabilityVector
from ipan_optimizer.game.session import GameSessionController
from ipan_optimizer.ports.windows import WindowsBackend


class OptimizerService:
    def __init__(
        self,
        backend: WindowsBackend,
        transactions: TransactionManager,
        data_dir: Path,
    ) -> None:
        self.backend = backend
        self.transactions = transactions
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.jobs = JobManager()
        self.scans: dict[str, MachineCapabilityVector] = {}
        self.game_sessions: dict[str, dict[str, object]] = {}
        self.benchmarks: dict[str, dict[str, object]] = {}
        self.settings: dict[str, object] = {
            "dry_run": True,
            "language": "id-ID",
            "theme": "dark",
        }
        self.activity: list[dict[str, object]] = []
        self.game_controller = GameSessionController(dry_run=backend.dry_run)

    def _log_activity(self, category: str, message: str, **extra: object) -> None:
        """Record an activity event with timestamp."""
        now = datetime.now(tz=UTC)
        entry: dict[str, object] = {
            "category": category,
            "message": message,
            "timestamp": now.isoformat(),
            **extra,
        }
        self.activity.insert(0, entry)

    def scan_system(self) -> MachineCapabilityVector:
        vector = self.backend.scan_capabilities()
        self.scans[vector.scan_id] = vector
        self._log_activity("scan", "Pemindaian capability selesai.", scan_id=vector.scan_id)
        return vector

    def get_scan(self, scan_id: str) -> MachineCapabilityVector:
        if scan_id not in self.scans:
            raise KeyError("Hasil pemindaian tidak ditemukan.")
        return self.scans[scan_id]

    def recommendations(self, scan_id: str) -> list[dict[str, object]]:
        return [
            item.model_dump(mode="json") for item in build_recommendations(self.get_scan(scan_id))
        ]

    def scan_hardware(self) -> dict[str, object]:
        from ipan_optimizer.core.hardware_scanner import scan_hardware

        result = scan_hardware()
        self._log_activity("hardware_scan", "Scan hardware selesai.")
        return result.as_payload()

    def get_realtime_stats(self) -> dict[str, object]:
        from ipan_optimizer.adapters.windows.telemetry import read_telemetry

        sample = read_telemetry()
        return {
            "cpu_percent": sample.cpu_load_percent,
            "cpu_freq_mhz": sample.cpu_freq_mhz,
            "gpu_freq_mhz": sample.gpu_freq_mhz,
            "ram_used_mb": sample.ram_used_mb,
            "ram_percent": sample.ram_percent,
            "cpu_temp_c": sample.cpu_temp_c,
            "gpu_temp_c": sample.gpu_temp_c,
            "ssd_temp_c": sample.ssd_temp_c,
        }

    def start_game_session(self, profile_id: str, executable_id: str) -> dict[str, object]:
        controlled = self.game_controller.start(profile_id, executable_id)
        session_id = controlled.session_id
        session: dict[str, object] = {
            "session_id": session_id,
            "profile_id": profile_id,
            "executable_id": executable_id,
            "state": "DRY_RUN_ACTIVE",
            "message": "Sesi disimulasikan; tidak ada proses yang diluncurkan.",
        }
        self.game_sessions[session_id] = session
        self._log_activity(
            "game_session", f"Sesi gaming dimulai: {profile_id}.", session_id=session_id
        )
        return session

    def stop_game_session(self, session_id: str) -> dict[str, object]:
        session = self.game_sessions.get(session_id)
        if session is None:
            raise KeyError("Sesi game tidak ditemukan.")
        session["state"] = "RESTORED"
        session["message"] = "State sesi Dry Run dipulihkan."
        self.game_controller.stop(session_id)
        self._log_activity("game_session", "Sesi gaming dihentikan.", session_id=session_id)
        return session

    def discover_emulators(self) -> list[dict[str, object]]:
        return [
            {key: value for key, value in asdict(product).items()}
            for product in EmulatorDiscovery().discover()
        ]

    def start_benchmark(self, config: dict[str, object]) -> dict[str, object]:
        benchmark_id = str(uuid4())
        benchmark: dict[str, object] = {
            "benchmark_id": benchmark_id,
            "state": "GUIDED_READY",
            "config": config,
            "metrics": {},
            "message": "Belum diukur. Ikuti panduan run yang konsisten.",
        }
        self.benchmarks[benchmark_id] = benchmark
        self._log_activity("benchmark", "Benchmark dimulai.", benchmark_id=benchmark_id)
        return benchmark

    def compare_benchmarks(self, ids: list[str]) -> dict[str, object]:
        known = [self.benchmarks[item] for item in ids if item in self.benchmarks]
        return {
            "state": "INCONCLUSIVE",
            "message": "Tidak ada perubahan bermakna atau data run belum cukup.",
            "benchmarks": known,
        }

    def export_report(self, payload: dict[str, object]) -> str:
        report_id = str(uuid4())
        path = self.data_dir / f"diagnostic-{report_id}.json"
        safe = {
            "schema_version": 1,
            "dry_run": True,
            "options": payload,
            "scan_count": len(self.scans),
            "activity_count": len(self.activity),
        }
        path.write_text(json.dumps(safe, indent=2, ensure_ascii=False), encoding="utf-8")
        return str(path)

    _REMEMBER_FILE = "remember.json"

    def save_remember(
        self,
        username: str,
        password: str,
        license_key: str,
        expires_at: float,
    ) -> dict[str, object]:
        """Persist login credentials to disk so they survive app restarts."""
        data = {
            "username": username,
            "password": password,
            "license_key": license_key,
            "expires_at": expires_at,
        }
        path = self.data_dir / self._REMEMBER_FILE
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return {"saved": True}

    def load_remember(self) -> dict[str, object]:
        """Load persisted login data. Returns empty if expired or missing."""
        path = self.data_dir / self._REMEMBER_FILE
        if not path.exists():
            return {"username": "", "password": "", "license_key": "", "active": False}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"username": "", "password": "", "license_key": "", "active": False}
        import time

        expires_at = data.get("expires_at", 0)
        if not isinstance(expires_at, (int, float)) or expires_at <= time.time():
            return {"username": "", "password": "", "license_key": "", "active": False}
        return {
            "username": data.get("username", ""),
            "password": data.get("password", ""),
            "license_key": data.get("license_key", ""),
            "active": True,
        }
