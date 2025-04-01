@echo off
echo 正在安装 BanG Dream! 卡面下载工具...
echo.

REM 检查Python是否已安装
python --version >nul 2>&1
if errorlevel 1 (
    echo Python未安装，请先安装Python 3.8或更高版本
    echo 访问 https://www.python.org/downloads/ 下载安装
    pause
    exit /b 1
)

REM 创建虚拟环境
echo 正在创建虚拟环境...
python -m venv venv
if errorlevel 1 (
    echo 创建虚拟环境失败
    pause
    exit /b 1
)

REM 激活虚拟环境
echo 正在激活虚拟环境...
call venv\Scripts\activate
if errorlevel 1 (
    echo 激活虚拟环境失败
    pause
    exit /b 1
)

REM 安装依赖
echo 正在安装依赖包...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
    echo 安装依赖包失败
    pause
    exit /b 1
)

REM 创建启动脚本
echo 正在创建启动脚本...
echo @echo off > start.bat
echo call venv\Scripts\activate >> start.bat
echo python src/gui/app.py >> start.bat

echo.
echo 安装完成！
echo 请双击 start.bat 运行程序
echo.
pause 