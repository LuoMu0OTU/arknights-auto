# arknights-auto — 明日方舟本地自动化助手

![License](https://img.shields.io/badge/license-AGPL--3.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%2011-lightgrey.svg)
![Engine](https://img.shields.io/badge/engine-MaaFramework-orange.svg)
![Status](https://img.shields.io/badge/status-%E5%8F%AF%E7%94%A8-brightgreen.svg)

一个跑在**本机**、由 [MaaFramework](https://github.com/MaaXYZ/MaaFramework)（`MaaFw` Python 绑定）驱动的
明日方舟自动化程序。目标端为**官方 PC 客户端**（`E:\Arknights\Arknights.exe`）——
不需要模拟器、不注入进程、不改游戏文件，纯**图像识别 + 窗口截图**。

> 设计思路与识别素材大量参考 [MaaAssistantArknights](https://github.com/MaaAssistantArknights/MaaAssistantArknights)（MAA）。
> 与 MAA 的区别：MAA 是 C++ 全功能客户端，本项目是**轻量、可读、可改**的 Python 流水线实现，方便自行扩展。

## 📸 效果

| 主界面 | 公开招募 |
|:---:|:---:|
| ![](docs/images/home.jpg) | ![](docs/images/recruit.jpg) |

| 基建收菜 | 信用商店 |
|:---:|:---:|
| ![](docs/images/infrast.jpg) | ![](docs/images/mall.jpg) |

| 好友访问 | 自动刷图 |
|:---:|:---:|
| ![](docs/images/visit.jpg) | ![](docs/images/fight.jpg) |

## ✨ 功能与状态

| 功能 | 流水线 | 状态 | 说明 |
|------|--------|:----:|------|
| 启动 / 回主界面 / 消弹窗 | `common.json` | ✅ 稳定 | 自动处理公告、断线、活动弹窗 |
| 公开招募 | `recruit.json` | ✅ 稳定 | 标签识别 + 保底 4★ 词条组合，自动设 9:00 计时 |
| 基建收菜 | `infrast.json` | ✅ 稳定 | 进基建 → 点铃铛 → 逐个点待办收菜 |
| 好友访问 | `visit.json` | ✅ 稳定 | 好友列表 → 访问基建 → 「访问下位」连续访问 |
| 信用商店采购 | `mall.json` | ✅ 稳定 | 按优先级购买，可配置信用留存策略 |
| 任务 / 邮件 / 签到 | `award.json` | ✅ 稳定 | 每日一键领取 |
| 自动刷图 | `fight.json` | 🔶 可用 | 单场全自动（编队→代理指挥→结算）；选关导航待稳定 |
| 基建换班 | `infrast.json` | ⏳ 计划中 | 按预设干员自动轮换 |
| 吃药 / 碎石刷图 | — | ⏳ 计划中 | 默认关闭，避免误消耗 |

> 状态含义：✅ 真机验证通过 · 🔶 能跑但仍有边界情况 · ⏳ 尚未实现

## ⚙️ 环境要求

- **Windows 11**（10.0.1903+），已安装**明日方舟官方 PC 客户端**
- **Python 3.12**（⚠ 3.14 下 `onnxruntime` 等轮子缺失，**不要**用默认 `python`）
- 游戏窗口建议窗口化 **1280×720（16:9）**，并在游戏内 `设置 → 游戏` 把 **UI 缩放改为 100**
  （识别模板按 16:9 的 720p 标定；16:10 / 全屏会导致模板对不齐，与 MAA PC 端同款要求）

## 📦 便携安装包（无需 Python）

Phase 6 起提供 Windows 便携包（PyInstaller onedir，约 344 MB），**无需预装 Python**：

1. 下载并解压 `ArknightsAuto-windows.zip`（GitHub Release 发布包）。
2. 双击 `arknights-auto.exe` → 首次启动向导 → 环境检查 → 自动下载识别资源（需联网）。
3. 连接游戏（游戏客户端需管理员权限，会弹一次 UAC）→ 勾选任务 → 开始。
4. 配置/日志/识别资源都在 exe 旁目录；升级只替换 `arknights-auto.exe` + `_internal/`。

> **新用户请看 [用户指南](docs/USER_GUIDE.md)**（下载 → 首次启动 → 日常使用 → 常见问题）。详细构建与干净机验收清单见 [docs/BUILD.md](docs/BUILD.md)。

## 🚀 快速开始（源码运行）

### 方式 A：双击启动（推荐，无需命令行）

仓库根目录自带四个批处理脚本，**双击即用**：

| 脚本 | 作用 |
|---|---|
| **`首次安装.bat`** | 建 venv → 装依赖 → 生成配置 → 拉取 MAA 素材 → 自检（**只需跑一次**） |
| **`启动界面.bat`** | 图形界面（深色主题）：勾选任务、预设、一键日常、查看记录 |
| **`启动日常.bat`** | 前台跑日常全家桶，日志直接显示在窗口里 |
| **`静默日常.bat`** | 后台（最小化窗口）跑日常，输出写入 `logs\daily.log`，跑完自动关窗 |

> - 脚本要求已装 Python 3.12。双击「首次安装.bat」后，按提示确认 `config\config.json` 里的游戏路径即可。
> - 明日方舟官方客户端要求**管理员权限**，因此会拉起游戏的脚本（启动界面/启动日常/静默日常）双击时会弹一次
>   **UAC 授权窗口，请点「是」**；若已用管理员方式打开则不会再弹。

### 方式 B：命令行

```powershell
# 1) 用 3.12 建虚拟环境
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -U pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -e .

# 2) 组装 MAA 识别资源（模板图 / OCR 模型 / 数据表）
.\.venv\Scripts\python.exe -m ak_auto fetch-assets --tag v6.19.0

# 3) 复制配置并填写游戏路径
Copy-Item config\config.example.json config\config.json

# 4) 自检 → 跑日常
.\.venv\Scripts\python.exe -m ak_auto doctor
.\.venv\Scripts\python.exe -m ak_auto daily
```

> 改了启动脚本？用 `python tools/make_launchers.py` 重新生成即可
> （批处理必须以系统 ANSI 代码页 GBK 保存，否则 cmd 会按 936 解析 UTF-8 字节导致乱码）。

## 🎮 使用

```powershell
python -m ak_auto doctor                     # 环境 / 资源 / 窗口 / 截图自检
python -m ak_auto probe                      # 探测窗口与截图/输入方式，输出推荐配置
python -m ak_auto run Recruit                # 跑单个任务
python -m ak_auto run Fight --stage CE-6     # 指定关卡刷图
python -m ak_auto daily                      # 日常全家桶（按 task_order 顺序）
python -m ak_auto lint                       # 流水线静态校验
python -m ak_auto fetch-assets --tag v6.19.0 # 重新拉取 MAA 识别素材
```

运行日志在 `logs/`，失败截图与识别可视化在 `debug/`。

**日常默认顺序**（可在 `config.json` 的 `runtime.task_order` 覆盖）：

```
StartUp → AwardVisit(好友访问) → Infrast(基建收菜) → Mall(采购)
        → Recruit(公招) → Fight(刷图) → Award → AwardMail → AwardSignIn
```

> 先「好友访问 + 基建收菜」赚信用，再「采购」消费，符合信用商店的最优收益顺序。

## ❓ 常见问题

<details>
<summary><b>提示找不到游戏窗口 / 匹配错窗口</b></summary>

窗口匹配以**进程名**为准（默认 `Arknights`），不依赖标题，避免误匹配浏览器等标题含「明日方舟」的窗口。
若你的客户端进程名不同，改 `config.json` 的 `device.window_match.process_name`。
先用 `python -m ak_auto probe` 查看当前所有候选窗口。
</details>

<details>
<summary><b>识别不准 / 点不到按钮</b></summary>

九成是**分辨率或 UI 缩放**问题：请确认游戏窗口为 **1280×720**、游戏内 **UI 缩放 100%**。
本项目按 16:9 / 720p 标定模板；PC 端图标与手机端模板存在差异，因此关键入口采用
**固定坐标点击 + OCR 兜底** 的策略，分辨率一变就会错位。
</details>

<details>
<summary><b>报错缺少模板图 / OCR 模型</b></summary>

识别素材（模板图、OCR 模型、数据表）体积大且可再生成，**不进版本库**。
执行一次 `python -m ak_auto fetch-assets --tag v6.19.0` 即可生成到 `assets/` 下。
</details>

<details>
<summary><b>为什么必须 Python 3.12？</b></summary>

`onnxruntime` / `numpy` 等依赖在 3.14 上尚无可用轮子，装不上。用 `py -3.12 -m venv` 显式建环境。
</details>

<details>
<summary><b>刷图时理智不足会怎样？</b></summary>

会识别「理智不足」弹窗并**安全停止**（默认不吃药、不碎石），任务返回失败但不会误操作。
</details>

<details>
<summary><b>弹窗太多，偶尔卡住？</b></summary>

`common.json` 里的弹窗消化是**有限步数**的启发式，遇到全新的活动弹窗可能失效。
此时手动点掉一次即可；也欢迎按弹窗文字往 `DismissPopup` / `CloseAnno` 里加词条。
</details>

<details>
<summary><b>会封号吗？</b></summary>

本项目只是模拟人在本机的鼠标点击与截图，**不注入、不读内存、不改包**，行为特征与手动操作接近；
但**使用第三方工具本身可能违反游戏服务条款**，风险请自行评估（见下方免责声明）。
</details>

## 🏗 工作原理

```
┌──────────────┐   截图    ┌────────────────────┐   next/on_error   ┌──────────────────┐
│ 明日方舟 PC  │ ────────► │  MaaFramework 识别 │ ────────────────► │ 自写流水线 JSON  │
│   （窗口）   │ ◄──────── │ 模板匹配 / OCR     │      点击         │ assets/.../pipeline │
└──────────────┘   点击    └────────────────────┘                   └──────────────────┘
                                    ▲                                        │
                                    │            复杂判断（选标签 / 算信用 / 选商品）
                                    └──────────── Custom Action (Python) ◄────┘
```

- **流水线 JSON** 描述「识别什么 → 点击哪里 → 下一步是谁」，全部在 `assets/resource/pipeline/`，可直接改。
- 需要读数据、算最优解的地方（公招选标签、信用商店选商品）用 **Custom Action** 在 Python 里实现。

## 📁 目录结构

```
首次安装.bat / 启动界面.bat / 启动日常.bat / 静默日常.bat   一键启动脚本（GBK 编码，自动提权）
assets/resource/pipeline/   自写流水线 JSON（MaaFw 协议）
assets/resource/image/      模板图        ┐
assets/resource/model/ocr/  OCR 模型      ├ 由 fetch-assets 生成，不入库
assets/maa-vendor/          数据表        ┘
src/ak_auto/                应用代码（设备/调度/配置/报告 + 各任务）
src/ak_auto/tasks/          各任务的 Custom Action
docs/images/                README 截图
tools/                      资源获取 / 窗口探测 / 流水线校验 / 启动脚本生成
tests/                      测试（pytest）
config/                     config.example.json 等
```

## 📜 许可证与致谢

- 本项目代码与整体仓库：**AGPL-3.0**（见 [`LICENSE`](LICENSE)）
- 识别素材大量复用 [MaaAssistantArknights](https://github.com/MaaAssistantArknights/MaaAssistantArknights)
  （AGPL-3.0，tag `v6.19.0`）；来源与许可详见 [`NOTICE.md`](NOTICE.md)
- 运行时框架 [MaaFramework](https://github.com/MaaXYZ/MaaFramework)（LGPL-3.0）通过 `MaaFw` 动态调用

## ⚠️ 免责声明

本项目为**非官方、非营利**的个人辅助工具，与鹰角网络 / MAA 项目组**无任何隶属关系**。
使用本工具可能违反游戏服务条款，存在账号风险，**请自行评估并承担后果**。
请勿用于商业用途。

## 🔗 参考

- [MaaFramework 文档](https://maafw.com/)
- [MaaFramework Pipeline 协议](https://github.com/MaaXYZ/MaaFramework/blob/main/docs/zh_cn/3.1-%E4%BB%BB%E5%8A%A1%E6%B5%81%E6%B0%B4%E7%BA%BF%E5%8D%8F%E8%AE%AE.md)
- [MaaFramework Win32 控制方式](https://github.com/MaaXYZ/MaaFramework/blob/main/docs/zh_cn/2.4-%E6%8E%A7%E5%88%B6%E6%96%B9%E5%BC%8F%E8%AF%B4%E6%98%8E.md)
- [MaaAssistantArknights](https://github.com/MaaAssistantArknights/MaaAssistantArknights)
