@echo off
echo ====================================
echo Bestdori App 环境搭建脚本
echo ====================================
echo.

:: 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.8或更高版本
    pause
    exit /b 1
)

:: 检查pip是否安装
pip --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到pip，请确保Python安装正确
    pause
    exit /b 1
)

:: 创建虚拟环境
echo [步骤1/4] 创建虚拟环境...
python -m venv venv
if errorlevel 1 (
    echo [错误] 创建虚拟环境失败
    pause
    exit /b 1
)

:: 激活虚拟环境
echo [步骤2/4] 激活虚拟环境...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [错误] 激活虚拟环境失败
    pause
    exit /b 1
)

:: 升级pip
echo [步骤3/4] 升级pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo [警告] pip升级失败，但将继续安装依赖
)

:: 安装依赖
echo [步骤4/4] 安装项目依赖...
pip install -r requirements.txt
if errorlevel 1 (
    echo [错误] 安装依赖失败
    pause
    exit /b 1
)

echo.
echo ====================================
echo 环境搭建完成！
echo 使用说明：
echo 1. 每次开始工作时，运行 venv\Scripts\activate.bat 激活虚拟环境
echo 2. 工作结束后，输入 deactivate 命令退出虚拟环境
echo ====================================
pause 