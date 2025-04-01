@echo off
setlocal enabledelayedexpansion

REM 设置代码页为UTF-8
chcp 65001 > nul

REM 检查Python是否已安装
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed. Please install Python 3.8 or higher.
    echo Visit https://www.python.org/downloads/ to download and install.
    pause
    exit /b 1
)

REM 创建虚拟环境
echo Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo Failed to create virtual environment.
    pause
    exit /b 1
)

REM 激活虚拟环境
echo Activating virtual environment...
call venv\Scripts\activate
if errorlevel 1 (
    echo Failed to activate virtual environment.
    pause
    exit /b 1
)

REM 升级pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM 安装依赖
echo Installing dependencies...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
    echo Failed to install dependencies.
    pause
    exit /b 1
)

REM 创建启动脚本
echo Creating startup script...
(
echo @echo off
echo chcp 65001 ^> nul
echo call venv\Scripts\activate
echo python src/gui/app.py
) > start.bat

echo.
echo Installation completed!
echo Please double click start.bat to run the program.
echo.
pause 