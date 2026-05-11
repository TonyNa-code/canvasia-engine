<p align="center">
  <img src="docs/github/canvasia-engine-hero.png" alt="Canvasia Engine hero" width="100%" />
</p>

<h1 align="center">Canvasia Engine</h1>

<p align="center">
  一套面向视觉小说 / Galgame 创作者的可视化引擎原型。<br />
  目标是让“不懂编程的人”，也能用上传素材、输入台词、点按钮和可视化编辑的方式完成游戏开发。
</p>

<p align="center">
  <img src="https://img.shields.io/badge/status-source--available%20preview-3fb7ff?style=for-the-badge" alt="Status: Source-Available Preview" />
  <img src="https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-0e1628?style=for-the-badge" alt="Platforms" />
  <img src="https://img.shields.io/badge/tests-smoke%20%2B%20playwright-1fc98b?style=for-the-badge" alt="Tests" />
  <img src="https://img.shields.io/badge/license-Creator%20License%201.0-f5c451?style=for-the-badge" alt="Creator License 1.0" />
</p>

<p align="center">
  <a href="#快速开始">快速开始</a> ·
  <a href="#当前已经有的核心能力">核心能力</a> ·
  <a href="#功能状态">功能状态</a> ·
  <a href="#界面预览">界面预览</a> ·
  <a href="#发布状态">发布状态</a> ·
  <a href="CONTRIBUTING.md">参与贡献</a>
</p>

---

## 项目定位

Canvasia Engine 当前更适合这样理解：

- `源码可见创作者预览版`
- `Early Access / Preview`
- `适合独立开发者、同人作者、内部测试成员先拿来试做项目`

当前版本已经具备较完整的编辑器能力、导出能力和自动化测试基础，但仍然保留以下发布边界：

- 已接入后端 smoke、浏览器 Playwright smoke 和发布前自检脚本
- 适合做小型项目试制、导出链验证、功能体验和问题反馈
- 仍按 **Preview / Early Access** 口径发布；正式商业稳定版会在签名、公证、安装器和长流程点测进一步完成后单独标记

## 当前已经有的核心能力

- 可视化剧情编辑器
- 项目中心与空白新建项目
- 新手模式 / 高级模式分层
- 角色、素材、台词台本、配音工作流
- 首页今日工作台、最终发表门禁、项目巡检、项目医生小白修复向导、项目医生回执导出 / 复制 / 编号、成品目标路线、一键安全修复低风险结构问题、一键发布前修复顺序、素材性能预算、发布总控 Markdown / JSON 报告、自动回归试玩路线测试
- Canvasia Assistant 智能创作助手：支持零配置本地模板，也支持创作者自带 OpenAI、DeepSeek、通义千问、Kimi、智谱 GLM 或自定义兼容 API Key 调用真模型生成剧情、建议、素材提示、灵感盒归档包和可插入剧情卡片
- 正式存档 / 读档、系统菜单
- 项目级成品 UI 皮肤、UI Kit 部件绑定、九宫格贴图、按钮多状态贴图、布局位置微调与视觉小说文本框设计
- EXTRA 回想馆、图鉴馆、成就馆、章节回放、结局回放、语音回听
- 高级粒子系统、项目级粒子预设库
- Live2D / 3D 角色模型与 3D 场景资产导入，原生 Runtime 可输出 glTF 结构、材质贴图槽、动画通道、依赖、引用位置和转换建议清单
- 网页试玩包、Windows 桌面包、编辑器桌面包、三系统编辑器套装
- 自动化测试体系（本地 CI 预检 + 按钮动作覆盖扫描 + 未接线按钮运行时兜底 + 后端 smoke + Playwright 浏览器烟测）

## 功能状态

