# Financial Planner - stop the background server (called by "Stop Financial Planner.bat").
$Root = Split-Path -Parent $PSScriptRoot
$PidFile = Join-Path $Root '.server.pid'
$Port = 8502
if ($env:FP_PORT) { $Port = [int]$env:FP_PORT }
$stopped = $false

if (Test-Path $PidFile) {
    $id = [int]((Get-Content $PidFile -Raw).Trim())
    $p = Get-Process -Id $id -ErrorAction SilentlyContinue
    if ($p -and $p.ProcessName -like 'python*') { Stop-Process -Id $id -Force; $stopped = $true }
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
}
# also stop whatever python is still listening on the port (older launchers saved the wrong PID)
if (Get-Command Get-NetTCPConnection -ErrorAction SilentlyContinue) {
    foreach ($c in @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)) {
        $p = Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue
        if ($p -and $p.ProcessName -like 'python*') { Stop-Process -Id $p.Id -Force; $stopped = $true }
    }
}
if ($stopped) { Write-Host "  Financial Planner stopped." } else { Write-Host "  Financial Planner wasn't running." }
