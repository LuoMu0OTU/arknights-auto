# ak-auto 开发路线图（ROADMAP）

> 依据：AGENTS.md 第 6/8 节。每阶段有进入/退出条件；未经授权不得跳过验收或推进下一阶段。
> 当前阶段：**Phase 7（持续维护）** —— v0.2.0 已发布；GUI 专项（Phase 7-GUI）进行中，见 docs/architecture/PHASE7_GUI_PRODUCTIZATION_PLAN.md。

## 阶段总览

| 阶段 | 内容 | 验收要点 |
|---|---|---|
| **Phase 0 审计与基线** | 完整审计、测试基线、架构设计、技术选型、路线图 | ✅ 已人工验收（2026-10-12）：审计/架构/路线图齐全 |
| **Phase 1 核心解耦** | 统一任务接口、配置模型、状态机/事件、取消；CLI 不回归 | ✅ 已人工验收（2026-10-13）：CLI 行为不变 + 59 测试全绿 + 真机验收通过 |
| **Phase 2 GUI 基础** | 窗口/导航/首页/简单模式/向导/设置/日志 | ✅ 已人工验收（2026-10-13）：GUI 跑/停真实任务真机验证通过 |
| **Phase 3 核心集成** | 全部稳定任务接入 GUI，状态/异常/停止/配置同步 | ✅ 已人工验收（2026-10-13）：真机 GUI 完成日常 16/17 + 安全停止，验收报告见 docs/architecture/PHASE3_ACCEPTANCE.md |
| **Phase 4 高级模式** | 完整参数/预设管理/排序/诊断；两模式共享核心 | ✅ 已人工验收（2026-10-13）：真机自定义预设 6/6，验收报告见 docs/architecture/PHASE4_ACCEPTANCE.md |
| **Phase 5 自动化增强** | 逐项实现 P1 功能（选关/多次刷图/理智/换班等） | ✅ 收尾（待验收）：公招策略/运行统计/信用购买优先级/截图回归完成；Fight 代码+逐项真机证据（精确选次/坐标修正/截图自愈/安全分支），实战闭环按负责人指示跳过；换班/选关如实未完成（Phase 7） |
| **Phase 6 发布工程** | 打包、资源分发、CI、干净 Windows 验证、发布文档 | ✅ 完成并发布 v0.1.0（2026-10-20）：PyInstaller 便携包 + CI 全绿 + GitHub Release（AkAuto-windows.zip） |
| **Phase 7 持续维护** | 用户反馈修复、回归、P2 扩展 | v0.2.0 已发布（2026-10-22，完整日常 17/17）；GUI 专项 G7.0–G7.3 完成，G7.4 部分完成（干净机验收待第二台机器） |

## P0（最小可用产品）验收

> 在真实环境通过 GUI 执行已有任务并能正确反馈和安全停止；CLI 不回归。

| 能力 | 对应阶段 |
|---|---|
| 统一任务 API、执行状态和取消 | Phase 1 |
| GUI 框架、连接检测、首次启动向导、任务勾选与预设、真实任务调用、状态与日志、配置持久化、异常处理、基本 Windows 打包 | Phase 2–3、6 |

## P1（核心体验增强）——逐项单独验收，不能实现则保留「未完成」

| 功能 | 现状 | 依赖 |
|---|---|---|
| 稳定选关（读 stages.json 定位章节→关卡） | ❌ 未完成（「前往上一次作战」仅能到最近关卡；选关导航需图像输入） | Phase 7 |
| 多次刷图 + 连战次数自动选择 | 🔶 大体重写：列表结构人眼确认（从大到小、底部=1），times=1/最大可连战精确点击真机验证；times>1 滚动待完善；实战闭环按指示跳过 | Phase 7 |
| 理智策略（耗尽停止/吃药/碎石显式授权） | ✅ min_sanity 下限 + 理智不足弹窗安全分支（拒绝补理智）已实现并真机验证；吃药/碎石保持默认关闭 | — |
| 基建换班（shift_presets） | ⏳ 未实现（逐屏逆向工程量与风险大，如实保留） | Phase 7 |
| 公招策略、信用购买优先级 | ✅ 完成：tag_priority 消费 + mall 按 buy_first/blacklist 购买（各 5 测试） | — |
| 自定义排序、预设管理、运行统计、有限失败恢复 | ✅ 完成（排序/预设 Phase 4 验收；运行统计 Phase 5；有限重试 Phase 1） | — |

