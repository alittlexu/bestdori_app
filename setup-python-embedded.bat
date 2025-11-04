@echo off
REM Python Embedded 自动配置脚本
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

echo ========================================
echo   Python Embedded 自动配置脚本
echo ========================================
echo.

set PYTHON_EMBED_DIR=python_embedded
set PYTHON_VERSION=3.11.9
set PYTHON_ARCH=amd64
set PYTHON_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-embed-%PYTHON_ARCH%.zip
set MAX_RETRIES=3
set RETRY_COUNT=0

REM 检查是否已存在Python Embedded
if exist "%PYTHON_EMBED_DIR%\python.exe" (
    echo [信息] 检测到已存在的 Python Embedded 环境
    echo [信息] 位置: %CD%\%PYTHON_EMBED_DIR%
    echo.
    echo 是否重新下载并配置？(Y/N)
    set /p REINSTALL=
    if /i not "!REINSTALL!"=="Y" (
        echo 跳过下载，使用现有环境。
        echo.
        echo 下一步：运行 install-dependencies.bat 安装依赖
        echo.
        pause
        exit /b 0
    )
    echo 删除旧环境...
    rmdir /s /q "%PYTHON_EMBED_DIR%" 2>nul
)

REM ========================================
REM 步骤 1/5: 创建目录
REM ========================================
echo [步骤 1/5] 创建目录...
if not exist "%PYTHON_EMBED_DIR%" (
    mkdir "%PYTHON_EMBED_DIR%"
    if errorlevel 1 (
        echo [错误] 无法创建目录: %PYTHON_EMBED_DIR%
        echo.
        echo 可能的原因：
        echo 1. 没有写入权限
        echo 2. 磁盘空间不足
        echo 3. 目录被其他程序占用
        echo.
        echo 解决方案：
        echo 1. 以管理员身份运行此脚本
        echo 2. 检查磁盘空间
        echo 3. 关闭可能占用目录的程序
        echo.
        pause
        exit /b 1
    )
    echo [成功] 目录创建成功
) else (
    echo [信息] 目录已存在
)
cd "%PYTHON_EMBED_DIR%"

REM ========================================
REM 步骤 2/5: 检查网络连接
REM ========================================
echo [步骤 2/5] 检查网络连接...
ping -n 1 www.python.org >nul 2>&1
if errorlevel 1 (
    echo [警告] 无法连接到 python.org，可能网络有问题
    echo.
    set /p CONTINUE=是否继续尝试下载？(Y/N): 
    if /i not "!CONTINUE!"=="Y" (
        echo 已取消下载
        cd ..
        pause
        exit /b 1
    )
) else (
    echo [成功] 网络连接正常
)
echo.

REM ========================================
REM 步骤 3/5: 下载 Python Embedded
REM ========================================
:download_start
echo [步骤 3/5] 下载 Python Embedded %PYTHON_VERSION%...
echo 这可能需要几分钟，请耐心等待...
echo.
echo 下载地址: %PYTHON_URL%
echo.

REM 检查下载工具
set DOWNLOAD_TOOL=
where curl >nul 2>&1
if %errorlevel%==0 (
    set DOWNLOAD_TOOL=curl
    echo [信息] 使用 curl 下载
) else (
    where powershell >nul 2>&1
    if %errorlevel%==0 (
        set DOWNLOAD_TOOL=powershell
        echo [信息] 使用 PowerShell 下载
    ) else (
        echo [错误] 未找到可用的下载工具！
        echo.
        echo 需要以下工具之一：
        echo 1. curl（Windows 10 1803+ 自带）
        echo 2. PowerShell（Windows 自带）
        echo.
        echo 解决方案：
        echo 1. 更新 Windows 到最新版本
        echo 2. 或手动下载 Python Embedded（见下方说明）
        goto :manual_download_guide
    )
)

REM 执行下载
if "!DOWNLOAD_TOOL!"=="curl" (
    echo 正在下载...
    curl -L -o python-embed.zip "%PYTHON_URL%"
    set DOWNLOAD_ERROR=!errorlevel!
) else (
    echo 正在下载...
    powershell -Command "$ProgressPreference = 'SilentlyContinue'; try { Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile 'python-embed.zip' -ErrorAction Stop; exit 0 } catch { Write-Host $_.Exception.Message; exit 1 }"
    set DOWNLOAD_ERROR=!errorlevel!
)

REM 检查下载结果
if !DOWNLOAD_ERROR! neq 0 (
    echo [错误] 下载过程出现错误（错误代码: !DOWNLOAD_ERROR!）
    set /a RETRY_COUNT+=1
    if !RETRY_COUNT! lss !MAX_RETRIES! (
        echo.
        echo [重试] 第 !RETRY_COUNT!/!MAX_RETRIES! 次重试...
        timeout /t 2 >nul
        goto :download_start
    ) else (
        echo [错误] 已重试 !MAX_RETRIES! 次，仍然失败
        goto :download_failed
    )
)

