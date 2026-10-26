"""Domain 层：任务定义目录（Phase 1 任务 1）。

对应 AGENTS.md 第 2.5 条的「任务统一定义」：
稳定 ID、名称、分类、描述、参数 Schema、默认/推荐值、风险等级、
前置条件、执行入口、超时、重试、结果与错误。
"""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator


class ParamSpec(BaseModel):
    """任务参数描述（值实际存放在 config 的对应分区，Phase 4 再做参数化 UI）。"""

    key: str
    label: str
    kind: str = "str"  # int / float / bool / str / enum
    default: Any = None
    description: str = ""
    options: list[str] = Field(default_factory=list)


class TaskDefinition(BaseModel):
    """一个可执行任务的定义。"""

    id: str  # 稳定 ID：与流水线入口同名（英文）
    name: str  # 中文显示名
    category: str  # 分类
    description: str = ""
    entry: str = ""  # 执行入口（pipeline 节点名；留空 = 与 id 相同）
    params: list[ParamSpec] = Field(default_factory=list)
    recommended: dict[str, Any] = Field(default_factory=dict)
    risk_level: str = "low"  # low / medium / high
    preconditions: list[str] = Field(default_factory=list)
    timeout_ms: int = 20000  # 单任务整体建议超时；0 = 不限（实际超时由 pipeline 节点决定）
    retries: int = 2
    errors: dict[str, str] = Field(default_factory=dict)  # 错误码 → 用户可读说明

    @model_validator(mode="after")
    def _fill_entry(self) -> "TaskDefinition":
        if not self.entry:
            self.entry = self.id
        return self


TASK_CATALOG: list[TaskDefinition] = [
    TaskDefinition(
        id="StartUp",
        name="启动游戏 / 回到主界面",
        category="系统",
        description="启动客户端（如未运行）并消化启动/公告/活动弹窗，直到回到主界面。",
        risk_level="low",
        preconditions=["游戏可启动或已运行", "识别资源已组装（fetch-assets）"],
        timeout_ms=180000,
        errors={"no-window": "未找到游戏窗口，且自动启动失败。请确认 config 的 startup.game_path。"},
    ),
    TaskDefinition(
        id="ReturnToHome",
        name="回到主界面",
        category="系统",
        description="从任意界面返回主界面（日常序列中用于任务之间不串场）。",
        risk_level="low",
        timeout_ms=60000,
    ),
    TaskDefinition(
        id="AwardVisit",
        name="好友访问",
        category="日常",
        description="好友列表 → 访问基建 →「访问下位」连续访问，赚取信用。",
        risk_level="low",
        preconditions=["已登录账号", "好友列表可用"],
        recommended={"visits": 10},
    ),
    TaskDefinition(
        id="Infrast",
        name="基建收菜",
        category="基建",
        description="进基建 → 自动恢复停工的制造站/贸易站 → 会客室线索全套 → 收菜（多轮）。",
        risk_level="low",
        params=[
            ParamSpec(key="collect", label="收菜", kind="bool", default=True),
            ParamSpec(key="shift_presets", label="换班预设", kind="str", default=[], description="计划中"),
            ParamSpec(key="morale_threshold", label="心情阈值", kind="float", default=0.3, description="计划中"),
        ],
        recommended={"collect": True},
        preconditions=["基建已解锁"],
    ),
    TaskDefinition(
        id="Mall",
        name="信用商店采购",
        category="采购",
        description="采购中心 → 信用交易所 → 按 buy_first 优先级购买，blacklist 跳过。",
        risk_level="low",
        params=[
            ParamSpec(key="buy_first", label="优先购买", kind="str", default=["招聘许可", "寻访凭证"]),
            ParamSpec(key="blacklist", label="黑名单", kind="str", default=["家具零件"]),
        ],
        preconditions=["信用充足或已收基建信用"],
    ),
    TaskDefinition(
        id="Recruit",
        name="公开招募",
        category="公招",
        description="公开招募：先聘用已完成的候选人，再按标签策略开新招募。",
        risk_level="low",
        params=[
            ParamSpec(key="max_times", label="最大招募次数", kind="int", default=4),
            ParamSpec(key="ensure_4star", label="保底 4★", kind="bool", default=True),
            ParamSpec(key="time_hours", label="招募时长(小时)", kind="int", default=9),
            ParamSpec(key="expedite", label="立即加急", kind="bool", default=False, description="计划中"),
        ],
        preconditions=["公开招募可用", "有招募许可或龙门币"],
    ),
    TaskDefinition(
        id="Fight",
        name="自动刷图",
        category="战斗",
        description="前往上一次作战 → 代理指挥 → 战斗 → 识别战报结算。",
        params=[
            ParamSpec(key="stage", label="关卡", kind="str", default="CE-6", description="仅用于理智消耗回落表；选关导航计划中"),
            ParamSpec(key="times", label="次数", kind="int", default=0, description="0 = 直到理智耗尽"),
            ParamSpec(key="medicine", label="用药", kind="int", default=0, description="计划中（暂不生效）"),
            ParamSpec(key="stone", label="碎石", kind="int", default=0, description="计划中（暂不生效）；付费资源"),
            ParamSpec(key="series", label="连续作战", kind="bool", default=True, description="计划中（暂不生效）"),
        ],
        recommended={"times": 0, "medicine": 0, "stone": 0},
        risk_level="high",
        preconditions=["理智 ≥ 单次消耗", "编队可用"],
        timeout_ms=300000,
        errors={
            "sanity-short": "理智不足，已安全停止（默认不吃药、不碎石）。",
            "stage-nav": "选关导航失败：'前往上一次作战'可能指向了错误关卡（已知问题）。",
        },
    ),
    TaskDefinition(
        id="Award",
        name="任务领取",
        category="领奖",
        description="领取日常/周常任务奖励。",
        risk_level="low",
    ),
    TaskDefinition(
        id="AwardMail",
        name="邮件领取",
        category="领奖",
        description="收取所有邮件（顺带清掉邮件通知，避免挡主界面识别）。",
        risk_level="low",
    ),
    TaskDefinition(
        id="AwardSignIn",
        name="签到",
        category="领奖",
        description="每日签到领取。",
        risk_level="low",
    ),
]

_CATALOG_BY_ID = {t.id: t for t in TASK_CATALOG}
_CATALOG_BY_NAME = {t.name: t for t in TASK_CATALOG}


def all_tasks() -> list[TaskDefinition]:
    """全部任务定义（按注册顺序）。"""
    return list(TASK_CATALOG)


def resolve_task(token: str) -> Optional[TaskDefinition]:
    """按 ID 或中文名解析任务；不区分大小写、忽略首尾空白。

    解析不到返回 None（调用方自行决定是否当作原始流水线节点名处理）。
    """
    key = (token or "").strip()
    if not key:
        return None
    if key in _CATALOG_BY_ID:
        return _CATALOG_BY_ID[key]
    low = key.lower()
    for t in TASK_CATALOG:
        if t.id.lower() == low or t.name == key:
            return t
    return None
