import os
import sys

def _append_run_path():
    """添加运行时路径"""
    if getattr(sys, 'frozen', False):
        # 如果是打包后的exe
        application_path = os.path.dirname(sys.executable)
        if application_path not in sys.path:
            sys.path.append(application_path)
            
        # 添加DLL目录
        dll_path = os.path.join(application_path, 'DLLs')
        if os.path.exists(dll_path) and dll_path not in os.environ['PATH']:
            os.environ['PATH'] = dll_path + os.pathsep + os.environ['PATH']
            
        # 添加Python DLL目录
        python_dll_path = os.path.dirname(sys.executable)
        if python_dll_path not in os.environ['PATH']:
            os.environ['PATH'] = python_dll_path + os.pathsep + os.environ['PATH']

_append_run_path()