REM 检查文件是否存在
if not exist "python-embed.zip" (
    echo [错误] 下载失败：文件不存在
    goto :download_failed
)

REM 检查文件大小（至少应该大于1MB）
for %%A in ("python-embed.zip") do set FILE_SIZE=%%~zA
if !FILE_SIZE! lss 1048576 (
    echo [错误] 下载的文件异常小（!FILE_SIZE! 字节），可能下载不完整
    del python-embed.zip 2>nul
    set /a RETRY_COUNT+=1
    if !RETRY_COUNT! lss !MAX_RETRIES! (
        echo.
        echo [重试] 第 !RETRY_COUNT!/!MAX_RETRIES! 次重试...
        timeout /t 2 >nul
        goto :download_start
    ) else (
        goto :download_failed
    )
)

echo [成功] 下载完成（文件大小: !FILE_SIZE! 字节）
goto :download_success

:download_failed
echo.
echo ========================================
echo   下载失败 - 问题诊断
echo ========================================
echo.
echo 可能的原因：
echo 1. 网络连接不稳定或中断
echo 2. Python 官网服务器暂时不可用
echo 3. 防火墙或代理阻止了下载
echo 4. 磁盘空间不足
echo 5. 下载工具（curl/PowerShell）配置问题
echo.
echo ========================================
echo   解决方案
echo ========================================
:manual_download_guide
echo.
echo 方案一：手动下载（推荐）
echo ----------------------------
echo 1. 打开浏览器，访问以下地址：
echo    https://www.python.org/downloads/windows/
echo.
echo 2. 找到 "Python %PYTHON_VERSION%" 部分
echo.
echo 3. 下载 "Windows embeddable package (64-bit)"
echo    文件名类似: python-%PYTHON_VERSION%-embed-%PYTHON_ARCH%.zip
echo.
echo 4. 将下载的 zip 文件放到以下目录：
echo    %CD%\python_embedded\
echo.
echo 5. 将文件重命名为: python-embed.zip
echo.
echo 6. 重新运行此脚本，脚本会自动检测并解压
echo.
echo 方案二：检查网络设置
echo ----------------------------
echo 1. 检查网络连接是否正常
echo 2. 如果使用代理，请配置系统代理设置
echo 3. 检查防火墙是否阻止了下载
echo 4. 尝试使用VPN或更换网络
echo.
echo 方案三：使用镜像源（如果有）
echo ----------------------------
echo 如果您的网络环境可以使用镜像源，可以修改脚本中的下载地址
echo.
set /p RETRY_CHOICE=是否要重试下载？(R) 或 退出后手动下载？(Q): 
if /i "!RETRY_CHOICE!"=="R" (
    set RETRY_COUNT=0
    goto :download_start
)
cd ..
pause
exit /b 1

:download_success

REM ========================================
REM 步骤 4/5: 解压 Python Embedded
REM ========================================
echo [步骤 4/5] 解压 Python Embedded...
echo.

REM 检查zip文件是否有效
powershell -Command "try { Add-Type -AssemblyName System.IO.Compression.FileSystem; [System.IO.Compression.ZipFile]::OpenRead('python-embed.zip').Dispose(); exit 0 } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
    echo [错误] ZIP 文件损坏或格式不正确！
    echo.
    echo 可能的原因：
    echo 1. 下载不完整
    echo 2. 文件损坏
    echo.
    echo 解决方案：
    echo 1. 删除 python-embed.zip，重新下载
    echo 2. 或手动下载并放到当前目录
    echo.
    cd ..
    pause
    exit /b 1
)

REM 尝试使用PowerShell解压
echo 正在解压...
powershell -Command "try { Expand-Archive -Path 'python-embed.zip' -DestinationPath '.' -Force -ErrorAction Stop; exit 0 } catch { Write-Host $_.Exception.Message; exit 1 }" 2>nul
if errorlevel 1 (
    echo [警告] PowerShell 解压失败，尝试其他方法...
    
    REM 尝试使用tar（Windows 10 1803+）
    where tar >nul 2>&1
    if %errorlevel%==0 (
        echo 尝试使用 tar 解压...
        tar -xf python-embed.zip 2>nul
        if errorlevel 1 (
            goto :extract_failed
        )
    ) else (
        goto :extract_failed
    )
)

REM 验证解压结果
if not exist "python.exe" (
    echo [错误] 解压后未找到 python.exe！
    goto :extract_failed
)

echo [成功] 解压完成

del python-embed.zip 2>nul
goto :extract_success

:extract_failed
echo.
echo ========================================
echo   解压失败 - 问题诊断
echo ========================================
echo.
echo 可能的原因：
echo 1. ZIP 文件损坏
echo 2. 磁盘空间不足
echo 3. 没有解压权限
echo 4. 解压工具不可用
echo.
echo 解决方案：
echo 1. 手动解压 python-embed.zip 到当前目录
echo 2. 确保解压后包含 python.exe 文件
echo 3. 重新运行此脚本
echo.
cd ..
pause
exit /b 1

