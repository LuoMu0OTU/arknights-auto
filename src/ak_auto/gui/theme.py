"""界面主题：设计令牌 + QSS + 调色板（AGENTS.md 第 4 节）。

- 深色为默认，浅色可选（config.ui.theme = dark|light，切换不重置其它配置）。
- 视觉基调：明日方舟式「深色 + 琥珀金」，卡片化布局、细边框、柔和层次。
- 所有颜色/圆角/字号集中在 TOKENS，QSS 与调色板都由它生成，避免散落硬编码。
"""
from __future__ import annotations

from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QApplication

# ---- 设计令牌 ----
DARK: dict[str, str] = {
    "bg": "#0f1013",
    "sidebar": "#121418",
    "surface": "#16181d",
    "surface_alt": "#1d2026",
    "elevated": "#22252c",
    "border": "#2a2e35",
    "border_hi": "#3a3f48",
    "text": "#e9eaec",
    "text_dim": "#c2c6cc",
    "muted": "#8a9099",
    "primary": "#e8a33d",
    "primary_hover": "#f4b45a",
    "primary_press": "#cf8f2e",
    "on_primary": "#1a1206",
    "success": "#4cbb5e",
    "danger": "#ef5f57",
    "warning": "#e0a225",
    "shadow": "#000000",
    "log_bg": "#101216",
    "log_fg": "#b8c0ca",
}

LIGHT: dict[str, str] = {
    "bg": "#f2f4f7",
    "sidebar": "#ffffff",
    "surface": "#ffffff",
    "surface_alt": "#eef1f5",
    "elevated": "#ffffff",
    "border": "#dde1e7",
    "border_hi": "#c4cad3",
    "text": "#1a1d22",
    "text_dim": "#3d434b",
    "muted": "#6b7280",
    "primary": "#b8761a",
    "primary_hover": "#d18a24",
    "primary_press": "#9c6414",
    "on_primary": "#fffaf0",
    "success": "#2f9e44",
    "danger": "#d3362c",
    "warning": "#b8860b",
    "shadow": "#b9c0c9",
    "log_bg": "#f7f8fa",
    "log_fg": "#33383f",
}

# 圆角/间距/字号（与主题无关）
GEOMETRY = {
    "radius": "10px",
    "radius_sm": "7px",
    "radius_lg": "14px",
    "font_family": '"Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI", sans-serif',
    "mono_family": '"Cascadia Mono", "Consolas", "Courier New", monospace',
    "fs_base": "13px",
    "fs_sm": "12px",
    "fs_h1": "22px",
    "fs_h2": "16px",
}

TOKENS: dict[str, str] = {}  # 兼容旧引用：当前生效令牌


def tokens_for(mode: str) -> dict[str, str]:
    return dict(DARK if mode == "light" and False else (LIGHT if mode == "light" else DARK))


