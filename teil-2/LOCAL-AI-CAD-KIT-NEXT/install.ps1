# Local AI CAD Kit - installer (Windows 10/11)
# Installs: FreeCAD 1.1, uv, Node.js LTS, opencode, llama.cpp (CUDA or Vulkan), a Qwen vision model chosen for your GPU,
# the FreeCAD-MCP addon and the photo-measure MCP server of this kit. Everything except the winget programs
# stays inside this folder. Run via START-HERE.bat. Use -DryRun to only print what would happen.
param(
    [switch]$DryRun,
    [switch]$SkipModel,
    [string]$ModelProfile = "",   # big | medium | small | mini | custom (empty = chosen from your hardware)
    [string]$ModelRepo = "",      # custom: Hugging Face repo with GGUF files, e.g. unsloth/Qwen3.5-9B-GGUF
    [string]$ModelFile = "",      # custom: the .gguf file inside that repo (a vision model with an F16 mmproj file)
    [int]$Ctx = 0,                # custom: context size (default 32768)
    [int]$CpuMoe = 0,
    [string]$ExternalUrl = "",    # Ollama / LM Studio / any OpenAI-compatible server you already run, e.g. http://127.0.0.1:11434/v1
    [string]$ExternalModel = "",  # the model name exactly as that server lists it, e.g. qwen3-vl:8b
             # custom: for MoE models, number of layers whose experts stay in RAM (e.g. 99)
    [string]$LlamaTag = "b11580",
    [string]$FreecadMcpVersion = "0.1.31"
)
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$Kit = $PSScriptRoot
$Programs = Join-Path $Kit "programs"
$Models = Join-Path $Kit "models"
$Log = Join-Path $Kit "install.log"
if ($Kit -match '(?i)\\Temp\\|\.zip') { throw "This folder looks like a ZIP preview or a temp folder ($Kit). Please unpack the whole ZIP (right click > Extract all) to a normal folder such as C:\local-ai-cad-kit and run START-HERE.bat there." }
if ($Kit -match '\s') { Write-Host "Warning: the folder path contains spaces ($Kit). If something fails, move the kit to a path without spaces such as C:\local-ai-cad-kit." -ForegroundColor Yellow }

function Say($msg) { Write-Host ""; Write-Host "==> $msg" -ForegroundColor Cyan; if (-not $DryRun) { Add-Content -Path $Log -Value ("[{0}] {1}" -f (Get-Date -Format s), $msg) } }
function Do-Step($what, [scriptblock]$action) {
    if ($DryRun) { Write-Host "    (dry run) $what" -ForegroundColor Yellow; return }
    & $action
}
function Refresh-Path {
    $m = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $u = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$m;$u"
}
function Have($cmd) { return [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }
function Winget-Install($id, $name) {
    Say "Installing $name ($id) with winget"
    if (-not (Have "winget") -and -not $DryRun) { throw "winget is missing and $name must be installed. Install 'App Installer' from the Microsoft Store, or install $name yourself and run this again." }
    Do-Step "winget install --id $id" {
        winget install --id $id --exact --silent --accept-package-agreements --accept-source-agreements
        if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne -1978335189) { throw "winget could not install $name (exit $LASTEXITCODE)." }
        Refresh-Path
    }
}
function Download($url, $target) {
    Do-Step "download $url -> $target" {
        # curl.exe ships with Windows 10/11; -C - resumes an interrupted download.
        & curl.exe -L --fail --retry 3 -C - -o $target $url
        if ($LASTEXITCODE -ne 0) { throw "Download failed: $url" }
    }
}

if (-not $DryRun) { "" | Set-Content -Path $Log }
Say "Local AI CAD Kit installer. Folder: $Kit"

# 0. Checks
# winget is only needed when a program is missing (checked in Winget-Install), so a PC that already has FreeCAD, uv, Node.js and opencode does not need it.
$freeGB = [math]::Round((Get-PSDrive -Name ($Kit.Substring(0,1))).Free / 1GB, 1)
Say "Free disk space on this drive: $freeGB GB (about 30 GB needed with the model)"
if (-not $SkipModel -and $freeGB -lt 30 -and -not $DryRun) { throw "Not enough free disk space for the model." }

