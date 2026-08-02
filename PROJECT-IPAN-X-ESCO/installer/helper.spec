# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

ROOT = Path(SPECPATH).parent
SRC = ROOT / "src"
PACKAGE = SRC / "ipan_optimizer"

analysis = Analysis(
    [str(PACKAGE / "privileged" / "helper.py")],
    pathex=[str(SRC)],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["webview", "playwright", "pytest"],
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
    name="IPANOptimizerHelper",
    debug=False,
    strip=False,
    upx=False,
    console=True,
    manifest=str(ROOT / "installer" / "helper.manifest"),
)
