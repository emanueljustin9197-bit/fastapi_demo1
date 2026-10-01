@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo [错误] 未找到 Python，请先安装 Python 3.9 或更高版本。
  pause
  exit /b 1
)

where node >nul 2>nul
if errorlevel 1 (
  echo [错误] 未找到 Node.js，请先安装 Node.js 18 或更高版本。
  pause
  exit /b 1
)

if not exist "backend\.env" (
  copy /Y "backend\.env.example" "backend\.env" >nul
  echo [提示] 已生成 backend\.env，请填入 MySQL 密码、随机 SECRET_KEY 和可选的 DeepSeek Key。
)

if not exist "backend\.venv\Scripts\python.exe" (
  echo [1/4] 创建 Python 虚拟环境...
  python -m venv "backend\.venv"
  if errorlevel 1 goto :failed
)

echo [2/4] 安装后端依赖...
"backend\.venv\Scripts\python.exe" -m pip install -r "backend\requirements.txt"
if errorlevel 1 goto :failed

echo [3/4] 安装前端依赖...
pushd "frontend"
call npm.cmd install
if errorlevel 1 (
  popd
  goto :failed
)

echo [4/4] 构建前端生产文件...
call npm.cmd run build
if errorlevel 1 (
  popd
  goto :failed
)
popd

echo.
echo 安装和构建完成。
echo 下一步：
echo 1. 使用 database\schema.sql 初始化 MySQL 8 数据库。
echo 2. 检查 backend\.env 中的数据库密码和 SECRET_KEY。
echo 3. 双击 02_启动系统.bat。
pause
exit /b 0

:failed
echo.
echo [错误] 安装或构建失败，请根据上方信息检查环境。
pause
exit /b 1
