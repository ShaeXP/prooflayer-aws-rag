# Print database migrations for easy copy/paste into Supabase SQL editor
# Usage: .\scripts\print_migrations.ps1

$ErrorActionPreference = "Stop"

$migration1 = "db\migrations\001_enable_pgvector.sql"
$migration2 = "db\migrations\002_tables.sql"

$separator = "=" * 80
$dash = "-" * 80

Write-Host ""
Write-Host $separator
Write-Host "MIGRATION 001: Enable pgvector Extension"
Write-Host $separator
Write-Host "File: $migration1"
Write-Host $dash
Write-Host ""
Get-Content $migration1
Write-Host ""
Write-Host ""
Write-Host $separator
Write-Host "MIGRATION 002: Create Tables"
Write-Host $separator
Write-Host "File: $migration2"
Write-Host $dash
Write-Host ""
Get-Content $migration2
Write-Host ""
Write-Host $separator
Write-Host "END OF MIGRATIONS"
Write-Host $separator
Write-Host ""
Write-Host "Instructions:"
Write-Host "1. Copy the SQL from MIGRATION 001 above (between the separators)"
Write-Host "2. Paste into Supabase SQL Editor and execute"
Write-Host "3. Copy the SQL from MIGRATION 002 above"
Write-Host "4. Paste into Supabase SQL Editor and execute"
Write-Host ""

