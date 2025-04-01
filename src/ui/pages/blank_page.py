from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class BlankPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        """设置页面UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 添加欢迎文本
        welcome_label = QLabel("欢迎使用 Bestdori Card Manager")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_label.setFont(QFont("Arial", 24))
        welcome_label.setStyleSheet("color: #2c3e50;")
        layout.addWidget(welcome_label)
        
        # 添加提示文本
        hint_label = QLabel("请从上方工具栏选择功能开始使用")
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint_label.setFont(QFont("Arial", 14))
        hint_label.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(hint_label)
        
    def reset(self):
        """重置页面状态"""
        # 空白页面不需要重置
        pass 