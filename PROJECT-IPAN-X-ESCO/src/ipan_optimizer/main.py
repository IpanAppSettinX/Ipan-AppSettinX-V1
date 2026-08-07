from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from ipan_optimizer.adapters.dry_run import DryRunWindowsBackend
from ipan_optimizer.adapters.windows.backend import WindowsReadOnlyBackend
from ipan_optimizer.adapters.windows.real_backend import REAL_WRITE_ENV
from ipan_optimizer.app.api import ApiBridge
from ipan_optimizer.app.service import OptimizerService
from ipan_optimizer.core.journal import RecoveryJournal
from ipan_optimizer.core.transactions import TransactionManager
from ipan_optimizer.domain.models import MachineCapabilityVector
from ipan_optimizer.logging_config import configure_logging
from ipan_optimizer.persistence.database import Database
from ipan_optimizer.ports.windows import WindowsBackend
from ipan_optimizer.privileged.runner import execute_plan_file


@dataclass(frozen=True)
class Runtime:
    bridge: ApiBridge
    data_dir: Path
    database: Database


def default_data_dir() -> Path:
    override = os.environ.get("IPAN_OPTIMIZER_DATA_DIR")
    if override:
        return Path(override).resolve()
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "IPAN Optimizer"
    return Path.cwd() / ".ipan-optimizer-data"


def build_backend(
    *,
    capabilities: MachineCapabilityVector,
    read_only: WindowsReadOnlyBackend,
) -> WindowsBackend:
    """Select the backend.

    Default: Dry Run overlay (copy-on-write, host never mutated). When the
    documented release gate is explicitly opened with
    ``IPAN_ENABLE_REAL_WRITE=1``, the narrow real-write HKCU backend is used
    instead. Every other environment keeps the safe default.
    """
    if os.environ.get(REAL_WRITE_ENV) == "1":
        from ipan_optimizer.adapters.windows.real_backend import RealWindowsBackend

        print(f"[Ipan AppSettinX] Real write mode AKTIF ({REAL_WRITE_ENV}=1, kategori HKCU).")
        return RealWindowsBackend(read_only=read_only)
    return DryRunWindowsBackend(capabilities=capabilities, source=read_only)


def create_runtime(data_dir: Path | None = None) -> Runtime:
    root = (data_dir or default_data_dir()).resolve()
    root.mkdir(parents=True, exist_ok=True)
    configure_logging(root / "logs" / "ipan-optimizer.jsonl")
    database = Database(root / "ipan-optimizer.sqlite3")
    database.migrate()
    read_only = WindowsReadOnlyBackend()
    capabilities = read_only.scan_capabilities()
    backend = build_backend(capabilities=capabilities, read_only=read_only)
    journal = RecoveryJournal(root / "recovery" / "transactions.jsonl")
    transactions = TransactionManager(backend, journal)
    service = OptimizerService(backend, transactions, root / "exports")
    return Runtime(
        bridge=ApiBridge(service),
        data_dir=root,
        database=database,
    )


def cleanup_orphan_meipass(max_age_hours: float = 24.0, limit: int = 12) -> int:
    """Hapus folder ``_MEIxxxxx`` yatim (orphan) peninggalan force-close.

    PyInstaller one-file mengekstrak bundle ke ``%TEMP%\\_MEI<pid>`` dan
    membersihkannya saat proses keluar normal. Bila pengguna men-force-close
    aplikasi (Task Manager / ``taskkill /f`` setelah hang), bootloader mati
    sebelum sempat menghapus folder itu — muncul log
    "failed to remove temporary directory ...\\_MEI9242". Sisa folder juga
    bisa memuat file ``index.html`` frontend versi lama yang kedaluwarsa;
    inilah sumber ``ERR_FILE_NOT_FOUND`` saat aplikasi dijalankan ulang.

    Fungsi ini hanya menyentuh folder milik aplikasi ini: berawalan
    ``_MEI``, berada di direktori temp OS yang aktif (dinamis — tidak ada
    hardcode drive letter), usianya lebih tua dari ``max_age_hours`` (aman:
    instance yang sedang berjalan tidak akan tersentuh), dan tidak sedang
    dipakai proses lain (rename-gagal = terkunci = dilewati). Mengembalikan
    jumlah folder yang berhasil dihapus.
    """
    if sys.platform != "win32":
        return 0
    import contextlib
    import shutil
    import tempfile
    import time

    try:
        temp_root = Path(tempfile.gettempdir())
    except Exception:  # pragma: no cover - defensif
        return 0
    own = Path(getattr(sys, "_MEIPASS", "")).resolve() if getattr(sys, "_MEIPASS", None) else None
    cutoff = time.time() - max_age_hours * 3600
    removed = 0
    try:
        candidates = sorted(
            (p for p in temp_root.glob("_MEI*") if p.is_dir()),
            key=lambda p: p.stat().st_mtime,
        )
    except OSError:  # pragma: no cover - defensif
        return 0
    for candidate in candidates:
        if removed >= limit:
            break
        try:
            if candidate.stat().st_mtime > cutoff:
                continue  # terlalu baru: bisa jadi milik instance yang sedang hidup
            if own is not None and candidate.resolve() == own:
                continue  # jangan pernah hapus folder tempat kita berjalan
        except OSError:
            continue
        # Rename-dulu sebagai uji kunci: bila gagal, folder masih dipakai
        # proses lain -> lewati dengan aman.
        probe = candidate.with_name(candidate.name + ".cleanup")
        try:
            candidate.rename(probe)
        except OSError:
            continue
        with contextlib.suppress(OSError):
            shutil.rmtree(probe, ignore_errors=True)
        if probe.exists():  # rmtree gagal sebagian -> kembalikan nama aslinya
            with contextlib.suppress(OSError):
                probe.rename(candidate)
        else:
            removed += 1
    return removed


