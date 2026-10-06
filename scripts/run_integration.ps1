$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
$taskPython = Join-Path $PWD '.venv\Scripts\python.exe'
# Creates an isolated database if absent, never deletes one or modifies development tables.
& $taskPython scripts/prepare_test_database.py
if ($LASTEXITCODE -ne 0) { throw 'Cannot prepare isolated test database (CREATEDB privilege required).' }
$taskPreviousDb = $env:POSTGRES_DB
$taskPreviousRun = $env:RUN_DB_TESTS
try {
    $env:POSTGRES_DB = 'sales_profitability_test'
    $env:RUN_DB_TESTS = '1'
    & $taskPython -m pytest --cov=src --cov-report=term-missing --cov-report=json:artifacts/coverage.json
    if ($LASTEXITCODE -ne 0) { throw 'Tests failed.' }
} finally {
    $env:POSTGRES_DB = $taskPreviousDb
    $env:RUN_DB_TESTS = $taskPreviousRun
}
