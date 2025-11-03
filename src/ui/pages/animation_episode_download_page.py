from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                            QLabel, QComboBox, QPushButton, QScrollArea, QFrame,
                            QGridLayout, QSpinBox, QFileDialog, QMessageBox, QListWidget,
                            QListWidgetItem, QProgressBar, QMenu, QCheckBox, QToolButton,
                            QWidgetAction, QDialog)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPoint, QEvent
from PyQt6.QtGui import QAction, QPixmap, QMouseEvent
from src.utils.database import DatabaseManager
from src.core.animation_episode.animation_episode_downloader import AnimationEpisodeDownloader
from src.utils.config_manager import get_config_manager
from src.utils.path_utils import ensure_download_path
import os
import requests
import time
import logging
import json

# 使用说明文本
USAGE_TEXT = """
<h2>BanG Dream! 动态卡面视频下载工具使用说明</h2>

<h3>基本功能</h3>
<p>本工具可以帮助您下载BanG Dream!游戏中各角色的动态卡面视频资源(mp4格式)。</p>

<h3>使用步骤</h3>
<ol>
    <li><b>筛选角色</b>: 通过乐队、乐器和角色三个下拉菜单进行筛选。
        <ul>
            <li>您可以选择一个或多个乐队</li>
            <li>您可以选择一个或多个乐器类型</li>
            <li>您可以选择特定角色或使用"全部"选项</li>
        </ul>
    </li>
    <li><b>开始下载</b>: 点击"下载"按钮后，选择保存目录。
        <ul>
            <li>系统将自动创建乐队文件夹和角色文件夹</li>
            <li>例如：选择下载Poppin'Party的户山香澄，将创建"Poppin'Party/ksm/"目录结构</li>
        </ul>
    </li>
    <li><b>下载进度</b>: 下载过程中可以实时查看进度和状态。
        <ul>
            <li>进度条显示总体完成情况</li>
            <li>状态文本显示当前下载视频的ID和结果</li>
            <li>日志区域记录详细下载历史</li>
        </ul>
    </li>
    <li><b>下载结果</b>: 下载完成后会显示统计信息。
        <ul>
            <li>显示成功下载的视频数量</li>
            <li>显示失败或不存在的视频信息</li>
        </ul>
    </li>
    <li><b>其他功能</b>:
        <ul>
            <li>刷新按钮: 重置所有筛选条件，清空日志</li>
            <li>停止按钮: 中断当前下载任务</li>
        </ul>
    </li>
</ol>

<h3>注意事项</h3>
<ul>
    <li>下载速度取决于您的网络连接</li>
    <li>动态卡面视频文件较大，请耐心等待</li>
    <li>部分角色可能只有少量或没有动态卡面视频</li>
    <li>如需下载大量视频，建议分批进行</li>
</ul>
"""

# 关于文本
ABOUT_TEXT = """
<h2>BanG Dream! 动态卡面视频下载工具</h2>

<p><b>版本:</b> 2.1.1</p>

<p>本工具用于下载BanG Dream!游戏中的动态卡面视频资源(mp4格式)，支持按乐队、乐器和角色进行筛选，并自动创建对应的文件夹结构。</p>

<p><b>视频资源来源:</b> <a href="https://bestdori.com">Bestdori</a></p>

<h3>支持的功能:</h3>
<ul>
    <li>按乐队、乐器和角色筛选下载</li>
    <li>下载动态卡面视频文件(mp4格式)</li>
    <li>自动创建乐队/角色文件夹结构</li>
    <li>实时显示下载进度和状态</li>
    <li>详细的下载日志记录</li>
</ul>

<h3>技术特点:</h3>
<ul>
    <li>使用PyQt6开发的现代化界面</li>
    <li>多线程下载，保持UI响应性</li>
    <li>智能视频验证，确保下载文件质量</li>
    <li>自动重试机制，提高下载成功率</li>
</ul>

<h3>注意事项:</h3>
<ul>
    <li>本工具仅用于个人学习和欣赏，请勿用于商业用途</li>
    <li>下载的资源版权归BanG Dream!及Craft Egg/Bushiroad所有</li>
    <li>如遇下载失败，请检查网络连接或稍后再试</li>
</ul>

<p>© dx闹着玩的</p>
"""


def sanitize_filename(filename):
    """清理文件名中的非法字符（Windows文件系统）"""
    # Windows不允许的字符: < > : " / \ | ? * （包括全角和半角）
    invalid_chars = '<>:"/\\|?*'
    # 也替换全角字符
    fullwidth_chars = {
        '＜': '<',
        '＞': '>',
        '：': ':',
        '"': '"',
        '"': '"',
        '／': '/',
        '＼': '\\',
        '｜': '|',
        '？': '?',
        '＊': '*'  # 全角星号
    }
    # 先将全角字符转换为半角，然后再替换
    for full, half in fullwidth_chars.items():
        filename = filename.replace(full, half)
    # 替换半角非法字符
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    # 移除首尾空格和点
    filename = filename.strip(' .')
    # 限制文件名长度（Windows路径限制）
    if len(filename) > 255:
        filename = filename[:255]
    return filename


