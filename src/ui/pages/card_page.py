from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                          QPushButton, QLabel, QComboBox, 
                          QLineEdit, QScrollArea, QFrame,
                          QGridLayout, QSpinBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

class CardPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        """设置页面UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建筛选栏
        filter_bar = self.create_filter_bar()
        layout.addWidget(filter_bar)
        
        # 创建卡面显示区域
        content = self.create_content()
        layout.addWidget(content)
        
    def create_filter_bar(self):
        """创建筛选栏"""
        filter_frame = QFrame()
        filter_frame.setObjectName("filterFrame")
        
        layout = QHBoxLayout(filter_frame)
        layout.setContentsMargins(10, 0, 10, 10)
        
        # 添加卡片类型筛选
        type_label = QLabel("卡片类型:")
        layout.addWidget(type_label)
        
        type_combo = QComboBox()
        type_combo.addItems(["全部", "活动卡", "常驻卡", "限定卡"])
        type_combo.setObjectName("filterCombo")
        layout.addWidget(type_combo)
        
        # 添加角色筛选
        char_label = QLabel("角色:")
        layout.addWidget(char_label)
        
        char_combo = QComboBox()
        char_combo.addItems(["全部", "Kasumi", "Tae", "Rimi", "Saaya", "Arisa"])
        char_combo.setObjectName("filterCombo")
        layout.addWidget(char_combo)
        
        # 添加星级筛选
        star_label = QLabel("星级:")
        layout.addWidget(star_label)
        
        star_combo = QComboBox()
        star_combo.addItems(["全部", "1★", "2★", "3★", "4★"])
        star_combo.setObjectName("filterCombo")
        layout.addWidget(star_combo)
        
        layout.addStretch()
        
        return filter_frame
        
    def create_content(self):
        """创建内容显示区域"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("cardScroll")
        
        content = QWidget()
        layout = QGridLayout(content)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(20)
        
        # 这里后续会添加卡面网格显示
        placeholder = QLabel("卡面显示区域\n(加载中...)")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: #666; font-size: 16px;")
        layout.addWidget(placeholder, 0, 0)
        
        scroll.setWidget(content)
        return scroll

    def reset(self):
        """重置页面状态"""
        # 清空所有内容
        self.setup_ui()