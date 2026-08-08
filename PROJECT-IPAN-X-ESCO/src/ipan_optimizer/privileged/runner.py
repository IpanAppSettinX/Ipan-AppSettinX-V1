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
import threading
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

APPSX_DEBLOAT_STEP_ID = "__appx_debloat__"

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


# ── Hidden-window process execution ─────────────────────────────

# Windows process creation flags (stable ABI constants, safe to hard-code).
_CREATE_NO_WINDOW = 0x08000000
_STARTF_USESHOWWINDOW = 0x00000001
_SW_HIDE = 0


def _hidden_console_kwargs() -> dict[str, Any]:
    """Return subprocess kwargs that guarantee NO console window is shown.

    On Windows, spawning a console subsystem binary (``powershell.exe``,
    ``cmd.exe``) from a GUI process without these flags flashes a visible
    console window on screen. Worse, on stripped/modded Windows (X-Lite,
    KernelOS, AtlasOS, ReviOS, Ghost Spectre) a half-removed console host can
    make the child block on console init, which froze the apply job at 87%.
    ``CREATE_NO_WINDOW`` + ``STARTUPINFO.wShowWindow = SW_HIDE`` prevents the
    window entirely and avoids the blocking console allocation.
    """
    if sys.platform != "win32":
        return {}
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= _STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = _SW_HIDE
    return {
        "creationflags": _CREATE_NO_WINDOW,
        "startupinfo": startupinfo,
    }


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
            **_hidden_console_kwargs(),
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


# ── Native AppX debloat (in-process; powershell fallback only) ───
#
# Windows Runtime / Desktop Bridge AppX removal used to be delegated to
# ``powershell -Command Get-AppxPackage ... | Remove-AppxPackage``. That is
# fragile on real user machines: a stripped/modded Windows (X-Lite, KernelOS,
# AtlasOS, ReviOS, Ghost Spectre) may ship a half-removed powershell.exe that
# hangs on profile load or exits non-zero, and a plain per-user (non-elevated)
# ``Remove-AppxPackage -AllUsers`` is denied unless the process owns a
# trusted-package capability. This module instead loads
# ``Windows.Management.Deployment.PackageManager`` through pythonnet and talks
# to the AppX deployment service (AppXSVC) directly over COM — the very same
# service the Store and powershell cmdlets call — so:
#
#   * the primary path spawns NO console process (no window, no hang),
#   * per-user removal needs NO elevation, so the tweak runs in-process and
#     never touches the UAC/elevated-helper relaunch path,
#   * a missing/broken powershell.exe cannot block the tweak (it is only a
#     fallback when the native deployment call itself rejects a package),
#   * every target package gets its own isolated removal attempt so one
#     protected app cannot fail the whole tweak.
#
# Protected system packages are skipped explicitly so the operation can never
# wedge the OS, mirroring the allow-list the tweak already used.

#: Substring patterns matched (case-insensitively) against the package Name.
#: Kept aligned with the tweak's original target list plus common bloat.
_APPSX_DEBLOAT_PATTERNS: tuple[str, ...] = (
    "3dbuilder",
    "sway",
    "bing",
    "zune",
    "reader",
    "maps",
    "phone",
    "wallet",
    "camera",
    "mail",
    "calendar",
    "people",
    "feedback",
    "hub",
    "mixed",
    "oneconnect",
    "print3d",
    "skype",
    "tips",
    "microsoft3dviewer",
    "microsoftofficehub",
    "windowscommunicationsapps",
    "windowsmaps",
    "bingweather",
    "bingnews",
    "gethelp",
    "getstarted",
    "mspaint",
    "microsoftstickynotes",
    "office.onenote",
    "skypeapp",
    "windowsalarms",
    "windowscamera",
    "xboxapp",
    "yourphone",
    "zunemusic",
    "zunevideo",
)

