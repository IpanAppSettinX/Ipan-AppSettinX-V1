# Last Activity Log

> **Wajib dibaca agent di awal setiap sesi baru.** Catatan ini merekam
> pekerjaan sesi paling akhir agar konteks tidak hilang antar sesi. Setelah
> menyelesaikan pekerjaan pada sesi berjalan, agent **wajib memperbarui** file
> ini (entri terbaru diletakkan paling atas).

## 2026-08-07 (sesi 4) — Startup cleanup _MEI orphan + pre-check powershell/explorer + build.py

**Status:** Selesai. Semua gates hijau (pytest **133/133**, mypy 0 error, ruff
file-yang-disentuh bersih; 6 warning lint tersisa = pre-existing di HEAD).

### 1. Startup cleanup folder `_MEI` yatim (ERR_FILE_NOT_FOUND + Temp lock)
- Gejala: setelah force-close saat hang, folder `%TEMP%\_MEI<pid>` tertinggal;
  log "failed to remove temporary directory ...\_MEI9242" dan UI re-run
  menampilkan `ERR_FILE_NOT_FOUND` karena bootloader membaca frontend usang
  di folder `_MEI` sisa crash.
- Fix: `main.cleanup_orphan_meipass()` (baru) dipanggil di `main()` sebelum
  UI dibuka. Menghapus hanya folder `_MEI*` di `tempfile.gettempdir()`
  (dinamis, tanpa drive letter) yang (a) lebih tua dari 24 jam, (b) bukan
  bundle tempat proses berjalan, dan (c) lolos uji rename (terkunci = skip).
- Test baru: `tests/unit/test_main.py` (5 skenario: hapus yatim tua, jaga
  folder baru, jangan hapus bundle sendiri, abaikan non-_MEI, no-op non-Windows).

### 2. Pre-check biner sistem tambahan untuk Windows X-Lite
- `runner.run_step` kini juga melewati `explorer` dan `powershell` bila biner
  tidak ada (X-Lite sering men-strip PowerShell) — sebelumnya hanya
  `powercfg/bcdedit/taskkill/reg/sc/net`. Dua langkah `aim_stabilizer`
  (Flush RAM via PowerShell, Restart Explorer) kini aman di OS stripped.

### 3. `build.py` (baru, root proyek)
- Padanan Python dari `build_exe.bat`: deteksi interpreter dinamis
  (`.venv-build` → `.venv` → `sys.executable` → PATH), bersihkan
  `build/ dist/ dist_new/` + cache PyInstaller di `%APPDATA%`/`%LOCALAPPDATA%`,
  rebuild via spec, verifikasi `verify_exe.py`, lalu buka Explorer ke `dist`.
- Tanpa hardcode drive letter; aman di dual-boot Windows X-Lite.

### Catatan
- Perubahan sesi ini TIDAK di-commit oleh agent (menunggu perintah user).
- `.venv-build/` masih untracked & belum masuk `.gitignore` (pre-existing).

---

## 2026-08-07 (sesi 3) — Fix hang 87% + EXE "can't run on your PC" + malware

**Status:** Selesai. EXE final **berjalan bersih** (exit 0, stderr kosong).

### 1. Fix hang 87% (Neural AimSync X)
- Akar: `_launch_elevated` di `privileged/runner.py` memakai
  `WaitForSingleObject(120s)` yang memblokir thread job bila helper elevated
  mati di tengah → UI membeku. Juga `powercfg`/`bcdedit`/`taskkill` dijalankan
  tanpa cek keberadaan di Windows X Lite.
- Fix: `runner.py` poll non-blocking (slice 250ms, berhenti saat helper keluar),
  pre-check biner sistem (skip aman bila hilang), timeout 15s→10s,
  `is_modded_windows()`; `tweak_engine.py` watchdog daemon-thread
  `_run_step_guarded`(20s)/`_run_elevated_guarded`(150s); `jobs.py` progress
  monotonic.

