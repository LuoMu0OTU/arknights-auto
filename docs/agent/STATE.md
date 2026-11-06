Agent 可恢复工作状态


每轮结束、上下文压缩前更新。这里记录当前事实，不代替 AGENTS.md 的长期规则。

> **每次会话开始必读：`docs/GAME_FLOW_NOTES.md`** —— 负责人（玩家本人）亲口确认的游戏流程口径、精确坐标、踩坑记录与已知未完成项。流水线行为以该文件为准。




更新日期：2026-11-02

当前阶段：Phase 7 持续维护（选关、基建收菜已修；Fight 暂移出日常序列）

本轮成果（2026-11-02 晚，负责人报告「铃铛点不开」）：
- **根因**：`InfrastOpenTodo` / `InfrastTodoCollect` 在 CustomAction 里用 `ctrl.cached_image` 判断点击结果，而它只是**本节点识别时**的旧帧、点击后不刷新 → 铃铛已点开待办条却判定"没打开"，补点第二下（点空/关掉），随后收菜识别不到按钮 → 报「待办事项已点完」静默跳过。
- **修复**：新增 `fresh_image(ctrl)`（每次 `post_screencap` 抓新帧）+ 判据改为 OCR「待办事项」标签（`bar_opened`）+ 按钮挑选用纯函数 `pick_target`/`todo_names_in`（同名按钮最多重点 3 次，点满仍在则如实失败）。`InfrastResumeStations` / `InfrastReception` 也改用新帧。
- **真机验证（1281×720）**：修复前 `点铃铛#1→#2→仍未打开→待办已点完`（收菜实际没做）；修复后 `点铃铛#1→待办条已打开→点「订单交付」(232,693)→点「干员休整」(257,688)→清空`，`Infrast` 两轮 112 秒 OK，铃铛角标消失。
- **新事实**：待办条清空后**自动收起**、铃铛角标同时消失；无 ⚠ 时铃铛在 (1242,97)，(1242,133) 点空。
- 测试：新增 `tests/test_infrast_todo_bar.py` 12 例；全套 144 例全绿；`tools/pipeline_lint.py` 0 错误 0 警告。
- 文档：`docs/GAME_FLOW_NOTES.md` 增加铁律 #8（cached_image 陷阱）、待办条开合真机表、⚠=铃铛同流程口径、第 10 节修复记录；CHANGELOG 增条目。
- 同步更新 skill `arknights-automation`：铁律 #7（cached_image）+ 铃铛定位纠错（OCR「NOTIFICATION」读不出来，改固定坐标 + 抓新帧验证）。
- **负责人 2026-11-02 口径（重要）**：⚠ 与铃铛是**同一套流程** —— 点哪个都打开底部「待办事项」条，照常点条上按钮即可，**不需要给 ⚠ 单独分支**；2026-10-26 的"⚠ 任务不同"作废。仅差 ⚠ 在场那天的真机复验。
- **待负责人决定**：无（"两位置改 3 次尝试"已判定不需要）。

上一轮重大成果（2026-10-31）：
- **新增选关流程**（HEAD 9b33ee2）：不再依赖不可靠的「前往上一次作战」（实测指向周本），改为 终端→资源收集(530,660)→货物运送→CE-6→开始行动→编队→战斗。真机 326 秒完整跑通一场。
- **公招四处修复**：聘用区域覆盖全 4 槽位、识别词改短词「聘用」、动画节奏放慢（聘用3s/跳过OCR+3s/结果页2.5s）、入口坐标修正到 (975,482)（原点到干员寻访）。
- **基建两处修复**：待办事项按钮收菜节点（可收获/干员信赖/队列轮换/干员疲劳/干员休整）；回主页等待 2.5s→4s、进基建 4s→5s（第 2 轮 Enter 点空）。
- **冷启动与活动**：新增开场引导页 START 节点（冷启动 87 秒）；主页左侧活动图标点击即领取 + 签到页 × (1248,92)；新增 `ReturnToHome@CloseSignin`（签到页只有 × 没有 ←，否则后续任务连锁失败）。
- **日常实测 14/15**（无战斗，137.9 秒），仅基建第 2 轮失败→已修（等待加长）。
- **便携包验证**：PATH 剥离后 `arknights-auto.exe tasks` 正常，证明不依赖系统 Python。
- **知识库**：skill `arknights-automation`（UI 位置/各任务口径/踩坑）+ 本仓库 `docs/GAME_FLOW_NOTES.md`。

