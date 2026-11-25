param([ValidateSet('opencode','opencode2','cline-core','crush')][string]$Harness='opencode',[switch]$DryRun)
$ErrorActionPreference='Stop'
$packages=@{opencode='opencode-ai@1.19.6';opencode2='@opencode/cli@2.3.2';'cline-core'='cline@3.0.75';crush='@charmland/crush@0.102.0'}
$destination=Join-Path $PSScriptRoot "programs\harnesses\$Harness"
Write-Host "Install $($packages[$Harness]) in $destination"
if ($DryRun) { return }
$lockSource=Join-Path $PSScriptRoot "harnesses\locks\$Harness"
if (-not (Test-Path -LiteralPath (Join-Path $lockSource 'package-lock.json'))) { throw 'The tested dependency lock is missing' }
New-Item -ItemType Directory -Force -Path $destination | Out-Null
foreach ($filename in @('package.json','package-lock.json')) { Copy-Item -LiteralPath (Join-Path $lockSource $filename) -Destination (Join-Path $destination $filename) }
& npm ci --prefix $destination --no-audit --no-fund
if ($LASTEXITCODE -ne 0) { throw "Harness installation failed: $Harness" }
if ($Harness -eq 'cline-core') {
    $sdk=Join-Path $destination 'node_modules\@cline\sdk\package.json'
    if (-not (Test-Path -LiteralPath $sdk)) { throw 'Cline SDK not present in pinned Cline package' }
    if ((Get-Content -LiteralPath $sdk -Raw | ConvertFrom-Json).version -ne '0.2.1') { throw 'Expected Cline SDK0.2.1' }
}
$pythonAvailable=& uv python find 3.12 2>$null
if ($LASTEXITCODE -ne 0) {
    & uv python install 3.12
    if ($LASTEXITCODE -ne 0) { throw 'Python3.12 preparation failed' }
}
& uvx --python 3.12 --from freecad-mcp==0.1.31 freecad-mcp --help
if ($LASTEXITCODE -ne 0) { throw 'FreeCAD MCP preparation failed' }
Write-Host 'Harness and MCP prepared. See CAD-NEXT.md for startup.'
