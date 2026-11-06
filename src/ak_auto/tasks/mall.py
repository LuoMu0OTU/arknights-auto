"""采购任务：信用商店购买（按配置的购买优先级 + 黑名单，Phase 5）。"""
from __future__ import annotations

from maa.custom_action import CustomAction
from maa.resource import Resource

from ..config import AppConfig


def _norm(text: str) -> str:
    return (text or "").strip().replace(" ", "")


def _box_xywh(box) -> tuple[int, int, int, int]:
    if hasattr(box, "x"):
        return (box.x, box.y, box.w, box.h)
    t = tuple(box)
    return (t[0], t[1], t[2], t[3])


def pick_item(
    items: list[str],
    buy_first: list[str],
    blacklist: list[str],
    already_bought: list[str],
) -> str | None:
    """信用购买优先级：按 buy_first 顺序选第一个「在售、未买过、不在黑名单」的物品。

    OCR 文本可能截断，匹配双向包含；返回配置里的物品名（找不到返回 None）。
    """
    in_sale = {_norm(t) for t in items if _norm(t)}
    bought = {_norm(t) for t in already_bought}
    black = {_norm(t) for t in blacklist}
    for want in buy_first:
        w = _norm(want)
        if not w or w in black or w in bought:
            continue
        for t in in_sale:
            if w in t or t in w:
                return want
    return None


def pick_any(
    items: list[str],
    blacklist: list[str],
    already_bought: list[str],
) -> str | None:
    """信用过多时兜底：买任意在售、不在黑名单、没买过的物品。"""
    black = {_norm(t) for t in blacklist}
    bought = {_norm(t) for t in already_bought}
    for t in items:
        n = _norm(t)
        if not n or n in black or n in bought:
            continue
        if any(b in n or n in b for b in black):
            continue
        return t
    return None


class MallSelectBuy(CustomAction):
    """在信用商店里按 buy_first 顺序购买物品（每项最多买一次）。"""

    def __init__(self, cfg: AppConfig) -> None:
        super().__init__()
        self.cfg = cfg
        self._bought: list[str] = []

    def _read_credit(self, context) -> int | None:
        """读取右上角信用数字（形如 262/300），解析出当前信用。"""
        try:
            img = context.tasker.controller.cached_image
            od = context.run_recognition("Mall@OcrCredit", img) if img is not None else None
        except Exception:  # noqa: BLE001
            return None
        if not od:
            return None
        import re
        for r in od.all_results:
            text = (getattr(r, "text", "") or "").replace(" ", "")
            m = re.search(r"(\d{1,4})", text)
            if m:
                return int(m.group(1))
        return None

    def run(self, context, argv) -> bool:
        img = context.tasker.controller.cached_image
        od = context.run_recognition("Mall@OcrItems", img)
        if not od:
            return False

        results = [r for r in od.all_results if getattr(r, "text", "") and getattr(r, "box", None)]
        items = [getattr(r, "text", "") for r in results]
        pick = pick_item(items, self.cfg.mall.buy_first, self.cfg.mall.blacklist, self._bought)
        if not pick:
            # 优先物品买完后：信用超过阈值就必须继续买（上限 300，超出次日清零）
            credit = self._read_credit(context)
            keep = self.cfg.mall.credit_keep_below
            if credit is not None and credit >= keep:
                pick = pick_any(items, self.cfg.mall.blacklist, self._bought)
                if pick:
                    print(f"[mall] 信用 {credit} ≥ {keep}，继续购买 {pick} 以降低信用", flush=True)
                else:
                    print(f"[mall] 信用 {credit} ≥ {keep}，但已无可买物品", flush=True)
                    return False
            else:
                print(f"[mall] 无可买物品（目标={self.cfg.mall.buy_first} 已买={self._bought} 信用={credit}），停止", flush=True)
                return False

        for r in results:
            text = _norm(getattr(r, "text", ""))
            if _norm(pick) in text or text in _norm(pick):
                x, y, w, h = _box_xywh(getattr(r, "box"))
                context.tasker.controller.post_click(x + w // 2, y + h // 2).wait()
                self._bought.append(pick)
                print(f"[mall] 购买 {pick} ({x},{y},{w},{h})", flush=True)
                return True
        return False


def register(resource: Resource, cfg: AppConfig) -> None:
    resource.register_custom_action("MallSelectBuy", MallSelectBuy(cfg))
