param([ValidateSet('rocm-gfx1151','vulkan')][string]$Backend='rocm-gfx1151',[ValidateSet('b12649-mix-c7059d6','b12631-mix-acc0843')][string]$Build='b12649-mix-c7059d6',[switch]$DryRun)
$ErrorActionPreference='Stop'
$tag=$Build
$name="app-$tag-windows-x64-$Backend.zip"
$url="https://github.com/unslothai/llama.cpp/releases/download/$tag/$name"
$hashesByBuild=@{
    'b12649-mix-c7059d6'=@{'rocm-gfx1151'='42fdb1a9a89d3d795d049e5a8abaa9981470790c3018229d125e1f27c90be867';vulkan='38f217096d87539a4274d39384854d06f9430f5a270e2c6c7c2892953be09a3b'}
    'b12631-mix-acc0843'=@{'rocm-gfx1151'='527d116574f3af0961f7daf1ebf6c36fb85f5b5cffb004feae3f340dc78f42ee';vulkan='e822862e815ca6f274a16c480f62876306d8a8cf83495000ea9fd395249de4c1'}
}
$hashes=$hashesByBuild[$tag]
$destination=Join-Path $PSScriptRoot "programs\llama-next\$tag-$Backend"
$archive=Join-Path $PSScriptRoot "programs\downloads\$name"
if ($DryRun) { Write-Output (@{url=$url;archive=$archive;sha256=$hashes[$Backend];destination=$destination;inference_started=$false} | ConvertTo-Json); return }
if (Test-Path -LiteralPath $destination) { throw "Destination already exists: $destination. Existing runtime was left unchanged." }
New-Item -ItemType Directory -Force -Path (Split-Path $archive -Parent) | Out-Null
if (-not (Test-Path -LiteralPath $archive)) {
    & curl.exe -L --fail -o ($archive+'.part') $url
    if ($LASTEXITCODE -ne 0) { throw "Download failed; partial file preserved at $archive.part" }
    if ((Get-FileHash -LiteralPath ($archive+'.part') -Algorithm SHA256).Hash.ToLowerInvariant() -ne $hashes[$Backend]) { throw 'Downloaded runtime SHA256 does not match' }
    Move-Item -LiteralPath ($archive+'.part') -Destination $archive
}
if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $hashes[$Backend]) { throw 'Runtime archive SHA256 does not match' }
Expand-Archive -LiteralPath $archive -DestinationPath $destination
$server=Get-ChildItem -LiteralPath $destination -Recurse -File -Filter 'llama-server.exe' | Select-Object -First 1
if (-not $server) { throw 'No llama-server.exe in verified runtime archive' }
Write-Host "Verified runtime extracted. Keep its DLLs together: $($server.FullName)"
Write-Host 'No inference was started. Register the matching GGUF/projector separately.'
