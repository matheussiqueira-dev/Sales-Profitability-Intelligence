param([switch]$WithPgAdmin)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)

function Invoke-Checked {
    param([string]$Command, [string[]]$Arguments)
    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Command failed: $Command (exit $LASTEXITCODE)" }
}

function New-LocalSecret {
    $taskBytes = New-Object byte[] 24
    $taskRng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try { $taskRng.GetBytes($taskBytes) } finally { $taskRng.Dispose() }
    return [BitConverter]::ToString($taskBytes).Replace('-', '')
}

Get-Command python,docker,git -ErrorAction Stop | Out-Null
Invoke-Checked 'python' @('-c', 'import sys; assert sys.version_info >= (3,12)')
Invoke-Checked 'docker' @('info', '--format', '{{.ServerVersion}}')
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    Invoke-Checked 'python' @('-m', 'venv', '.venv')
}
$taskPython = Join-Path $PWD '.venv\Scripts\python.exe'
Invoke-Checked $taskPython @('-m', 'pip', 'install', '-r', 'requirements.lock.txt')
if (-not (Test-Path -LiteralPath '.env')) {
    $taskSecret = New-LocalSecret
    $taskAdminSecret = New-LocalSecret
    $taskEnvText = (Get-Content -LiteralPath '.env.example' -Raw).
        Replace('POSTGRES_PASSWORD=', ('POSTGRES_PASSWORD=' + $taskSecret)).
        Replace('PGADMIN_PASSWORD=', ('PGADMIN_PASSWORD=' + $taskAdminSecret))
    [System.IO.File]::WriteAllText((Join-Path $PWD '.env'), $taskEnvText)
}
Invoke-Checked 'docker' @('compose', 'config', '--quiet')
if ($WithPgAdmin) {
    Invoke-Checked 'docker' @('compose', '--profile', 'tools', 'up', '-d', '--wait')
} else {
    Invoke-Checked 'docker' @('compose', 'up', '-d', '--wait')
}
Invoke-Checked $taskPython @('scripts/prepare_dataset.py')
Invoke-Checked $taskPython @('-m', 'src.pipeline')
Invoke-Checked $taskPython @('-m', 'pytest', '-m', 'not integration')
Invoke-Checked $taskPython @('-m', 'ruff', 'check', '.')
Write-Host 'Setup passed: PostgreSQL snapshot reconciled; unit tests and Ruff passed.'
Write-Host 'Integration tests require isolated *_test database; see docs/execution.md.'
Write-Host 'No push performed. Existing .env, CSVs and Docker volumes were preserved.'
