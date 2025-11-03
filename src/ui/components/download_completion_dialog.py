"""
下载完成提示框组件 - 美化版本
使用粉色主题，优化信息显示和视觉效果
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class DownloadCompletionDialog(QDialog):
    """下载完成提示框 - 美化版本"""
    
    def __init__(self, parent=None, title="下载完成", content="", is_success=True):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(500, 400)
        
        # 设置窗口样式
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFFFF;
                border: 2px solid #E85D9E;
                border-radius: 12px;
            }
            QLabel {
                color: #333333;
                background-color: transparent;
            }
            QTextEdit {
                background-color: #F8F9FA;
                border: 1px solid #E1E6EF;
                border-radius: 8px;
                padding: 10px;
                color: #333333;
                font-size: 13px;
            }
            QPushButton {
                background-color: #E85D9E;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 10px 30px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #D1498F;
            }
            QPushButton:pressed {
                background-color: #B83D7A;
            }
        """)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(25, 25, 25, 25)
        
        # 标题区域
        title_layout = QHBoxLayout()
        title_layout.setSpacing(15)
        
        # 图标或标题文本
        if is_success:
            icon_label = QLabel("✓")
            icon_label.setStyleSheet("""
                QLabel {
                    color: #4CAF50;
                    font-size: 32px;
                    font-weight: bold;
                    background-color: transparent;
                }
            """)
            title_layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #E85D9E; background-color: transparent;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        main_layout.addLayout(title_layout)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: #E1E6EF; max-height: 1px;")
        main_layout.addWidget(line)
        
        # 内容区域
        content_text = QTextEdit()
        content_text.setReadOnly(True)
        content_text.setHtml(f'<div style="line-height: 1.8;">{content}</div>')
        content_text.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        main_layout.addWidget(content_text)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        ok_button = QPushButton("确定")
        ok_button.setFixedWidth(120)
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button)
        
        main_layout.addLayout(button_layout)
    
    @staticmethod
    def show_card_completion(parent, result):
        """显示卡面下载完成对话框"""
        if result.get('success'):
            total = result.get('total', 0)
            complete = result.get('complete', 0)
            normal_only = result.get('normal_only', 0)
            trained_only = result.get('trained_only', 0)
            failed = result.get('failed', 0)
            nonexistent_count = len(result.get('nonexistent', []))
            
            # 计算成功率
            success_count = complete + normal_only + trained_only
            success_rate = (success_count / total * 100) if total > 0 else 0
            
            content = f"""
            <div style="color: #333333;">
                <p style="font-size: 15px; font-weight: bold; color: #E85D9E; margin-bottom: 12px;">
                    📊 下载统计
                </p>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 15px;">
                    <tr>
                        <td style="padding: 8px 0; color: #666666;">总计卡片数：</td>
                        <td style="padding: 8px 0; font-weight: bold; color: #333333;">{total} 张</td>
                    </tr>
                    <tr style="background-color: #F0F8F4;">
                        <td style="padding: 8px 0; color: #4CAF50;">✓ 完整下载：</td>
                        <td style="padding: 8px 0; font-weight: bold; color: #4CAF50;">{complete} 张</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #666666;">✓ 仅Normal形态：</td>
                        <td style="padding: 8px 0; font-weight: bold; color: #333333;">{normal_only} 张</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #666666;">✓ 仅Trained形态：</td>
                        <td style="padding: 8px 0; font-weight: bold; color: #333333;">{trained_only} 张</td>
                    </tr>
                    <tr style="background-color: #FFF5F5;">
                        <td style="padding: 8px 0; color: #D32F2F;">✗ 下载失败：</td>
                        <td style="padding: 8px 0; font-weight: bold; color: #D32F2F;">{failed} 张</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #666666;">○ 不存在的卡片：</td>
                        <td style="padding: 8px 0; font-weight: bold; color: #666666;">{nonexistent_count} 张</td>
                    </tr>
                </table>
                <div style="margin-top: 15px; padding: 10px; background-color: #F8F9FA; border-radius: 6px; border-left: 4px solid #E85D9E;">
                    <p style="margin: 0; font-size: 14px; color: #666666;">
                        <strong>成功率：</strong><span style="color: #E85D9E; font-size: 16px; font-weight: bold;">{success_rate:.1f}%</span>
                    </p>
                </div>
            </div>
            """
            
            dialog = DownloadCompletionDialog(parent, "卡面下载完成", content, True)
            return dialog.exec()
        else:
            content = f"""
            <div style="color: #D32F2F; padding: 15px;">
                <p style="font-size: 15px; font-weight: bold; margin-bottom: 10px;">
                    ⚠️ 下载失败
                </p>
                <p style="font-size: 14px; line-height: 1.6;">
                    {result.get('message', '未知错误')}
                </p>
            </div>
            """
            dialog = DownloadCompletionDialog(parent, "下载失败", content, False)
            dialog.setStyleSheet("""
                QDialog {
                    background-color: #FFFFFF;
                    border: 2px solid #D32F2F;
                    border-radius: 12px;
                }
            """)
            return dialog.exec()
    
    @staticmethod
    def show_animation_completion(parent, result):
        """显示动态卡面下载完成对话框"""
        if result.get('success'):
            total = result.get('total', 0)
            downloaded = result.get('downloaded', 0)
            failed = result.get('failed', 0)
            nonexistent_count = len(result.get('nonexistent', []))
            
            # 计算成功率
            success_rate = (downloaded / total * 100) if total > 0 else 0
            
            content = f"""
            <div style="color: #333333;">
                <p style="font-size: 15px; font-weight: bold; color: #E85D9E; margin-bottom: 12px;">
                    📊 下载统计
                </p>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 15px;">
                    <tr>
                        <td style="padding: 8px 0; color: #666666;">总计视频数：</td>
                        <td style="padding: 8px 0; font-weight: bold; color: #333333;">{total} 个</td>
                    </tr>
                    <tr style="background-color: #F0F8F4;">
                        <td style="padding: 8px 0; color: #4CAF50;">✓ 成功下载：</td>
                        <td style="padding: 8px 0; font-weight: bold; color: #4CAF50;">{downloaded} 个</td>
                    </tr>
                    <tr style="background-color: #FFF5F5;">
                        <td style="padding: 8px 0; color: #D32F2F;">✗ 下载失败：</td>
                        <td style="padding: 8px 0; font-weight: bold; color: #D32F2F;">{failed} 个</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #666666;">○ 不存在的视频：</td>
                        <td style="padding: 8px 0; font-weight: bold; color: #666666;">{nonexistent_count} 个</td>
                    </tr>
                </table>
                <div style="margin-top: 15px; padding: 10px; background-color: #F8F9FA; border-radius: 6px; border-left: 4px solid #E85D9E;">
                    <p style="margin: 0; font-size: 14px; color: #666666;">
                        <strong>成功率：</strong><span style="color: #E85D9E; font-size: 16px; font-weight: bold;">{success_rate:.1f}%</span>
                    </p>
                </div>
            </div>
            """
            
            dialog = DownloadCompletionDialog(parent, "动态卡面下载完成", content, True)
            return dialog.exec()
        else:
            content = f"""
            <div style="color: #D32F2F; padding: 15px;">
                <p style="font-size: 15px; font-weight: bold; margin-bottom: 10px;">
                    ⚠️ 下载失败
                </p>
                <p style="font-size: 14px; line-height: 1.6;">
                    {result.get('message', '未知错误')}
                </p>
            </div>
            """
            dialog = DownloadCompletionDialog(parent, "下载失败", content, False)
            dialog.setStyleSheet("""
                QDialog {
                    background-color: #FFFFFF;
                    border: 2px solid #D32F2F;
                    border-radius: 12px;
                }
            """)
            return dialog.exec()
    
    @staticmethod
    def show_voice_completion(parent, result):
        """显示语音下载完成对话框"""
        if result.get('success'):
            stats = result.get('stats', {})
            downloaded = stats.get('downloaded', 0)
            failed = stats.get('failed', 0)
            skipped = stats.get('skipped', 0)
            characters = stats.get('characters', [])
            
            total_chars = len(characters)
            success_chars = total_chars - skipped
            
            content = f"""
            <div style="color: #333333;">
                <p style="font-size: 15px; font-weight: bold; color: #E85D9E; margin-bottom: 12px;">
                    📊 下载统计
                </p>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 15px;">
                    <tr>
                        <td style="padding: 8px 0; color: #666666;">处理角色数：</td>
                        <td style="padding: 8px 0; font-weight: bold; color: #333333;">{total_chars} 个</td>
                    </tr>
                    <tr style="background-color: #F0F8F4;">
                        <td style="padding: 8px 0; color: #4CAF50;">✓ 成功下载：</td>
                        <td style="padding: 8px 0; font-weight: bold; color: #4CAF50;">{downloaded} 个文件</td>
                    </tr>
                    <tr style="background-color: #FFF5F5;">
                        <td style="padding: 8px 0; color: #D32F2F;">✗ 下载失败：</td>
                        <td style="padding: 8px 0; font-weight: bold; color: #D32F2F;">{failed} 个文件</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #666666;">○ 跳过的角色：</td>
                        <td style="padding: 8px 0; font-weight: bold; color: #666666;">{skipped} 个</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #666666;">✓ 成功处理角色：</td>
                        <td style="padding: 8px 0; font-weight: bold; color: #333333;">{success_chars} 个</td>
                    </tr>
                </table>
                <div style="margin-top: 15px; padding: 10px; background-color: #F8F9FA; border-radius: 6px; border-left: 4px solid #E85D9E;">
                    <p style="margin: 0; font-size: 14px; color: #666666;">
                        <strong>角色处理率：</strong><span style="color: #E85D9E; font-size: 16px; font-weight: bold;">{(success_chars / total_chars * 100) if total_chars > 0 else 0:.1f}%</span>
                    </p>
                </div>
            </div>
            """
            
            dialog = DownloadCompletionDialog(parent, "语音下载完成", content, True)
            return dialog.exec()
        else:
            content = f"""
            <div style="color: #D32F2F; padding: 15px;">
                <p style="font-size: 15px; font-weight: bold; margin-bottom: 10px;">
                    ⚠️ 下载失败
                </p>
                <p style="font-size: 14px; line-height: 1.6;">
                    {result.get('message', '未知错误')}
                </p>
            </div>
            """
            dialog = DownloadCompletionDialog(parent, "下载失败", content, False)
            dialog.setStyleSheet("""
                QDialog {
                    background-color: #FFFFFF;
                    border: 2px solid #D32F2F;
                    border-radius: 12px;
                }
            """)
            return dialog.exec()