### 2. Fix EXE "this app can't run on your PC" (pydantic + PyInstaller 6.16)
- Gejala: EXE baru ditolak loader ("not a valid application for this OS
  platform"). Traceback aktual menunjukkan **DUA masalah bertingkat**:
  1. **`pydantic` tidak ter-bundle** → EXE crash `ModuleNotFoundError` saat
     import. Build sebelumnya hanya install dependensi minimal.
  2. **Bootloader PyInstaller 6.21** di venv utama ditolak loader host ini
     (bug `apphelp` patch kernel pada Windows custom — lihat AGENTS.md).
- Fix:
  - `installer/ipan_optimizer.spec`: `hiddenimports` C-extension (`unicodedata`,
    `_decimal`, `_bz2`, `_lzma`, `_sqlite3`, `_ssl`, `_socket`, `_queue`,
    `_ctypes`, `_elementtree`, `pyexpat`, `select`, `zlib`). Blok UCRT +
    forwarder `api-ms-win-core-path` sudah ada dari commit `d92ab24`.
  - Build memakai **`.venv-build` khusus** (PyInstaller **6.16.0** — yang
    terbukti diload loader) dengan `pip install -e .` agar SEMUA dependensi
    runtime (pydantic dkk.) terpasang. `.venv-build` ini terpisah dari `.venv`
    (yang tetap 6.21 untuk gates) — lihat AGENTS.md.
- Terverifikasi: EXE `dist\Ipan AppSettinX V1.exe` (16.87 MB) exit 0, stderr
  kosong; `unicodedata`/`pydantic`/`webview`/`psutil`/`win32api` TER-BUNDLE;
  UCRT + forwarder ADA; `verify_exe.py` OK.

### 3. Malware / persistence — BERSIH
- Audit live 10 titik (Scheduled Tasks, Run/RunOnce, WMI, IFEO, Winlogon,
  proses miner, koneksi mining, service) → semua legit. File crack Office
  (`cleanospp.exe`, `OInstall.exe`, `KMS_VL_ALL_AIO.cmd`) di `D:\BACKUP PC` dihapus.
- Notifikasi virus yang muncul = **false positive Defender** pada file legit
  (PyInstaller bootloader, Git, esbuild, game). EXE proyek discan → BERSIH.
- Skrip: `scripts/remove_malware.ps1` (admin). Ukuran EXE 17,277 KB = 16.87 MB
  (sama, beda satuan Explorer vs MB — bukan virus).

### Verifikasi
- `pytest` unit+security+integration: **121/121 LULUS**. 3 test
  `tests/integration/test_api.py` (test_emulator/gaming/advanced) diperbaiki:
  dulu keliru menganggap `apply_*_tweak` sinkron padahal mengembalikan job
  async; ditambah helper `_run_tweak_job` yang me-poll job lalu baca
  `status.result`. Ini perbaikan test, bukan logika produksi.
- `ruff format`+`ruff check` bersih; `mypy -p ipan_optimizer` (59 file, scope
  resmi) = 0 error. (mypy tidak mengecek `tests/` sesuai pyproject.)

### File baru
- `build_exe.bat` (root) — clean rebuild + buka Explorer ke dist.
- `scripts/remove_malware.ps1` — eradikasi malware/persistence (admin).

---

## Arsip Sesi Sebelumnya (2026-08-03 s.d. 2026-08-06)

> Ringkasan kronologis. Detail langkah perubahan ada di histori `git log`.

### 2026-08-06
- **Wajib Administrator**: manifest `asInvoker` → `requireAdministrator` +
  `uac_admin=True`; hapus guard relaunch non-elevated. App selalu elevated agar
  tweak HKLM/service/powercfg/bcdedit benar-benar diterapkan. `verify_exe.py`
  smoke-test elevated.
- **Self-elevation**: `privileged/runner.py` (baru) — `run_step`,
  `run_elevated_steps` (plan one-shot: nonce + SHA-256 + expiry 120s,
  `--apply-plan`/`--result`), `validate_plan_file` (anti-replay/tamper).
  `helper.py` bukan stub lagi. Test: `tests/unit/test_runner.py` (13).
- **Hardware scan akurat**: `hardware_scanner.py` — nama CPU marketing (bukan
  string CPUID), VRAM GPU dari registry QWORD (>4GB), map enum storage
  (SSD/HDD/NVMe), kecepatan RAM/network. Test: `test_hardware_scanner.py`.
- **Ikon Fluent + telemetry Task Manager**: ikon `hw/*.svg` → Fluent
  `currentColor`; telemetry GPU/disk/network dari counter PDH (tanpa MSI
  Afterburner). Panel telemetry jadi 10 kartu.
- **Copywriting login**: pesan tanpa kata "Firebase"; license key = UID akun
  (`localId`), fail-closed bila tak cocok.

### 2026-08-05
- Commit pekerjaan 8/3. Gates lulus.

### 2026-08-03
- **EXE 220 MB → 16 MB**: hapus `MicrosoftEdgeWebView2RuntimeInstallerX64.exe`
  (200 MB, fallback Evergreen+bootstrapper 172 KB cukup); tambah excludes
  (numpy/pandas/matplotlib/dll).
- **Onefile**: `COLLECT`(onedir) → `EXE(onefile)`; single file portable.
  Rename `IPANOptimizer` → `Ipan AppSettinX V1`; hidden imports pywin32/PDH.
- **Smart Scan 35x** (6542ms → 185ms): CPU/RAM via psutil, GPU/storage/network
  via WMI COM, Windows via winreg; hapus ThreadPoolExecutor.
- **Animasi apply-process**: ring → terminal `process-terminal`; percepat
  timing login. Fix real-write: `_resolve_command` expand env + wrap `cmd /c`
  untuk internal command (`del`, `rd`, `start`, dll).
- **Optimasi CPU 100%**: `_SlowSensorCache` background thread untuk slow
  sensor; `read_telemetry()` fast-path (PDH+psutil); frontend interval 1s→2.5s
  + skip saat `document.hidden`. Idle CPU <1%.
- **Cross-OS**: manifest `asInvoker` + supportedOS lengkap + Common-Controls v6;
  WebView2 resolution order (Fixed → Evergreen → offline → bootstrapper).

---

*Riwayat lengkap perubahan kode tersedia via `git log`.*