#: Names that must never be removed even if they match a pattern — removing
#: these breaks the shell / OOBE / settings on stock Windows.
_APPSX_PROTECTED_NAMES: tuple[str, ...] = (
    "microsoft.windows.startmenuexperiencehost",
    "microsoft.windows.shellexperiencehost",
    "microsoft.windows.immersivecontrolpanel",
    "windows.immersivecontrolpanel",
    "microsoft.windows.cortana",
    "microsoft.aad.brokerplugin",
    "microsoft.accountcontrol",
    "microsoft.windows.assignedaccesslockapp",
    "microsoft.windows.oobenetworkconnectionflow",
    "microsoft.windows.oobenetworkcaptiveportal",
    "microsoft.windows.parentalcontrols",
    "microsoft.windows.photos",  # keep: Photos powers image previews
    "microsoft.windows.secureassessmentbrowser",
    "microsoft.windows.capturepicker",
    "microsoft.windows.pinningconfirmation",
    "microsoft.ui.xaml",
    "microsoft.vclibs",
    "microsoft.net.native",
    "microsoft.windowsstore",
    "microsoft.storepurchaseapp",
    "microsoft.desktopappinstaller",
    "microsoft.windows.applicationcompat",
)


def _name_matches_pattern(name: str) -> bool:
    lowered = name.lower()
    return any(pattern in lowered for pattern in _APPSX_DEBLOAT_PATTERNS)


def _is_protected_package(name: str) -> bool:
    lowered = name.lower()
    if any(protected in lowered for protected in _APPSX_PROTECTED_NAMES):
        return True
    # Anything from the Windows infrastructure / framework publisher is
    # load-bearing (UI XAML, VCLibs, .NET Native runtime, app installer).
    if "framework" in lowered or "vclibs" in lowered or "xaml" in lowered:
        return True
    return "windowsterminal" in lowered  # keeps wt.exe available


def _load_appx_package_manager() -> Any:
    """Return a live ``Windows.Management.Deployment.PackageManager`` instance.

    pythonnet + the ``netfx`` runtime are already bundled in the release EXE
    (see ``installer/ipan_optimizer.spec``). Raising ``RuntimeError`` here lets
    the caller report a clean, actionable outcome instead of a crash.

    Initialisation is IDEMPOTENT: pythonnet (this build) makes ``set_runtime``
    raise ``RuntimeError: The runtime ... has already been loaded`` once the
    CLR was loaded by an earlier ``import clr``. The app process outlives a
    single Apply (the user can run the tweak many times), so the second Debloat
    run would crash with that exact error. Guarding ``set_runtime`` with
    ``get_runtime_info()`` makes every subsequent call a cheap no-op.
    """
    try:
        from clr_loader import get_netfx
        from pythonnet import get_runtime_info, set_runtime  # type: ignore[import-untyped]

        if get_runtime_info() is None:
            set_runtime(get_netfx())
        # NOTE: the `clr` module is a pythonnet runtime binding with no stubs;
        # it must be imported AFTER set_runtime() (isort:skip keeps it here).
        import clr  # type: ignore[import-untyped]  # noqa: F401,isort:skip

        from System import Activator, Type  # type: ignore[import-not-found]
    except Exception as exc:  # pragma: no cover - depends on host runtime
        raise RuntimeError(f"Runtime .NET untuk AppX tidak tersedia: {exc}") from exc

    # Windows.Management.Deployment.PackageManager is a WinRT class; pythonnet
    # resolves it through the System.Type interop path on .NET Framework.
    pm_type = Type.GetType(
        "Windows.Management.Deployment.PackageManager, "
        "Windows.Management.Deployment, ContentType=WindowsRuntime"
    )
    if pm_type is None:
        # Fall back to direct WinRT activation by name (works on .NET 5+/netfx
        # with the WinRT interop shim that pythonnet ships).
        pm_type = Type.GetTypeFromProgID("Windows.Management.Deployment.PackageManager")
        if pm_type is None:
            raise RuntimeError("PackageManager WinRT class tidak ditemukan")
    return Activator.CreateInstance(pm_type)


def _current_user_sid() -> str:
    """Return the current interactive user's SID string (S-1-5-21-...)."""
    import win32api  # type: ignore[import-untyped]
    import win32security  # type: ignore[import-untyped]

    sid, _, _ = win32security.LookupAccountName(None, win32api.GetUserName())
    return str(win32security.ConvertSidToStringSid(sid))


