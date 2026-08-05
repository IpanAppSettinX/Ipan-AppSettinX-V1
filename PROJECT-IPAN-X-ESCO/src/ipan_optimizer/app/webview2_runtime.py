"""WebView2 Evergreen runtime detection and automatic installation.

This module is the single source of truth for checking whether the Microsoft
Edge WebView2 Runtime is installed on the current Windows host and for
launching the official Microsoft bootstrapper (``MicrosoftEdgeWebview2Setup.exe``)
when it is missing.

Design notes:
- Detection reads the same EdgeUpdate registry keys that Microsoft documents
  for the WebView2 Runtime installer: the per-machine install under
  ``HKLM\\SOFTWARE\\Microsoft\\EdgeUpdate\\Clients\\{F3017226-...}`` (WOW64 32-bit
  view) and the per-user install under ``HKCU\\Software\\Microsoft\\EdgeUpdate\\
  Clients\\{F3017226-...}``. A registered runtime reports its ``pv`` value,
  which is never ``0.0.0.0`` for a real install.
- Installation is **never silent**. The bundled bootstrapper is launched with
  its default UI so the user can see and confirm the Microsoft installer. This
  keeps the application transparent: no hidden component install, no
  ``/silent`` flag. The Microsoft installer itself may still prompt for
  elevation depending on install scope.
- All host interaction is delegated through small seam functions so unit tests
  can mock detection and installation without ever touching the real host.
- On non-Windows platforms detection returns ``False`` and installation raises
  ``RuntimeError``. The caller is expected to handle that gracefully (e.g. dev
  boxes running Linux/macOS).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

# The Microsoft-published WebView2 Runtime client GUID. Microsoft documents
# this GUID as the stable identifier for the Evergreen standalone runtime
# under the EdgeUpdate client registry namespace.
WEBVIEW2_CLIENT_GUID = "{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"

# EdgeUpdate registry paths. The machine-wide key lives in the 32-bit view
# because EdgeUpdate itself is a 32-bit service; the user key is view-neutral.
WEBVIEW2_MACHINE_KEY = r"SOFTWARE\Microsoft\EdgeUpdate\Clients\\" + WEBVIEW2_CLIENT_GUID
WEBVIEW2_USER_KEY = r"Software\Microsoft\EdgeUpdate\Clients\\" + WEBVIEW2_CLIENT_GUID

# Sentinel version that EdgeUpdate writes while a runtime is being staged. We
# treat it as "not yet installed" so we do not skip the bootstrapper for a
# half-staged runtime.
WEBVIEW2_STAGING_VERSION = "0.0.0.0"  # noqa: S104 - sentinel version string, not a network bind

# Bootstrapper file name. Microsoft distributes this exact file from its
# official download page for WebView2 (see docs/WEBVIEW2_BOOTSTRAP.md).
# It must be placed by the developer into ``src/ipan_optimizer/data/`` before
# building the EXE. See ``docs/WEBVIEW2_BOOTSTRAP.md`` for provenance and
# license notes.
WEBVIEW2_BOOTSTRAPPER_NAME = "MicrosoftEdgeWebview2Setup.exe"

# Standalone offline installer (~200 MB). Microsoft ships this as
# ``MicrosoftEdgeWebView2RuntimeInstallerX64.exe``. Unlike the bootstrapper it
# embeds the full runtime and does not require an internet connection. Used as
# fallback when the bootstrapper cannot reach Microsoft CDN (Windows mod with
# stripped Windows Update / edgeupdate) and no Fixed Version runtime is bundled.
WEBVIEW2_STANDALONE_INSTALLER_NAME = "MicrosoftEdgeWebView2RuntimeInstallerX64.exe"

# Fixed Version runtime folder name. When the developer extracts a Fixed
# Version Runtime package into ``src/ipan_optimizer/data/webview2_fixed/``,
# the app points pywebview at it via ``WEBVIEW2_RUNTIME_PATH`` and skips
# system detection entirely. Fully portable, no installer, no admin.
WEBVIEW2_FIXED_DIR_NAME = "webview2_fixed"


def _read_registry_pv(hive: int, key_path: str, view: int) -> str | None:
    """Read the ``pv`` value of an EdgeUpdate client key.

    Returns the version string if the key/value exists, otherwise ``None``.
    Any registry error (access denied, key missing, etc.) is mapped to
    ``None``; callers only need a yes/no answer.
    """
    if sys.platform != "win32":
        return None
    try:
        import winreg

        with winreg.OpenKey(hive, key_path, 0, winreg.KEY_QUERY_VALUE | view) as key:
            value, _ = winreg.QueryValueEx(key, "pv")
            return str(value)
    except FileNotFoundError:
        return None
    except OSError:
        return None


def is_webview2_installed(
    *,
    reader: Callable[[int, str, int], str | None] | None = None,
) -> bool:
    """Return ``True`` when the WebView2 Evergreen runtime is installed.

    A runtime is considered installed when either the machine-wide or the
    per-user EdgeUpdate client key exists and its ``pv`` value is anything
    other than the staging sentinel ``0.0.0.0``.

    The optional ``reader`` seam is used by tests to avoid touching the real
    Windows registry. Production callers leave it as ``None``.
    """
    if sys.platform != "win32":
        return False
    if reader is None:
        reader = _read_registry_pv
    try:
        import winreg

        hklm = winreg.HKEY_LOCAL_MACHINE
        hkcu = winreg.HKEY_CURRENT_USER
        wow64_32 = winreg.KEY_WOW64_32KEY
    except ImportError:  # pragma: no cover - winreg missing on non-Windows
        return False

    for hive, path, view in (
        (hklm, WEBVIEW2_MACHINE_KEY, wow64_32),
        (hkcu, WEBVIEW2_USER_KEY, 0),
    ):
        version = reader(hive, path, view)
        if version and version != WEBVIEW2_STAGING_VERSION:
            return True
    return False


def bootstrapper_path(bundle_root: Path | None = None) -> Path:
    """Return the expected path of the bundled WebView2 bootstrapper.

    Inside a PyInstaller bundle the file is collected under
    ``_MEIPASS/ipan_optimizer/data/<name>``. In dev mode it lives next to the
    package source. The optional ``bundle_root`` argument is used by tests to
    point at a temp directory.
    """
    if bundle_root is not None:
        return bundle_root / WEBVIEW2_BOOTSTRAPPER_NAME
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass) / "ipan_optimizer" / "data" / WEBVIEW2_BOOTSTRAPPER_NAME
    return Path(__file__).resolve().parent.parent / "data" / WEBVIEW2_BOOTSTRAPPER_NAME


def _data_dir(bundle_root: Path | None = None) -> Path:
    """Resolve the bundled ``data`` directory (PyInstaller or dev mode)."""
    if bundle_root is not None:
        return bundle_root
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass) / "ipan_optimizer" / "data"
    return Path(__file__).resolve().parent.parent / "data"


def standalone_installer_path(bundle_root: Path | None = None) -> Path:
    """Return the expected path of the bundled offline WebView2 installer."""
    return _data_dir(bundle_root) / WEBVIEW2_STANDALONE_INSTALLER_NAME


def fixed_runtime_path(bundle_root: Path | None = None) -> Path:
    """Return the expected path of the bundled Fixed Version runtime folder.

    Returns a Path that may not exist. Callers must check ``is_dir()`` before
    using it. When the folder exists and contains ``msedgewebview2.exe``, the
    app sets ``WEBVIEW2_RUNTIME_PATH`` to it and skips system install.
    """
    return _data_dir(bundle_root) / WEBVIEW2_FIXED_DIR_NAME


def fixed_runtime_available(bundle_root: Path | None = None) -> bool:
    """Return ``True`` when the bundled Fixed Version runtime is usable."""
    path = fixed_runtime_path(bundle_root)
    return path.is_dir() and (path / "msedgewebview2.exe").is_file()


def install_webview2(
    *,
    exe_path: Path,
    runner: Callable[[list[str]], int] | None = None,
) -> int:
    """Launch the official Microsoft WebView2 bootstrapper and wait for it.

    The bootstrapper is started with its default UI (no ``/silent`` flag) so
    the user can see and confirm the Microsoft installer. The return code is
    the bootstrapper's exit code: ``0`` means success.

    The optional ``runner`` seam is used by tests to avoid launching a real
    process. Production callers leave it as ``None``.
    """
    if sys.platform != "win32":
        raise RuntimeError("Instalasi WebView2 hanya didukung pada Windows.")
    if not exe_path.is_file():
        raise FileNotFoundError(
            f"Bootstrapper WebView2 tidak ditemukan: {exe_path}. "
            "Unduh MicrosoftEdgeWebview2Setup.exe resmi dari "
            "https://developer.microsoft.com/microsoft-edge/webview2/ dan "
            "letakkan di src/ipan_optimizer/data/ sebelum membangun EXE."
        )
    if runner is None:

        def runner(cmd: list[str]) -> int:
            # ``shell=False`` with an absolute path to a signed Microsoft
            # binary. We do not pass any silent flags so the user sees the
            # official installer UI.
            completed = subprocess.run(  # noqa: S603 - signed Microsoft binary, absolute path
                cmd,
                check=False,
                shell=False,
            )
            return int(completed.returncode)

    return runner([str(exe_path)])


def ensure_webview2(
    *,
    reader: Callable[[int, str, int], str | None] | None = None,
    runner: Callable[[list[str]], int] | None = None,
    bundle_root: Path | None = None,
    headless: bool = False,
) -> bool:
    """Ensure the WebView2 runtime is available before the UI starts.

    Resolution order:
    1. Bundled Fixed Version runtime (``data/webview2_fixed/``). When present,
       the caller sets ``WEBVIEW2_RUNTIME_PATH`` to it and we return ``True``
       without touching the system install. Fully portable, no admin.
    2. System Evergreen install (registry detection).
    3. Bundled offline installer (``MicrosoftEdgeWebView2RuntimeInstallerX64.exe``).
       Launched with its default UI so the user sees the Microsoft installer.
    4. Bundled bootstrapper (``MicrosoftEdgeWebview2Setup.exe``). Smaller but
       requires an internet connection to the Microsoft CDN.

    Returns ``True`` when a usable runtime is available at the end. When
    ``headless`` is ``True`` (smoke tests / non-Windows CI), only detection is
    performed and no installer is ever launched.
    """
    if fixed_runtime_available(bundle_root):
        return True
    if is_webview2_installed(reader=reader):
        return True
    if headless:
        return False
    if sys.platform != "win32":
        return False
    # Prefer the offline standalone installer (works without internet / WU).
    standalone = standalone_installer_path(bundle_root)
    if standalone.is_file():
        try:
            exit_code = install_webview2(exe_path=standalone, runner=runner)
        except FileNotFoundError:
            exit_code = -1
        if exit_code == 0 and is_webview2_installed(reader=reader):
            return True
    # Fall back to the small bootstrapper (needs internet).
    exe = bootstrapper_path(bundle_root)
    try:
        exit_code = install_webview2(exe_path=exe, runner=runner)
    except FileNotFoundError:
        return False
    if exit_code != 0:
        return False
    return is_webview2_installed(reader=reader)
