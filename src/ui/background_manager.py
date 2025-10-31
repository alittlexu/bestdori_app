import os
import random
from PyQt6.QtGui import QPixmap, QPainter, QColor
from PyQt6.QtCore import Qt

class BackgroundManager:
    """背景管理器，负责处理应用的背景图片"""
    
    def __init__(self):
        """初始化背景管理器"""
        # 设置背景图片目录路径
        self.background_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'assets', 'backgrounds')
        self.backgrounds = []
        self.current_background = None  # 添加当前背景缓存
        self.load_backgrounds()
        
    def load_backgrounds(self):
        """加载背景图片列表"""
        if not os.path.exists(self.background_path):
            os.makedirs(self.background_path)
            print(f"Created background directory: {self.background_path}")
            
        for file in os.listdir(self.background_path):
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                full_path = os.path.join(self.background_path, file)
                self.backgrounds.append(full_path)
                print(f"Loaded background: {full_path}")
                
    def get_random_background(self):
        """获取随机背景图片，如果有缓存的背景则返回缓存的背景"""
        # 如果有缓存的背景，则返回缓存的背景
        if hasattr(self, 'current_background') and self.current_background:
            return self.current_background
            
        # 否则随机选择一个新背景
        if not self.backgrounds:
            print("No background images found")
            return None
            
        background = random.choice(self.backgrounds)
        self.current_background = background
        return background
        
    def apply_background(self, widget):
        """将背景应用到窗口，优化缩放以适应不同窗口大小"""
        background_path = self.get_random_background()
        if background_path:
            pixmap = QPixmap(background_path)
            if not pixmap.isNull():
                # 获取窗口大小
                widget_size = widget.size()
                # 若窗口尚未建立有效尺寸，跳过本次绘制
                if widget_size.width() <= 0 or widget_size.height() <= 0:
                    return None
                
                # 对于非常小的窗口，使用更强的缩放算法
                if widget_size.width() < 800 or widget_size.height() < 600:
                    # 缩放图片以适应窗口大小，确保覆盖整个窗口
                    scaled_pixmap = pixmap.scaled(
                        max(widget_size.width(), 800), 
                        max(widget_size.height(), 600),
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                        Qt.TransformationMode.SmoothTransformation
                    )
                else:
                    # 对于较大窗口使用标准缩放
                    scaled_pixmap = pixmap.scaled(
                        widget_size, 
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                        Qt.TransformationMode.SmoothTransformation
                    )
                
                # 如果缩放后的图片大于窗口，从中心裁剪
                if scaled_pixmap.width() > widget_size.width() or scaled_pixmap.height() > widget_size.height():
                    x = max(0, (scaled_pixmap.width() - widget_size.width()) // 2)
                    y = max(0, (scaled_pixmap.height() - widget_size.height()) // 2)
                    scaled_pixmap = scaled_pixmap.copy(
                        x, y, 
                        min(scaled_pixmap.width(), widget_size.width()),
                        min(scaled_pixmap.height(), widget_size.height())
                    )
                
                # 创建半透明效果，调整小窗口时使用不同的透明度
                result_pixmap = QPixmap(widget_size)
                result_pixmap.fill(Qt.GlobalColor.transparent)
                
                painter = QPainter(result_pixmap)
                # 确保图像质量
                painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                
                # 绘制背景
                painter.drawPixmap(0, 0, scaled_pixmap)
                
                # 应用半透明叠加层，小窗口时增加透明度
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn)
                # 根据窗口大小调整透明度
                alpha = min(230, 180 + (widget_size.width() / 1200) * 50)
                painter.fillRect(result_pixmap.rect(), QColor(255, 255, 255, int(alpha)))
                painter.end()
                
                return result_pixmap
            else:
                print(f"Failed to load background image: {background_path}")
        return None
        
    def reset_background(self):
        """重置背景缓存，下次将选择新的随机背景"""
        self.current_background = None
        
    def set_specific_background(self, background_path):
        """设置特定的背景图片"""
        if os.path.exists(background_path):
            self.current_background = background_path
            return True
        return False 