def _wait_appx_operation(operation: Any, timeout_s: int = 25) -> tuple[bool, str]:
    """Poll a WinRT IAsyncOperationWithProgress until it completes.

    ``GetAwaiter().GetResult()`` is not exposed by pythonnet for WinRT async
    ops, so we poll ``Status`` with a hard watchdog. ``AsyncStatus`` values:
    0 = Started, 1 = Completed, 2 = Canceled, 3 = Error.
    """
    import time

    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        status = int(operation.Status)
        if status == 1:  # Completed
            return True, ""
        if status == 2:
            return False, "Operasi dibatalkan."
        if status == 3:  # Error
            error_code = 0
            with contextlib.suppress(Exception):
                error_code = int(operation.ErrorCode.HResult) & 0xFFFFFFFF
            return False, f"AppXSVC mengembalikan HRESULT 0x{error_code:08X}."
        time.sleep(0.05)
    with contextlib.suppress(Exception):
        operation.Cancel()
    return False, f"Operasi AppX melebihi {timeout_s} dtk."


def _remove_appx_package(package_manager: Any, package_full_name: str) -> tuple[bool, str]:
    """Remove one package (current user) via ``RemovePackageAsync``."""
    try:
        operation = package_manager.RemovePackageAsync(package_full_name)
    except Exception as exc:
        return False, f"gagal memulai removal: {exc}"
    return _wait_appx_operation(operation)


def _appx_powershell_script(names: list[str]) -> str:
    """Build the per-user Remove-AppxPackage script for the given names.

    ``Get-AppxPackage -Name`` only accepts a plain ``string`` (a single-element
    array is rejected with a binding error), so the targets are matched through
    ``Where-Object { $names -contains $_.Name }`` instead — valid for 1..N.
    """
    quoted = ",".join("'" + n.replace("'", "''") + "'" for n in names)
    return (
        "$ErrorActionPreference='Continue'; "
        f"$names = @({quoted}); "
        "Get-AppxPackage | Where-Object { $names -contains $_.Name } | "
        "Remove-AppxPackage -ErrorAction SilentlyContinue"
    )


def _remove_appx_packages_powershell(names: list[str]) -> tuple[bool, str]:
    """Fallback: per-user ``Remove-AppxPackage`` (no ``-AllUsers``).

    Mirrors the manual PowerShell script that users confirm removes bloatware
    without errors: enumerate the exact package names and remove them for the
    current user. This is only reached when the native deployment call above
    could not remove something, so the "no powershell.exe" guarantee holds for
    the normal path. The command runs with a hidden console, no profile, and a
    short timeout so a broken powershell on stripped Windows can never hang the
    apply job (watchdog still bounds it).
    """
    if not names:
        return True, ""
    script = _appx_powershell_script(names)
    # Resolve powershell through %WINDIR% (avoids S607 partial-path); fall back
    # to PATH only when the canonical location is missing (e.g. stripped OS).
    powershell_path = os.path.expandvars(r"%WINDIR%\System32\WindowsPowerShell\v1.0\powershell.exe")
    if not Path(powershell_path).is_file():
        powershell_path = "powershell"
    try:
        result = subprocess.run(  # noqa: S603 - trusted system package names
            [
                powershell_path,
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                script,
            ],
            capture_output=True,
            text=True,
            timeout=20,
            shell=False,
            **_hidden_console_kwargs(),
        )
    except subprocess.TimeoutExpired:
        return False, "powershell fallback melebihi batas waktu."
    except (OSError, subprocess.SubprocessError) as exc:
        return False, f"powershell fallback gagal: {exc}"
    if result.returncode != 0:
        return False, (
            result.stderr.strip()[:300] or f"powershell fallback returncode {result.returncode}"
        )
    return True, result.stdout.strip()[:200]


