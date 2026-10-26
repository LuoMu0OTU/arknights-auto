"""主窗口与页面框架（Phase 2，视觉重设计 Phase 7）。

结构：左侧品牌侧边栏（首页/任务中心/运行记录/设置 + 高级模式页）+ QStackedWidget 页面。
任务中心：勾选任务目录 → 生成执行序列（ReturnToHome 间隔）→ 经 TaskWorker 走真实 Application 层执行。
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ..application import ConfigurationService
from ..config import PresetConfig
from ..domain import all_tasks
from .pages import AdvancedPage, DiagnosticsPage, RunLogPage, SettingsPage
from .worker import TaskWorker

NAV_ITEMS = ["首页", "任务中心", "运行记录", "设置"]
ADVANCED_NAV = ["高级设置", "诊断"]  # 仅高级模式显示

FIXED_PRESETS: dict[str, list[str]] = {
    "快速收菜": ["Infrast"],
    "公招与信用": ["AwardVisit", "Mall", "Recruit"],
}

RISK_TEXT = {"low": "低", "medium": "中", "high": "高"}

# 任务支持状态（与 docs/architecture/PHASE7_GUI_AUDIT.md 的矩阵保持一致）
TASK_STATUS: dict[str, tuple[str, str]] = {
    "StartUp": ("已验证", "启动游戏 / 自动点开始唤醒 / 清弹窗"),
    "ReturnToHome": ("已验证", "回到主界面"),
    "AwardVisit": ("已验证", "好友列表逐个访问基建"),
    "Infrast": ("已验证", "收菜 + 会客室线索 + 发光站恢复生产；干员换班计划中"),
    "Mall": ("已验证", "按优先级采购（列表加载慢时会等待）"),
    "Recruit": ("已验证", "标签识别 + 聘用候选人 + 新招募"),
    "Fight": ("有限制", "仅打「上一次作战」；选关导航与精确选次计划中"),
    "Award": ("已验证", "日常 + 周常「收集全部」"),
    "AwardMail": ("已验证", "邮件一键收取"),
    "AwardSignIn": ("已验证", "每日签到"),
}


def _sequence(chosen: list[str], order: list[str] | None = None) -> list[str]:
    """按 order 生成执行序列：非 StartUp 任务前插 ReturnToHome（与 CLI daily 一致）。

    order 之外的勾选任务按目录顺序跟在后面。
    """
    if order is None:
        order = [t.id for t in all_tasks()]
    pos = {t: i for i, t in enumerate(order)}
    chosen = sorted(chosen, key=lambda t: (pos.get(t, 10**6), t))
    entries: list[str] = []
    for t in chosen:
        if t != "StartUp":
            entries.append("ReturnToHome")
        entries.append(t)
    return entries


# ---------------------------------------------------------------- 通用小组件
def card(*, flat: bool = False) -> QFrame:
    f = QFrame()
    f.setObjectName("cardFlat" if flat else "card")
    f.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
    return f


def h1(text: str) -> QLabel:
    lb = QLabel(text)
    lb.setObjectName("h1")
    return lb


def h2(text: str) -> QLabel:
    lb = QLabel(text)
    lb.setObjectName("h2")
    return lb


def caption(text: str) -> QLabel:
    lb = QLabel(text)
    lb.setObjectName("caption")
    lb.setWordWrap(True)
    return lb


def status_dot(ok: bool, text: str) -> QLabel:
    """圆点 + 文本的轻量状态徽标。"""
    lb = QLabel(("● " if ok else "○ ") + text)
    lb.setObjectName("badgeOk" if ok else "badgeBad")
    return lb


def page_header(title: str, subtitle: str = "") -> QVBoxLayout:
    lay = QVBoxLayout()
    lay.setSpacing(4)
    lay.addWidget(h1(title))
    if subtitle:
        lay.addWidget(caption(subtitle))
    return lay


# ---------------------------------------------------------------- 首页
class HomePage(QWidget):
    run_requested = Signal(list)
    stop_requested = Signal()

    def __init__(self, cfg, parent=None) -> None:
        super().__init__(parent)
        self.cfg = cfg
        self._build()
        self.refresh_status()

    # ---- 布局 ----
    def _build(self) -> None:
        # 顶部标题（徽标右上、副标题整行）
        self.status_chip = status_dot(False, "检测中")
        title_row = QHBoxLayout()
        title_row.addWidget(h1("指挥中心"))
        title_row.addStretch(1)
        title_row.addWidget(self.status_chip, 0, Qt.AlignmentFlag.AlignTop)
        header = QVBoxLayout()
        header.setSpacing(4)
        header.addLayout(title_row)
        header.addWidget(caption("游戏连接状态、任务运行入口与实时日志。"))

        # 状态卡片行
        self.game_chip = status_dot(False, "游戏窗口：检测中")
        self.asset_chip = status_dot(False, "识别资源：检测中")
        status_card = card()
        sc = QVBoxLayout(status_card)
        sc.setContentsMargins(16, 14, 16, 14)
        sc.setSpacing(8)
        sc.addWidget(h2("运行环境"))
        row = QHBoxLayout()
        row.addWidget(self.game_chip)
        row.addWidget(self.asset_chip)
        row.addStretch(1)
        sc.addLayout(row)

        # 上次结果 + 更新提示
        self.last_label = QLabel(self._last_run_text())
        self.last_label.setObjectName("dim")
        self.last_label.setWordWrap(True)
        self.update_label = QLabel("")
        self.update_label.setObjectName("update")
        self.update_label.setOpenExternalLinks(True)
        self.update_label.setVisible(False)

        result_card = card()
        rc = QVBoxLayout(result_card)
        rc.setContentsMargins(16, 14, 16, 14)
        rc.setSpacing(8)
        rc.addWidget(h2("上次运行"))
        rc.addWidget(self.last_label)

        # 运行控制卡片
        self.run_state = QLabel("运行状态：空闲")
        self.run_state.setObjectName("accent")
        self.progress = QProgressBar()
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self.progress.setVisible(False)

        self.start_btn = QPushButton("快速启动 StartUp")
        self.start_btn.setObjectName("bigPrimary")
        self.start_btn.setToolTip("进入游戏主页并清弹窗，确认环境就绪")
        self.start_btn.clicked.connect(lambda: self.run_requested.emit(["StartUp"]))
        self.stop_btn = QPushButton("停止")
        self.stop_btn.setObjectName("danger")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_requested.emit)

        run_card = card()
        rl = QVBoxLayout(run_card)
        rl.setContentsMargins(16, 14, 16, 16)
        rl.setSpacing(10)
        rl.addWidget(h2("开始运行"))
        rl.addWidget(caption("快速启动仅确认游戏可连接；完整任务请到「任务中心」选择。"))
        btns = QHBoxLayout()
        btns.setSpacing(10)
        btns.addWidget(self.start_btn)
        btns.addWidget(self.stop_btn)
        btns.addStretch(1)
        rl.addLayout(btns)
        rl.addWidget(self.run_state)
        rl.addWidget(self.progress)

        # 日志卡片
        self.log_view = QPlainTextEdit()
        self.log_view.setObjectName("log")
        self.log_view.setReadOnly(True)
        self.log_view.setPlaceholderText("事件与日志会显示在这里 ...")
        log_card = card()
        lc = QVBoxLayout(log_card)
        lc.setContentsMargins(16, 14, 16, 16)
        lc.setSpacing(8)
        lc.addWidget(h2("实时日志"))
        lc.addWidget(self.log_view, 1)

        # 组装
        body = QVBoxLayout()
        body.setSpacing(12)
        body.addLayout(header)
        body.addWidget(status_card)
        body.addWidget(result_card)
        body.addWidget(self.update_label)
        body.addWidget(run_card)
        body.addWidget(log_card, 1)

        wrap = QWidget()
        wrap.setLayout(body)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(wrap)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    # ---- 状态刷新 ----
    def refresh_status(self) -> None:
        from .. import device
        from ..infrastructure import AssetManager

        am = AssetManager().status()
        self.asset_chip.setText(("● " if am["ready"] else "○ ") + "识别资源：" + ("就绪" if am["ready"] else "未就绪"))
        self.asset_chip.setObjectName("badgeOk" if am["ready"] else "badgeBad")
        self.asset_chip.style().unpolish(self.asset_chip)
        self.asset_chip.style().polish(self.asset_chip)

        running = False
        try:
            device.init_maa()
            win = device.find_game_window(self.cfg)
            running = bool(win)
        except Exception:  # noqa: BLE001
            pass
        self.game_chip.setText(("● " if running else "○ ") + "游戏窗口：" + ("已运行" if running else "未运行"))
        self.game_chip.setObjectName("badgeOk" if running else "badgeBad")
        self.game_chip.style().unpolish(self.game_chip)
        self.game_chip.style().polish(self.game_chip)

        self.status_chip.setText("● 已就绪" if (running and am["ready"]) else "○ 待准备")
        self.status_chip.setObjectName("badgeOk" if (running and am["ready"]) else "badgeBad")
        self.status_chip.style().unpolish(self.status_chip)
        self.status_chip.style().polish(self.status_chip)

    # ---- 运行状态区（TaskWorker 信号驱动）----
    def begin_run(self, total: int) -> None:
        self.progress.setRange(0, max(1, total))
        self.progress.setValue(0)
        self.progress.setVisible(True)
        self.run_state.setText("运行状态：准备中 ...")

    def set_task_state(self, task_id: str, state: str) -> None:
        self.run_state.setText(f"运行状态：{task_id} — {state}")

    def set_progress(self, done: int, total: int) -> None:
        self.progress.setRange(0, max(1, total))
        self.progress.setValue(done)

    def finish_run(self, summary: str) -> None:
        self.run_state.setText(f"运行状态：已结束（{summary}）")
        self.progress.setVisible(False)
        self.refresh_last()
        self.refresh_status()

    @staticmethod
    def _last_run_text() -> str:
        import json

        from ..config import PROJECT_ROOT

        files = sorted(
            (PROJECT_ROOT / "logs").glob("run-*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if not files:
            return "暂无运行记录"
        try:
            data = json.loads(files[0].read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return "记录无法读取"
        tasks = data.get("tasks", [])
        ok_n = sum(1 for t in tasks if t.get("ok"))
        total = data.get("total_ms", 0) / 1000
        return f"{data.get('started_at', '?')} · {ok_n}/{len(tasks)} 成功 · 耗时 {total:.0f}s"

    def refresh_last(self) -> None:
        self.last_label.setText(self._last_run_text())

    def show_update(self, info) -> None:
        """展示新版本提示（点击链接跳到 GitHub Release 页）；info=None 或非更新则隐藏。"""
        if info is None or not info.is_newer:
            self.update_label.setVisible(False)
            return
        self.update_label.setText(
            f'🔔 发现新版本 <a href="{info.url}">{info.latest}</a>（当前 {info.current}）'
        )
        self.update_label.setVisible(True)

    def append_log(self, text: str) -> None:
        self.log_view.appendPlainText(text)

    def set_running(self, running: bool) -> None:
        self.start_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)


# ---------------------------------------------------------------- 任务中心
class TaskPage(QWidget):
    run_requested = Signal(list)

    def __init__(self, cfg, svc: ConfigurationService | None = None, parent=None) -> None:
        super().__init__(parent)
        self.cfg = cfg
        self.svc = svc or ConfigurationService()
        self._build()
        self.refresh_presets()
        self.refresh_mode()

    def _build(self) -> None:
        header = page_header("任务中心", "勾选要执行的任务，或直接套用预设。每日常规 = 配置中的任务顺序。")

        # 预设 chips
        self.preset_row = QHBoxLayout()
        self.preset_row.setSpacing(8)
        preset_card = card()
        pc = QVBoxLayout(preset_card)
        pc.setContentsMargins(16, 12, 16, 12)
        pc.setSpacing(8)
        pc.addWidget(h2("预设"))
        pc.addLayout(self.preset_row)

        # 任务卡片列表（可展开真实参数）
        from PySide6.QtWidgets import QFormLayout, QSpinBox

        self.checks: dict[str, QCheckBox] = {}
        self.task_settings: dict[str, QWidget] = {}
        self.task_save_status: dict[str, QLabel] = {}
        task_box = QVBoxLayout()
        task_box.setSpacing(6)
        for t in all_tasks():
            status, note = TASK_STATUS.get(t.id, ("已验证", ""))
            row = QFrame()
            row.setObjectName("cardFlat")
            outer = QVBoxLayout(row)
            outer.setContentsMargins(14, 9, 14, 9)
            outer.setSpacing(6)

            rl = QHBoxLayout()
            rl.setSpacing(12)
            cb = QCheckBox(t.name)
            cb.setChecked(t.id in self._preset_ids("每日常规"))
            cb.setMinimumWidth(150)
            self.checks[t.id] = cb
            desc = QLabel(t.description or "")
            desc.setObjectName("caption")
            desc.setWordWrap(True)
            meta = QLabel(f"{t.category} · 风险 {RISK_TEXT.get(t.risk_level, t.risk_level)}")
            meta.setObjectName("muted")
            badge = QLabel(status)
            badge.setObjectName("badgeOk" if status == "已验证" else ("badgeWarn" if status == "有限制" else "badgeBad"))
            rl.addWidget(cb)
            rl.addWidget(desc, 1)
            rl.addWidget(badge)
            rl.addWidget(meta)

            settings = self._build_task_settings(t.id, note)
            if settings is not None:
                gear = QPushButton("⚙")
                gear.setObjectName("ghost")
                gear.setFixedWidth(34)
                gear.setToolTip("展开该任务的可用设置")
                gear.clicked.connect(lambda _=False, w=settings: w.setVisible(not w.isVisible()))
                rl.addWidget(gear)
                settings.setVisible(False)
                self.task_settings[t.id] = settings

            outer.addLayout(rl)
            if settings is not None:
                outer.addWidget(settings)
            task_box.addWidget(row)

        task_card = card()
        tc = QVBoxLayout(task_card)
        tc.setContentsMargins(16, 14, 16, 14)
        tc.setSpacing(10)
        tc.addWidget(h2("任务"))
        tc.addLayout(task_box)

        # 预设管理行（仅高级模式）
        self.preset_edit = QLineEdit()
        self.preset_edit.setPlaceholderText("预设名称")
        self.save_preset_btn = QPushButton("保存当前勾选")
        self.save_preset_btn.clicked.connect(self._save_preset)
        self.preset_combo = QComboBox()
        self.preset_combo.setMinimumWidth(150)
        self.delete_preset_btn = QPushButton("删除")
        self.delete_preset_btn.setObjectName("danger")
        self.delete_preset_btn.clicked.connect(self._delete_preset)
        self.preset_status = QLabel("")
        self.preset_status.setObjectName("muted")
        mgmt_row = QHBoxLayout()
        mgmt_row.setSpacing(8)
        self._mgmt_label = QLabel("预设管理：")
        self._mgmt_label.setObjectName("muted")
        mgmt_row.addWidget(self._mgmt_label)
        mgmt_row.addWidget(self.preset_edit)
        mgmt_row.addWidget(self.save_preset_btn)
        mgmt_row.addWidget(self.preset_combo)
        mgmt_row.addWidget(self.delete_preset_btn)
        mgmt_row.addWidget(self.preset_status)
        mgmt_row.addStretch(1)
        self._mgmt_widgets = [self._mgmt_label, self.preset_edit, self.save_preset_btn,
                              self.preset_combo, self.delete_preset_btn, self.preset_status]

        # 执行按钮（固定在页面底部，始终可见）
        self.run_btn = QPushButton("开始执行所选任务")
        self.run_btn.setObjectName("bigPrimary")
        self.run_btn.clicked.connect(self._emit_run)
        bottom = QHBoxLayout()
        bottom.setContentsMargins(20, 8, 20, 14)
        bottom.addWidget(self.run_btn)
        bottom.addStretch(1)

        body = QVBoxLayout()
        body.setSpacing(12)
        body.addLayout(header)
        body.addWidget(preset_card)
        body.addWidget(task_card)
        body.addLayout(mgmt_row)
        body.addStretch(1)

        wrap = QWidget()
        wrap.setLayout(body)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(wrap)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(scroll, 1)
        outer.addLayout(bottom)

    # ---- 任务卡片的真实参数 ----
    def _build_task_settings(self, task_id: str, note: str) -> QWidget | None:
        """按任务返回可编辑的真实参数区；无参数的返回 None（只显示状态说明）。

        只放已被执行路径消费的参数（见 PHASE7_GUI_AUDIT 配置消费矩阵）。
        """
        from PySide6.QtWidgets import QFormLayout, QSpinBox

        cfg = self.cfg
        box = QWidget()
        lay = QFormLayout(box)
        lay.setContentsMargins(6, 4, 6, 4)
        lay.setSpacing(8)

        if task_id == "Fight":
            self.fight_times = QSpinBox()
            self.fight_times.setRange(0, 999)
            self.fight_times.setValue(cfg.fight.times)
            self.fight_times.setSpecialValueText("按理智自动")
            self.fight_min_sanity = QSpinBox()
            self.fight_min_sanity.setRange(0, 200)
            self.fight_min_sanity.setValue(cfg.fight.min_sanity)
            self.fight_min_sanity.setSpecialValueText("不限制")
            lay.addRow("刷图次数（0 = 按理智自动）", self.fight_times)
            lay.addRow("理智低于该值停止（0 = 不限制）", self.fight_min_sanity)
            lay.addRow("", QLabel("关卡固定为「上一次作战」；用药/碎石/选关导航：计划中（暂不生效）"))
        elif task_id == "Recruit":
            self.recruit_tags = QLineEdit(", ".join(cfg.recruit.tag_priority))
            self.recruit_tags.setPlaceholderText("例如：资深干员, 高级资深干员（留空 = 默认策略）")
            lay.addRow("标签优先级（真实生效）", self.recruit_tags)
            lay.addRow("", QLabel("次数上限 / 4★保底 / 时长 / 加急：计划中（暂不生效）"))
        elif task_id == "Mall":
            self.mall_buy = QLineEdit(", ".join(cfg.mall.buy_first))
            self.mall_buy.setPlaceholderText("例如：招聘许可, 寻访凭证")
            self.mall_block = QLineEdit(", ".join(cfg.mall.blacklist))
            self.mall_block.setPlaceholderText("例如：家具零件")
            lay.addRow("购买优先级（真实生效）", self.mall_buy)
            lay.addRow("黑名单（真实生效）", self.mall_block)
        else:
            if not note:
                return None
            info = QLabel(note)
            info.setObjectName("caption")
            info.setWordWrap(True)
            lay.addRow(info)
            return None if task_id in ("StartUp", "ReturnToHome") else box

        status = QLabel("")
        status.setObjectName("muted")
        save = QPushButton("保存本任务设置")
        save.clicked.connect(lambda _=False, tid=task_id, st=status: self._save_task_settings(tid, st))
        row = QHBoxLayout()
        row.addWidget(save)
        row.addWidget(status)
        row.addStretch(1)
        lay.addRow(row)
        return box

    def _save_task_settings(self, task_id: str, status: QLabel) -> None:
        cfg = self.cfg
        if task_id == "Fight":
            cfg.fight.times = self.fight_times.value()
            cfg.fight.min_sanity = self.fight_min_sanity.value()
        elif task_id == "Recruit":
            tags = [s.strip() for s in self.recruit_tags.text().replace("，", ",").split(",")]
            cfg.recruit.tag_priority = [s for s in tags if s]
        elif task_id == "Mall":
            for attr, widget in (("buy_first", self.mall_buy), ("blacklist", self.mall_block)):
                items = [s.strip() for s in widget.text().replace("，", ",").split(",")]
                setattr(cfg.mall, attr, [s for s in items if s])
        self.svc.save(cfg)
        status.setText("✓ 已保存，下次运行生效")

    # ---- 预设 ----
    def preset_names(self) -> list[str]:
        """内置推荐预设 + 用户自定义预设。"""
        names = ["每日常规"] + list(FIXED_PRESETS)
        names += [p.name for p in self.cfg.custom_presets if p.name]
        return names

    def _preset_ids(self, name: str) -> list[str]:
        if name == "每日常规":
            return list(self.cfg.runtime.task_order)
        if name in FIXED_PRESETS:
            return FIXED_PRESETS[name]
        for p in self.cfg.custom_presets:
            if p.name == name:
                return list(p.task_ids)
        return []

    def refresh_presets(self) -> None:
        """重建预设按钮与删除下拉框。"""
        while self.preset_row.count():
            item = self.preset_row.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        for name in self.preset_names():
            btn = QPushButton(name)
            btn.setObjectName("chip")
            btn.clicked.connect(lambda _=False, n=name: self.apply_preset(n))
            self.preset_row.addWidget(btn)
        self.preset_row.addStretch(1)

        self.preset_combo.clear()
        for p in self.cfg.custom_presets:
            if p.name:
                self.preset_combo.addItem(p.name)

    def refresh_mode(self) -> None:
        """高级模式才显示预设管理行。"""
        visible = self.cfg.ui.mode == "advanced"
        for w in self._mgmt_widgets:
            w.setVisible(visible)

    def _save_preset(self) -> None:
        name = self.preset_edit.text().strip()
        if not name:
            self.preset_status.setText("请先输入预设名称")
            return
        if name in ("每日常规", *FIXED_PRESETS):
            self.preset_status.setText("名称与内置预设冲突，请换一个")
            return
        ids = [t.id for t in all_tasks() if self.checks[t.id].isChecked()]
        if not ids:
            self.preset_status.setText("请先勾选任务")
            return
        self.cfg.custom_presets = [p for p in self.cfg.custom_presets if p.name != name]
        self.cfg.custom_presets.append(PresetConfig(name=name, task_ids=ids))
        self.svc.save(self.cfg)
        self.refresh_presets()
        self.preset_status.setText(f"已保存预设「{name}」（{len(ids)} 个任务）")

    def _delete_preset(self) -> None:
        name = self.preset_combo.currentText()
        if not name:
            self.preset_status.setText("没有可删除的自定义预设")
            return
        self.cfg.custom_presets = [p for p in self.cfg.custom_presets if p.name != name]
        self.svc.save(self.cfg)
        self.refresh_presets()
        self.preset_status.setText(f"已删除预设「{name}」")

    def apply_preset(self, name: str) -> None:
        ids = self._preset_ids(name)
        for tid, cb in self.checks.items():
            cb.setChecked(tid in ids)

    def selected_entries(self) -> list[str]:
        chosen = [t.id for t in all_tasks() if self.checks[t.id].isChecked()]
        return _sequence(chosen, list(self.cfg.runtime.task_order))

    def _emit_run(self) -> None:
        entries = self.selected_entries()
        if entries:
            self.run_requested.emit(entries)


# ---------------------------------------------------------------- 主窗口
class MainWindow(QMainWindow):
    def __init__(self, cfg, svc: ConfigurationService | None = None) -> None:
        super().__init__()
        self.cfg = cfg
        self.svc = svc or ConfigurationService()
        self.worker: TaskWorker | None = None
        self.setWindowTitle("arknights-auto — 明日方舟本地自动化助手")
        self.resize(1120, 740)
        self.setMinimumSize(920, 620)

        self._build_sidebar()
        self._build_pages()

        central = QWidget()
        lay = QHBoxLayout(central)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self.sidebar)
        lay.addWidget(self.pages, 1)
        self.setCentralWidget(central)

        self.statusBar().showMessage("就绪")
        self._update_worker = None

    # ---- 侧边栏 ----
    def _build_sidebar(self) -> None:
        from .. import __version__

        self.sidebar = QWidget()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(208)
        lay = QVBoxLayout(self.sidebar)
        lay.setContentsMargins(14, 18, 14, 14)
        lay.setSpacing(6)

        # 品牌区
        brand = QHBoxLayout()
        brand.setSpacing(10)
        mark = QLabel("◈")
        mark.setStyleSheet("font-size: 26px; font-weight: 900;")
        mark.setObjectName("brandAccent")
        words = QVBoxLayout()
        words.setSpacing(0)
        name1 = QLabel("ARKNIGHTS")
        name1.setObjectName("brand")
        name2 = QLabel("AUTO")
        name2.setObjectName("brandAccent")
        words.addWidget(name1)
        words.addWidget(name2)
        brand.addWidget(mark)
        brand.addLayout(words)
        brand.addStretch(1)
        lay.addLayout(brand)

        ver = QLabel(f"v{__version__}")
        ver.setObjectName("version")
        lay.addWidget(ver)
        lay.addSpacing(14)

        # 导航
        self.nav = QListWidget()
        self.nav.setObjectName("nav")
        self.nav.addItems(NAV_ITEMS + ADVANCED_NAV)
        self.nav.setFrameShape(QFrame.Shape.NoFrame)
        self.nav.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.nav.currentRowChanged.connect(self._on_nav)
        lay.addWidget(self.nav, 1)

        # 底部：模式 + 主题
        self.mode_btn = QPushButton()
        self.mode_btn.setObjectName("modeBtn")
        self.mode_btn.clicked.connect(self._toggle_mode)
        self.theme_btn = QPushButton()
        self.theme_btn.setObjectName("modeBtn")
        self.theme_btn.clicked.connect(self._toggle_theme)
        lay.addWidget(self.mode_btn)
        lay.addWidget(self.theme_btn)

    # ---- 页面 ----
    def _build_pages(self) -> None:
        self.home = HomePage(self.cfg)
        self.task_page = TaskPage(self.cfg, self.svc)
        self.runlog = RunLogPage()
        self.advanced = AdvancedPage(self.cfg, self.svc)
        self.diagnostics = DiagnosticsPage(self.cfg)
        self.pages = QStackedWidget()
        self.pages.addWidget(self.home)
        self.pages.addWidget(self.task_page)
        self.pages.addWidget(self.runlog)
        self.pages.addWidget(SettingsPage(self.cfg, self.svc))
        self.pages.addWidget(self.advanced)
        self.pages.addWidget(self.diagnostics)
        self.nav.setCurrentRow(0)

        self.home.run_requested.connect(self._start)
        self.home.stop_requested.connect(self._stop)
        self.task_page.run_requested.connect(self._start_and_show_log)
        self._refresh_mode_ui()
        self._refresh_theme_ui()

    # ---- 模式切换（简单 / 高级）----
    def _refresh_mode_ui(self) -> None:
        advanced = self.cfg.ui.mode == "advanced"
        for i in range(len(NAV_ITEMS), len(NAV_ITEMS) + len(ADVANCED_NAV)):
            self.nav.item(i).setHidden(not advanced)
        self.mode_btn.setText("⚙  模式：高级" if advanced else "⚙  模式：简单")
        self.mode_btn.setToolTip("切换简单/高级模式（不影响已保存的参数）")
        self.task_page.refresh_mode()

    def _toggle_mode(self) -> None:
        self.cfg.ui.mode = "advanced" if self.cfg.ui.mode == "simple" else "simple"
        self.svc.save(self.cfg)
        self._refresh_mode_ui()
        self.statusBar().showMessage(f"已切换到{'高级' if self.cfg.ui.mode == 'advanced' else '简单'}模式")

    # ---- 主题切换 ----
    def _refresh_theme_ui(self) -> None:
        light = getattr(self.cfg.ui, "theme", "dark") == "light"
        self.theme_btn.setText("☀  主题：浅色" if light else "☾  主题：深色")
        self.theme_btn.setToolTip("切换深色/浅色主题")

    def _toggle_theme(self) -> None:
        from PySide6.QtWidgets import QApplication

        from .theme import apply_theme

        self.cfg.ui.theme = "light" if getattr(self.cfg.ui, "theme", "dark") == "dark" else "dark"
        self.svc.save(self.cfg)
        apply_theme(QApplication.instance(), self.cfg.ui.theme)
        self._refresh_theme_ui()
        self.statusBar().showMessage(f"主题已切换为{'浅色' if self.cfg.ui.theme == 'light' else '深色'}")

    def _on_nav(self, row: int) -> None:
        self.pages.setCurrentIndex(row)
        if row == 0:
            self.home.refresh_status()

    def check_updates(self) -> None:
        """后台检查新版本（Phase 7；config.updates.check_enabled 控制）。

        由 GUI 入口 run_gui 在窗口显示后调用（不在构造器里触发，避免测试/短生命周期崩溃）。
        """
        if not getattr(self.cfg, "updates", None) or not self.cfg.updates.check_enabled:
            return
        from .. import __version__
        from .worker import UpdateWorker

        self._update_worker = UpdateWorker(__version__, self.cfg.updates.repo, self)
        self._update_worker.result.connect(self.home.show_update)
        self._update_worker.start()

    # ---- 任务执行（经 TaskWorker / Application 层）----
    def _start(self, entries: list[str]) -> None:
        if self.worker is not None and self.worker.isRunning():
            self._log("[gui] 已有任务在运行，先停止再开始。")
            return
        self.worker = TaskWorker(self.cfg, entries, parent=self)
        self.worker.log.connect(self._log)
        self.worker.done.connect(self._on_done)
        self.worker.failed.connect(lambda msg: self._log(f"[gui] 失败：{msg}"))
        self.worker.finished.connect(self._on_finished)
        self.worker.task_state.connect(self.home.set_task_state)
        self.worker.seq_progress.connect(self.home.set_progress)
        self.worker.start()
        self.home.set_running(True)
        self.home.begin_run(len(entries))
        self.statusBar().showMessage("运行中 ...")

    def _start_and_show_log(self, entries: list[str]) -> None:
        self._start(entries)
        self.nav.setCurrentRow(0)  # 切回首页看日志

    def _stop(self) -> None:
        if self.worker is not None and self.worker.isRunning():
            self.worker.stop()

    def _on_done(self, results) -> None:
        for r in results:
            self._log(r.summary)
        ok_n = sum(1 for r in results if r.ok)
        self.home.finish_run(f"{ok_n}/{len(results)} 成功")

    def _on_finished(self) -> None:
        self.home.set_running(False)
        self.statusBar().showMessage("就绪")
        self.runlog.refresh()
        self.home.refresh_last()

    def _log(self, text: str) -> None:
        self.home.append_log(text)

    def closeEvent(self, event) -> None:  # noqa: N802 —— Qt 命名
        if self.worker is not None and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(5000)
        super().closeEvent(event)
