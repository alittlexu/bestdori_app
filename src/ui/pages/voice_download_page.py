from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar,
    QFileDialog, QFrame, QMessageBox, QScrollArea, QTabWidget, QGroupBox,
    QListWidget, QListWidgetItem, QApplication, QCheckBox, QWidgetAction
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon
try:
    from src.ui.styles.theme import (
        get_common_styles, get_tabs_styles, get_groupbox_styles,
        get_voice_page_styles, build_stylesheet
    )
except Exception:
    get_common_styles = lambda: ""
    get_tabs_styles = lambda: ""
    get_groupbox_styles = lambda: ""
    get_voice_page_styles = lambda: ""
    build_stylesheet = lambda *parts: ""

import os

from src.core.voice.voice_downloader import VoiceDownloader
from src.ui.pages.card_download_page import MenuComboBox  # 复用多选控件
from src.utils.config_manager import get_config_manager
from src.utils.path_utils import ensure_download_path


class VoiceDownloadThread(QThread):
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    download_completed = pyqtSignal(dict)

    def __init__(self, nicknames: list[str], mode: str, to_wav: bool, save_dir: str):
        super().__init__()
        self.nicknames = nicknames
        self.mode = mode
        self.to_wav = to_wav
        self.save_dir = save_dir
        self.downloader = VoiceDownloader(save_dir)

    def _progress_cb(self, value: int):
        self.progress_updated.emit(max(0, min(100, int(value))))

    def _status_cb(self, text: str):
        self.status_updated.emit(text)

    def run(self):
        try:
            stats = self.downloader.download_by_characters(
                nicknames=self.nicknames,
                mode=self.mode,
                to_wav=self.to_wav,
                status_callback=self._status_cb,
                progress_callback=self._progress_cb
            )
            self.download_completed.emit({
                'success': True,
                'stats': stats
            })
        except Exception as e:
            self.download_completed.emit({
                'success': False,
                'message': str(e)
            })


