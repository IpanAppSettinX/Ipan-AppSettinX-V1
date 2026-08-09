# ===================================================================
#  Ipan AppSettinX - Setup Exclusion Defender (harus RUN AS ADMIN)
#  Jalankan: klik kanan script ini > Run with PowerShell / Run as administrator
#  Lingkup minimal aman: hanya folder build/venv proyek (bukan root project).
#  Verifikasi tamper protection tetap AKTIF setelahnya.
# ===================================================================
#Requires -RunAsAdministrator
$ErrorActionPreference = 'Continue'

$proj = "D:\Ipan-AppSettinX-V1\PROJECT-IPAN-X-ESCO"
$targets = @(
    (Join-Path $proj ".venv"),
    (Join-Path $proj ".venv-build"),
    (Join-Path $proj "build"),
    (Join-Path $proj "build_new"),
    (Join-Path $proj "dist"),
    (Join-Path $proj "dist_new")
)

Write-Host "=== SETUP EXCLUSION DEFENDER (Ipan AppSettinX) ===" -ForegroundColor Cyan
$before = @(Get-MpPreference).ExclusionPath
Write-Host "Exclusion saat ini:" -ForegroundColor Yellow
$before | ForEach-Object { Write-Host "  $_" }

foreach ($t in $targets) {
    if (Test-Path -LiteralPath $t) {
        Add-MpPreference -ExclusionPath $t -ErrorAction Stop
        Write-Host "DITAMBAHKAN: $t" -ForegroundColor Green
    } else {
        Write-Host "LEWAT (folder belum ada): $t" -ForegroundColor DarkGray
    }
}

# Jalur interpreter Python baru (per-user) juga diamankan
$pyDir = "C:\Users\WINDOWS KERJA\AppData\Local\Programs\Python"
if (Test-Path -LiteralPath $pyDir) {
    Add-MpPreference -ExclusionPath $pyDir -ErrorAction SilentlyContinue
    Write-Host "DITAMBAHKAN: $pyDir" -ForegroundColor Green
}

Write-Host "`n=== VERIFIKASI ===" -ForegroundColor Cyan
$status = Get-MpComputerStatus
Write-Host "Real-time protection : $($status.RealTimeProtectionEnabled)"
Write-Host "Tamper protection    : $($status.IsTamperProtected)"
Write-Host "`nExclusion setelah:" -ForegroundColor Yellow
@(Get-MpPreference).ExclusionPath | ForEach-Object { Write-Host "  $_" }

Write-Host "`nSELESAI. Tekan tombol apa saja untuk menutup..." -ForegroundColor Green
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