| 模块 | 当前状态 | 说明 |
| --- | --- | --- |
| 剧情 / 分支编辑 | 可用 | 支持可视化卡片、选项跳转、条件与变量、场景树筛选。 |
| 素材管理 | 可用 | 支持背景、角色、CG、BGM、音效、语音、字体等素材导入、替换、删除、使用保护与发布前体积预算提示。 |
| 智能创作助手 | 可用 | 默认本地模板；可选自带 OpenAI、DeepSeek、通义千问、Kimi、智谱 GLM 或自定义兼容 API Key 的真模型模式；支持灵感盒搜索、收藏保留、卡片预览、勾选插入、单条 / 全量 Markdown 创作档案、单条导出、全部归档、导入与本机 Key 遗忘。 |
| 项目安全网 | 可用 | 支持自动快照、版本恢复、崩溃恢复、正式存档 / 读档、首页今日工作台、最终发表门禁、项目医生修复队列、项目医生可追溯回执、成品目标路线、入口场景 / 章节顺序 / 场景顺序的一键安全修复、发布前检查与发布总控 Markdown / JSON 报告导出。 |
| 成品 UI 自定义 | 可用 | 支持项目级 UI 皮肤、按钮多状态、九宫格贴图、布局位置与视觉小说文本框设计。 |
| EXTRA / 回想系统 | 可用 | 支持图鉴馆、回想馆、成就馆、章节回放、结局回放与语音回听。 |
| 粒子与演出 | 可用 | 支持高级粒子预设、项目级自定义粒子、镜头、滤镜、闪屏、震动等演出配置。 |
| Live2D / 3D 资产 | Preview | 支持 Live2D、3D 角色模型和 3D 场景素材导入；原生 Runtime 会生成 3D 资产结构、材质贴图槽、动画通道和依赖清单，并可把风险定位回编辑器素材库。 |
| 网页 / 桌面导出 | Preview | 网页试玩包与三平台桌面包可用；签名、公证和安装器状态以 Release notes 为准。 |
| 原生 Runtime | Preview | 已覆盖核心播放链、存档、设置、历史文本、自动播放、视频兜底、3D 资产清单与第一批资料馆。 |
| 手机端 Runtime | 实验规划 | 当前处于触控、音频策略和界面适配验证阶段。 |

## 界面预览

| 剧情编辑与智能助手 | 试玩与导出 |
| --- | --- |
| ![Canvasia Engine story editor with assistant](docs/github/canvasia-screenshot-story-assistant.png) | ![Canvasia Engine preview and export screen](docs/github/canvasia-screenshot-preview-export.png) |
| 剧情页支持可视化卡片、场景结构、Canvasia Assistant、灵感盒和勾选式插入。 | 试玩页集中处理预览、设置、发布前问题提示和多平台导出入口。 |

## 仓库结构

- [`run_editor.py`](run_editor.py)  
  本地编辑器服务、导出链、项目管理、打包链的主入口

- [`prototype_editor`](prototype_editor)  
  编辑器前端

- [`prototype_editor/modules`](prototype_editor/modules)
  前端纯逻辑模块，覆盖素材目录、创作助手、项目医生、成品目标路线、发布总控、变量、外观主题、项目历史等可单独测试的能力

- [`export_player_template`](export_player_template)  
  导出后玩家端 Runtime 模板

- [`template_project`](template_project)  
  示例项目

- [`tests`](tests)  
  自动化测试

## 智能创作助手

剧情编辑页内置 `Canvasia Assistant`：

- 默认使用本地模板模式，不需要联网，不会上传项目内容，也不会产生 API 费用
- 创作者可自带 OpenAI、DeepSeek、通义千问、Kimi、智谱 GLM 或自定义兼容 API Key，并在面板里切换对应生成引擎，用于生成更自由的剧情片段、创作建议、场景润色和素材概念提示
- API Key 不会写入项目文件；只有勾选“只在本浏览器记住 Key”时，才会保存在当前浏览器的 localStorage，并可随时点击“忘记本机 Key”移除；助手结果进入界面和灵感盒前会按固定字段清洗，避免异常字段混入项目数据
- 真模型不可用或未填写 Key 时，会自动回落到本地模板助手，避免创作流程被卡住
- 生成结果会进入本地“灵感盒”，可搜索、收藏、恢复、删除、清理未收藏、复制历史剧情卡片、复制单条 Markdown 文档、导出 Markdown 创作档案、单条导出为 `.canvasia-idea.json`，也可以导出当前视图或导入全部 `.canvasia-idea-vault.json`；容量到上限时会优先保留收藏灵感，清理类操作会先提醒备份并要求确认，最近一次清理前的灵感盒可一键恢复，恢复前会把当前灵感盒转存成新的恢复点
- 插入前可以预览、勾选将要写入的剧情卡片，并复制成台本文本，方便创作者先审稿或发给协作者

