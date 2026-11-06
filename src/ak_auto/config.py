"""配置模型与加载。

对应 `config/config.json`（模板见 `config/config.example.json`）。
所有字段都提供默认值，缺字段/旧配置也能安全加载。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator

from .paths import data_dir

# 数据目录：开发模式=仓库根；打包模式=exe 旁目录（ADR-0003 配置与程序分离）
PROJECT_ROOT = data_dir()


class WindowMatch(BaseModel):
    class_name: str = ""
    title_contains: str = "明日方舟"
    process_name: str = "Arknights"


class DeviceConfig(BaseModel):
    kind: str = "win32"
    window_match: WindowMatch = Field(default_factory=WindowMatch)
    screencap: list[str] = Field(
        # DXGI 优先：战斗切换渲染管线时 FramePool(PrintWindow) 会长时间截图失败（真机实测）
        default_factory=lambda: ["DXGI_DesktopDup_Window|ScreenDC", "FramePool|PrintWindow"]
    )
    mouse_input: list[str] = Field(
        default_factory=lambda: [
            "SendMessageWithCursorPos",
            "PostMessageWithCursorPos",
            "AnchoredTouch",
            "Seize",
        ]
    )
    keyboard_input: str = "PostMessage"
    inference: str = "directml"  # directml | cpu

    @field_validator("kind")
    @classmethod
    def _kind(cls, v: str) -> str:
        if v not in ("win32", "adb"):
            raise ValueError(f"device.kind 只能是 win32/adb，得到 {v!r}")
        return v


class StartupConfig(BaseModel):
    game_path: str = r"E:\Arknights\Arknights.exe"
    launch: bool = True


class FightConfig(BaseModel):
    stage: str = "CE-6"
    times: int = 0          # 0 = 直到理智耗尽
    medicine: int = 0       # 用药数量
    stone: int = 0          # 碎源石数量（默认关闭）
    series: bool = True     # 连续作战
    min_sanity: int = 0     # 理智策略：低于该值停止刷图（0=不限）—— 计划中：战斗任务 Phase 5 消费


class InfrastConfig(BaseModel):
    collect: bool = True
    shift_presets: list[str] = Field(default_factory=list)
    morale_threshold: float = 0.3


class RecruitConfig(BaseModel):
    max_times: int = 4
    ensure_4star: bool = True
    time_hours: int = 9
    expedite: bool = False
    tag_priority: list[str] = Field(default_factory=list)  # 公招标签优先策略 —— 计划中：Phase 5 消费


class MallConfig(BaseModel):
    buy_first: list[str] = Field(default_factory=lambda: ["招聘许可", "寻访凭证"])
    blacklist: list[str] = Field(default_factory=lambda: ["家具零件"])
    # 每日信用上限 300，超出部分次日清零 → 领完信用后必须把它花到这个数以下
    credit_limit: int = Field(default=300, ge=0, le=3000)
    credit_keep_below: int = Field(default=300, ge=0, le=3000)


class AwardConfig(BaseModel):
    daily: bool = True
    weekly: bool = True
    mail: bool = True
    signin: bool = True


class RuntimeConfig(BaseModel):
    task_order: list[str] = Field(
        default_factory=lambda: [
            "StartUp", "AwardVisit", "Infrast", "Mall", "Recruit", "Fight",
            "Award", "AwardMail", "AwardSignIn",
        ]
    )
    retry_per_task: int = 2
    screenshot_on_error: bool = True


class UiConfig(BaseModel):
    """界面偏好（简单/高级模式切换不得重置其它参数）。"""

    mode: str = "simple"   # simple | advanced
    theme: str = "dark"    # dark | light（浅色主题后续轮次实现）

    @field_validator("mode")
    @classmethod
    def _mode(cls, v: str) -> str:
        if v not in ("simple", "advanced"):
            raise ValueError(f"ui.mode 只能是 simple/advanced，得到 {v!r}")
        return v

    @field_validator("theme")
    @classmethod
    def _theme(cls, v: str) -> str:
        if v not in ("dark", "light"):
            raise ValueError(f"ui.theme 只能是 dark/light，得到 {v!r}")
        return v


class UpdatesConfig(BaseModel):
    """更新检查（Phase 7）：只检查+提示，不自动下载安装。"""

    check_enabled: bool = True   # 启动时后台检查新版本
    repo: str = "LuoMu0OTU/arknights-auto"


class PresetConfig(BaseModel):
    """自定义任务预设（与内置推荐预设区分：内置预设不落配置）。"""

    name: str = ""
    task_ids: list[str] = Field(default_factory=list)


CONFIG_SCHEMA_VERSION = 2  # 当前配置 Schema 版本（ConfigurationService 负责迁移）


class AppConfig(BaseModel):
    schema_version: int = CONFIG_SCHEMA_VERSION
    device: DeviceConfig = Field(default_factory=DeviceConfig)
    startup: StartupConfig = Field(default_factory=StartupConfig)
    fight: FightConfig = Field(default_factory=FightConfig)
    infrast: InfrastConfig = Field(default_factory=InfrastConfig)
    recruit: RecruitConfig = Field(default_factory=RecruitConfig)
    mall: MallConfig = Field(default_factory=MallConfig)
    award: AwardConfig = Field(default_factory=AwardConfig)
    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)
    ui: UiConfig = Field(default_factory=UiConfig)
    updates: UpdatesConfig = Field(default_factory=UpdatesConfig)
    custom_presets: list[PresetConfig] = Field(default_factory=list)

    @classmethod
    def load(cls, path: str | Path | None = None) -> "AppConfig":
        """从 JSON 加载；文件不存在/字段缺失时回退到默认值。"""
        p = Path(path) if path else PROJECT_ROOT / "config" / "config.json"
        data: dict[str, Any] = {}
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
        return cls.model_validate(data)

    def dump(self, path: str | Path | None = None) -> Path:
        p = Path(path) if path else PROJECT_ROOT / "config" / "config.json"
        p.write_text(
            json.dumps(self.model_dump(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return p


def default_config_path() -> Path:
    return PROJECT_ROOT / "config" / "config.json"
