# Xiaohongshu MCP launcher (PowerShell)
# Default: debugpy on 5678; use --no-debug for normal runs.
# Usage: .\run.ps1 [options]

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

function Show-Help {
    Write-Host "Xiaohongshu MCP launcher" -ForegroundColor Green
    Write-Host ""
    Write-Host "By default debugpy blocks until a debugger attaches (port 5678)."
    Write-Host "For daily use add: --no-debug"
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Cyan
    Write-Host "    .\run.ps1 [options]"
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Cyan
    Write-Host "    --no-debug          Run MCP directly (no debugpy)"
    Write-Host "    --port PORT         HTTP port (default: 8003)"
    Write-Host "    --headless          Headless browser"
    Write-Host "    help, --help, -h    Show this help"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Cyan
    Write-Host "    .\run.ps1 --no-debug"
    Write-Host "    .\run.ps1 --no-debug --port 9000"
    Write-Host "    .\run.ps1             # debug: wait for attach on 5678"
    Write-Host ""
}

function Get-UvExecutable {
    $cmd = Get-Command uv -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source) {
        return $cmd.Source
    }
    $local = Join-Path $env:USERPROFILE ".local\bin\uv.exe"
    if (Test-Path -LiteralPath $local) {
        return $local
    }
    Write-Host "ERROR: uv not found." -ForegroundColor Red
    Write-Host 'Install: powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"'
    exit 1
}

function Test-UvPythonImport {
    param(
        [Parameter(Mandatory)][string]$UvExe,
        [Parameter(Mandatory)][string]$ModuleName
    )
    $cmdLine = "`"$UvExe`" run python -c `"import $ModuleName`" >nul 2>&1"
    cmd.exe /c $cmdLine | Out-Null
    return ($LASTEXITCODE -eq 0)
}

function Test-UvDependencies {
    param([string]$UvExe)
    if (-not (Test-UvPythonImport -UvExe $UvExe -ModuleName "xiaohongshu_mcp_python")) {
        Write-Host "Installing dependencies (uv sync)..." -ForegroundColor Yellow
        & $UvExe sync
    }
}

$ExtraArgs = @()
$EnvArgs = @("--env", "development")
$NoDebug = $false
$i = 0
$argv = $args

while ($i -lt $argv.Count) {
    $a = $argv[$i]
    switch -Regex ($a) {
        '^(help|--help|-h)$' {
            Show-Help
            exit 0
        }
        '^--no-debug$' {
            $NoDebug = $true
            $i += 1
            continue
        }
        '^--port$' {
            if ($i + 1 -ge $argv.Count) {
                Write-Host "ERROR: --port requires a value." -ForegroundColor Red
                exit 1
            }
            $ExtraArgs += @("--port", $argv[$i + 1])
            $i += 2
            continue
        }
        '^--headless$' {
            $ExtraArgs += "--headless"
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

if ($ExtraArgs -notcontains "--port") {
    $ExtraArgs += @("--port", "8003")
}

$UvExe = Get-UvExecutable
Test-UvDependencies -UvExe $UvExe

$headless = $ExtraArgs -contains "--headless"

if ($headless) {
    $env:BROWSER_HEADLESS = "true"
}
else {
    $env:BROWSER_HEADLESS = "false"
}

if ($NoDebug) {
    Write-Host "Starting (no debugpy)" -ForegroundColor Green
}
else {
    Write-Host "Starting (debugpy, port 5678)" -ForegroundColor Green
}
Write-Host "Environment: development" -ForegroundColor Cyan
if ($headless) {
    Write-Host "Browser: headless" -ForegroundColor Cyan
}
else {
    Write-Host "Browser: headed" -ForegroundColor Cyan
}

if (-not $NoDebug) {
    Write-Host "Debugger waits on 5678; use .\run.ps1 --no-debug to skip." -ForegroundColor Yellow
    Write-Host ""
}

if (-not $headless) {
    Write-Host "A browser window will open on the desktop session." -ForegroundColor DarkGray
    Write-Host ""
}

if ($NoDebug) {
    $runArgs = @("run", "python", "-m", "xiaohongshu_mcp_python.main") + $EnvArgs + $ExtraArgs
    $joined = $runArgs -join " "
    Write-Host "Command: $UvExe $joined" -ForegroundColor Yellow
    Write-Host ""
    & $UvExe @runArgs
    exit $LASTEXITCODE
}

if (-not (Test-UvPythonImport -UvExe $UvExe -ModuleName "debugpy")) {
    Write-Host "Installing debugpy..." -ForegroundColor Yellow
    & $UvExe pip install debugpy
}

$tempPy = Join-Path ([System.IO.Path]::GetTempPath()) ("xiaohongshu_debug_" + [guid]::NewGuid().ToString("N") + ".py")
$pythonBootstrap = @'
import debugpy
import sys
import os

debugpy.listen(('localhost', 5678))
print('debugpy listening on 5678; attach your IDE debugger')
debugpy.wait_for_client()

sys.path.insert(0, os.path.join(os.getcwd(), 'src'))
os.environ['PYTHONPATH'] = os.path.join(os.getcwd(), 'src')

from xiaohongshu_mcp_python.main import cli_main
cli_main()
'@
Set-Content -LiteralPath $tempPy -Value $pythonBootstrap -Encoding UTF8

try {
    $runArgs = @("run", "python", $tempPy) + $EnvArgs + $ExtraArgs
    $joined = $runArgs -join " "
    Write-Host "Command: $UvExe $joined" -ForegroundColor Yellow
    Write-Host ""
    & $UvExe @runArgs
    exit $LASTEXITCODE
}
finally {
    Remove-Item -LiteralPath $tempPy -ErrorAction SilentlyContinue
}