_QSS = """
/* ---------- 基础 ---------- */
* { font-family: %(font_family)s; }
QWidget { background: %(bg)s; color: %(text)s; font-size: %(fs_base)s; }
QMainWindow, QDialog { background: %(bg)s; }
QToolTip {
    background: %(elevated)s; color: %(text)s; border: 1px solid %(border_hi)s;
    border-radius: %(radius_sm)s; padding: 5px 8px;
}
QStatusBar { background: %(surface)s; color: %(muted)s; border-top: 1px solid %(border)s; }
QStatusBar::item { border: none; }

/* ---------- 侧边栏 ---------- */
QWidget#sidebar { background: %(sidebar)s; border-right: 1px solid %(border)s; }
QLabel#brand { font-size: 15px; font-weight: 800; letter-spacing: 1px; color: %(text)s; }
QLabel#brandAccent { font-size: 15px; font-weight: 800; letter-spacing: 1px; color: %(primary)s; }
QLabel#version { color: %(muted)s; font-size: %(fs_sm)s; }
QListWidget#nav {
    background: transparent; border: none; outline: none; padding: 6px 10px;
}
QListWidget#nav::item {
    color: %(text_dim)s; padding: 10px 14px; margin: 2px 0;
    border-radius: %(radius_sm)s; border-left: 3px solid transparent;
}
QListWidget#nav::item:hover { background: %(surface_alt)s; color: %(text)s; }
QListWidget#nav::item:selected {
    background: %(surface_alt)s; color: %(primary)s;
    border-left: 3px solid %(primary)s; font-weight: 600;
}
QPushButton#modeBtn {
    text-align: left; padding: 9px 14px; color: %(muted)s;
    background: transparent; border: 1px solid %(border)s; border-radius: %(radius_sm)s;
}
QPushButton#modeBtn:hover { color: %(primary)s; border-color: %(primary)s; }

/* ---------- 卡片与文字层级 ---------- */
QFrame#card {
    background: %(surface)s; border: 1px solid %(border)s;
    border-radius: %(radius)s;
}
QFrame#cardFlat { background: %(surface)s; border: 1px solid %(border)s; }
QLabel { background: transparent; }
QLabel#h1 { font-size: %(fs_h1)s; font-weight: 800; color: %(text)s; }
QLabel#h2 { font-size: %(fs_h2)s; font-weight: 700; color: %(text)s; }
QLabel#title { font-size: 18px; font-weight: 700; }
QLabel#muted { color: %(muted)s; }
QLabel#dim { color: %(text_dim)s; }
QLabel#caption { color: %(muted)s; font-size: %(fs_sm)s; }
QLabel#accent { color: %(primary)s; font-weight: 600; }
QLabel#update {
    color: %(primary)s; background: rgba(232, 163, 61, 0.10);
    border: 1px solid rgba(232, 163, 61, 0.35); border-radius: %(radius_sm)s;
    padding: 7px 10px;
}
QLabel#badgeOk {
    color: %(success)s; background: rgba(76, 187, 94, 0.12);
    border-radius: %(radius_sm)s; padding: 2px 8px; font-size: %(fs_sm)s;
}
QLabel#badgeWarn {
    color: %(warning)s; background: rgba(224, 162, 37, 0.12);
    border-radius: %(radius_sm)s; padding: 2px 8px; font-size: %(fs_sm)s;
}
QLabel#badgeBad {
    color: %(danger)s; background: rgba(239, 95, 87, 0.12);
    border-radius: %(radius_sm)s; padding: 2px 8px; font-size: %(fs_sm)s;
}

/* ---------- 按钮 ---------- */
QPushButton {
    background: %(surface_alt)s; color: %(text)s;
    border: 1px solid %(border)s; border-radius: %(radius_sm)s;
    padding: 8px 16px; min-height: 16px;
}
QPushButton:hover { border-color: %(border_hi)s; background: %(elevated)s; }
QPushButton:pressed { background: %(surface)s; }
QPushButton:disabled { color: %(muted)s; background: %(surface)s; border-color: %(border)s; }
QPushButton:focus { border: 1px solid %(primary)s; }
QPushButton#primary:focus { border: 2px solid %(on_primary)s; }
QPushButton#primary {
    background: %(primary)s; color: %(on_primary)s;
    border: 1px solid %(primary)s; font-weight: 700;
}
QPushButton#primary:hover { background: %(primary_hover)s; border-color: %(primary_hover)s; }
QPushButton#primary:pressed { background: %(primary_press)s; }
QPushButton#primary:disabled { background: %(surface_alt)s; color: %(muted)s; border-color: %(border)s; }
QPushButton#danger {
    background: transparent; color: %(danger)s; border: 1px solid rgba(239, 95, 87, 0.5);
}
QPushButton#danger:hover { background: rgba(239, 95, 87, 0.10); border-color: %(danger)s; }
QPushButton#danger:disabled { color: %(muted)s; border-color: %(border)s; }
QPushButton#ghost {
    background: transparent; border: 1px solid transparent; color: %(muted)s;
}
QPushButton#ghost:hover { color: %(text)s; background: %(surface_alt)s; }
QPushButton#chip {
    background: %(surface_alt)s; border: 1px solid %(border)s;
    border-radius: 14px; padding: 6px 14px; color: %(text_dim)s;
}
QPushButton#chip:hover { border-color: %(primary)s; color: %(primary)s; }
QPushButton#bigPrimary {
    background: %(primary)s; color: %(on_primary)s; border: none;
    border-radius: %(radius)s; padding: 13px 26px; font-size: 14px; font-weight: 800;
}
QPushButton#bigPrimary:hover { background: %(primary_hover)s; }
QPushButton#bigPrimary:disabled { background: %(surface_alt)s; color: %(muted)s; }

/* ---------- 输入控件 ---------- */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QPlainTextEdit, QTextEdit {
    background: %(surface_alt)s; color: %(text)s;
    border: 1px solid %(border)s; border-radius: %(radius_sm)s;
    padding: 7px 10px; selection-background-color: %(primary)s; selection-color: %(on_primary)s;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus,
QPlainTextEdit:focus, QTextEdit:focus { border: 1px solid %(primary)s; }
QLineEdit:disabled, QComboBox:disabled { color: %(muted)s; }
QComboBox::drop-down { border: none; width: 22px; }
QComboBox QAbstractItemView {
    background: %(elevated)s; border: 1px solid %(border_hi)s;
    border-radius: %(radius_sm)s; selection-background-color: %(surface_alt)s;
    selection-color: %(primary)s; outline: none;
}
QPlainTextEdit#log {
    background: %(log_bg)s; color: %(log_fg)s;
    font-family: %(mono_family)s; font-size: 12px;
    border: 1px solid %(border)s; border-radius: %(radius_sm)s; padding: 8px;
}

/* ---------- 复选 / 单选 ---------- */
QCheckBox, QRadioButton { spacing: 8px; color: %(text)s; background: transparent; }
QCheckBox::indicator, QRadioButton::indicator {
    width: 17px; height: 17px; border-radius: 5px;
    border: 1px solid %(border_hi)s; background: %(surface_alt)s;
}
QCheckBox::indicator:hover, QRadioButton::indicator:hover { border-color: %(primary)s; }
QCheckBox::indicator:checked {
    background: %(primary)s; border-color: %(primary)s;
    image: none;
}
QRadioButton::indicator { border-radius: 9px; }
QRadioButton::indicator:checked { background: %(primary)s; border-color: %(primary)s; }

/* ---------- 进度条 ---------- */
QProgressBar {
    background: %(surface_alt)s; border: 1px solid %(border)s;
    border-radius: %(radius_sm)s; height: 10px; text-align: center; color: %(text)s;
}
QProgressBar::chunk {
    background: %(primary)s; border-radius: %(radius_sm)s;
}

/* ---------- 列表 / 表格 / 树 ---------- */
QListWidget, QTreeWidget, QTableWidget {
    background: %(surface)s; border: 1px solid %(border)s;
    border-radius: %(radius_sm)s; outline: none;
}
QListWidget::item { padding: 7px 10px; border-radius: %(radius_sm)s; }
QListWidget::item:hover { background: %(surface_alt)s; }
QListWidget::item:selected { background: %(surface_alt)s; color: %(primary)s; }
QHeaderView::section {
    background: %(surface_alt)s; color: %(muted)s;
    border: none; border-bottom: 1px solid %(border)s; padding: 6px 8px;
}

/* ---------- 标签页 ---------- */
QTabWidget::pane { border: 1px solid %(border)s; border-radius: %(radius_sm)s; top: -1px; }
QTabBar::tab {
    background: transparent; color: %(muted)s; padding: 8px 18px; margin-right: 2px;
    border-bottom: 2px solid transparent;
}
QTabBar::tab:hover { color: %(text)s; }
QTabBar::tab:selected { color: %(primary)s; border-bottom: 2px solid %(primary)s; font-weight: 600; }

/* ---------- 滚动条 ---------- */
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical {
    background: %(border_hi)s; border-radius: 5px; min-height: 28px;
}
QScrollBar::handle:vertical:hover { background: %(muted)s; }
QScrollBar:horizontal { background: transparent; height: 10px; margin: 2px; }
QScrollBar::handle:horizontal { background: %(border_hi)s; border-radius: 5px; min-width: 28px; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }

/* ---------- 分组 ---------- */
QGroupBox {
    border: 1px solid %(border)s; border-radius: %(radius)s;
    margin-top: 12px; padding: 14px 12px 10px 12px; background: %(surface)s;
}
QGroupBox::title {
    subcontrol-origin: margin; left: 12px; padding: 0 6px;
    color: %(primary)s; font-weight: 700; background: %(surface)s;
}
QSplitter::handle { background: %(border)s; }
"""


