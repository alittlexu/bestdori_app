@echo off
REM 安装Python依赖包
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

set PYTHON_EMBED_DIR=python_embedded
set MAX_RETRIES=2

echo ========================================
echo   安装应用依赖包
echo ========================================
echo.

REM ========================================
REM 检查 Python Embedded 环境
REM ========================================
echo [检查] 验证 Python Embedded 环境...
if not exist "%PYTHON_EMBED_DIR%\python.exe" (
    echo [错误] 未找到 Python Embedded 环境！
    echo.
    echo 环境位置: %CD%\%PYTHON_EMBED_DIR%
    echo.
    echo 可能的原因：
    echo 1. 尚未运行 setup-python-embedded.bat
    echo 2. Python Embedded 环境被删除
    echo 3. 路径不正确
    echo.
    echo 解决方案：
    echo 请先运行 setup-python-embedded.bat 配置环境
    echo.
    pause
    exit /b 1
)

REM 验证Python是否可用
"%PYTHON_EMBED_DIR%\python.exe" --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Python 无法运行！
    echo.
    echo 可能的原因：
    echo 1. Python Embedded 环境不完整
    echo 2. 文件损坏
    echo.
    echo 解决方案：
    echo 1. 重新运行 setup-python-embedded.bat
    echo 2. 或删除 python_embedded 文件夹后重新配置
    echo.
    pause
    exit /b 1
)

"%PYTHON_EMBED_DIR%\python.exe" --version
echo [成功] Python 环境正常
echo [信息] 使用 Python Embedded: %CD%\%PYTHON_EMBED_DIR%
echo.

REM ========================================
REM 检查并安装 pip
REM ========================================
echo [检查] 验证 pip 是否可用...
"%PYTHON_EMBED_DIR%\python.exe" -m pip --version >nul 2>&1
if errorlevel 1 (
    echo [信息] pip 未安装，正在安装 pip...
    echo.
    
    REM 下载get-pip.py
    cd "%PYTHON_EMBED_DIR%"
    set PIP_URL=https://bootstrap.pypa.io/get-pip.py
    set PIP_RETRY=0
    
    :download_pip_script
    where curl >nul 2>&1
    if %errorlevel%==0 (
        echo [下载] 使用 curl 下载 pip 安装脚本...
        curl -L -o get-pip.py "%PIP_URL%" 2>nul
    ) else (
        echo [下载] 使用 PowerShell 下载 pip 安装脚本...
        powershell -Command "$ProgressPreference = 'SilentlyContinue'; try { Invoke-WebRequest -Uri '%PIP_URL%' -OutFile 'get-pip.py' -ErrorAction Stop; exit 0 } catch { Write-Host $_.Exception.Message; exit 1 }" 2>nul
    )
    
    if not exist "get-pip.py" (
        set /a PIP_RETRY+=1
        if !PIP_RETRY! lss 3 (
            echo [重试] 下载 pip 安装脚本（第 !PIP_RETRY!/3 次）...
            timeout /t 2 >nul
            goto :download_pip_script
        ) else (
            echo [错误] 无法下载 pip 安装脚本
            echo.
            echo 可能的原因：
            echo 1. 网络连接问题
            echo 2. 无法访问 bootstrap.pypa.io
            echo 3. 防火墙阻止
            echo.
            echo 解决方案：
            echo 1. 检查网络连接
            echo 2. 配置代理或VPN
            echo 3. 手动下载 get-pip.py 放到 python_embedded 目录
            echo    下载地址: %PIP_URL%
            echo.
            cd ..
            pause
            exit /b 1
        )
    )
    
    echo [安装] 正在安装 pip...
    python.exe get-pip.py --no-warn-script-location 2>&1
    if errorlevel 1 (
        echo [错误] pip 安装失败！
        echo.
        echo 可能的原因：
        echo 1. Python 环境配置不完整
        echo 2. 网络问题导致下载失败
        echo 3. 权限问题
        echo.
        echo 解决方案：
        echo 1. 检查网络连接
        echo 2. 以管理员身份运行此脚本
        echo 3. 重新运行 setup-python-embedded.bat
        echo.
        del get-pip.py 2>nul
        cd ..
        pause
        exit /b 1
    )
    
    del get-pip.py 2>nul
    cd ..
    
    REM 验证pip安装
    "%PYTHON_EMBED_DIR%\python.exe" -m pip --version >nul 2>&1
    if errorlevel 1 (
        echo [错误] pip 安装后仍不可用！
        echo.
        echo 请检查 Python Embedded 环境配置
        echo 尝试重新运行 setup-python-embedded.bat
        echo.
        pause
        exit /b 1
    )
    
    "%PYTHON_EMBED_DIR%\python.exe" -m pip --version
    echo [成功] pip 安装完成
) else (
    "%PYTHON_EMBED_DIR%\python.exe" -m pip --version
    echo [成功] pip 已可用
)
echo.

