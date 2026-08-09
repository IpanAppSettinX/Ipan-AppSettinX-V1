# ===================================================================
#  Ipan AppSettinX - BACKUP SEKALI KLIK (untuk Google Drive / drive lain)
#
#  CARA PAKAI:
#    1) Edit variabel $dest di bawah -> path folder tujuan backup
#    2) Jalankan:  kanan-klik file ini -> "Run with PowerShell"
#       atau:      powershell -ExecutionPolicy Bypass -File backup_project.ps1
#
#  YANG DILAKUKAN:
#    1. Verifikasi hash folder project (harus MATCH semua, kalau tidak BERHENTI)
#    2. Update manifest (make_manifest)  [opsional, default ON]
#    3. Salin folder project ke $dest\Ipan-AppSettinX-V1 (robocopy, bisa resume)
#    4. Salin sertifikat + README code signing
#    5. Verifikasi hash hasil salinan (bandingkan source vs target)
#    6. Buat laporan di $dest\BACKUP_REPORT.txt
# ===================================================================
$ErrorActionPreference = 'Continue'

# >>>>> EDIT DI SINI: path tujuan backup <<<<<
$dest = "PUT_YOUR_GOOGLE_DRIVE_PATH_HERE"

$src   = "D:\Ipan-AppSettinX-V1"
$proj  = "$src\PROJECT-IPAN-X-ESCO"
$runMakeManifest = $true   # set $false jika sudah yakin manifest terbaru

$report = @()
function Log($m) { Write-Host $m; $script:report += $m }

if ($dest -eq "PUT_YOUR_GOOGLE_DRIVE_PATH_HERE" -or -not (Test-Path -LiteralPath $dest)) {
    Log "ERROR: Set dulu path tujuan di variabel `$dest (baris paling atas script ini)."
    Log "Contoh: `$dest = `"G:\My Drive\Backup`""
    Read-Host "Tekan Enter untuk keluar"
    exit 1
}

Log "======================================================"
Log " BACKUP IPAN APPSETTINX V1"
Log " Source : $src"
Log " Target : $dest"
Log " Waktu  : $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Log "======================================================"

# --- 1. Verifikasi hash source ---
Log "`n[1/6] Verifikasi hash folder source..."
$verifyLog = & powershell -NoProfile -ExecutionPolicy Bypass -File "$proj\scripts\verify_hash.ps1"
$verifyLog | ForEach-Object { Log "  $_" }
if (($verifyLog | Select-String "MISMATCH|MISSING") -or -not ($verifyLog | Select-String "SEMUA FILE MATCH")) {
    Log "`n!!! VERIFIKASI GAGAL. Ada file MISMATCH/MISSING. Backup DIBATALKAN."
    Log "Perbaiki dulu file yang bermasalah, atau jalankan make_manifest.ps1"
    Log "jika kamu baru build EXE baru (file memang berubah karena build baru)."
    Read-Host "Tekan Enter untuk keluar"
    exit 1
}
Log "  OK - source bersih."

# --- 2. Update manifest (opsional) ---
if ($runMakeManifest) {
    Log "`n[2/6] Update BACKUP_MANIFEST.txt..."
    & powershell -NoProfile -ExecutionPolicy Bypass -File "$proj\scripts\make_manifest.ps1" | ForEach-Object { Log "  $_" }
}

# --- 3. Robocopy folder project ---
$targetDir = Join-Path $dest "Ipan-AppSettinX-V1"
Log "`n[3/6] Menyalin folder project -> $targetDir"
robocopy $src $targetDir /E /COPY:DAT /DCOPY:DAT /R:2 /W:2 /NFL /NDL /NP /MT:8 | Out-Null
$rc = $LASTEXITCODE
if ($rc -ge 8) { Log "  !!! robocopy gagal (exit code $rc). Cek drive tujuan." }
else { Log "  OK - penyalinan selesai (robocopy exit $rc, >=8 = ada error)." }

# --- 4. Salin sertifikat + README ---
Log "`n[4/6] Menyalin sertifikat code signing + README..."
$certFiles = Get-ChildItem "$proj\installer" -Filter "*signing*" -ErrorAction SilentlyContinue
$certFiles += Get-Item "$proj\installer\CODE_SIGNING_README.txt" -ErrorAction SilentlyContinue
foreach ($cf in $certFiles) {
    $cfDest = Join-Path (Join-Path $targetDir "PROJECT-IPAN-X-ESCO\installer") $cf.Name
    Copy-Item -LiteralPath $cf.FullName -Destination $cfDest -Force
    Log "  OK - $($cf.Name)"
}

# --- 5. Verifikasi hash hasil salinan ---
Log "`n[5/6] Verifikasi hash hasil salinan (source vs target)..." 
$targetManifest = "$targetDir\PROJECT-IPAN-X-ESCO\BACKUP_MANIFEST.txt"
$check = 0; $bad = 0
Get-Content $targetManifest | Where-Object { $_ -notmatch '^#' -and $_ -match '^[A-F0-9]{64}' } | ForEach-Object {
    $parts = $_ -split "`t", 2
    $exp = $parts[0].Trim()
    $tgt = $parts[1].Trim().Replace($src, $targetDir)
    if (-not (Test-Path -LiteralPath $tgt)) { Log "  MISSING TARGET: $tgt"; $bad++; return }
    $actual = (Get-FileHash -LiteralPath $tgt -Algorithm SHA256).Hash
    $check++
    if ($actual -ne $exp) { Log "  MISMATCH TARGET: $tgt"; $bad++ }
}
Log "  File dicek: $check, bermasalah: $bad"
if ($bad -eq 0) { Log "  OK - semua file backup MATCH." } else { Log "  !!! Ada $bad file backup tidak cocok." }

# --- 6. Laporan ---
$reportPath = Join-Path $dest "BACKUP_REPORT.txt"
$report | Out-File $reportPath -Encoding UTF8
Log "`n[6/6] Laporan disimpan: $reportPath"
Log "`n======================================================"
Log " BACKUP SELESAI."
Log " Untuk melanjutkan project setelah install ulang Windows:"
Log "   1. Salin kembali folder Ipan-AppSettinX-V1 ke D:\"
Log "   2. Import installer\IpanAppSettinX_code-signing.pfx (lihat README)"
Log "   3. Jalankan scripts\verify_clean_after_restore.ps1"
Log "======================================================"
Read-Host "Tekan Enter untuk menutup"
