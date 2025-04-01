from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                          QPushButton, QLabel, QComboBox, 
                          QLineEdit, QScrollArea, QFrame,
                          QGridLayout, QSpinBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

class CardPreviewPage(QWidget):
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
        
        # 创建卡面预览区域
        content = self.create_content()
        layout.addWidget(content)
        
    def create_filter_bar(self):
        """创建筛选栏"""
        filter_frame = QFrame()
        filter_frame.setObjectName("filterFrame")
        
        layout = QHBoxLayout(filter_frame)
        layout.setContentsMargins(10, 0, 10, 10)
        
        # 添加角色筛选
        char_label = QLabel("角色:")
        layout.addWidget(char_label)
        
        char_combo = QComboBox()
        char_combo.addItems(["全部", "Kasumi", "Tae", "Rimi", "Saaya", "Arisa"])
        char_combo.setObjectName("filterCombo")
        layout.addWidget(char_combo)
        
        # 添加乐队筛选
        band_label = QLabel("乐队:")
        layout.addWidget(band_label)
        
        band_combo = QComboBox()
        band_combo.addItems(["全部", "Poppin'Party", "Roselia", "Afterglow", "Pastel*Palettes", "Hello, Happy World!"])
        band_combo.setObjectName("filterCombo")
        layout.addWidget(band_combo)
        
        # 添加星级筛选
        star_label = QLabel("星级:")
        layout.addWidget(star_label)
        
        star_combo = QComboBox()
        star_combo.addItems(["全部", "1★", "2★", "3★", "4★", "5★"])
        star_combo.setObjectName("filterCombo")
        layout.addWidget(star_combo)
        
        # 添加乐器筛选
        instrument_label = QLabel("乐器:")
        layout.addWidget(instrument_label)
        
        instrument_combo = QComboBox()
        instrument_combo.addItems(["全部", "吉他", "贝斯", "鼓", "键盘", "主唱"])
        instrument_combo.setObjectName("filterCombo")
        layout.addWidget(instrument_combo)
        
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
        
        # 创建卡面预览卡片
        for i in range(12):  # 示例显示12张卡片
            card_frame = self.create_card_preview()
            layout.addWidget(card_frame, i // 4, i % 4)
        
        scroll.setWidget(content)
        return scroll
        
    def create_card_preview(self):
        """创建单个卡面预览卡片"""
        card_frame = QFrame()
        card_frame.setObjectName("cardPreviewFrame")
        card_frame.setFixedSize(250, 350)
        
        layout = QVBoxLayout(card_frame)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 卡面预览图
        preview_label = QLabel()
        preview_label.setFixedSize(230, 230)
        preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_label.setStyleSheet("background-color: #e0e0e0; border-radius: 5px;")
        preview_label.setText("预览图")
        layout.addWidget(preview_label)
        
        # 卡面名称
        name_label = QLabel("卡面名称")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(name_label)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        # 下载卡面按钮
        download_btn = QPushButton("下载卡面")
        download_btn.setObjectName("downloadBtn")
        button_layout.addWidget(download_btn)
        
        # 播放语音按钮
        play_btn = QPushButton("播放语音")
        play_btn.setObjectName("playBtn")
        button_layout.addWidget(play_btn)
        
        layout.addLayout(button_layout)
        
        return card_frame

    def reset(self):
        """重置页面状态"""
        # 清空所有内容
        self.setup_ui() 