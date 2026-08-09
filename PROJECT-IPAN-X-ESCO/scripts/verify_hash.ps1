# ===================================================================
#  Ipan AppSettinX - Verify Hash Batch (sebelum/sesudah backup)
#  Membandingkan hash SHA256 file exe/dll dengan BACKUP_MANIFEST.txt
#  Jalankan: .\verify_hash.ps1   (jalankan dari folder project)
#  Keluar "MATCH" = file identik dgn saat backup (bersih, tidak berubah)
#        "MISMATCH" = file BERUBAH / mungkin terkontaminasi
# ===================================================================
$ErrorActionPreference = 'Continue'
$root = "D:\Ipan-AppSettinX-V1"
$manifest = Join-Path $root "PROJECT-IPAN-X-ESCO\BACKUP_MANIFEST.txt"

if (-not (Test-Path $manifest)) {
    Write-Host "MANIFEST TIDAK DITEMUKAN: $manifest" -ForegroundColor Red
    Write-Host "Buat dulu dengan menjalankan script pembuat manifest, atau pastikan BACKUP_MANIFEST.txt ada." -ForegroundColor Yellow
    exit 1
}

Write-Host "=== VERIFIKASI HASH - Ipan AppSettinX ===" -ForegroundColor Cyan
Write-Host "Membandingkan file terhadap: $manifest`n"

$total = 0; $match = 0; $mismatch = 0; $missing = 0
$lines = Get-Content $manifest | Where-Object { $_ -notmatch '^#' -and $_ -match '^[A-F0-9]{64}' }

foreach ($line in $lines) {
    $parts = $line -split "`t", 2
    if ($parts.Count -lt 2) { $parts = $line -split '\s\s+', 2 }
    if ($parts.Count -lt 2) { continue }
    $expected = $parts[0].Trim()
    $path = $parts[1].Trim()
    $total++

    if (-not (Test-Path -LiteralPath $path)) {
        $missing++
        Write-Host "MISSING : $path" -ForegroundColor Yellow
        continue
    }

    $actual = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
    if ($actual -eq $expected) {
        $match++
        Write-Host "MATCH   : $path" -ForegroundColor Green
    } else {
        $mismatch++
        Write-Host "MISMATCH: $path" -ForegroundColor Red
        Write-Host "         Expected: $expected" -ForegroundColor Red
        Write-Host "         Actual  : $actual" -ForegroundColor Red
    }
}

Write-Host "`n=== RINGKASAN ===" -ForegroundColor Cyan
Write-Host "  Total  : $total"
Write-Host "  MATCH  : $match" -ForegroundColor Green
Write-Host "  MISMATCH: $mismatch" -ForegroundColor $(if ($mismatch -gt 0) {"Red"} else {"Green"})
Write-Host "  MISSING: $missing" -ForegroundColor $(if ($missing -gt 0) {"Yellow"} else {"Green"})

if ($mismatch -eq 0 -and $missing -eq 0) {
    Write-Host "`n>>> SEMUA FILE MATCH. Folder bersih & identik dgn saat backup." -ForegroundColor Green
} else {
    Write-Host "`n>>> ADA PERBEDAAN! Cek file MISMATCH/MISSING sebelum memakai project." -ForegroundColor Red
}
