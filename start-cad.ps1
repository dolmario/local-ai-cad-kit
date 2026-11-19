# Local AI CAD Kit - start everything: llama.cpp server (Qwen with vision), FreeCAD with the MCP bridge, opencode.
# Reads models\profile.json written by the installer (big = Qwen3.8 27B on the GPU, medium = Qwen3.6 35B-A3B with experts in RAM).
# Test mode (no typing): -TestCommand beschreibung -TestArgs "cable clip ..." runs one slash command with "opencode run",
# saves the answer to output\test-<time>.txt and then stops ONLY the two processes this script started (by PID).
param([int]$Port = 18080, [switch]$DryRun, [string]$TestCommand = "", [string]$TestArgs = "", [string]$Profile = "")
$ErrorActionPreference = "Stop"
$Kit = $PSScriptRoot
$Server = Join-Path $Kit "programs\llama.cpp\llama-server.exe"
$Models = Join-Path $Kit "models"
$ProfileFile = Join-Path $Models "profile.json"
# -Profile <name> starts another installed model (models\profile-<name>.json, created by START-HERE.bat -ModelProfile <name>) and makes it the default.
if ($Profile) {
    $chosen = Join-Path $Models "profile-$Profile.json"
    if (-not (Test-Path $chosen)) { throw "No installed profile '$Profile'. Install it first: START-HERE.bat -ModelProfile $Profile" }
    Copy-Item $chosen $ProfileFile -Force
}

function Wait-Url($url, $seconds, $what) {
    $end = (Get-Date).AddSeconds($seconds)
    while ((Get-Date) -lt $end) {
        try { Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 3 | Out-Null; return } catch { Start-Sleep -Seconds 2 }
    }
    throw "$what did not answer within $seconds s ($url)."
}
function Wait-Port($port, $seconds, $what) {
    $end = (Get-Date).AddSeconds($seconds)
    while ((Get-Date) -lt $end) {
        $c = New-Object Net.Sockets.TcpClient
        try { $c.Connect("127.0.0.1", $port); $c.Close(); return } catch { Start-Sleep -Seconds 2 } finally { $c.Dispose() }
    }
    throw "$what did not open port $port within $seconds s."
}

if (-not (Test-Path $ProfileFile)) { throw "models\profile.json missing. Run START-HERE.bat first." }
$prof = Get-Content $ProfileFile -Raw | ConvertFrom-Json
# profile "external" = your own server (Ollama, LM Studio, ...): nothing is started here except FreeCAD and opencode.
$External = ($prof.profile -eq "external")
if (-not $External) {
    if (-not (Test-Path $Server)) { throw "llama-server.exe missing. Run START-HERE.bat first." }
    $Model = Join-Path $Models $prof.model
    $Proj = Join-Path $Models $prof.projector
    foreach ($f in @($Model, $Proj)) { if (-not (Test-Path $f)) { throw "Missing model file: $f. Run START-HERE.bat again (downloads resume)." } }
}

# Paths are quoted: Start-Process in Windows PowerShell 5.1 joins arguments without quoting.
if (-not $External) { $ServerArgs = @("-m", "`"$Model`"", "--mmproj", "`"$Proj`"", "--alias", "local-cad", "--host", "127.0.0.1", "--port", "$Port",
          "--parallel", "1", "--ctx-size", "$($prof.ctx)", "--n-gpu-layers", "999", "--flash-attn", "on",
          "--cache-type-k", "q8_0", "--cache-type-v", "q8_0", "--jinja",
          "--no-context-shift", "--temp", "0.6", "--top-p", "0.95", "--top-k", "20") + $(if ($prof.reasoning -eq $false) { @() } else { @("--reasoning", "on", "--reasoning-budget", "6144", "--reasoning-format", "deepseek") }) + @($prof.extra) }
$FreeCad = Get-ChildItem -Path "$env:LOCALAPPDATA\Programs", "$env:ProgramFiles" -Filter "FreeCAD 1.*" -Directory -ErrorAction SilentlyContinue |
           ForEach-Object { Join-Path $_.FullName "bin\freecad.exe" } | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $FreeCad) { throw "FreeCAD 1.x not found." }