## P2（高级扩展）——P0/P1 稳定后评估，不得提前侵入核心

定时任务、资源版本管理、自动更新检查、多配置方案、诊断导出、系统托盘、条件编排、插件机制。

## Phase 7 持续维护 —— backlog（按真实反馈驱动）

> 优先级由项目负责人排定；「需图像输入」的项建议在具备视觉的会话中实施。

| 项 | 来源 | 阻塞/依赖 |
|---|---|---|
| ✅ Fight 端到端（入口→选次→战斗→战报检测→收尾） | Phase 5 遗留 | **已跑通（2026-10-22，322s SUCCEEDED）** |
| Fight 选关导航（fight.stage 定位章节→关卡） | Phase 5 未完成 | 需图像输入；当前用「前往上一次作战」打最近关卡 |
| Fight times>1 精确选次（可视区外滚动） | Phase 5 未完成 | times=1 已真机验证；>1 滚动待完善 |
| 基建换班（shift_presets） | Phase 5 未完成 | 需图像输入 |
| 正式干净机验证 | Phase 6 未做（无第二台机器） | 待有干净机 |
| ✅ P2：自动更新检查 / 多配置方案 / 诊断导出 | 宪章 P2 | 已落地（2026-10-22） |
| P2：定时任务 / 系统托盘 | 宪章 P2 | 评估：定时任务有人值守风险、系统托盘价值低，暂缓 |

## Phase 1 任务拆解（草案，供验收后开工）

> 目标：统一任务接口、配置模型、状态机/事件、取消；**保持 CLI 兼容**。不做 GUI、不改任务行为。

1. **TaskDefinition 目录**：把 10 个流水线入口（StartUp/ReturnToHome/AwardVisit/Infrast/Mall/Recruit/Fight/Award/AwardMail/AwardSignIn）登记为任务定义（稳定 ID、名称、分类、描述、参数 Schema、默认值、风险等级、前置条件、执行入口、超时、重试、结果与错误）。兼容层：`run <任务名>` 仍可用。
2. **ExecutionState 状态机**：Pending/Preparing/Running/Stopping/Succeeded/Failed/Cancelled；`ExecutionResult` 替代裸 `TaskResult`（保留其字段为兼容子集）。
3. **事件总线（最小）**：TaskStarted/TaskProgress/TaskCompleted/TaskFailed/TaskCancelled/ConnectionChanged，携带 run_id/task_id/时间戳/状态/诊断。
4. **ExecutionController（取消）**：协作式取消令牌；评估 `Tasker.post_stop` 是否可用，不可用则记录降级方案（有限等待 + 节点超时）。
5. **ConfigurationService**：schema_version、原子写、备份、损坏恢复、迁移框架；保持 `config.json` 兼容读取。
6. **Adapters 收敛（最小）**：MaaFrameworkAdapter / GameWindowAdapter / AssetManager 包一层（不重写内部逻辑），供 GUI 复用。
7. **测试**：为 1–6 补单元测试（Fake 控制器 + 录制截图）；保持现有 15 例全绿。
8. **CLI 兼容验收**：`run`/`daily`/`doctor`/`probe`/`restore` 行为与 Phase 0 一致（人工真机对照）。

**Phase 1 退出条件**：上述全部完成 + 单测覆盖新核心 + CLI 真机对照通过 + `docs/agent/STATE.md` 更新 + 人工验收。

## 各阶段进入/退出条件（通用模板）

- 进入：上一阶段人工验收通过；本阶段任务清单在 STATE.md 明确。
- 退出：本阶段验收命令全部通过（测试 + 真机项）；文档（STATE/ROADMAP/AD 相关）更新；人工验收通过。
- 例外：无法真机测试的项必须标注「待真机验证」并给出可复现步骤，不得标为完成。
