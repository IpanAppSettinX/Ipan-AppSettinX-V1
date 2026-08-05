# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

ROOT = Path(SPECPATH).parent
SRC = ROOT / "src"
PACKAGE = SRC / "ipan_optimizer"

# Bundle the official Microsoft Edge WebView2 Runtime bootstrapper so the app
# can auto-install the runtime when missing. The developer must download
# MicrosoftEdgeWebview2Setup.exe from
# https://developer.microsoft.com/microsoft-edge/webview2/ and place it in
# src/ipan_optimizer/data/ before building. If absent, the build still
# succeeds but the auto-install path will not be available at runtime.
bootstrapper = PACKAGE / "data" / "MicrosoftEdgeWebview2Setup.exe"

# WebView2 Fixed Version Runtime (optional, ~250 MB). Excluded from onefile
# builds — extracting 250 MB to temp on every startup adds 3-5 s delay.
# The bootstrapper (172 KB) handles WebView2 install when missing.
fixed_runtime = PACKAGE / "data" / "webview2_fixed"

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
    icon=str(PACKAGE / "frontend" / "assets" / "ipan-store-logo.ico"),
)
