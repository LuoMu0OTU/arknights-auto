"""GUI 启动入口（Phase 2）。"""
from __future__ import annotations

import sys


def run_gui() -> int:
    """启动图形界面并进入事件循环；返回 Qt 退出码。"""
    from PySide6.QtWidgets import QApplication, QDialog

    from .. import paths
    from ..application import ConfigurationService
    from .main_window import MainWindow
    from .theme import apply_theme
    from .wizard import FirstRunWizard

    # 打包版首启：把只读资源（流水线/数据表/配置模板）复制到数据目录
    paths.ensure_data_layout()

    svc = ConfigurationService()
    cfg = svc.load()

    app = QApplication(sys.argv)
    app.setApplicationName("arknights-auto")
    app.setOrganizationName("arknights-auto")
    apply_theme(app, getattr(cfg.ui, "theme", "dark"))

    # 首次运行（无配置文件）→ 先走向导
    if not svc.path.exists():
        wiz = FirstRunWizard(cfg, svc)
        if wiz.exec() != QDialog.DialogCode.Accepted:
            return 0

    win = MainWindow(cfg, svc)
    if svc.warning:
        win._log(f"[warn] {svc.warning}")  # noqa: SLF001 —— 启动期提示
    win.show()
    win.check_updates()  # 后台检查新版本（Phase 7，只提示不安装）
    return app.exec()
