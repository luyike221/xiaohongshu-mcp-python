# MCP Inspector helper (Windows PowerShell)
# Connect MCP Inspector to this project's HTTP MCP endpoint.
# Usage: .\inspector_test_mcp.ps1 [options]

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$DEFAULT_HOST = "127.0.0.1" # match uvicorn bind; "localhost" may resolve to ::1 on Windows
$DEFAULT_PORT = "8003"
$DEFAULT_ENDPOINT = "/mcp"

$script:BgServerProcess = $null

function Show-Help {
    Write-Host "MCP Inspector helper" -ForegroundColor Green
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Cyan
    Write-Host "    .\inspector_test_mcp.ps1 [options]"
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Cyan
    Write-Host ("    --host HOST          MCP host (default: " + $DEFAULT_HOST + ")")
    Write-Host "    --port PORT          MCP port (default: $DEFAULT_PORT)"
    Write-Host "    --endpoint PATH      MCP path (default: $DEFAULT_ENDPOINT)"
    Write-Host "    --auto-start         Start MCP server in background if down"
    Write-Host "    --no-auto-start      Only check + launch Inspector (default)"
    Write-Host "    --skip-confirm       Skip Enter prompt before Inspector"
    Write-Host "    --help, -h           Show this help"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Cyan
    Write-Host "    .\inspector_test_mcp.ps1"
    Write-Host "    .\inspector_test_mcp.ps1 --port 9000"
    Write-Host "    .\inspector_test_mcp.ps1 --auto-start --skip-confirm"
    Write-Host ""
}

function Get-UvExecutable {
    $cmd = Get-Command uv -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source) { return $cmd.Source }
    $local = Join-Path $env:USERPROFILE ".local\bin\uv.exe"
    if (Test-Path -LiteralPath $local) { return $local }
    return $null
}

function Add-NodeDirToPath {
    # Prepend common Node install dirs when Cursor terminal has stale PATH
    $pf86 = [Environment]::GetEnvironmentVariable("ProgramFiles(x86)")
    $dirs = @(
        (Join-Path $env:ProgramFiles "nodejs")
    )
    if (-not [string]::IsNullOrWhiteSpace($pf86)) {
        $dirs += (Join-Path $pf86 "nodejs")
    }
    $dirs += @(
        (Join-Path $env:LOCALAPPDATA "Programs\nodejs")
        (Join-Path $env:USERPROFILE "scoop\apps\nodejs\current")
        (Join-Path $env:USERPROFILE ".volta\bin")
    )
    foreach ($d in $dirs) {
        if ([string]::IsNullOrWhiteSpace($d)) { continue }
        $nodeExe = Join-Path $d "node.exe"
        if (Test-Path -LiteralPath $nodeExe) {
            if ($env:Path -notlike "*$d*") {
                $env:Path = "$d;$env:Path"
            }
            return $true
        }
    }
    return $false
}

function Test-NodeTools {
    if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
        [void](Add-NodeDirToPath)
    }
    if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
        Write-Host "ERROR: Node.js not found in PATH." -ForegroundColor Red
        Write-Host "  Install LTS from https://nodejs.org/ and tick ""Add to PATH"", then restart this terminal." -ForegroundColor Yellow
        Write-Host "  Or ensure ""node.exe"" exists under Program Files\nodejs." -ForegroundColor Yellow
        exit 1
    }
    if (-not (Get-Command npx -ErrorAction SilentlyContinue)) {
        Write-Host "ERROR: npx not found next to node (reinstall Node.js from nodejs.org)." -ForegroundColor Red
        exit 1
    }
}

function Test-McpSingleUri {
    param([string]$UriToTry)
    try {
        $null = Invoke-WebRequest -Uri $UriToTry -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
        return $true
    } catch {
        $resp = $_.Exception.Response
        return ($null -ne $resp)
    }
}

function Test-McpServerReachable {
    param(
        [string]$ServerHost,
        [string]$ServerPort,
        [string]$Endpoint,
        [switch]$Quiet
    )
    $uri = "http://${ServerHost}:${ServerPort}${Endpoint}"
    if (-not $Quiet) {
        Write-Host "Checking: $uri" -ForegroundColor Cyan
    }
    if (Test-McpSingleUri -UriToTry $uri) {
        if (-not $Quiet) { Write-Host "Server is reachable." -ForegroundColor Green }
        return $true
    }
    # localhost -> ::1，服务若只监听 127.0.0.1 会失败，再试 IPv4
    if ($ServerHost -eq "localhost") {
        $uri4 = "http://127.0.0.1:${ServerPort}${Endpoint}"
        if (-not $Quiet) {
            Write-Host "Retrying IPv4: $uri4" -ForegroundColor DarkYellow
        }
        if (Test-McpSingleUri -UriToTry $uri4) {
            if (-not $Quiet) { Write-Host "Server is reachable." -ForegroundColor Green }
            return $true
        }
    }
    if (-not $Quiet) { Write-Host "Server is not running or not reachable." -ForegroundColor Yellow }
    return $false
}