REM ========================================
REM 检查 requirements.txt
REM ========================================
echo [检查] 验证 requirements.txt...
if not exist "requirements.txt" (
    echo [错误] 未找到 requirements.txt 文件！
    echo.
    echo 请确保在项目根目录运行此脚本
    echo.
    pause
    exit /b 1
)
echo [成功] requirements.txt 存在
echo.

REM ========================================
REM 安装依赖包
REM ========================================
echo [安装] 开始安装依赖包...
echo 这可能需要较长时间（5-15分钟），请耐心等待...
echo [提示] 如果下载速度慢，可以按 Ctrl+C 中断，然后使用镜像源重试
echo.

set INSTALL_RETRY=0
:install_dependencies
"%PYTHON_EMBED_DIR%\python.exe" -m pip install --no-warn-script-location -r requirements.txt 2>&1
if errorlevel 1 (
    echo.
    echo ========================================
    echo   依赖安装失败 - 问题诊断
    echo ========================================
    echo.
    set /a INSTALL_RETRY+=1
    
    if !INSTALL_RETRY! lss !MAX_RETRIES! (
        echo [重试] 第 !INSTALL_RETRY!/!MAX_RETRIES! 次重试安装...
        echo.
        timeout /t 3 >nul
        goto :install_dependencies
    )
    
    echo 可能的原因：
    echo 1. 网络连接不稳定或中断
    echo 2. PyPI 服务器暂时不可用
    echo 3. 防火墙或代理阻止了连接
    echo 4. 某些包需要编译，但缺少编译工具
    echo 5. 磁盘空间不足
    echo.
    echo ========================================
    echo   解决方案
    echo ========================================
    echo.
    echo 方案一：使用国内镜像源（推荐）
    echo ----------------------------
    echo 运行以下命令使用清华大学镜像源：
    echo.
    echo   python_embedded\python.exe -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-warn-script-location -r requirements.txt
    echo.
    echo 其他镜像源：
    echo - 阿里云: https://mirrors.aliyun.com/pypi/simple/
    echo - 中科大: https://pypi.mirrors.ustc.edu.cn/simple/
    echo.
    echo 方案二：检查网络和权限
    echo ----------------------------
    echo 1. 检查网络连接是否正常
    echo 2. 如果使用代理，确保代理配置正确
    echo 3. 尝试以管理员身份运行此脚本
    echo 4. 检查防火墙设置
    echo.
    echo 方案三：分步安装
    echo ----------------------------
    echo 如果某些包安装失败，可以尝试单独安装：
    echo    python_embedded\python.exe -m pip install --no-warn-script-location 包名
    echo.
    echo 方案四：检查错误信息
    echo ----------------------------
    echo 查看上方的详细错误信息，根据具体错误进行修复
    echo.
    set /p USE_MIRROR=是否使用清华大学镜像源重试？(Y/N): 
    if /i "!USE_MIRROR!"=="Y" (
        echo.
        echo [重试] 使用清华大学镜像源安装...
        "%PYTHON_EMBED_DIR%\python.exe" -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-warn-script-location -r requirements.txt 2>&1
        if errorlevel 1 (
            echo.
            echo [错误] 使用镜像源后仍然失败
            echo 请查看上方的详细错误信息
            echo.
            pause
            exit /b 1
        )
    ) else (
        pause
        exit /b 1
    )
)

REM ========================================
REM 验证安装结果
REM ========================================
echo.
echo [检查] 验证关键依赖是否安装成功...
"%PYTHON_EMBED_DIR%\python.exe" -c "import PyQt6" >nul 2>&1
if errorlevel 1 (
    echo [警告] PyQt6 未正确安装
    echo 这可能导致应用无法启动
    echo.
) else (
    echo [成功] PyQt6 已安装
)

"%PYTHON_EMBED_DIR%\python.exe" -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo [警告] requests 未正确安装
) else (
    echo [成功] requests 已安装
)

"%PYTHON_EMBED_DIR%\python.exe" -c "import PIL" >nul 2>&1
if errorlevel 1 (
    echo [警告] Pillow 未正确安装
) else (
    echo [成功] Pillow 已安装
)

echo.
echo ========================================
echo   依赖安装完成！
echo ========================================
echo.
echo [下一步]
echo 现在可以运行 run-embedded.bat 启动应用
echo.
echo [提示]
echo - 如果应用启动失败，请检查上方的依赖验证结果
echo - 某些依赖可能需要系统库支持（如 Visual C++ Redistributable）
echo.

pause
exit /b 0

