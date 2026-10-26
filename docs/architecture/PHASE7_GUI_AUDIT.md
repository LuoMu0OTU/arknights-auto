# Phase 7-GUI 基线审计（G7.0）

> 依据：`docs/architecture/PHASE7_GUI_PRODUCTIZATION_PLAN.md` G7.0 要求。
> 审计日期：2026-10-26；基准提交：`b5074b4`（含 GUI 视觉重设计 + 自动唤醒）。
> 证据来源：仓库代码、128 项 pytest、流水线 lint、以及 2026-10-22 完整日常 17/17 实机记录。

---

## 1. GUI 现状清单

| 文件 | 行数 | 职责 | 状态 |
|---|---|---|---|
| `gui/main_window.py` | ~610 | 主窗口（品牌侧边栏、导航、模式/主题切换）、首页（HomePage）、任务中心（TaskPage） | 已重设计 |
| `gui/pages.py` | ~530 | 设置页、运行记录页、高级设置页、诊断页 | 已统一页头/卡片 |
| `gui/theme.py` | ~330 | 设计令牌（深/浅两套）+ QSS + 调色板 | 已重写 |
| `gui/wizard.py` | ~165 | 首次启动向导（5 页） | 已美化 + 中文按钮 |
| `gui/worker.py` | 69 | 后台执行线程（TaskWorker / UpdateWorker） | 稳定，未改 |
| `gui/app.py` | 39 | GUI 入口（主题、向导、更新检查） | 已支持主题读取配置 |

**导航结构**：首页 / 任务中心 / 运行记录 / 设置（+ 高级模式：高级设置 / 诊断）。
**入口**：`启动界面.bat`（源码）、`dist/ArknightsAuto/arknights-auto.exe`（便携包）、CLI `python -m ak_auto gui`。

---

## 2. 任务事实矩阵（单一事实来源 = 代码 + 测试 + 真机记录）

| 任务 | 显示名 | 实现 | 测试 | 真机验证 | 支持状态 |
|---|---|---|---|---|---|
| StartUp | 启动游戏/回到主界面 | `common.json` | ✅ | ✅ 12s（含自动唤醒） | **已验证可用** |
| ReturnToHome | 回到主界面 | `common.json` | ✅ | ✅ 多次 | **已验证可用** |
| AwardVisit | 好友访问 | `visit.json` | ✅ | ✅ 30s | **已验证可用** |
| Infrast | 基建收菜 | `infrast.json` + 4 个 CustomAction | ✅ | ✅ 91s（含会客室两轮） | **已验证可用**（换班未实现） |
| Mall | 信用商店采购 | `mall.json` + `MallSelectBuy` | ✅ | ✅ 7s | **已验证可用**（列表加载慢需等待） |
| Recruit | 公开招募 | `recruit.json` + `RecruitSelectTags` | ✅ | ✅ 64s（聘用+招募） | **已验证可用** |
| Fight | 自动刷图 | `fight.json` + 3 个 CustomAction | ✅ | ✅ 332s（单场端到端） | **有限制**：只打「上一次作战」；选关导航未实现 |
| Award | 任务领取 | `award.json` | ✅ | ✅ 3s（日常+周常） | **已验证可用** |
| AwardMail | 邮件领取 | `award.json` | ✅ | ✅ 4s | **已验证可用** |
| AwardSignIn | 签到 | `award.json` | ✅ | ✅ 4s | **已验证可用** |

**未实现（不得在 UI 中表现为可用）**：指定关卡自动导航、连战超出可视区精确选次、基建干员自动换班、定时任务、系统托盘。

---

## 3. 配置字段消费矩阵（关键发现）

| 配置项 | 默认值 | 是否被执行路径消费 | 实际用途 / 备注 |
|---|---|---|---|
| `fight.times` | 0 | ✅ `tasks/fight.py:decide_loops` | 次数上限（0=按理智自动） |
| `fight.min_sanity` | 0 | ✅ `decide_loops` | 理智低于该值停止 |
| `fight.stage` | CE-6 | ⚠ 部分 `decide_loops` | **仅用于 AP 消耗回落表**；不参与选关导航 |
| `fight.medicine` / `fight.stone` | 0 | ❌ | 计划中（UI 已标注付费风险） |
| `fight.series` | True | ❌ | 计划中 |
| `recruit.tag_priority` | [] | ✅ `tasks/recruit.py` | 公招标签优先 |
| `recruit.max_times` / `ensure_4star` / `time_hours` / `expedite` | — | ❌ | 计划中（当前用流水线内置策略） |
| `mall.buy_first` / `mall.blacklist` | 招聘许可/寻访凭证；家具零件 | ✅ `tasks/mall.py` | 购买优先级与黑名单 |
| `award.daily` / `weekly` / `mail` / `signin` | True | ❌ | 开关未接线（流水线固定执行全套） |
| `infrast.collect` / `shift_presets` / `morale_threshold` | — | ❌ | 换班相关，计划中 |
| `runtime.task_order` / `retry_per_task` | — | ✅ `scheduler.py` | 任务顺序与重试 |
| `updates.check_enabled` / `repo` | True / arknights-auto | ✅ `worker.py UpdateWorker` | 更新检查 |

> **结论**：UI 当前把「字段存在」与「功能生效」混在一起展示。G7.2 必须把**未消费字段标为「计划中（暂不生效）」或从常规流程隐藏**，只把真实生效的参数放到任务卡片里。

---

## 4. 交互缺陷清单（按优先级）

| # | 缺陷 | 影响 | 计划阶段 |
|---|---|---|---|
| 1 | 任务参数散落在「设置 / 高级设置」，任务卡片无配置入口 | 用户不知道某任务可配什么 | G7.2 |
| 2 | 未接线参数（award 开关、recruit 次数等）看起来可用 | 误导，改了不起作用 | G7.2 |
| 3 | 高级设置残留「计划中」旧文案（如"理智下限计划中"，实际已接线） | 状态不一致 | G7.2 |
| 4 | 运行中「停止」只在首页可见，其他页面无入口 | 运行中切页后无法停止 | G7.3 |
| 5 | 失败信息只有日志文本，无「原因/建议」结构化展示 | 用户不知下一步 | G7.3 |
| 6 | 首页状态仅在进入时刷新，运行结束才更新 | 游戏中途启动/关闭不同步 | G7.3 |
| 7 | CI 的 `doctor` 冒烟为 `continue-on-error: true` | 发布门槛形同虚设 | G7.4 |

---

## 5. 建议的最小改动范围（G7.2）

1. **任务卡片内嵌配置**（`main_window.py TaskPage`）：
   - Fight 卡：次数、理智下限、用药、碎石（后两项保留付费警示）
   - Recruit 卡：标签优先（真实生效）
   - Mall 卡：购买优先级、黑名单（真实生效）
   - 其余任务卡：显示支持状态说明，不提供假参数
2. **状态徽标统一**：`已验证 / 有限制 / 计划中`，由 `domain.TaskDefinition` 派生，不手写第二份状态。
3. **清理旧文案**：高级设置/设置页中与实际不符的「计划中」标注。
4. **保存反馈**：卡片内保存 → 状态行提示「已保存，下次运行生效」。

**不改**：执行核心、CLI、.bat、流水线、打包方式。

---

## 6. 测试基线

- 当前：`pytest -q` = **128 passed**；`tools/pipeline_lint.py` = 0 错误 0 警告。
- G7.2 需补充：任务卡片配置读写往返、简单/高级切换不丢参数、未接线参数不出现在可编辑区。