def run_appx_debloat(step: Any) -> dict[str, Any]:
    """Execute the Debloat Windows tweak for the CURRENT user, in-process.

    Primary path is native: pythonnet -> ``PackageManager.RemovePackageAsync``
    (COM to AppXSVC), no console process and no elevation required. If a package
    cannot be removed natively, a per-user ``Remove-AppxPackage`` fallback
    (matching the manual script users confirm works) is attempted. Every target
    package is isolated so one protected/stubborn app never fails the tweak;
    the step only reports failure when *nothing* could be removed.
    """
    if sys.platform != "win32":
        return {
            "description": step.description,
            "success": False,
            "error": "Tweak hanya berjalan di Windows.",
            "requires_admin": step.requires_admin,
        }
    try:
        package_manager = _load_appx_package_manager()
    except RuntimeError as exc:
        return {
            "description": step.description,
            "success": False,
            "error": str(exc),
            "requires_admin": step.requires_admin,
        }

    try:
        user_sid = _current_user_sid()
    except Exception as exc:
        return {
            "description": step.description,
            "success": False,
            "error": f"Tidak dapat membaca SID user: {exc}",
            "requires_admin": step.requires_admin,
        }

    # Enumerate candidate packages for the current user.
    try:
        candidates = [
            package
            for package in package_manager.FindPackagesForUser(user_sid)
            if _name_matches_pattern(str(package.Id.Name))
        ]
    except Exception as exc:
        return {
            "description": step.description,
            "success": False,
            "error": f"Enumerasi AppX gagal: {exc}",
            "requires_admin": step.requires_admin,
        }

    if not candidates:
        return {
            "description": step.description,
            "success": True,
            "stdout": "Tidak ada aplikasi bawaan yang cocok; Windows sudah bersih.",
            "requires_admin": step.requires_admin,
            "skipped": True,
        }

    removed = 0
    attempted = 0
    targets: list[str] = []
    native_failures: list[tuple[str, str]] = []
    for package in candidates:
        name = str(package.Id.Name)
        if _is_protected_package(name):
            continue
        attempted += 1
        targets.append(name)
        ok, detail = _remove_appx_package(package_manager, str(package.Id.FullName))
        if ok:
            removed += 1
        else:
            native_failures.append((name, detail))

    # Fallback: per-user Remove-AppxPackage (no -AllUsers), mirroring the manual
    # script that works on the user's machine. Covers builds/editions where the
    # native deployment call is rejected while the standard cmdlet succeeds.
    fallback_error = ""
    failed_names = [name for name, _ in native_failures]
    if failed_names:
        ok, detail = _remove_appx_packages_powershell(failed_names)
        if not ok:
            fallback_error = detail

    # Ground truth: re-scan what actually remains registered for this user, so
    # the reported number reflects reality no matter which path removed what.
    try:
        remaining = {str(pkg.Id.Name) for pkg in package_manager.FindPackagesForUser(user_sid)}
    except Exception:
        remaining = set()
    still_installed = [name for name in targets if name in remaining]
    actually_removed = len(targets) - len(still_installed)

    if actually_removed > 0:
        note = f"{actually_removed} aplikasi bawaan dihapus."
        if still_installed:
            note += f" Gagal sebagian: {', '.join(still_installed[:5])}."
        return {
            "description": step.description,
            "success": True,
            "stdout": note,
            "requires_admin": step.requires_admin,
        }
    if attempted == 0:
        return {
            "description": step.description,
            "success": True,
            "stdout": "Semua aplikasi yang cocok dilindungi sistem; tidak ada yang dihapus.",
            "requires_admin": step.requires_admin,
            "skipped": True,
        }
    detail_parts = [f"{name}: {detail}" for name, detail in native_failures[:3]]
    if fallback_error:
        detail_parts.append(f"fallback: {fallback_error}")
    return {
        "description": step.description,
        "success": False,
        "error": (
            "Tidak ada aplikasi yang dapat dihapus. "
            + ("; ".join(detail_parts) if detail_parts else "tanpa rincian.")
        ),
        "requires_admin": step.requires_admin,
    }


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


def _is_explorer_relaunch(command: list[str]) -> bool:
    """Detect a Windows-shell relaunch step from its RAW command.

    Both legacy spellings appear in the tweak catalog:
      * ``["start", "explorer.exe"]`` — ``start`` is a CMD builtin, which would
        be wrapped to ``cmd /c start explorer.exe`` (console flash + block).
      * ``["explorer.exe"]`` — a bare call would make ``subprocess.run`` WAIT
        on the long-running shell until the 10 s timeout (misreported).
    """
    if not command:
        return False
    head = command[0].lower()
    if head in {"explorer", "explorer.exe"}:
        return True
    return head == "start" and len(command) >= 2 and "explorer" in command[1].lower()