当前分支：main

HEAD：见 `git log -1`（上一提交为 febcef9 订单交付；本轮铃铛/待办修复另有一提交）

工作区状态：见 git status

本轮获准任务：v0.1.0 已发布（Phase 6 完成）；授权进入 Phase 7 持续维护（按真实反馈修复 + 回归 + P2 扩展）。

本轮成果（Phase 6）：
- ADR-0003：打包选型 PyInstaller（onedir 便携）——理由见 docs/architecture/adr/ADR-0003-packaging.md。
- frozen 路径层（src/ak_auto/paths.py）：数据目录=exe 旁（可写）、bundle=_internal（只读）；首启 bootstrap 复制流水线/数据表/配置模板。
- fetch/lint 进程内化（src/ak_auto/assets_fetch.py + tools 薄包装）：打包版无 Python 解释器也可用；AssetManager.ensure 改进程内调用。
- PyInstaller 打包（packaging/ak_auto.spec + launcher.py + tools/build_windows.py）：dist/ArknightsAuto/arknights-auto.exe（约 344 MB）。
  - 控制台版构建 + GUI 启动时隐藏控制台（窗口版引导器在本机于 Python 之前静默崩溃，已规避并记录）。
  - 显式收集 maa/ak_auto 惰性导入子模块 + maa/bin 动态库（MaaFramework/onnxruntime/opencv 等）。
- 真机冒烟（打包版）：doctor 全绿（Python/MaaFw/资源/游戏路径/窗口）、GUI 首次启动向导弹出、`run ReturnToHome` 全栈跑通（控制器+OCR+点击+流水线）。
- CI：.github/workflows/ci.yml（test=pytest+lint，build=PyInstaller+artifact）。
- 文档：docs/BUILD.md（构建+干净机验收清单）、README 加便携包章节、ROADMAP/CHANGELOG 更新。

待办（Phase 6 收尾）：
- 干净机验收（用户另一台机器跑 docs/BUILD.md 清单）——本机无第二台干净机，如实待用户。
- 推送 7d661a5（shell 网络到 GitHub 间歇中断，已多次重试失败）。


已完成

- Phase 0：完整审计 + 测试基线 + 架构设计 + 路线图，已人工验收。
- Phase 1：八项全部完成并已人工验收。细节见 CHANGELOG.md 与 git 历史。
- 修复（用户报告：双击启动脚本崩溃）：launch_game 捕获启动异常（游戏清单 requireAdministrator，普通权限报 740）+ 三个启动器自动提权 + 新增「启动界面.bat」。测试 tests/test_device_launch.py 4 例。
- Phase 5 第 1 项 —— Fight 修复（代码与逐项验证完成；实战闭环按项目负责人指示跳过）：
  - 修复：自定义动作改用任务器传入的配置（原 `AppConfig.load()` 读全局配置）；runtime.build_tasker 传递 cfg。
  - decide_loops 纯函数：times 上限、min_sanity 下限；精确选次（列表从大到小、底部=1、每数字两条白线，times=1/最大可连战真机点击验证）；tests/test_fight_logic.py 6 例。
  - fight.json：入口坐标 (960,160)（修误触合成玉弹窗）、FormationStart 坐标校正（差 39px 点空=317s 卡住根因）、战报检测「已成功代理作战/行动结束」、盲等收尾流（DoNothing 300s + 截图自愈 + 清场点击）、超时 1500s。
  - 新增 FightRecoverCapture 自定义动作：restore 窗口+重截，DXGI ACCESS_LOST 自愈（入口/收尾真机验证有效）。
  - 逐项真机证据：战斗跑完（战报/信赖/掉落）、战报检测命中、收尾清场单独验证 25s、理智安全分支三次命中、精确选次 y=496 多次验证；人眼配合确认列表结构/弹窗按钮。
  - **按项目负责人指示跳过实战闭环**（理智不足）；连续链的「战报检测」受环境级约束（战斗独占渲染下两种截图均失效）→ 列入 Phase 7（配合图像输入模型）。选关（fight.stage 导航）未实现，同样 Phase 7。
