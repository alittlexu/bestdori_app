#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bestdori Card Manager - 主启动脚本
启动图形用户界面应用程序
"""

import sys
import os

# 确保项目根目录在 Python 路径中
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow


def main():
    """主函数：启动 GUI 应用程序"""
    # 创建应用程序实例
    app = QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle('Fusion')
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用程序事件循环
    sys.exit(app.exec())


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n程序已手动终止")
        sys.exit(1)
    except Exception as e:
        print(f"\n程序启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