class DownloadThread(QThread):
    """下载线程"""
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    download_completed = pyqtSignal(dict)
    
    def __init__(self, characters, save_dir=None, character_id_mapping=None):
        super().__init__()
        self.characters = characters
        self.save_dir = save_dir
        self.character_id_mapping = character_id_mapping
        self.downloader = AnimationEpisodeDownloader(save_dir)
        
    def update_progress_callback(self, video_id, current, total, stats):
        """更新进度回调"""
        progress = int((current / max(total, 1)) * 100)
        self.progress_updated.emit(progress)
        
        # 创建当前视频的状态信息
        last_video_info = ""
        nonexistent_count = len(stats["nonexistent"])
        
        # 判断最后一次下载的视频结果
        if current > 0:
            if stats["downloaded"] > 0:
                # 下载成功
                last_video_info = f"动态卡面视频 {video_id} 下载成功"
            elif stats["failed"] > 0:
                # 下载失败
                last_video_info = f"动态卡面视频 {video_id} 下载失败"
        
        # 如果没有任何视频下载信息，显示不存在的视频信息
        if not last_video_info and nonexistent_count > 0:
            # 找到最后一个不存在的视频ID
            if stats["nonexistent"]:
                last_nonexistent_id = stats["nonexistent"][-1]
                last_video_info = f"动态卡面视频 {last_nonexistent_id} 不存在，已跳过"
        
        # 构建状态文本
        status_text = f"当前检查: 视频ID {video_id} | 已下载: {current}个 | 已跳过: {nonexistent_count}个 | 进度: {progress}%"
        if last_video_info:
            status_text += f" | {last_video_info}"
            
        self.status_updated.emit(status_text)
        
    def run(self):
        """执行下载"""
        try:
            total_videos_found = 0
            
            self.status_updated.emit("开始下载流程...")
            
            for char in self.characters:
                bestdori_id = self.character_id_mapping.get(char['id'])
                if not bestdori_id:
                    self.status_updated.emit(f"未找到角色 {char['id']} 的映射ID")
                    continue
                
                self.status_updated.emit(f"下载角色 {char['name']} 的动态卡面视频...")
                
                # 获取角色所属乐队信息
                band_name = None
                for band in [
                    {'id': 1, 'name': 'Poppin\'Party'},
                    {'id': 2, 'name': 'Afterglow'},
                    {'id': 3, 'name': 'Hello, Happy World!'},
                    {'id': 4, 'name': 'Pastel*Palettes'},
                    {'id': 5, 'name': 'Roselia'},
                    {'id': 6, 'name': 'Morfonica'},
                    {'id': 7, 'name': 'RAISE A SUILEN'},
                    {'id': 8, 'name': 'MyGO!!!!!'},
                    {'id': 9, 'name': 'その他'}
                ]:
                    if band['id'] == char['band_id']:
                        band_name = band['name']
                        break
                
                # 创建角色专属下载目录
                character_save_dir = self.save_dir
                if band_name:
                    # 清理乐队名称中的非法字符
                    sanitized_band_name = sanitize_filename(band_name)
                    # 创建乐队文件夹
                    band_dir = os.path.join(self.save_dir, sanitized_band_name)
                    os.makedirs(band_dir, exist_ok=True)
                    
                    # 创建角色文件夹
                    if 'nickname' in char and char['nickname']:
                        sanitized_nickname = sanitize_filename(char['nickname'])
                        character_save_dir = os.path.join(band_dir, sanitized_nickname)
                    else:
                        character_save_dir = os.path.join(band_dir, str(char['id']))
                    
                    os.makedirs(character_save_dir, exist_ok=True)
                    self.status_updated.emit(f"创建目录: {character_save_dir}")
                
                # 为当前角色创建专用的下载器实例，使用角色专属目录
                char_downloader = AnimationEpisodeDownloader(character_save_dir)
                
                # 下载该角色的所有动态卡面视频
                stats = char_downloader.download_character_videos(
                    bestdori_id,
                    bestdori_id + 999,
                    self.update_progress_callback
                )
                
                # 统计找到的视频数量
                total_videos_found += stats["downloaded"] + stats["failed"]
                
                # 合并统计信息
                self.downloader.stats["downloaded"] += stats["downloaded"]
                self.downloader.stats["failed"] += stats["failed"]
                self.downloader.stats["nonexistent"].extend(stats["nonexistent"])
            
            if total_videos_found == 0:
                self.download_completed.emit({
                    'success': False,
                    'message': '未找到符合条件的动态卡面视频',
                    'nonexistent': self.downloader.stats["nonexistent"]
                })
                return
            
            # 发送完成信号
            self.download_completed.emit({
                'success': True,
                'total': total_videos_found,
                'downloaded': self.downloader.stats["downloaded"],
                'failed': self.downloader.stats["failed"],
                'nonexistent': self.downloader.stats["nonexistent"]
            })
            
        except Exception as e:
            self.status_updated.emit(f"下载过程出错: {str(e)}")
            self.download_completed.emit({
                'success': False,
                'message': f'下载失败: {str(e)}'
            })

