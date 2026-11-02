"""基建任务：点击「发光的制造站」（已停止的制造站）自动恢复生产（Phase 7）。

真机逆向（截图确认）：
- 已停止的制造站在基地地图上是「**制造站**」+ 橙红「**已停止**」小字 + 亮黄粗边框；
- 点击方块内任意位置 → 「制造站已自动补货」、恢复生产中；
- 原流水线「点制造停工文字」会卡住，必须点这些发光的制造站。

检测（实测区分度）：OCR 读站名「制造站」→ 采样站名下方的状态小字区 →
  「生产中」为黄字（黄色像素 24~38）、「已停止」为橙字（黄色像素 0），
  以「黄色像素 < 12」判定停工。点击站名下方（方块内）恢复，循环直到没有停工站。
"""
from __future__ import annotations

import time

import numpy as np
from maa.custom_action import CustomAction
from maa.resource import Resource

# 状态文字区（站名下方）
STATE_DY = 2
STATE_W, STATE_H = 55, 14
YELLOW_MIN_STOPPED = 12   # 状态区黄色像素 < 该值 → 已停止（生产中为 24~38）
CLICK_DY = 15             # 从站名中心向下偏到方块中心


def _yellow_count(img: np.ndarray, x: int, y: int, w: int, h: int) -> int:
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(img.shape[1], x + w), min(img.shape[0], y + h)
    if x1 <= x0 or y1 <= y0:
        return 0
    sub = img[y0:y1, x0:x1]
    b = sub[..., 0].astype(np.int16)
    g = sub[..., 1].astype(np.int16)
    r = sub[..., 2].astype(np.int16)
    return int(((r > 180) & (g > 170) & (b < 120)).sum())


def is_stopped(img: np.ndarray, name_box: tuple[int, int, int, int]) -> bool:
    """站名所在的制造站是否处于「已停止」状态。"""
    x, y, _w, h = name_box
    yellow = _yellow_count(img, x, y + h + STATE_DY, STATE_W, STATE_H)
    return yellow < YELLOW_MIN_STOPPED