if ($DryRun) {
    if ($External) { Write-Host "(dry run) external server $($prof.baseUrl), model $($prof.apiModel)" }
    else {
        Write-Host "(dry run) profile $($prof.profile): $($prof.model) on $($prof.gpu)"
        Write-Host "(dry run) $Server $($ServerArgs -join ' ')"
    }
    Write-Host "(dry run) $FreeCad $(Join-Path $Kit 'freecad\freecad_rpc_start.py')"
    Write-Host "(dry run) OPENCODE_CONFIG=$(Join-Path $Kit 'opencode.runtime.json') opencode  (in $Kit)"
    return
}

# Never reuse or touch something that is already running: if a port is taken, stop and explain.
function Port-Owner($p) {
    $c = Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($c) { return $c.OwningProcess } else { return $null }
}
$portChecks = @(@(9875, "FreeCAD MCP bridge (close the other FreeCAD first)"))
if (-not $External) { $portChecks = @(@($Port, "model server (use START-CAD.bat -Port <free port>)")) + $portChecks }
foreach ($pp in $portChecks) {
    $owner = Port-Owner $pp[0]
    if ($owner) {
        $name = (Get-Process -Id $owner -ErrorAction SilentlyContinue).ProcessName
        throw "Port $($pp[0]) is already used by '$name' (PID $owner): $($pp[1]). Nothing was started or stopped."
    }
}
function Wait-Own($p, $proc, $seconds, $what) {
    $end = (Get-Date).AddSeconds($seconds)
    while ((Get-Date) -lt $end) {
        if ($proc.HasExited) { throw "$what exited early (exit code $($proc.ExitCode))." }
        $owner = Port-Owner $p
        if ($owner) {
            if ($owner -ne $proc.Id) { throw "Port $p was taken by another process (PID $owner), not by $what. Stopping." }
            return
        }
        Start-Sleep -Seconds 2
    }
    throw "$what did not open port $p within $seconds s."
}

if ($External) {
    Write-Host "==> Using your model server $($prof.baseUrl) (model $($prof.apiModel))" -ForegroundColor Cyan
    $serverProc = $null
    Wait-Url "$($prof.baseUrl)/models" 30 "your model server (is Ollama / LM Studio running with the server enabled?)"
} else {
Write-Host "==> Starting the local model server ($($prof.model)); the first start can take several minutes (large model loads into memory) - please wait, do not close this window" -ForegroundColor Cyan
# The server log is kept (logs\llama-server.log, logs\llama-server.err.log) so a crash can be diagnosed: send these two files when you report a problem.
New-Item -ItemType Directory -Force -Path (Join-Path $Kit "logs") | Out-Null
$serverProc = Start-Process -FilePath $Server -ArgumentList $ServerArgs -WindowStyle Minimized -PassThru -RedirectStandardOutput (Join-Path $Kit "logs\llama-server.log") -RedirectStandardError (Join-Path $Kit "logs\llama-server.err.log")
Wait-Own $Port $serverProc 900 "llama-server"
Wait-Url "http://127.0.0.1:$Port/health" 900 "llama-server"
}

