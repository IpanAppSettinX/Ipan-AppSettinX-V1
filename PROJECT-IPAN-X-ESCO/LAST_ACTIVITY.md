# Last Activity Log

> **Wajib dibaca agent di awal setiap sesi baru.** Catatan ini merekam
> pekerjaan sesi paling akhir agar konteks tidak hilang antar sesi. Setelah
> menyelesaikan pekerjaan pada sesi berjalan, agent **wajib memperbarui** file
> ini (entri terbaru diletakkan paling atas).

## 2026-08-02 — Login "Ingat saya", label AppSensiX, logo resize, ikon EXE, telemetry fallback, Amber tweaks

**Status:** Selesai. `pytest` = **88 passed, 4 deselected**; `ruff format`,
`ruff check`, dan `mypy src` bersih (0 error). `check_control_matrix.py`,
`check_frontend_policy.py`, dan `check_asset_budget.py` valid.

### Perubahan

1. **Login "Ingat saya dalam 30 hari"** (`index.html`, `app.js`, `layout.css`):
   checkbox `#login-remember` (`data-control-id="auth.remember"`) ditambahkan
   setelah field license. `runLoginSequence` menyimpan
   `ipan_remember_expires` (Date.now()+30 hari) dan `ipan_remember_username`
   saat dicentang; `restoreRememberedLogin()` dipanggil saat login screen tampil
   untuk mengisi otomatis username dan mencentang kembali (dihapus bila expired).
2. **Label AppSensiX** (`index.html`): 4 tombol (ACTIVATE/ENABLE CORE/ENGAGE/
   START OVERDRIVE) kini semua "Apply Tweak".
3. **Logo resize** (`layout.css`, `components.css`): `.brand-mark` & `.login-brand
   .brand-mark` 32→40px; `.about-logo` 160×80→200×100; `.support-grid
   button:first-child img` 44×30→56×40.
4. **Ikon EXE** (`installer/ipan_optimizer.spec`): `icon=...ipan-store-logo.png`
   ditambahkan ke `EXE(...)`.
5. **Telemetry fallback** (`adapters/windows/telemetry.py`): setelah blok
   nvidia-smi ditambahkan (a) deteksi nama GPU AMD via `Win32_VideoController`,
   (b) fallback CPU temp via `MSAcpi_ThermalZoneTemperature` (tenths Kelvin),
   (c) fallback CPU/GPU temp via WMI `root/OpenHardwareMonitor` Sensor.
6. **Amber Optimizer tweaks** (`core/tweak_engine.py`): `TWEAK_MENU_COMMANDS`
   item 1/2/3/5 diganti dengan konten Amber (reg GPU/power/mouse/DWM/Games
   Task, `del %TEMP%\*`, 20+ `bcdedit`, ~45 service `Start=4` via
   `SYSTEM\ControlSet001\Services\...`, telemetry/advertising/privacy reg,
   `del %homepath%\*.log` + `ClearPageFileAtShutdown=0`). Item 4 tetap
   `action="restore"`.

### Dukungan

- `docs/control_matrix.source.json` + `docs/CONTROL_MATRIX.md`:
  `auth.remember` ditambahkan (62 kontrol); `test_control_matrix.py` count
  61→62.
- `tests/ui/test_e2e.py`: ekspektasi label tombol AppSensiX diperbarui ke
  "Apply Tweak".

## 2026 — Tweak engine nyata: 35 tweak kini menerapkan perubahan Windows

**Status:** Selesai. `pytest` = **88 passed, 4 deselected**; `ruff`, `mypy`,
control matrix, frontend policy, dan asset budget semua valid. EXE direbuild
dan window terbuka normal.

### Masalah
Ketika Apply Tweak diklik, aplikasi selalu merespons "tweak tidak diterapkan".
Penyebab: `apply_advanced_tweak` di `api.py` selalu melempar `ValueError`
(reject), dan semua 5 item Tweak Menu memiliki `action="blocked"`. Tidak ada
satu pun tweak yang benar-benar menjalankan operasi Windows.

