# ===================================================================
#  Ipan AppSettinX - Verify Folder Bersih Setelah Install Ulang Windows
#  Jalankan dari folder project setelah restore backup.
#  Cek: signature EXE valid + tidak ada file miner/trojan tersisa.
# ===================================================================
$ErrorActionPreference = 'SilentlyContinue'
$root = "D:\Ipan-AppSettinX-V1"
$results = @()

Write-Host "=== 1. Cek ancaman aktif Defender ===" -ForegroundColor Cyan
$active = (Get-MpThreat | Where-Object { $_.IsActive -eq $true }).Count
$results += "Ancaman aktif: $active"
Write-Host "  Ancaman aktif: $active"

Write-Host "=== 2. Cek file miner/trojan dikenal ===" -ForegroundColor Cyan
$badNames = 'bungee.boo','DiniiXX.jpeg','DiniiYY.jpeg','DinoSaur.jpeg','tx_*.exe','profapi.dll'
$found = $false
foreach ($n in $badNames) {
    $hits = Get-ChildItem $root -Recurse -Force -Include $n -ErrorAction SilentlyContinue
    foreach ($h in $hits) { $results += "DITEMUKAN: $($h.FullName)"; $found = $true }
}
if (-not $found) { $results += "File miner/trojan: BERSIH" ; Write-Host "  BERSIH" } else { Write-Host "  ADA TEMUAN! Lihat hasil di file log" }

Write-Host "=== 3. Cek signature EXE final ===" -ForegroundColor Cyan
$exe = Join-Path $root "PROJECT-IPAN-X-ESCO\dist\Ipan AppSettinX V1.exe"
if (Test-Path $exe) {
    $sig = Get-AuthenticodeSignature -FilePath $exe
    $results += "Signature EXE: $($sig.Status)"
    Write-Host "  Signature: $($sig.Status) ($($sig.SignerCertificate.Subject))"
} else {
    $results += "EXE final TIDAK ADA di dist/"
    Write-Host "  EXE final tidak ditemukan!"
}

Write-Host "=== 4. Cek sertifikat ter-import ===" -ForegroundColor Cyan
$certFound = Get-ChildItem Cert:\CurrentUser\My | Where-Object { $_.Subject -match 'Ipan AppSettinX' }
if ($certFound) { $results += "Sertifikat: TER-IMPORT"; Write-Host "  Sertifikat OK" } else { $results += "Sertifikat: BELUM di-import (import pfx dari installer/)"; Write-Host "  BELUM di-import" }

$log = "$env:TEMP\ipan_verify_$(Get-Date -Format yyyyMMdd_HHmmss).log"
$results | Out-File $log -Encoding UTF8
Write-Host "`n=== HASIL DISIMPAN DI: $log ===" -ForegroundColor Green