Write-Host "==> Starting FreeCAD with the MCP bridge (port 9875)" -ForegroundColor Cyan
$freecadProc = Start-Process -FilePath $FreeCad -ArgumentList "`"$(Join-Path $Kit 'freecad\freecad_rpc_start.py')`"" -PassThru
Wait-Own 9875 $freecadProc 180 "FreeCAD"
Set-Content -Path (Join-Path $Kit "running.txt") -Value ("llama-server PID {0}`r`nFreeCAD PID {1}`r`nRun STOP-CAD.bat when you are done." -f $(if ($serverProc) { $serverProc.Id } else { "(your own server)" }), $freecadProc.Id)

# Runtime copy of opencode.json with absolute paths, so the MCP servers start no matter which folder opencode uses.
$cfg = Get-Content (Join-Path $Kit "opencode.json") -Raw | ConvertFrom-Json
$cfg.provider.local.models.'local-cad'.limit.context = [int]$prof.ctx
if ($External) {
    $cfg.provider.local.options.baseURL = $prof.baseUrl
    $m = $cfg.provider.local.models.'local-cad'
    $m.name = "$($prof.apiModel) (your server)"
    $cfg.provider.local.models = [pscustomobject]@{ ($prof.apiModel) = $m }
    $cfg.model = "local/$($prof.apiModel)"
} else {
    $cfg.provider.local.options.baseURL = "http://127.0.0.1:$Port/v1"
    $cfg.provider.local.models.'local-cad'.name = "$($prof.model -replace '\.gguf$','') (local, vision)"
}
$cfg.mcp.'photo-measure'.command = @("uv", "run", "--project", (Join-Path $Kit "foto-mcp"), "python", (Join-Path $Kit "foto-mcp\foto_mcp.py"))
# Skills (key-cap, drawing-to-part, printability, photo-vs-caliper, freecad-mcp-rules) and the absolute kit path for them.
$cfg | Add-Member -NotePropertyName skills -NotePropertyValue @((Join-Path $Kit "skills")) -Force
[IO.File]::WriteAllText((Join-Path $Kit "kit-path.txt"), ($Kit -replace "\\", "/"), (New-Object Text.UTF8Encoding $false))
# Same path in the user profile: FreeCAD scripts (cad_helpers.py) find the kit from there, wherever it was unpacked.
[IO.File]::WriteAllText((Join-Path $env:USERPROFILE ".local-ai-cad-kit-path.txt"), ($Kit -replace "\\", "/"), (New-Object Text.UTF8Encoding $false))
$runtime = Join-Path $Kit "opencode.runtime.json"
[IO.File]::WriteAllText($runtime, ($cfg | ConvertTo-Json -Depth 20), (New-Object Text.UTF8Encoding $false))
New-Item -ItemType Directory -Force -Path (Join-Path $Kit "output") | Out-Null

if ($TestCommand) {
    $env:OPENCODE_CONFIG = $runtime
    Set-Location $Kit
    $log = Join-Path (Join-Path $Kit "output") ("test-" + (Get-Date -Format "yyyyMMdd-HHmmss") + "-" + $TestCommand + ".txt")
    Write-Host "==> Test: /$TestCommand $TestArgs  (answer -> $log)" -ForegroundColor Cyan
    $t0 = Get-Date
    $rc = 1
    try {
        # Windows PowerShell 5.1 turns the first stderr line of a native program into a terminating error when
        # ErrorActionPreference is Stop. Switch to Continue for this call and write every line as text.
        $ErrorActionPreference = "Continue"
        & opencode run --command $TestCommand $TestArgs 2>&1 | ForEach-Object { $_.ToString() } | Tee-Object -FilePath $log
        $rc = $LASTEXITCODE
        $ErrorActionPreference = "Stop"
    } finally {
        Add-Content -Path $log -Value ("`r`n[kit] exit code {0}, {1:N0} s" -f $rc, ((Get-Date) - $t0).TotalSeconds)
        foreach ($p in @($freecadProc, $serverProc)) { if ($p -and -not $p.HasExited) { Stop-Process -Id $p.Id } }
        Remove-Item (Join-Path $Kit "running.txt") -ErrorAction SilentlyContinue
    }
    exit $rc
}

Write-Host "==> Ready. When you are done: type /exit, then double-click STOP-CAD.bat (frees graphics memory and RAM)." -ForegroundColor Cyan
Write-Host "==> Starting opencode. Use /kappe, /zeichnung, /beschreibung or /pruefen, for example:" -ForegroundColor Cyan
Write-Host "    /beschreibung cable clip for a 6 mm cable, 3 mm wall, screw hole 3.5 mm" -ForegroundColor Green
$env:OPENCODE_CONFIG = $runtime
Set-Location $Kit
opencode
