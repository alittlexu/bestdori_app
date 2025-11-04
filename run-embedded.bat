@echo off
REM 使用Python Embedded运行应用
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
set PYTHONIOENCODING=UTF-8

set PYTHON_EMBED_DIR=python_embedded

echo ========================================
echo   Bestdori 应用 - Embedded Python 启动
echo ========================================
echo.

REM 检查Python Embedded是否存在
if not exist "%PYTHON_EMBED_DIR%\python.exe" (
    echo [错误] 未找到 Python Embedded 环境！
    echo.
    echo 请先运行 setup-python-embedded.bat 配置环境
    echo.
    pause
    exit /b 1
)

REM 检查依赖是否已安装
"%PYTHON_EMBED_DIR%\python.exe" -c "import PyQt6" >nul 2>&1
if errorlevel 1 (
    echo [警告] 检测到依赖包未安装
    echo.
    set /p INSTALL_DEPS=是否现在安装依赖？(Y/N): 
    if /i "!INSTALL_DEPS!"=="Y" (
        call install-dependencies.bat
        if errorlevel 1 (
            echo [错误] 依赖安装失败，无法启动应用
            pause
            exit /b 1
        )
    ) else (
        echo [错误] 未安装依赖，无法启动应用
        pause
        exit /b 1
    )
)

echo [信息] 启动应用...
echo.

REM 使用Python Embedded运行应用
"%PYTHON_EMBED_DIR%\python.exe" run.py

REM 检查退出代码
if errorlevel 1 (
    echo.
    echo [错误] 应用启动失败！
    echo.
    echo 可能的解决方案：
    echo 1. 检查依赖是否完整安装
    echo 2. 查看上面的错误信息
    echo 3. 尝试重新安装依赖：install-dependencies.bat
    echo.
    pause
    exit /b 1
)

exit /b 0

