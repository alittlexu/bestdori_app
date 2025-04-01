from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, 
                             QStackedWidget, QFrame, QToolBar,
                             QMenuBar, QMenu)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QFont, QAction, QPainter, QPixmap
import os

from .pages.card_page import CardPage
from .pages.card_preview_page import CardPreviewPage
from .pages.blank_page import BlankPage
from .pages.card_download_page import CardDownloadPage
from .pages.card_search_page import CardSearchPage
from .background_manager import BackgroundManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bestdori Card Manager")
        self.setMinimumSize(1200, 800)
        
        # 设置图标路径
        self.icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'assets', 'icons')
        
        # 设置应用图标
        icon = QIcon(os.path.join(self.icon_path, 'bestdori.ico'))
        self.setWindowIcon(icon)
        
        # 初始化背景管理器
        self.background_manager = BackgroundManager()
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建工具栏
        self.create_tool_bars()
        
        # 创建主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建内容区域
        self.content_area = self.create_content_area()
        main_layout.addWidget(self.content_area)
        
        # 设置样式
        self.setup_styles()
        
        # 连接信号
        self.connect_signals()
        
        # 设置背景（只在初始化时设置一次）
        self.set_background()
        
    def set_background(self):
        """设置窗口背景"""
        self.background_pixmap = self.background_manager.apply_background(self)
        if self.background_pixmap:
            self.update()
            
    def paintEvent(self, event):
        """重写绘制事件以显示背景"""
        super().paintEvent(event)
        if hasattr(self, 'background_pixmap') and self.background_pixmap:
            painter = QPainter(self)
            painter.drawPixmap(0, 0, self.background_pixmap)
            
    def resizeEvent(self, event):
        """重写大小改变事件，移除背景更新"""
        super().resizeEvent(event)
        # 不再更新背景，保持原有背景
        
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        file_menu.addAction(QIcon(os.path.join(self.icon_path, 'import.png')), "导入设置")
        file_menu.addAction(QIcon(os.path.join(self.icon_path, 'export.png')), "导出设置")
        file_menu.addSeparator()
        file_menu.addAction(QIcon(os.path.join(self.icon_path, 'exit.png')), "退出")
        
        # 卡面管理菜单
        card_menu = menubar.addMenu("卡面管理")
        card_menu.addAction(QIcon(os.path.join(self.icon_path, 'batch.png')), "批量下载设置")
        card_menu.addAction(QIcon(os.path.join(self.icon_path, 'history.png')), "下载历史")
        card_menu.addAction(QIcon(os.path.join(self.icon_path, 'export.png')), "卡面导出")
        card_menu.addAction(QIcon(os.path.join(self.icon_path, 'settings.png')), "存储位置设置")
        
        # 语音管理菜单
        voice_menu = menubar.addMenu("语音管理")
        voice_menu.addAction(QIcon(os.path.join(self.icon_path, 'batch.png')), "批量下载设置")
        voice_menu.addAction(QIcon(os.path.join(self.icon_path, 'history.png')), "下载历史")
        voice_menu.addAction(QIcon(os.path.join(self.icon_path, 'package.png')), "语音包管理")
        voice_menu.addAction(QIcon(os.path.join(self.icon_path, 'settings.png')), "存储位置设置")
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        self.usage_action = help_menu.addAction(QIcon(os.path.join(self.icon_path, 'help.png')), "使用说明")
        self.usage_action.triggered.connect(self.show_usage_guide)
        
        self.about_action = help_menu.addAction(QIcon(os.path.join(self.icon_path, 'about.png')), "关于")
        self.about_action.triggered.connect(self.show_about)
        
    def create_tool_bars(self):
        """创建工具栏"""
        # 卡面工具栏
        card_toolbar = QToolBar("卡面工具")
        card_toolbar.setObjectName("cardToolBar")
        card_toolbar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, card_toolbar)
        
        # 创建卡面获取菜单
        card_fetch_menu = QMenu("卡面获取", self)
        card_fetch_menu.setObjectName("cardFetchMenu")
        
        # 添加卡面获取相关动作
        card_refresh_action = QAction(QIcon(os.path.join(self.icon_path, 'refresh.png')), "刷新界面", self)
        card_download_action = QAction(QIcon(os.path.join(self.icon_path, 'download.png')), "下载卡面", self)
        card_search_action = QAction(QIcon(os.path.join(self.icon_path, 'search.png')), "搜索卡面", self)
        
        card_fetch_menu.addAction(card_refresh_action)
        card_fetch_menu.addAction(card_download_action)
        card_fetch_menu.addAction(card_search_action)
        
        # 创建卡面获取按钮
        card_fetch_btn = QPushButton("卡面获取")
        card_fetch_btn.setObjectName("cardFetchBtn")
        card_fetch_btn.setMenu(card_fetch_menu)
        card_toolbar.addWidget(card_fetch_btn)
        
        # 添加分隔符
        card_toolbar.addSeparator()
        
        # 语音工具栏
        voice_toolbar = QToolBar("语音工具")
        voice_toolbar.setObjectName("voiceToolBar")
        voice_toolbar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, voice_toolbar)
        
        # 创建语音获取菜单
        voice_fetch_menu = QMenu("语音获取", self)
        voice_fetch_menu.setObjectName("voiceFetchMenu")
        
        # 添加语音获取相关动作
        voice_refresh_action = QAction(QIcon(os.path.join(self.icon_path, 'refresh.png')), "刷新语音", self)
        voice_download_action = QAction(QIcon(os.path.join(self.icon_path, 'voice_download.png')), "下载语音", self)
        voice_search_action = QAction(QIcon(os.path.join(self.icon_path, 'voice_search.png')), "搜索语音", self)
        
        voice_fetch_menu.addAction(voice_refresh_action)
        voice_fetch_menu.addAction(voice_download_action)
        voice_fetch_menu.addAction(voice_search_action)
        
        # 创建语音获取按钮
        voice_fetch_btn = QPushButton("语音获取")
        voice_fetch_btn.setObjectName("voiceFetchBtn")
        voice_fetch_btn.setMenu(voice_fetch_menu)
        voice_toolbar.addWidget(voice_fetch_btn)
        
        # 添加分隔符
        voice_toolbar.addSeparator()
        
        # 创建卡面预览按钮
        card_preview_btn = QPushButton("卡面预览")
        card_preview_btn.setObjectName("cardPreviewBtn")
        voice_toolbar.addWidget(card_preview_btn)
        
    def setup_styles(self):
        """设置窗口样式"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: transparent;
            }
            
            #contentArea {
                background-color: transparent;
            }
            
            QWidget {
                background-color: transparent;
            }
            
            QMenuBar {
                background-color: #2c3e50;
                color: white;
            }
            
            QMenuBar::item {
                padding: 8px 12px;
            }
            
            QMenuBar::item:selected {
                background-color: #34495e;
            }
            
            QMenu {
                background-color: #2c3e50;
                color: white;
                border: none;
            }
            
            QMenu::item {
                padding: 8px 20px;
            }
            
            QMenu::item:selected {
                background-color: #34495e;
            }
            
            QToolBar {
                background-color: #f8f9fa;
                border-bottom: 1px solid #dee2e6;
                spacing: 10px;
                padding: 5px;
            }
            
            QToolBar QToolButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
            }
            
            QToolBar QToolButton:hover {
                background-color: #2980b9;
            }
            
            QToolBar QToolButton:pressed {
                background-color: #2472a4;
            }
            
            QToolBar QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                min-width: 100px;
            }
            
            QToolBar QPushButton:hover {
                background-color: #2980b9;
            }
            
            QToolBar QPushButton:pressed {
                background-color: #2472a4;
            }
            
            #cardFetchBtn, #voiceFetchBtn {
                background-color: #2ecc71;
            }
            
            #cardFetchBtn:hover, #voiceFetchBtn:hover {
                background-color: #27ae60;
            }
            
            #cardFetchBtn:pressed, #voiceFetchBtn:pressed {
                background-color: #219a52;
            }
            
            #cardPreviewBtn {
                background-color: #e74c3c;
            }
            
            #cardPreviewBtn:hover {
                background-color: #c0392b;
            }
            
            #cardPreviewBtn:pressed {
                background-color: #a93226;
            }
            
            #navFrame {
                background-color: #2c3e50;
                border-right: 1px solid #34495e;
            }
            
            QPushButton {
                padding: 12px 20px;
                border: none;
                border-radius: 5px;
                color: #ecf0f1;
                text-align: left;
                font-size: 14px;
            }
            
            #toolbar QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
            }
            
            #toolbar QPushButton:hover {
                background-color: #2980b9;
            }
            
            #downloadBtn {
                background-color: #2ecc71 !important;
            }
            
            #downloadBtn:hover {
                background-color: #27ae60 !important;
            }
            
            #playBtn {
                background-color: #3498db !important;
            }
            
            #playBtn:hover {
                background-color: #2980b9 !important;
            }
            
            #cardPreviewFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #dee2e6;
            }
            
            #cardPreviewFrame:hover {
                border-color: #3498db;
                background-color: #f8f9fa;
            }
            
            #filterFrame {
                background-color: #f8f9fa;
                border-radius: 5px;
                margin-top: 5px;
            }
            
            QComboBox {
                padding: 5px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                min-width: 120px;
            }
            
            QLabel {
                color: #2c3e50;
            }
            
            #searchBox {
                padding: 8px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                min-width: 200px;
            }
            
            #cardScroll {
                border: none;
                background-color: white;
                border-radius: 5px;
            }
        """)

    def create_content_area(self):
        """创建右侧内容区域"""
        content = QStackedWidget()
        content.setObjectName("contentArea")
        
        # 添加各个页面
        self.blank_page = BlankPage()
        self.card_page = CardPage()
        self.card_preview_page = CardPreviewPage()
        self.card_download_page = CardDownloadPage()
        self.card_search_page = CardSearchPage()
        
        content.addWidget(self.blank_page)
        content.addWidget(self.card_page)
        content.addWidget(self.card_preview_page)
        content.addWidget(self.card_download_page)
        content.addWidget(self.card_search_page)
        
        # 默认显示空白页面
        content.setCurrentWidget(self.blank_page)
        
        return content
        
    def connect_signals(self):
        """连接信号"""
        # 工具栏动作信号
        # 查找工具栏中的按钮
        for child in self.findChildren(QPushButton):
            if child.objectName() == "cardPreviewBtn":
                child.clicked.connect(self.on_card_preview_clicked)
        
        # 查找菜单中的动作
        card_fetch_menu = self.findChild(QMenu, "cardFetchMenu")
        if card_fetch_menu:
            for action in card_fetch_menu.actions():
                if action.text() == "下载卡面":
                    action.triggered.connect(self.on_card_download_clicked)
                elif action.text() == "搜索卡面":
                    action.triggered.connect(self.on_card_search_clicked)
                elif action.text() == "刷新界面":
                    action.triggered.connect(self.on_refresh_clicked)
    
    def on_card_preview_clicked(self):
        """卡面预览按钮点击处理"""
        self.content_area.setCurrentWidget(self.card_preview_page)
        
    def on_card_download_clicked(self):
        """卡面下载按钮点击处理"""
        self.content_area.setCurrentWidget(self.card_download_page)
        
    def on_card_search_clicked(self):
        """卡面搜索按钮点击处理"""
        self.content_area.setCurrentWidget(self.card_search_page)

    def on_refresh_clicked(self):
        """刷新界面按钮点击处理"""
        # 重置内容区域到空白页面
        self.content_area.setCurrentWidget(self.blank_page)
        
        # 重新设置背景
        self.set_background()
        
        # 更新界面
        self.update()
        
        # 重置所有页面状态
        # 先移除所有页面
        self.content_area.removeWidget(self.card_page)
        self.content_area.removeWidget(self.card_preview_page)
        self.content_area.removeWidget(self.card_download_page)
        self.content_area.removeWidget(self.card_search_page)
        
        # 重新创建页面
        self.card_page = CardPage()
        self.card_preview_page = CardPreviewPage()
        self.card_download_page = CardDownloadPage()
        self.card_search_page = CardSearchPage()
        
        # 重新添加页面
        self.content_area.addWidget(self.card_page)
        self.content_area.addWidget(self.card_preview_page)
        self.content_area.addWidget(self.card_download_page)
        self.content_area.addWidget(self.card_search_page)

    def show_usage_guide(self):
        """显示使用说明"""
        # 获取当前显示的页面
        current_widget = self.content_area.currentWidget()
        if hasattr(current_widget, 'show_usage_guide'):
            current_widget.show_usage_guide()
        else:
            # 如果当前页面没有使用说明，默认使用卡面下载页面的使用说明
            if hasattr(self, 'card_download_page'):
                self.card_download_page.show_usage_guide()
            else:
                # 创建一个临时的卡面下载页面来显示使用说明
                temp_page = CardDownloadPage()
                temp_page.show_usage_guide()
    
    def show_about(self):
        """显示关于信息"""
        # 获取当前显示的页面
        current_widget = self.content_area.currentWidget()
        if hasattr(current_widget, 'show_about'):
            current_widget.show_about()
        else:
            # 如果当前页面没有关于信息，默认使用卡面下载页面的关于信息
            if hasattr(self, 'card_download_page'):
                self.card_download_page.show_about()
            else:
                # 创建一个临时的卡面下载页面来显示关于信息
                temp_page = CardDownloadPage()
                temp_page.show_about()