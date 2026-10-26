"""GUI 冒烟测试（Phase 2：offscreen 平台，不弹窗、不连游戏）。"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from ak_auto.config import AppConfig  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app
    app.processEvents()


@pytest.fixture(scope="module", autouse=True)
def _qt_cleanup(qapp):
    """模块结束时清理残留控件，避免 Qt/MaaFw C++ teardown 冲突。"""
    yield
    for w in qapp.topLevelWidgets():
        w.deleteLater()
    qapp.processEvents()


def test_main_window_constructs(qapp) -> None:
    from ak_auto.gui.main_window import NAV_ITEMS, MainWindow

    win = MainWindow(AppConfig())
    assert win.windowTitle() == "arknights-auto — 明日方舟本地自动化助手"
    assert win.nav.count() == len(NAV_ITEMS) + 2 == 6  # 4 常规页 + 高级设置 + 诊断
    assert win.pages.count() == 6
    assert win.nav.item(4).isHidden() and win.nav.item(5).isHidden()  # 简单模式下隐藏
    assert win.home.start_btn.isEnabled() is True
    assert win.home.stop_btn.isEnabled() is False  # 未运行时停止按钮禁用
    win.close()


def test_theme_applies(qapp) -> None:
    from ak_auto.gui.theme import TOKENS, apply_theme

    apply_theme(qapp)
    assert qapp.styleSheet()
    assert TOKENS["primary"] and TOKENS["bg"]


def test_task_page_lists_catalog(qapp) -> None:
    from ak_auto.gui.main_window import TaskPage

    page = TaskPage(AppConfig())
    assert len(page.checks) == 10  # 任务目录全量


def test_sequence_interleaves_return_home() -> None:
    from ak_auto.gui.main_window import _sequence

    assert _sequence(["StartUp", "Infrast"]) == ["StartUp", "ReturnToHome", "Infrast"]
    assert _sequence(["Infrast"]) == ["ReturnToHome", "Infrast"]


def test_sequence_honors_custom_order() -> None:
    from ak_auto.gui.main_window import _sequence

    # 自定义顺序：Recruit 在 Infrast 之前 → 序列按该顺序生成
    order = ["StartUp", "Recruit", "Infrast", "Mall"]
    entries = _sequence(["Infrast", "Recruit"], order)
    assert entries == ["ReturnToHome", "Recruit", "ReturnToHome", "Infrast"]


def test_task_page_preset_and_selection(qapp) -> None:
    from ak_auto.gui.main_window import TaskPage

    page = TaskPage(AppConfig())
    page.apply_preset("快速收菜")
    assert page.selected_entries() == ["ReturnToHome", "Infrast"]


def test_task_page_custom_preset(qapp) -> None:
    from ak_auto.config import AppConfig, PresetConfig

    from ak_auto.gui.main_window import TaskPage

    cfg = AppConfig()
    cfg.custom_presets = [PresetConfig(name="收菜+公招", task_ids=["Infrast", "Recruit"])]
    page = TaskPage(cfg)
    assert "收菜+公招" in page.preset_names()
    page.apply_preset("收菜+公招")
    assert page.selected_entries() == ["ReturnToHome", "Infrast", "ReturnToHome", "Recruit"]


def test_worker_is_qthread() -> None:
    from PySide6.QtCore import QThread

    from ak_auto.gui.worker import TaskWorker

    assert issubclass(TaskWorker, QThread)


def test_settings_page_save(tmp_path, qapp) -> None:
    from ak_auto.application import ConfigurationService
    from ak_auto.gui.pages import SettingsPage

    svc = ConfigurationService(tmp_path / "c.json")
    cfg = svc.load()
    page = SettingsPage(cfg, svc)
    page.game_path.setText(r"C:\Games\Arknights.exe")
    page._save()

    loaded = svc.load()
    assert loaded.startup.game_path == r"C:\Games\Arknights.exe"
    assert (tmp_path / "c.json").exists()


def test_runlog_page_reads_reports(tmp_path, qapp, monkeypatch) -> None:
    import json

    from ak_auto.gui import pages as pages_mod

    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "run-x.json").write_text(
        json.dumps(
            {
                "started_at": "2026-10-13T00:00:00",
                "all_ok": True,
                "total_ms": 1000,
                "tasks": [{"entry": "StartUp", "ok": True, "status": "succeeded",
                           "duration_ms": 1000, "nodes": ["StartUp"], "run_id": "r", "error": ""}],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(pages_mod, "PROJECT_ROOT", tmp_path)
    page = pages_mod.RunLogPage()
    assert page.list.count() == 1
    assert "StartUp" in page.detail.toPlainText()


def test_wizard_constructs(qapp, tmp_path) -> None:
    from ak_auto.application import ConfigurationService
    from ak_auto.gui.wizard import FirstRunWizard

    svc = ConfigurationService(tmp_path / "c.json")
    wiz = FirstRunWizard(svc.load(), svc)
    assert len(wiz.pageIds()) == 5
    assert wiz.windowTitle() == "arknights-auto 首次启动向导"
    wiz.close()


def test_home_run_state_updates(qapp) -> None:
    from ak_auto.gui.main_window import HomePage

    page = HomePage(AppConfig())
    page.begin_run(5)
    assert not page.progress.isHidden() and "准备中" in page.run_state.text()

    page.set_task_state("Infrast", "running")
    assert "Infrast — running" in page.run_state.text()

    page.set_progress(2, 5)
    assert page.progress.value() == 2

    page.finish_run("3/5 成功")
    assert "已结束" in page.run_state.text()
    assert page.progress.isHidden()


def test_worker_has_state_signals() -> None:
    from ak_auto.gui.worker import TaskWorker

    for name in ("task_state", "seq_progress", "log", "done", "failed"):
        assert hasattr(TaskWorker, name), f"缺信号 {name}"


def test_mode_toggle_does_not_reset_params(qapp, tmp_path) -> None:
    from ak_auto.application import ConfigurationService
    from ak_auto.gui.main_window import MainWindow

    svc = ConfigurationService(tmp_path / "c.json")
    cfg = svc.load()
    cfg.fight.times = 7
    svc.save(cfg)

    win = MainWindow(cfg, svc)
    assert cfg.ui.mode == "simple"
    assert win.nav.item(4).isHidden()

    win._toggle_mode()
    assert cfg.ui.mode == "advanced"
    assert not win.nav.item(4).isHidden()
    assert cfg.fight.times == 7  # 切换模式不重置任何参数

    reloaded = svc.load()
    assert reloaded.ui.mode == "advanced" and reloaded.fight.times == 7
    win.close()


def test_advanced_page_save(qapp, tmp_path) -> None:
    from ak_auto.application import ConfigurationService
    from ak_auto.gui.pages import AdvancedPage

    svc = ConfigurationService(tmp_path / "c.json")
    cfg = svc.load()
    page = AdvancedPage(cfg, svc)

    page.order_list.setCurrentRow(2)
    page._move(-1)  # 把第 3 项上移一位
    page.min_sanity.setValue(30)
    page.tag_priority.setText("资深干员, 高级资深干员")
    page._save()

    loaded = svc.load()
    assert loaded.fight.min_sanity == 30
    assert loaded.recruit.tag_priority == ["资深干员", "高级资深干员"]
    assert loaded.runtime.task_order == page._order()


def test_preset_management_save_delete(qapp, tmp_path) -> None:
    from ak_auto.application import ConfigurationService
    from ak_auto.gui.main_window import TaskPage

    svc = ConfigurationService(tmp_path / "c.json")
    cfg = svc.load()
    cfg.ui.mode = "advanced"
    page = TaskPage(cfg, svc)

    page.apply_preset("快速收菜")  # 勾选 Infrast
    page.preset_edit.setText("我的预设")
    page._save_preset()

    assert "我的预设" in page.preset_names()
    reloaded = svc.load()
    assert reloaded.custom_presets[0].name == "我的预设"
    assert reloaded.custom_presets[0].task_ids == ["Infrast"]

    page.preset_combo.setCurrentText("我的预设")
    page._delete_preset()
    assert "我的预设" not in page.preset_names()
    assert svc.load().custom_presets == []


def test_preset_management_hidden_in_simple_mode(qapp) -> None:
    from ak_auto.gui.main_window import TaskPage

    cfg = AppConfig()
    page = TaskPage(cfg)
    assert page.preset_edit.isHidden()  # 简单模式隐藏管理行

    cfg.ui.mode = "advanced"
    page.refresh_mode()
    assert not page.preset_edit.isHidden()


def test_diagnostics_page_constructs(qapp) -> None:
    from ak_auto.gui.pages import DiagnosticsPage

    page = DiagnosticsPage(AppConfig())
    assert page.check_btn.isEnabled() and page.win_btn.isEnabled()


def test_diagnostics_run_checks() -> None:
    from ak_auto.application.diagnostics import run_checks

    checks = run_checks(AppConfig())
    names = [n for n, _, _ in checks]
    assert "Python 3.12" in names
    assert "识别资源（MANIFEST）" in names
    assert "游戏窗口" in names
    assert all(isinstance(ok, bool) and isinstance(msg, str) for _, ok, msg in checks)


# ---------------- G7.3：竞态与防护 ----------------
class _FakeRunningWorker:
    def __init__(self) -> None:
        self.stopped = False
        self.waited = 0

    def isRunning(self) -> bool:  # noqa: N802 —— 模拟 QThread API
        return True

    def stop(self) -> None:
        self.stopped = True

    def wait(self, ms: int = 0) -> bool:
        self.waited += 1
        return True


def test_start_guard_blocks_second_run(qapp) -> None:
    """已有任务在跑时，再点开始不会新建 worker（任务单例）。"""
    from ak_auto.gui.main_window import MainWindow

    win = MainWindow(AppConfig())
    fake = _FakeRunningWorker()
    win.worker = fake
    win._start(["StartUp"])
    assert win.worker is fake  # 未被替换
    win.close()


def test_close_during_run_stops_worker(qapp) -> None:
    """运行中关闭窗口 → 协作式停止并等待（不遗留点击线程）。"""
    from ak_auto.gui.main_window import MainWindow

    win = MainWindow(AppConfig())
    fake = _FakeRunningWorker()
    win.worker = fake
    win.close()
    assert fake.stopped and fake.waited >= 1


def test_repeated_page_switches_safe(qapp) -> None:
    """反复切换页面不崩溃、索引始终有效。"""
    from ak_auto.gui.main_window import ADVANCED_NAV, NAV_ITEMS, MainWindow

    win = MainWindow(AppConfig())
    for _ in range(3):
        for i in range(len(NAV_ITEMS) + len(ADVANCED_NAV)):
            win.nav.setCurrentRow(i)
    assert 0 <= win.pages.currentIndex() < win.pages.count()
    win.close()


def test_global_stop_hidden_when_idle(qapp) -> None:
    """空闲时状态栏的全局停止按钮不可见。"""
    from ak_auto.gui.main_window import MainWindow

    win = MainWindow(AppConfig())
    assert win.global_stop.isVisible() is False
    win.close()


def test_failure_hints_cover_known_codes() -> None:
    from ak_auto.gui.main_window import FAILURE_HINTS

    for code in ("missing-node", "timeout", "cancelled"):
        assert FAILURE_HINTS.get(code)

