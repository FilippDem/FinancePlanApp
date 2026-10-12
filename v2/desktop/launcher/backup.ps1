# Financial Planner - copy the data folder to a zip somewhere off this computer (OneDrive by default).
#
#   backup.ps1                  make a backup now (skipped if nothing changed since the newest one)
#   backup.ps1 -Force           make one even if nothing changed
#   backup.ps1 -Check [-Zip f]  restore test only: unzip the newest backup (or f) to a temp folder and check it
#   backup.ps1 -Register        add a daily Task Scheduler task for this user that runs this script (-At 12:30)
#   backup.ps1 -Unregister      remove that task
#
# Where the zips go, first match wins: -Target, "backup_dir" in settings.json, %OneDrive%\FinancialPlanner-backups.
# Only data\ is read; nothing in it is changed (data\.session_secret is left out of the zip). The newest -Keep zips are kept (default 30); older
# FinancialPlanner-data-*.zip files in the target folder are removed. Everything is logged to logs\backup.log.
param(
    [string]$Target = '',
    [int]$Keep = 30,
    [switch]$Force,
    [switch]$Check,
    [string]$Zip = '',
    [switch]$Register,
    [switch]$Unregister,
    [string]$At = '12:30',
    [string]$Root = ''
)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression, System.IO.Compression.FileSystem, System.Web.Extensions

if (-not $Root) { $Root = Split-Path -Parent $PSScriptRoot }
$Root = (Resolve-Path $Root).Path
$Data = Join-Path $Root 'data'
$LogDir = Join-Path $Root 'logs'
$LogFile = Join-Path $LogDir 'backup.log'
$TaskName = 'Financial Planner backup'
$Prefix = 'FinancialPlanner-data-'
$CheckSummary = ''

function Log([string]$msg) {
    $line = '{0}  {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $msg
    Write-Host "  $msg"
    try {
        if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }
        Add-Content -Path $LogFile -Value $line -Encoding UTF8
    } catch { }
}

function Get-TargetDir {
    if ($Target) { return $Target }
    $settings = Join-Path $Root 'settings.json'
    if (Test-Path $settings) {
        try {
            $s = Get-Content $settings -Raw -Encoding UTF8 | ConvertFrom-Json
            if ($s.backup_dir) { return [Environment]::ExpandEnvironmentVariables([string]$s.backup_dir) }
        } catch { Log "settings.json unreadable ($($_.Exception.Message)); ignoring it" }
    }
    if ($env:OneDrive -and (Test-Path $env:OneDrive)) { return (Join-Path $env:OneDrive 'FinancialPlanner-backups') }
    return ''
}