- Phase 5 第 6 项 —— 信用购买优先级（P1 清单补充项）✅：
  - tasks/mall.py：MallSelectBuy 改用任务器配置，按 mall.buy_first 顺序购买（每项最多一次）、跳过 mall.blacklist；新增纯函数 pick_item（优先级/已买跳过/黑名单/OCR 截断容错）。
  - 原行为硬编码只买「加急许可」，现按配置执行（默认买招聘许可+寻访凭证）。
  - 测试：tests/test_mall_strategy.py 5 例，全套 113 例 exit=0。
- Phase 5 第 5 项 —— 截图回归扩展 ✅（无需真机的结构回归防线）：
  - 新增 tests/test_pipeline_structure.py 6 例：全部流水线 next/on_error 引用完整、Fight 链可达终节点且不跨文件、关键点击目标在 1280×720 内、自定义动作均已注册、回归夹具存在、任务目录入口全部在流水线中。
  - tests/fixtures/README.md：夹具采集流程与约束（为后续视觉模型/人工配合的扩展采集立规范）。
  - 全套 108 例 exit=0。
- Phase 5 第 2 项 —— 公招策略（tag_priority 消费）✅：
  - data/recruitment.py：best_selection 支持 tag_priority——命中时选优先级最高的标签单独选（先全量精确匹配再包含匹配，避免「资深干员」⊂「高级资深干员」误匹配）；未命中回退原保底逻辑。
  - tasks/recruit.py：RecruitSelectTags 改用任务器传入的配置（同 Fight 的配置传递修复）；runtime.py 同步。
  - 测试：tests/test_recruit_strategy.py 5 例（命中/顺序/回退/保底/空优先级），全套 102 例 exit=0。
- Phase 5 第 4 项 —— 运行统计 ✅：
  - 新增 application/stats.py：run_stats 聚合 logs/run-*.json（运行数/成功率/累计耗时/每任务 runs-ok-avg_ms，可限份数）。
  - 运行记录页顶部加聚合统计行（含「最常失败任务」）。
  - 测试：tests/test_stats.py 3 例；真机 logs 实测输出正常。
- Phase 4 第 2 项 —— GUI 模式切换 + 高级设置页：
  - 侧边栏底部「模式：简单/高级」切换：仅切 ui.mode 与可见项，**不重置任何参数**（已测：fight.times 切换前后不变）；高级设置导航项仅高级模式可见。
  - 新增 AdvancedPage（pages.py）：任务排序（上移/下移，写 runtime.task_order）、刷图高级（理智下限[已生效]/连续作战[计划中]）、公招高级（标签优先级[已生效]/次数/时长/保底/加急）、运行参数（重试/失败截图），范围验证 + 恢复默认 + 风险提示。
  - 任务中心：预设改为「每日常规 = 配置的 task_order + 内置推荐 + 自定义预设（按名应用）」；勾选序列按 task_order 排序生成（排序真正生效）。
  - 真机验证：模式切换按钮/可见性正确；测试新增 4 例，全套 84 例 exit=0。
- Phase 4 第 1 项 —— 配置 Schema v2：
  - config.py：CONFIG_SCHEMA_VERSION=2；新增 UiConfig（mode simple/advanced、theme dark/light，校验器）、PresetConfig（自定义预设）、fight.min_sanity（理智策略，计划中）、recruit.tag_priority（公招策略，计划中）、AppConfig.ui 与 AppConfig.custom_presets。
  - configsvc.py：注册 MIGRATIONS[1]（v1→v2 无字段搬移，仅刷新版本）。
  - config.example.json：升级到 v2 并附新字段。
  - 测试：迁移/校验/预设往返 4 例；本地真实 config v1→v2 无损加载验证；全套 80 例 exit=0。
