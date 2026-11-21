<#
.SYNOPSIS
    Automated execution of Olist PostgreSQL warehouse setup and validation.
.DESCRIPTION
    Runs:
      0. sql/00_create_database.sql (creates olist_db)
      1. sql/01_create_raw_tables.sql
      2. sql/02_load_raw_data.sql
      3. sql/03_create_derived_tables.sql
      4. python/02_validate_warehouse.py
.EXAMPLE
    .\run_all_sql.ps1 -User postgres -Password your_password
#>

param (
    [string]$User = "postgres",
    [string]$Password = "",
    [string]$HostName = "localhost",
    [int]$Port = 5432,
    [string]$Database = "olist_db"
)

$ErrorActionPreference = "Stop"

if ($Password) {
    $env:PGPASSWORD = $Password
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " OLIST POSTGRESQL WAREHOUSE SETUP & RECONCILIATION RUNNER " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 0. Create Database (connects to default maintenance db 'postgres')
Write-Host "`n[Step 0/4] Creating database '$Database'..." -ForegroundColor Yellow
psql -h $HostName -p $Port -U $User -d postgres -f sql/00_create_database.sql

# 1. Create Raw Tables
Write-Host "`n[Step 1/4] Creating raw staging tables..." -ForegroundColor Yellow
psql -h $HostName -p $Port -U $User -d $Database -f sql/01_create_raw_tables.sql

# 2. Load Raw CSVs
Write-Host "`n[Step 2/4] Ingesting raw CSV datasets via \copy..." -ForegroundColor Yellow
psql -h $HostName -p $Port -U $User -d $Database -f sql/02_load_raw_data.sql

# 3. Create Derived Tables (Star Schema)
Write-Host "`n[Step 3/4] Transforming and populating dimensional star schema..." -ForegroundColor Yellow
psql -h $HostName -p $Port -U $User -d $Database -f sql/03_create_derived_tables.sql

# 4. Run Automated Validation Check
Write-Host "`n[Step 4/4] Executing automated Python validation against canonical control totals..." -ForegroundColor Yellow
$pythonExec = if (Get-Command python -ErrorAction SilentlyContinue) { "python" } elseif (Get-Command py -ErrorAction SilentlyContinue) { "py" } else { "python3" }
& $pythonExec python/02_validate_warehouse.py --dbname $Database --user $User --password $Password --host $HostName --port $Port

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host " SETUP AND VALIDATION PIPELINE FINISHED!                 " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
