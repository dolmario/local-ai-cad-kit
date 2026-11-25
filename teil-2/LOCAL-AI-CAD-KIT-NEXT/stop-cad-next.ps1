param([string]$StateFile='')
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'harnesses\processes.ps1')
if (-not $StateFile) { $StateFile=Join-Path $PSScriptRoot 'running-next.json' }
if (-not (Test-Path -LiteralPath $StateFile)) { Write-Host 'No CAD Next processes recorded.'; return }
$state=Get-Content -LiteralPath $StateFile -Raw | ConvertFrom-Json
foreach ($record in @($state.processes)) {
    $process=Get-CadOwnedProcess $record
    if (-not $process) { continue }
    if ($record.role -eq 'freecad') {
        Write-Host 'Save your open FreeCAD documents before closing FreeCAD.'
        if (-not $process.CloseMainWindow()) { Write-Host 'FreeCAD could not be closed automatically; close it in its window.' }
    } else { Stop-CadOwnedServer $record }
}
Write-Host 'Owned model/server processes stopped. FreeCAD may ask you to save.'