# 1. Programs via winget
if (-not (Get-ChildItem -Path "$env:LOCALAPPDATA\Programs", "$env:ProgramFiles" -Filter "FreeCAD 1.*" -Directory -ErrorAction SilentlyContinue)) {
    Winget-Install "FreeCAD.FreeCAD" "FreeCAD"
} else { Say "FreeCAD already installed" }
if (-not (Have "uv")) { Winget-Install "astral-sh.uv" "uv (Python package manager)" } else { Say "uv already installed" }
if (-not (Have "npm")) { Winget-Install "OpenJS.NodeJS.LTS" "Node.js LTS" } else { Say "Node.js already installed" }

# 2. opencode (terminal AI agent)
if (-not (Have "opencode")) {
    Say "Installing opencode 1.19.0 (npm package opencode-ai, the version we tested)"
    Do-Step "npm install -g opencode-ai@1.19.0" { npm install -g opencode-ai@1.19.0; if ($LASTEXITCODE -ne 0) { throw "npm could not install opencode." }; Refresh-Path }
} else {
    $ocv = (& opencode --version 2>$null | Select-Object -First 1)
    Say "opencode already installed (version $ocv; we tested 1.19.0). Your own opencode settings are not touched: the kit starts opencode with its own config file."
}

# 3. Hardware check and model profile
#    big    : >= 22 GB GPU memory (e.g. RTX 3090/4090/5090, Strix Halo with 64+ GB) -> Qwen3.8-27B dense, all on GPU
#    medium : 8-22 GB GPU memory and >= 32 GB RAM (e.g. RTX 3080 Ti 12 GB)         -> Qwen3.6-35B-A3B MoE, experts in RAM
#    otherwise: stop with a clear message
function Get-Hardware {
    $ramGB = [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB)
    $gpus = @()
    if (Have "nvidia-smi") {
        foreach ($line in (& nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits)) {
            $p = $line.Split(","); $gpus += [pscustomobject]@{ Name = $p[0].Trim(); VramGB = [math]::Round([double]$p[1] / 1024); Vendor = "nvidia" }
        }
    }
    $class = "HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
    foreach ($k in (Get-ChildItem $class -ErrorAction SilentlyContinue | Where-Object { $_.PSChildName -match "^\d{4}$" })) {
        $prop = Get-ItemProperty $k.PSPath -ErrorAction SilentlyContinue
        $name = $prop.DriverDesc
        if (-not $name -or $name -match "(?i)nvidia|microsoft|basic") { continue }
        $bytes = $prop."HardwareInformation.qwMemorySize"
        $vendor = if ($name -match "(?i)amd|radeon") { "amd" } elseif ($name -match "(?i)intel|arc") { "intel" } else { "other" }
        $vram = if ($bytes) { [math]::Round([double]$bytes / 1GB) } else { 0 }
        # Strix Halo / AMD APUs share system memory with the GPU (Vulkan can use it).
        if ($vendor -eq "amd" -and $name -match "(?i)8060S|8050S|890M|880M" -and $ramGB -ge 64) { $vram = [math]::Max($vram, [math]::Floor($ramGB * 0.6)) }
        $gpus += [pscustomobject]@{ Name = $name; VramGB = $vram; Vendor = $vendor }
    }
    $best = $gpus | Sort-Object VramGB -Descending | Select-Object -First 1
    return [pscustomobject]@{ RamGB = $ramGB; Gpu = $best }
}
$External = [bool]$ExternalUrl
if ($External) {
    if (-not $ExternalModel) { throw "-ExternalUrl needs -ExternalModel (the model name as your server lists it)." }
    Say "Using your own model server $ExternalUrl with model '$ExternalModel' (no llama.cpp, no model download). Needs vision and tool calling, context 32768 or more."
    if (-not $DryRun) {
        New-Item -ItemType Directory -Force -Path $Models | Out-Null
        $cfg = [ordered]@{ profile = "external"; baseUrl = $ExternalUrl.TrimEnd("/"); apiModel = $ExternalModel; ctx = $(if ($Ctx -gt 0) { $Ctx } else { 32768 }); reasoning = $false }
        $json = $cfg | ConvertTo-Json
        [IO.File]::WriteAllText((Join-Path $Models "profile.json"), $json, (New-Object Text.UTF8Encoding $false))
        [IO.File]::WriteAllText((Join-Path $Models "profile-external.json"), $json, (New-Object Text.UTF8Encoding $false))
    }
} else {
$hw = Get-Hardware
if (-not $hw.Gpu) { throw "No supported graphics card found (NVIDIA, AMD or Intel with at least 8 GB)." }
Say ("Hardware: {0} with about {1} GB GPU memory, {2} GB RAM" -f $hw.Gpu.Name, $hw.Gpu.VramGB, $hw.RamGB)
if (-not $ModelProfile) {
    if ($ModelRepo -and $ModelFile) { $ModelProfile = "custom" }
    elseif ($hw.Gpu.VramGB -ge 22) { $ModelProfile = "big" }
    elseif ($hw.Gpu.VramGB -ge 8 -and $hw.RamGB -ge 32) { $ModelProfile = "medium" }
    elseif ($hw.Gpu.VramGB -ge 8 -and $hw.RamGB -ge 16) { $ModelProfile = "small" }
    elseif ($hw.Gpu.VramGB -ge 4 -and $hw.RamGB -ge 16) { $ModelProfile = "mini" }
    else { throw "This PC is too small for the kit: needs at least 4 GB GPU memory and 16 GB RAM (see README, 'Smaller PCs')." }
}
$Profiles = @{
    big    = @{ Repo = "unsloth/Qwen3.8-27B-GGUF";      File = "Qwen3.8-27B-UD-Q4_K_XL.gguf";      Ctx = 65536; Extra = @(); Reasoning = $true;
                Note = "Qwen3.8 27B, fully on the GPU (tested by us on the EVO-X2)" }
    medium = @{ Repo = "unsloth/Qwen3.6-35B-A3B-GGUF"; File = "Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf"; Ctx = 65536; Extra = @("--n-cpu-moe", "99"); Reasoning = $true;
                Note = "Qwen3.6 35B-A3B (MoE): attention on the GPU, experts in system RAM (tested by us on an RTX 3080 Ti, needs 32 GB RAM)" }
    small  = @{ Repo = "unsloth/Qwen3.5-9B-GGUF";      File = "Qwen3.5-9B-UD-Q4_K_XL.gguf";       Ctx = 32768; Extra = @(); Reasoning = $true;
                Note = "Qwen3.5 9B on the GPU, 8 GB or more (NOT tested by us; drawings will be less reliable)" }
    mini   = @{ Repo = "unsloth/Qwen3-VL-4B-Instruct-GGUF"; File = "Qwen3-VL-4B-Instruct-UD-Q4_K_XL.gguf"; Ctx = 32768; Extra = @(); Reasoning = $false;
                Note = "Qwen3-VL 4B on the GPU, 4 GB or more (NOT tested by us; for photos and simple parts only)" }
}
if ($ModelProfile -eq "custom") {
    if (-not ($ModelRepo -and $ModelFile)) { throw "Profile custom needs -ModelRepo and -ModelFile." }
    $Profiles["custom"] = @{ Repo = $ModelRepo; File = $ModelFile; Ctx = $(if ($Ctx -gt 0) { $Ctx } else { 32768 });
                             Extra = $(if ($CpuMoe -gt 0) { @("--n-cpu-moe", "$CpuMoe") } else { @() }); Reasoning = $true;
                             Note = "your own choice: $ModelRepo / $ModelFile (NOT tested by us)" }
}
if (-not $Profiles.ContainsKey($ModelProfile)) { throw "Unknown profile '$ModelProfile' (use big, medium, small, mini or custom)." }
$P = $Profiles[$ModelProfile]
Say "Model profile: $ModelProfile - $($P.Note)"

# 4. llama.cpp server: CUDA build for NVIDIA, Vulkan build for AMD/Intel
$LlamaDir = Join-Path $Programs "llama.cpp"
$backend = if ($hw.Gpu.Vendor -eq "nvidia") { "cuda-12.4" } else { "vulkan" }
if (-not (Test-Path (Join-Path $LlamaDir "llama-server.exe"))) {
    Say "Downloading llama.cpp $LlamaTag ($backend, Windows x64)"
    Do-Step "query GitHub release $LlamaTag and download the $backend build" {
        $rel = Invoke-RestMethod -Uri "https://api.github.com/repos/ggml-org/llama.cpp/releases/tags/$LlamaTag" -Headers @{ "User-Agent" = "local-ai-cad-kit" }
        $want = @($rel.assets | Where-Object { $_.name -like "llama-*-bin-win-$backend-x64.zip" })
        if ($backend -like "cuda*") { $want += @($rel.assets | Where-Object { $_.name -like "cudart-llama-bin-win-$backend-x64.zip" }) }
        if ($want.Count -lt 1 -or ($backend -like "cuda*" -and $want.Count -lt 2)) { throw "llama.cpp $LlamaTag has no complete $backend build." }
        New-Item -ItemType Directory -Force -Path $LlamaDir | Out-Null
        foreach ($asset in $want) {
            $zip = Join-Path $Programs $asset.name
            Download $asset.browser_download_url $zip
            Expand-Archive -Path $zip -DestinationPath $LlamaDir -Force
            Remove-Item $zip
        }
        $found = Get-ChildItem -Path $LlamaDir -Recurse -Filter "llama-server.exe" | Select-Object -First 1
        if (-not $found) { throw "llama-server.exe not found after unpacking." }
        if ($found.DirectoryName -ne $LlamaDir) { Get-ChildItem $found.DirectoryName | Move-Item -Destination $LlamaDir -Force }
    }
} else { Say "llama.cpp already present" }

# 5. Model + vision projector from Hugging Face
if (-not $SkipModel) {
    if (-not $DryRun) { New-Item -ItemType Directory -Force -Path $Models | Out-Null }
    Say "Looking up $($P.Repo) on Hugging Face"
    Do-Step "download $($P.File) and the F16 mmproj" {
        $tree = Invoke-RestMethod -Uri "https://huggingface.co/api/models/$($P.Repo)/tree/main?recursive=true"
        if (-not ($tree | Where-Object { $_.path -eq $P.File })) { throw "$($P.File) is not in $($P.Repo)." }
        $proj = $tree | Where-Object { $_.path -match "mmproj" -and $_.path -match "(?i)(^|[-_/])f16\.gguf$" } | Select-Object -First 1
        if (-not $proj) { throw "No F16 mmproj (vision projector) found in $($P.Repo)." }
        $projLocal = "mmproj-" + ($P.File -replace "\.gguf$", "") + "-F16.gguf"
        foreach ($pair in @(@($P.File, $P.File), @($proj.path, $projLocal))) {
            Say "Downloading $($pair[0]) (large file, can take a while; it resumes if interrupted)"
            Download "https://huggingface.co/$($P.Repo)/resolve/main/$($pair[0])" (Join-Path $Models $pair[1])
        }
        $cfg = [ordered]@{ profile = $ModelProfile; model = $P.File; projector = $projLocal; ctx = $P.Ctx; extra = $P.Extra; reasoning = $P.Reasoning;
                           gpu = $hw.Gpu.Name; gpu_gb = $hw.Gpu.VramGB; ram_gb = $hw.RamGB; backend = $backend }
        # profile.json = the model START-CAD uses. profile-<name>.json keeps every model you installed, so you can switch with START-CAD.bat -Profile <name>.
        $json = $cfg | ConvertTo-Json
        [IO.File]::WriteAllText((Join-Path $Models "profile.json"), $json, (New-Object Text.UTF8Encoding $false))
        [IO.File]::WriteAllText((Join-Path $Models "profile-$ModelProfile.json"), $json, (New-Object Text.UTF8Encoding $false))
    }
} else { Say "Model download skipped (-SkipModel)" }
}