class VoiceDownloadPage(QWidget):
    """语音下载页面（初版骨架）。
    后续将与实际语音下载实现对接，当前提供基本的保存目录选择、开始/停止与进度显示。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread = None
        self._save_dir = None
        self.config_manager = get_config_manager()
        self._instrument_cats = ['吉他', '贝斯', '鼓', '键盘', '主唱', 'DJ', '小提琴']
        self._bands = []
        self._characters = []
        # 初始化任务统计
        self._task_index = 0
        self._task_total = 0
        # 定义统一的菜单样式，供所有筛选菜单使用
        self._menu_stylesheet = """
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
            """
        self._init_ui()
        self._load_character_data()
        self._populate_filters()

    def _init_ui(self):
        self.setObjectName("VoiceDownloadPage")
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # 子导航（四个模块）
        tabs = QTabWidget()
        tabs.setObjectName("VoiceTabs")
        main_layout.addWidget(tabs, 1)

        # 1) 卡面语音获取（含筛选区 + 状态/日志）
        self.card_voice_tab = QWidget()
        self.card_voice_tab.setObjectName("CardVoiceTab")
        tabs.addTab(self.card_voice_tab, "卡面语音获取")
        card_layout = QVBoxLayout(self.card_voice_tab)

        # 路径设置区域
        path_container = QFrame()
        path_container.setFrameShape(QFrame.Shape.StyledPanel)
        path_container.setStyleSheet("background-color: #e8f5e9; border-radius: 5px; padding: 5px;")
        path_container.setContentsMargins(10, 10, 10, 10)
        card_layout.addWidget(path_container)
        
        path_layout = QHBoxLayout(path_container)
        path_layout.addWidget(QLabel("下载根路径:"))
        
        # 显示当前路径
        self.path_label = QLabel()
        self._update_path_label()
        self.path_label.setStyleSheet("color: #333; padding: 3px;")
        self.path_label.setWordWrap(True)
        path_layout.addWidget(self.path_label, 1)
        
        # 设置路径按钮（次要按钮 - 浅粉色）
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
        self.set_path_button.clicked.connect(self._on_set_path_clicked)
        path_layout.addWidget(self.set_path_button)

        # 筛选区：复用卡页的多选控件
        filter_group = QGroupBox("")
        filter_group.setObjectName("FilterGroup")
        card_layout.addWidget(filter_group)
        filter_layout = QHBoxLayout(filter_group)

        # 图标路径
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), 'assets', 'icons')

        band_icon = QLabel()
        band_icon.setPixmap(QIcon(os.path.join(icon_path, 'package.png')).pixmap(16, 16))
        filter_layout.addWidget(band_icon)
        self.band_select = MenuComboBox("选择乐队 (可多选)")
        filter_layout.addWidget(self.band_select)

        ins_icon = QLabel()
        ins_icon.setPixmap(QIcon(os.path.join(icon_path, 'voice_search.png')).pixmap(16, 16))
        filter_layout.addWidget(ins_icon)
        self.instrument_select = MenuComboBox("选择乐器 (可多选)")
        filter_layout.addWidget(self.instrument_select)

        member_icon = QLabel()
        member_icon.setPixmap(QIcon(os.path.join(icon_path, 'download.png')).pixmap(16, 16))
        filter_layout.addWidget(member_icon)
        self.character_select = MenuComboBox("选择人物 (可多选)")
        filter_layout.addWidget(self.character_select)

        filter_layout.addStretch(1)
        
        # 重置筛选按钮（次要按钮 - 浅粉色）
        self.reset_btn = QPushButton("重置筛选")
        self.reset_btn.setIcon(QIcon(os.path.join(icon_path, 'refresh.png')))
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #F8BBD9;
                color: #333333;
                padding: 6px 12px;
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
        self.reset_btn.clicked.connect(self._on_reset_filters)
        filter_layout.addWidget(self.reset_btn)
        
        # 终止下载按钮（危险按钮 - 深粉红）（初始隐藏）
        self.stop_btn = QPushButton("终止下载")
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #D32F2F;
                color: #ffffff;
                padding: 6px 12px;
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
        self.stop_btn.setVisible(False)
        self.stop_btn.clicked.connect(self._on_stop)
        filter_layout.addWidget(self.stop_btn)

        # 进度区块（标题统计 + 列表 + 控制）
        progress_group = QGroupBox("下载进度")
        card_layout.addWidget(progress_group, 1)
        prog_layout = QVBoxLayout(progress_group)

        self.progress_summary = QLabel("当前下载任务 (0/0)")
        prog_layout.addWidget(self.progress_summary)

        self.tasks_list = QListWidget()
        self.tasks_list.setObjectName("VoiceTaskList")
        prog_layout.addWidget(self.tasks_list, 1)

        ctrl_row = QHBoxLayout()
        prog_layout.addLayout(ctrl_row)
        self.pause_all_btn = QPushButton("全部暂停")
        self.pause_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #D32F2F;
                color: #ffffff;
                padding: 6px 12px;
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
        self.pause_all_btn.clicked.connect(self._on_stop)  # 暂以停止实现
        ctrl_row.addWidget(self.pause_all_btn)
        self.cancel_all_btn = QPushButton("全部取消")
        self.cancel_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #D32F2F;
                color: #ffffff;
                padding: 6px 12px;
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
        self.cancel_all_btn.clicked.connect(self._on_stop)
        ctrl_row.addWidget(self.cancel_all_btn)
        ctrl_row.addStretch(1)

        # 启动下载按钮（主按钮 - 主题粉色）放置在筛选与进度之间更直观
        self.start_btn = QPushButton("开始下载")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #E85D9E;
                color: #ffffff;
                padding: 8px 20px;
                border-radius: 6px;
                border: 1px solid #C34E84;
                font-weight: 500;
                font-size: 14px;
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
        self.start_btn.clicked.connect(self._on_start)
        card_layout.addWidget(self.start_btn)

        # 2) 故事语音获取（占位）
        self.story_voice_tab = QWidget()
        tabs.addTab(self.story_voice_tab, "故事语音获取")
        story_layout = QVBoxLayout(self.story_voice_tab)
        story_layout.addWidget(QLabel("故事语音获取（开发中）"))

        # 3) 场景语音获取（占位）
        self.scene_voice_tab = QWidget()
        tabs.addTab(self.scene_voice_tab, "场景语音获取")
        scene_layout = QVBoxLayout(self.scene_voice_tab)
        scene_layout.addWidget(QLabel("场景语音获取（开发中）"))

        # 4) 活动语音获取（占位）
        self.event_voice_tab = QWidget()
        tabs.addTab(self.event_voice_tab, "活动语音获取")
        event_layout = QVBoxLayout(self.event_voice_tab)
        event_layout.addWidget(QLabel("活动语音获取（开发中）"))

        # 采用全局主题样式，保持统一
        self.setStyleSheet(build_stylesheet(
            get_common_styles(),
            get_tabs_styles(),
            get_groupbox_styles(),
            get_voice_page_styles()
        ))

    def _update_path_label(self):
        """更新路径显示标签"""
        root_path = self.config_manager.get_download_root_path()
        if root_path:
            self.path_label.setText(f"{root_path}/Bestdori/voice/")
            self.path_label.setToolTip(f"根路径: {root_path}")
        else:
            self.path_label.setText("未设置（点击\"设置路径\"按钮设置）")
            self.path_label.setToolTip("请设置下载根路径")
    
    def _on_set_path_clicked(self):
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
                self._update_path_label()
                QMessageBox.information(self, "设置成功", f"下载根路径已设置为：\n{selected_path}\n\n下载文件将保存在：\n{selected_path}/Bestdori/")
            else:
                QMessageBox.warning(self, "设置失败", "保存路径配置失败，请重试")

    def _on_start(self):
        # 检查是否设置了下载根路径
        try:
            # 使用新的路径结构：<root>/Bestdori/voice/
            save_dir = ensure_download_path('voice')
        except ValueError as e:
            QMessageBox.warning(self, "路径未设置", f"{str(e)}\n\n请先点击\"设置路径\"按钮设置下载根路径。")
            return
        except Exception as e:
            QMessageBox.critical(self, "路径错误", f"创建下载目录失败: {str(e)}")
            return

        # 从筛选结果生成昵称列表
        nicknames = self._gather_selected_nicknames()
        if not nicknames:
            QMessageBox.information(self, "提示", "请至少选择一个人物或一个乐队")
            return
        # 任务计入前输出选择摘要
        self._append_log(f"准备下载: {', '.join(nicknames[:5])}{'...' if len(nicknames)>5 else ''}")
        mode = "card"  # 先固定使用卡面故事
        to_wav = False

        self._thread = VoiceDownloadThread(nicknames, mode, to_wav, save_dir)
        self._thread.progress_updated.connect(self._on_progress)
        self._thread.status_updated.connect(self._on_status)
        self._thread.download_completed.connect(self._on_completed)

        # 清理任务列表与统计
        self.tasks_list.clear()
        self._task_index = 0
        self._task_total = len(nicknames)  # 粗略以人物数量作为起点
        self._update_summary()
        self.start_btn.setEnabled(False)
        self.stop_btn.setVisible(True)
        self._thread.start()

    def _on_stop(self):
        """处理停止/暂停/取消下载"""
        # 安全地终止线程
        if hasattr(self, '_thread') and self._thread is not None:
            if self._thread.isRunning():
                self._thread.terminate()
                self._thread.wait(3000)  # 最多等待3秒
                # 清理线程引用
                self._thread = None
        
        # 更新UI状态
        if hasattr(self, 'start_btn'):
            self.start_btn.setEnabled(True)
        if hasattr(self, 'stop_btn'):
            self.stop_btn.setVisible(False)
        
        # 注意：语音获取页面没有独立的进度条，只有 progress_summary 标签
        # 重置进度显示
        if hasattr(self, 'progress_summary'):
            self.progress_summary.setText("当前下载任务 (0/0)")
        
        # 重置任务统计
        self._task_index = 0
        self._task_total = 0
        
        # 添加日志
        if hasattr(self, 'tasks_list'):
            self._append_log("下载已停止")

    def _on_progress(self, value: int):
        # 顶部汇总用整体百分比呈现（无需单条更新）
        self.progress_summary.setText(f"当前下载任务 ({int(value)}%)")

    def _on_status(self, text: str):
        # 解析状态：创建或更新任务行
        # 1) 遇到“尝试 resXXXXXX.mp3” 新建或标记为下载中
        # 2) 遇到“已保存: <path>” 标记完成
        # 3) 其余附加为日志行
        if "尝试 res" in text and text.endswith(".mp3"):
            name = text.split("尝试 ")[-1].split(" ")[0]
            self._ensure_task_item(name, status="下载中", progress=50)
        elif text.startswith("已保存:"):
            path = text.split(":", 1)[-1].strip()
            name = os.path.basename(path)
            self._ensure_task_item(name, status="已完成", progress=100)
            self._task_index += 1
            self._update_summary()
        else:
            # 追加简易日志为单行项目
            item = QListWidgetItem(text)
            self.tasks_list.addItem(item)

    def _on_completed(self, result: dict):
        """下载完成处理"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setVisible(False)
        # 注意：语音获取页面没有独立的进度条，只有 progress_summary 标签
        # 重置进度显示已在完成时由 _update_summary 处理
        
        if result.get('success'):
            self._update_summary(done=True)
            from src.ui.components.download_completion_dialog import DownloadCompletionDialog
            DownloadCompletionDialog.show_voice_completion(self, result)
        else:
            from src.ui.components.download_completion_dialog import DownloadCompletionDialog
            DownloadCompletionDialog.show_voice_completion(self, result)
            # 失败时重置进度显示
            self.progress_summary.setText("当前下载任务 (0/0)")
            self._task_index = 0
            self._task_total = 0

    def _append_log(self, text: str):
        self.tasks_list.addItem(QListWidgetItem(text))

    def _on_reset_filters(self):
        # 取消菜单勾选并重置展示文本
        for menu_btn in [self.band_select, self.instrument_select, self.character_select]:
            m = menu_btn.menu()
            for a in m.actions():
                if a.isCheckable():
                    a.setChecked(False)
        self._update_band_text()
        self._update_instrument_text()
        self._update_character_text()
        self.tasks_list.clear()
        self.progress_summary.setText("当前下载任务 (0/0)")

    def _ensure_task_item(self, name: str, status: str, progress: int):
        # 在列表中查找同名项，否则创建
        for i in range(self.tasks_list.count()):
            it = self.tasks_list.item(i)
            if it.text().startswith(name + " "):
                it.setText(f"{name}  |  {status}  |  {progress}%")
                return
        self.tasks_list.addItem(QListWidgetItem(f"{name}  |  {status}  |  {progress}%"))

    def _update_summary(self, done: bool=False):
        if done:
            self.progress_summary.setText(f"当前下载任务 ({self._task_index}/{self._task_total}) 完成")
        else:
            self.progress_summary.setText(f"当前下载任务 ({self._task_index}/{self._task_total})")

    # ===== 数据加载与筛选逻辑 =====
    def _load_character_data(self):
        try:
            # 计算项目根目录：.../src/ui/pages -> 上上上上一层
            base_dir = os.path.dirname(
                os.path.dirname(
                    os.path.dirname(
                        os.path.dirname(os.path.abspath(__file__))
                    )
                )
            )
            # 优先根目录，其次 data 目录
            candidates = [
                os.path.join(base_dir, 'character_list.json'),
                os.path.join(base_dir, 'data', 'character_list.json'),
            ]
            data_path = None
            for p in candidates:
                if os.path.exists(p):
                    data_path = p
                    break
            if not data_path:
                raise FileNotFoundError("未找到 character_list.json")
            import json
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            bands = []
            characters = []
            for group in data.get('groups', []):
                bands.append({'id': group.get('id'), 'name': group.get('name')})
                for member in group.get('members', []):
                    ins_list = member.get('instruments') or []
                    ins_text = "|".join([str(x) for x in ins_list])
                    characters.append({
                        'id': member.get('id'),
                        'name': member.get('name'),
                        'band_id': group.get('id'),
                        'nickname': member.get('nickname'),
                        'instrument_cat': self._normalize_instrument(ins_text)
                    })
            self._bands = bands
            self._characters = characters
        except Exception as e:
            QMessageBox.warning(self, "数据加载失败", f"无法加载人物数据: {e}")

    def _populate_filters(self):
        # 乐队填充 - 使用 QWidgetAction + QCheckBox + QLabel 实现手指针效果和批量选择
        band_menu = self.band_select.menu()
        band_menu.setObjectName("FilterMenu")
        
        def ensure_band_menu_style():
            band_menu.setStyleSheet(self._menu_stylesheet)
        try:
            band_menu.aboutToShow.disconnect()
        except:
            pass
        band_menu.aboutToShow.connect(ensure_band_menu_style)
        band_menu.setStyleSheet(self._menu_stylesheet)
        band_menu.clear()
        
        # 创建"全部"选项
        all_widget = QWidget(band_menu)
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
        
        def create_band_click_handler(cb):
            return lambda e: self._toggle_band_checkbox(cb)
        
        all_label.mousePressEvent = create_band_click_handler(all_checkbox)
        all_checkbox.stateChanged.connect(lambda state: self._on_band_checkbox_changed(-1, state))
        all_layout.addWidget(all_label)
        all_layout.addStretch()
        
        all_action = QWidgetAction(band_menu)
        all_action.setDefaultWidget(all_widget)
        band_menu.addAction(all_action)
        
        # 存储全部复选框引用
        self.band_checkboxes = {-1: all_checkbox}
        self.band_actions = {-1: all_action}
        self.band_labels = {-1: all_label}
        
        band_menu.addSeparator()
        
        # 添加每个乐队选项
        for band in self._bands:
            band_widget = QWidget(band_menu)
            band_layout = QHBoxLayout(band_widget)
            band_layout.setContentsMargins(8, 4, 8, 4)
            
            checkbox = QCheckBox(band_widget)
            checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
            checkbox.setChecked(False)  # 初始未选中，只有"全部"选中
            band_layout.addWidget(checkbox)
            
            label = QLabel(band.get('name') or '', band_widget)
            label.setCursor(Qt.CursorShape.PointingHandCursor)
            label.setProperty("is_checked", False)  # 默认未选中
            label.setStyleSheet("color: #333333;")  # 默认未选中状态使用黑色
            label.mousePressEvent = create_band_click_handler(checkbox)
            band_layout.addWidget(label)
            band_layout.addStretch()
            
            action = QWidgetAction(band_menu)
            action.setDefaultWidget(band_widget)
            band_menu.addAction(action)
            
            self.band_checkboxes[band.get('id')] = checkbox
            self.band_actions[band.get('id')] = action
            self.band_labels[band.get('id')] = label
            checkbox.stateChanged.connect(lambda state, b_id=band.get('id'): self._on_band_checkbox_changed(b_id, state))
        
        band_menu.addSeparator()
        confirm_widget = QWidget(band_menu)
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
        confirm_button.clicked.connect(band_menu.hide)
        confirm_layout.addWidget(confirm_button)
        
        confirm_action = QWidgetAction(band_menu)
        confirm_action.setDefaultWidget(confirm_widget)
        band_menu.addAction(confirm_action)
        
        # 更新确认按钮引用
        self.band_select.confirm_action = confirm_action

        # 乐器填充 - 使用 QWidgetAction + QCheckBox + QLabel 实现手指针效果和批量选择
        ins_menu = self.instrument_select.menu()
        ins_menu.setObjectName("FilterMenu")
        
        def ensure_ins_menu_style():
            ins_menu.setStyleSheet(self._menu_stylesheet)
        try:
            ins_menu.aboutToShow.disconnect()
        except:
            pass
        ins_menu.aboutToShow.connect(ensure_ins_menu_style)
        ins_menu.setStyleSheet(self._menu_stylesheet)
        ins_menu.clear()
        
        # 创建"全部"选项
        all_ins_widget = QWidget(ins_menu)
        all_ins_layout = QHBoxLayout(all_ins_widget)
        all_ins_layout.setContentsMargins(8, 4, 8, 4)
        
        all_ins_checkbox = QCheckBox(all_ins_widget)
        all_ins_checkbox.setChecked(True)
        all_ins_checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        all_ins_layout.addWidget(all_ins_checkbox)
        
        all_ins_label = QLabel("全部", all_ins_widget)
        all_ins_label.setCursor(Qt.CursorShape.PointingHandCursor)
        all_ins_label.setProperty("is_checked", True)
        all_ins_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        
        def create_ins_click_handler(cb):
            return lambda e: self._toggle_instrument_checkbox(cb)
        
        all_ins_label.mousePressEvent = create_ins_click_handler(all_ins_checkbox)
        all_ins_checkbox.stateChanged.connect(lambda state: self._on_instrument_checkbox_changed(-1, state))
        all_ins_layout.addWidget(all_ins_label)
        all_ins_layout.addStretch()
        
        all_ins_action = QWidgetAction(ins_menu)
        all_ins_action.setDefaultWidget(all_ins_widget)
        ins_menu.addAction(all_ins_action)
        
        # 存储全部复选框引用
        self.instrument_checkboxes = {-1: all_ins_checkbox}
        self.instrument_actions = {-1: all_ins_action}
        self.instrument_labels = {-1: all_ins_label}
        
        ins_menu.addSeparator()
        
        # 添加每个乐器选项
        for ins in self._instrument_cats:
            ins_widget = QWidget(ins_menu)
            ins_layout = QHBoxLayout(ins_widget)
            ins_layout.setContentsMargins(8, 4, 8, 4)
            
            checkbox = QCheckBox(ins_widget)
            checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
            checkbox.setChecked(False)  # 初始未选中，只有"全部"选中
            ins_layout.addWidget(checkbox)
            
            label = QLabel(ins, ins_widget)
            label.setCursor(Qt.CursorShape.PointingHandCursor)
            label.setProperty("is_checked", False)  # 默认未选中
            label.setStyleSheet("color: #333333;")  # 默认未选中状态使用黑色
            label.mousePressEvent = create_ins_click_handler(checkbox)
            ins_layout.addWidget(label)
            ins_layout.addStretch()
            
            action = QWidgetAction(ins_menu)
            action.setDefaultWidget(ins_widget)
            ins_menu.addAction(action)
            
            self.instrument_checkboxes[ins] = checkbox
            self.instrument_actions[ins] = action
            self.instrument_labels[ins] = label
            checkbox.stateChanged.connect(lambda state, ins_cat=ins: self._on_instrument_checkbox_changed(ins_cat, state))
        
        ins_menu.addSeparator()
        confirm_ins_widget = QWidget(ins_menu)
        confirm_ins_layout = QHBoxLayout(confirm_ins_widget)
        confirm_ins_layout.setContentsMargins(8, 2, 8, 2)
        
        confirm_ins_button = QPushButton("确认选择", confirm_ins_widget)
        confirm_ins_button.setStyleSheet("""
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
        confirm_ins_button.clicked.connect(ins_menu.hide)
        confirm_ins_layout.addWidget(confirm_ins_button)
        
        confirm_ins_action = QWidgetAction(ins_menu)
        confirm_ins_action.setDefaultWidget(confirm_ins_widget)
        ins_menu.addAction(confirm_ins_action)
        
        # 更新确认按钮引用
        self.instrument_select.confirm_action = confirm_ins_action

        # 确认按钮也触发一次文本刷新
        confirm_button.clicked.connect(lambda: self._update_band_text())
        confirm_ins_button.clicked.connect(lambda: self._update_instrument_text())
        
        # 初始化时更新文本显示（显示"全部"状态）
        self._update_band_text()
        self._update_instrument_text()
        
        # 人物填充将通过_update_character_menu方法实现，该方法会根据前两级筛选结果动态更新
        # 注意：_update_character_menu内部会连接char_menu的信号，所以这里不需要重复连接
        self._update_character_menu()

    def _update_character_menu(self):
        """根据前两级筛选结果更新成员菜单"""
        # 获取当前选中的乐队和乐器
        selected_bands = self._get_selected_bands()
        selected_instruments = self._get_selected_instruments()
        
        # 根据筛选条件过滤人物
        filtered_characters = []
        for ch in self._characters:
            band_match = not selected_bands or ch.get('band_id') in selected_bands
            instrument_match = not selected_instruments or ch.get('instrument_cat') in selected_instruments
            if band_match and instrument_match:
                filtered_characters.append(ch)
        
        # 重建成员菜单
        char_menu = self.character_select.menu()
        # 确保菜单对象名正确（apply样式）
        char_menu.setObjectName("FilterMenu")
        # 注意：MenuComboBox 内部已经设置了样式，我们不应该覆盖它
        # 如果需要强制应用样式，在 aboutToShow 时重新设置
        def ensure_char_menu_style():
            # 在菜单显示前确保样式被应用
            char_menu.setStyleSheet(self._menu_stylesheet)
        # 先断开之前的连接（如果存在）
        try:
            char_menu.aboutToShow.disconnect()
        except:
            pass
        char_menu.aboutToShow.connect(ensure_char_menu_style)
        # 立即设置一次样式
        char_menu.setStyleSheet(self._menu_stylesheet)
        
        # 在清除菜单之前，先断开所有信号连接并清理引用，避免访问已删除的对象
        if hasattr(self, 'character_checkboxes'):
            # 断开所有信号连接
            for checkbox in list(self.character_checkboxes.values()):
                try:
                    checkbox.stateChanged.disconnect()
                except:
                    pass
        
        # 清空引用字典（在clear之前）
        if hasattr(self, 'character_checkboxes'):
            self.character_checkboxes.clear()
        if hasattr(self, 'character_actions'):
            self.character_actions.clear()
        if hasattr(self, 'character_labels'):
            self.character_labels.clear()
        
        char_menu.clear()
        
        # 构建 band_id -> band_name 映射
        band_name_map = {b.get('id'): (b.get('name') or '') for b in self._bands}
        
        # 按乐队分组显示 - 使用 QWidgetAction + QCheckBox + QLabel 实现手指针效果和批量选择
        grouped = {}
        for ch in filtered_characters:
            grouped.setdefault(ch.get('band_id'), []).append(ch)
        
        # 初始化存储结构（已在上面的clear()前清空，这里重新创建）
        self.character_checkboxes = {}
        self.character_actions = {}
        self.character_labels = {}
        
        # 创建"全部"选项
        all_char_widget = QWidget(char_menu)
        all_char_layout = QHBoxLayout(all_char_widget)
        all_char_layout.setContentsMargins(8, 4, 8, 4)
        
        all_char_checkbox = QCheckBox(all_char_widget)
        all_char_checkbox.setChecked(True)
        all_char_checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        all_char_layout.addWidget(all_char_checkbox)
        
        all_char_label = QLabel("全部", all_char_widget)
        all_char_label.setCursor(Qt.CursorShape.PointingHandCursor)
        all_char_label.setProperty("is_checked", True)
        all_char_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        
        def create_char_click_handler(cb):
            return lambda e: self._toggle_character_checkbox(cb)
        
        all_char_label.mousePressEvent = create_char_click_handler(all_char_checkbox)
        all_char_checkbox.stateChanged.connect(lambda state: self._on_character_checkbox_changed(-1, state))
        all_char_layout.addWidget(all_char_label)
        all_char_layout.addStretch()
        
        all_char_action = QWidgetAction(char_menu)
        all_char_action.setDefaultWidget(all_char_widget)
        char_menu.addAction(all_char_action)
        
        self.character_checkboxes[-1] = all_char_checkbox
        self.character_actions[-1] = all_char_action
        self.character_labels[-1] = all_char_label
        
        char_menu.addSeparator()
        
        for band_id, members in grouped.items():
            # 分组标题
            title = QLabel(band_name_map.get(band_id, ''))
            title.setStyleSheet("font-weight: bold; color: #666666; padding: 4px 8px;")
            title_action = QWidgetAction(char_menu)
            title_action.setDefaultWidget(title)
            char_menu.addAction(title_action)
            
            # 成员项
            for ch in members:
                char_widget = QWidget(char_menu)
                char_layout = QHBoxLayout(char_widget)
                char_layout.setContentsMargins(8, 4, 8, 4)
                
                checkbox = QCheckBox(char_widget)
                checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
                checkbox.setChecked(False)  # 初始未选中，只有"全部"选中
                char_layout.addWidget(checkbox)
                
                label_text = f"{ch.get('name')} ({ch.get('nickname')})"
                label = QLabel(label_text, char_widget)
                label.setCursor(Qt.CursorShape.PointingHandCursor)
                label.setProperty("is_checked", False)  # 默认未选中
                label.setStyleSheet("color: #333333;")  # 默认未选中状态使用黑色
                label.mousePressEvent = create_char_click_handler(checkbox)
                char_layout.addWidget(label)
                char_layout.addStretch()
                
                action = QWidgetAction(char_menu)
                action.setDefaultWidget(char_widget)
                char_menu.addAction(action)
                
                nickname = ch.get('nickname')
                self.character_checkboxes[nickname] = checkbox
                self.character_actions[nickname] = action
                self.character_labels[nickname] = label
                checkbox.stateChanged.connect(lambda state, n=nickname: self._on_character_checkbox_changed(n, state))
            
            char_menu.addSeparator()
        
        char_menu.addSeparator()
        confirm_char_widget = QWidget(char_menu)
        confirm_char_layout = QHBoxLayout(confirm_char_widget)
        confirm_char_layout.setContentsMargins(8, 2, 8, 2)
        
        confirm_char_button = QPushButton("确认选择", confirm_char_widget)
        confirm_char_button.setStyleSheet("""
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
        confirm_char_button.clicked.connect(char_menu.hide)
        confirm_char_button.clicked.connect(lambda: self._update_character_text())
        confirm_char_layout.addWidget(confirm_char_button)
        
        confirm_char_action = QWidgetAction(char_menu)
        confirm_char_action.setDefaultWidget(confirm_char_widget)
        char_menu.addAction(confirm_char_action)
        
        # 更新确认按钮引用
        self.character_select.confirm_action = confirm_char_action
    
    def _get_selected_bands(self) -> set:
        """获取当前选中的乐队ID集合"""
        selected_bands = set()
        if hasattr(self, 'band_checkboxes'):
            for band_id, checkbox in list(self.band_checkboxes.items()):
                try:
                    if band_id != -1 and checkbox.isChecked():
                        selected_bands.add(band_id)
                except RuntimeError:
                    # 对象已被删除，跳过
                    continue
        return selected_bands
    
    def _get_selected_instruments(self) -> set:
        """获取当前选中的乐器类别集合"""
        selected_instruments = set()
        if hasattr(self, 'instrument_checkboxes'):
            for ins_cat, checkbox in list(self.instrument_checkboxes.items()):
                try:
                    if ins_cat != -1 and checkbox.isChecked():
                        selected_instruments.add(ins_cat)
                except RuntimeError:
                    # 对象已被删除，跳过
                    continue
        return selected_instruments

    def _toggle_band_checkbox(self, checkbox):
        """切换乐队复选框状态"""
        checkbox.setChecked(not checkbox.isChecked())
    
    def _toggle_instrument_checkbox(self, checkbox):
        """切换乐器复选框状态"""
        checkbox.setChecked(not checkbox.isChecked())
    
    def _toggle_character_checkbox(self, checkbox):
        """切换人物复选框状态"""
        checkbox.setChecked(not checkbox.isChecked())
    
    def _on_band_checkbox_changed(self, band_id, state):
        """乐队复选框状态改变时的处理"""
        if band_id == -1:  # "全部"选项
            if state == Qt.CheckState.Checked:
                # 如果选中"全部"，取消其他所有选项（使用blockSignals避免触发信号）
                for id, checkbox in list(self.band_checkboxes.items()):
                    try:
                        if id != -1:
                            checkbox.blockSignals(True)
                            checkbox.setChecked(False)
                            checkbox.blockSignals(False)
                            # 只更新标签样式，不触发其他复选框的更新
                            if id in self.band_labels:
                                self.band_labels[id].setProperty("is_checked", False)
                                self.band_labels[id].setStyleSheet("color: #333333;")
                    except RuntimeError:
                        continue
                
                # 更新"全部"标签样式
                if -1 in self.band_labels:
                    self.band_labels[-1].setProperty("is_checked", True)
                    self.band_labels[-1].setStyleSheet("color: #4CAF50; font-weight: bold;")
        else:  # 其他选项
            is_checked = state == Qt.CheckState.Checked
            # 检查是否有任何具体选项被选中
            any_specific_checked = False
            for id, checkbox in list(self.band_checkboxes.items()):
                try:
                    if id != -1 and checkbox.isChecked():
                        any_specific_checked = True
                        break
                except RuntimeError:
                    continue
            
            # 如果有任何具体选项被选中，取消"全部"选项
            if any_specific_checked:
                if -1 in self.band_checkboxes:
                    try:
                        self.band_checkboxes[-1].blockSignals(True)
                        self.band_checkboxes[-1].setChecked(False)
                        self.band_checkboxes[-1].blockSignals(False)
                        if -1 in self.band_labels:
                            self.band_labels[-1].setProperty("is_checked", False)
                            self.band_labels[-1].setStyleSheet("color: #333333;")
                    except RuntimeError:
                        pass
            else:
                # 如果没有任何具体选项被选中，选中"全部"选项
                if -1 in self.band_checkboxes:
                    try:
                        self.band_checkboxes[-1].blockSignals(True)
                        self.band_checkboxes[-1].setChecked(True)
                        self.band_checkboxes[-1].blockSignals(False)
                        if -1 in self.band_labels:
                            self.band_labels[-1].setProperty("is_checked", True)
                            self.band_labels[-1].setStyleSheet("color: #4CAF50; font-weight: bold;")
                    except RuntimeError:
                        pass
            
            # 更新当前选项样式
            if band_id in self.band_labels:
                try:
                    label = self.band_labels[band_id]
                    label.setProperty("is_checked", is_checked)
                    label.setStyleSheet("color: #4CAF50;" if is_checked else "color: #333333;")
                except RuntimeError:
                    pass
        
        self._update_band_text()
        self._update_character_menu()
    
    def _on_instrument_checkbox_changed(self, ins_cat, state):
        """乐器复选框状态改变时的处理"""
        if ins_cat == -1:  # "全部"选项
            if state == Qt.CheckState.Checked:
                # 如果选中"全部"，取消其他所有选项（使用blockSignals避免触发信号）
                for cat, checkbox in list(self.instrument_checkboxes.items()):
                    try:
                        if cat != -1:
                            checkbox.blockSignals(True)
                            checkbox.setChecked(False)
                            checkbox.blockSignals(False)
                            # 只更新标签样式，不触发其他复选框的更新
                            if cat in self.instrument_labels:
                                self.instrument_labels[cat].setProperty("is_checked", False)
                                self.instrument_labels[cat].setStyleSheet("color: #333333;")
                    except RuntimeError:
                        continue
                
                # 更新"全部"标签样式
                if -1 in self.instrument_labels:
                    self.instrument_labels[-1].setProperty("is_checked", True)
                    self.instrument_labels[-1].setStyleSheet("color: #4CAF50; font-weight: bold;")
        else:  # 其他选项
            is_checked = state == Qt.CheckState.Checked
            # 检查是否有任何具体选项被选中
            any_specific_checked = False
            for cat, checkbox in list(self.instrument_checkboxes.items()):
                try:
                    if cat != -1 and checkbox.isChecked():
                        any_specific_checked = True
                        break
                except RuntimeError:
                    continue
            
            # 如果有任何具体选项被选中，取消"全部"选项
            if any_specific_checked:
                if -1 in self.instrument_checkboxes:
                    try:
                        self.instrument_checkboxes[-1].blockSignals(True)
                        self.instrument_checkboxes[-1].setChecked(False)
                        self.instrument_checkboxes[-1].blockSignals(False)
                        if -1 in self.instrument_labels:
                            self.instrument_labels[-1].setProperty("is_checked", False)
                            self.instrument_labels[-1].setStyleSheet("color: #333333;")
                    except RuntimeError:
                        pass
            else:
                # 如果没有任何具体选项被选中，选中"全部"选项
                if -1 in self.instrument_checkboxes:
                    try:
                        self.instrument_checkboxes[-1].blockSignals(True)
                        self.instrument_checkboxes[-1].setChecked(True)
                        self.instrument_checkboxes[-1].blockSignals(False)
                        if -1 in self.instrument_labels:
                            self.instrument_labels[-1].setProperty("is_checked", True)
                            self.instrument_labels[-1].setStyleSheet("color: #4CAF50; font-weight: bold;")
                    except RuntimeError:
                        pass
            
            # 更新当前选项样式
            if ins_cat in self.instrument_labels:
                try:
                    label = self.instrument_labels[ins_cat]
                    label.setProperty("is_checked", is_checked)
                    label.setStyleSheet("color: #4CAF50;" if is_checked else "color: #333333;")
                except RuntimeError:
                    pass
        
        self._update_instrument_text()
        self._update_character_menu()
    
    def _on_character_checkbox_changed(self, nickname, state):
        """人物复选框状态改变时的处理"""
        try:
            if nickname == -1:  # "全部"选项
                if state == Qt.CheckState.Checked:
                    # 如果选中"全部"，取消其他所有选项（使用blockSignals避免触发信号）
                    for n, checkbox in list(self.character_checkboxes.items()):
                        try:
                            if n != -1:
                                checkbox.blockSignals(True)
                                checkbox.setChecked(False)
                                checkbox.blockSignals(False)
                                # 只更新标签样式，不触发其他复选框的更新
                                if n in self.character_labels:
                                    self.character_labels[n].setProperty("is_checked", False)
                                    self.character_labels[n].setStyleSheet("color: #333333;")
                        except RuntimeError:
                            continue
                    
                    # 更新"全部"标签样式
                    if -1 in self.character_labels:
                        self.character_labels[-1].setProperty("is_checked", True)
                        self.character_labels[-1].setStyleSheet("color: #4CAF50; font-weight: bold;")
            else:  # 其他选项
                is_checked = state == Qt.CheckState.Checked
                # 检查是否有任何具体选项被选中
                any_specific_checked = False
                for n, checkbox in list(self.character_checkboxes.items()):
                    try:
                        if n != -1 and checkbox.isChecked():
                            any_specific_checked = True
                            break
                    except RuntimeError:
                        continue
                
                # 如果有任何具体选项被选中，取消"全部"选项
                if any_specific_checked:
                    if -1 in self.character_checkboxes:
                        try:
                            self.character_checkboxes[-1].blockSignals(True)
                            self.character_checkboxes[-1].setChecked(False)
                            self.character_checkboxes[-1].blockSignals(False)
                            if -1 in self.character_labels:
                                self.character_labels[-1].setProperty("is_checked", False)
                                self.character_labels[-1].setStyleSheet("color: #333333;")
                        except RuntimeError:
                            pass
                else:
                    # 如果没有任何具体选项被选中，选中"全部"选项
                    if -1 in self.character_checkboxes:
                        try:
                            self.character_checkboxes[-1].blockSignals(True)
                            self.character_checkboxes[-1].setChecked(True)
                            self.character_checkboxes[-1].blockSignals(False)
                            if -1 in self.character_labels:
                                self.character_labels[-1].setProperty("is_checked", True)
                                self.character_labels[-1].setStyleSheet("color: #4CAF50; font-weight: bold;")
                        except RuntimeError:
                            pass
                
                # 更新当前选项样式
                if nickname in self.character_labels:
                    try:
                        label = self.character_labels[nickname]
                        label.setProperty("is_checked", is_checked)
                        label.setStyleSheet("color: #4CAF50;" if is_checked else "color: #333333;")
                    except RuntimeError:
                        pass
            
            self._update_character_text()
        except RuntimeError:
            # 对象已被删除，不更新文本
            pass

    def _gather_selected_nicknames(self) -> list:
        """收集选中的昵称列表"""
        nicknames = []
        # 优先读取直接选中的人物
        if hasattr(self, 'character_checkboxes'):
            for nickname, checkbox in list(self.character_checkboxes.items()):
                try:
                    if nickname != -1 and checkbox.isChecked():
                        nicknames.append(nickname)
                except RuntimeError:
                    # 对象已被删除，跳过
                    continue
        
        if nicknames:
            self.character_select.setCurrentText("已选人物: " + ", ".join(nicknames[:3]) + ("..." if len(nicknames) > 3 else ""))
            return nicknames

        # 若未选人物，按乐队/乐器自动选择
        band_ids = self._get_selected_bands()
        ins_cats = self._get_selected_instruments()
        
        if band_ids or ins_cats:
            for ch in self._characters:
                if ch.get('nickname'):
                    if band_ids and ch.get('band_id') not in band_ids:
                        continue
                    if ins_cats and ch.get('instrument_cat') not in ins_cats:
                        continue
                    nicknames.append(ch['nickname'])
            self.character_select.setCurrentText("人物(按筛选自动选择)")
        return nicknames

    def _update_band_text(self):
        """更新乐队选择文本"""
        if hasattr(self, 'band_checkboxes') and hasattr(self, 'band_labels'):
            # 检查是否只有"全部"选中
            if -1 in self.band_checkboxes:
                try:
                    all_checked = self.band_checkboxes[-1].isChecked()
                    if all_checked:
                        # 检查是否有其他选项被选中
                        any_specific_checked = False
                        for band_id, checkbox in list(self.band_checkboxes.items()):
                            try:
                                if band_id != -1 and checkbox.isChecked():
                                    any_specific_checked = True
                                    break
                            except RuntimeError:
                                continue
                        
                        if not any_specific_checked:
                            # 只有"全部"选中
                            self.band_select.setCurrentText("全部乐队")
                            return
                except RuntimeError:
                    pass
            
            names = []
            for band_id, checkbox in list(self.band_checkboxes.items()):
                try:
                    if band_id != -1 and checkbox.isChecked():
                        if band_id in self.band_labels:
                            try:
                                # 从label获取文本
                                label_text = self.band_labels[band_id].text()
                                names.append(label_text)
                            except RuntimeError:
                                # 对象已被删除，跳过
                                continue
                except RuntimeError:
                    # 复选框对象已被删除，跳过
                    continue
            
            if names:
                if len(names) <= 2:
                    text = ", ".join(names)
                else:
                    text = "已选乐队: " + ", ".join(names[:3]) + "..."
            else:
                text = "选择乐队 (可多选)"
            self.band_select.setCurrentText(text)
        else:
            self.band_select.setCurrentText("选择乐队 (可多选)")

    def _update_instrument_text(self):
        """更新乐器选择文本"""
        if hasattr(self, 'instrument_checkboxes') and hasattr(self, 'instrument_labels'):
            # 检查是否只有"全部"选中
            if -1 in self.instrument_checkboxes:
                try:
                    all_checked = self.instrument_checkboxes[-1].isChecked()
                    if all_checked:
                        # 检查是否有其他选项被选中
                        any_specific_checked = False
                        for ins_cat, checkbox in list(self.instrument_checkboxes.items()):
                            try:
                                if ins_cat != -1 and checkbox.isChecked():
                                    any_specific_checked = True
                                    break
                            except RuntimeError:
                                continue
                        
                        if not any_specific_checked:
                            # 只有"全部"选中
                            self.instrument_select.setCurrentText("全部乐器")
                            return
                except RuntimeError:
                    pass
            
            names = []
            for ins_cat, checkbox in list(self.instrument_checkboxes.items()):
                try:
                    if ins_cat != -1 and checkbox.isChecked():
                        if ins_cat in self.instrument_labels:
                            try:
                                label_text = self.instrument_labels[ins_cat].text()
                                names.append(label_text)
                            except RuntimeError:
                                # 对象已被删除，跳过
                                continue
                except RuntimeError:
                    # 复选框对象已被删除，跳过
                    continue
            
            if names:
                if len(names) <= 2:
                    text = ", ".join(names)
                else:
                    text = "已选乐器: " + ", ".join(names[:3]) + "..."
            else:
                text = "选择乐器 (可多选)"
            self.instrument_select.setCurrentText(text)
        else:
            self.instrument_select.setCurrentText("选择乐器 (可多选)")

    def _update_character_text(self):
        """更新人物选择文本"""
        if hasattr(self, 'character_checkboxes') and hasattr(self, 'character_labels'):
            # 检查是否只有"全部"选中
            if -1 in self.character_checkboxes:
                try:
                    all_checked = self.character_checkboxes[-1].isChecked()
                    if all_checked:
                        # 检查是否有其他选项被选中
                        any_specific_checked = False
                        for nickname, checkbox in list(self.character_checkboxes.items()):
                            try:
                                if nickname != -1 and checkbox.isChecked():
                                    any_specific_checked = True
                                    break
                            except RuntimeError:
                                continue
                        
                        if not any_specific_checked:
                            # 只有"全部"选中
                            self.character_select.setCurrentText("全部人物")
                            return
                except RuntimeError:
                    pass
            
            names = []
            for nickname, checkbox in list(self.character_checkboxes.items()):
                try:
                    # 检查对象是否仍然有效
                    if nickname != -1 and checkbox.isChecked():
                        if nickname in self.character_labels:
                            label = self.character_labels[nickname]
                            try:
                                label_text = label.text()
                                # 提取人物名称部分（格式：名称 (nickname)）
                                if "(" in label_text:
                                    name_part = label_text.split("(")[0].strip()
                                    names.append(name_part)
                                else:
                                    names.append(label_text)
                            except RuntimeError:
                                # 对象已被删除，跳过
                                continue
                except RuntimeError:
                    # 复选框对象已被删除，跳过
                    continue
            
            if names:
                if len(names) <= 2:
                    text = ", ".join(names)
                else:
                    text = "已选人物: " + ", ".join(names[:3]) + "..."
            else:
                text = "选择人物 (可多选)"
            self.character_select.setCurrentText(text)
        else:
            self.character_select.setCurrentText("选择人物 (可多选)")

    def _normalize_instrument(self, text: str) -> str:
        t = text.lower()
        if any(k in t for k in ['guitar', 'ギター', '吉他']):
            return '吉他'
        if any(k in t for k in ['bass', 'ベース', '贝斯']):
            return '贝斯'
        if any(k in t for k in ['drums', 'ドラム', '鼓']):
            return '鼓'
        if any(k in t for k in ['keyboard', 'キーボード', '键盘']):
            return '键盘'
        if any(k in t for k in ['vocals', 'ボーカル', '主唱']):
            return '主唱'
        if any(k in t for k in ['dj']):
            return 'DJ'
        if any(k in t for k in ['violin', 'ヴァイオリン', '小提琴']):
            return '小提琴'
        return ''


