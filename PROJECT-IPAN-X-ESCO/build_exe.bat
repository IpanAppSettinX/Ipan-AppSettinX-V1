@echo off
REM ===================================================================
REM  Ipan AppSettinX V1 - Clean Rebuild (PyInstaller)
REM  Jalankan dari dalam folder: D:\Ipan-AppSettinX-V1\PROJECT-IPAN-X-ESCO
REM  - Menghapus build/, dist/, dan cache PyInstaller (cegah Temp_MEI error)
REM  - Rebuild EXE via installer\ipan_optimizer.spec
REM  - Membuka File Explorer ke folder dist setelah selesai
REM ===================================================================
setlocal EnableDelayedExpansion

REM Pindah ke folder tempat script ini berada (root proyek)
cd /d "%~dp0"

echo ===================================================================
echo  [Ipan AppSettinX] Clean Rebuild
echo  Working dir: %CD%
echo ===================================================================

REM --- Tentukan interpreter build ---
REM Prioritas: venv proyek (PyInstaller 6.21 terbukti berfungsi), lalu global.
set "PY="
set "VENV_PY=%~dp0.venv\Scripts\python.exe"
if exist "%VENV_PY%" (
    "%VENV_PY%" -m PyInstaller --version >nul 2>&1 && set "PY=%VENV_PY%"
)
if not defined PY (
    if exist "C:\Python312\python.exe" (
        "C:\Python312\python.exe" -m PyInstaller --version >nul 2>&1 && set "PY=C:\Python312\python.exe"
    )
)
if not defined PY (
    echo [ERROR] Tidak ada interpreter dengan PyInstaller yang berfungsi.
    echo         Coba: venv proyek atau C:\Python312 dengan 'pip install pyinstaller'.
    pause
    exit /b 1
)
echo  Interpreter: %PY%

REM --- [1/5] Bersihkan artefak build lama (mencegah Temp_MEI corrupt) ---
echo.
echo [1/5] Menghapus folder build, dist, dan cache PyInstaller...
if exist "build"  rmdir /s /q "build"
if exist "dist"   rmdir /s /q "dist"
if exist "dist_new" rmdir /s /q "dist_new"
REM Cache PyInstaller di %APPDATA%\pyinstaller sering menyimpan bootloader
REM yang dikarantina Defender -> penyebab "No module named unicodedata".
if defined APPDATA (
    if exist "%APPDATA%\pyinstaller" rmdir /s /q "%APPDATA%\pyinstaller"
)
if defined LOCALAPPDATA (
    if exist "%LOCALAPPDATA%\pyinstaller" rmdir /s /q "%LOCALAPPDATA%\pyinstaller"
)
echo      Bersih.

REM --- [2/5] Pastikan PyInstaller tersedia ---
echo.
echo [2/5] Memeriksa PyInstaller...
"%PY%" -c "import PyInstaller; print('      PyInstaller', PyInstaller.__version__)" 2>nul
if errorlevel 1 (
    echo      PyInstaller belum terpasang. Memasang 6.21.0...
    "%PY%" -m pip install "pyinstaller==6.21.0"
    if errorlevel 1 (
        echo [ERROR] Gagal memasang PyInstaller.
        pause
        exit /b 1
    )
)

REM --- [3/5] Build EXE ---
echo.
echo [3/5] Build EXE (clean, noconfirm)...
"%PY%" -m PyInstaller --clean --noconfirm "installer\ipan_optimizer.spec"
if errorlevel 1 (
    echo.
    echo [ERROR] Build gagal. Periksa log di atas.
    pause
    exit /b 1
)

REM --- [4/5] Verifikasi artefak ---
echo.
echo [4/5] Memverifikasi hasil build...
set "EXE=dist\Ipan AppSettinX V1.exe"
if not exist "%EXE%" (
    echo [ERROR] EXE tidak ditemukan di %EXE%
    pause
    exit /b 1
)
for %%A in ("%EXE%") do echo      Ukuran EXE: %%~zA bytes
REM Verifikasi opsional (abaikan kegagalan non-kritis)
if exist "scripts\verify_exe.py" (
    "%PY%" "scripts\verify_exe.py" "%EXE%" 2>nul
)

REM --- [5/5] Buka Explorer ke folder dist ---
echo.
echo [5/5] Membuka File Explorer ke folder dist...
start "" explorer "%CD%\dist"

echo.
echo ===================================================================
echo  SELESAI. EXE ada di: %CD%\%EXE%
echo ===================================================================
pause
endlocal
