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
<h2>BanG Dream! 动态卡面视频下载工具 - 使用说明</h2>

<h3>📖 基本功能</h3>
<p>本工具可以帮助您从 Bestdori 网站下载 BanG Dream! 游戏中各角色的动态卡面视频资源（MP4格式）。动态卡面是游戏中角色卡面的动画版本，通常包含精美的特效和动画效果。</p>

<h3>🚀 快速开始</h3>
<ol>
    <li><b>设置下载路径</b>: 首次使用前，请点击"设置路径"按钮选择您希望保存视频的根目录。
        <ul>
            <li>下载的文件将保存在：<code>&lt;您设置的路径&gt;/Bestdori/animation/</code> 目录下</li>
            <li>系统会自动创建乐队和角色子文件夹，例如：<code>Bestdori/animation/Poppin_Party/ksm/</code></li>
            <li>路径设置只需一次，之后会自动保存</li>
        </ul>
    </li>
    <li><b>筛选角色</b>: 使用三个下拉菜单进行精确筛选。
        <ul>
            <li><b>乐队筛选</b>: 选择要下载的乐队（如 Poppin'Party、Roselia 等）</li>
            <li><b>乐器筛选</b>: 选择乐器类型（吉他、贝斯、鼓、键盘、主唱、DJ、小提琴）</li>
            <li><b>角色筛选</b>: 选择具体的角色（支持多选，或选择"全部"）</li>
            <li>所有筛选条件支持多选，通过勾选复选框实现</li>
            <li>筛选菜单支持批量选择：点击选项后菜单保持打开，可连续选择多个选项</li>
            <li>只有点击菜单外部区域或"确认选择"按钮时菜单才会关闭</li>
            <li>鼠标悬停时显示手指针，提示可点击交互</li>
            <li>筛选后点击菜单底部的"确认选择"按钮生效</li>
        </ul>
    </li>
    <li><b>开始下载</b>: 设置好筛选条件后，点击粉色的"下载"按钮开始下载。
        <ul>
            <li>系统会自动检查每个视频是否存在（通过文件大小验证）</li>
            <li>如果某个角色从开头连续3次查找都失败，系统会判定该角色没有动态卡面，自动跳过</li>
            <li>已找到视频后，如果连续3次查找失败，判定该角色下载完成</li>
        </ul>
    </li>
    <li><b>监控下载进度</b>: 下载过程中可以实时查看：
        <ul>
            <li><b>进度条</b>: 显示整体下载完成百分比</li>
            <li><b>状态文本</b>: 显示当前处理的视频ID、已下载数量等</li>
            <li><b>日志区域</b>: 记录每个视频的详细下载结果</li>
            <li>如需中断下载，点击红色的"停止"按钮</li>
        </ul>
    </li>
    <li><b>查看下载结果</b>: 下载完成后会弹出统计对话框：
        <ul>
            <li>成功下载的视频数量</li>
            <li>下载失败的视频信息</li>
            <li>不存在的视频ID列表</li>
        </ul>
    </li>
</ol>

<h3>🔧 功能按钮说明</h3>
<ul>
    <li><b>下载</b>（粉色）: 开始下载选中的角色动态卡面视频</li>
    <li><b>刷新</b>（浅粉色）: 重置所有筛选条件，清空日志和状态</li>
    <li><b>停止</b>（深粉红）: 中断当前正在进行的下载任务</li>
    <li><b>设置路径</b>（浅粉色）: 设置或修改下载文件的保存根目录</li>
</ul>