# Fingerprint of a folder: relative path + SHA-256 of every file. Same data -> same fingerprint.
function Get-Fingerprint([string]$dir) {
    $base = (Resolve-Path $dir).Path.TrimEnd('\') + '\'
    $lines = Get-ChildItem -Path $dir -Recurse -File | Sort-Object FullName | ForEach-Object {
        $_.FullName.Substring($base.Length).Replace('\', '/') + ' ' + (Get-FileHash -Path $_.FullName -Algorithm SHA256).Hash
    }
    $bytes = [Text.Encoding]::UTF8.GetBytes(($lines -join "`n"))
    $sha = [Security.Cryptography.SHA256]::Create()
    return (-join ($sha.ComputeHash($bytes) | ForEach-Object { $_.ToString('x2') }))
}

# ConvertFrom-Json in PowerShell 5.1 caps the input size; JavaScriptSerializer with a raised limit does not.
function Read-Json([string]$path) {
    $js = New-Object System.Web.Script.Serialization.JavaScriptSerializer
    $js.MaxJsonLength = [int]::MaxValue
    $js.RecursionLimit = 1000
    return $js.DeserializeObject([IO.File]::ReadAllText($path, [Text.Encoding]::UTF8))
}

# Restore test: unzip to a fresh temp folder; households_index.json and every households\*.json must parse,
# and every household in the index must have its file. With $expected, the unzipped files must also match
# that folder byte for byte. Returns a list of problems (empty = good).
function Test-Backup([string]$zipPath, [string]$expected = '') {
    $problems = New-Object System.Collections.Generic.List[string]
    $tmp = Join-Path ([IO.Path]::GetTempPath()) ('fp-restore-test-' + [guid]::NewGuid().ToString('N'))
    try {
        [IO.Compression.ZipFile]::ExtractToDirectory($zipPath, $tmp)
        $d = Join-Path $tmp 'data'
        $index = Join-Path $d 'households_index.json'
        $ids = @()
        if (-not (Test-Path $index)) { $problems.Add('households_index.json missing') }
        else {
            try {
                $ix = Read-Json $index
                if ($ix -isnot [Collections.IDictionary]) { $problems.Add('households_index.json is not a JSON object') }
                else { $ids = @($ix.Keys) }
            } catch { $problems.Add("households_index.json does not parse: $($_.Exception.Message)") }
        }
        $hdir = Join-Path $d 'households'
        $files = @()
        if (Test-Path $hdir) { $files = @(Get-ChildItem -Path $hdir -Filter '*.json' -File) }
        foreach ($f in $files) {
            try {
                if ((Read-Json $f.FullName) -isnot [Collections.IDictionary]) { $problems.Add("households\$($f.Name) is not a JSON object") }
            } catch { $problems.Add("households\$($f.Name) does not parse: $($_.Exception.Message)") }
        }
        foreach ($id in $ids) {
            if (-not (Test-Path (Join-Path $hdir "$id.json"))) { $problems.Add("household $id is in the index but households\$id.json is missing") }
        }
        if ($expected) {
            $base = (Resolve-Path $expected).Path.TrimEnd('\') + '\'
            foreach ($src in @(Get-ChildItem -Path $expected -Recurse -File)) {
                $rel = $src.FullName.Substring($base.Length)
                $got = Join-Path $d $rel
                if (-not (Test-Path $got)) { $problems.Add("$rel missing from the zip") }
                elseif ((Get-FileHash $got -Algorithm SHA256).Hash -ne (Get-FileHash $src.FullName -Algorithm SHA256).Hash) {
                    $problems.Add("$rel differs from the original")
                }
            }
        }
        $script:CheckSummary = "index lists $($ids.Count) household(s), $($files.Count) household file(s) parsed"
    } catch {
        $problems.Add("could not unzip: $($_.Exception.Message)")
    } finally {
        if (Test-Path $tmp) { Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue }
    }
    return ,$problems
}

function Get-Backups([string]$dir) {
    if (-not $dir -or -not (Test-Path $dir)) { return @() }
    return @(Get-ChildItem -Path $dir -Filter "$Prefix*.zip" -File | Sort-Object Name -Descending)
}

# --- scheduled task ---------------------------------------------------------------------------
if ($Register -or $Unregister) {
    $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($Unregister) {
        if ($existing) { Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false; Log "removed the daily task '$TaskName'" }
        else { Log "no task named '$TaskName'" }
        exit 0
    }
    $script = Join-Path $PSScriptRoot 'backup.ps1'
    $taskArgs = "-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$script`""
    $action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $taskArgs -WorkingDirectory $Root
    $trigger = New-ScheduledTaskTrigger -Daily -At $At
    # StartWhenAvailable: if the laptop was off or asleep at that time, run at the next chance.
    $set = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
        -ExecutionTimeLimit (New-TimeSpan -Minutes 15) -MultipleInstances IgnoreNew
    $who = [Security.Principal.WindowsIdentity]::GetCurrent().Name
    $principal = New-ScheduledTaskPrincipal -UserId $who -LogonType Interactive -RunLevel Limited
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $set -Principal $principal `
        -Description 'Zips the Financial Planner data folder to OneDrive (see logs\backup.log).' -Force | Out-Null
    Log "daily task '$TaskName' set for $At (runs as $who): $script"
    exit 0
}

$dest = Get-TargetDir

# --- restore test only ------------------------------------------------------------------------
if ($Check) {
    if (-not $Zip) {
        $newest = Get-Backups $dest | Select-Object -First 1
        if (-not $newest) { Log "CHECK FAIL: no backups found in '$dest'"; exit 1 }
        $Zip = $newest.FullName
    }
    $p = Test-Backup $Zip
    if ($p.Count) { Log "CHECK FAIL $Zip"; $p | ForEach-Object { Log "  - $_" }; exit 1 }
    Log "CHECK OK $Zip ($CheckSummary)"
    exit 0
}

# --- backup -----------------------------------------------------------------------------------
if (-not (Test-Path (Join-Path $Data 'households_index.json'))) { Log "FAIL: no plans found in $Data"; exit 1 }
if (-not $dest) {
    Log 'FAIL: no backup folder. OneDrive is not set up on this PC; add "backup_dir": "D:\\somewhere" to settings.json or pass -Target.'
    exit 1
}

$work = Join-Path ([IO.Path]::GetTempPath()) ('fp-backup-' + [guid]::NewGuid().ToString('N'))
try {
    # Copy first, then zip the copy: the planner may save while we work, and a zip must not mix two versions.
    $stage = Join-Path $work 'data'
    New-Item -ItemType Directory -Path $work | Out-Null
    Copy-Item -LiteralPath $Data -Destination $stage -Recurse
    # The sign-in signing key stays on this PC; the server makes a new one if it's missing (you just sign in again).
    Remove-Item -LiteralPath (Join-Path $stage '.session_secret') -Force -ErrorAction SilentlyContinue
    $short = (Get-Fingerprint $stage).Substring(0, 8)

    if (-not (Test-Path $dest)) { New-Item -ItemType Directory -Path $dest -Force | Out-Null }
    $newest = Get-Backups $dest | Select-Object -First 1
    if (-not $Force -and $newest -and $newest.BaseName.EndsWith("-$short")) {
        Log "unchanged since $($newest.Name); no new backup"
    } else {
        $name = '{0}{1}-{2}.zip' -f $Prefix, (Get-Date -Format 'yyyyMMdd-HHmmss'), $short
        $tmpZip = Join-Path $work $name
        # Entry by entry: ZipFile.CreateFromDirectory on PowerShell 5.1 writes "data\x" names, which unzip badly off Windows.
        $base = $stage.TrimEnd('\') + '\'
        $archive = [IO.Compression.ZipFile]::Open($tmpZip, [IO.Compression.ZipArchiveMode]::Create)
        try {
            foreach ($f in @(Get-ChildItem -Path $stage -Recurse -File)) {
                $entry = 'data/' + $f.FullName.Substring($base.Length).Replace('\', '/')
                [IO.Compression.ZipFileExtensions]::CreateEntryFromFile($archive, $f.FullName, $entry, [IO.Compression.CompressionLevel]::Optimal) | Out-Null
            }
        } finally { $archive.Dispose() }
        $p = Test-Backup $tmpZip $stage
        if ($p.Count) {
            Log 'FAIL: the new backup did not pass the restore test, so it was not saved:'
            $p | ForEach-Object { Log "  - $_" }
            exit 1
        }
        $final = Join-Path $dest $name
        Move-Item -LiteralPath $tmpZip -Destination $final
        $kb = [math]::Ceiling((Get-Item $final).Length / 1KB)
        Log "saved $name ($kb KB) to $dest; restore test OK ($CheckSummary)"
    }

    $all = Get-Backups $dest
    if ($Keep -gt 0 -and $all.Count -gt $Keep) {
        foreach ($old in $all[$Keep..($all.Count - 1)]) {
            Remove-Item -LiteralPath $old.FullName -Force
            Log "removed old backup $($old.Name)"
        }
    }
    exit 0
} catch {
    Log "FAIL: $($_.Exception.Message)"
    exit 1
} finally {
    if (Test-Path $work) { Remove-Item -LiteralPath $work -Recurse -Force -ErrorAction SilentlyContinue }
}