## 快速开始

### 运行环境

- Python 3
- macOS / Windows / Linux

启动编辑器默认只需要 Python 3。

### 启动编辑器

最简单的方式是使用对应系统的启动脚本：

- macOS：双击 [`start_editor.command`](start_editor.command)
- Windows：双击 [`start_editor.cmd`](start_editor.cmd)
- Linux：运行 [`start_editor.sh`](start_editor.sh)

或者命令行启动。下面这些命令逻辑是通用的，主要差别只是不同系统里 Python 启动器名字不一样：

macOS / Linux：

```bash
git clone https://github.com/TonyNa-code/canvasia-engine.git
cd canvasia-engine
python3 run_editor.py
```

Windows：

```bat
git clone https://github.com/TonyNa-code/canvasia-engine.git
cd canvasia-engine
py -3 run_editor.py
```

如果 Windows 没有 `py` 启动器，也可以改用：

```bat
python run_editor.py
```

## 下载与导出

### 编辑器 App

编辑器预览包通过 GitHub Releases 分发。每个预览版会尽量提供下列三类附件，实际可下载文件以对应 Release 页面为准：

- `macos.tar.gz`
- `windows.zip`
- `linux.tar.gz`

预览包用于快速体验编辑器本体，不需要从源码启动。若某个平台包暂未出现在 Release 附件中，可先使用源码方式启动，或等待该平台附件补齐。

### 该下载哪个文件

| 目标 | 建议下载 | 说明 |
| --- | --- | --- |
| 只想体验编辑器 | 对应系统的编辑器预览包 | 如果 Release 里暂时没有你的系统包，可先用源码方式启动。 |
| 想从源码运行 / 二次开发 | `Source code` | 需要本机安装 Python 3。 |
| 想试玩导出的游戏 | 网页试玩包或原生 Runtime 包 | 网页包适合浏览器预览；原生 Runtime 包用于验证脱离 HTML 的桌面播放链。 |
| 想确认下载没损坏 | `.sha256` / `.checksum.json` / `verify_release_assets.*` | 有这些附件时，建议先校验压缩包再解压。 |

当前属于 Preview 分发阶段，未签名或未公证的包可能触发 macOS Gatekeeper、Windows SmartScreen 或杀毒软件提示。请只从本仓库 Release 页面下载，并优先校验 SHA-256。

发布预览版时，`prepare_preview_release.py` 会生成公开推荐附件的 `.sha256`、`.checksum.json` 和三系统校验脚本；加上 `--copy-public-assets` 后，还会把推荐附件、校验清单和校验脚本集中到一个可直接上传到 GitHub Release 的目录。如果 Release 页面附带这些文件，下载者可以先核对哈希再解压。

### 游戏成品导出

打开项目后，可在编辑器的 `预览导出` 页生成游戏成品包：

- 网页试玩包
- Windows 桌面包
- macOS 桌面包
- Linux 桌面包
- 原生 Runtime 包（Preview，含独立 App 打包脚手架）

### 平台状态

- `网页试玩包`：适合快速预览、网页分发和轻量测试。
- `Windows / macOS / Linux 桌面包`：当前主要基于 NW.js 桌面 Runtime。
- `原生 Runtime 包`：Preview 路线，已覆盖标题页主菜单、基础剧情主链、正式存档/读档、系统菜单设置项、文本历史、自动播放、已读快进、项目字体、玩家档案/自动续玩、基础粒子与镜头演出、3D 资产结构 / 依赖清单、可选 PyAV/FFmpeg 音画同步内嵌视频播放、OpenCV 画面兜底、系统播放器桥接兜底、第一批资料馆，以及随包生成的发布候选总报告与发布总控报告。
- `手机端 Runtime`：实验规划阶段，当前重点是触控、音频策略和界面适配验证。

### 原生 Runtime 发布体检

导出的原生 Runtime 包会随包生成：

