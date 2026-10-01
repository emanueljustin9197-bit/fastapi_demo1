@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

if not exist "backend\.env" (
  echo [错误] 缺少 backend\.env，请先双击 01_安装依赖.bat 并完成配置。
  pause
  exit /b 1
)

if not exist "backend\.venv\Scripts\python.exe" (
  echo [错误] 后端依赖未安装，请先双击 01_安装依赖.bat。
  pause
  exit /b 1
)

if not exist "frontend\node_modules" (
  echo [错误] 前端依赖未安装，请先双击 01_安装依赖.bat。
  pause
  exit /b 1
)

start "Online Form API - 8000" cmd /k "cd /d ""%~dp0backend"" && .venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000"
start "Online Form Web - 5173" cmd /k "cd /d ""%~dp0frontend"" && npm.cmd run dev -- --host 0.0.0.0"

echo 后端和前端正在启动，请保留两个服务窗口。
timeout /t 4 /nobreak >nul
start "" "http://localhost:5173"
exit /b 0