- Phase 3 第 1 项 —— GUI 首页状态区：
  - worker.py：新增 task_state(task_id, 状态值) 与 seq_progress(已完成, 总数) 信号（由事件总线驱动，跨线程安全）。
  - 首页：运行状态标签（当前任务 — 状态机状态）+ 序列进度条；开始→准备中，结束→「已结束（k/n 成功）」。
  - 真机验证：跑 StartUp 时状态区「准备中…」+ 进度条可见，结束「已结束（1/1 成功）」。
  - 测试：tests/test_gui.py 新增 2 例（状态区流转 / worker 信号齐全），全套 74 例 exit=0。
- Phase 2 第 1 轮：
  - PySide6 6.12.0 加入 requirements/pyproject；NOTICE 增加 PySide6 LGPL 声明。
  - 新增 src/ak_auto/gui/：theme.py（深色设计令牌 + QSS + QPalette）、worker.py（TaskWorker(QThread) 桥接 ExecutionController：事件/结果经 Qt 信号回传、stop() 协作取消、finally 还原窗口）、main_window.py（侧边导航 + 四页面：首页（运行 StartUp/停止 + 日志窗）、任务中心（任务目录勾选展示）、运行记录、设置占位）、app.py（run_gui 入口）。
  - __main__.py 新增 `gui` 命令。
  - 测试：tests/test_gui.py 4 例（offscreen 冒烟：主窗口/主题/任务页/Worker 类型）。
  - 真机验证：真实窗口启动（1024×680、深色主题、2 秒自动关闭退出码 0）——DPI/字体/线程三风险的首项目检通过。
- Phase 2 第 2 轮：
  - 任务中心：勾选（任务目录全量，默认每日常规）+ 三个推荐预设（每日常规/快速收菜/公招与信用）+ `_sequence()` 生成执行序列（非 StartUp 前插 ReturnToHome，与 CLI daily 一致）+「开始执行」。
  - 首页：连接状态行（识别资源 + 游戏窗口，AssetManager/device 只读检查）；开始执行后自动切回首页看日志。
  - 真机验证：GUI 点击「运行 StartUp」→ TaskWorker → 真实 ExecutionController → StartUp OK（3.6s），事件实时进日志窗，停止按钮状态正确，退出码 0。
- Phase 2 第 3 轮：
  - 新增 src/ak_auto/gui/pages.py：SettingsPage（游戏路径/关卡/次数/用药/碎石/重试 编辑 + 保存（ConfigurationService 原子写）+ 恢复默认 + 付费资源风险提示）、RunLogPage（读 logs/run-*.json 列表 + 详情渲染）。
  - worker.py：任务结束自动保存运行报告（logs/run-*.json），运行记录页随之刷新。
  - 修复：Qt offscreen 与 MaaFw 同进程的解释器退出崩溃（0xC0000409）——模块级清理 fixture（deleteLater + processEvents），全套 exit=0。
- Phase 2 第 4 轮（收尾）：
  - 新增 src/ak_auto/gui/wizard.py：FirstRunWizard（欢迎 → 环境检查 → 游戏路径 → 资源准备 → 完成保存），首次运行（无 config.json）自动弹出；设置页加「重新运行首次向导」。
  - 首页加「上次结果」行（读最新 logs/run-*.json 摘要，运行结束后自动刷新）。
  - **真机验证：GUI 内停止真实任务**——任务中心勾选 StartUp/AwardVisit/Infrast/Mall 执行中点击停止 → post_stop → 当前任务 CANCELLED → 剩余任务全部跳过 → 窗口还原、退出码 0。
  - 测试：wizard 冒烟 1 例；全套 68 例 exit=0。


进行中 / 待办

Phase 5 剩余（如实状态，验收报告 docs/architecture/PHASE5_ACCEPTANCE.md）：
- Fight 完整战斗真机验证：**阻塞**——需人工在游戏里把连战次数重置为 ×1（本轮探索误设成未知值）；且需更谨慎的配合式验证。
- Fight 选关 / 精确选次：未实现（真机逆向风险高，保留「未完成」）。
- 基建换班 shift_presets：未完成（逐屏逆向工程量与风险大，保留「未完成」）。
- 截图回归扩展：框架已有（Phase 1），扩展采集待安全时机。


