#Requires -Version 5.1
<#
.SYNOPSIS
    Creates a local .venv (if missing), installs both agents' dependencies, and runs a sample critique with each.
#>

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$venvPath = Join-Path $root ".venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "Creating virtual environment at $venvPath ..."
    python -m venv $venvPath
}

Write-Host "Installing pydantic/ dependencies ..."
& $venvPython -m pip install -q --upgrade pip
& $venvPython -m pip install -q -r (Join-Path $root "pydantic\requirements.txt")

Write-Host "Installing autogen/ dependencies ..."
& $venvPython -m pip install -q -r (Join-Path $root "autogen\requirements.txt")

Write-Host "Installing Streamlit app dependencies ..."
& $venvPython -m pip install -q -r (Join-Path $root "requirements.txt")

Write-Host "`n=== Running pydantic-ai critique agent ==="
Push-Location (Join-Path $root "pydantic")
try {
    & $venvPython main.py
} finally {
    Pop-Location
}

Write-Host "`n=== Running AutoGen critique agent ==="
Push-Location (Join-Path $root "autogen")
try {
    & $venvPython main.py
} finally {
    Pop-Location
}