<h3>💡 使用技巧</h3>
<ul>
    <li><b>批量下载</b>: 可以选择多个乐队、多个角色同时下载，系统会自动按文件夹分类保存</li>
    <li><b>精确筛选</b>: 结合乐队、乐器、角色三个条件可以精确定位到某个特定角色</li>
    <li><b>批量筛选</b>: 筛选菜单支持批量选择，点击选项后菜单不会关闭，可连续勾选多个选项，提高筛选效率</li>
    <li><b>交互提示</b>: 鼠标悬停在可选项上会显示手指针，清晰提示可点击区域</li>
    <li><b>智能跳过</b>: 系统会自动识别没有动态卡面的角色，避免无效查找</li>
    <li><b>文件夹结构</b>: 所有视频按照 <code>乐队名/角色昵称/</code> 的结构自动组织</li>
    <li><b>文件命名</b>: 视频文件名格式为 <code>mov{ID}.mp4</code>，其中ID为6位数字（如 mov001001.mp4）</li>
    <li><b>路径管理</b>: 所有下载内容统一保存在 <code>Bestdori/</code> 文件夹下，便于统一管理</li>
</ul>

<h3>⚠️ 注意事项</h3>
<ul>
    <li><b>文件大小</b>: 动态卡面视频文件较大（通常数MB到数十MB），下载前请确保有足够的磁盘空间</li>
    <li><b>下载时间</b>: 视频文件较大，下载速度取决于网络带宽，请耐心等待</li>
    <li><b>数量限制</b>: 不同角色的动态卡面数量差异较大，部分角色可能只有少量或没有动态卡面</li>
    <li><b>网络要求</b>: 建议在网络稳定、带宽充足时进行下载</li>
    <li><b>分批下载</b>: 如需下载大量视频，建议分批进行，避免单次下载时间过长</li>
    <li><b>文件格式</b>: 所有视频以 MP4 格式保存，兼容主流播放器</li>
</ul>

<h3>📁 文件保存位置</h3>
<p>所有下载的动态卡面视频文件保存在以下目录结构中：</p>
<pre>
&lt;您设置的根路径&gt;/
└── Bestdori/
    └── animation/                # 动态卡面下载目录
        ├── Poppin_Party/
        │   ├── ksm/
        │   │   ├── mov001001.mp4
        │   │   ├── mov001002.mp4
        │   │   └── ...
        │   └── ...
        └── ...
</pre>

<h3>🔄 与卡面下载的区别</h3>
<ul>
    <li><b>文件类型</b>: 动态卡面下载的是 MP4 视频文件，而卡面下载的是 PNG 图片文件</li>
    <li><b>查找策略</b>: 动态卡面数量较少，采用连续3次失败即停止的策略，更高效</li>
    <li><b>存储位置</b>: 保存在 <code>Bestdori/animation/</code> 目录下，与卡面分开存储</li>
</ul>
"""

# 关于文本
ABOUT_TEXT = """
<h2>BanG Dream! 动态卡面视频下载工具</h2>

<p><b>版本:</b> 2.1.2</p>
<p><b>更新日期:</b> 2025年11月</p>

<h3>📝 简介</h3>
<p>动态卡面视频下载工具是 Bestdori Card Manager 的重要组成部分，专门用于下载 BanG Dream! 游戏中的动态卡面视频资源。动态卡面包含了角色的精美动画效果，是卡面收藏的重要补充。</p>

<p><b>资源来源:</b> <a href="https://bestdori.com">Bestdori</a> - BanG Dream! 社区数据网站</p>

<h3>✨ 核心功能</h3>
<ul>
    <li><b>智能筛选</b>: 支持按乐队、乐器类型、角色进行多维度筛选，精确定位目标视频</li>
    <li><b>批量下载</b>: 一键批量下载多个角色的所有动态卡面视频</li>
    <li><b>智能查找</b>: 自动识别角色的动态卡面范围，连续失败自动跳过，提高效率</li>
    <li><b>文件验证</b>: 自动验证视频文件大小，确保下载的是有效视频文件</li>
    <li><b>自动分类</b>: 按乐队和角色自动创建文件夹结构，便于管理和查找</li>
    <li><b>实时反馈</b>: 详细的进度显示、状态信息和下载日志</li>
    <li><b>统一路径管理</b>: 所有下载资源（卡面、动态卡面、语音）统一保存在 <code>Bestdori/</code> 文件夹下</li>
    <li><b>优化交互体验</b>: 筛选菜单支持批量选择，手指针提示，点击外部区域自动关闭菜单</li>
    <li><b>文件处理</b>: 自动处理文件名非法字符，兼容 Windows 文件系统，避免路径错误</li>
