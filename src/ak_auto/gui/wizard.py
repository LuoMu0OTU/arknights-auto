"""首次启动向导（Phase 2 第 4 轮）。

环境检查 → 游戏路径 → 资源准备 → 完成（保存配置）。
通过 Application 层（AssetManager / ConfigurationService）与只读设备检查，不直接执行任务。
"""
from __future__ import annotations

import os
import sys

from PySide6.QtWidgets import (
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWizard,
    QWizardPage,
)

from ..application import ConfigurationService
from ..infrastructure import AssetManager
from ..config import AppConfig


class WelcomePage(QWizardPage):
    def __init__(self) -> None:
        super().__init__()
        self.setTitle("欢迎使用")
        brand = QLabel("◈  ARKNIGHTS AUTO")
        brand.setStyleSheet("font-size: 24px; font-weight: 900;")
        brand.setObjectName("brandAccent")
        sub = QLabel("面向《明日方舟》官方 PC 客户端的本地自动化助手")
        sub.setObjectName("muted")
        text = QLabel(
            "本向导将帮你：\n\n"
            "  1. 检查运行环境（Python / MaaFw / 识别资源）\n"
            "  2. 确认游戏客户端路径\n"
            "  3. 准备识别资源（首次需联网下载）\n\n"
            "全程只在本机运行，不注入游戏、不修改游戏文件。\n"
            "使用第三方自动化可能涉及账号风险，请自行评估。"
        )
        text.setWordWrap(True)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 12, 8, 8)
        lay.setSpacing(10)
        lay.addWidget(brand)
        lay.addWidget(sub)
        lay.addSpacing(6)
        lay.addWidget(text)
        lay.addStretch(1)


class EnvPage(QWizardPage):
    def __init__(self) -> None:
        super().__init__()
        self.setTitle("环境检查")
        self.status = QLabel("点击「重新检查」开始。")
        self.status.setWordWrap(True)
        self.check_btn = QPushButton("重新检查")
        self.check_btn.clicked.connect(self.refresh)
        lay = QVBoxLayout(self)
        lay.addWidget(self.status)
        lay.addWidget(self.check_btn)

    def refresh(self) -> None:
        lines: list[str] = []
        py = sys.version_info
        lines.append(f"[{'OK ' if (py.major, py.minor) == (3, 12) else 'FAIL'}] Python 3.12（当前 {py.major}.{py.minor}.{py.micro}）")
        try:
            import maa  # noqa: F401
            lines.append("[OK ] MaaFw 可导入")
        except Exception:  # noqa: BLE001
            lines.append("[FAIL] MaaFw 导入失败")
        am = AssetManager().status()
        lines.append(f"[{'OK ' if am['ready'] else '待准备'}] 识别资源（下一步可下载）")
        self.status.setText("\n".join(lines))


class PathPage(QWizardPage):
    def __init__(self, cfg: AppConfig) -> None:
        super().__init__()
        self.setTitle("游戏客户端路径")
        self.edit = QLineEdit(cfg.startup.game_path)
        self.edit.setPlaceholderText(r"例如 E:\Arknights\Arknights.exe")
        self.registerField("game_path*", self.edit)
        self.status = QLabel("")
        self.status.setWordWrap(True)
        self.detect_btn = QPushButton("检测")
        self.detect_btn.clicked.connect(self._detect)
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("明日方舟官方 PC 客户端的 Arknights.exe 完整路径："))
        lay.addWidget(self.edit)
        lay.addWidget(self.detect_btn)
        lay.addWidget(self.status)

    def _detect(self) -> None:
        p = self.edit.text().strip()
        self.status.setText(f"[{'OK ' if os.path.isfile(p) else 'FAIL'}] 文件存在：{p}")


class AssetPage(QWizardPage):
    def __init__(self) -> None:
        super().__init__()
        self.setTitle("识别资源")
        self.am = AssetManager()
        self.status = QLabel("")
        self.status.setWordWrap(True)
        self.fetch_btn = QPushButton("准备资源（联网下载，约几十 MB）")
        self.fetch_btn.clicked.connect(self._ensure)
        lay = QVBoxLayout(self)
        lay.addWidget(self.status)
        lay.addWidget(self.fetch_btn)
        self.refresh()

    def refresh(self) -> None:
        st = self.am.status()
        parts = [
            f"[{'OK ' if st['manifest'] else '缺失'}] 资源清单",
            f"[{'OK ' if st['ocr'] else '缺失'}] OCR 模型",
            f"[{'OK ' if st['images'] else '缺失'}] 模板图",
        ]
        self.status.setText("、".join(parts))

    def _ensure(self) -> None:
        self.status.setText("正在下载资源，请稍候 ...")
        self.setEnabled(False)
        try:
            ok = self.am.ensure()
            self.status.setText("资源就绪 ✓" if ok else "资源准备失败，请检查网络后重试。")
        finally:
            self.setEnabled(True)
            self.refresh()


class FinishPage(QWizardPage):
    def __init__(self) -> None:
        super().__init__()
        self.setTitle("完成")
        text = QLabel(
            "配置已就绪。开始使用前请确认：\n\n"
            "  1. 游戏窗口化为 1280×720（16:9），游戏内 UI 缩放 100%；\n"
            "  2. 若识别异常，先运行 doctor / 窗口探测排查。\n\n"
            "点「完成」保存配置并进入主界面。"
        )
        text.setWordWrap(True)
        lay = QVBoxLayout(self)
        lay.addWidget(text)


class FirstRunWizard(QWizard):
    def __init__(self, cfg: AppConfig, svc: ConfigurationService) -> None:
        super().__init__()
        self.cfg = cfg
        self.svc = svc
        self.setWindowTitle("arknights-auto 首次启动向导")
        self.resize(640, 480)
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setButtonText(QWizard.WizardButton.NextButton, "下一步")
        self.setButtonText(QWizard.WizardButton.BackButton, "上一步")
        self.setButtonText(QWizard.WizardButton.CancelButton, "取消")
        self.setButtonText(QWizard.WizardButton.FinishButton, "完成")
        self.setButtonText(QWizard.WizardButton.HelpButton, "帮助")
        self.addPage(WelcomePage())
        self.addPage(EnvPage())
        self.path_page = PathPage(cfg)
        self.addPage(self.path_page)
        self.addPage(AssetPage())
        self.addPage(FinishPage())

    def accept(self) -> None:  # noqa: D102 —— 保存配置后关闭
        path = self.field("game_path").strip()
        if path:
            self.cfg.startup.game_path = path
        self.svc.save(self.cfg)
        super().accept()
