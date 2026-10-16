#requires -Version 7.0
<#
.SYNOPSIS
Prepara e valida a fase 1 (Power BI), sem automatizar login ou revisão visual.
.EXAMPLE
pwsh -File ./scripts/phase1_powerbi.ps1 -Mode Prepare
.EXAMPLE
pwsh -File ./scripts/phase1_powerbi.ps1 -Mode Validate -Port 59212
#>
[CmdletBinding()]
param(
    [ValidateSet('Prepare','Validate')][string]$Mode = 'Prepare',
    [ValidateRange(1,65535)][int]$Port,
    [switch]$StartPostgres
)
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskOriginalLocation = Get-Location
$taskSession = Join-Path $taskRoot ('artifacts/phase1/' + [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ') + '-' + [Guid]::NewGuid().ToString('N').Substring(0,8))
$taskSteps = [Collections.Generic.List[object]]::new()
$taskResult = 'FAILED'
$taskExit = 1
$taskPython = Join-Path $taskRoot '.venv/Scripts/python.exe'

function Invoke-PhaseStep {
    param([string]$Name,[scriptblock]$Action)
    $taskStarted = [DateTime]::UtcNow
    Write-Host "`n>> $Name" -ForegroundColor Cyan
    try {
        & $Action
        $taskSteps.Add([pscustomobject]@{name=$Name;status='PASSED';started_utc=$taskStarted.ToString('o');duration_seconds=[Math]::Round(([DateTime]::UtcNow-$taskStarted).TotalSeconds,2)})
    } catch {
        $taskSteps.Add([pscustomobject]@{name=$Name;status='FAILED';started_utc=$taskStarted.ToString('o');duration_seconds=[Math]::Round(([DateTime]::UtcNow-$taskStarted).TotalSeconds,2)})
        throw
    }
}
function Invoke-CheckedNative {
    param([string]$Executable,[string[]]$Arguments)
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) {throw "Falha na ferramenta $([IO.Path]::GetFileName($Executable)), codigo $LASTEXITCODE."}
}
function Get-DesktopPort {
    $taskCandidates = [Collections.Generic.List[int]]::new()
    $taskWorkspaceRoots = @(
        (Join-Path $env:USERPROFILE 'Microsoft/Power BI Desktop Store App/AnalysisServicesWorkspaces'),
        (Join-Path $env:LOCALAPPDATA 'Microsoft/Power BI Desktop/AnalysisServicesWorkspaces')
    )
    foreach ($taskWorkspaceRoot in $taskWorkspaceRoots) {
        if (Test-Path -LiteralPath $taskWorkspaceRoot) {
            foreach ($taskFile in Get-ChildItem -LiteralPath $taskWorkspaceRoot -Filter 'msmdsrv.port.txt' -Recurse -File) {
                $taskValue = [IO.File]::ReadAllText($taskFile.FullName).Replace([string][char]0,'').Trim()
                $taskCandidate = 0
                if ([int]::TryParse($taskValue,[ref]$taskCandidate) -and $taskCandidate -ge 1 -and $taskCandidate -le 65535) {
                    $taskClient = [Net.Sockets.TcpClient]::new()
                    try {
                        $taskPending = $taskClient.ConnectAsync('127.0.0.1',$taskCandidate)
                        if ($taskPending.Wait(1000) -and $taskClient.Connected) {$taskCandidates.Add($taskCandidate)}
                    } catch { } finally {$taskClient.Dispose()}
                }
            }
        }
    }
    $taskUnique = @($taskCandidates | Sort-Object -Unique)
    if ($taskUnique.Count -ne 1) {throw 'Nao foi encontrada exatamente uma porta ativa. Abra somente o PBIP deste projeto ou informe -Port. Veja o roteiro.'}
    return $taskUnique[0]
}

try {
    Set-Location -LiteralPath $taskRoot
    New-Item -ItemType Directory -Path $taskSession -Force | Out-Null
    Invoke-PhaseStep 'Pre-requisitos locais' {
        if (-not (Test-Path -LiteralPath $taskPython)) {throw 'Ambiente .venv ausente. Siga o setup documentado antes desta fase.'}
        if (-not (Test-Path -LiteralPath '.env')) {throw '.env local ausente. Configure as credenciais sem versiona-las.'}
        if (-not (Test-Path -LiteralPath 'powerbi/project/SalesProfitability.pbip')) {throw 'PBIP ausente.'}
        if ($env:POSTGRES_DB -and $env:POSTGRES_DB.EndsWith('_test')) {throw 'POSTGRES_DB aponta para testes. Use a base de desenvolvimento para comparar com o Desktop.'}
        Invoke-CheckedNative $taskPython @('-m','pip','check')
    }
    Invoke-PhaseStep 'Registro e copia dos arquivos versionados do Power BI' {
        $taskSha = & git rev-parse HEAD
        if ($LASTEXITCODE -ne 0) {throw 'Nao foi possivel identificar o commit.'}
        $taskStatus = @(& git status --short)
        if ($LASTEXITCODE -ne 0) {throw 'Nao foi possivel conferir o estado do Git.'}
        [pscustomobject]@{commit=$taskSha;changes=$taskStatus;powershell=$PSVersionTable.PSVersion.ToString();mode=$Mode;created_utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $taskSession 'environment.json') -Encoding utf8
        $taskFiles = @(& git -c core.quotepath=false ls-files -- powerbi)
        if ($LASTEXITCODE -ne 0) {throw 'Nao foi possivel listar o Power BI versionado.'}
        foreach ($taskRelative in $taskFiles) {
            $taskSource = Join-Path $taskRoot $taskRelative
            if (Test-Path -LiteralPath $taskSource -PathType Leaf) {
                $taskTarget = Join-Path $taskSession ('backup/' + $taskRelative)
                New-Item -ItemType Directory -Path (Split-Path -Parent $taskTarget) -Force | Out-Null
                Copy-Item -LiteralPath $taskSource -Destination $taskTarget
            }
        }
        # Nao inclui .env, cache .pbi, tokens ou credenciais salvas no Desktop.
    }
    if ($StartPostgres) {
        Invoke-PhaseStep 'Iniciar somente PostgreSQL do Compose deste projeto' {
            Invoke-CheckedNative 'docker' @('compose','up','-d','--wait','postgres')
        }
    }
    Invoke-PhaseStep 'Conferir warehouse existente, sem recarregar dados' {
        # Leitura SQL; o verificador grava apenas seu JSON em data/processed.
        Invoke-CheckedNative $taskPython @('scripts/verify_database.py')
        Copy-Item -LiteralPath 'data/processed/database-verification.json' -Destination (Join-Path $taskSession 'warehouse.json')
    }
    Invoke-PhaseStep 'Verificar segredos nos candidatos ao Git' {
        Invoke-CheckedNative $taskPython @('scripts/audit_repository.py')
    }
    Invoke-PhaseStep 'Validar estrutura PBIR' {
        Invoke-CheckedNative $taskPython @('scripts/verify_powerbi.py')
    }
    Invoke-PhaseStep 'Preparar bibliotecas oficiais Microsoft e validar TMDL' {
        # Sempre verifica SHA512 dos pacotes antes de carregar as bibliotecas.
        & (Join-Path $PSScriptRoot 'setup_powerbi_tools.ps1')
        & (Join-Path $PSScriptRoot 'verify_tmdl.ps1')
    }
    if ($Mode -eq 'Validate') {
        Invoke-PhaseStep 'Consultar o motor DAX ativo do Desktop' {
            $taskRuntimePort = if ($Port) {$Port} else {Get-DesktopPort}
            Write-Host "Porta local Analysis Services: $taskRuntimePort (nao e a porta PostgreSQL)."
            & (Join-Path $PSScriptRoot 'powerbi_query.ps1') -Port $taskRuntimePort -QueryFile 'powerbi/validation.dax' -Output (Join-Path $taskSession 'dax-totals.json')
            & (Join-Path $PSScriptRoot 'powerbi_query.ps1') -Port $taskRuntimePort -QueryFile 'powerbi/scenarios.dax' -Output (Join-Path $taskSession 'dax-scenarios.json')
            # Compare script existente le esses nomes fixos. Copias sao somente dos
            # resultados NOVOS desta sessao, nunca de uma execucao antiga.
            Copy-Item -LiteralPath (Join-Path $taskSession 'dax-totals.json') -Destination 'artifacts/powerbi-dax-results.json' -Force
            Copy-Item -LiteralPath (Join-Path $taskSession 'dax-scenarios.json') -Destination 'artifacts/powerbi-scenarios.json' -Force
        }
        Invoke-PhaseStep 'Conciliar oito totais e quatro cenarios com Python/PostgreSQL' {
            Invoke-CheckedNative $taskPython @('scripts/compare_powerbi.py')
            Copy-Item -LiteralPath 'artifacts/powerbi-parity.json' -Destination (Join-Path $taskSession 'parity.json')
            $taskParity = Get-Content -LiteralPath (Join-Path $taskSession 'parity.json') -Raw | ConvertFrom-Json
            if ($taskParity.passed -ne $true) {throw 'Paridade financeira reprovada.'}
            $taskDiscounts = @($taskParity.scenarios | ForEach-Object {[decimal]$_.discount} | Sort-Object)
            $taskExpectedDiscounts = @([decimal]0,[decimal]0.10,[decimal]0.20,[decimal]0.30)
            if ($taskDiscounts.Count -ne 4) {throw 'Cenarios incompletos ou duplicados.'}
            for ($taskDiscountIndex=0;$taskDiscountIndex -lt 4;$taskDiscountIndex++) {
                if ($taskDiscounts[$taskDiscountIndex] -ne $taskExpectedDiscounts[$taskDiscountIndex]) {throw 'Cenarios incorretos ou duplicados.'}
            }
        }
        $taskResult = 'AUTOMATED_CHECKS_PASSED_MANUAL_REVIEW_PENDING'
    } else {$taskResult = 'PREPARATION_PASSED_MANUAL_STEPS_REQUIRED'}
    $taskExit = 0
} catch {
    # Nao serializa mensagens de conectores, URLs de conexao ou credenciais.
    Write-Host 'Etapa reprovada. Consulte a ultima etapa acima e a secao de diagnostico do roteiro.' -ForegroundColor Red
} finally {
    if (Test-Path -LiteralPath $taskSession) {
        [pscustomobject]@{
            status=$taskResult;phase_complete=$false;mode=$Mode;finished_utc=[DateTime]::UtcNow.ToString('o');steps=@($taskSteps.ToArray())
            manual_pending=@('Autenticacao PostgreSQL e refresh no Desktop','Tabela calendario e relacoes','Revisao das cinco paginas','Filtros e estados vazios','What-if na interface','Acessibilidade e mobile','BPA com regras identificadas','Screenshots e demonstracao reais')
        } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $taskSession 'result.json') -Encoding utf8
        Write-Host "`nEvidencias locais: $taskSession"
        Write-Host "Resultado: $taskResult"
        Write-Host 'A fase so termina depois da revisao manual do roteiro docs/phase1-powerbi-runbook.md.'
    }
    Set-Location -LiteralPath $taskOriginalLocation
}
exit $taskExit
