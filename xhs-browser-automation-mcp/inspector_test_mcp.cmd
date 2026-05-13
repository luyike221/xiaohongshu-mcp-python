@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0inspector_test_mcp.ps1" %*
