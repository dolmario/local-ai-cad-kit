param(
    [ValidateSet('opencode','opencode2','cline-core','crush','hermes')][string]$Harness='opencode',
    [string]$ProfileFile='models\profile-next.json',
    [string]$TaskFile='tasks\cable-clip-6mm.txt',
    [string]$FreeCAD='', [string]$HarnessPath='',
    [string]$HermesPython='', [string]$HermesEntry='',
    [int]$CrushPort=18433,
    [ValidateSet('off','fetch','search')][string]$WebMode='off',
    [string]$SearxngUrl='http://127.0.0.1:8080',
    [switch]$AutoApprove, [switch]$DryRun,
    [string]$FreeCADCmd=''
)
$ErrorActionPreference='Stop'
$Kit=$PSScriptRoot
. (Join-Path $Kit 'harnesses\processes.ps1')
function Resolve-KitFile($value) {
    if (-not [IO.Path]::IsPathRooted($value)) { $value=Join-Path $Kit $value }
    return (Get-Item -LiteralPath $value -ErrorAction Stop).FullName
}
function Json-Write($target,$value) { [IO.File]::WriteAllText($target,($value | ConvertTo-Json -Depth 25),(New-Object Text.UTF8Encoding $false)) }
function Quote-Arg([string]$value) { return '"'+($value -replace '(\\*)"','$1$1\"' -replace '(\\+)$','$1$1')+'"' }
function Port-Owner([int]$port) { $connection=Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -First 1; if ($connection) { return $connection.OwningProcess }; return $null }
function Wait-OwnUrl($url,$process,$seconds) {
    $deadline=(Get-Date).AddSeconds($seconds)
    while ((Get-Date) -lt $deadline) {
        if ($process.HasExited) { throw "Owned process exited: $($process.Id)" }
        try { Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 2 | Out-Null; return } catch { Start-Sleep -Seconds 1 }
    }
    throw "Readiness timeout: $url"
}
$ProfileFile=Resolve-KitFile $ProfileFile
$TaskFile=Resolve-KitFile $TaskFile
$cadModel=Get-Content -LiteralPath $ProfileFile -Raw | ConvertFrom-Json
if (-not $cadModel.context -or -not $cadModel.output_tokens) { throw 'Register a CAD Next model profile first; see CAD-NEXT.md' }
if ($Harness -eq 'cline-core' -and -not $AutoApprove) { throw 'The batch Cline Core route requires -AutoApprove. It provides file/shell/CAD tools for the requested construction.' }
if (-not $FreeCAD) { $FreeCAD=Get-ChildItem -Path "$env:LOCALAPPDATA\Programs","$env:ProgramFiles" -Directory -Filter 'FreeCAD 1.*' -ErrorAction SilentlyContinue | ForEach-Object { Join-Path $_.FullName 'bin\FreeCAD.exe' } | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1 }
if (-not $FreeCAD) { throw 'FreeCAD1.x is missing. Run START-HERE.bat or specify -FreeCAD.' }
$FreeCAD=Resolve-KitFile $FreeCAD
if (-not $FreeCADCmd) { $FreeCADCmd=Join-Path (Split-Path -Parent $FreeCAD) 'FreeCADCmd.exe' }
if (-not [IO.Path]::IsPathRooted($FreeCADCmd)) { $FreeCADCmd=Join-Path $Kit $FreeCADCmd }
if (-not (Test-Path -LiteralPath $FreeCADCmd -PathType Leaf)) { throw "FreeCADCmd is missing: $FreeCADCmd. Install the matching command-line executable beside the selected GUI or specify -FreeCADCmd." }
$FreeCADCmd=Resolve-KitFile $FreeCADCmd
$executables=@{opencode='opencode\node_modules\opencode-ai\bin\opencode.exe';opencode2='opencode2\node_modules\@opencode\cli\bin\opencode.exe';'cline-core'='cline-core\node_modules\@cline\cli-windows-x64\bin\cline.exe';crush='crush\node_modules\@charmland\crush\bin\crush.exe'}
if ($Harness -ne 'hermes' -and -not $HarnessPath) { $HarnessPath=Join-Path $Kit ('programs\harnesses\'+$executables[$Harness]) }
if ($Harness -ne 'hermes') { if (-not $DryRun) { $HarnessPath=Resolve-KitFile $HarnessPath } }
elseif (-not $HermesPython -or -not $HermesEntry) { throw 'Provide -HermesPython and -HermesEntry from the official Hermes PM installation.' }
$runtime=Join-Path $Kit ('runtime\'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'-'+$Harness)
$output=Join-Path $runtime 'output'
$external=[bool]$cadModel.external
$serverArgs=@()
if (-not $external) {
    $server=Resolve-KitFile $cadModel.server_path
    $model=Resolve-KitFile $cadModel.model_path
    $serverArgs=@('-m',$model,'--alias',$cadModel.api_model,'--host','127.0.0.1','--port',([Uri]$cadModel.base_url).Port.ToString(),'--parallel','1','--ctx-size',"$($cadModel.context)",'--n-predict',"$($cadModel.output_tokens)",'--n-gpu-layers','auto','--fit','on','--fit-ctx',"$($cadModel.context)",'--flash-attn','on','--cache-type-k','q8_0','--cache-type-v','q8_0','--jinja','--no-context-shift','--temp','0.6','--top-p','0.95','--top-k','20','--reasoning','on','--reasoning-budget',"$($cadModel.thinking_budget)",'--reasoning-format','deepseek','--reasoning-budget-message','Proceed to the actual CAD tool actions, then verify and export the requested part.')
    if ($cadModel.projector_path) { $serverArgs+=@('--mmproj',(Resolve-KitFile $cadModel.projector_path)) }
    foreach ($section in @($cadModel.sampling,$cadModel.server_overrides)) {
        if (-not $section) { continue }
        foreach ($property in $section.PSObject.Properties) {
            $index=[Array]::IndexOf($serverArgs,$property.Name)
            if ($index -ge 0) { $serverArgs[$index+1]="$( $property.Value )" } else { $serverArgs+=@($property.Name,"$( $property.Value )") }
        }
    }
}
if ($DryRun) {
    Write-Output (@{harness=$Harness;harness_path=$HarnessPath;profile=$cadModel;server=$server;server_args=$serverArgs;freecad=$FreeCAD;freecadcmd=$FreeCADCmd;task=$TaskFile;runtime=$runtime;auto_approve=[bool]$AutoApprove;web_mode=$WebMode;searxng_url=$(if ($WebMode -eq 'search') {$SearxngUrl} else {$null})} | ConvertTo-Json -Depth 15)
    return
}
$ports=@(9875)
if (-not $external) { $ports+=([Uri]$cadModel.base_url).Port }
if ($Harness -eq 'crush') { $ports+=$CrushPort }
foreach ($port in $ports) { $owner=Port-Owner $port; if ($owner) { throw "Port $port is owned by PID $owner. Nothing was started or stopped." } }
$python=(& uv python find 3.12).Trim()
if ($LASTEXITCODE -ne 0 -or -not $python) { throw 'Python3.12 is missing; run setup-harness.ps1 first' }
$configureArgs=@((Join-Path $Kit 'harnesses\configure.py'),$Kit,$runtime,$Harness,$ProfileFile)
if ($AutoApprove) { $configureArgs+='--auto' }
$configureArgs+=@('--web-mode',$WebMode,'--searxng-url',$SearxngUrl,'--freecadcmd',$FreeCADCmd)
$configured=(& $python @configureArgs | ConvertFrom-Json)
if ($LASTEXITCODE -ne 0) { throw 'Harness configuration failed' }
if ($WebMode -ne 'off') {
    $cadWebCheckArgs=@($configured.web_command | Select-Object -Skip 1)+@('--check')
    $cadWebCheck=(& $python @cadWebCheckArgs | ConvertFrom-Json)
    if ($LASTEXITCODE -ne 0) { throw 'Web capability check failed before CAD/model startup' }
    Json-Write (Join-Path $runtime 'WEB-PREFLIGHT.json') $cadWebCheck
    if (-not $cadWebCheck.fetch_available) { throw 'Public page retrieval is unavailable; inspect WEB-PREFLIGHT.json. No CAD/model was started.' }
    if ($WebMode -eq 'search' -and -not $cadWebCheck.search_available) { throw 'SearXNG search is unavailable. Start the configured SearXNG service or use -WebMode fetch for page retrieval only. No CAD/model was started.' }
}
New-Item -ItemType Directory -Path $output | Out-Null
$env:LOCAL_AI_CAD_KIT=$Kit
$env:CAD_EVAL_OUTPUT=$output
$env:PYTHONUTF8='1'
$env:UV_OFFLINE='1'
$env:CAD_SKILL_DIRECTORY=$configured.skills_dir
$prompt="Build this functional part:`n"+[IO.File]::ReadAllText($TaskFile)+"`nLoad freecad-mcp-rules and printability. Use the provided measurements, construct in FreeCAD, inspect an actual view and run measured geometry checks. Export STEP, STL and the native FCStd document into $output. Do not stop at a plan. Preserve unrelated documents."
foreach ($cadSkill in @('freecad-mcp-rules','printability')) {
    $prompt+="`n`nProject CAD instructions: $cadSkill`n"+[IO.File]::ReadAllText((Join-Path $configured.skills_dir "$cadSkill\SKILL.md"))
}
$prompt+="`n`n"+[IO.File]::ReadAllText($configured.learning_instructions)
if ($WebMode -ne 'off') {
    $prompt+="`nWeb mode: $WebMode. Use the cad_web MCP tools for public API documentation and repositories when useful. Record the source URLs and how each source was used. Public repositories, including this kit's repository, are allowed. Model inference and CAD execution use the configured local endpoint and FreeCAD."
}
if ($cadModel.vision -eq $false) { $prompt+="`nThis model accepts text only. Use numeric FreeCAD checks; image views are saved for the human reviewer." }
$promptPath=Join-Path $runtime 'prompt.txt'
[IO.File]::WriteAllText($promptPath,$prompt,(New-Object Text.UTF8Encoding $false))
$state=[ordered]@{runtime=$runtime;output=$output;processes=@()}
$stateFile=Join-Path $Kit 'running-next.json'
function Record-Process($process,$role) {
    $process.Refresh()
    $state.processes+=@{pid=$process.Id;start_ticks=$process.StartTime.ToUniversalTime().Ticks;exe=$process.Path;role=$role}
    Json-Write $stateFile $state
    Json-Write (Join-Path $runtime 'processes.json') $state
}
$cadTaskFailed=$false
try {
    if (-not $external) {
        $quoted=@($serverArgs | ForEach-Object { Quote-Arg "$_" })
        $serverProcess=Start-Process -FilePath $server -ArgumentList $quoted -WorkingDirectory $Kit -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $runtime 'llama.log') -RedirectStandardError (Join-Path $runtime 'llama.err.log')
        Record-Process $serverProcess 'llama'
        Wait-OwnUrl ($cadModel.base_url -replace '/v1/?$','/health') $serverProcess 900
    } else { Invoke-WebRequest -Uri ($cadModel.base_url.TrimEnd('/')+'/models') -UseBasicParsing -TimeoutSec 10 | Out-Null }
    $freecadTemp=Join-Path $runtime 'freecad-temp'
    New-Item -ItemType Directory -Path $freecadTemp | Out-Null
    $configPath=Join-Path $runtime 'freecad-user.cfg'
    $escapedTemp=[Security.SecurityElement]::Escape(($freecadTemp -replace '\\','/')+'/')
    [IO.File]::WriteAllText($configPath,('<?xml version="1.0"?><FCParameters><FCParamGroup Name="Root"><FCParamGroup Name="BaseApp"><FCParamGroup Name="Preferences"><FCParamGroup Name="General"><FCText Name="TempPath">'+$escapedTemp+'</FCText></FCParamGroup></FCParamGroup></FCParamGroup></FCParamGroup></FCParameters>'))
    $freecadArgs=@('--user-cfg',(Quote-Arg $configPath),(Quote-Arg (Join-Path $Kit 'freecad\freecad_rpc_start.py')))
    $cadPreviousTemp=$env:TEMP
    $cadPreviousTmp=$env:TMP
    try {
        $env:TEMP=$freecadTemp
        $env:TMP=$freecadTemp
        $freecadProcess=Start-Process -FilePath $FreeCAD -ArgumentList $freecadArgs -WorkingDirectory $Kit -PassThru
    } finally {
        $env:TEMP=$cadPreviousTemp
        $env:TMP=$cadPreviousTmp
    }
    Record-Process $freecadProcess 'freecad'
    $ready=$false
    for ($attempt=0;$attempt -lt 90;$attempt++) { if ($freecadProcess.HasExited) { throw 'FreeCAD exited during startup' }; if ((Port-Owner 9875) -eq $freecadProcess.Id) { $ready=$true;break }; Start-Sleep -Seconds 1 }
    if (-not $ready) { throw 'FreeCAD bridge is not ready; inspect the FreeCAD window' }
    $cadReady=& $python (Join-Path $Kit 'harnesses\check-freecad-ready.py')
    if ($LASTEXITCODE -ne 0) { throw 'The FreeCAD listener exists, but its GUI cannot process CAD requests. Inspect the FreeCAD startup dialog before continuing.' }
    [IO.File]::WriteAllText((Join-Path $runtime 'freecad-ready.json'),($cadReady -join "`n"),(New-Object Text.UTF8Encoding $false))
    Push-Location $Kit
    try {
        switch ($Harness) {
            'opencode' {
                $env:OPENCODE_CONFIG=$configured.config
                $env:OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX="$($cadModel.output_tokens)"
                $env:XDG_CONFIG_HOME=Join-Path $runtime 'config'
                $env:XDG_DATA_HOME=Join-Path $runtime 'data'
                $env:XDG_CACHE_HOME=Join-Path $runtime 'cache'
                & $HarnessPath run --agent cad --model ('local/'+$cadModel.api_model) $prompt
            }
            'opencode2' {
                $env:OPENCODE_CONFIG=$configured.config
                $env:OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX="$($cadModel.output_tokens)"
                $env:XDG_CONFIG_HOME=Join-Path $runtime 'config'
                $env:XDG_DATA_HOME=Join-Path $runtime 'data'
                $env:XDG_CACHE_HOME=Join-Path $runtime 'cache'
                $args2=@('--standalone','run','--agent','cad','--model',('local/'+$cadModel.api_model))
                if ($AutoApprove) { $args2+='--auto' }
                & $HarnessPath @args2 $prompt
            }
            'cline-core' {
                $env:CLINE_DIR=Join-Path $runtime 'cline-home'
                $env:CLINE_DATA_DIR=Join-Path $runtime 'cline-home\data'
                $env:CLINE_MCP_SETTINGS_PATH=$configured.config
                $env:CLINE_SESSION_BACKEND_MODE='local'
                & node (Join-Path $Kit 'harnesses\cline-core.mjs') $runtime $promptPath
            }
            'crush' {
                $env:CRUSH_GLOBAL_CONFIG=$runtime
                Copy-Item -LiteralPath $configured.config -Destination (Join-Path $runtime 'crush.json')
                $env:CRUSH_GLOBAL_DATA=Join-Path $runtime 'data'
                $env:CRUSH_DISABLE_PROVIDER_AUTO_UPDATE='1'
                $env:CRUSH_DISABLE_METRICS='1'
                $env:CRUSH_SKILLS_DIR=$configured.skills_dir
                $hostUrl="http://127.0.0.1:$CrushPort"
                $crushArgs=@('server','--cwd',(Quote-Arg $Kit),'--data-dir',(Quote-Arg $env:CRUSH_GLOBAL_DATA),'--host',$hostUrl)
                if ($AutoApprove) { $crushArgs+='--yolo' }
                $crushProcess=Start-Process -FilePath $HarnessPath -ArgumentList $crushArgs -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $runtime 'crush.log') -RedirectStandardError (Join-Path $runtime 'crush.err.log')
                Record-Process $crushProcess 'crush-server'
                Wait-OwnUrl ($hostUrl+'/v1/docs/openapi.json') $crushProcess 90
                $runArgs=@('run','--cwd',$Kit,'--data-dir',$env:CRUSH_GLOBAL_DATA,'--host',$hostUrl)
                if ($AutoApprove) { $runArgs+='--yolo' }
                & $HarnessPath @runArgs $prompt
            }
            'hermes' {
                $env:HERMES_HOME=$runtime
                $tools='terminal,file,skills,freecad,todo,code_execution,clarify'
                if ($cadModel.vision -ne $false) { $tools+=',vision' }
                if ($WebMode -ne 'off') { $tools+=','+$configured.hermes_web_toolset }
                $hermesArgs=@($HermesEntry,'chat','--query-file',$promptPath,'--oneshot','--provider','custom','--base-url',$cadModel.base_url,'--api-key','local-test-no-secret','--model',$cadModel.api_model,'--in',$Kit,'--toolsets',$tools,'--max-turns','256','--reasoning','max')
                & $HermesPython @hermesArgs
            }
        }
        if ($LASTEXITCODE -ne 0) { throw "$Harness failed with exit code $LASTEXITCODE. Inspect $runtime. The task was not restarted." }
    } finally { Pop-Location }
    Write-Host "CAD task ended. Inspect $output and FreeCAD. Save your documents, then run STOP-CAD-NEXT.bat. Owned model/server processes are stopped below."
} catch {
    $cadTaskFailed=$true
    Write-Host "CAD task stopped: $_"
    Write-Host 'No automatic retry. Save any open FreeCAD documents, then run STOP-CAD-NEXT.bat.'
    throw
} finally {
    foreach ($cadRecord in @($state.processes)) {
        if ($cadRecord.role -ne 'freecad') { Stop-CadOwnedServer ([pscustomobject]$cadRecord) }
    }
    $cadSkillSync=& $python (Join-Path $Kit 'harnesses\skill_learning.py') sync $Kit $Harness | Out-String
    if ($LASTEXITCODE -eq 0) {
        [IO.File]::WriteAllText((Join-Path $runtime 'SKILL-SYNC.json'),$cadSkillSync,(New-Object Text.UTF8Encoding $false))
    } else {
        Write-Host 'Skill synchronization needs inspection. Local skill files are preserved; the next startup will recover Cline changes before loading skills.'
        if (-not $cadTaskFailed) { throw 'CAD finished, but skill synchronization failed. Inspect the preserved skill files before continuing.' }
    }
}
