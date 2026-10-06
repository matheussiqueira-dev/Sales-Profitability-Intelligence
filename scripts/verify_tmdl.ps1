$ErrorActionPreference='Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
$taskLibrary=(Resolve-Path 'artifacts/tom/lib/netcoreapp3.0').Path
Get-ChildItem -LiteralPath $taskLibrary -Filter '*.dll' | ForEach-Object {[Reflection.Assembly]::LoadFrom($_.FullName)|Out-Null}
$taskDefinition=Join-Path $PWD 'powerbi/project/SalesProfitability.SemanticModel/definition'
$taskDatabase=[Microsoft.AnalysisServices.Tabular.TmdlSerializer]::DeserializeDatabaseFromFolder($taskDefinition)
if (-not $taskDatabase.Model.Tables.Contains('fact_sales')) {throw 'Missing fact table'}
if ($taskDatabase.Model.Tables.Find('fact_sales').Measures.Count -lt 26) {throw 'Missing financial measures'}
$taskKeys=@('date_key','customer_key','product_key','channel_key','seller_key')
foreach ($taskKey in $taskKeys) {
    $taskRelationships=@($taskDatabase.Model.Relationships | Where-Object {$_.FromTable.Name -eq 'fact_sales' -and $_.FromColumn.Name -eq $taskKey})
    if ($taskRelationships.Count -ne 1) {throw ('Missing/ambiguous relation: '+$taskKey)}
}
Write-Output 'Microsoft TMDL parser and star-schema structure passed. This does not execute DAX.'
