param([Parameter(Mandatory=$true)][int]$Port,
      [string]$QueryFile='powerbi/validation.dax',
      [string]$Output='artifacts/powerbi-dax-results.json')
$ErrorActionPreference='Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
$taskLibrary = (Resolve-Path 'artifacts/adomd/lib/netcoreapp3.0').Path
Get-ChildItem -LiteralPath $taskLibrary -Filter '*.dll' | ForEach-Object {
    [Reflection.Assembly]::LoadFrom($_.FullName) | Out-Null
}
$taskConnection = New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection
$taskConnection.ConnectionString='Data Source=localhost:'+ $Port
try {
    $taskConnection.Open()
    $taskCommand=$taskConnection.CreateCommand()
    $taskCommand.CommandText=[IO.File]::ReadAllText((Join-Path $PWD $QueryFile))
    $taskReader=$taskCommand.ExecuteReader()
    $taskRows=@()
    while ($taskReader.Read()) {
        $taskRow=[ordered]@{}
        for ($taskIndex=0;$taskIndex -lt $taskReader.FieldCount;$taskIndex++) {
            $taskValue=$taskReader.GetValue($taskIndex)
            $taskRow[$taskReader.GetName($taskIndex)]=if ($taskValue -is [DBNull]) {$null} else {$taskValue.ToString([Globalization.CultureInfo]::InvariantCulture)}
        }
        $taskRows+=$taskRow
    }
    $taskReader.Close()
    $taskRows | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $Output -Encoding utf8
    $taskRows | ConvertTo-Json -Depth 5
} finally { $taskConnection.Close() }
