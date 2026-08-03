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
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "pytest", "mypy", "ruff", "playwright"],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(analysis.pure)

exe = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="IPANOptimizer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    manifest=str(ROOT / "installer" / "main.manifest"),
    uac_admin=True,
    icon=str(PACKAGE / "frontend" / "assets" / "ipan-store-logo.ico"),
)

collect = COLLECT(
    exe,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=False,
    name="IPANOptimizer",
)