:extract_success

REM ========================================
REM 步骤 5/5: 配置 Python 环境
REM ========================================
echo [步骤 5/5] 配置 Python 环境...
echo.

REM 修改python311._pth文件以启用site-packages
REM python311._pth文件格式：每行一个路径，最后一行如果是import site则启用site-packages
REM 默认情况下，python311._pth中#import site是注释的，需要取消注释
if exist "python311._pth" (
    copy "python311._pth" "python311._pth.bak" >nul
    REM 使用PowerShell处理文件，取消注释import site行（如果被注释）
    powershell -Command "$content = Get-Content 'python311._pth.bak'; $content = $content -replace '^#import site$', 'import site'; Set-Content 'python311._pth' -Value $content" 2>nul
    if errorlevel 1 (
        REM 如果PowerShell失败，使用findstr和临时文件处理
        findstr /v "^#import site$" "python311._pth.bak" > "python311._pth.tmp" 2>nul
        if exist "python311._pth.tmp" (
            move /y "python311._pth.tmp" "python311._pth" >nul
            echo import site >> "python311._pth"
        ) else (
            REM 最后手段：直接添加import site行
            (
                type "python311._pth.bak"
                echo import site
            ) > "python311._pth"
        )
    )
    REM 验证是否成功
    findstr /c:"import site" "python311._pth" | findstr /v "^#" >nul 2>&1
    if errorlevel 1 (
        echo [警告] 可能无法正确启用 site-packages，但将继续尝试安装 pip
    )
)

REM 验证Python是否可用
echo [检查] 验证 Python 环境...
python.exe --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Python 无法运行！
    echo.
    echo 可能的原因：
    echo 1. Python 文件损坏
    echo 2. 缺少必要的系统库
    echo 3. 架构不匹配（需要64位系统）
    echo.
    echo 解决方案：
    echo 1. 重新下载 Python Embedded
    echo 2. 确保系统是64位 Windows
    echo 3. 安装 Visual C++ Redistributable
    echo.
    cd ..
    pause
    exit /b 1
)
python.exe --version
echo [成功] Python 环境正常
echo.

REM 下载get-pip.py
echo [配置] 下载 pip 安装脚本...
set PIP_URL=https://bootstrap.pypa.io/get-pip.py
set PIP_RETRY=0
:download_pip
where curl >nul 2>&1
if %errorlevel%==0 (
    curl -L -o get-pip.py "%PIP_URL%" 2>nul
) else (
    powershell -Command "$ProgressPreference = 'SilentlyContinue'; try { Invoke-WebRequest -Uri '%PIP_URL%' -OutFile 'get-pip.py' -ErrorAction Stop; exit 0 } catch { exit 1 }" 2>nul
)

if not exist "get-pip.py" (
    set /a PIP_RETRY+=1
    if !PIP_RETRY! lss 3 (
        echo [重试] 下载 pip 安装脚本（第 !PIP_RETRY!/3 次）...
        timeout /t 2 >nul
        goto :download_pip
    ) else (
        echo [警告] 无法下载 pip 安装脚本
        echo.
        echo 这不会阻止配置完成，但您需要在后续步骤中手动安装 pip
        echo 或运行 install-dependencies.bat，它会自动安装 pip
        echo.
        goto :skip_pip
    )
)

echo [成功] pip 安装脚本下载完成
echo [配置] 安装 pip...
python.exe get-pip.py --no-warn-script-location 2>&1
if errorlevel 1 (
    echo [警告] pip 安装过程中出现错误
    echo.
    echo 这通常不影响后续使用，install-dependencies.bat 会重新安装 pip
    echo.
) else (
    echo [成功] pip 安装完成
)
del get-pip.py 2>nul

:skip_pip

REM 创建site-packages目录
if not exist "site-packages" (
    mkdir "site-packages"
    if errorlevel 1 (
        echo [警告] 无法创建 site-packages 目录
    ) else (
        echo [成功] site-packages 目录创建完成
    )
)

REM 验证pip是否可用
echo.
echo [检查] 验证 pip 是否可用...
python.exe -m pip --version >nul 2>&1
if errorlevel 1 (
    echo [信息] pip 暂不可用，将在 install-dependencies.bat 中安装
) else (
    python.exe -m pip --version
    echo [成功] pip 已可用
)

cd ..

echo.
echo ========================================
echo   Python Embedded 配置完成！
echo ========================================
echo.
echo [环境信息]
echo - 位置: %CD%\%PYTHON_EMBED_DIR%
echo - Python 版本: %PYTHON_VERSION%
echo.
echo [下一步]
echo 请运行 install-dependencies.bat 安装应用依赖
echo.
echo [提示]
echo - 如果遇到问题，请查看 README_EMBEDDED.md
echo - 所有文件都保存在项目目录中，不会影响系统
echo.

pause
exit /b 0