### Perubahan
- **`core/tweak_engine.py` (baru):** Engine eksekusi tweak nyata. Memetakan
  setiap `tweak_id` (30 advanced + 4 tweak menu) ke daftar `TweakStep` yang
  menjalankan perintah `reg add`, `sc config/stop`, `powercfg`, `bcdedit`,
  `del`, `taskkill`, dan PowerShell `Remove-AppxPackage` via `subprocess`.
  Setiap step mencatat sukses/gagal + output. Pesan akhir menjelaskan berapa
  operasi berhasil dan apakah butuh hak Administrator.
- **`app/api.py`:** `apply_advanced_tweak` kini memanggil `execute_tweak()`
  (bukan reject). Method baru `apply_tweak(tweak_id)` untuk Tweak Menu.
  Hasil dicatat di activity log.
- **`core/tweak_catalog.py`:** `action="blocked"` → `action="apply"` untuk
  4 item (APPLY REGEDIT, CLEAN TEMP FILES, APPLY BOOSTER, CLEAN LOG FILES).
  REVERT ALL CHANGES tetap `action="restore"`.
- **`frontend/js/app.js`:** `handleTweakAction` menangani `action="apply"`
  dengan memanggil `invoke("apply_tweak", tweak_id)` dan menampilkan pesan
  hasil dari backend.
- **Test:** `test_api.py` diperbarui — katalog assertion `apply` (bukan
  `blocked`), `test_advanced_tweak_is_analysis_only` diganti
  `test_advanced_tweak_executes_real_operations`.

### Catatan penting
- Tweak HKCU (mouse, visual) berfungsi tanpa admin. Tweak HKLM, service
  config, powercfg, bcdedit **memerlukan hak Administrator** — jalankan EXE
  sebagai Admin untuk tweak tersebut.
- User telah menyatakan paham risiko tweak CRITICAL (Defender/Firewall/
  Update/BCEDIT).

## 2026 — Login form: Username + License Key, overlay Auth Trace baru

**Status:** Selesai. `pytest` = **88 passed, 4 deselected**; `ruff`, `mypy`,
control matrix, frontend policy, dan asset budget semua valid. EXE direbuild
dan window terbuka normal.

### Perubahan
- **Form login** (`frontend/index.html`)
  - Field `Email` → `Username` (label + `type="text"`, validasi longgar; nilai
    tetap diteruskan ke payload sign-in Firebase).
  - Field baru `License Key` di bawah Password, dikirim sebagai argumen ke-3
    `authenticate(username, password, license_key)`.
- **Backend** (`app/auth.py`, `app/api.py`): `authenticate` kini menerima
  `license_key` (default `""`), di-trim, divalidasi fail-closed (kosong /
  >128 char → `ValueError`), tidak pernah di-log.
- **Desain overlay login** diganti total: kotak node CPU/GPU/RAM/SSD
  (`.optimizer-stage-map` + `.map-*` + keyframes) dihapus, diganti panel
  **Auth Trace Minimal** — kartu terminal dengan baris DEVICE / HWID / LICENSE /
  AUTH yang garis isinya menyala berurutan mengikuti tahap login nyata, plus
  satu meter progress aksen. Satu motif kuat, tipografi mono, tanpa animasi
  multi-ring yang ramai (menghindari kesan "AI slop").
- `runLoginSequence` (app.js) menggerakkan status `is-active`/`is-done` pada
  trace rows paralel dengan panggilan bridge `authenticate` yang sebenarnya;
  reduced-motion tetap ter-cover oleh aturan `.login-screen *` yang ada.
- **Test** diperbarui: unit (`test_auth.py` menyertakan license key),
  integration, dan E2E (`test_e2e.py` — label baru, field license, asersi
  `.auth-trace-row` menggantikan `.map-node`). Control matrix `auth.login`
  tetap akurat.

### Catatan
- Validasi License Key saat ini memeriksa format/keberadaan di backend; bila
  nanti Anda ingin License Key murni UI (tidak dikirim), cukup beri tahu saya
  untuk mengembalikannya ke mode UI-only.
- EXE terbaru sudah ada di `dist/IPANOptimizer/IPANOptimizer.exe`.

