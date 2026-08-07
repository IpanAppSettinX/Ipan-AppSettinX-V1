# -*- mode: python ; coding: utf-8 -*-
import os
import platform as _platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(SPECPATH).parent
SRC = ROOT / "src"
PACKAGE = SRC / "ipan_optimizer"

_build_machine = _platform.machine().upper()
if _build_machine not in {"AMD64", "X86_64"}:
    raise SystemExit(
        f"Build harus dijalankan pada x64 (AMD64). Terdeteksi: {_build_machine}"
    )

bootstrapper = PACKAGE / "data" / "MicrosoftEdgeWebview2Setup.exe"

datas = [
    (str(PACKAGE / "frontend"), "ipan_optimizer/frontend"),
    (str(PACKAGE / "data"), "ipan_optimizer/data"),
]

binaries = []
if bootstrapper.is_file():
    binaries.append((str(bootstrapper), "ipan_optimizer/data"))

# Bundle the Universal C Runtime (UCRT) so the app runs on machines without
# the Visual C++ Redistributable installed. python312.dll depends on
# ucrtbase.dll and api-ms-win-crt-*.dll; without them the bootloader fails
# with "failed to load python dll".
_crt_source = Path(os.environ.get("WINDIR", r"C:\Windows")) / "System32"
_crt_downlevel = _crt_source / "downlevel"
for _dll_name in ["ucrtbase.dll"]:
    _dll_path = _crt_source / _dll_name
    if _dll_path.is_file():
        binaries.append((str(_dll_path), "."))
if _crt_downlevel.is_dir():
    for _dll_path in _crt_downlevel.glob("api-ms-win-crt-*.dll"):
        binaries.append((str(_dll_path), "."))

# Generate and bundle api-ms-win-core-path-l1-1-0.dll forwarder.
# Python 3.12 links against this API set which only exists as a virtual
# contract on Windows 10/11. On stripped Windows editions (Ghost Spectre,
# AtlasOS, ReviOS, X Lite, Kernel OS) the API set resolution is broken,
# causing python312.dll to fail to load. This forwarder DLL redirects the
# calls to shlwapi.dll and kernel32.dll where the real implementations live.
_path_wrapper_script = ROOT / "scripts" / "gen_path_wrapper.py"
_path_wrapper_dll = ROOT / "build" / "api-ms-win-core-path-l1-1-0.dll"
if _path_wrapper_script.is_file():
    _path_wrapper_dll.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [sys.executable, str(_path_wrapper_script), str(_path_wrapper_dll)],
        check=True,
        capture_output=True,
    )
    if _path_wrapper_dll.is_file():
        binaries.append((str(_path_wrapper_dll), "."))

analysis = Analysis(
    [str(PACKAGE / "main.py")],
    pathex=[str(SRC)],
    binaries=binaries,
    datas=datas,
    hiddenimports=[
        "webview.platforms.edgechromium",
        "clr",
        "win32api",
        "win32con",
        "win32com",
        "win32com.client",
        "pythoncom",
        "win32timezone",
        "win32pdh",
        "win32pdhutil",
        # C-extension stdlib modules that PyInstaller's modulegraph can miss
        # when a stale/corrupted build cache is reused. ``unicodedata`` is the
        # one that crashed the release EXE on the modded test OS with
        # "ModuleNotFoundError: No module named 'unicodedata'". Listing them
        # here forces them to be bundled from C:\\Python312\\DLLs.
        "unicodedata",
        "_decimal",
        "_bz2",
        "_lzma",
        "_sqlite3",
        "_ssl",
        "_socket",
        "_queue",
        "_ctypes",
        "_elementtree",
        "pyexpat",
        "select",
        "zlib",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "pytest",
        "mypy",
        "ruff",
        "playwright",
        "win32ui",
        "Pythonwin",
        "pip",
        "setuptools",
        "pygments",
        "IPython",
        "matplotlib",
        "numpy",
        "pandas",
        "PIL",
        "PyInstaller",
    ],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(analysis.pure)

exe = EXE(
    pyz,
    analysis.scripts,
    analysis.binaries,
    analysis.datas,
    [],
    name="Ipan AppSettinX V1",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    manifest=str(ROOT / "installer" / "main.manifest"),
    uac_admin=True,
    icon=str(PACKAGE / "frontend" / "assets" / "ipan-store-logo.ico"),
)
