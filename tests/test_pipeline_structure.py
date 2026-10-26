"""流水线结构回归测试（Phase 5 第 5 项：不需要真实游戏的回归防线）。

守卫：节点引用完整、战斗链可达终节点、点击目标在 1280×720 内、
自定义动作已注册、截图回归夹具存在。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

PIPELINE_DIR = ROOT / "assets" / "resource" / "pipeline"

# 与 src/ak_auto/tasks/*.py 的 register() 保持一致
KNOWN_CUSTOM_ACTIONS = {
    "FightSetRepeatCount",
    "FightRecoverCapture",
    "RecruitSelectTags",
    "MallSelectBuy",
    "InfrastResumeStations",
    "InfrastResetRound",
    "InfrastNextRound",
    "InfrastReception",
    "InfrastTodoCollect",
    "InfrastOpenTodo",
}


def _load() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for p in sorted(PIPELINE_DIR.glob("*.json")):
        data = json.loads(p.read_text(encoding="utf-8"))
        for name, node in data.items():
            node["__file"] = p.name
            out[name] = node
    return out


PIPELINES = _load()


def test_all_next_targets_exist() -> None:
    for name, node in PIPELINES.items():
        for key in ("next", "on_error"):
            for target in node.get(key, []):
                assert target in PIPELINES, (
                    f"{node['__file']}:{name} 的 {key} 指向不存在的节点 {target!r}"
                )


def test_fight_chain_reaches_done() -> None:
    """Fight 入口沿 next/on_error 可达 Fight@Done（无断链），且不跨文件。"""
    assert "Fight@Done" in PIPELINES
    seen: set[str] = set()
    queue = ["Fight"]
    while queue:
        n = queue.pop()
        if n in seen:
            continue
        seen.add(n)
        for key in ("next", "on_error"):
            for t in PIPELINES[n].get(key, []):
                if t not in seen:
                    queue.append(t)
    assert "Fight@Done" in seen
    for n in seen:
        assert PIPELINES[n]["__file"] == "fight.json", f"{n} 跨文件引用"


def test_fight_click_targets_in_bounds() -> None:
    for name in ("Fight@FormationStart", "Fight@Enter", "Fight@BattleEnd", "Fight@Aftermath", "Fight@Aftermath2"):
        node = PIPELINES[name]
        if "target" in node:
            x, y, w, h = node["target"]
            assert 0 <= x and x + w <= 1280 and 0 <= y and y + h <= 720, f"{name} target 越界"


def test_custom_actions_registered() -> None:
    for name, node in PIPELINES.items():
        ca = node.get("custom_action")
        if ca:
            assert ca in KNOWN_CUSTOM_ACTIONS, f"{node['__file']}:{name} 引用了未注册的自定义动作 {ca!r}"


def test_regression_fixture_exists() -> None:
    assert (ROOT / "tests" / "fixtures" / "selector_rows.png").exists()


def test_entry_tasks_are_covered() -> None:
    """任务目录（taskdef）里的每个执行入口必须在流水线中存在。"""
    from ak_auto.domain import all_tasks

    for t in all_tasks():
        assert t.entry in PIPELINES, f"任务 {t.id} 的入口 {t.entry} 不在流水线中"
