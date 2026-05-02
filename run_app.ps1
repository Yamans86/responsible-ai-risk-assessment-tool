$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

Set-Location $ProjectRoot
& $Python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --server.headless true
