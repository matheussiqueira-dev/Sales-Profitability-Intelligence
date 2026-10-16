# Runs Ruff, the full pytest suite (PostgreSQL integration included) and the DDL drift
# check inside Linux containers, mirroring the CI "unit" and "integration" jobs.
# Use when the host blocks native wheels/executables (e.g. Windows Application Control).
# Works on a disposable copy of the tracked + untracked (non-ignored) files, so .env,
# .venv, data and web/public are never mounted. The PostgreSQL container is ephemeral,
# has no published port and uses a random throwaway password; nothing is persisted.
param(
    [string]$ReportDir = 'artifacts/container-checks'
)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)

$docker = (Get-Command docker -ErrorAction SilentlyContinue).Source
if (-not $docker) { $docker = Join-Path $env:LOCALAPPDATA 'Programs\DockerDesktop\resources\bin\docker.exe' }
if (-not (Test-Path -LiteralPath $docker)) { throw 'Docker CLI not found.' }
& $docker version --format '{{.Server.Version}}' *> $null
if ($LASTEXITCODE -ne 0) { throw 'Docker Engine is not running.' }

# Same PostgreSQL digest as CI/docker-compose; Python digest validated on 2026-10-08.
$postgresImage = 'postgres:17-alpine@sha256:b0f9560a2de083e2cc7382e75f808c7381a32852a7ec49117deedb300e552b24'
$pythonImage = 'python:3.13-slim@sha256:bf44cdfcb76cd3b41e879bc058fc37ec5872002ccfde7fcb765e218cde0cd79c'

$suffix = [guid]::NewGuid().ToString('N').Substring(0, 8)
$network = "spi-check-$suffix"
$database = "spi-check-pg-$suffix"
$password = [guid]::NewGuid().ToString('N')
$workspace = Join-Path ([IO.Path]::GetTempPath()) "spi-check-$suffix"
$report = Join-Path $PWD $ReportDir
New-Item -ItemType Directory -Force -Path $report | Out-Null

try {
    $files = git ls-files --cached --others --exclude-standard
    if ($LASTEXITCODE -ne 0) { throw 'git ls-files failed.' }
    foreach ($file in $files) {
        if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { continue }  # deleted in worktree
        $target = Join-Path $workspace $file
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target) | Out-Null
        Copy-Item -LiteralPath $file -Destination $target
    }

    & $docker network create $network | Out-Null
    & $docker run -d --name $database --network $network `
        -e POSTGRES_DB=sales_profitability_test -e POSTGRES_USER=sales_app `
        -e POSTGRES_PASSWORD=$password $postgresImage | Out-Null
    $ready = $false
    for ($i = 0; $i -lt 60; $i++) {
        & $docker exec $database pg_isready -U sales_app -d sales_profitability_test *> $null
        if ($LASTEXITCODE -eq 0) { $ready = $true; break }
        Start-Sleep -Seconds 2
    }
    if (-not $ready) { throw 'PostgreSQL container did not become ready.' }

    $script = @'
set -u
export PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_ROOT_USER_ACTION=ignore
pip install --quiet -r requirements.lock.txt || exit 3
python --version > /report/python-version.txt
ruff --version > /report/ruff-version.txt
failed=0
: > /report/summary.txt
step() {
  name="$1"; shift
  start=$(date +%s)
  "$@" > "/report/$name.txt" 2>&1
  code=$?
  echo "$name exit=$code seconds=$(( $(date +%s) - start ))" | tee -a /report/summary.txt
  [ "$code" -eq 0 ] || { failed=1; tail -n 40 "/report/$name.txt"; }
}
step ruff-check ruff check .
step ruff-format ruff format --check .
step ddl-check python scripts/generate_source_ddl.py --check
step pytest pytest -p no:cacheprovider --cov=src --cov-report=term-missing \
  --cov-report=json:/report/coverage.json --junitxml=/report/junit.xml -v
tail -n 25 /report/pytest.txt
exit $failed
'@ -replace "`r", ''
    # Written as a file: Windows PowerShell 5.1 mangles embedded quotes in native arguments.
    [IO.File]::WriteAllText((Join-Path $workspace '.container-checks.sh'), $script)
    & $docker run --rm --network $network `
        -e POSTGRES_HOST=$database -e POSTGRES_PORT=5432 `
        -e POSTGRES_DB=sales_profitability_test -e POSTGRES_USER=sales_app `
        -e POSTGRES_PASSWORD=$password -e RUN_DB_TESTS=1 `
        -v "${workspace}:/work" -v "${report}:/report" -w /work `
        $pythonImage bash /work/.container-checks.sh
    if ($LASTEXITCODE -ne 0) { throw "Container checks failed (exit $LASTEXITCODE). See $ReportDir." }
    Write-Host "Container checks passed. Reports in $ReportDir."
} finally {
    & $docker rm -f $database *> $null
    & $docker network rm $network *> $null
    if (Test-Path -LiteralPath $workspace) { Remove-Item -LiteralPath $workspace -Recurse -Force }
}
