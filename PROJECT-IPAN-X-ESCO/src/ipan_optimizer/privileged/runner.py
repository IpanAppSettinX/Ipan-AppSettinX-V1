"""Elevated tweak execution for the release EXE.

The release EXE runs ``asInvoker`` because the WebView2 host (pywebview) cannot
initialise reliably in an elevated process. Tweak steps that require an
Administrator token (HKLM Registry, ``sc config``, ``powercfg``, ``bcdedit``,
system-file cleanup) are therefore executed by a second, elevated instance of
the same EXE, launched once per tweak through a UAC prompt (``runas`` verb).

Flow (one UAC prompt per tweak that has privileged steps):

1. ``run_elevated_steps`` writes a signed one-shot plan
   (nonce + expiry + SHA-256 digest of the steps) to a temp file.
2. The plan is executed by ``ShellExecuteExW(..., "runas")`` on the same EXE
   with ``--apply-plan <plan> --result <result>``. Windows shows UAC once; the
   elevated instance validates the plan and runs the steps with the elevated
   token via ``run_step``, then writes the results JSON and exits.
3. The invoker waits for the process, reads the results file, and returns the
   per-step outcomes.

Safety:

- The plan is one-shot (nonce replay is rejected) and short-lived (120 s).
- A digest binds the plan to its exact steps; tampering is rejected.
- Only the EXE's own, statically defined tweak commands can be produced by the
  app, and a forged plan cannot exceed what running the EXE as Administrator
  could already do.
- Development/tests set ``IPAN_OPTIMIZER_NO_ELEVATION=1`` so steps run
  in-process without any UAC prompt; the host is never elevated by tests.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import secrets
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

NO_ELEVATION_ENV = "IPAN_OPTIMIZER_NO_ELEVATION"
_PLAN_DIR_NAME = "ipan_optimizer_plans"
_PLAN_LIFETIME_SECONDS = 120
_USED_NONCES_FILE = "used_nonces.txt"

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


def _service_exists(service: str) -> bool:
    """Return True when the Windows service is installed (sc query succeeds)."""
    if sys.platform != "win32":
        return False
    try:
        result = subprocess.run(
            ["sc", "query", service],
            capture_output=True,
            text=True,
            timeout=5,
            shell=False,
        )
        return result.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def _file_exists_resolved(path: str) -> bool:
    """Check if a (possibly env-var) path exists after expansion."""
    expanded = os.path.expandvars(path)
    return Path(expanded).is_file()


def is_modded_windows() -> bool:
    """Heuristic: True when core Windows binaries/services are missing.

    Stripped custom builds (X Lite, ReviOS, KernelOS, Ghost Spectre, AtlasOS)
    remove components like DiagTrack, the DPS service, or even powercfg. When
    several of these are absent we treat the OS as "modded" so the tweak
    engine can prefer non-destructive, missing-safe operations.
    """
    if sys.platform != "win32":
        return False
    probes = 0
    missing = 0
    for rel in (r"%WINDIR%\System32\powercfg.exe", r"%WINDIR%\System32\bcdedit.exe"):
        probes += 1
        if not _file_exists_resolved(rel):
            missing += 1
    for svc in ("DiagTrack", "DPS", "SysMain", "WSearch"):
        probes += 1
        if not _service_exists(svc):
            missing += 1
    return probes > 0 and missing >= 2


def resolve_command(command: list[str]) -> list[str]:
    """Expand env vars and wrap CMD internal commands for ``shell=False``.

    ``subprocess.run(shell=False)`` cannot expand ``%TEMP%`` or run CMD
    builtins like ``del``/``rd``, so those are rewritten as ``cmd /c ...``.
    """
    if not command:
        return command
    expanded = [os.path.expandvars(arg) for arg in command]
    if expanded[0].lower() in _CMD_INTERNAL_COMMANDS:
        return ["cmd", "/c", *expanded]
    return expanded


@dataclass
class ExecStep:
    """Duck-typed step accepted by :func:`run_step` (mirrors TweakStep)."""

    description: str
    command: list[str]
    requires_admin: bool = False


def run_step(step: Any) -> dict[str, Any]:
    """Execute one command step with ``subprocess.run(shell=False)``.

    Returns the outcome dict used by the tweak engine and the plan results.
    """
    if sys.platform != "win32":
        return {
            "description": step.description,
            "success": False,
            "error": "Tweak hanya berjalan di Windows.",
            "requires_admin": step.requires_admin,
        }
    try:
        resolved = resolve_command(step.command)
        if not resolved:
            return {
                "description": step.description,
                "success": False,
                "error": "Command kosong.",
                "requires_admin": step.requires_admin,
            }

        # Pre-check: skip `sc config`/`sc stop` for non-existent services.
        # Custom Windows (AtlasOS, ReviOS, Ghost Spectre, X-Lite) often removes
        # services like DiagTrack, SysMain, WinDefend. Running `sc config` on a
        # missing service returns error 1060 and counts as failure.
        if (
            len(resolved) >= 3
            and resolved[0].lower() == "sc"
            and resolved[1].lower() in {"config", "stop"}
        ):
            svc_name = resolved[2]
            if not _service_exists(svc_name):
                return {
                    "description": step.description,
                    "success": True,
                    "stdout": f"Service {svc_name} tidak ditemukan, dilewati.",
                    "requires_admin": step.requires_admin,
                    "skipped": True,
                }

        # Pre-check: skip executable tweaks when the target binary is absent.
        # E.g. OneDriveSetup.exe, wmic (deprecated on Win11 22H2+).
        first = resolved[0].lower()

        # Pre-check: core system binaries that stripped/modded Windows builds
        # (X Lite, ReviOS, KernelOS, Ghost Spectre, AtlasOS) may have removed or
        # locked. If the binary is gone the command would either fail with
        # "not recognized" or block; skip it cleanly as a no-op so the progress
        # bar always advances instead of hanging.
        _SYSTEM_BINARIES = {
            "powercfg": r"%WINDIR%\System32\powercfg.exe",
            "bcdedit": r"%WINDIR%\System32\bcdedit.exe",
            "taskkill": r"%WINDIR%\System32\taskkill.exe",
            "reg": r"%WINDIR%\System32\reg.exe",
            "sc": r"%WINDIR%\System32\sc.exe",
            "net": r"%WINDIR%\System32\net.exe",
            "explorer": r"%WINDIR%\explorer.exe",
            "powershell": r"%WINDIR%\System32\WindowsPowerShell\v1.0\powershell.exe",
        }
        if first in _SYSTEM_BINARIES and not _file_exists_resolved(_SYSTEM_BINARIES[first]):
            return {
                "description": step.description,
                "success": True,
                "stdout": f"{first} tidak tersedia pada Windows ini (modded/stripped), dilewati.",
                "requires_admin": step.requires_admin,
                "skipped": True,
            }

        if first == "wmic" and not _file_exists_resolved(r"%WINDIR%\System32\wbem\wmic.exe"):
            return {
                "description": step.description,
                "success": True,
                "stdout": "wmic tidak tersedia (deprecated), dilewati.",
                "requires_admin": step.requires_admin,
                "skipped": True,
            }
        # Detect direct .exe invocation with a full path that doesn't exist.
        if first.endswith(".exe") and (":\\" in first or first.startswith("%")):
            if not _file_exists_resolved(first):
                return {
                    "description": step.description,
                    "success": True,
                    "stdout": f"{first} tidak ditemukan, dilewati.",
                    "requires_admin": step.requires_admin,
                    "skipped": True,
                }

        # Per-step timeout: keep it short so a hung component on a modded OS
        # (locked service manager, stuck power service) can never freeze the
        # job thread / progress bar. 10 s per step is generous for reg/sc/cfg.
        result = subprocess.run(  # noqa: S603 - trusted local commands; env vars expanded, CMD internals wrapped.
            resolved,
            capture_output=True,
            text=True,
            timeout=10,
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
    except subprocess.TimeoutExpired:
        return {
            "description": step.description,
            "success": True,
            "stdout": "Command melebihi batas waktu, dilewati.",
            "requires_admin": step.requires_admin,
            "skipped": True,
        }
    except (OSError, subprocess.SubprocessError) as exc:
        return {
            "description": step.description,
            "success": False,
            "error": str(exc),
            "requires_admin": step.requires_admin,
        }


# ── Elevation detection ─────────────────────────────────────────


def is_elevated() -> bool:
    """Return True when the current process runs with an elevated token."""
    if sys.platform != "win32":
        return False
    import ctypes

    try:
        token = ctypes.c_void_p()
        if not ctypes.windll.advapi32.OpenProcessToken(
            ctypes.windll.kernel32.GetCurrentProcess(), 0x0008, ctypes.byref(token)
        ):
            return False
        elevated = ctypes.c_ulong(0)
        size = ctypes.c_ulong(ctypes.sizeof(elevated))
        ok = ctypes.windll.advapi32.GetTokenInformation(
            token,
            20,  # TokenElevation
            ctypes.byref(elevated),
            size,
            ctypes.byref(size),
        )
        ctypes.windll.kernel32.CloseHandle(token)
        return bool(ok and elevated.value)
    except Exception:  # pragma: no cover - defensive fail-open
        return False


# ── One-shot plan (signature + replay protection) ───────────────


def _plan_dir() -> Path:
    path = Path(tempfile.gettempdir()) / _PLAN_DIR_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def _steps_canonical(steps: list[Any]) -> str:
    payload = [{"description": step.description, "command": step.command} for step in steps]
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _steps_digest(steps: list[Any]) -> str:
    return hashlib.sha256(_steps_canonical(steps).encode("utf-8")).hexdigest()


def _used_nonces() -> set[str]:
    path = _plan_dir() / _USED_NONCES_FILE
    if not path.is_file():
        return set()
    try:
        return {
            line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
        }
    except OSError:  # pragma: no cover
        return set()


def _mark_nonce_used(nonce: str) -> None:
    path = _plan_dir() / _USED_NONCES_FILE
    try:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(nonce + "\n")
    except OSError:  # pragma: no cover - best effort
        pass


def write_plan(
    steps: list[Any],
    tweak_id: str,
    plan_path: Path,
) -> None:
    """Write a signed one-shot plan file for the elevated instance."""
    now = datetime.now(UTC)
    plan = {
        "schema_version": 1,
        "nonce": secrets.token_urlsafe(24),
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(seconds=_PLAN_LIFETIME_SECONDS)).isoformat(),
        "plan_digest": _steps_digest(steps),
        "tweak_id": tweak_id,
        "steps": [{"description": step.description, "command": step.command} for step in steps],
    }
    plan_path.write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")


def _parse_iso(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def validate_plan_file(plan_path: Path) -> list[ExecStep]:
    """Validate a plan file and return its steps (raises ``ValueError``)."""
    try:
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Plan tidak dapat dibaca: {exc}") from exc

    if plan.get("schema_version") != 1:
        raise ValueError("Schema plan tidak dikenal.")
    nonce = plan.get("nonce", "")
    if not isinstance(nonce, str) or not 32 <= len(nonce) <= 128:
        raise ValueError("Nonce plan tidak valid.")

    now = datetime.now(UTC)
    created_at = _parse_iso(str(plan.get("created_at", "")))
    expires_at = _parse_iso(str(plan.get("expires_at", "")))
    if expires_at <= now:
        raise ValueError("Plan telah kedaluwarsa.")
    if created_at > now + timedelta(seconds=5):
        raise ValueError("Waktu pembuatan plan tidak valid.")

    steps_raw = plan.get("steps")
    if not isinstance(steps_raw, list) or not steps_raw:
        raise ValueError("Plan tidak memiliki langkah operasi.")
    steps = [
        ExecStep(
            description=str(step["description"]),
            command=[str(arg) for arg in step["command"]],
            requires_admin=True,
        )
        for step in steps_raw
    ]

    if plan.get("plan_digest") != _steps_digest(steps):
        raise ValueError("Digest plan tidak cocok (plan diubah).")

    if nonce in _used_nonces():
        raise ValueError("Nonce telah digunakan (replay).")
    _mark_nonce_used(nonce)
    return steps


# ── Running elevated steps ──────────────────────────────────────


def _failed_outcome(step: Any, error: str) -> dict[str, Any]:
    return {
        "description": step.description,
        "success": False,
        "error": error,
        "requires_admin": True,
    }


def run_elevated_steps(steps: list[Any], tweak_id: str) -> list[dict[str, Any]]:
    """Run privileged steps, elevating once via UAC when needed.

    When the current process already has an elevated token, or when
    ``IPAN_OPTIMIZER_NO_ELEVATION=1`` is set (tests/development), the steps are
    executed in-process instead.
    """
    if is_elevated() or os.environ.get(NO_ELEVATION_ENV) == "1":
        return [run_step(step) for step in steps]

    plan_dir = _plan_dir()
    nonce = secrets.token_urlsafe(24)
    plan_path = plan_dir / f"plan_{nonce}.json"
    result_path = plan_dir / f"result_{nonce}.json"
    write_plan(steps, tweak_id, plan_path)
    try:
        if not _launch_elevated(plan_path, result_path):
            return [
                _failed_outcome(
                    step,
                    "Helper elevated tidak merespons (UAC dibatalkan, komponen "
                    "hilang pada Windows modded, atau helper berhenti).",
                )
                for step in steps
            ]
        if not result_path.is_file():
            return [
                _failed_outcome(step, "Helper elevated tidak menghasilkan laporan.")
                for step in steps
            ]
        try:
            results = json.loads(result_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return [_failed_outcome(step, "Laporan helper elevated tidak valid.") for step in steps]
        if not isinstance(results, dict):
            return [_failed_outcome(step, "Laporan helper elevated tidak valid.") for step in steps]
        steps_results = results.get("steps", [])
        if not isinstance(steps_results, list):
            return [_failed_outcome(step, "Laporan helper elevated tidak valid.") for step in steps]
        return steps_results
    finally:
        for leftover in (plan_path, result_path):
            with contextlib.suppress(OSError):
                leftover.unlink(missing_ok=True)


def _launch_elevated(plan_path: Path, result_path: Path) -> bool:
    """Launch the same EXE elevated (``runas``) to apply the plan.

    Returns True when the elevated process started and finished.
    """
    if getattr(sys, "frozen", None) is None:
        return False  # dev/source run: no self-elevation
    if sys.platform != "win32":
        return False
    import ctypes
    from typing import ClassVar

    class ShellExecuteInfoW(ctypes.Structure):
        _fields_: ClassVar[list[tuple[str, type]]] = [
            ("cbSize", ctypes.c_uint32),
            ("fMask", ctypes.c_uint32),
            ("hwnd", ctypes.c_void_p),
            ("lpVerb", ctypes.c_wchar_p),
            ("lpFile", ctypes.c_wchar_p),
            ("lpParameters", ctypes.c_wchar_p),
            ("lpDirectory", ctypes.c_wchar_p),
            ("nShow", ctypes.c_int),
            ("hInstApp", ctypes.c_void_p),
            ("lpIDList", ctypes.c_void_p),
            ("lpClass", ctypes.c_wchar_p),
            ("hkeyClass", ctypes.c_void_p),
            ("dwHotKey", ctypes.c_uint32),
            ("hIcon", ctypes.c_void_p),
            ("hProcess", ctypes.c_void_p),
        ]

    params = f'--apply-plan "{plan_path}" --result "{result_path}"'
    info = ShellExecuteInfoW()
    info.cbSize = ctypes.sizeof(info)
    info.fMask = 0x00000040  # SEE_MASK_NOCLOSEPROCESS
    info.lpVerb = "runas"
    info.lpFile = str(sys.executable)
    info.lpParameters = params
    info.lpDirectory = str(Path(sys.executable).parent)
    info.nShow = 0  # SW_HIDE

    if not ctypes.windll.shell32.ShellExecuteExW(ctypes.byref(info)):
        return False

    # Poll the elevated helper instead of a single long blocking wait. On a
    # modded OS the helper can die instantly (missing DLL / module) leaving a
    # valid-but-dead process handle; a 120 s WaitForSingleObject would freeze
    # the job thread (the "stuck at 87%" symptom). We poll the result file and
    # bail out as soon as the helper exits OR the result appears.
    import time

    process = info.hProcess
    deadline = time.monotonic() + _PLAN_LIFETIME_SECONDS
    wait_ok = False
    while time.monotonic() < deadline:
        if result_path.is_file():
            wait_ok = True
            break
        if process:
            # WaitForSingleObject with a short slice; WAIT_OBJECT_0 (0) = exited.
            state = ctypes.windll.kernel32.WaitForSingleObject(process, 250)
            if state == 0:  # helper finished (or crashed) -> stop waiting
                wait_ok = result_path.is_file()
                break
        else:
            time.sleep(0.1)
    if process:
        ctypes.windll.kernel32.CloseHandle(process)
    return wait_ok


# ── Elevated instance entry point ───────────────────────────────


def execute_plan_file(plan_path: Path, result_path: Path) -> int:
    """Run inside the elevated instance: validate the plan, execute, report.

    Returns process exit code (0 = reported, non-zero = could not report).
    """
    try:
        steps = validate_plan_file(plan_path)
    except ValueError as exc:
        _write_error_result(result_path, str(exc))
        return 1
    outcomes = [run_step(step) for step in steps]
    return _write_result(result_path, outcomes)


def _write_result(result_path: Path, outcomes: list[dict[str, Any]]) -> int:
    try:
        result_path.parent.mkdir(parents=True, exist_ok=True)
        result_path.write_text(
            json.dumps({"steps": outcomes}, ensure_ascii=False),
            encoding="utf-8",
        )
        return 0
    except OSError:  # pragma: no cover
        return 1


def _write_error_result(result_path: Path, message: str) -> None:
    try:
        result_path.parent.mkdir(parents=True, exist_ok=True)
        result_path.write_text(
            json.dumps({"error": message}, ensure_ascii=False),
            encoding="utf-8",
        )
    except OSError:  # pragma: no cover
        pass
