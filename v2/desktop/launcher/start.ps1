# Financial Planner - start (called by "Start Financial Planner.bat" and "Open in Browser.bat").
#   (default)  set up if needed, then open the Financial Planner desktop window
#   -Browser   set up if needed, run the planner in the background and open it in your browser
# First run: finds or installs Python, sets up a private environment (.venv), adds shortcuts.
# Works in Windows PowerShell 5.1 and PowerShell 7.
param([switch]$Browser)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$App = Join-Path $Root 'app'
$Data = Join-Path $Root 'data'
$Venv = Join-Path $Root '.venv'
$Logs = Join-Path $Root 'logs'
$Wheels = Join-Path $PSScriptRoot 'wheels'
$Desktop = Join-Path $PSScriptRoot 'desktop.py'
$Port = 8502
if ($env:FP_PORT) { $Port = [int]$env:FP_PORT }
$Url = "http://localhost:$Port"
$OnWindows = ($env:OS -eq 'Windows_NT')

function Say([string]$m) { Write-Host "  $m" }
function Fail([string]$m) { Write-Host ""; Write-Host "  $m" -ForegroundColor Red; Write-Host ""; exit 1 }
function Test-Up {
    # plain TCP connect to 127.0.0.1: avoids system proxies and the slow IPv6 "localhost" lookup
    $c = New-Object Net.Sockets.TcpClient
    try {
        $iar = $c.BeginConnect('127.0.0.1', $Port, $null, $null)
        if (-not $iar.AsyncWaitHandle.WaitOne(1500)) { return $false }
        $c.EndConnect($iar)
        return $c.Connected
    } catch { return $false } finally { $c.Close() }
}
function Test-WebView2 {
    if (-not $OnWindows) { return $true }
    $id = '{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}'
    foreach ($k in @("HKLM:\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\$id", "HKLM:\SOFTWARE\Microsoft\EdgeUpdate\Clients\$id",
                     "HKCU:\Software\Microsoft\EdgeUpdate\Clients\$id")) {
        try { $pv = (Get-ItemProperty -Path $k -Name pv -ErrorAction Stop).pv; if ($pv -and $pv -ne '0.0.0.0') { return $true } } catch { }
    }
    return $false
}

Write-Host ""
Write-Host "  Financial Planner" -ForegroundColor Cyan
Write-Host ""

# files from a downloaded zip carry a "from the internet" mark; clear it so Windows stops asking
if ($OnWindows -and -not (Test-Path $Venv)) { try { Get-ChildItem $Root -Recurse -File -ErrorAction SilentlyContinue | Unblock-File -ErrorAction SilentlyContinue } catch { } }

# ---- 1. Python 3.10 or newer ------------------------------------------------------------
function Find-Python {
    $cands = @(@('py', '-3'), @('python'), @('python3'))
    if ($env:LOCALAPPDATA) {
        foreach ($v in @('313', '312', '311', '310')) {
            $cands += , @("$env:LOCALAPPDATA\Programs\Python\Python$v\python.exe")
        }
    }
    foreach ($c in $cands) {
        $exe = $c[0]
        $rest = @()
        if ($c.Count -gt 1) { $rest = @($c[1..($c.Count - 1)]) }
        if (-not (Get-Command $exe -ErrorAction SilentlyContinue)) { continue }
        try {
            $v = & $exe @rest -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>$null
            if ($LASTEXITCODE -eq 0 -and "$v" -match '^3\.(\d+)$' -and [int]$Matches[1] -ge 10) {
                return @{ Exe = $exe; Args = $rest; Version = "$v" }
            }
        } catch { }
    }
    return $null
}

$VPy = if ($OnWindows) { Join-Path $Venv 'Scripts\python.exe' } else { Join-Path $Venv 'bin/python' }
$VPyw = if ($OnWindows) { Join-Path $Venv 'Scripts\pythonw.exe' } else { $VPy }

if (-not (Test-Path $VPy)) {
    $py = Find-Python
    if (-not $py -and $OnWindows -and (Get-Command winget -ErrorAction SilentlyContinue)) {
        Say "Installing Python 3.12 (one time only, takes a few minutes)..."
        winget install -e --id Python.Python.3.12 --scope user --silent --accept-package-agreements --accept-source-agreements | Out-Null
        $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')
        $py = Find-Python
    }
    if (-not $py) {
        if ($OnWindows) { Start-Process 'https://www.python.org/downloads/windows/' }
        Fail "Python 3.10 or newer is needed. Install it from python.org (tick 'Add python.exe to PATH'), then double-click Start Financial Planner again."
    }
    Say "First run: setting up (Python $($py.Version))..."
    & $py.Exe @($py.Args) -m venv $Venv
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $VPy)) { Fail "Could not create the Python environment in $Venv." }
}