def build_qss(mode: str) -> str:
    t = dict(DARK if mode != "light" else LIGHT)
    t.update(GEOMETRY)
    return _QSS % t


def _palette(mode: str) -> QPalette:
    t = DARK if mode != "light" else LIGHT
    pal = QPalette()
    roles = {
        QPalette.ColorRole.Window: t["bg"],
        QPalette.ColorRole.WindowText: t["text"],
        QPalette.ColorRole.Base: t["surface"],
        QPalette.ColorRole.AlternateBase: t["surface_alt"],
        QPalette.ColorRole.Text: t["text"],
        QPalette.ColorRole.Button: t["surface_alt"],
        QPalette.ColorRole.ButtonText: t["text"],
        QPalette.ColorRole.Highlight: t["primary"],
        QPalette.ColorRole.HighlightedText: t["on_primary"],
        QPalette.ColorRole.PlaceholderText: t["muted"],
        QPalette.ColorRole.ToolTipBase: t["elevated"],
        QPalette.ColorRole.ToolTipText: t["text"],
        QPalette.ColorRole.Link: t["primary"],
        QPalette.ColorRole.Accent: t["primary"],
    }
    for role, value in roles.items():
        pal.setColor(role, QColor(value))
    return pal


def apply_theme(app: QApplication, mode: str = "dark") -> None:
    """应用主题（mode: dark|light）。可多次调用实现运行时切换。"""
    TOKENS.clear()
    TOKENS.update(DARK if mode != "light" else LIGHT)
    TOKENS.update(GEOMETRY)
    app.setStyle("Fusion")
    font = QFont("Microsoft YaHei UI")
    font.setPixelSize(13)
    app.setFont(font)
    app.setPalette(_palette(mode))
    app.setStyleSheet(build_qss(mode))