## 2026 — Perbaikan `ERR_FILE_NOT_FOUND` pada EXE hasil build

**Status:** Selesai. `pytest` = **88 passed, 4 deselected**; `ruff format`,
`ruff check`, dan `mypy` semua lulus. EXE direbuild dan tampilan terverifikasi
termuat normal.

### Masalah
EXE `dist/IPANOptimizer/IPANOptimizer.exe` terbuka menampilkan halaman error
WebView2/Edge: "File not found … ERR_FILE_NOT_FOUND" (logo Microsoft Edge di
kiri bawah). Penyebab: `frontend_path()` memakai
`Path(__file__).resolve().parent / "frontend" / "index.html"`. Di dalam bundle
PyInstaller one-folder, kode Python dikemas dalam arsip PYZ sehingga `__file__`
**tidak menunjuk ke file nyata di disk** — path yang dihasilkan tidak ada,
meskipun asset frontend sudah benar disalin ke `_internal/ipan_optimizer/frontend`.

### Perubahan
- `src/ipan_optimizer/main.py`
  - Tambah `import sys`.
  - `frontend_path()` kini memakai `sys._MEIPASS` saat berjalan di dalam bundle
    (`Path(sys._MEIPASS) / "ipan_optimizer" / "frontend" / "index.html"`),
    fallback ke lokasi relatif `__file__` untuk mode dev. Ini adalah pola
    standar resource PyInstaller.

### Verifikasi
- Rebuild via `python -m PyInstaller --clean --noconfirm installer/ipan_optimizer.spec`.
- EXE baru dijalankan: window "Ipan AppSettinX" terbuka, `Responding = True`.
- Analisis screenshot programatis: `DarkRatio ≈ 0.95`, `WhiteRatio ≈ 0.005`
  → tema gelap aplikasi termuat (bukan halaman error Edge yang putih).
- Aplikasi stabil sampai halaman login.

## 2026 — Verifikasi EXE `dist/IPANOptimizer` terbuka normal

**Status:** Selesai. EXE hasil build PyInstaller di `dist/IPANOptimizer/IPANOptimizer.exe`
dijalankan dan terverifikasi terbuka normal.

### Hasil
- `Start-Process` EXE → proses `IPANOptimizer` (PID 14828) berjalan stabil.
- `MainWindowTitle` = **"Ipan AppSettinX"**, `Responding = True` setelah 8s
  dan tetap responsif setelah 16s (tidak crash / tidak hang).
- Window dibawa ke foreground via `SetForegroundWindow` sehingga tampilan
  (splash → login screen) terlihat oleh user.
- Tidak ada perubahan kode; ini sesi verifikasi runtime saja.

### Catatan
- Login memerlukan kredensial Firebase produksi (lihat entri binding 1 akun/1
  perangkat di bawah — deploy `firestore.rules` masih pending milik user).

## 2026 — Loading screen dipersingkat ke ~5 detik

**Status:** Selesai. `pytest` = **88 passed, 4 deselected**; frontend policy,
asset budget, dan control matrix valid.

### Perubahan
- `src/ipan_optimizer/frontend/js/app.js`
  - `STARTUP_MIN_PRESENTATION_MS`: 137000 → 5000.
  - 9 tahap `creepStartupProgress(..., 15000)` diskala ke 350–450ms per tahap
    (total animasi tahap ~3,6s; sisa waktu diserap hold akhir).
  - Perilaku `loadStageWithProgress` (freeze-fix) tidak berubah.
- `TASKS.md`: entri pacing baru dicatat.

## 2026 — Binding 1 akun / 1 perangkat via Firestore Rules (Spark gratis, tanpa Cloud Functions)

**Status:** Kode selesai; semua gate lulus (`ruff`, `mypy`, control matrix,
frontend policy, asset budget) dan `pytest` = **88 passed, 4 deselected**.
Deploy `firestore.rules` ke project Firebase produksi masih pending (butuh
`firebase login` interaktif milik user).

