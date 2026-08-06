# -*- mode: python ; coding: utf-8 -*-
import platform as _platform
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