</ul>

<h3>🎬 视频特性</h3>
<ul>
    <li><b>文件格式</b>: MP4 - 兼容所有主流播放器和设备</li>
    <li><b>命名规则</b>: mov{ID}.mp4，其中ID为6位数字（如 mov001001.mp4）</li>
    <li><b>文件大小</b>: 通常每个视频文件数MB到数十MB，请确保足够的存储空间</li>
    <li><b>下载策略</b>: 采用连续3次查找失败即停止的智能策略，适合动态卡面数量较少的特点</li>
</ul>

<h3>🎨 界面特性</h3>
<ul>
    <li><b>现代化设计</b>: 采用粉色主题风格，界面美观统一，所有按钮和控件样式协调一致</li>
    <li><b>响应式布局</b>: 自适应窗口大小，支持自由调整界面尺寸</li>
    <li><b>多线程处理</b>: 后台下载不影响界面操作，保持流畅体验</li>
    <li><b>优化交互</b>: 筛选菜单支持批量选择，手指针提示，点击外部区域自动关闭</li>
    <li><b>统一样式</b>: 所有下拉菜单、按钮样式统一，文字清晰可见，无黑色色块问题</li>
</ul>

<h3>🛠️ 技术架构</h3>
<ul>
    <li><b>开发框架</b>: PyQt6 - 跨平台图形界面框架，提供现代化UI组件</li>
    <li><b>网络请求</b>: requests - 高效稳定的HTTP客户端，支持文件下载</li>
    <li><b>多线程</b>: QThread - 异步下载，确保界面响应性</li>
    <li><b>文件验证</b>: 通过 Content-Length 检查文件大小，确保下载的是有效视频</li>
    <li><b>路径管理</b>: 统一的配置管理系统，自动创建最佳目录结构</li>
    <li><b>数据持久化</b>: JSON配置文件 - 保存用户设置和下载路径，支持配置管理</li>
    <li><b>文件管理</b>: 自动处理文件名非法字符（包括全角字符），兼容 Windows 文件系统</li>
    <li><b>UI样式</b>: QSS样式表 - 统一的主题样式，支持自定义和扩展</li>
</ul>

<h3>📦 版本信息</h3>
<ul>
    <li><b>当前版本</b>: 2.1.2</li>
    <li><b>主要功能</b>: 
        <ul>
            <li>卡面下载 - 高清PNG图片，支持normal和trained双形态</li>
            <li>动态卡面下载 - MP4视频格式，精美的动画效果</li>
            <li>语音下载 - MP3音频格式，按乐队和角色分类</li>
            <li>卡面预览 - 浏览和预览卡面资源</li>
        </ul>
    </li>
    <li><b>支持格式</b>: PNG图片、MP4视频、MP3音频</li>
    <li><b>操作系统</b>: Windows 10/11</li>
    <li><b>Python版本</b>: 3.8 及以上</li>
    <li><b>界面优化</b>: 统一的粉色主题、优化的筛选菜单交互、清晰的文字显示</li>
</ul>

<h3>⚠️ 使用须知</h3>
<ul>
    <li><b>使用目的</b>: 本工具仅用于个人学习、欣赏和研究，严禁用于任何商业用途</li>
    <li><b>版权声明</b>: 所有下载的游戏资源版权归 BanG Dream! 及其版权方 Craft Egg/Bushiroad 所有</li>
    <li><b>数据来源</b>: 资源来源于 Bestdori 社区网站，使用时请遵守该网站的使用条款</li>
    <li><b>存储空间</b>: 动态卡面视频文件较大，请确保有足够的磁盘空间</li>
    <li><b>网络要求</b>: 建议在网络稳定、带宽充足时进行下载</li>
    <li><b>数量说明</b>: 不同角色的动态卡面数量差异较大，部分角色可能没有动态卡面</li>