### Latar belakang
User meminta sistem lisensi gaya KeyAuth (1 akun ↔ 1 HWID, terkunci otomatis
saat login pertama) tanpa mendaftarkan metode pembayaran Firebase. Implementasi
Cloud Function `bindDevice` sebelumnya digantikan oleh Firestore Security
Rules sehingga seluruh fitur berjalan di paket Spark gratis.

### Yang diubah
- `firestore.rules` (baru): invariant 1 `deviceUsers/{uid}` ↔ 1
  `deviceBindings/{deviceHash}` dijamin atomik oleh rules lewat `getAfter()`
  dalam satu `commit` dua dokumen. Client hanya bisa CREATE pasangan miliknya
  yang konsisten; update/delete ditolak (Reset HWID = admin hapus kedua
  dokumen via Console). Read dibatasi dokumen milik sendiri.
- `src/ipan_optimizer/app/auth.py`: binding kini POST langsung ke Firestore
  REST (`GET deviceUsers/{uid}` → jika belum ada, `POST :commit` dengan
  `currentDocument.exists=false` pada kedua dok). Env var
  `IPAN_FIREBASE_DEVICE_BINDING_URL` dihapus; fail-closed untuk kredensial
  salah, binding bentrok (PERMISSION_DENIED), atau token tidak valid.
- `firebase.json` kini menunjuk `firestore.rules`; `firebase/functions/`
  (Cloud Function bindDevice + node_modules) dihapus seluruhnya.
- Test: `tests/unit/test_auth.py` ditulis ulang (5 kasus: commit atomik untuk
  binding baru, binding cocok diterima, akun terikat perangkat lain ditolak,
  rules menolak commit = fail-closed, token tidak valid).
  `tests/integration/test_api.py` mengganti kasus env-var hilang menjadi
  kredensial salah ditolak. Control matrix `auth.login` diperbarui
  ("atomic Firestore rules device binding").
- Docs: `docs/FIREBASE_AUTH.md` (setup Spark, deploy rules, Reset HWID via
  Console), `SPEC.md`, `ARCHITECTURE.md`, `THREAT_MODEL.md`, `TASKS.md`.

### Cara mengaktifkan (pending, butuh kredensial user)
1. Aktifkan Email/Password auth + Firestore di Firebase Console.
2. `firebase deploy --only firestore:rules`
3. Jalankan aplikasi dengan `$env:PYTHONPATH = "src"` — tidak ada env var lain.

### Catatan
- Perubahan belum di-commit.



**Status:** Kode selesai; semua gate lulus (`ruff`, `mypy`, control matrix,
frontend policy, asset budget) dan `pytest` = **86 passed, 4 deselected**.
Deploy Cloud Function ke project Firebase produksi masih pending (butuh
`firebase login` interaktif milik user).

### Yang diubah
- `src/ipan_optimizer/app/auth.py` (baru): Firebase Email/Password sign-in via
  Identity Toolkit REST, fingerprint perangkat = `SHA-256(project_id + "\0" +
  MachineGuid)` (dibaca read-only dari `HKLM\SOFTWARE\Microsoft\Cryptography`,
  nilai mentah tidak pernah keluar proses/dicatat), lalu POST ke Cloud Function
  verifier. Fail-closed untuk endpoint non-HTTPS, konfigurasi hilang, token
  tidak valid, atau binding ditolak.
- `src/ipan_optimizer/app/api.py`: method bridge typed `authenticate`.
- `src/ipan_optimizer/frontend/index.html`: field login berubah Username →
  Email (type email).
- `src/ipan_optimizer/frontend/js/app.js`: `runLoginSequence` kini memanggil
  bridge `authenticate`; shell hanya terbuka bila backend mengotorisasi,
  kegagalan menampilkan pesan dan menjaga login tetap terkunci.
- `src/ipan_optimizer/frontend/js/bridge.js`: fallback browser menolak login
  (desktop-only).
- `firebase.json`, `.firebaserc`, `firebase/functions/` (baru): Cloud Function
  `bindDevice` (Node 22, region asia-southeast1/Singapore, mengikuti lokasi
  Firestore user) memverifikasi Firebase ID
  token + transaksi Firestore atomik yang menjamin 1 `deviceUsers/{uid}` ↔ 1
  `deviceBindings/{deviceHash}`; bentrok = 403.
