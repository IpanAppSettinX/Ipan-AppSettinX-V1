"""Verify a built release EXE before shipping.

The release EXE is a system-tweaking tool built with ``requireAdministrator``
(WebView2 runs fine elevated; see LAST_ACTIVITY.md for the investigation).
This gate checks:

1. Structural sanity of the PE (x64, PE32+, GUI subsystem, sane versions).
2. Manifest declares ``requireAdministrator``.
3. Runtime smoke test: ``--no-window`` must exit 0, proving the bootloader,
   embedded Python, and the full import graph start cleanly. Because the EXE
   requires elevation, the smoke test launches it elevated (``runas``); when
   elevation is not possible on the build host, the smoke test is reported as
   a warning and skipped rather than failing the gate.

Usage:
    python scripts/verify_exe.py <path-to-exe>

Exit code 0 = healthy, 1 = unhealthy, 2 = usage error.
"""

from __future__ import annotations

import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    import pefile
except ImportError:  # pragma: no cover
    print("pefile is required: python -m pip install pefile")
    sys.exit(2)

REQUIRED_LEVEL = "requireAdministrator"


def verify_pe(path: Path) -> list[str]:
    problems: list[str] = []
    pe = pefile.PE(str(path))
    opt = pe.OPTIONAL_HEADER

    if pe.FILE_HEADER.Machine != 0x8664:
        problems.append(f"Machine=0x{pe.FILE_HEADER.Machine:x} (expected 0x8664 x64)")

    if opt.Magic != 0x20B:  # IMAGE_NT_OPTIONAL_HDR64_MAGIC
        problems.append(f"Optional header Magic=0x{opt.Magic:x} (expected PE32+ 0x20b)")

    if opt.Subsystem != 2:  # IMAGE_SUBSYSTEM_WINDOWS_GUI
        problems.append(f"Subsystem={opt.Subsystem} (expected 2 = Windows GUI)")

    if opt.MajorSubsystemVersion > 6:
        problems.append(
            f"MajorSubsystemVersion={opt.MajorSubsystemVersion} - a newer "
            "minimum Windows platform may trigger 'minimum supported platform' "
            "errors on older Windows."
        )

    if pe.FILE_HEADER.TimeDateStamp == 0:
        problems.append(
            "TimeDateStamp is 0 (1970); rebuild with a current PyInstaller so the header is patched"
        )

    if opt.CheckSum == 0:
        problems.append(
            "CheckSum is 0; rebuild with a current PyInstaller so the header is patched"
        )
    return problems


def read_manifest_level(path: Path) -> str | None:
    pe = pefile.PE(str(path))
    entry = None
    if hasattr(pe, "DIRECTORY_ENTRY_RESOURCE"):
        for entry in pe.DIRECTORY_ENTRY_RESOURCE.entries:
            if entry.name is not None and entry.name == pefile.RESOURCE_TYPE["RT_MANIFEST"]:
                break
    if entry is None:
        return None
    data = entry.directory.entries[0].directory.entries[0].data.struct
    manifest = pe.get_data(data.OffsetToData, data.Size)
    root = ET.fromstring(manifest)  # noqa: S314 - manifest is from our own EXE
    ns = {"asmv3": "urn:schemas-microsoft-com:asm.v3"}
    level = root.find(".//asmv3:requestedExecutionLevel", ns)
    if level is None:
        return None
    return level.attrib.get("level")


def verify_manifest(path: Path) -> list[str]:
    problems: list[str] = []
    try:
        level = read_manifest_level(path)
        if level is None:
            problems.append("requestedExecutionLevel not found in manifest")
        elif level != REQUIRED_LEVEL:
            problems.append(
                f"requestedExecutionLevel={level!r} (expected "
                f"{REQUIRED_LEVEL!r}; the release EXE is a system tweaking "
                "tool that must run elevated)"
            )
    except Exception as exc:
        problems.append(f"failed to read manifest: {exc}")
    return problems


def _run_elevated_and_wait(path: Path, args: list[str]) -> tuple[bool, int | None]:
    """Launch ``path`` elevated via ``runas`` and wait; return (launched, exit)."""
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

    params = " ".join(f'"{arg}"' for arg in args)
    info = ShellExecuteInfoW()
    info.cbSize = ctypes.sizeof(info)
    info.fMask = 0x00000040  # SEE_MASK_NOCLOSEPROCESS
    info.lpVerb = "runas"
    info.lpFile = str(path)
    info.lpParameters = params
    info.lpDirectory = str(path.parent)
    info.nShow = 0  # SW_HIDE

    if not ctypes.windll.shell32.ShellExecuteExW(ctypes.byref(info)):
        return False, None
    process = info.hProcess
    if not process:
        return False, None
    ctypes.windll.kernel32.WaitForSingleObject(process, 120000)
    exit_code = ctypes.c_ulong(0)
    ctypes.windll.kernel32.GetExitCodeProcess(process, ctypes.byref(exit_code))
    ctypes.windll.kernel32.CloseHandle(process)
    return True, exit_code.value


def smoke_test(path: Path) -> list[str]:
    problems: list[str] = []
    level = read_manifest_level(path)
    if level == REQUIRED_LEVEL:
        launched, exit_code = _run_elevated_and_wait(path, ["--no-window"])
        if not launched:
            print("  WARNING: elevation not available; smoke test skipped")
            return problems
        if exit_code != 0:
            problems.append(f"elevated smoke test '--no-window' exit={exit_code}")
        return problems
    try:
        result = subprocess.run(  # noqa: S603 - dev tool; runs the EXE under test with a fixed flag
            [str(path), "--no-window"],
            capture_output=True,
            timeout=120,
            check=False,
        )
        if result.returncode != 0:
            problems.append(
                f"smoke test '--no-window' exit={result.returncode} "
                "(bootloader/Python failed to start)"
            )
    except subprocess.TimeoutExpired:
        problems.append("smoke test '--no-window' timed out")
    except OSError as exc:
        problems.append(f"smoke test could not start: {exc}")
    return problems


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: python scripts/verify_exe.py <path-to-exe>")
        return 2
    path = Path(argv[0]).resolve()
    if not path.is_file():
        print(f"not a file: {path}")
        return 2

    problems: list[str] = []
    problems += verify_pe(path)
    problems += verify_manifest(path)
    problems += smoke_test(path)

    if problems:
        print(f"FAIL {path}")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print(f"OK {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