function Start-McpServerBackground {
    param(
        [string]$ServerHost,
        [string]$ServerPort
    )
    $UvExe = Get-UvExecutable
    if (-not $UvExe -or -not (Test-Path -LiteralPath (Join-Path $ScriptDir "pyproject.toml"))) {
        Write-Host "ERROR: uv or pyproject.toml not found." -ForegroundColor Red
        return $null
    }

    $logOut = Join-Path $env:TEMP "xiaohongshu-mcp-server.out.log"
    $logErr = Join-Path $env:TEMP "xiaohongshu-mcp-server.err.log"

    Write-Host "Starting MCP server..." -ForegroundColor Cyan

    $savedServerHost = $env:SERVER_HOST
    $env:SERVER_HOST = $ServerHost
    try {
        $proc = Start-Process -FilePath $UvExe `
            -ArgumentList @(
                "run", "python", "-m", "xiaohongshu_mcp_python.main",
                "--env", "development",
                "--port", $ServerPort,
                "--headless"
            ) `
            -WorkingDirectory $ScriptDir `
            -WindowStyle Hidden `
            -PassThru `
            -RedirectStandardOutput $logOut `
            -RedirectStandardError $logErr
    } finally {
        if ($null -eq $savedServerHost -or $savedServerHost -eq "") {
            Remove-Item Env:\SERVER_HOST -ErrorAction SilentlyContinue
        } else {
            $env:SERVER_HOST = $savedServerHost
        }
    }

    Write-Host "Server PID: $($proc.Id)" -ForegroundColor Green
    Write-Host "Logs: $logOut | $logErr" -ForegroundColor Blue

    Write-Host "Waiting for server..." -ForegroundColor Cyan
    $maxAttempts = 30
    for ($attempt = 0; $attempt -lt $maxAttempts; $attempt++) {
        if (Test-McpServerReachable -ServerHost $ServerHost -ServerPort $ServerPort -Endpoint $script:MCP_ENDPOINT -Quiet) {
            Write-Host "Server is up." -ForegroundColor Green
            return $proc
        }
        Start-Sleep -Seconds 1
        Write-Host "." -NoNewline
    }
    Write-Host ""
    Write-Host "ERROR: server start timed out." -ForegroundColor Red
    Write-Host "See logs: $logOut | $logErr" -ForegroundColor Yellow
    if ($proc -and -not $proc.HasExited) {
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    }
    return $null
}

function Stop-McpServerBackground {
    if ($null -eq $script:BgServerProcess) { return }
    $procId = $script:BgServerProcess.Id
    if (-not $script:BgServerProcess.HasExited) {
        Write-Host ""
        Write-Host "Stopping background server (PID $procId)..." -ForegroundColor Yellow
        Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        Write-Host "Stopped." -ForegroundColor Green
    }
    $script:BgServerProcess = $null
}

# ---------- args ----------
$ServerHost = $DEFAULT_HOST
$ServerPort = $DEFAULT_PORT
$script:MCP_ENDPOINT = $DEFAULT_ENDPOINT
$AUTO_START = $false
$SKIP_CONFIRM = $false

$i = 0
$argv = $args
while ($i -lt $argv.Count) {
    $a = $argv[$i]
    switch -Regex ($a) {
        '^(help|--help|-h)$' {
            Show-Help
            exit 0
        }
        '^--host$' {
            if ($i + 1 -ge $argv.Count) {
                Write-Host "ERROR: --host needs a value." -ForegroundColor Red
                exit 1
            }
            $ServerHost = $argv[$i + 1]
            $i += 2
            continue
        }
        '^--port$' {
            if ($i + 1 -ge $argv.Count) {
                Write-Host "ERROR: --port needs a value." -ForegroundColor Red
                exit 1
            }
            $ServerPort = $argv[$i + 1]
            $i += 2
            continue
        }
        '^--endpoint$' {
            if ($i + 1 -ge $argv.Count) {
                Write-Host "ERROR: --endpoint needs a value." -ForegroundColor Red
                exit 1
            }
            $script:MCP_ENDPOINT = $argv[$i + 1]
            $i += 2
            continue
        }
        '^--auto-start$' {
            $AUTO_START = $true
            $i += 1
            continue
        }
        '^--no-auto-start$' {
            $AUTO_START = $false
            $i += 1
            continue
        }
        '^--skip-confirm$' {
            $SKIP_CONFIRM = $true
            $i += 1
            continue
        }
        default {
            Write-Host "ERROR: unknown argument: $a" -ForegroundColor Red
            Show-Help
            exit 1
        }
    }
}

Test-NodeTools

$MCP_URL = "http://${ServerHost}:${ServerPort}${script:MCP_ENDPOINT}"

Write-Host "========================================" -ForegroundColor Green
Write-Host " MCP Inspector" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Endpoint: $MCP_URL" -ForegroundColor Blue
Write-Host ""

if (-not (Test-McpServerReachable -ServerHost $ServerHost -ServerPort $ServerPort -Endpoint $script:MCP_ENDPOINT)) {
    if ($AUTO_START) {
        Write-Host ""
        $script:BgServerProcess = Start-McpServerBackground -ServerHost $ServerHost -ServerPort $ServerPort
        if ($null -eq $script:BgServerProcess) {
            exit 1
        }
    } else {
        Write-Host "Tip: use --auto-start to launch the server, or run:" -ForegroundColor Yellow
        Write-Host "  .\run.ps1 --no-debug --port $ServerPort" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host " Launching MCP Inspector" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Use HTTP/HTTPS transport in the browser UI (not STDIO)." -ForegroundColor Yellow
Write-Host "URL: $MCP_URL" -ForegroundColor Cyan
Write-Host ""

if (-not $SKIP_CONFIRM) {
    $null = Read-Host "Press Enter to start MCP Inspector (Ctrl+C to cancel)"
    Write-Host ""
}

Write-Host 'Starting @modelcontextprotocol/inspector@0.16.2 ...' -ForegroundColor Cyan
Write-Host ""

try {
    & npx --yes '@modelcontextprotocol/inspector@0.16.2'
    exit $LASTEXITCODE
}
finally {
    Stop-McpServerBackground
}
