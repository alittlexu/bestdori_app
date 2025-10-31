from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar,
    QFileDialog, QFrame, QMessageBox, QScrollArea, QTabWidget, QGroupBox,
    QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon
try:
    from src.gui.styles.theme import (
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
        self._instrument_cats = ['吉他', '贝斯', '鼓', '键盘', '主唱', 'DJ', '小提琴']
        self._bands = []
        self._characters = []
        self._init_ui()
        self._load_character_data()
        self._populate_filters()

    def _init_ui(self):
        self.setObjectName("VoiceDownloadPage")
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # 顶部标题与目录/控制区
        header = QVBoxLayout()
        main_layout.addLayout(header)

        title = QLabel("卡面语音获取")
        title.setObjectName("CardVoiceTitle")
        header.addWidget(title)

        ops = QHBoxLayout()
        header.addLayout(ops)

        self.dir_label = QLabel("保存目录: 未选择")
        ops.addWidget(self.dir_label, 1)

        self.choose_btn = QPushButton("选择保存目录")
        self.choose_btn.clicked.connect(self._on_choose_dir)
        ops.addWidget(self.choose_btn)

        self.stop_btn = QPushButton("终止下载")
        self.stop_btn.setVisible(False)
        self.stop_btn.clicked.connect(self._on_stop)
        ops.addWidget(self.stop_btn)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(line)

        # 子导航（四个模块）
        tabs = QTabWidget()
        tabs.setObjectName("VoiceTabs")
        main_layout.addWidget(tabs, 1)

        # 1) 卡面语音获取（含筛选区 + 状态/日志）
        self.card_voice_tab = QWidget()
        self.card_voice_tab.setObjectName("CardVoiceTab")
        tabs.addTab(self.card_voice_tab, "卡面语音获取")
        card_layout = QVBoxLayout(self.card_voice_tab)

        # 筛选区：复用卡页的多选控件
        filter_group = QGroupBox("筛选")
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
        self.reset_btn = QPushButton("重置筛选")
        self.reset_btn.setIcon(QIcon(os.path.join(icon_path, 'refresh.png')))
        self.reset_btn.clicked.connect(self._on_reset_filters)
        filter_layout.addWidget(self.reset_btn)

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
        self.pause_all_btn.clicked.connect(self._on_stop)  # 暂以停止实现
        ctrl_row.addWidget(self.pause_all_btn)
        self.cancel_all_btn = QPushButton("全部取消")
        self.cancel_all_btn.clicked.connect(self._on_stop)
        ctrl_row.addWidget(self.cancel_all_btn)
        ctrl_row.addStretch(1)

        # 启动下载按钮放置在筛选与进度之间更直观
        self.start_btn = QPushButton("开始下载")
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

    def _on_choose_dir(self):
        directory = QFileDialog.getExistingDirectory(self, "选择保存目录", os.path.expanduser("~/Music"))
        if directory:
            self._save_dir = directory
            self.dir_label.setText(f"保存目录: {directory}")

    def _on_start(self):
        if not self._save_dir:
            QMessageBox.warning(self, "提示", "请先选择保存目录")
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

        self._thread = VoiceDownloadThread(nicknames, mode, to_wav, self._save_dir)
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
        if self._thread and self._thread.isRunning():
            self._thread.terminate()
            self._thread.wait()
        self.start_btn.setEnabled(True)
        self.stop_btn.setVisible(False)
        self.progress.setVisible(False)
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
        self.start_btn.setEnabled(True)
        self.stop_btn.setVisible(False)
        if result.get('success'):
            self._update_summary(done=True)
            QMessageBox.information(self, "完成", "语音下载完成（占位统计）")
        else:
            msg = result.get('message', '未知错误')
            QMessageBox.warning(self, "失败", msg)

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
        # 乐队填充
        band_menu = self.band_select.menu()
        band_menu.clear()
        for band in self._bands:
            act = band_menu.addAction(band.get('name') or '')
            act.setCheckable(True)
            act.setData({'type': 'band', 'id': band.get('id')})
        band_menu.addSeparator()
        band_menu.addAction(self.band_select.confirm_action)

        # 乐器填充
        ins_menu = self.instrument_select.menu()
        ins_menu.clear()
        for ins in self._instrument_cats:
            act = ins_menu.addAction(ins)
            act.setCheckable(True)
            act.setData({'type': 'instrument', 'cat': ins})
        ins_menu.addSeparator()
        ins_menu.addAction(self.instrument_select.confirm_action)

        # 人物填充（分组：按乐队添加分组标题，再列出人物）
        char_menu = self.character_select.menu()
        char_menu.clear()
        # 构建 band_id -> band_name 映射
        band_name_map = {b.get('id'): (b.get('name') or '') for b in self._bands}
        # 分组
        from PyQt6.QtWidgets import QLabel, QWidgetAction
        grouped = {}
        for ch in self._characters:
            grouped.setdefault(ch.get('band_id'), []).append(ch)
        for band_id, members in grouped.items():
            # 分组标题
            title = QLabel(band_name_map.get(band_id, ''))
            title_action = QWidgetAction(char_menu)
            title_action.setDefaultWidget(title)
            char_menu.addAction(title_action)
            # 成员项
            for ch in members:
                label = f"{ch.get('name')} ({ch.get('nickname')})"
                act = char_menu.addAction(label)
                act.setCheckable(True)
                act.setData({'type': 'character', 'nickname': ch.get('nickname'), 'band_id': ch.get('band_id'), 'instrument_cat': ch.get('instrument_cat')})
            char_menu.addSeparator()
        char_menu.addSeparator()
        char_menu.addAction(self.character_select.confirm_action)

        band_menu.triggered.connect(self._on_band_menu_changed)
        ins_menu.triggered.connect(self._on_instrument_menu_changed)
        char_menu.triggered.connect(self._on_character_menu_changed)
        # 确认按钮也触发一次文本刷新
        self.band_select.confirm_action.triggered.connect(lambda: self._update_band_text())
        self.instrument_select.confirm_action.triggered.connect(lambda: self._update_instrument_text())
        self.character_select.confirm_action.triggered.connect(lambda: self._update_character_text())

    def _rebuild_character_menu(self):
        # 收集选中的乐队与乐器
        band_ids = set()
        band_menu = self.band_select.menu()
        for a in band_menu.actions():
            if a.isCheckable() and a.isChecked():
                data = a.data() or {}
                if data.get('type') == 'band':
                    band_ids.add(data.get('id'))
        ins_cats = set()
        ins_menu = self.instrument_select.menu()
        for a in ins_menu.actions():
            if a.isCheckable() and a.isChecked():
                data = a.data() or {}
                if data.get('type') == 'instrument' and data.get('cat'):
                    ins_cats.add(data.get('cat'))

        # 过滤角色
        filtered = []
        for ch in self._characters:
            if band_ids and ch.get('band_id') not in band_ids:
                continue
            if ins_cats and ch.get('instrument_cat') not in ins_cats:
                continue
            filtered.append(ch)

        # 重建菜单
        char_menu = self.character_select.menu()
        char_menu.clear()
        from PyQt6.QtWidgets import QLabel, QWidgetAction
        band_name_map = {b.get('id'): (b.get('name') or '') for b in self._bands}
        grouped = {}
        for ch in filtered:
            grouped.setdefault(ch.get('band_id'), []).append(ch)
        for band_id, members in grouped.items():
            title = QLabel(band_name_map.get(band_id, ''))
            title_action = QWidgetAction(char_menu)
            title_action.setDefaultWidget(title)
            char_menu.addAction(title_action)
            for ch in members:
                label = f"{ch.get('name')} ({ch.get('nickname')})"
                act = char_menu.addAction(label)
                act.setCheckable(True)
                act.setData({'type': 'character', 'nickname': ch.get('nickname'), 'band_id': ch.get('band_id'), 'instrument_cat': ch.get('instrument_cat')})
            char_menu.addSeparator()
        char_menu.addSeparator()
        char_menu.addAction(self.character_select.confirm_action)
        char_menu.triggered.connect(self._on_character_menu_changed)
        self._update_character_text()

    def _on_band_menu_changed(self, act):
        self._update_band_text()
        self._rebuild_character_menu()

    def _gather_selected_nicknames(self) -> list:
        # 优先读取直接选中的人物
        char_menu = self.character_select.menu()
        nicknames = []
        for a in char_menu.actions():
            if a.isCheckable() and a.isChecked():
                data = a.data() or {}
                if data.get('type') == 'character' and data.get('nickname'):
                    nicknames.append(data['nickname'])
        if nicknames:
            self.character_select.setCurrentText("已选人物: " + ", ".join(nicknames[:3]) + ("..." if len(nicknames) > 3 else ""))
            return nicknames

        # 若未选人物，按乐队/乐器自动选择
        band_ids = set()
        band_menu = self.band_select.menu()
        for a in band_menu.actions():
            if a.isCheckable() and a.isChecked():
                data = a.data() or {}
                if data.get('type') == 'band':
                    band_ids.add(data.get('id'))
        ins_cats = set()
        if hasattr(self, 'instrument_select'):
            ins_menu = self.instrument_select.menu()
            for a in ins_menu.actions():
                if a.isCheckable() and a.isChecked():
                    data = a.data() or {}
                    if data.get('type') == 'instrument' and data.get('cat'):
                        ins_cats.add(data.get('cat'))
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

    def _on_instrument_menu_changed(self, act):
        self._update_instrument_text()
        self._rebuild_character_menu()

    def _on_character_menu_changed(self, act):
        self._update_character_text()

    def _update_band_text(self):
        band_menu = self.band_select.menu()
        names = [a.text() for a in band_menu.actions() if a.isCheckable() and a.isChecked()]
        text = "已选乐队: " + ", ".join(names[:3]) + ("..." if len(names) > 3 else "") if names else "选择乐队 (可多选)"
        self.band_select.setCurrentText(text)

    def _update_instrument_text(self):
        ins_menu = self.instrument_select.menu()
        names = [a.text() for a in ins_menu.actions() if a.isCheckable() and a.isChecked()]
        text = "已选乐器: " + ", ".join(names[:3]) + ("..." if len(names) > 3 else "") if names else "选择乐器 (可多选)"
        self.instrument_select.setCurrentText(text)

    def _update_character_text(self):
        char_menu = self.character_select.menu()
        names = []
        for a in char_menu.actions():
            d = a.data() or {}
            if a.isCheckable() and a.isChecked() and d.get('type') == 'character':
                names.append(a.text())
        text = "已选人物: " + ", ".join(names[:3]) + ("..." if len(names) > 3 else "") if names else "选择人物 (可多选)"
        self.character_select.setCurrentText(text)

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


