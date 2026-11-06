# 交接单：待解决问题（下次会话直接看这个）

> 生成时间：2026-11-02
> 会话开始时**必读顺序**：`AGENTS.md` → 本文件 → `docs/GAME_FLOW_NOTES.md` → `docs/agent/STATE.md`

## 当前确定事实

- 分支 `main`，HEAD `febcef9`，工作区干净
- 128 单测全绿，`python tools/pipeline_lint.py` 0 错误 0 警告
- 游戏窗口客户区 **1280×720（比例 1.778）**，与 MaaFw 抓图基准 1281×720 匹配 → 坐标基准正确
- 负责人桌面跑的是**源码版**（`启动界面.bat` → `python -m ak_auto gui`），改代码即时生效

## 问题 1（最高优先级）：基建铃铛点不开待办条

### 现象（负责人真机复现 4 次）
- 待办条明明有任务（可收获 5 / 订单交付 1 / 队列轮换 / 干员疲劳 1），脚本**没去点**
- 日志却打印 `[infrast] 待办事项已点完（连续 2 次确认）` 并**报 success**

### 已确认的日志证据
```
[infrast] 点铃铛 #1 (1242,97)
[infrast] 点铃铛 #2 (1242,133)
[infrast] 铃铛两次点击后仍未打开待办条   ← 铃铛没点开
[infrast] 待办事项已点完（连续 2 次确认） ← 假成功
[infrast] 点铃铛 ... 会客室 ...
[infrast] 已完成 2 轮，结束
Infrast: OK (106~110s)
```

### 已排除
- 坐标基准错误（窗口 1280×720 与抓图基准匹配）
- 连点两次把条点关（已改为「点一次→检查→没开才点第二位」，`5ca6c4b`）

### 待查方向
1. **点击是否落到游戏**：窗口未在前台 / 被其他窗口遮挡时点击可能无效。考虑点击前 `SetForegroundWindow`
2. **待办条展开动画时长**：`time.sleep(2.2)` 后检测，可能条还没展开 → 试 3~4 秒
3. **`_bar_visible()` 的 OCR 是否有效**：它调用 `context.run_recognition("Infrast@OcrTodoBar", img)`，节点 roi 为 `[0,630,900,90]`。
   - **建议加调试**：点击后立即 `device.save_image` 存图到 `debug/shots/`，人工核对条是否真的打开
   - 再单独对该图跑 OCR，确认 `可收获/订单交付` 能否被识别
4. **按钮 OCR 可能漏读**：「可收获」是 3 个中文字，MaaFw OCR 应该能读，但要用截图验证
5. **失败必须可见**：`InfrastTodoCollect` 超过最大轮次已 `return False`，但「铃铛没打开」分支目前仍 `return True`（假成功）→ **必须改为 False 或抛出明确错误**

### 关键代码位置
- `src/ak_auto/tasks/infrast.py`
  - `TODO_BUTTONS`（已含 可收获/订单交付/干员信赖/队列轮换/干员疲劳/干员休整）
  - `InfrastOpenTodo.run()` —— 铃铛点击 + `_bar_visible()` 判定
  - `InfrastTodoCollect.run()` —— 待办按钮循环点击 + 连续 2 次确认 + 未清空返回 False
- `assets/resource/pipeline/infrast.json` —— `Infrast@Bell`（Custom）、`Infrast@OcrTodoBar`（OCR roi `[0,630,900,90]`）、`Infrast@TodoCollect`

## 问题 2：信用采购（Mall）有 bug

**负责人尚未说明具体现象**，下次会话需先问清楚：
- 是买不到东西（OCR 识别不到商品）？
- 还是买多了/买错了（把不该买的买了）？
- 还是买完回不到主页（Mall 结束时停在商店页，ReturnToHome 可能失败）？
- 还是信用点不够时的处理不对？

### 关键代码位置
- `assets/resource/pipeline/mall.json`（`CollectCredit` / `Buy`，`Buy.pre_delay=1000`、`CollectCredit.post_delay=3000`）
- 配置项：`mall.buy_first`（购买优先级）、`mall.blacklist`
- 已知历史问题：商品列表加载慢（>3 秒），OCR 前等待不足会误判"无可买物品"

## 问题 3：基建任务「日志报成功但实际没完成」

### 现象
任务结束时游戏停在会客室线索板，但日志报 success。

### 建议
给 `Infrast` 加**最终状态校验**：任务结束前确认已回到基地或主页，否则返回失败。
参考节点：`Infrast@Done` 之前加一个「IsBase」校验节点（OCR `待办事项/控制中枢`）。

## 问题 4（已缓解待验证）：会客室收尾

- 负责人第 4 次实验时会客室已全部完成，脚本只是"走流程"（没有实际可做的），属正常
- 但第 1 次实验时曾停在会客室线索板 → 需确认会客室内部流程（线索交流→接收→传递→信用奖励→返回）是否完整
- 参考 `docs/GAME_FLOW_NOTES.md` 第 2 节「会客室」完整流程
- 代码：`src/ak_auto/tasks/infrast.py` 的 `InfrastReception`

## 已知未完成（负责人后续补充）

| 项 | 状态 |
|---|---|
| ⚠（EMERGENCY）任务具体流程 | 负责人未说明，只确认「与普通收菜不同」 |
| 基建特殊待办项（需点具体设施） | 除会客室外未逐项确认 |
| 资源收集其它分类坐标 | 只标定了「货物运送」，LS/SK/AP 未测 |
| 公招职业标签实际效果 | 策略已支持但未验证 |
| 周本（每周部署） | 不支持 |
| 自动更新机制 | 未实现 |

## 下次会话第一步（精确）

1. 跑 `git log --oneline -3` + `pytest -q` + `python tools/pipeline_lint.py` 确认基线
2. 问负责人信用采购的具体 bug 现象
3. 按「问题 1」的待查方向，在 `InfrastOpenTodo` 里加调试截图 + 单独 OCR 验证
4. 修好后把「铃铛没打开」分支改为返回 False（不再假成功）
5. 真机跑一次基建，确认日志出现「待办事项已点完（连续 2 次确认）」且游戏回主页
