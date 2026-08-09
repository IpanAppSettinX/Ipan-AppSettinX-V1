# ===================================================================
#  Ipan AppSettinX - Buat BACKUP_MANIFEST.txt
#  Menghitung hash SHA256 semua exe/dll (selain .venv & node_modules)
#  dan menyimpannya ke BACKUP_MANIFEST.txt.
#  Jalankan SETELAH build EXE baru dan SEBELUM backup folder.
#  Gunakan bersama verify_hash.ps1 untuk cek integritas setelah restore.
# ===================================================================
$ErrorActionPreference = 'Continue'
$root = "D:\Ipan-AppSettinX-V1"
$manifest = Join-Path $root "PROJECT-IPAN-X-ESCO\BACKUP_MANIFEST.txt"

Write-Host "=== MEMBUAT MANIFEST - Ipan AppSettinX ===" -ForegroundColor Cyan
Write-Host "Memindai exe/dll (kecuali .venv & node_modules)..."

"# Ipan AppSettinX - Backup Manifest" | Out-File $manifest -Encoding UTF8
"# Dibuat: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Out-File $manifest -Append
"# Format: SHA256<dua spasi>FullPath" | Out-File $manifest -Append
"" | Out-File $manifest -Append

$files = Get-ChildItem $root -Recurse -Force -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Extension -in '.exe','.dll' -and $_.DirectoryName -notmatch '\.venv|node_modules' }

$count = 0
foreach ($f in $files) {
    $hash = (Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash
    "$hash  $($f.FullName)" | Out-File $manifest -Append
    $count++
}

Write-Host "Manifest dibuat: $manifest" -ForegroundColor Green
Write-Host "Jumlah file: $count"