</ul>

<h3>🔄 与其他功能的配合</h3>
<p>动态卡面视频下载与卡面图片下载、语音下载、卡面预览共同构成了完整的 BanG Dream! 资源获取方案：</p>
<ul>
    <li><b>卡面下载</b>: 获取静态高清卡面图片（PNG格式），支持normal和trained双形态</li>
    <li><b>动态卡面下载</b>: 获取动态卡面视频（MP4格式），精美的动画效果</li>
    <li><b>语音下载</b>: 获取角色语音文件（MP3格式），按乐队和角色分类</li>
    <li><b>卡面预览</b>: 浏览和预览卡面资源，快速定位目标内容</li>
</ul>
<p>所有资源统一保存在 <code>Bestdori/</code> 目录下，按类型分类管理：</p>
<ul>
    <li><code>Bestdori/card/</code> - 卡面图片</li>
    <li><code>Bestdori/animation/</code> - 动态卡面视频</li>
    <li><code>Bestdori/voice/</code> - 语音文件</li>
</ul>
<p>统一的路径管理让所有资源井然有序，便于查找和管理。</p>

<h3>🙏 致谢</h3>
<p>感谢 Bestdori 社区提供的数据支持，感谢所有 BanG Dream! 玩家的热爱与支持。</p>

<p style="margin-top: 20px; color: #888; font-size: 12px;">
© 2025 Bestdori Card Manager | 开发者: dx闹着玩的 | 版本 2.1.2
</p>
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
                padding: 6px 20px 6px 8px; 
                border: 1px solid #E1E6EF;
                border-radius: 6px;
                background-color: #FFFFFF;
                color: #333333;
                font-size: 13px;
            }
            QToolButton::menu-indicator { 
                subcontrol-origin: padding;
                subcontrol-position: center right;
                margin-right: 8px;
                width: 12px;
                height: 12px;
            }
            QToolButton:hover { 
                background-color: #F5F7FA;
                border-color: #E85D9E;
            }
            QToolButton:pressed {
                background-color: #EDF1F5;
                border-color: #D35490;
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
        
        # QMenu 默认支持：1) checkable action 点击后不关闭菜单；2) 点击外部区域关闭菜单
        self._menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #E1E6EF;
                border-radius: 6px;
                padding: 4px 0;
            }
            QMenu::item { 
                padding: 6px 32px 6px 8px;
                color: #333333;
                background: transparent;
                min-height: 15px;
            }
            QMenu::item:hover {
                background: rgb(135, 206, 250);
                color: #FFFFFF;
            }
            QMenu::item:selected { 
                background: rgb(135, 206, 250);
                color: #FFFFFF;
            }
            QMenu::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #E1E6EF;
                border-radius: 4px;
                background: #FFFFFF;
                margin-left: 8px;
                margin-right: 8px;
            }
            QMenu::indicator:checked {
                background: rgb(135, 206, 250);
                border-color: rgb(135, 206, 250);
            }
            QMenu::separator {
                height: 1px;
                background: #F0F2F5;
                margin: 4px 0;
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
                border: 1px solid #E1E6EF;
                border-radius: 4px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: rgb(135, 206, 250);
                border-color: rgb(135, 206, 250);
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
        self.set_path_button.setStyleSheet("""
            QPushButton {
                background-color: #F8BBD9;
                color: #333333;
                padding: 6px 15px;
                border-radius: 6px;
                border: 1px solid #E5A5C5;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #F4A5CC;
            }
            QPushButton:pressed {
                background-color: #E895B8;
            }
        """)
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
        
        # 下载按钮（主按钮 - 主题粉色）
        self.download_button = QPushButton("下载")
        self.download_button.setStyleSheet("""
            QPushButton {
                background-color: #E85D9E;
                color: #ffffff;
                padding: 6px 15px;
                border-radius: 6px;
                border: 1px solid #C34E84;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #D35490;
            }
            QPushButton:pressed {
                background-color: #B3487D;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
                color: #666666;
                border-color: #999999;
            }
        """)
        self.download_button.clicked.connect(self.on_filter_clicked)
        button_container.addWidget(self.download_button)
        
        # 刷新按钮（次要按钮 - 浅粉色）
        self.refresh_button = QPushButton("刷新")
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #F8BBD9;
                color: #333333;
                padding: 6px 15px;
                border-radius: 6px;
                border: 1px solid #E5A5C5;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #F4A5CC;
            }
            QPushButton:pressed {
                background-color: #E895B8;
            }
        """)
        self.refresh_button.clicked.connect(self.on_refresh_clicked)
        button_container.addWidget(self.refresh_button)
        
        # 停止按钮（危险按钮 - 深粉红）（初始隐藏）
        self.stop_button = QPushButton("停止")
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #D32F2F;
                color: #ffffff;
                padding: 6px 15px;
                border-radius: 6px;
                border: 1px solid #B71C1C;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #C62828;
            }
            QPushButton:pressed {
                background-color: #B71C1C;
            }
        """)
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
                border: 1px solid #E1E6EF;
                border-radius: 6px;
                padding: 4px 0;
            }
            QMenu::item { 
                padding: 6px 32px 6px 8px;
                color: #333333;
                background: transparent;
                min-height: 15px;
            }
            QMenu::item:hover {
                background: rgb(135, 206, 250);
                color: #FFFFFF;
            }
            QMenu::item:selected { 
                background: rgb(135, 206, 250);
                color: #FFFFFF;
            }
            QMenu::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #E1E6EF;
                border-radius: 4px;
                background: #FFFFFF;
                margin-left: 8px;
                margin-right: 8px;
            }
            QMenu::indicator:checked {
                background: rgb(135, 206, 250);
                border-color: rgb(135, 206, 250);
            }
            QMenu::separator {
                height: 1px;
                background: #F0F2F5;
                margin: 4px 0;
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
                border: 1px solid #E1E6EF;
                border-radius: 4px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: rgb(135, 206, 250);
                border-color: rgb(135, 206, 250);
            }
        """)
        
        # 创建全部选项
        all_widget = QWidget(menu)
        all_layout = QHBoxLayout(all_widget)
        all_layout.setContentsMargins(8, 4, 8, 4)
        
        all_checkbox = QCheckBox(all_widget)
        all_checkbox.setChecked(True)
        all_checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
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
            checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
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
                background-color: #E85D9E; 
                color: white; 
                padding: 6px 15px; 
                border-radius: 6px;
                border: 1px solid #C34E84;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #D35490;
            }
            QPushButton:pressed {
                background-color: #B3487D;
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
                border: 1px solid #E1E6EF;
                border-radius: 6px;
                padding: 4px 0;
            }
            QMenu::item { 
                padding: 6px 32px 6px 8px;
                color: #333333;
                background: transparent;
                min-height: 15px;
            }
            QMenu::item:hover {
                background: rgb(135, 206, 250);
                color: #FFFFFF;
            }
            QMenu::item:selected { 
                background: rgb(135, 206, 250);
                color: #FFFFFF;
            }
            QMenu::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #E1E6EF;
                border-radius: 4px;
                background: #FFFFFF;
                margin-left: 8px;
                margin-right: 8px;
            }
            QMenu::indicator:checked {
                background: rgb(135, 206, 250);
                border-color: rgb(135, 206, 250);
            }
            QMenu::separator {
                height: 1px;
                background: #F0F2F5;
                margin: 4px 0;
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
                border: 1px solid #E1E6EF;
                border-radius: 4px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: rgb(135, 206, 250);
                border-color: rgb(135, 206, 250);
            }
        """)
        
        # 创建全部选项
        all_widget = QWidget(menu)
        all_layout = QHBoxLayout(all_widget)
        all_layout.setContentsMargins(8, 4, 8, 4)
        
        all_checkbox = QCheckBox(all_widget)
        all_checkbox.setChecked(True)
        all_checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
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
            checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
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
                background-color: #E85D9E; 
                color: white; 
                padding: 6px 15px; 
                border-radius: 6px;
                border: 1px solid #C34E84;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #D35490;
            }
            QPushButton:pressed {
                background-color: #B3487D;
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
                border: 1px solid #E1E6EF;
                border-radius: 6px;
                padding: 4px 0;
            }
            QMenu::item { 
                padding: 6px 32px 6px 8px;
                color: #333333;
                background: transparent;
                min-height: 15px;
            }
            QMenu::item:hover {
                background: rgb(135, 206, 250);
                color: #FFFFFF;
            }
            QMenu::item:selected { 
                background: rgb(135, 206, 250);
                color: #FFFFFF;
            }
            QMenu::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #E1E6EF;
                border-radius: 4px;
                background: #FFFFFF;
                margin-left: 8px;
                margin-right: 8px;
            }
            QMenu::indicator:checked {
                background: rgb(135, 206, 250);
                border-color: rgb(135, 206, 250);
            }
            QMenu::separator {
                height: 1px;
                background: #F0F2F5;
                margin: 4px 0;
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
                border: 1px solid #E1E6EF;
                border-radius: 4px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: rgb(135, 206, 250);
                border-color: rgb(135, 206, 250);
            }
        """)
        
        # 创建全部选项
        all_widget = QWidget(menu)
        all_layout = QHBoxLayout(all_widget)
        all_layout.setContentsMargins(8, 4, 8, 4)
        
        all_checkbox = QCheckBox(all_widget)
        all_checkbox.setChecked(True)
        all_checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
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
            checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
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
                background-color: #E85D9E; 
                color: white; 
                padding: 6px 15px; 
                border-radius: 6px;
                border: 1px solid #C34E84;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #D35490;
            }
            QPushButton:pressed {
                background-color: #B3487D;
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
        
        # 重置进度条和状态
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setVisible(False)
        if hasattr(self, 'status_label'):
            self.status_label.setText("")
        
        # 重新启用下载按钮
        if hasattr(self, 'download_button'):
            self.download_button.setEnabled(True)
        if hasattr(self, 'stop_button'):
            self.stop_button.setVisible(False)
        
        self.add_log_entry("界面已重置", True)
    
    def on_stop_clicked(self):
        """处理停止按钮点击事件"""
        # 安全地终止线程
        if hasattr(self, 'download_thread') and self.download_thread is not None:
            if self.download_thread.isRunning():
                self.download_thread.terminate()
                self.download_thread.wait(3000)  # 最多等待3秒
                # 清理线程引用
                self.download_thread = None
            
            # 更新UI状态
            if hasattr(self, 'download_button'):
                self.download_button.setEnabled(True)
            if hasattr(self, 'stop_button'):
                self.stop_button.setVisible(False)
            if hasattr(self, 'progress_bar'):
                self.progress_bar.setVisible(False)
            
            # 添加停止日志
            if hasattr(self, 'add_log_entry'):
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
        # 安全地更新UI状态
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setVisible(False)
        if hasattr(self, 'download_button'):
            self.download_button.setEnabled(True)
        if hasattr(self, 'stop_button'):
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
                background-color: #E85D9E;
                color: white;
                border: 1px solid #C34E84;
                border-radius: 6px;
                padding: 8px 16px;
                min-width: 80px;
                font-weight: 500;
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
                background-color: #E85D9E;
                color: white;
                border: 1px solid #C34E84;
                border-radius: 6px;
                padding: 8px 16px;
                min-width: 80px;
                font-weight: 500;
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

