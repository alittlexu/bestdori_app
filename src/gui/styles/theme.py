"""全局主题样式定义（设计语言）。

主色 #E85D9E（粉）；文字 #333；背景 #F5F7FA；圆角 6-8px。
"""


def get_common_styles() -> str:
    return """
    QLabel { color: #333333; font-size: 13px; }
    QPushButton {
        background: #E85D9E;
        border: 1px solid #C34E84;
        border-radius: 6px;
        padding: 6px 12px;
        color: #ffffff;
        font-weight: 500;
    }
    QPushButton:hover { background: #D35490; }
    QPushButton:pressed { background: #B3487D; }

    QProgressBar {
        border: 1px solid #E1E6EF;
        border-radius: 6px;
        background: #FFFFFF;
        height: 14px;
    }
    QProgressBar::chunk { background-color: #E85D9E; border-radius: 6px; }

    QScrollArea { background: transparent; border: none; }
    QFrame[frameShape="4"] { color: #e6e6e6; }

    QComboBox, QLineEdit {
        background: #FFFFFF;
        color: #333333;
        border: 1px solid #E1E6EF;
        border-radius: 6px;
        padding: 6px 8px;
    }
    QComboBox:hover, QLineEdit:hover { border-color: #E85D9E; }
    QComboBox:focus, QLineEdit:focus { border-color: #E85D9E; }
    """


def get_tabs_styles() -> str:
    return """
    QTabWidget::pane {
        border: 1px solid #E1E6EF;
        background: rgba(255,255,255,235);
        border-radius: 8px;
    }
    QTabBar::tab {
        background: rgba(245,247,250,1);
        border: 1px solid #E1E6EF;
        padding: 8px 14px;
        margin-right: 4px;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        color: #333333;
        font-weight: 500;
    }
    QTabBar::tab:selected {
        background: #FFFFFF;
        border-bottom-color: #FFFFFF;
        color: #222222;
    }
    """


def get_groupbox_styles() -> str:
    return """
    QGroupBox {
        background: rgba(255,255,255,235);
        border: 1px solid #E1E6EF;
        border-radius: 8px;
        margin-top: 12px;
        padding-top: 12px;
    }
    QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
    """


def get_voice_page_styles() -> str:
    return """
    QWidget#VoiceDownloadPage { background-color: transparent; }
    QWidget#CardVoiceTab { background: rgba(255,255,255,0); }
    QWidget#LogContainer { background: transparent; }

    QListWidget#VoiceTaskList {
        background: #FFFFFF;
        border: 1px solid #E1E6EF;
        border-radius: 8px;
        padding: 6px;
    }
    QListWidget#VoiceTaskList::item { padding: 6px 8px; }
    QListWidget#VoiceTaskList::item:selected { background: #FFE6F0; color: #E85D9E; }

    /* MenuComboBox 内部 QToolButton */
    QToolButton {
        background: #FFFFFF;
        border: 1px solid #E1E6EF;
        border-radius: 6px;
        padding: 6px 10px;
        color: #333333;
        min-width: 170px;
    }
    QToolButton:hover { border-color: #E85D9E; }

    /* 统一筛选下拉菜单颜色（对象名 FilterMenu） */
    QMenu#FilterMenu {
        background-color: #FFFFFF;
        border: 1px solid #E1E6EF;
        border-radius: 6px;
        padding: 4px 0;
        cursor: pointer;
    }
    QMenu#FilterMenu::item {
        padding: 6px 12px 6px 32px;
        color: #333333;
        background: transparent;
        min-height: 15px;
        cursor: pointer;
    }
    /* 方形圆角框指示器（左侧） */
    QMenu#FilterMenu::indicator {
        width: 16px;
        height: 16px;
        border: 1px solid #E1E6EF;
        border-radius: 4px;
        background: #FFFFFF;
        margin-left: 8px;
        margin-right: 8px;
    }
    /* 选中时填充颜色 rgb(135, 206, 250) */
    QMenu#FilterMenu::indicator:checked {
        background: rgb(135, 206, 250);
        border-color: rgb(135, 206, 250);
    }
    /* 悬停效果：手指针和背景颜色 rgb(135, 206, 250) */
    QMenu#FilterMenu::item:hover {
        background: rgb(135, 206, 250);
        color: #FFFFFF;
        cursor: pointer;
    }
    QMenu#FilterMenu::item:selected {
        background: rgb(135, 206, 250);
        color: #FFFFFF;
    }
    QMenu#FilterMenu::separator {
        height: 1px;
        background: #F0F2F5;
        margin: 4px 0;
    }
    """


def build_stylesheet(*parts: str) -> str:
    return "\n".join(part for part in parts if part)


