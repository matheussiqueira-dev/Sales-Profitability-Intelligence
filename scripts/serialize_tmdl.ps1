param([string]$LibraryPath = 'artifacts/tom/lib/netcoreapp3.0')
$ErrorActionPreference='Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
$taskLibrary = (Resolve-Path -LiteralPath $LibraryPath).Path
Get-ChildItem -LiteralPath $taskLibrary -Filter '*.dll' | ForEach-Object {
    [Reflection.Assembly]::LoadFrom($_.FullName) | Out-Null
}
$taskModelPath = Join-Path $PWD 'artifacts/powerbi/model.bim'
$taskModel = [Microsoft.AnalysisServices.Tabular.JsonSerializer]::DeserializeDatabase([IO.File]::ReadAllText($taskModelPath))
$taskDefinition = Join-Path $PWD 'powerbi/project/SalesProfitability.SemanticModel/definition'
[Microsoft.AnalysisServices.Tabular.TmdlSerializer]::SerializeDatabaseToFolder($taskModel,$taskDefinition)
# Validate the actual serialized definition with Microsoft's parser.
$taskParsed = [Microsoft.AnalysisServices.Tabular.TmdlSerializer]::DeserializeDatabaseFromFolder($taskDefinition)
Write-Output ('TMDL parsed: '+$taskParsed.Model.Tables.Count+' tables, '+$taskParsed.Model.Relationships.Count+' relationships')
