function Get-CadOwnedProcess($Record) {
    $cadProcess=Get-Process -Id $Record.pid -ErrorAction SilentlyContinue
    if (-not $cadProcess) { return $null }
    if ($cadProcess.StartTime.ToUniversalTime().Ticks -ne [long]$Record.start_ticks -or $cadProcess.Path -ne $Record.exe) { return $null }
    return $cadProcess
}

function Stop-CadOwnedServer($Record) {
    $cadParent=Get-CadOwnedProcess $Record
    if (-not $cadParent) { return }
    $cadDescendants=New-Object 'System.Collections.Generic.List[object]'
    $cadVisited=@{}
    function Find-CadDescendants([int]$CadParentId,[long]$CadParentTicks) {
        foreach ($cadChildInfo in @(Get-CimInstance Win32_Process -Filter "ParentProcessId=$CadParentId" -ErrorAction SilentlyContinue)) {
            $cadChild=Get-Process -Id $cadChildInfo.ProcessId -ErrorAction SilentlyContinue
            if (-not $cadChild) { continue }
            $cadTicks=$cadChild.StartTime.ToUniversalTime().Ticks
            if ($cadTicks -lt $CadParentTicks -or $cadVisited.ContainsKey($cadChild.Id)) { continue }
            $cadVisited[$cadChild.Id]=$true
            $cadChildRecord=[pscustomobject]@{pid=$cadChild.Id;start_ticks=$cadTicks;exe=$cadChild.Path}
            $cadDescendants.Add($cadChildRecord)
            Find-CadDescendants $cadChild.Id $cadTicks
        }
    }
    Find-CadDescendants $cadParent.Id $cadParent.StartTime.ToUniversalTime().Ticks
    $cadParent=Get-CadOwnedProcess $Record
    if ($cadParent) { Stop-Process -Id $cadParent.Id -ErrorAction SilentlyContinue }
    for ($cadIndex=$cadDescendants.Count-1;$cadIndex -ge 0;$cadIndex--) {
        $cadChild=Get-CadOwnedProcess $cadDescendants[$cadIndex]
        if ($cadChild) { Stop-Process -Id $cadChild.Id -ErrorAction SilentlyContinue }
    }
}