- `native-runtime-release-check.json`：发布前自检，覆盖入口、缺失素材、格式风险、存档位、UI 引用等。
- `native-runtime-3d-asset-report.json`：3D 模型 / 3D 场景清单，统计 glTF/GLB/VRM 节点、网格、材质、贴图槽、动画通道、相机灯光、二进制容器、性能预算、内部索引、外部依赖和引用位置。
- `native-runtime-3d-asset-summary.md`：同一份 3D 清单的 Markdown 摘要，适合创作者直接打开阅读或贴到 Issue / Release notes。
- `native-runtime-3d-risk-digest.json`：面向编辑器和发布页的精简 3D 风险摘要，汇总性能预算、容器、内部引用、贴图槽和依赖风险，并保留素材 ID 供编辑器一键定位。
- `native-runtime-release-candidate-report.json`：发布候选总报告，汇总 doctor、打包脚手架、视频后端、3D 资产和下一步建议。
- `native-runtime-release-control-report.md`：面向人工验收的发布总控报告，汇总自检、RC、3D 风险、发布状态和下一步顺序。
- `native-runtime-release-control-report.json`：同一份总控结论的机器可读版本，适合接 CI、发布脚本或自动化验收。
- `生成原生Runtime发布总控报告.command` / `generate_native_runtime_release_control.sh` / `generate_native_runtime_release_control.bat`：三系统刷新脚本，可在不打开编辑器的情况下重新生成发布总控 Markdown / JSON。
- `native-runtime-file-integrity.md` / `native-runtime-file-integrity.json`：导出包核心文件 SHA-256 完整性清单，用于确认脚本、素材、manifest 和游戏数据没有丢失或被改坏。
- `校验原生Runtime文件完整性.command` / `verify_native_runtime_file_integrity.sh` / `verify_native_runtime_file_integrity.bat`：三系统完整性校验脚本。
- `*.zip.sha256` / `*.zip.checksum.json`：导出压缩包的 SHA-256 校验文件，适合上传 GitHub Release 时一起附带，方便下载后先验证压缩包本身。
- `*.zip.verify.command` / `*.zip.verify.sh` / `*.zip.verify.bat`：三系统压缩包一键校验脚本，下载者无需手动复制 SHA-256 命令。
- `*.zip.release-artifacts.md` / `*.zip.release-artifacts.json`：发布附件索引，列出建议上传到 GitHub Release 的附件、包内报告和下载者验证步骤。
- `*.zip.release-notes.md`：可直接复制到 GitHub Release 正文的发布说明草稿，包含主包下载、SHA-256、校验脚本和包内报告提示。

这些命令在 macOS / Linux / Windows 上逻辑相同，只是 Python 启动器可能不同。

macOS / Linux：

```bash
cd exported-native-runtime-folder
python3 runtime_player.py --describe-3d-assets .
python3 runtime_player.py --describe-3d-assets-markdown .
python3 runtime_player.py --doctor .
python3 runtime_player.py --release-candidate-report .
python3 runtime_player.py --write-release-control-reports .
python3 runtime_player.py --verify-file-integrity .
```

Windows：

```bat
cd exported-native-runtime-folder
py -3 runtime_player.py --describe-3d-assets .
py -3 runtime_player.py --describe-3d-assets-markdown .
py -3 runtime_player.py --doctor .
py -3 runtime_player.py --release-candidate-report .
py -3 runtime_player.py --write-release-control-reports .
py -3 runtime_player.py --verify-file-integrity .
```

## 测试

### 测试环境准备

浏览器自动化测试依赖 Playwright。第一次运行前建议先执行：

macOS / Linux：

```bash
cd canvasia-engine
python3 -m pip install -r requirements-dev.txt
python3 -m playwright install chromium
```

Windows：

```bat
cd canvasia-engine
py -3 -m pip install -r requirements-dev.txt
py -3 -m playwright install chromium
```

### 本地检查

推荐先跑本地 CI 预检。它会自动读取 `prototype_editor/index.html` 中加载的前端模块和 `tests/test_frontend*.py` 测试文件，避免 README、CI 和实际模块清单互相漂移。

macOS / Linux：

```bash
cd canvasia-engine
./verify_before_push.sh
```

Windows：

