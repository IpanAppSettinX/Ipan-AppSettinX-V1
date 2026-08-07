"""Clean rebuild otomatis untuk EXE rilis (PyInstaller).

Jalankan dari mana saja (drive letter boleh berubah antar-boot pada sistem
dual-boot Windows X-Lite — script ini memakai path dinamis, TIDAK ada
hardcode ``C:\\`` atau ``E:\\``)::

    python build.py

Langkah yang dilakukan:
1. Menemukan root proyek dari lokasi file ini (bukan dari CWD).
2. Memilih interpreter yang berfungsi: ``.venv``/``.venv-build`` proyek
   lebih dulu, lalu interpreter yang sedang menjalankan script ini.
3. Menghapus ``build/``, ``dist/``, ``dist_new/``, dan cache PyInstaller
   di ``%APPDATA%``/``%LOCALAPPDATA%`` (sumber error ``unicodedata``).
4. Rebuild lewat ``installer/ipan_optimizer.spec`` (``--clean --noconfirm``).
5. Memverifikasi artefak lewat ``scripts/verify_exe.py`` bila tersedia.
6. Membuka Windows File Explorer tepat di folder EXE hasil build.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SPEC = ROOT / "installer" / "ipan_optimizer.spec"
EXE_NAME = "Ipan AppSettinX V1.exe"


def _pyinstaller_works(python: Path) -> bool:
    try:
        result = subprocess.run(  # noqa: S603 - interpreter ditemukan dari venv proyek/PATH sendiri
            [str(python), "-m", "PyInstaller", "--version"],
            capture_output=True,
            timeout=60,
        )
        return result.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def _find_interpreter() -> Path:
    """Pilih interpreter build secara dinamis (tanpa hardcode drive letter)."""
    candidates: list[Path] = []
    for venv_name in (".venv-build", ".venv"):
        candidates.append(ROOT / venv_name / "Scripts" / "python.exe")
    # Interpreter yang sedang menjalankan script ini (bisa venv aktif atau
    # instalasi global di drive mana pun).
    candidates.append(Path(sys.executable))
    # Interpreter global resmi dari PATH (nama saja -> diresolve Windows).
    resolved = shutil.which("python")
    if resolved:
        candidates.append(Path(resolved))
    for python in candidates:
        if python.is_file() and _pyinstaller_works(python):
            return python
    raise SystemExit(
        "[ERROR] Tidak ada interpreter dengan PyInstaller yang berfungsi. "
        "Pasang dulu: python -m pip install pyinstaller"
    )


def _remove(path: Path) -> None:
    if path.exists():
        print(f"      menghapus {path}")
        shutil.rmtree(path, ignore_errors=True)


def _clean() -> None:
    print("[1/5] Membersihkan artefak build lama ...")
    for folder in ("build", "dist", "dist_new"):
        _remove(ROOT / folder)
    # Cache PyInstaller menyimpan bootloader hasil karantina Defender ->
    # penyebab EXE korup ("No module named unicodedata"). Lokasi dinamis
    # via env var, bukan drive letter tetap.
    for env_var in ("APPDATA", "LOCALAPPDATA"):
        base = os.environ.get(env_var)
        if base:
            _remove(Path(base) / "pyinstaller")
    # Cache PyInstaller versi Linux-style (jaga-jaga bila di-set manual).
    cache = sysconfig.get_config_var("cachedir")
    if cache:
        _remove(Path(cache) / "pyinstaller")


def _build(python: Path) -> Path:
    print("[3/5] Build EXE (clean, noconfirm) ...")
    result = subprocess.run(  # noqa: S603 - argumen statis milik proyek sendiri
        [str(python), "-m", "PyInstaller", "--clean", "--noconfirm", str(SPEC)],
        cwd=ROOT,
    )
    if result.returncode != 0:
        raise SystemExit("[ERROR] Build gagal. Periksa log PyInstaller di atas.")
    exe = ROOT / "dist" / EXE_NAME
    if not exe.is_file():
        raise SystemExit(f"[ERROR] EXE tidak ditemukan di {exe}")
    return exe


def _verify(python: Path, exe: Path) -> None:
    print("[4/5] Memverifikasi hasil build ...")
    print(f"      Ukuran EXE: {exe.stat().st_size} bytes")
    verify_script = ROOT / "scripts" / "verify_exe.py"
    if verify_script.is_file():
        subprocess.run(  # noqa: S603 - script verifikasi milik proyek sendiri
            [str(python), str(verify_script), str(exe)], cwd=ROOT
        )


def _open_explorer(folder: Path) -> None:
    print(f"[5/5] Membuka File Explorer ke {folder} ...")
    if sys.platform == "win32":
        subprocess.Popen(["explorer", str(folder)])  # noqa: S603,S607 - explorer adalah biner OS tepercaya
    else:
        print(f"      (bukan Windows) buka manual: {folder}")


def main() -> int:
    print("=" * 67)
    print(" [Ipan AppSettinX] Clean Rebuild (dinamis, tanpa drive letter)")
    print(f" Working dir: {ROOT}")
    print("=" * 67)

    python = _find_interpreter()
    print(f" Interpreter: {python}")

    _clean()
    print("[2/5] PyInstaller siap (sudah divalidasi saat memilih interpreter).")
    exe = _build(python)
    _verify(python, exe)
    _open_explorer(exe.parent)

    print()
    print("=" * 67)
    print(f" SELESAI. EXE ada di: {exe}")
    print("=" * 67)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
