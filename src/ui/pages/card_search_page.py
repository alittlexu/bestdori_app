from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                          QPushButton, QLabel, QComboBox, 
                          QLineEdit, QScrollArea, QFrame,
                          QGridLayout, QSpinBox)
from PyQt6.QtCore import Qt

class CardSearchPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        """设置页面UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建搜索栏
        search_bar = self.create_search_bar()
        layout.addWidget(search_bar)
        
        # 创建搜索结果区域
        content = self.create_content()
        layout.addWidget(content)
        
    def create_search_bar(self):
        """创建搜索栏"""
        search_frame = QFrame()
        search_frame.setObjectName("filterFrame")
        
        layout = QHBoxLayout(search_frame)
        layout.setContentsMargins(10, 0, 10, 10)
        
        # 添加搜索框
        search_label = QLabel("搜索:")
        layout.addWidget(search_label)
        
        search_box = QLineEdit()
        search_box.setPlaceholderText("输入卡面名称或ID")
        search_box.setObjectName("searchBox")
        layout.addWidget(search_box)
        
        # 添加搜索按钮
        search_btn = QPushButton("搜索")
        search_btn.setObjectName("searchBtn")
        layout.addWidget(search_btn)
        
        layout.addStretch()
        
        return search_frame
        
    def create_content(self):
        """创建内容显示区域"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("cardScroll")
        
        content = QWidget()
        layout = QGridLayout(content)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(20)
        
        # 这里后续会添加搜索结果列表
        placeholder = QLabel("搜索结果区域\n(请输入搜索内容)")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: #666; font-size: 16px;")
        layout.addWidget(placeholder, 0, 0)
        
        scroll.setWidget(content)
        return scroll
        
    def reset(self):
        """重置页面状态"""
        # 清空所有内容
        self.setup_ui() 