class InfrastResumeStations(CustomAction):
    """内部循环点完所有停工的制造站/贸易站，然后一次性返回 True（避免 next/on_error 重叠导致的死循环）。"""

    def run(self, context, argv) -> bool:
        self.reset_clicked()
        for _ in range(6):
            if not self._click_one(context):
                break
        return True

    def _click_one(self, context) -> bool:
        ctrl = context.tasker.controller
        img = fresh_image(ctrl)   # 每轮都要新图：点击后 cached_image 不会刷新
        if img is None:
            return False
        detail = context.run_recognition("Infrast@OcrMfgStation", img)
        if not detail:
            return False
        stopped: list[tuple[int, int]] = []
        for r in detail.all_results:
            text = (getattr(r, "text", "") or "").replace(" ", "")
            # 只认「制造站/贸易站」开头的站名（排除「加工站」等误读）
            if not (text.startswith("制造站") or text.startswith("贸易站")):
                continue
            box = r.box
            if is_stopped(img, (box[0], box[1], box[2], box[3])):
                stopped.append((box[0] + box[2] // 2, box[1] + box[3] // 2 + CLICK_DY))
        if not stopped:
            print("[infrast] 没有停工的制造站了", flush=True)
            return False
        clicked = getattr(self, "_clicked", None)
        if clicked is None:
            clicked = self._clicked = set()
        fresh = [(x, y) for (x, y) in stopped if (x, y) not in clicked]
        if not fresh:
            print("[infrast] 已点击过的站不再重复点", flush=True)
            return False
        cx, cy = fresh[0]
        clicked.add((cx, cy))
        print(f"[infrast] 点击停工制造站 ({cx},{cy})，共 {len(fresh)} 个待点", flush=True)
        ctrl.post_click(cx, cy).wait()
        time.sleep(3.0)
        return True

    def reset_clicked(self) -> None:
        self._clicked = set()


# ---- 会客室线索收取（完整流程，坐标 1281×720 真机标定）----
# 图2 线索板右侧图标
BOARD_CREDIT = (1202, 178)    # 信用奖励
BOARD_RECEIVE = (1202, 267)   # 接收线索
BOARD_PASS = (1202, 357)      # 传递线索
BOARD_CLUE = (1202, 512)      # 线索
BOARD_QUICK = (1180, 660)     # 快捷置入
BOARD_EXCHANGE = (690, 660)   # 线索交流（7 线索填满时可点）
# 各子面板
ROOM_COLLECT = (320, 682)     # 图1 搜集中
RECEIVE_ALL = (1070, 688)     # 图3 全部收取
PASS_SEND_ALL = (200, 660)    # 图4 左下角「一键递送」（有时出现）
PASS_CLOSE = (1237, 37)       # 图4 右上 ×
CREDIT_CLAIM = (815, 578)     # 图7 领取（计时完成才可点）
CREDIT_CLOSE = (985, 100)     # 图7 ×
PANEL_BLANK = (300, 400)      # 图2 左侧空白（关闭右侧面板）
BACK_BTN2 = (40, 40)          # 返回基地


class InfrastReception(CustomAction):
    """整套会客室收菜：进房 → 搜集中 → 线索板 → 接收/传递/线索/信用奖励 → 回基地。"""

    def run(self, context, argv) -> bool:
        ctrl = context.tasker.controller
        img = fresh_image(ctrl)
        if img is None:
            print("[infrast] 会客室抓图失败", flush=True)
            return False

        def click(pt, wait=1.2):
            ctrl.post_click(pt[0], pt[1]).wait()
            time.sleep(wait)

        # 1) 从基地地图点「会客室」（OCR 定位，避免镜头偏移）
        detail = context.run_recognition("Infrast@OcrReception", img)
        box = None
        if detail is not None:
            best = getattr(detail, "best_result", None)
            if best is not None:
                box = best.box
        if box:
            ctrl.post_click(box[0] + box[2] // 2, box[1] + box[3] // 2).wait()
            print(f"[infrast] 点击会客室 OCR@({box[0]},{box[1]})", flush=True)
        else:
            click((1170, 212), 0)  # 兜底：标定位置
            print("[infrast] 会客室 OCR 未命中，用标定位置", flush=True)
        time.sleep(3.0)

        # 2) 房间内「搜集中」
        click(ROOM_COLLECT, 2.5)

        # 3) 线索板：快捷置入 + 线索交流
        click(BOARD_QUICK)
        click(BOARD_EXCHANGE)

        # 4) 接收线索 → 全部收取 → 空白返回
        click(BOARD_RECEIVE, 2.0)
        click(RECEIVE_ALL, 1.5)
        click(PANEL_BLANK, 1.5)

        # 5) 传递线索 → 一键递送（若有）→ ×
        click(BOARD_QUICK)
        click(BOARD_PASS, 2.0)
        click(PASS_SEND_ALL)
        click(PASS_CLOSE, 1.5)

        # 6) 线索（查看已置入；多余线索回收为后续增强）→ 空白返回
        click(BOARD_QUICK)
        click(BOARD_CLUE, 2.0)
        click(PANEL_BLANK, 1.5)

        # 7) 信用奖励 → 领取（计时完成才可点，未完成点了也无害）→ ×
        click(BOARD_QUICK)
        click(BOARD_CREDIT, 2.0)
        click(CREDIT_CLAIM)
        click(CREDIT_CLOSE, 1.5)

        # 8) 回基地地图
        click(BACK_BTN2, 2.5)
        print("[infrast] 会客室线索收取完成", flush=True)
        return True


def register(resource: Resource) -> None:
    resource.register_custom_action("InfrastResumeStations", InfrastResumeStations())
    resource.register_custom_action("InfrastResetRound", InfrastResetRound())
    resource.register_custom_action("InfrastNextRound", InfrastNextRound())
    resource.register_custom_action("InfrastReception", InfrastReception())
    resource.register_custom_action("InfrastTodoCollect", InfrastTodoCollect())
    resource.register_custom_action("InfrastOpenTodo", InfrastOpenTodo())


# ---- 多轮收菜（用户经验：回主页再进基建可刷新待办，收菜卡住时重来一轮）----
_ROUND = {"n": 0}
ROUNDS = 2          # 基建收菜轮数（1 = 只收一轮）
BACK_BTN = (40, 40)  # 基建内「<」返回 → 主界面


class InfrastResetRound(CustomAction):
    """进入 Infrast 时重置轮次计数。"""

    def run(self, context, argv) -> bool:
        _ROUND["n"] = 0
        return True


class InfrastNextRound(CustomAction):
    """一轮收菜结束：返回 True（回主页，再进基建收下一轮）/ False（轮次用完，结束）。"""

    def run(self, context, argv) -> bool:
        _ROUND["n"] += 1
        if _ROUND["n"] >= ROUNDS:
            print(f"[infrast] 已完成 {_ROUND['n']} 轮，结束", flush=True)
            return False
        ctrl = context.tasker.controller
        print(f"[infrast] 第 {_ROUND['n']} 轮完成，回主界面准备再进基建", flush=True)
        ctrl.post_click(*BACK_BTN).wait()
        time.sleep(4.0)   # 基地→主页切换动画需要时间，2.5 秒不够会导致下一轮 Enter 点空
        return True


# ---- 待办事项收菜（用户口径：把左下角「待办事项」右边的按钮全部点完才算收成功）----
# 待办事项条上可能出现的按钮（负责人真机截图确认，缺少任何一个都会导致「有任务却不做」）
TODO_BUTTONS = (
    "可收获",       # 设施产物（制造站/贸易站）
    "订单交付",     # 贸易站订单（曾遗漏，导致订单堆着不收）
    "干员信赖",     # 干员信赖值
    "队列轮换",     # 换班队列
    "干员疲劳",     # 疲劳干员
    "干员休整",     # 待休整干员
)
BAR_LABEL = "待办事项"   # 待办条打开时左下角一定有这个标签（条开没开用它判断，比按钮稳）

# ---- 打开待办事项 ----
# 右上角 ⚠（EMERGENCY）与蓝铃铛（NOTIFICATION）上下堆叠：
#   ⚠ 本身就是一项收菜任务，点完并处理完后 ⚠ 消失，铃铛上移顶替它的位置。
# 蓝铃铛是**开关**：待办条打开时再点会关掉！所以必须
#   「点一次 → 检查待办条是否出现 → 没出现才点另一个位置」，绝不能无脑连点两次。
BELL_OCR = (1000, 50, 281, 140)
BELL_POSITIONS = ((1242, 97), (1242, 133))   # 上面(⚠或已上移的铃铛) / 下面(⚠在时的铃铛)
BELL_X = 1242


def _norm(text: str) -> str:
    return (text or "").replace(" ", "")


def bar_opened(texts) -> bool:
    """待办条是否已打开：OCR 到「待办事项」标签或任一待办按钮即算打开。

    ⚠ 真机实测：条收起时左下角什么都没有；条打开时一定有「待办事项」标签，
    因此标签比「有没有按钮」更可靠（按钮为 0 个时条仍然是开着的）。
    """
    for text in texts:
        t = _norm(text)
        if BAR_LABEL in t:
            return True
        if any(name in t for name in TODO_BUTTONS):
            return True
    return False


def todo_names_in(texts) -> list[str]:
    """OCR 文本里出现的待办按钮名（按 TODO_BUTTONS 优先顺序）。"""
    found = []
    normed = [_norm(t) for t in texts]
    for name in TODO_BUTTONS:
        if any(name in t for t in normed):
            found.append(name)
    return found


def pick_target(results, clicks, max_same: int = 3):
    """挑下一个要点的待办按钮。

    results: [(text, box)]（Infrast@OcrTodoBar 的识别结果）
    clicks:  {按钮名: 已点次数}
    策略：优先点**还没点过**的按钮；都点过了就挑点得最少的重试（「2个干员」这类
          点一次只处理一个），但同一个按钮最多 max_same 次，防止死循环。
    返回 (name, box) 或 None（没有任何按钮 / 全部点够次数）。
    """
    candidates: list[tuple[int, str, tuple[int, int, int, int]]] = []
    for name in TODO_BUTTONS:
        for text, box in results:
            if name in _norm(text):
                candidates.append((clicks.get(name, 0), name, box))
                break
    if not candidates:
        return None
    clickable = [c for c in candidates if c[0] < max_same]
    if not clickable:
        return None
    _count, name, box = min(clickable, key=lambda c: c[0])
    return name, box


def fresh_image(ctrl):
    """主动抓一帧新图（点击后必须用它，否则永远看到点击前的画面）。

    ⚠ 踩坑（2026-11-02）：CustomAction 里 `ctrl.cached_image` 返回的是
    **本节点做识别时**那张旧帧，点击之后不会刷新。用它去判断「待办条开没开」，
    就会永远看到点击前的画面 → 铃铛明明已经点开却判定「没打开」，然后补点第二下
    把条关掉 / 继续走流程，表现为「铃铛点不开、收菜没收」的静默失败。
    """
    try:
        img = ctrl.post_screencap().wait().get()
    except Exception:  # noqa: BLE001
        return None
    if img is None or getattr(img, "size", 0) == 0:
        return None
    return img


def ocr_todo_bar(context, img) -> list[tuple[str, tuple[int, int, int, int]]]:
    """跑 Infrast@OcrTodoBar 识别，返回 [(text, box)]。"""
    detail = context.run_recognition("Infrast@OcrTodoBar", img)
    out: list[tuple[str, tuple[int, int, int, int]]] = []
    if detail is None:
        return out
    for r in (getattr(detail, "all_results", None) or []):
        box = tuple(getattr(r, "box", ()))
        out.append(((getattr(r, "text", "") or ""), box))
    return out


class InfrastTodoCollect(CustomAction):
    """循环点击待办事项条上的按钮直到点完；不点设施图标（避免进入房间）。

    完成判据（负责人要求）：待办事项按钮全部消失才算收菜成功。
    每轮都用**新截图**判断（见 fresh_image 的踩坑说明）：
    - 条上没有任何按钮 → 连续 EMPTY_CONFIRM 次确认后算成功；
    - 按钮还在、但每个都点够 MAX_SAME 次仍不消失 → 返回 False（如实失败，不假装成功）。
    """

    EMPTY_CONFIRM = 2      # 连续空识别次数（防抖动误判）
    MAX_CLICKS = 12        # 最多点击轮次
    MAX_SAME = 3           # 同一个按钮最多点几次（「2个干员」这类要重复点）
    CLICK_WAIT = 3.0       # 点击后等待识别结果稳定

    def run(self, context, argv) -> bool:
        ctrl = context.tasker.controller
        clicks: dict[str, int] = {}
        empty_checks = 0
        for _ in range(self.MAX_CLICKS + self.EMPTY_CONFIRM):
            img = fresh_image(ctrl)
            if img is None:
                print("[infrast] 抓图失败，停止待办收菜", flush=True)
                return False
            results = ocr_todo_bar(context, img)
            texts = [t for t, _ in results]
            if not bar_opened(texts):
                # 真机实测：待办项清空后待办条会**自动收起**，所以「条不见了」= 已收完
                if clicks:
                    print(f"[infrast] 待办条已自动收起（已点 {sum(clicks.values())} 次，视为收完）", flush=True)
                else:
                    print("[infrast] 待办条未打开（按没有待办处理）", flush=True)
                return True
            if not todo_names_in(texts):
                empty_checks += 1
                if empty_checks >= self.EMPTY_CONFIRM:
                    print(f"[infrast] 待办事项已点完（连续 {empty_checks} 次确认）", flush=True)
                    return True
                time.sleep(0.8)
                continue
            empty_checks = 0
            target = pick_target(results, clicks, self.MAX_SAME)
            if target is None:
                stuck = [n for n in todo_names_in(texts) if clicks.get(n, 0) >= self.MAX_SAME]
                print(f"[infrast] 待办按钮点了 {self.MAX_SAME} 次仍在：{'/'.join(stuck)}", flush=True)
                return False
            name, box = target
            cx, cy = box[0] + box[2] // 2, box[1] + box[3] // 2
            print(f"[infrast] 点待办「{name}」({cx},{cy})", flush=True)
            ctrl.post_click(cx, cy).wait()
            clicks[name] = clicks.get(name, 0) + 1
            time.sleep(self.CLICK_WAIT)
        print("[infrast] 待办事项未清空（超过最大点击次数），标记失败", flush=True)
        return False


class InfrastOpenTodo(CustomAction):
    """点开待办事项条：点一次就检查是否打开，避免把刚打开的条又点关。"""

    CLICK_WAIT = 1.8       # 点击后等开合动画
    ENSURE_WAIT = 1.2      # 动画慢时的二次确认等待

    def _bar_visible(self, context) -> bool:
        img = fresh_image(context.tasker.controller)
        if img is None:
            return False
        return bar_opened([t for t, _ in ocr_todo_bar(context, img)])

    def run(self, context, argv) -> bool:
        ctrl = context.tasker.controller
        for attempt, (x, y) in enumerate(BELL_POSITIONS, start=1):
            if self._bar_visible(context):
                print("[infrast] 待办条已打开，不再重复点铃铛", flush=True)
                return True
            print(f"[infrast] 点铃铛 #{attempt} ({x},{y})", flush=True)
            ctrl.post_click(x, y).wait()
            time.sleep(self.CLICK_WAIT)
            if self._bar_visible(context):
                print(f"[infrast] 待办条已打开（第 {attempt} 次点击）", flush=True)
                return True
            time.sleep(self.ENSURE_WAIT)
            if self._bar_visible(context):
                print(f"[infrast] 待办条已打开（第 {attempt} 次点击，延迟确认）", flush=True)
                return True
        # 两次都没打开：可能本来就没有待办（条不会弹），交给 InfrastTodoCollect 判空
        print("[infrast] 铃铛两次点击后仍未打开待办条（按没有待办继续）", flush=True)
        return True