def frontend_path() -> Path:
    # Di dalam bundle PyInstaller, __file__ tidak menunjuk ke file nyata di
    # disk (kode Python dikemas dalam arsip PYZ). Asset frontend disalin ke
    # ``sys._MEIPASS/ipan_optimizer/frontend``, jadi gunakan itu. Di luar
    # bundle (mode dev), fallback ke lokasi relatif ``__file__`` seperti biasa.
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass) / "ipan_optimizer" / "frontend" / "index.html"
    return Path(__file__).resolve().parent / "frontend" / "index.html"


def run_window(runtime: Runtime, *, debug: bool = False) -> None:
    import webview

    remote_debugging_port = os.environ.get("IPAN_OPTIMIZER_REMOTE_DEBUGGING_PORT")
    if debug and remote_debugging_port:
        webview.settings["REMOTE_DEBUGGING_PORT"] = int(remote_debugging_port)
    window = webview.create_window(
        "Ipan AppSettinX",
        url=frontend_path().as_uri(),
        js_api=runtime.bridge,
        width=1280,
        height=800,
        min_size=(1024, 700),
        resizable=True,
        text_select=True,
        frameless=True,
        easy_drag=False,
    )
    runtime.bridge._window = window
    webview.start(debug=debug, gui="edgechromium")


def ensure_runtime_requirements(*, headless: bool) -> bool:
    """Ensure host prerequisites (WebView2) are met before starting the UI.

    Returns ``True`` when the WebView2 runtime is installed (or was installed
    by the bundled Microsoft bootstrapper), ``False`` when it is still missing
    and the UI cannot be started safely.

    In ``--no-window`` mode this only performs a non-invasive detection check
    and never launches the bootstrapper.
    """
    from ipan_optimizer.app.webview2_runtime import (
        ensure_webview2,
        fixed_runtime_available,
        fixed_runtime_path,
    )

    # When the developer bundles a Fixed Version Runtime, point pywebview at
    # it before any window is created. This skips system detection entirely
    # and works on Windows mod where Evergreen runtime is unavailable.
    if fixed_runtime_available():
        import webview

        webview.settings["WEBVIEW2_RUNTIME_PATH"] = str(fixed_runtime_path())
        _grant_appcontainer_access(fixed_runtime_path())
        return True

    return ensure_webview2(headless=headless)


def _grant_appcontainer_access(runtime_dir: Path) -> None:
    """Grant AppContainer SIDs read access to the bundled Fixed Version runtime.

    WebView2 renderer runs under an AppContainer and needs read access to the
    runtime folder. On Windows 10 (Fixed Version 120+) this ACL entry is
    required; without it the renderer fails to initialise silently. This is a
    no-op on non-Windows or when icacls is unavailable.
    """
    if sys.platform != "win32":
        return
    import contextlib
    import shutil
    import subprocess

    for sid in ("*S-1-15-2-2", "*S-1-15-2-1"):
        with contextlib.suppress(FileNotFoundError, OSError):
            subprocess.run(  # noqa: S603 - icacls is a signed Windows system binary
                [
                    shutil.which("icacls") or "icacls",
                    str(runtime_dir),
                    "/grant",
                    f"{sid}:(OI)(CI)(RX)",
                ],
                check=False,
                shell=False,
                capture_output=True,
            )


def main() -> int:
    parser = argparse.ArgumentParser(description="Ipan AppSettinX")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Semua perubahan disimulasikan (selalu aktif pada build ini).",
    )
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--no-window", action="store_true")
    parser.add_argument(
        "--apply-plan",
        type=str,
        default=None,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--result",
        type=str,
        default=None,
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args()
    if args.apply_plan:
        if not args.result:
            return 2
        # Elevated one-shot mode: applies a signed tweak plan and writes the
        # results JSON, then exits. Never starts the WebView2 UI here.
        return execute_plan_file(Path(args.apply_plan), Path(args.result))
    del args.dry_run
    # Bersihkan folder _MEI yatim peninggalan force-close SEBELUM membuka UI.
    # Ini mencegah ERR_FILE_NOT_FOUND (frontend usang di _MEI lama) dan
    # pesan "failed to remove temporary directory" pada log.
    cleanup_orphan_meipass()
    runtime = create_runtime()
    if not args.no_window:
        if not ensure_runtime_requirements(headless=False):
            print(
                "[Ipan AppSettinX] WebView2 Runtime belum tersedia. "
                "Pasang Microsoft Edge WebView2 Runtime Evergreen resmi, "
                "lalu jalankan aplikasi kembali.",
                file=sys.stderr,
            )
            return 3
        run_window(runtime, debug=args.debug)
    else:
        ensure_runtime_requirements(headless=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
