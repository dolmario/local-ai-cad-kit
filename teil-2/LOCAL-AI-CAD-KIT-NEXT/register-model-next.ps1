param(
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-z0-9-]+$')][string]$Name,
    [Parameter(Mandatory=$true)][string]$Model,
    [Parameter(Mandatory=$true)][string]$Server,
    [string]$Projector='', [string]$Draft='', [switch]$TextOnly,
    [ValidateSet('qwen','flint','inkling')][string]$Sampling='qwen',
    [int]$Context=262144, [int]$OutputTokens=131072, [int]$ThinkingBudget=-1
)
$ErrorActionPreference='Stop'
if ($Context -le 0 -or $OutputTokens -le 0 -or $OutputTokens -gt $Context) { throw 'Invalid context/output limits' }
if ($ThinkingBudget -lt -1 -or $ThinkingBudget -gt $OutputTokens) { throw 'ThinkingBudget must be -1 (no separate cap) or within the total output limit' }
function Full-File($value) { return (Get-Item -LiteralPath $value -ErrorAction Stop).FullName }
$data=[ordered]@{name=$Name;model_path=(Full-File $Model);server_path=(Full-File $Server);projector_path='';vision=(-not $TextOnly);context=$Context;output_tokens=$OutputTokens;thinking_budget=$ThinkingBudget;api_model='local-cad';base_url='http://127.0.0.1:18080/v1';sampling=@{};server_overrides=@{}}
if ($Projector) { $data.projector_path=Full-File $Projector }
if (-not $TextOnly -and -not $Projector) { throw 'A vision profile needs its matching projector; use -TextOnly for a text model' }
if ($Sampling -eq 'flint') { $data.sampling=@{'--temp'=1;'--top-p'=0.95;'--top-k'=20} }
if ($Sampling -eq 'inkling') { $data.sampling=@{'--temp'=1;'--top-p'=1;'--top-k'=0;'--min-p'=0} }
if ($Draft) { $data.server_overrides=@{'--model-draft'=(Full-File $Draft);'--spec-type'='draft-dspark';'--spec-draft-n-max'=2;'--n-gpu-layers-draft'=99} }
$folder=Join-Path $PSScriptRoot 'models'
New-Item -ItemType Directory -Force -Path $folder | Out-Null
$destination=Join-Path $folder "profile-next-$Name.json"
if (Test-Path -LiteralPath $destination) { Copy-Item -LiteralPath $destination -Destination ($destination+'.'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'.bak') }
$json=$data | ConvertTo-Json -Depth 12
[IO.File]::WriteAllText($destination,$json,(New-Object Text.UTF8Encoding $false))
[IO.File]::WriteAllText((Join-Path $folder 'profile-next.json'),$json,(New-Object Text.UTF8Encoding $false))
Write-Host "Registered $Name. Start: START-CAD-NEXT.bat -ProfileFile models\profile-next-$Name.json"
