param(
    [ValidateSet('opencode','opencode2','cline-core','crush','hermes')][string]$Harness = 'opencode',
    [string]$ProfileFile = 'models\profile-next.json',
    [string]$TaskFile = 'tasks\cable-clip-6mm.txt',
    [ValidateSet('search','off')][string]$WebMode = 'search',
    [string]$SearxngUrl = 'http://127.0.0.1:8080',
    [string]$FreeCAD, [string]$FreeCADCmd, [string]$HarnessPath,
    [string]$HermesPython, [string]$HermesEntry,
    [int]$CrushPort = 18433,
    [switch]$AutoApprove, [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$taskPath = $TaskFile
if (-not [IO.Path]::IsPathRooted($taskPath)) {
    $taskPath = Join-Path $PSScriptRoot $taskPath
}
$taskPath = (Get-Item -LiteralPath $taskPath -ErrorAction Stop).FullName
$originalTask = [IO.File]::ReadAllText($taskPath)

$sourceRules = @'
Retain the original measurement brief and distinguish its specified dimensions from dimensions obtained through research.
When the task needs outside dimensions, find a primary source. Record each adopted dimension in web-sources.json beside the CAD outputs with the value, unit, part or revision, original URL, page/table/section, and access date. Mark an external dimension without a supporting source as unverified. Do not replace an explicitly specified test dimension with a convenient number from the web. Report dimensions measured on the finished CAD geometry separately.
Use web documentation for FreeCAD methods as needed. Report the public pages actually retrieved and how they informed the work. A search result alone is not a retrieved page. If no external dimension was adopted, report that all specified dimensions came from the supplied brief when that is true.
'@
if ($WebMode -eq 'off') {
    $sourceRules = @'
Run this explicit offline comparison using the supplied dimensions. Record that the search adapter was off. Identify any missing external dimension as unverified and keep it separate from values stated in the task and those measured on the finished CAD geometry.
'@
}
$briefDir = Join-Path $PSScriptRoot 'runtime\web-briefs'
[IO.Directory]::CreateDirectory($briefDir) | Out-Null
$combined = Join-Path $briefDir (([Guid]::NewGuid().ToString('N')) + '.txt')
[IO.File]::WriteAllText($combined, $originalTask + [Environment]::NewLine + [Environment]::NewLine + $sourceRules, (New-Object Text.UTF8Encoding $false))

$launch = @{
    Harness = $Harness; ProfileFile = $ProfileFile; TaskFile = $combined;
    WebMode = $WebMode; SearxngUrl = $SearxngUrl; CrushPort = $CrushPort;
    AutoApprove = $AutoApprove; DryRun = $DryRun
}
foreach ($key in 'FreeCAD','FreeCADCmd','HarnessPath','HermesPython','HermesEntry') {
    if ($PSBoundParameters.ContainsKey($key)) { $launch[$key] = $PSBoundParameters[$key] }
}
& (Join-Path $PSScriptRoot 'start-cad-next.ps1') @launch
