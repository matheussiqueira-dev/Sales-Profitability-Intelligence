param([Parameter(Mandatory=$true)][int]$Port,
      [ValidateSet('Snapshot','PostgreSQL')][string]$SourceMode='Snapshot')
$ErrorActionPreference='Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
$taskLibrary=(Resolve-Path 'artifacts/tom/lib/netcoreapp3.0').Path
Get-ChildItem -LiteralPath $taskLibrary -Filter '*.dll' | ForEach-Object {[Reflection.Assembly]::LoadFrom($_.FullName)|Out-Null}
$taskServer=New-Object Microsoft.AnalysisServices.Tabular.Server
try {
    $taskServer.Connect('Data Source=localhost:'+$Port)
    if ($taskServer.Databases.Count -ne 1) {throw 'Expected one local Power BI model.'}
    $taskModel=$taskServer.Databases[0].Model
    if (-not $taskModel.Tables.Contains('fact_sales')) {throw 'Unexpected semantic model.'}
    $taskParameter=$taskModel.Tables.Find('Desconto Simulado')
    $taskModel.Expressions.Find('SourceMode').Expression='"'+$SourceMode+'" meta [IsParameterQuery=true,Type="Text",IsParameterQueryRequired=true]'
    $taskParameter.Partitions[0].Source.Expression='GENERATESERIES(CURRENCY(0),CURRENCY(0.30),CURRENCY(0.01))'
    $taskParameter.Columns.Find('Value').DataType=[Microsoft.AnalysisServices.Tabular.DataType]::Decimal
    $taskSource=Get-Content -LiteralPath 'artifacts/powerbi/model.bim' -Raw | ConvertFrom-Json
    $taskFact=($taskSource.model.tables | Where-Object {$_.name -eq 'fact_sales'})
    foreach ($taskMeasure in $taskFact.measures) {
        $taskModel.Tables.Find('fact_sales').Measures.Find($taskMeasure.name).Expression=$taskMeasure.expression
    }
    $taskModel.RequestRefresh([Microsoft.AnalysisServices.Tabular.RefreshType]::Calculate)
    $taskModel.SaveChanges() | Out-Null
    Write-Output 'Local Power BI discount parameter recalculated with exact fixed decimals.'
} finally {$taskServer.Disconnect()}
