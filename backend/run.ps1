$ErrorActionPreference = "Stop"
$backendRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $backendRoot
& .\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