class MenuComboBox(QWidget):
    """自定义下拉菜单组件，使用QToolButton展示当前选择，点击后弹出菜单"""
    
    def __init__(self, placeholder="请选择...", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.button = QToolButton(self)
        self.button.setText(placeholder)
        # 修改为InstantPopup模式，使整个按钮区域可点击展开菜单
        self.button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.button.setStyleSheet("""
            QToolButton { 
                min-width: 150px; 
                text-align: left; 
                padding: 3px 20px 3px 3px; 
                border: 1px solid #aaa;
                border-radius: 3px;
                background-color: #f8f8f8;
            }
            QToolButton::menu-indicator { 
                subcontrol-origin: padding;
                subcontrol-position: center right;
                margin-right: 5px;
            }
            QToolButton:hover { 
                background-color: #e0e0e0;
                border-color: #999;
            }
        """)
        self.button.setSizePolicy(QComboBox().sizePolicy())
        layout.addWidget(self.button)
        
        # 创建自定义菜单类
        class NonClosingMenu(QMenu):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.setObjectName("FilterMenu")
                
            def keyPressEvent(self, event):
                """重写键盘事件，ESC键关闭菜单"""
                if event.key() == Qt.Key.Key_Escape:
                    self.hide()
                    return
                super().keyPressEvent(event)
        
        self._menu = NonClosingMenu(self)
        
        self._menu.setStyleSheet("""
            QMenu::item { 
                padding: 8px; 
                cursor: pointer;
            }
            QMenu::item:selected { 
                background-color: #e0e0e0; 
                cursor: pointer;
            }
            QMenu::item:hover {
                cursor: pointer;
            }
            QLabel {
                padding: 3px 0;
            }
            QLabel:hover {
                color: #4CAF50;
            }
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #aaa;
                border-radius: 3px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #4CAF50;
                border-color: #4CAF50;
                image: url(check.png);
            }
        """)
        
        # 创建一个确认按钮
        self.confirm_action = QAction("确认选择", self)
        self.confirm_action.triggered.connect(self._menu.hide)
        
        self._menu.triggered.connect(self._on_menu_item_triggered)
        
        self.button.setMenu(self._menu)
    
    def _on_menu_item_triggered(self, action):
        """处理菜单项触发"""
        pass
    
    def menu(self):
        """获取菜单对象"""
        return self.button.menu()
    
    def setCurrentText(self, text):
        """设置当前显示的文本"""
        self.button.setText(text)
        
    def currentText(self):
        """获取当前显示的文本"""
        return self.button.text()

class AnimationEpisodeDownloadPage(QWidget):
    """动态卡面视频下载页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseManager()
        self.config_manager = get_config_manager()
        self.init_data()
        self.init_character_mapping()
        self.init_ui()
        
    def init_data(self):
        """初始化数据"""
        # 预设乐队数据
        self.bands = [
            {'id': 1, 'name': 'Poppin\'Party'},
            {'id': 2, 'name': 'Afterglow'},
            {'id': 3, 'name': 'Hello, Happy World!'},
            {'id': 4, 'name': 'Pastel*Palettes'},
            {'id': 5, 'name': 'Roselia'},
            {'id': 6, 'name': 'Morfonica'},
            {'id': 7, 'name': 'RAISE A SUILEN'},
            {'id': 8, 'name': 'MyGO!!!!!'},
            {'id': 9, 'name': 'その他'}
        ]
        
        # 预设乐器数据
        self.instruments = [
            {'id': 1, 'name': '吉他'},
            {'id': 2, 'name': '贝斯'},
            {'id': 3, 'name': '鼓'},
            {'id': 4, 'name': '键盘'},
            {'id': 5, 'name': '主唱'},
            {'id': 6, 'name': 'DJ'},
            {'id': 7, 'name': '小提琴'}
        ]
        
        # 预设角色数据
        self.characters = [
            {'id': 1, 'name': '戸山香澄', 'band_id': 1, 'instrument_id': 1, 'nickname': 'ksm'},
            {'id': 2, 'name': '花園たえ', 'band_id': 1, 'instrument_id': 1, 'nickname': 'tae'},
            {'id': 3, 'name': '牛込りみ', 'band_id': 1, 'instrument_id': 2, 'nickname': 'rimi'},
            {'id': 4, 'name': '山吹沙綾', 'band_id': 1, 'instrument_id': 3, 'nickname': 'saya'},
            {'id': 5, 'name': '市ヶ谷有咲', 'band_id': 1, 'instrument_id': 4, 'nickname': 'arisa'},
            {'id': 6, 'name': '美竹蘭', 'band_id': 2, 'instrument_id': 1, 'nickname': 'ran'},
            {'id': 7, 'name': '青葉モカ', 'band_id': 2, 'instrument_id': 1, 'nickname': 'moca'},
            {'id': 8, 'name': '上原ひまり', 'band_id': 2, 'instrument_id': 4, 'nickname': 'himari'},
            {'id': 9, 'name': '宇田川巴', 'band_id': 2, 'instrument_id': 3, 'nickname': 'tomoe'},
            {'id': 10, 'name': '羽沢つぐみ', 'band_id': 2, 'instrument_id': 2, 'nickname': 'tsugu'},
            {'id': 11, 'name': '弦巻こころ', 'band_id': 3, 'instrument_id': 5, 'nickname': 'kokoro'},
            {'id': 12, 'name': '瀬田薫', 'band_id': 3, 'instrument_id': 3, 'nickname': 'kaoru'},
            {'id': 13, 'name': '北沢はぐみ', 'band_id': 3, 'instrument_id': 2, 'nickname': 'hagumi'},
            {'id': 14, 'name': '松原花音', 'band_id': 3, 'instrument_id': 4, 'nickname': 'kanon'},
            {'id': 15, 'name': '奥沢美咲', 'band_id': 3, 'instrument_id': 6, 'nickname': 'misaki'},
            {'id': 16, 'name': '丸山彩', 'band_id': 4, 'instrument_id': 5, 'nickname': 'aya'},
            {'id': 17, 'name': '氷川日菜', 'band_id': 4, 'instrument_id': 1, 'nickname': 'hina'},
            {'id': 18, 'name': '白鷺千聖', 'band_id': 4, 'instrument_id': 2, 'nickname': 'chisato'},
            {'id': 19, 'name': '大和麻弥', 'band_id': 4, 'instrument_id': 3, 'nickname': 'maya'},
            {'id': 20, 'name': '若宮イヴ', 'band_id': 4, 'instrument_id': 4, 'nickname': 'eve'},
            {'id': 21, 'name': '湊友希那', 'band_id': 5, 'instrument_id': 5, 'nickname': 'yukina'},
            {'id': 22, 'name': '氷川紗夜', 'band_id': 5, 'instrument_id': 1, 'nickname': 'sayo'},
            {'id': 23, 'name': '今井リサ', 'band_id': 5, 'instrument_id': 2, 'nickname': 'lisa'},
            {'id': 24, 'name': '宇田川あこ', 'band_id': 5, 'instrument_id': 3, 'nickname': 'ako'},
            {'id': 25, 'name': '白金燐子', 'band_id': 5, 'instrument_id': 4, 'nickname': 'rinko'},
            {'id': 26, 'name': '倉田ましろ', 'band_id': 6, 'instrument_id': 1, 'nickname': 'mashiro'},
            {'id': 27, 'name': '桐ケ谷透子', 'band_id': 6, 'instrument_id': 7, 'nickname': 'touko'},
            {'id': 28, 'name': '広町七深', 'band_id': 6, 'instrument_id': 2, 'nickname': 'nanami'},
            {'id': 29, 'name': '二葉つくし', 'band_id': 6, 'instrument_id': 3, 'nickname': 'tsukushi'},
            {'id': 30, 'name': '八潮瑠唯', 'band_id': 6, 'instrument_id': 5, 'nickname': 'rui'},
            {'id': 31, 'name': '和奏レイ', 'band_id': 7, 'instrument_id': 6, 'nickname': 'layer'},
            {'id': 32, 'name': '朝日六花', 'band_id': 7, 'instrument_id': 1, 'nickname': 'lock'},
            {'id': 33, 'name': '佐藤ますき', 'band_id': 7, 'instrument_id': 3, 'nickname': 'masking'},
            {'id': 34, 'name': '鳰原令王那', 'band_id': 7, 'instrument_id': 4, 'nickname': 'pareo'},
            {'id': 35, 'name': 'チュチュ', 'band_id': 7, 'instrument_id': 2, 'nickname': 'chu2'},
            {'id': 36, 'name': '高松燈', 'band_id': 8, 'instrument_id': 5, 'nickname': 'tomorin'},
            {'id': 37, 'name': '千早愛音', 'band_id': 8, 'instrument_id': 1, 'nickname': 'ano'},
            {'id': 38, 'name': '要楽奈', 'band_id': 8, 'instrument_id': 1, 'nickname': 'rana'},
            {'id': 39, 'name': '長崎そよ', 'band_id': 8, 'instrument_id': 2, 'nickname': 'soyo'},
            {'id': 40, 'name': '椎名立希', 'band_id': 8, 'instrument_id': 3, 'nickname': 'taki'}
        ]
        
    def init_character_mapping(self):
        """初始化角色ID映射"""
        # 根据视频ID规律，前三位是角色ID，这里映射数据库角色ID到Bestdori角色ID
        self.character_id_mapping = {
            1: 1000,    # 戸山香澄
            2: 2000,    # 花園たえ
            3: 3000,    # 牛込りみ
            4: 4000,    # 山吹沙綾
            5: 5000,    # 市ヶ谷有咲
            6: 6000,    # 美竹蘭
            7: 7000,    # 青葉モカ
            8: 8000,    # 上原ひまり
            9: 9000,    # 宇田川巴
            10: 10000,  # 羽沢つぐみ
            11: 11000,  # 弦巻こころ
            12: 12000,  # 瀬田薫
            13: 13000,  # 北沢はぐみ
            14: 14000,  # 松原花音
            15: 15000,  # 奥沢美咲
            16: 16000,  # 丸山彩
            17: 17000,  # 氷川日菜
            18: 18000,  # 白鷺千聖
            19: 19000,  # 大和麻弥
            20: 20000,  # 若宮イヴ
            21: 21000,  # 湊友希那
            22: 22000,  # 氷川紗夜
            23: 23000,  # 今井リサ
            24: 24000,  # 宇田川あこ
            25: 25000,  # 白金燐子
            26: 26000,  # 倉田ましろ
            27: 27000,  # 桐ケ谷透子
            28: 28000,  # 広町七深
            29: 29000,  # 二葉つくし
            30: 30000,  # 八潮瑠唯
            31: 31000,  # 和奏レイ
            32: 32000,  # 朝日六花
            33: 33000,  # 佐藤ますき
            34: 34000,  # 鳰原令王那
            35: 35000,  # チュチュ
            36: 36001,  # 高松燈
            37: 37001,  # 千早愛音
            38: 38001,  # 要楽奈
            39: 39001,  # 長崎そよ
            40: 40001   # 椎名立希
        }
        
    def init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # 路径设置区域容器
        path_container = QFrame()
        path_container.setFrameShape(QFrame.Shape.StyledPanel)
        path_container.setStyleSheet("background-color: #e8f5e9; border-radius: 5px; padding: 5px;")
        path_container.setContentsMargins(10, 10, 10, 10)
        main_layout.addWidget(path_container)
        
        path_layout = QHBoxLayout(path_container)
        path_layout.addWidget(QLabel("下载根路径:"))
        
        # 显示当前路径
        self.path_label = QLabel()
        self.update_path_label()
        self.path_label.setStyleSheet("color: #333; padding: 3px;")
        self.path_label.setWordWrap(True)
        path_layout.addWidget(self.path_label, 1)
        
        # 设置路径按钮
        self.set_path_button = QPushButton("设置路径")
        self.set_path_button.setStyleSheet("background-color: #2196F3; color: white; padding: 5px 15px; border-radius: 3px;")
        self.set_path_button.clicked.connect(self.on_set_path_clicked)
        path_layout.addWidget(self.set_path_button)
        
        # 筛选区域容器(带背景)
        filter_container = QFrame()
        filter_container.setFrameShape(QFrame.Shape.StyledPanel)
        filter_container.setStyleSheet("background-color: #f0f0f0; border-radius: 5px;")
        filter_container.setContentsMargins(10, 10, 10, 10)
        main_layout.addWidget(filter_container)
        
        # 筛选区域布局
        filter_layout = QHBoxLayout(filter_container)
        
        # 乐队选择
        band_layout = QVBoxLayout()
        filter_layout.addLayout(band_layout)
        band_layout.addWidget(QLabel("乐队:"))
        self.band_combo = MenuComboBox("请选择乐队...")
        band_layout.addWidget(self.band_combo)
        self.band_checkboxes = {}
        self.setup_band_menu()
        
        # 乐器选择
        instrument_layout = QVBoxLayout()
        filter_layout.addLayout(instrument_layout)
        instrument_layout.addWidget(QLabel("乐器:"))
        self.instrument_combo = MenuComboBox("请选择乐器...")
        instrument_layout.addWidget(self.instrument_combo)
        self.instrument_checkboxes = {}
        self.setup_instrument_menu()
        
        # 角色选择
        character_layout = QVBoxLayout()
        filter_layout.addLayout(character_layout)
        character_layout.addWidget(QLabel("角色:"))
        self.character_combo = MenuComboBox("请选择角色...")
        character_layout.addWidget(self.character_combo)
        self.character_checkboxes = {}
        self.update_character_menu()
        
        # 按钮区域
        button_layout = QVBoxLayout()
        filter_layout.addLayout(button_layout)
        button_layout.addWidget(QLabel(""))  # 占位符
        
        # 按钮容器
        button_container = QHBoxLayout()
        button_layout.addLayout(button_container)
        
        # 下载按钮
        self.download_button = QPushButton("下载")
        self.download_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px 15px; border-radius: 3px;")
        self.download_button.clicked.connect(self.on_filter_clicked)
        button_container.addWidget(self.download_button)
        
        # 刷新按钮
        self.refresh_button = QPushButton("刷新")
        self.refresh_button.setStyleSheet("background-color: #2196F3; color: white; padding: 5px 15px; border-radius: 3px;")
        self.refresh_button.clicked.connect(self.on_refresh_clicked)
        button_container.addWidget(self.refresh_button)
        
        # 停止按钮（初始隐藏）
        self.stop_button = QPushButton("停止")
        self.stop_button.setStyleSheet("background-color: #F44336; color: white; padding: 5px 15px; border-radius: 3px;")
        self.stop_button.clicked.connect(self.on_stop_clicked)
        self.stop_button.setVisible(False)
        button_container.addWidget(self.stop_button)
        
        # 添加分隔器
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(line)
        
        # 内容区域 - 分为上下两部分
        content_layout = QVBoxLayout()
        main_layout.addLayout(content_layout)
        
        # 上层区域 - 预留空间
        self.upper_area = QFrame()
        self.upper_area.setMinimumHeight(200)
        self.upper_area.setFrameShape(QFrame.Shape.StyledPanel)
        self.upper_area.setStyleSheet("background-color: rgba(255, 255, 255, 0.5); border-radius: 5px;")
        content_layout.addWidget(self.upper_area)
        
        # 添加分隔器
        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        line2.setFrameShadow(QFrame.Shadow.Sunken)
        content_layout.addWidget(line2)
        
        # 下层区域 - 显示下载信息
        download_info_group = QFrame()
        download_info_group.setFrameShape(QFrame.Shape.StyledPanel)
        download_info_group.setStyleSheet("background-color: rgba(249, 249, 249, 0.7); border-radius: 5px;")
        download_info_layout = QVBoxLayout(download_info_group)
        content_layout.addWidget(download_info_group)
        
        # 下载状态标题
        title_label = QLabel("下载状态")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        download_info_layout.addWidget(title_label)
        
        # 进度条
        progress_container = QHBoxLayout()
        download_info_layout.addLayout(progress_container)
        
        progress_container.addWidget(QLabel("下载进度:"))
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_container.addWidget(self.progress_bar)
        
        # 状态标签
        self.status_label = QLabel("")
        download_info_layout.addWidget(self.status_label)
        
        # 下载日志区域
        self.log_area = QScrollArea()
        self.log_area.setWidgetResizable(True)
        download_info_layout.addWidget(self.log_area)
        
        self.log_container = QWidget()
        self.log_layout = QVBoxLayout(self.log_container)
        self.log_area.setWidget(self.log_container)
    
    def setup_band_menu(self):
        """设置乐队下拉菜单"""
        class FilterMenu(QMenu):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.setObjectName("FilterMenu")
        
        menu = FilterMenu(self)
        menu.setStyleSheet("""
            QMenu { 
                background-color: white; 
                border: 1px solid #aaa; 
            }
            QMenu::item { 
                padding: 8px; 
            }
            QMenu::item:selected { 
                background-color: #e0e0e0; 
            }
            QLabel {
                padding: 3px 0;
                color: #333333;
            }
            QLabel:hover {
                color: #4CAF50;
            }
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #aaa;
                border-radius: 3px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #4CAF50;
                border-color: #4CAF50;
                image: url(check.png);
            }
        """)
        
        # 创建全部选项
        all_widget = QWidget(menu)
        all_layout = QHBoxLayout(all_widget)
        all_layout.setContentsMargins(8, 4, 8, 4)
        
        all_checkbox = QCheckBox(all_widget)
        all_checkbox.setChecked(True)
        all_layout.addWidget(all_checkbox)
        
        all_label = QLabel("全部", all_widget)
        all_label.setProperty("is_checked", True)
        all_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        all_label.setCursor(Qt.CursorShape.PointingHandCursor)
        
        def create_click_handler(cb):
            return lambda e: self.toggle_checkbox(cb)
            
        all_label.mousePressEvent = create_click_handler(all_checkbox)
        all_layout.addWidget(all_label)
        all_layout.addStretch()
        
        all_action = QWidgetAction(menu)
        all_action.setDefaultWidget(all_widget)
        menu.addAction(all_action)
        
        menu.addSeparator()
        
        # 存储复选框
        self.band_checkboxes = {-1: all_checkbox}
        self.band_actions = {-1: all_action}
        self.band_labels = {-1: all_label}
        
        all_checkbox.stateChanged.connect(lambda state: self.on_band_checkbox_changed(-1, state))
        
        # 添加每个乐队
        for band in self.bands:
            band_widget = QWidget(menu)
            band_layout = QHBoxLayout(band_widget)
            band_layout.setContentsMargins(8, 4, 8, 4)
            
            checkbox = QCheckBox(band_widget)
            band_layout.addWidget(checkbox)
            
            label = QLabel(band['name'], band_widget)
            label.setCursor(Qt.CursorShape.PointingHandCursor)
            label.setProperty("is_checked", False)
            label.setStyleSheet("color: #333333;")
            label.mousePressEvent = create_click_handler(checkbox)
            band_layout.addWidget(label)
            band_layout.addStretch()
            
            action = QWidgetAction(menu)
            action.setDefaultWidget(band_widget)
            menu.addAction(action)
            
            self.band_checkboxes[band['id']] = checkbox
            self.band_actions[band['id']] = action
            self.band_labels[band['id']] = label
            
            checkbox.stateChanged.connect(lambda state, b_id=band['id']: self.on_band_checkbox_changed(b_id, state))
        
        # 添加确认按钮
        menu.addSeparator()
        confirm_widget = QWidget(menu)
        confirm_layout = QHBoxLayout(confirm_widget)
        confirm_layout.setContentsMargins(8, 2, 8, 2)
        
        confirm_button = QPushButton("确认选择", confirm_widget)
        confirm_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; 
                color: white; 
                padding: 5px 15px; 
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        confirm_button.clicked.connect(menu.hide)
        confirm_layout.addWidget(confirm_button)
        
        confirm_action = QWidgetAction(menu)
        confirm_action.setDefaultWidget(confirm_widget)
        menu.addAction(confirm_action)
        
        self.band_combo.button.setMenu(menu)
        self.update_band_combo_text()
    
    def toggle_checkbox(self, checkbox):
        """切换复选框状态"""
        checkbox.setChecked(not checkbox.isChecked())
    
    def setup_instrument_menu(self):
        """设置乐器下拉菜单"""
        class FilterMenu(QMenu):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.setObjectName("FilterMenu")
        
        menu = FilterMenu(self)
        menu.setStyleSheet("""
            QMenu { 
                background-color: white; 
                border: 1px solid #aaa; 
            }
            QMenu::item { 
                padding: 8px; 
            }
            QMenu::item:selected { 
                background-color: #e0e0e0; 
            }
            QLabel {
                padding: 3px 0;
                color: #333333;
            }
            QLabel:hover {
                color: #4CAF50;
            }
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #aaa;
                border-radius: 3px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #4CAF50;
                border-color: #4CAF50;
                image: url(check.png);
            }
        """)
        
        # 创建全部选项
        all_widget = QWidget(menu)
        all_layout = QHBoxLayout(all_widget)
        all_layout.setContentsMargins(8, 4, 8, 4)
        
        all_checkbox = QCheckBox(all_widget)
        all_checkbox.setChecked(True)
        all_layout.addWidget(all_checkbox)
        
        all_label = QLabel("全部", all_widget)
        all_label.setCursor(Qt.CursorShape.PointingHandCursor)
        all_label.setProperty("is_checked", True)
        all_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        
        def create_click_handler(cb):
            return lambda e: self.toggle_checkbox(cb)
            
        all_label.mousePressEvent = create_click_handler(all_checkbox)
        all_layout.addWidget(all_label)
        all_layout.addStretch()
        
        all_action = QWidgetAction(menu)
        all_action.setDefaultWidget(all_widget)
        menu.addAction(all_action)
        
        menu.addSeparator()
        
        self.instrument_checkboxes = {-1: all_checkbox}
        self.instrument_actions = {-1: all_action}
        self.instrument_labels = {-1: all_label}
        
        all_checkbox.stateChanged.connect(lambda state: self.on_instrument_checkbox_changed(-1, state))
        
        # 添加每个乐器
        for instrument in self.instruments:
            instrument_widget = QWidget(menu)
            instrument_layout = QHBoxLayout(instrument_widget)
            instrument_layout.setContentsMargins(8, 4, 8, 4)
            
            checkbox = QCheckBox(instrument_widget)
            instrument_layout.addWidget(checkbox)
            
            label = QLabel(instrument['name'], instrument_widget)
            label.setCursor(Qt.CursorShape.PointingHandCursor)
            label.setProperty("is_checked", False)
            label.setStyleSheet("color: #333333;")
            label.mousePressEvent = create_click_handler(checkbox)
            instrument_layout.addWidget(label)
            instrument_layout.addStretch()
            
            action = QWidgetAction(menu)
            action.setDefaultWidget(instrument_widget)
            menu.addAction(action)
            
            self.instrument_checkboxes[instrument['id']] = checkbox
            self.instrument_actions[instrument['id']] = action
            self.instrument_labels[instrument['id']] = label
            
            checkbox.stateChanged.connect(lambda state, i_id=instrument['id']: self.on_instrument_checkbox_changed(i_id, state))
        
        # 添加确认按钮
        menu.addSeparator()
        confirm_widget = QWidget(menu)
        confirm_layout = QHBoxLayout(confirm_widget)
        confirm_layout.setContentsMargins(8, 2, 8, 2)
        
        confirm_button = QPushButton("确认选择", confirm_widget)
        confirm_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; 
                color: white; 
                padding: 5px 15px; 
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        confirm_button.clicked.connect(menu.hide)
        confirm_layout.addWidget(confirm_button)
        
        confirm_action = QWidgetAction(menu)
        confirm_action.setDefaultWidget(confirm_widget)
        menu.addAction(confirm_action)
        
        self.instrument_combo.button.setMenu(menu)
        self.update_instrument_combo_text()
    
    def update_character_menu(self):
        """更新角色下拉菜单"""
        band_ids = self.get_selected_band_ids()
        instrument_ids = self.get_selected_instrument_ids()
        characters = self.get_filtered_characters(band_ids, instrument_ids)
        
        class FilterMenu(QMenu):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.setObjectName("FilterMenu")
        
        menu = FilterMenu(self)
        menu.setStyleSheet("""
            QMenu { 
                background-color: white; 
                border: 1px solid #aaa; 
            }
            QMenu::item { 
                padding: 8px; 
            }
            QMenu::item:selected { 
                background-color: #e0e0e0; 
            }
            QLabel {
                padding: 3px 0;
                color: #333333;
            }
            QLabel:hover {
                color: #4CAF50;
            }
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #aaa;
                border-radius: 3px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #4CAF50;
                border-color: #4CAF50;
                image: url(check.png);
            }
        """)
        
        # 创建全部选项
        all_widget = QWidget(menu)
        all_layout = QHBoxLayout(all_widget)
        all_layout.setContentsMargins(8, 4, 8, 4)
        
        all_checkbox = QCheckBox(all_widget)
        all_checkbox.setChecked(True)
        all_layout.addWidget(all_checkbox)
        
        all_label = QLabel("全部", all_widget)
        all_label.setCursor(Qt.CursorShape.PointingHandCursor)
        all_label.setProperty("is_checked", True)
        all_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        
        def create_click_handler(cb):
            return lambda e: self.toggle_checkbox(cb)
        
        all_label.mousePressEvent = create_click_handler(all_checkbox)
        all_layout.addWidget(all_label)
        all_layout.addStretch()
        
        all_action = QWidgetAction(menu)
        all_action.setDefaultWidget(all_widget)
        menu.addAction(all_action)
        
        menu.addSeparator()
        
        self.character_checkboxes = {-1: all_checkbox}
        self.character_actions = {-1: all_action}
        self.character_labels = {-1: all_label}
        
        all_checkbox.stateChanged.connect(lambda state: self.on_character_checkbox_changed(-1, state))
        
        # 添加每个角色
        for character in characters:
            character_widget = QWidget(menu)
            character_layout = QHBoxLayout(character_widget)
            character_layout.setContentsMargins(8, 4, 8, 4)
            
            checkbox = QCheckBox(character_widget)
            character_layout.addWidget(checkbox)
            
            label = QLabel(character['name'], character_widget)
            label.setCursor(Qt.CursorShape.PointingHandCursor)
            label.setProperty("is_checked", False)
            label.setStyleSheet("color: #333333;")
            label.mousePressEvent = create_click_handler(checkbox)
            character_layout.addWidget(label)
            character_layout.addStretch()
            
            action = QWidgetAction(menu)
            action.setDefaultWidget(character_widget)
            menu.addAction(action)
            
            self.character_checkboxes[character['id']] = checkbox
            self.character_actions[character['id']] = action
            self.character_labels[character['id']] = label
            
            checkbox.stateChanged.connect(lambda state, c_id=character['id']: self.on_character_checkbox_changed(c_id, state))
        
        # 添加确认按钮
        menu.addSeparator()
        confirm_widget = QWidget(menu)
        confirm_layout = QHBoxLayout(confirm_widget)
        confirm_layout.setContentsMargins(8, 2, 8, 2)
        
        confirm_button = QPushButton("确认选择", confirm_widget)
        confirm_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; 
                color: white; 
                padding: 5px 15px; 
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        confirm_button.clicked.connect(menu.hide)
        confirm_layout.addWidget(confirm_button)
        
        confirm_action = QWidgetAction(menu)
        confirm_action.setDefaultWidget(confirm_widget)
        menu.addAction(confirm_action)
        
        self.character_combo.button.setMenu(menu)
        self.update_character_combo_text()
    
    def on_band_checkbox_changed(self, band_id, state):
        """乐队复选框改变处理"""
        if band_id == -1:  # "全部"选项
            if state == Qt.CheckState.Checked:
                for id, checkbox in self.band_checkboxes.items():
                    if id != -1:
                        checkbox.setChecked(False)
                        self.band_labels[id].setProperty("is_checked", False)
                        self.band_labels[id].setStyleSheet("color: #333333;")
                
                self.band_labels[-1].setProperty("is_checked", True)
                self.band_labels[-1].setStyleSheet("color: #4CAF50; font-weight: bold;")
        else:  # 其他选项
            any_specific_checked = False
            for id, checkbox in self.band_checkboxes.items():
                if id != -1 and checkbox.isChecked():
                    any_specific_checked = True
                    break
            
            if any_specific_checked:
                self.band_checkboxes[-1].setChecked(False)
                self.band_labels[-1].setProperty("is_checked", False)
                self.band_labels[-1].setStyleSheet("color: #333333;")
            else:
                self.band_checkboxes[-1].setChecked(True)
                self.band_labels[-1].setProperty("is_checked", True)
                self.band_labels[-1].setStyleSheet("color: #4CAF50; font-weight: bold;")
            
            if state == Qt.CheckState.Checked:
                self.band_labels[band_id].setProperty("is_checked", True)
                self.band_labels[band_id].setStyleSheet("color: #4CAF50; font-weight: bold;")
            else:
                self.band_labels[band_id].setProperty("is_checked", False)
                self.band_labels[band_id].setStyleSheet("color: #333333;")
        
        self.update_band_combo_text()
        self.update_character_menu()
    
    def on_instrument_checkbox_changed(self, instrument_id, state):
        """乐器复选框改变处理"""
        if instrument_id == -1:  # "全部"选项
            if state == Qt.CheckState.Checked:
                for id, checkbox in self.instrument_checkboxes.items():
                    if id != -1:
                        checkbox.setChecked(False)
                        self.instrument_labels[id].setProperty("is_checked", False)
                        self.instrument_labels[id].setStyleSheet("color: #333333;")
                
                self.instrument_labels[-1].setProperty("is_checked", True)
                self.instrument_labels[-1].setStyleSheet("color: #4CAF50; font-weight: bold;")
        else:  # 其他选项
            any_specific_checked = False
            for id, checkbox in self.instrument_checkboxes.items():
                if id != -1 and checkbox.isChecked():
                    any_specific_checked = True
                    break
            
            if any_specific_checked:
                self.instrument_checkboxes[-1].setChecked(False)
                self.instrument_labels[-1].setProperty("is_checked", False)
                self.instrument_labels[-1].setStyleSheet("color: #333333;")
            else:
                self.instrument_checkboxes[-1].setChecked(True)
                self.instrument_labels[-1].setProperty("is_checked", True)
                self.instrument_labels[-1].setStyleSheet("color: #4CAF50; font-weight: bold;")
            
            if state == Qt.CheckState.Checked:
                self.instrument_labels[instrument_id].setProperty("is_checked", True)
                self.instrument_labels[instrument_id].setStyleSheet("color: #4CAF50; font-weight: bold;")
            else:
                self.instrument_labels[instrument_id].setProperty("is_checked", False)
                self.instrument_labels[instrument_id].setStyleSheet("color: #333333;")
        
        self.update_instrument_combo_text()
        self.update_character_menu()
    
    def on_character_checkbox_changed(self, character_id, state):
        """角色复选框改变处理"""
        if character_id == -1:  # "全部"选项
            if state == Qt.CheckState.Checked:
                for id, checkbox in self.character_checkboxes.items():
                    if id != -1:
                        checkbox.setChecked(False)
                        self.character_labels[id].setProperty("is_checked", False)
                        self.character_labels[id].setStyleSheet("color: #333333;")
                
                self.character_labels[-1].setProperty("is_checked", True)
                self.character_labels[-1].setStyleSheet("color: #4CAF50; font-weight: bold;")
        else:  # 其他选项
            any_specific_checked = False
            for id, checkbox in self.character_checkboxes.items():
                if id != -1 and checkbox.isChecked():
                    any_specific_checked = True
                    break
            
            if any_specific_checked:
                self.character_checkboxes[-1].setChecked(False)
                self.character_labels[-1].setProperty("is_checked", False)
                self.character_labels[-1].setStyleSheet("color: #333333;")
            else:
                self.character_checkboxes[-1].setChecked(True)
                self.character_labels[-1].setProperty("is_checked", True)
                self.character_labels[-1].setStyleSheet("color: #4CAF50; font-weight: bold;")
            
            if state == Qt.CheckState.Checked:
                self.character_labels[character_id].setProperty("is_checked", True)
                self.character_labels[character_id].setStyleSheet("color: #4CAF50; font-weight: bold;")
            else:
                self.character_labels[character_id].setProperty("is_checked", False)
                self.character_labels[character_id].setStyleSheet("color: #333333;")
        
        self.update_character_combo_text()
    
    def update_band_combo_text(self):
        """更新乐队下拉框文本"""
        selected_bands = []
        for id, checkbox in self.band_checkboxes.items():
            if id != -1 and checkbox.isChecked():
                band_name = next((band['name'] for band in self.bands if band['id'] == id), None)
                if band_name:
                    selected_bands.append(band_name)
        
        if self.band_checkboxes[-1].isChecked() or not selected_bands:
            self.band_combo.setCurrentText("全部乐队")
        elif len(selected_bands) <= 2:
            self.band_combo.setCurrentText(", ".join(selected_bands))
        else:
            self.band_combo.setCurrentText(f"已选择 {len(selected_bands)} 个乐队")
    
    def update_instrument_combo_text(self):
        """更新乐器下拉框文本"""
        selected_instruments = []
        for id, checkbox in self.instrument_checkboxes.items():
            if id != -1 and checkbox.isChecked():
                instrument_name = next((instrument['name'] for instrument in self.instruments if instrument['id'] == id), None)
                if instrument_name:
                    selected_instruments.append(instrument_name)
        
        if self.instrument_checkboxes[-1].isChecked() or not selected_instruments:
            self.instrument_combo.setCurrentText("全部乐器")
        elif len(selected_instruments) <= 2:
            self.instrument_combo.setCurrentText(", ".join(selected_instruments))
        else:
            self.instrument_combo.setCurrentText(f"已选择 {len(selected_instruments)} 个乐器")
    
    def update_character_combo_text(self):
        """更新角色下拉框文本"""
        selected_characters = []
        for id, checkbox in self.character_checkboxes.items():
            if id != -1 and checkbox.isChecked():
                character_name = next((character['name'] for character in self.characters if character['id'] == id), None)
                if character_name:
                    selected_characters.append(character_name)
        
        if self.character_checkboxes[-1].isChecked() or not selected_characters:
            self.character_combo.setCurrentText("全部角色")
        elif len(selected_characters) <= 2:
            self.character_combo.setCurrentText(", ".join(selected_characters))
        else:
            self.character_combo.setCurrentText(f"已选择 {len(selected_characters)} 个角色")
    
    def on_refresh_clicked(self):
        """处理刷新按钮点击事件"""
        self.on_stop_clicked()
        
        # 重置所有复选框
        for id, checkbox in self.band_checkboxes.items():
            checkbox.setChecked(id == -1)
            
        for id, checkbox in self.instrument_checkboxes.items():
            checkbox.setChecked(id == -1)
            
        self.update_character_menu()
        
        self.update_band_combo_text()
        self.update_instrument_combo_text()
        self.update_character_combo_text()
        
        # 清空日志
        while self.log_layout.count():
            item = self.log_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.progress_bar.setVisible(False)
        self.status_label.setText("")
        
        self.download_button.setEnabled(True)
        self.stop_button.setVisible(False)
        
        self.add_log_entry("界面已重置", True)
    
    def on_stop_clicked(self):
        """处理停止按钮点击事件"""
        if hasattr(self, 'download_thread') and self.download_thread.isRunning():
            self.download_thread.terminate()
            self.download_thread.wait()
            
            self.download_button.setEnabled(True)
            self.stop_button.setVisible(False)
            self.progress_bar.setVisible(False)
            
            self.add_log_entry("下载已停止", False)
            QMessageBox.information(self, "下载停止", "下载任务已终止")
            
    def on_filter_clicked(self):
        """处理筛选按钮点击事件"""
        try:
            # 清空日志
            while self.log_layout.count():
                item = self.log_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            # 获取选中的角色列表
            characters = self.get_selected_characters()
            if not characters:
                QMessageBox.warning(self, "警告", "请至少选择一个角色")
                return
            
            self.add_log_entry("===== 开始下载 =====")
            self.add_log_entry(f"选择下载: {len(characters)}个角色")
            for char in characters:
                self.add_log_entry(f"- {char['name']}")
            
            # 检查是否设置了下载根路径
            try:
                # 使用新的路径结构：<root>/Bestdori/animation/
                save_dir = ensure_download_path('animation')
                self.add_log_entry(f"保存目录: {save_dir}")
            except ValueError as e:
                QMessageBox.warning(self, "路径未设置", f"{str(e)}\n\n请先点击\"设置路径\"按钮设置下载根路径。")
                return
            except Exception as e:
                QMessageBox.critical(self, "路径错误", f"创建下载目录失败: {str(e)}")
                return
            
            # 创建并启动下载线程
            self.download_thread = DownloadThread(
                characters=characters,
                save_dir=save_dir,
                character_id_mapping=self.character_id_mapping
            )
            
            # 连接信号
            self.download_thread.progress_updated.connect(self.update_progress)
            self.download_thread.status_updated.connect(self.update_status)
            self.download_thread.download_completed.connect(self.on_download_completed)
            
            # 禁用下载按钮，显示停止按钮
            self.download_button.setEnabled(False)
            self.stop_button.setVisible(True)
            
            # 启动下载线程
            self.progress_bar.setValue(0)
            self.progress_bar.setVisible(True)
            self.add_log_entry("启动下载线程...")
            self.download_thread.start()
            
        except Exception as e:
            error_msg = f"下载失败: {str(e)}"
            self.add_log_entry(error_msg, False)
            QMessageBox.critical(self, "错误", error_msg)
            self.download_button.setEnabled(True)
            self.stop_button.setVisible(False)
    
    def update_progress(self, value):
        """更新进度条"""
        self.progress_bar.setValue(value)
    
    def update_status(self, text):
        """更新状态文本"""
        self.status_label.setText(text)
        self.add_log_entry(text)
    
    def add_log_entry(self, text, success=None):
        """添加下载日志条目"""
        log_entry = QLabel(text)
        if success is not None:
            if success:
                log_entry.setStyleSheet("color: green;")
            else:
                log_entry.setStyleSheet("color: red;")
        
        self.log_layout.insertWidget(0, log_entry)
        self.log_area.verticalScrollBar().setValue(0)
    
    def on_download_completed(self, result):
        """下载完成处理"""
        self.progress_bar.setVisible(False)
        self.download_button.setEnabled(True)
        self.stop_button.setVisible(False)
        
        if result['success']:
            nonexistent_count = len(result.get('nonexistent', []))
            summary = (
                f"下载完成！\n"
                f"总数：{result['total']}个\n"
                f"成功下载：{result['downloaded']}个\n"
                f"下载失败：{result['failed']}个\n"
                f"不存在的视频：{nonexistent_count}个"
            )
            self.add_log_entry("===== 下载完成 =====", True)
            self.add_log_entry(summary, True)
            
            if nonexistent_count > 0:
                nonexistent_ids = result.get('nonexistent', [])
                display_ids = nonexistent_ids[:20]
                id_str = ", ".join(str(id) for id in display_ids)
                if nonexistent_count > 20:
                    id_str += f"... 等共{nonexistent_count}个ID"
                self.add_log_entry(f"不存在的视频ID: {id_str}", False)
            
            QMessageBox.information(
                self,
                "下载完成",
                summary
            )
        else:
            self.add_log_entry(f"===== 下载失败: {result['message']} =====", False)
            QMessageBox.warning(
                self,
                "下载失败",
                result['message']
            )

    def show_usage_guide(self):
        """显示使用说明"""
        from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QSizePolicy, QPushButton
        from PyQt6.QtGui import QPixmap
        from PyQt6.QtCore import Qt
        import os
        
        dialog = QDialog(self)
        dialog.setWindowTitle("使用说明")
        dialog.setMinimumSize(800, 600)
        dialog.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLabel {
                color: #333333;
            }
            QScrollArea {
                border: none;
                background-color: white;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        main_layout = QHBoxLayout(dialog)
        
        left_layout = QVBoxLayout()
        
        image_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'assets', 'images', 'bestdori.jpg')
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            image_label = QLabel()
            pixmap = pixmap.scaledToWidth(240, Qt.TransformationMode.SmoothTransformation)
            image_label.setPixmap(pixmap)
            image_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
            left_layout.addWidget(image_label)
            left_layout.addStretch()
        
        right_layout = QVBoxLayout()
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        
        text_label = QLabel(USAGE_TEXT)
        text_label.setWordWrap(True)
        text_label.setTextFormat(Qt.TextFormat.RichText)
        text_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        content_layout.addWidget(text_label)
        
        scroll_area.setWidget(content_container)
        right_layout.addWidget(scroll_area)
        
        button_layout = QHBoxLayout()
        ok_button = QPushButton("确认")
        ok_button.clicked.connect(dialog.accept)
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        right_layout.addLayout(button_layout)
        
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 3)
        
        dialog.exec()
    
    def show_about(self):
        """显示关于信息"""
        from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QSizePolicy, QPushButton
        from PyQt6.QtGui import QPixmap
        from PyQt6.QtCore import Qt
        import os
        
        dialog = QDialog(self)
        dialog.setWindowTitle("关于")
        dialog.setMinimumSize(800, 600)
        dialog.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLabel {
                color: #333333;
            }
            QScrollArea {
                border: none;
                background-color: white;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        main_layout = QHBoxLayout(dialog)
        
        left_layout = QVBoxLayout()
        
        image_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'assets', 'images', 'bestdori.jpg')
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            image_label = QLabel()
            pixmap = pixmap.scaledToWidth(240, Qt.TransformationMode.SmoothTransformation)
            image_label.setPixmap(pixmap)
            image_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
            left_layout.addWidget(image_label)
            left_layout.addStretch()
        
        right_layout = QVBoxLayout()
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        
        text_label = QLabel(ABOUT_TEXT)
        text_label.setWordWrap(True)
        text_label.setTextFormat(Qt.TextFormat.RichText)
        text_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        content_layout.addWidget(text_label)
        
        scroll_area.setWidget(content_container)
        right_layout.addWidget(scroll_area)
        
        button_layout = QHBoxLayout()
        ok_button = QPushButton("确认")
        ok_button.clicked.connect(dialog.accept)
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        right_layout.addLayout(button_layout)
        
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 3)
        
        dialog.exec()

    def get_selected_band_ids(self):
        """获取选中的乐队ID列表"""
        selected_ids = []
        for id, checkbox in self.band_checkboxes.items():
            if id != -1 and checkbox.isChecked():
                selected_ids.append(id)
        
        if not selected_ids or self.band_checkboxes[-1].isChecked():
            return [-1]
            
        return selected_ids
    
    def get_selected_instrument_ids(self):
        """获取选中的乐器ID列表"""
        selected_ids = []
        for id, checkbox in self.instrument_checkboxes.items():
            if id != -1 and checkbox.isChecked():
                selected_ids.append(id)
        
        if not selected_ids or self.instrument_checkboxes[-1].isChecked():
            return [-1]
            
        return selected_ids
    
    def get_selected_character_ids(self):
        """获取选中的角色ID列表"""
        selected_ids = []
        for id, checkbox in self.character_checkboxes.items():
            if id != -1 and checkbox.isChecked():
                selected_ids.append(id)
        
        if not selected_ids or self.character_checkboxes[-1].isChecked():
            return [-1]
            
        return selected_ids
    
    def get_filtered_characters(self, band_ids, instrument_ids):
        """获取符合筛选条件的角色列表"""
        filtered_characters = []
        
        use_all_bands = -1 in band_ids
        use_all_instruments = -1 in instrument_ids
        
        if not use_all_bands and not use_all_instruments:
            filtered_characters = [char for char in self.characters if char['band_id'] in band_ids and char['instrument_id'] in instrument_ids]
        elif not use_all_bands:
            filtered_characters = [char for char in self.characters if char['band_id'] in band_ids]
        elif not use_all_instruments:
            filtered_characters = [char for char in self.characters if char['instrument_id'] in instrument_ids]
        else:
            filtered_characters = self.characters.copy()
                
        return filtered_characters
    
    def get_selected_characters(self):
        """获取选中的角色列表"""
        character_ids = self.get_selected_character_ids()
        band_ids = self.get_selected_band_ids()
        instrument_ids = self.get_selected_instrument_ids()
        
        if character_ids == [-1]:
            return self.get_filtered_characters(band_ids, instrument_ids)
        
        result = []
        for char_id in character_ids:
            char = self.get_character_by_id(char_id)
            if char:
                result.append(char)
        
        return result
    
    def get_character_by_id(self, character_id):
        """根据ID获取角色"""
        for char in self.characters:
            if char['id'] == character_id:
                return char
        return None
    
    def update_path_label(self):
        """更新路径显示标签"""
        root_path = self.config_manager.get_download_root_path()
        if root_path:
            self.path_label.setText(f"{root_path}/Bestdori/animation/")
            self.path_label.setToolTip(f"根路径: {root_path}")
        else:
            self.path_label.setText("未设置（点击\"设置路径\"按钮设置）")
            self.path_label.setToolTip("请设置下载根路径")
    
    def on_set_path_clicked(self):
        """处理设置路径按钮点击事件"""
        # 获取当前路径作为默认路径
        current_path = self.config_manager.get_download_root_path()
        if not current_path:
            current_path = os.path.expanduser("~")
        
        # 选择目录
        selected_path = QFileDialog.getExistingDirectory(
            self,
            "选择下载根路径",
            current_path,
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
        )
        
        if selected_path:
            # 保存路径到配置
            if self.config_manager.set_download_root_path(selected_path):
                self.update_path_label()
                QMessageBox.information(self, "设置成功", f"下载根路径已设置为：\n{selected_path}\n\n下载文件将保存在：\n{selected_path}/Bestdori/")
            else:
                QMessageBox.warning(self, "设置失败", "保存路径配置失败，请重试")

