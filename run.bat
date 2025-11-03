@echo off
chcp 65001 >nul
echo 正在启动 Bestdori Card Manager...
python run.py
if errorlevel 1 (
    echo.
    echo 启动失败！请检查：
    echo 1. 是否已安装 Python 3.8 或更高版本
    echo 2. 是否已安装所有依赖：pip install -r requirements.txt
    echo 3. 查看上方错误信息
    pause
)