# 6. FreeCAD-MCP addon into the FreeCAD user Mod folder
Say "Installing the FreeCAD-MCP addon v$FreecadMcpVersion"
Do-Step "copy addon/FreeCADMCP into the Mod folder of the installed FreeCAD version (unchanged if same version, backup outside Mod)" {
    $zip = Join-Path $Programs "freecad-mcp.zip"
    New-Item -ItemType Directory -Force -Path $Programs | Out-Null
    Download "https://github.com/neka-nat/freecad-mcp/archive/refs/tags/v$FreecadMcpVersion.zip" $zip
    $tmp = Join-Path $Programs "freecad-mcp-src"
    if (Test-Path $tmp) { Remove-Item -Recurse -Force $tmp }
    Expand-Archive -Path $zip -DestinationPath $tmp -Force
    $addon = Get-ChildItem -Path $tmp -Recurse -Directory -Filter "FreeCADMCP" | Where-Object { $_.Parent.Name -eq "addon" } | Select-Object -First 1
    if (-not $addon) { throw "Addon folder not found in the freecad-mcp download." }
    function Addon-Version($dir) {
        $x = Join-Path $dir "package.xml"
        if (-not (Test-Path $x)) { return $null }
        $m = [regex]::Match((Get-Content $x -Raw), "<version>\s*([^<\s]+)\s*</version>")
        if ($m.Success) { return $m.Groups[1].Value } else { return $null }
    }
    $newVersion = Addon-Version $addon.FullName
    # Only the addon folder of the installed FreeCAD version (1.1+ uses %APPDATA%\FreeCAD\v1-1\Mod, older %APPDATA%\FreeCAD\Mod).
    $fcDir = Get-ChildItem -Path "$env:LOCALAPPDATA\Programs", "$env:ProgramFiles" -Filter "FreeCAD 1.*" -Directory -ErrorAction SilentlyContinue |
             Sort-Object Name -Descending | Select-Object -First 1
    $modDirs = @("$env:APPDATA\FreeCAD\Mod")
    if ($fcDir -and $fcDir.Name -match "FreeCAD (\d+)\.(\d+)" -and ([int]$Matches[1] -gt 1 -or [int]$Matches[2] -ge 1)) {
        $modDirs = @("$env:APPDATA\FreeCAD\v$($Matches[1])-$($Matches[2])\Mod")
    }
    foreach ($mod in $modDirs) {
        $dest = Join-Path $mod "FreeCADMCP"
        if (Test-Path $dest) {
            $old = Addon-Version $dest
            if ($old -and $old -eq $newVersion) { Say "FreeCAD-MCP addon $old already installed in $mod - left unchanged"; continue }
            # Never touch an addon while FreeCAD runs, never delete it: back it up OUTSIDE the Mod folder
            # (a copy inside Mod would be loaded by FreeCAD as a second addon).
            if (Get-Process -Name "freecad" -ErrorAction SilentlyContinue) { throw "FreeCAD is running. Close FreeCAD and run START-HERE.bat again (nothing was changed)." }
            $backup = Join-Path $Programs ("addon-backup\" + ($mod -replace "[:\\]", "_") + "-" + (Get-Date -Format "yyyyMMdd-HHmmss"))
            New-Item -ItemType Directory -Force -Path $backup | Out-Null
            Move-Item -Path $dest -Destination $backup
            Say "Existing addon (version $old) moved to $backup"
        }
        New-Item -ItemType Directory -Force -Path $mod | Out-Null
        Copy-Item -Recurse -Path $addon.FullName -Destination $dest
    }
    Remove-Item -Recurse -Force $tmp, $zip
}

# 7. Python environments for the two MCP servers
Say "Preparing the photo-measure MCP server (uv)"
Do-Step "uv sync in foto-mcp" { & uv sync --project (Join-Path $Kit "foto-mcp"); if ($LASTEXITCODE -ne 0) { throw "uv sync failed." } }
Say "Preparing the FreeCAD MCP server (uvx freecad-mcp==$FreecadMcpVersion)"
Do-Step "uvx --from freecad-mcp==$FreecadMcpVersion freecad-mcp --help" {
    & uv tool install --python 3.12 "freecad-mcp==$FreecadMcpVersion" --force
    if ($LASTEXITCODE -ne 0) { throw "Could not install freecad-mcp." }
}

# 8. Self-test of the photo measurement (synthetic photo, no camera needed)
Say "Self-test: synthetic markerboard photo"
Do-Step "uv run synthetischer_test.py" {
    Push-Location (Join-Path $Kit "tests")
    & uv run --project (Join-Path $Kit "foto-mcp") python synthetischer_test.py
    $rc = $LASTEXITCODE
    Pop-Location
    if ($rc -ne 0) { throw "Self-test failed." }
}

Say "Done. Start with START-CAD.bat"
