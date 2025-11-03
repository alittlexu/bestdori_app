 #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BanG Dream! 工具箱打包脚本
"""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path
from datetime import datetime

def clean_directories():
    """清理构建目录"""
    print("清理旧的构建文件...")
    for dir_name in ['build', 'dist', '__pycache__']:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
    
    # 删除旧的spec文件
    for spec_file in Path('.').glob('*.spec'):
        os.remove(spec_file)

def create_version_file():
    """创建版本信息文件"""
    print("生成版本信息...")
    version = "2.1.2"
    build_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open('version.txt', 'w', encoding='utf-8') as f:
        f.write(f"版本: {version}\n")
        f.write(f"构建日期: {build_date}\n")
        f.write(f"系统: {platform.system()} {platform.release()}\n")
        f.write(f"Python版本: {platform.python_version()}\n")

def build_executable():
    """构建可执行文件"""
    print("正在构建可执行文件...")
    
    # 确保assets目录存在
    if not os.path.exists('assets/icons/bestdori.ico'):
        print("错误: 缺少图标文件 assets/icons/bestdori.ico")
        return False
    
    # 创建版本信息文件
    create_version_file()
    
    # PyInstaller命令参数
    cmd = [
        'pyinstaller',
        'run.py',                           # 主程序入口
        '--name=BanG Dream! 工具箱',        # 应用名称
        '--windowed',                       # GUI模式
        '--icon=assets/icons/bestdori.ico', # 应用图标
        '--onefile',                        # 单文件模式
        '--noconfirm',                      # 不确认覆盖
        '--clean',                          # 清理临时文件
        '--add-data=assets;assets',         # 添加资源文件
        '--add-data=character_list.json;.', # 添加角色列表
        '--add-data=config;config',         # 添加配置文件
        '--add-data=version.txt;.',         # 添加版本信息
    ]
    
    # 运行PyInstaller
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"构建失败: {e}")
        return False

def create_desktop_shortcut():
    """创建桌面快捷方式"""
    print("正在创建桌面快捷方式...")
    
    try:
        import winshell
        from win32com.client import Dispatch
        
        # 获取桌面路径和目标文件路径
        desktop = winshell.desktop()
        target_exe = os.path.abspath(os.path.join('dist', 'BanG Dream! 工具箱.exe'))
        icon_path = os.path.abspath(os.path.join('assets', 'icons', 'bestdori.ico'))
        
        # 确保目标文件存在
        if not os.path.exists(target_exe):
            print(f"错误: 目标文件不存在 {target_exe}")
            return False
        
        # 创建快捷方式
        shortcut_path = os.path.join(desktop, "BanG Dream! 工具箱.lnk")
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = target_exe
        shortcut.WorkingDirectory = os.path.dirname(target_exe)
        shortcut.IconLocation = icon_path
        shortcut.Description = "BanG Dream! 卡面下载工具"
        shortcut.save()
        
        print(f"快捷方式已创建: {shortcut_path}")
        return True
    except Exception as e:
        print(f"创建快捷方式失败: {e}")
        return False

def create_archive():
    """创建发布包"""
    print("正在创建发布包...")
    
    try:
        import zipfile
        from datetime import datetime
        
        # 版本和日期信息
        version = "2.1.2"
        date_str = datetime.now().strftime("%Y%m%d")
        
        # 压缩包名称
        zip_filename = f"BanG_Dream_工具箱_v{version}_{date_str}.zip"
        
        # 创建压缩包
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 添加可执行文件
            exe_path = os.path.join('dist', 'BanG Dream! 工具箱.exe')
            if not os.path.exists(exe_path):
                print(f"错误: 可执行文件不存在 {exe_path}")
                return False
            
            zipf.write(exe_path, 'BanG Dream! 工具箱.exe')
            
            # 添加自述文件
            with open('README.txt', 'w', encoding='utf-8') as f:
                f.write("BanG Dream! 工具箱 v2.1.2\n")
                f.write("==========================\n\n")
                f.write("本工具用于下载BanG Dream!游戏中的卡面资源。\n\n")
                f.write("使用方法:\n")
                f.write("1. 解压缩本压缩包\n")
                f.write("2. 运行 BanG Dream! 工具箱.exe\n")
                f.write("3. 按照界面提示进行操作\n\n")
                f.write("注意事项:\n")
                f.write("- 本工具仅供个人学习使用\n")
                f.write("- 下载的资源版权归原作者所有\n")
                f.write("- 如有问题请联系开发者\n\n")
                f.write(f"构建日期: {datetime.now().strftime('%Y-%m-%d')}\n")
            
            zipf.write('README.txt', 'README.txt')
        
        # 清理临时文件
        if os.path.exists('README.txt'):
            os.remove('README.txt')
        
        print(f"发布包已创建: {os.path.abspath(zip_filename)}")
        return True
    except Exception as e:
        print(f"创建发布包失败: {e}")
        return False

def main():
    """主函数"""
    print("="*60)
    print("BanG Dream! 工具箱打包工具")
    print("="*60)
    
    # 步骤1: 清理旧的构建文件
    clean_directories()
    
    # 步骤2: 构建可执行文件
    if not build_executable():
        print("构建失败，程序终止。")
        return
    
    # 步骤3: 创建桌面快捷方式
    create_desktop_shortcut()
    
    # 步骤4: 创建发布包
    create_archive()
    
    # 完成
    print("="*60)
    print("构建完成!")
    print(f"可执行文件位置: {os.path.abspath(os.path.join('dist', 'BanG Dream! 工具箱.exe'))}")
    print("="*60)

if __name__ == '__main__':
    main()