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
        background: #F5F7FA;
        color: #666666;
        border: 1px solid transparent;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        padding: 8px 16px;
        margin-right: 2px;
    }
    QTabBar::tab:selected {
        background: #FFFFFF;
        color: #E85D9E;
        border-color: #E1E6EF;
        border-bottom-color: transparent;
    }
    QTabBar::tab:hover:!selected {
        background: #EDF1F5;
        color: #333333;
    }
    """


def get_groupbox_styles() -> str:
    return """
    QGroupBox {
        border: 1px solid #E1E6EF;
        border-radius: 8px;
        margin-top: 12px;
        padding-top: 12px;
        font-weight: 500;
        color: #333333;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 8px;
        color: #E85D9E;
    }
    """


def get_voice_page_styles() -> str:
    return """
    QWidget {
        background: #F5F7FA;
    }
    QListWidget {
        background: #FFFFFF;
        border: 1px solid #E1E6EF;
        border-radius: 6px;
        padding: 4px;
    }
    QListWidgetItem {
        padding: 6px;
        border-radius: 4px;
        margin: 2px;
    }
    QListWidgetItem:hover {
        background: #F0F4F8;
    }
    QListWidgetItem:selected {
        background: #E85D9E;
        color: #FFFFFF;
    }
    """


def build_stylesheet(*parts: str) -> str:
    """组合多个样式字符串"""
    return "\n".join(filter(None, parts))

