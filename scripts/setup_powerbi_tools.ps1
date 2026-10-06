$ErrorActionPreference='Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
# Official Microsoft NuGet libraries, local artifacts only; no global installation.
$taskVersion='19.84.1'
$taskPackages=@{
    tom='microsoft.analysisservices.netcore.retail.amd64'
    adomd='microsoft.analysisservices.adomdclient.netcore.retail.amd64'
}
$taskHashes=@{
    tom='C16F4BD11AC84930393F4A5629F077A0B352D1705FC6DEB7D817A8F70D51A4DF987E58AF3146ACAD3F2299389371D2F716E212E1B397B58FA6EF0765C1545D3B'
    adomd='2F3B2350167267A133328CBDCF7E74600A98B712F4EB2428F25B48DCDA7D77E3D34ED018B55C3AA8A8DE5813578161433A4BA17912752F11E587432AB0F010A7'
}
foreach ($taskName in $taskPackages.Keys) {
    $taskPackage=$taskPackages[$taskName]
    $taskBase='https://api.nuget.org/v3-flatcontainer/'+$taskPackage+'/'+$taskVersion+'/'+$taskPackage+'.'+$taskVersion+'.nupkg'
    $taskArchive=Join-Path $PWD ('artifacts/'+$taskName+'.zip')
    New-Item -ItemType Directory -Path (Split-Path -Parent $taskArchive) -Force | Out-Null
    Invoke-WebRequest -Uri $taskBase -OutFile $taskArchive
    $taskExpected=$taskHashes[$taskName]
    $taskActual=(Get-FileHash -LiteralPath $taskArchive -Algorithm SHA512).Hash
    if ($taskActual -ne $taskExpected) {throw ('NuGet hash mismatch: '+$taskPackage)}
    Expand-Archive -LiteralPath $taskArchive -DestinationPath (Join-Path $PWD ('artifacts/'+$taskName)) -Force
}
Write-Output 'Microsoft TOM/ADOMD 19.84.1 downloaded and SHA512 verified locally.'
