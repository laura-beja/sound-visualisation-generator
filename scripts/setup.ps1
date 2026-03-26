# Windows script to set up development Enviroment

$ErrorActionPreference = "Stop"

Set-Location ( Join-Path $PSScriptRoot "..")

if (-not (Test-Path ".venv")) {
    py -m venv .venv
}

& .\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r requirements.txt -r requirements-dev.txt 
python -m pip install -e .

Write-Host "Setup complete"
  

  