```bat
cd canvasia-engine
verify_before_push.cmd
```

也可以直接指定预检档位：

- `syntax`：只跑 Python / 前端脚本语法检查。
- `quick`：语法检查 + 发布工具 + 前端模块单元测试。
- `standard`：`quick` + 后端 smoke，适合日常提交前使用。
- `full`：`standard` + 原生 Runtime 渲染 smoke + Playwright 浏览器长流程，适合重要发布前使用。
- `browser`：只跑 Playwright 浏览器 smoke，适合排查 UI / 导出流程。

示例：

```bash
python3 tools/ci/local_verify.py --profile quick
python3 tools/ci/local_verify.py --profile full --json-report local-verify.json --markdown-report local-verify.md
python3 tools/ci/local_verify.py --profile full --no-fail-fast --markdown-report local-verify.md
python3 tools/ci/local_verify.py --profile full --no-fail-fast --report-dir verification_reports
python3 tools/ci/local_verify.py --profile full --strict-clean --report-dir verification_reports
python3 tools/ci/project_health.py template_project --markdown-report verification_reports/project-health-template.md
```

终端输出会显示检查档位、当前分支、提交号、本地改动数量、逐项通过/失败状态、分类汇总和下一步提示。
需要一次性看完整故障清单时，可以加 `--no-fail-fast`，报告会继续跑完后续检查并按类别汇总失败位置。
如果本机缺少某个必需工具，报告会归类到 `environment`，并列出受影响的检查项。
需要同时保存 JSON 和 Markdown 报告时，可以使用 `--report-dir verification_reports`；目录里会保留当前档位报告，也会生成 `local-verify-latest.md` 作为最新报告入口。
报告会记录当前分支、短提交号和未提交改动数量，方便确认验证对应的是哪一版代码。
正式发布前可以加 `--strict-clean`，让本地未提交改动也作为发布闸门失败项显示在报告里。
需要检查某个游戏项目是否缺素材、坏跳转或引用不存在，可以运行 `tools/ci/project_health.py <项目目录>`；它会在终端里显示项目健康状态、首批问题、安全修复分组和下一步建议。
编辑器的项目巡检页可以先点“先预览安全修复”，确认项目医生会改哪些低风险结构问题，再执行一键修复。如果报告里出现 `Optional safe repair preview command`，也可以先复制预览命令确认；确认无误后再运行 `Optional safe repair command`。它只处理入口场景、章节顺序和场景顺序这类可安全重建的项目索引，不会删除剧情卡片或素材文件。手动指定 `--repair-codes` 时工具会拒绝未知修复码，避免拼错后误以为已经完成修复。

### GitHub 检查状态

如果 GitHub 页面上出现红叉、黄点或绿色勾，可以直接运行状态检查脚本。它会读取当前仓库远程地址、当前提交和本地 Git 状态，同时显示 GitHub Actions 是否通过、本地是否有未提交改动、是否有提交还没推送、是否落后远端。

macOS / Linux：

```bash
cd canvasia-engine
./check_github_ci_status.sh
```

Windows：

```bat
cd canvasia-engine
check_github_ci_status.cmd
```

如果刚刚推送，想等待 GitHub Actions 跑完：

```bash
./check_github_ci_status.sh --watch
```

如果想先刷新远端分支缓存，再判断本地是否还有没推送或落后远端：

```bash
./check_github_ci_status.sh --fetch
```

发布预检会区分“当前 commit 的 GitHub Actions 还没开始跑”和“已经跑完但失败”。如果报告提示当前 commit 暂无 CI 结果，先推送该 commit，再等待 Actions 完成，不要只看上一条分支运行记录就直接发布。

### 自动化测试

如果只想单独跑某一类测试，也可以继续使用下面这些命令。

后端 smoke：

macOS / Linux：

```bash
cd canvasia-engine
python3 -m unittest discover -s tests -p 'test_run_editor_smoke.py' -v
```

Windows：

```bat
cd canvasia-engine
py -3 -m unittest discover -s tests -p "test_run_editor_smoke.py" -v
```

浏览器 Playwright：

macOS / Linux：

```bash
cd canvasia-engine
python3 -m unittest discover -s tests -p 'test_browser_playwright_smoke.py' -v
```

