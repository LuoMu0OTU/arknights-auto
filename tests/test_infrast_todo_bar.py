"""基建待办条判读（Phase 7）：铃铛/待办条「点不开」回归测试。

背景（2026-11-02 真机）：CustomAction 里 `ctrl.cached_image` 是节点识别时的旧帧，
点击后不刷新 → 待办条明明开了却判定「没打开」，补点第二下把条关掉 / 静默跳过收菜。
本测试锁定判读逻辑本身（纯函数），截图新鲜度由 fresh_image 在运行时保证。
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from ak_auto.tasks.infrast import (  # noqa: E402
    TODO_BUTTONS,
    bar_opened,
    pick_target,
    todo_names_in,
)


# ---- bar_opened：待办条开没开 ----
def test_bar_opened_by_label_only() -> None:
    """条上只有「待办事项」标签（0 个按钮）也算已打开。"""
    assert bar_opened(["待办事项"]) is True


def test_bar_opened_by_button_text() -> None:
    assert bar_opened(["订单交付"]) is True


def test_bar_closed_when_no_bar_text() -> None:
    """条收起时底部是基地地图文字（宿舍/制造站/进驻总览…），不能误判为已打开。"""
    assert bar_opened(["宿舍", "制造站", "进驻总览", "控制中枢"]) is False
    assert bar_opened([]) is False


def test_bar_opened_tolerates_spaces_and_garbage() -> None:
    assert bar_opened(["待 办 事 项"]) is True


# ---- todo_names_in：认出哪些按钮 ----
def test_names_in_order_follows_priority() -> None:
    texts = ["干员休整", "订 单 交 付", "2个干员"]
    assert todo_names_in(texts) == ["订单交付", "干员休整"]


def test_names_empty() -> None:
    assert todo_names_in(["待办事项", "1点击全部交付"]) == []


# ---- pick_target：挑下一个要点的按钮 ----
def test_pick_target_first_unclicked() -> None:
    results = [("待办事项", (54, 682, 82, 22)), ("订单交付", (170, 677, 124, 32))]
    assert pick_target(results, {}) == ("订单交付", (170, 677, 124, 32))


def test_pick_target_prefers_unclicked_buttons() -> None:
    """已点过的按钮还有别的没点过时，先去点没点过的。"""
    results = [("订单交付", (170, 677, 124, 32)), ("干员休整", (377, 676, 83, 23))]
    assert pick_target(results, {"订单交付": 1})[0] == "干员休整"


def test_pick_target_retries_when_only_one_left() -> None:
    results = [("干员休整", (377, 676, 83, 23))]
    assert pick_target(results, {"干员休整": 1}, max_same=3)[0] == "干员休整"


def test_pick_target_retries_same_button_until_max() -> None:
    """「2个干员」这类点一次只处理一个 → 还出现就允许重点，但到上限后放过。"""
    results = [("干员休整", (377, 676, 83, 23))]
    assert pick_target(results, {"干员休整": 1}, max_same=3)[0] == "干员休整"
    assert pick_target(results, {"干员休整": 3}, max_same=3) is None


def test_pick_target_none_when_no_buttons() -> None:
    assert pick_target([("待办事项", (54, 682, 82, 22))], {}) is None


def test_todo_buttons_contains_order_delivery() -> None:
    """「订单交付」曾漏配 → 订单堆积不交付（febcef9 修）。"""
    assert "订单交付" in TODO_BUTTONS
