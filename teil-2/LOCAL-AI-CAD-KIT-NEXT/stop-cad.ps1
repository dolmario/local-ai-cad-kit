# Stops only the processes that start-cad.ps1 started (PIDs in running.txt), after checking the process name. Nothing else is touched.
$Kit = $PSScriptRoot
$f = Join-Path $Kit "running.txt"
if (-not (Test-Path $f)) { Write-Host "Nothing to stop: running.txt not found (START-CAD is not running, or it was already closed)."; exit 0 }
$stopped = 0
foreach ($line in (Get-Content $f)) {
    if ($line -match '^(llama-server|FreeCAD) PID (\d+)') {
        $want = $Matches[1]; $id = [int]$Matches[2]
        $p = Get-Process -Id $id -ErrorAction SilentlyContinue
        if ($p -and $p.ProcessName -like "$want*") { Stop-Process -Id $id; Write-Host "Closed $want (PID $id)."; $stopped++ }
        elseif ($p) { Write-Host "PID $id is now '$($p.ProcessName)', not $want - left alone." }
        else { Write-Host "$want (PID $id) was already closed." }
    }
}
Remove-Item $f -ErrorAction SilentlyContinue
Write-Host "Done. $stopped program(s) closed. Close the opencode window yourself (Ctrl+C or /exit)."