Windows：

```bat
cd canvasia-engine
py -3 -m unittest discover -s tests -p "test_browser_playwright_smoke.py" -v
```

发布工具与前端模块：

macOS / Linux：

```bash
cd canvasia-engine
python3 -m unittest discover -s tests -p 'test_prepare_preview_release.py' -v
python3 -m unittest discover -s tests -p 'test_frontend*.py' -v
```

Windows：

```bat
cd canvasia-engine
py -3 -m unittest discover -s tests -p "test_prepare_preview_release.py" -v
py -3 -m unittest discover -s tests -p "test_frontend*.py" -v
```

原生 Runtime 渲染 smoke（会在仓库内创建隔离虚拟环境并安装 `pygame-ce`）：

macOS / Linux：

```bash
cd canvasia-engine
./run_native_runtime_smoke.sh
```

Windows：

```bat
cd canvasia-engine
run_native_runtime_smoke.cmd
```

或者直接运行对应系统脚本：

- macOS：[`verify_before_push.command`](verify_before_push.command) / [`check_github_ci_status.command`](check_github_ci_status.command) / [`run_tests.command`](run_tests.command) / [`run_browser_tests.command`](run_browser_tests.command) / [`run_native_runtime_smoke.command`](run_native_runtime_smoke.command)
- Windows：[`verify_before_push.cmd`](verify_before_push.cmd) / [`check_github_ci_status.cmd`](check_github_ci_status.cmd) / [`run_tests.cmd`](run_tests.cmd) / [`run_browser_tests.cmd`](run_browser_tests.cmd) / [`run_native_runtime_smoke.cmd`](run_native_runtime_smoke.cmd)
- Linux：[`verify_before_push.sh`](verify_before_push.sh) / [`check_github_ci_status.sh`](check_github_ci_status.sh) / [`run_tests.sh`](run_tests.sh) / [`run_browser_tests.sh`](run_browser_tests.sh) / [`run_native_runtime_smoke.sh`](run_native_runtime_smoke.sh)

### GitHub Actions

仓库已内置 CI，会在 `push / pull request` 时自动执行：

- Python 语法检查
- 前端脚本语法检查
- 发布工具、前端模块、按钮动作覆盖、未接线按钮兜底与统一弹窗回归测试
- 本地 CI 预检工具覆盖自检
- GitHub Actions 状态检查工具自检
- 后端 smoke 测试
- 原生 Runtime 渲染 smoke 测试
- Playwright 浏览器烟测

## 发布状态

当前仓库以 **源码可见创作者预览版** 方式维护。

- 源码可直接在本地启动与修改
- 自动化测试已经接通
- GitHub Releases 可用于提供编辑器可运行包
- 导出链和桌面打包链已经具备原型级完整度

## 其他设计文档

更早期的引擎规划和数据设计可参考：

- [`galgame_engine_blueprint.md`](galgame_engine_blueprint.md)
- [`v1_ui_structure.md`](v1_ui_structure.md)
- [`v1_data_format.md`](v1_data_format.md)

## 许可说明

当前仓库采用 **Canvasia Engine Creator License 1.0**：

- [`LICENSE`](LICENSE)

这份许可的核心口径是：

- 允许使用本引擎制作并商业发布游戏
- 允许为了自己的项目修改引擎
- 不允许把引擎本体或修改版引擎当作引擎产品再次商业化出售

因此它不是标准 OSI 意义上的开源协议，而是更接近“源码可见 / source-available”的创作者许可。

## 贡献

欢迎提 Issue、提想法、做测试反馈。

贡献前建议先看：

- [`CONTRIBUTING.md`](CONTRIBUTING.md)
- [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md)
- [`SECURITY.md`](SECURITY.md)

Issue / PR 入口：

- [Bug report](.github/ISSUE_TEMPLATE/bug_report.md)
- [Beginner help / usage question](.github/ISSUE_TEMPLATE/usage_help.md)
- [Feature request](.github/ISSUE_TEMPLATE/feature_request.md)
- [Release / package problem](.github/ISSUE_TEMPLATE/release_package_problem.md)
- [Pull request template](.github/pull_request_template.md)