修改文件

- 本轮起：src/ak_auto/gui/（新增）、requirements.txt/pyproject.toml（加 PySide6）、NOTICE.md（LGPL 声明）、__main__.py（gui 命令）、tests/（GUI 冒烟测试）、docs/agent/STATE.md、CHANGELOG.md


测试与验证

命令	结果	环境/备注
python -m pytest -q	88 passed，exit=0	Python 3.12.10 / pytest 9.1.1
真机模式切换	简单↔高级，导航可见性/按钮正确，参数不重置	本机
真机 GUI 诊断页	自检 7 项全部通过，与 CLI doctor 一致	本机真实游戏
真机自定义预设端到端	高级模式保存「收菜公招」→ 应用 → 执行 6/6 成功（顺序按 task_order）	本机真实游戏
本地真实 config	v1→v2 无损迁移	—


已知问题 / 风险 / 阻塞

- GUI 与真实游戏并发使用时会抢输入控制者（GameWindowAdapter 已做单控制器互斥，GUI 内串行任务）。
- native_wheel（真实光标滚动）执行期间会抢用户鼠标，GUI 运行刷图任务时应提示用户勿动鼠标。
- 高 DPI/中文字体需真机目检（本轮原型验证点）。
- 沿用 Phase 0 审计风险清单其余项（Fight 选关、连战次数两缺陷、固定坐标脆弱等，属 Phase 5 范围）。


待真机验证

- GUI 窗口在 125%/150% DPI 下的布局与字体；
- GUI 内启动/停止真实任务的完整链路（首轮原型即验证 StartUp 一次）。


设计决策及 ADR

- ADR-0001：GUI 框架 PySide6 + Qt Widgets —— 随 Phase 2 授权确认采纳。
- ADR-0002：协作式取消（post_stop + 轮询）—— 已真机验证。


下一轮第一步

1. 重新读取 AGENTS.md、SESSION_START.md、本文件与 docs/ROADMAP.md。
2. 网络恢复后先推送本地提交（64843b5 起）。
3. Phase 5 待人工验收；验收后进入 Phase 6 发布工程（或先处理 Phase 7 的 Fight 收尾项）。


阶段验收状态


Phase 0：✅ 已人工验收（2026-10-13）
Phase 1：✅ 已人工验收（2026-10-13）
Phase 2：✅ 已人工验收（2026-10-13）
Phase 3：✅ 已人工验收（2026-10-13）
Phase 4：✅ 已人工验收（2026-10-13）
Phase 5：✅ 已人工验收（2026-10-17；Fight 实战闭环按指示跳过，换班/选关如实未完成）
Phase 6：✅ 完成并发布 v0.1.0（2026-10-20；打包/CI/文档/真机+准干净机验证；正式干净机验证因无第二台机器未做，已文档化）

## Phase 7-GUI 进展（2026-10-26）

- **G7.0 审计**：docs/architecture/PHASE7_GUI_AUDIT.md（任务事实矩阵 + 配置消费矩阵 + 缺陷清单）。
- **G7.1/G7.2 完成**：视觉重设计（琥珀金深色/浅色主题、品牌侧边栏、卡片化）、任务卡片内嵌真实参数（次数/理智下限/标签/采购优先级）、支持状态徽标、清理过时文案。
- **G7.3 完成**：状态栏全局停止、中文任务名/状态、运行耗时、结构化结果卡 + 失败建议、空闲自动刷新、诊断导出确认、高 DPI（125%/150%）验证、键盘焦点、5 项竞态防护测试。
- **G7.4**：CI 冒烟改为发布阻断（	asks 输出校验）；**干净 Windows 机器验收仍待第二台设备**。

- 测试基线：**132 passed**；流水线 lint 0 错误 0 警告；HEAD = 2c22008（G7.3 收尾）。