- `docs/FIREBASE_AUTH.md` (baru): panduan setup admin, deploy, env var
  `IPAN_FIREBASE_DEVICE_BINDING_URL`, dan prosedur Reset HWID.
- Test baru: `tests/unit/test_auth.py` (3), `tests/integration/test_api.py`
  (+1), `tests/ui/test_e2e.py` (+1 login sukses membuka shell), freeze-test
  hooks ditambah stub `authenticate`. Control matrix `auth.login` diperbarui
  (bridge `authenticate`, server-side atomic device binding).
- Docs: `SPEC.md`, `ARCHITECTURE.md`, `THREAT_MODEL.md`, `TASKS.md` diperbarui
  dengan kontrak member access.

### Cara mengaktifkan (pending, butuh kredensial user)
1. Aktifkan Email/Password auth + Firestore di Firebase Console.
2. `npm install --prefix firebase/functions`
3. `firebase deploy --only functions:bindDevice`
4. `$env:IPAN_FIREBASE_DEVICE_BINDING_URL = "<URL fungsi>"`, lalu jalankan
   aplikasi dengan `$env:PYTHONPATH = "src"`.

### Catatan
- Test UI dijalankan dengan `reduced_motion="reduce"` agar tidak menunggu
  startup presentation 137 detik; asersi typewriter disesuaikan untuk mode itu.
- Dev tools dikembalikan ke versi lock proyek: ruff 0.14.2, mypy 1.18.2,
  pytest 8.4.2.
- Perubahan belum di-commit.

## 2026 — Perbaikan freeze startup (progress macet di 52%)

**Status:** Selesai. Semua gate lulus (`ruff`, `mypy`, control matrix, frontend
policy, asset budget) dan `pytest` = **81 passed, 4 deselected**.

### Konteks masalah
Progress startup berhenti di 52% dan tidak bergerak. Penyebab: tahap async pada
`initialize()` menampilkan label lalu `await`-menunggu panggilan bridge secara
berurutan. Ketika backend lambat/tidak merespons, persentase tidak pernah
diperbarui sehingga terlihat freeze permanen (tepat di batas akhir rentang Tweak
Menu = 52%).

### Perubahan yang diterapkan
- `src/ipan_optimizer/frontend/js/bridge.js`
  - Menambahkan `invokeWithTimeout(method, timeoutMs = 6000, ...args)` supaya
    panggilan katalog tidak bisa menggantung startup selamanya.
  - Tidak ada backdoor/test-hook di kode produksi (hook uji sempat dibuat lalu
    dihapus).
- `src/ipan_optimizer/frontend/js/app.js`
  - Mengganti tahap async yang memblokir dengan `loadStageWithProgress`, yang
    menggerakkan progress bar **paralel** dengan panggilan bridge dalam rentang
    aman dan berhenti satu langkah di bawah batas atas sampai data tiba.
  - Node RAM/GPU tidak ditandai DONE/READY sebelum datanya siap.
  - Saat timeout/respons kosong, startup lanjut mulus ke login dengan pesan
    status informatif, bukan menggantung.
  - Menghapus helper animasi lama yang tidak terpakai
    (`animateProgressInRange`, `animateProgressRange`,
    `cancelPendingRangeAnimations`, `activeStartupRangeAnimation`).
- `tests/ui/test_e2e.py` + `tests/ui/freeze_test_hooks.js`
  - Regresi baru `test_startup_progress_does_not_freeze_on_slow_backend`:
    menyuntik `window.pywebview.api` tak responsif 15 detik, memverifikasi
    progress hanya maju, mencapai ≥40%, selesai, dan mendarat di halaman login.

### Catatan durasi startup saat ini
`STARTUP_MIN_PRESENTATION_MS = 15000` (cinematic ~15,7s total). Rincian pacing
ada di bagian bawah `TASKS.md`.

### Tindak lanjut yang belum dikerjakan
- Perubahan masih berupa working tree (belum di-commit). Lihat `git status`.
- `tests/ui/freeze_test_hooks.js` adalah file bantu khusus uji; jangan dipakai
  di jalur produksi.