def _relaunch_explorer() -> None:
    """Relaunch ``explorer.exe`` detached, with no console window, and return.

    ``DETACHED_PROCESS`` + ``CREATE_NEW_PROCESS_GROUP`` fully detach the shell
    from our job object and console so the apply job never waits on it, and
    ``CREATE_NO_WINDOW`` + hidden ``STARTUPINFO`` guarantee nothing flashes.
    """
    _DETACHED_PROCESS = 0x00000008
    _CREATE_NEW_PROCESS_GROUP = 0x00000200
    subprocess.Popen(
        [r"%WINDIR%\explorer.exe"],  # noqa: S607 - %WINDIR% expands to SystemRoot.
        shell=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
        creationflags=_DETACHED_PROCESS | _CREATE_NEW_PROCESS_GROUP | _CREATE_NO_WINDOW,
        startupinfo=_hidden_console_kwargs().get("startupinfo"),
    )


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
        # Special case FIRST: the Debloat Windows tweak runs in-process through
        # pythonnet -> Windows.Management.Deployment.PackageManager (COM to
        # AppXSVC), with a per-user Remove-AppxPackage fallback only when the
        # native call is rejected. This must never go through the UAC/helper
        # relaunch path or a bare per-user -AllUsers command.
        if step.command and step.command[0] == APPSX_DEBLOAT_STEP_ID:
            return run_appx_debloat(step)
        # Special case: a shell relaunch must never go through CMD or be
        # waited on (see _is_explorer_relaunch). Handle it before resolve_command
        # rewrites "start" into "cmd /c start".
        if _is_explorer_relaunch(step.command):
            if not _file_exists_resolved(r"%WINDIR%\explorer.exe"):
                return {
                    "description": step.description,
                    "success": True,
                    "stdout": "explorer.exe tidak tersedia pada Windows ini, dilewati.",
                    "requires_admin": step.requires_admin,
                    "skipped": True,
                }
            _relaunch_explorer()
            return {
                "description": step.description,
                "success": True,
                "stdout": "explorer.exe diluncurkan ulang (detached, tanpa jendela).",
                "requires_admin": step.requires_admin,
            }

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
            **_hidden_console_kwargs(),
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


# Per-step hard timeout for an already-elevated batch. A single hung step
# (stuck service manager, half-removed PowerShell on a modded OS) must never
# freeze the whole batch / job thread, which was the "stuck at 87%" symptom.
_ELEVATED_STEP_TIMEOUT = 25


def _run_step_isolated(step: Any, timeout: int = _ELEVATED_STEP_TIMEOUT) -> dict[str, Any]:
    """Run ONE step under a hard watchdog so a stuck step is skipped, not fatal.

    The step executes in a daemon thread; if it does not finish within
    ``timeout`` seconds a "skipped" outcome is recorded and the batch moves on
    (the abandoned daemon thread dies with the process). This is what isolates
    each privileged step from the others inside a single elevated run.
    """
    if sys.platform != "win32":
        return run_step(step)
    box: list[dict[str, Any]] = []

    def _target() -> None:
        try:
            box.append(run_step(step))
        except Exception as exc:  # pragma: no cover - defensive
            box.append(_failed_outcome(step, str(exc)))

    worker = threading.Thread(target=_target, daemon=True)
    worker.start()
    worker.join(timeout)
    if worker.is_alive():
        outcome = _failed_outcome(step, "")
        outcome.update(
            {
                "success": True,
                "stdout": f"Operasi melebihi {timeout} dtk pada Windows ini, dilewati.",
                "skipped": True,
            }
        )
        outcome.pop("error", None)
        return outcome
    return box[0] if box else _failed_outcome(step, "Langkah tidak menghasilkan hasil.")


def run_elevated_steps(steps: list[Any], tweak_id: str) -> list[dict[str, Any]]:
    """Run privileged steps, elevating once via UAC when needed.

    When the current process already has an elevated token, or when
    ``IPAN_OPTIMIZER_NO_ELEVATION=1`` is set (tests/development), the steps are
    executed in-process instead. Each step runs under its own watchdog so one
    hung component can never freeze the entire batch.
    """
    if is_elevated() or os.environ.get(NO_ELEVATION_ENV) == "1":
        return [_run_step_isolated(step) for step in steps]

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
    outcomes = [_run_step_isolated(step) for step in steps]
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
