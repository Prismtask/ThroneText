# clean_pycache.ps1
# Recursively delete all __pycache__ folders in the Pandemonium project,
# excluding those inside .venv
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File clean_pycache.ps1
#   (or right-click -> Run with PowerShell)

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptRoot

Write-Host "Searching for __pycache__ folders (excluding .venv)..." -ForegroundColor Cyan

$pycacheDirs = Get-ChildItem -Path $scriptRoot -Directory -Recurse -Filter "__pycache__" -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch '[\\/]\.venv[\\/]' }

if (-not $pycacheDirs) {
    Write-Host "No __pycache__ folders found outside .venv." -ForegroundColor Green
    exit 0
}

Write-Host "`nFound the following __pycache__ folders:" -ForegroundColor Yellow
$pycacheDirs | ForEach-Object { Write-Host "  $_" }

$confirm = Read-Host "`nDelete these folders? (y/n)"
if ($confirm -ne 'y' -and $confirm -ne 'Y') {
    Write-Host "Aborted. Nothing was deleted." -ForegroundColor Green
    exit 0
}

$pycacheDirs | ForEach-Object {
    Remove-Item -Path $_.FullName -Recurse -Force
    Write-Host "Deleted: $_" -ForegroundColor Red
}

Write-Host "`nDone! All __pycache__ folders (outside .venv) have been removed." -ForegroundColor Green
