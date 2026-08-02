# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

ROOT = Path(SPECPATH).parent
SRC = ROOT / "src"
PACKAGE = SRC / "ipan_optimizer"

datas = [
    (str(PACKAGE / "frontend"), "ipan_optimizer/frontend"),
    (str(PACKAGE / "data"), "ipan_optimizer/data"),
]

analysis = Analysis(
    [str(PACKAGE / "main.py")],
    pathex=[str(SRC)],
    binaries=[],
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