# ---- 2. Packages (only when a requirements file changes) ---------------------------------
function Install-Req([string]$req, [string]$stampName, [string]$what) {
    if (-not (Test-Path $req)) { return $true }
    $stamp = Join-Path $Venv $stampName
    $hash = (Get-FileHash $req -Algorithm SHA256).Hash
    $old = if (Test-Path $stamp) { (Get-Content $stamp -Raw).Trim() } else { '' }
    if ($hash -eq $old) { return $true }
    Say "Installing $what (needs internet, about a minute)..."
    $pipArgs = @('-m', 'pip', 'install', '--disable-pip-version-check', '-q', '-r', $req)
    if (Test-Path $Wheels) { $pipArgs += @('--find-links', $Wheels) }
    & $VPy @pipArgs
    if ($LASTEXITCODE -ne 0) { return $false }
    Set-Content -Path $stamp -Value $hash -NoNewline
    return $true
}
if (-not (Install-Req (Join-Path $App 'requirements.txt') '.requirements.sha256' "the app's packages")) {
    Fail "Package install failed. Check your internet connection and try again."
}
$desktopReady = $false
if (-not $Browser) {
    if (-not (Test-WebView2)) {
        Say "The Edge WebView2 component isn't installed, so the planner opens in your browser instead."
        Say "(Get it from https://go.microsoft.com/fwlink/p/?LinkId=2124703 to use the desktop window.)"
    } elseif (Install-Req (Join-Path $PSScriptRoot 'requirements-desktop.txt') '.desktop-requirements.sha256' 'the desktop window') {
        $desktopReady = $true
    } else {
        Say "Couldn't install the desktop window, so the planner opens in your browser instead."
    }
}

# ---- 3. Your data -------------------------------------------------------------------------
New-Item -ItemType Directory -Force -Path (Join-Path $Data 'households') | Out-Null
New-Item -ItemType Directory -Force -Path $Logs | Out-Null
$haveData = @(Get-ChildItem (Join-Path $Data 'households') -Filter *.json -ErrorAction SilentlyContinue).Count -gt 0
if (-not $haveData -and $env:USERPROFILE) {
    # first run: bring over plans from the old app on this computer (a copy; the originals are not touched)
    foreach ($src in @("$env:USERPROFILE\financial-planner\data", "$env:USERPROFILE\financial-planner\app-data", "$env:USERPROFILE\financial-planner\v2\app-data-v2")) {
        $srcHh = Join-Path $src 'households'
        if ((Test-Path $srcHh) -and @(Get-ChildItem $srcHh -Filter *.json -ErrorAction SilentlyContinue).Count -gt 0) {
            Copy-Item -Path (Join-Path $src '*') -Destination $Data -Recurse -Force
            Say "Copied your existing plans from $src (the originals are untouched)."
            break
        }
    }
}

# ---- 4a. Desktop window ------------------------------------------------------------------
function Set-Shortcut([string]$lnk) {
    $ws = New-Object -ComObject WScript.Shell
    $s = $ws.CreateShortcut($lnk)
    $s.TargetPath = $VPyw
    $s.Arguments = "`"$Desktop`""
    $s.WorkingDirectory = $Root
    $s.IconLocation = (Join-Path $PSScriptRoot 'planner.ico') + ',0'
    $s.Description = 'Financial Planner'
    $s.Save()
}
if ($desktopReady) {
    if ($OnWindows) {
        # desktop + Start menu shortcuts open the window directly (no console); refreshed every time
        try {
            $dl = Join-Path ([Environment]::GetFolderPath('Desktop')) 'Financial Planner.lnk'
            $new = -not (Test-Path $dl)
            Set-Shortcut $dl
            Set-Shortcut (Join-Path ([Environment]::GetFolderPath('Programs')) 'Financial Planner.lnk')
            if ($new) { Say "Added 'Financial Planner' to your desktop and Start menu." }
        } catch { Say "(Could not update the shortcuts: $($_.Exception.Message))" }
    }
    if ($env:FP_NO_LAUNCH) { Say "Set up (FP_NO_LAUNCH: not opening the window)."; exit 0 }
    Say "Opening the Financial Planner window..."
    Start-Process -FilePath $VPyw -ArgumentList @("`"$Desktop`"") -WorkingDirectory $Root
    exit 0
}

# ---- 4b. Browser: run the planner in the background ---------------------------------------
if (Test-Up) { Say "Already running - opening it in your browser."; if ($OnWindows) { Start-Process $Url }; exit 0 }
$env:DATA_DIR = $Data
$env:FP_PORT = "$Port"
$runner = Join-Path $PSScriptRoot 'run_server.py'
Say "Starting..."
if ($OnWindows) {
    $proc = Start-Process -FilePath $VPyw -ArgumentList @("`"$runner`"") -WorkingDirectory $App -WindowStyle Hidden -PassThru
} else {
    $proc = Start-Process -FilePath $VPy -ArgumentList @($runner) -WorkingDirectory $App -PassThru
}
# run_server.py writes the real server PID to .server.pid (the venv's pythonw is only a launcher)
$deadline = (Get-Date).AddSeconds(90)
while (-not (Test-Up)) {
    if ($proc.HasExited -or (Get-Date) -gt $deadline) {
        $tail = ''
        $logFile = Join-Path $Logs 'server.log'
        if (Test-Path $logFile) { $tail = (Get-Content $logFile -Tail 15) -join "`n" }
        Write-Host $tail
        Fail "The app didn't start. The lines above (from logs\server.log) say why. Is something else using port $Port?"
    }
    Start-Sleep -Milliseconds 500
}
Say "Ready: $Url  (it keeps running in the background; 'Stop Financial Planner' stops it)"
if ($OnWindows) { Start-Process $Url } else { Say "Open $Url in your browser." }
exit 0
