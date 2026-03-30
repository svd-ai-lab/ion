# run_helpers.ps1 — shared functions for all execution test scripts.
# Dot-source this file: . "$PSScriptRoot\run_helpers.ps1"

$ION       = "E:\Code_MCP\ion\.venv\Scripts\ion.exe"
$SNIPPETS  = "E:\Code_MCP\ion\ion-main\tests\execution\snippets"
$ION_MAIN  = "E:\Code_MCP\ion\ion-main"

function New-LogDir {
    param([string]$CaseId)
    $ts      = Get-Date -Format "yyyyMMdd_HHmmss"
    $logDir  = "$ION_MAIN\tests\execution\logs\${CaseId}_${ts}"
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
    return $logDir
}

function Write-Log {
    param([string]$LogFile, [string]$Message)
    $ts = Get-Date -Format "HH:mm:ss"
    $line = "$ts  $Message"
    Write-Host $line
    Add-Content -Path $LogFile -Value $line
}

function Invoke-IonStep {
    param(
        [string]$CaseId,
        [string]$Label,
        [string]$SnippetFile,
        [string]$LogDir,
        [string]$LogFile
    )

    Write-Log $LogFile ""
    Write-Log $LogFile "=== STEP: $Label ==="
    Write-Log $LogFile "    snippet: $SnippetFile"

    # Run the snippet
    $runOut = & $ION run --code-file $SnippetFile --label $Label 2>&1
    $runOut | Out-File -FilePath "$LogDir\${Label}_run.txt" -Encoding utf8
    foreach ($line in $runOut) { Write-Log $LogFile "  run> $line" }

    $runExit = $LASTEXITCODE
    Write-Log $LogFile "    ion run exit code: $runExit"

    # Query last.result
    $queryOut = & $ION query last.result 2>&1
    $queryOut | Out-File -FilePath "$LogDir\${Label}_result.json" -Encoding utf8
    Write-Log $LogFile "    last.result saved to ${Label}_result.json"

    # Parse ok field
    try {
        $parsed = $queryOut | ConvertFrom-Json -ErrorAction Stop
        $ok = $parsed.ok
    } catch {
        $ok = $false
        Write-Log $LogFile "    WARNING: could not parse last.result as JSON"
    }

    # Exit 1 = server-level error (protocol/serialization), Exit 2 = snippet exception
    if ($runExit -eq 1) {
        Write-Log $LogFile "WARNING: ion run exit 1 (server error, e.g. serialization). Checking last.result..."
        if ($ok -eq $false) {
            Write-Log $LogFile "ERROR: step '$Label' — server error AND ok=false. Stopping."
            & $ION disconnect 2>&1 | Out-Null
            exit 1
        } else {
            Write-Log $LogFile "  Step '$Label' appears OK despite server warning (ok=true). Continuing."
        }
    } elseif ($runExit -eq 2 -or $ok -eq $false) {
        Write-Log $LogFile "ERROR: step '$Label' failed (ok=false or exit 2). Stopping test."
        Write-Log $LogFile "       See $LogDir\${Label}_result.json for details."
        # Disconnect cleanly before exit
        Write-Log $LogFile "  Disconnecting..."
        & $ION disconnect 2>&1 | Out-Null
        exit 1
    }

    Write-Log $LogFile "    Step '$Label' OK"
    return $parsed
}

function Invoke-IonConnect {
    param(
        [string]$Mode,
        [string]$UiMode = "gui",
        [int]$Processors = 2,
        [string]$LogFile
    )
    Write-Log $LogFile "=== CONNECT: mode=$Mode ui_mode=$UiMode processors=$Processors ==="
    $connectOut = & $ION connect --mode $Mode --ui-mode $UiMode --processors $Processors 2>&1
    $connectOut | ForEach-Object { Write-Log $LogFile "  connect> $_" }
    if ($LASTEXITCODE -ne 0) {
        Write-Log $LogFile "ERROR: ion connect failed (exit $LASTEXITCODE). Aborting."
        exit 1
    }
    Write-Log $LogFile "  Connect OK"
}

function Invoke-IonQuery {
    param([string]$Name, [string]$LogDir, [string]$Label, [string]$LogFile)
    $out = & $ION query $Name 2>&1
    $out | Out-File -FilePath "$LogDir\query_${Label}.json" -Encoding utf8
    Write-Log $LogFile "  query $Name -> saved to query_${Label}.json"
    try { return $out | ConvertFrom-Json -ErrorAction Stop } catch { return $null }
}

function Invoke-IonDisconnect {
    param([string]$LogFile)
    Write-Log $LogFile ""
    Write-Log $LogFile "=== DISCONNECT ==="
    $out = & $ION disconnect 2>&1
    $out | ForEach-Object { Write-Log $LogFile "  disconnect> $_" }
    Write-Log $LogFile "  Disconnect exit code: $LASTEXITCODE"
}
