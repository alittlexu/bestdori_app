import os
import random
from PyQt6.QtGui import QPixmap, QPainter, QColor
from PyQt6.QtCore import Qt

class BackgroundManager:
    def __init__(self):
        self.background_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'assets', 'backgrounds')
        self.backgrounds = []
        self.load_backgrounds()
        
    def load_backgrounds(self):
        """加载背景图片"""
        if not os.path.exists(self.background_path):
            os.makedirs(self.background_path)
            print(f"Created background directory: {self.background_path}")
            
        for file in os.listdir(self.background_path):
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                full_path = os.path.join(self.background_path, file)
                self.backgrounds.append(full_path)
                print(f"Loaded background: {full_path}")
                
    def get_random_background(self):
        """获取随机背景图片"""
        if not self.backgrounds:
            print("No background images found")
            return None
        return random.choice(self.backgrounds)
        
    def apply_background(self, widget):
        """将背景应用到窗口"""
        background_path = self.get_random_background()
        if background_path:
            pixmap = QPixmap(background_path)
            if not pixmap.isNull():
                # 缩放图片以适应窗口大小
                scaled_pixmap = pixmap.scaled(widget.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding)
                
                # 创建半透明效果
                result_pixmap = QPixmap(scaled_pixmap.size())
                result_pixmap.fill(Qt.GlobalColor.transparent)
                
                painter = QPainter(result_pixmap)
                painter.drawPixmap(0, 0, scaled_pixmap)
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn)
                painter.fillRect(result_pixmap.rect(), QColor(255, 255, 255, 230))  # 设置透明度为230
                painter.end()
                
                return result_pixmap
            else:
                print(f"Failed to load background image: {background_path}")
        return None 