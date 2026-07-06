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
  <strong>语言</strong>：
  简体中文 ·
  <a href="README.md">English</a> ·
  <a href="README.ja-JP.md">日本語</a>
</p>

<p align="center">
  <a href="docs/creator_quick_start_zh-CN.md">创作者零代码教程</a> ·
  <a href="#快速开始">快速开始</a> ·
  <a href="#当前已经有的核心能力">核心能力</a> ·
  <a href="#功能状态">功能状态</a> ·
  <a href="#界面预览">界面预览</a> ·
  <a href="#项目主页与传播素材">传播素材</a> ·
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
- 上下文感知指挥面板：可用 Cmd/Ctrl+K 快速搜索项目开工、页面跳转、推荐下一步、最近常用命令、剧情插卡、场景模板、主题切换、新手教程与导出入口
- 商业段落配方：可一键插入 OP 前导、日常对话节奏、好感度选项、悬念线索、关系揭露、分支汇合、高潮演出段、ED / 片尾、BGM 范围调度和带变量后果的分支骨架
- 场景演出配方：可一键把镜头、滤镜、景深、粒子、停顿、闪屏、震动、BGM 和黑场淡入淡出插成可继续编辑的卡片，用于告白特写、悬疑压迫、雨夜回忆、爆点冲击和收束留白等常见 VN 氛围
- 手写剧本转剧情卡片：可把文档 / 备忘录里的 `角色：台词`、`角色 "台词"`、旁白、连续选项、`- 选项 -> 场景 [好感 +1; 已见面=true]` 变量后果、`设置 好感 为 2` / `add affection +1` 独立变量卡、`if 好感 >= 2 -> 好结局 else -> 普通结局` 条件分支，以及 `scene / show / hide / show ... scale / x / y / opacity / layer / flip / speed slow / normal / fast / instant / play music / stop music / play sound / play video / wait / pause / 等待 / 停顿 / shake / flash / zoom / pan / filter / blur / particle / credits / voice / jump` 等轻量演出、文字速度、音频、视频、节奏停顿、镜头、角色舞台、氛围和路线指令预览后插入当前场景
- 角色、素材、台词台本、配音工作流
- 项目默认语言 / 可切换语言配置，网页 Runtime 与原生 Runtime 可按中日英等语言读取翻译文本并自动回退
- 首页今日工作台、最终发表门禁、项目巡检、跨模块生产待办队列 / CSV、Runtime 覆盖矩阵 / CSV、Runtime 导出验收清单、VN 基础能力成熟度体检、项目医生小白修复向导、项目医生回执导出 / 复制 / 编号、成品目标路线、一键安全修复低风险结构问题、一键发布前修复顺序（会把首屏加载风险、VN 基础缺口和具体路线试玩阻塞项纳入排序）、一键发布前整理（会先创建安全检查点，再安全处理长文本、基础演出、BGM 范围 / 淡入淡出、存档位、文本框可读性、UI 皮肤和字体绑定，并生成回执）、视觉小说基础质感体检、带节奏体检和一键配方建议的场景生产看板 / CSV、语音制作清单 / CSV、选项后果表 / CSV、变量影响表 / CSV、发布前路线试玩工作簿 / CSV、会从标准路线计划提取具体分支 / 结局阻塞项的生产待办、素材依赖表 / CSV、素材体积雷达 / CSV、Runtime 首屏加载预算 / CSV、可解锁内容清单 / CSV、BGM 调度表 / CSV、角色舞台调度表 / CSV、演出时间轴 / CSV、多语言覆盖报告 / CSV、翻译 CSV 安全导入、素材性能预算、会把首屏加载问题纳入队列的生产待办、发布总控 Markdown / JSON 报告、测试员试玩工单 / CSV、测试反馈模板 / CSV、反馈导入摘要、发布验收清单、带条件 / 否则分支变量预设的分支感知自动回归试玩路线测试
- Canvasia Assistant 智能创作助手：支持零配置本地模板，也支持创作者自带 OpenAI、DeepSeek、通义千问、Kimi、智谱 GLM 或自定义兼容 API Key 调用真模型生成剧情、建议、素材提示、灵感盒归档包和可插入剧情卡片
- 素材页可选 OpenAI Image 生图：输入提示词即可生成背景、立绘、CG 或 UI 素材，可点选画风预设统一风格；生成立绘时可直接绑定到角色表情和默认立绘，并自动导入项目素材库；API Key 只用于本次请求，不写入项目文件，并会校验提示词长度、模型名、透明背景 / JPEG 组合和返回图片格式
- 正式存档 / 读档、系统菜单
- 入口可达性路线分析：可检查坏链、孤立场景、入口实际走不到的场景、分支深度、结局候选、可打到结局路径预览，并可导出路线试玩手册 / CSV；巡检页会生成发布前路线试玩工作簿，把断点修复、分支逐条覆盖、结局完整跑通和自动回归优先种子拆成可执行步骤
- 场景节奏体检：可检查可试玩节奏、长文本、演出过平、假选项、缺少收尾提示，并在场景生产看板里给出下一步建议
- Ren'Py 草稿导出：可把场景、对白、旁白、逐句文字速度、选项、变量、条件分支、语音、带裁段 / 音量 / 时长的 video 过场、背景转场时长、立绘 / BGM 音量与循环提示、指定范围 BGM 停止 / 淡出、音效音量、自定义立绘位置 / 缩放 / 透明度 / 镜像 / 层级、带时长的滑入 / 升起 / 退场立绘转场、等待、闪屏 / 淡入淡出颜色与时长、基础镜头推近 / 平移 / 滤镜 / 景深模糊、基于 SnowBlossom 的氛围粒子、片尾字幕和跳转转换成 `.rpy` 草稿，并额外导出迁移备注标出需要人工复核的复杂时序和自定义演出
- 项目级成品 UI 皮肤、UI Kit 部件绑定、九宫格贴图、按钮多状态贴图、布局位置微调与视觉小说文本框设计
- EXTRA 回想馆、图鉴馆、成就馆、章节回放、结局回放、语音回听，并可导出可解锁内容清单 / CSV 检查 CG、BGM、语音回听、角色图鉴、地点图鉴、章节、结局和成就是否齐全
- 高级粒子系统、项目级粒子预设库
- Live2D / 3D 角色模型与 3D 场景资产导入，原生 Runtime 可输出 glTF 结构、材质贴图槽、动画通道、依赖、引用位置和转换建议清单
- 网页试玩包、Windows 桌面包、原生 Runtime 包、编辑器桌面包、三系统编辑器套装，并为试玩 Runtime 生成资源预热清单；编辑器内也可提前检查首屏 / 早期路线素材压力、缺文件和场景加载热点
- 自动化测试体系（本地 CI 预检 + 按钮动作覆盖扫描 + 未接线按钮运行时兜底 + Ren'Py 草稿导出测试 + 后端 smoke + Playwright 浏览器烟测）

## 功能状态

| 模块 | 当前状态 | 说明 |
| --- | --- | --- |
| 剧情 / 分支编辑 | 可用 | 支持可视化卡片、选项跳转、条件与变量、入口可达性路线检查、发布前路线试玩工作簿、带节奏体检配方建议的场景生产看板、完整剧本台本、Ren'Py 草稿导出、语音制作清单、变量影响表、场景树筛选、手写剧本文本识别插入，并可通过命令面板一键套用“第一段可试玩”剧情骨架。 |
| 素材管理 | 可用 | 支持背景、角色、CG、BGM、音效、语音、字体等素材导入、替换、删除、使用保护、素材依赖表、素材体积雷达与发布前体积预算提示；可选使用 OpenAI Image 直接生成背景、立绘、CG 和 UI 素材并入库，立绘可直接绑定角色表情，并带画风预设、提示词、模型名、格式组合和返回文件校验。 |
| 多语言 / 国际化 | Preview | 支持项目默认语言与可切换语言配置；可在项目巡检中导出缺翻译 / 疑似占位翻译覆盖报告，并安全导入角色、章节、场景与剧情卡片翻译 CSV；导出数据会保留场景、章节、台词、选项和角色名翻译，网页 Runtime 与原生 Runtime 可切换语言并在缺失翻译时自动回退。 |
| 智能创作助手 | 可用 | 默认本地模板；可选自带 OpenAI、DeepSeek、通义千问、Kimi、智谱 GLM 或自定义兼容 API Key 的真模型模式；支持灵感盒搜索、收藏保留、卡片预览、勾选插入、单条 / 全量 Markdown 创作档案、单条导出、全部归档、导入与本机 Key 遗忘。 |
| 项目安全网 | 可用 | 支持自动快照、版本恢复、崩溃恢复、正式存档 / 读档、首页今日工作台、最终发表门禁、跨模块生产待办队列、项目医生修复队列、项目医生可追溯回执、成品目标路线、入口场景 / 章节顺序 / 场景顺序的一键安全修复、一键发布前整理回执、发布前检查、视觉小说基础质感体检、VN 基础能力成熟度体检、可解锁内容就绪度与发布总控 Markdown / JSON 报告导出。 |
| 成品 UI 自定义 | 可用 | 支持项目级 UI 皮肤、按钮多状态、九宫格贴图、布局位置与视觉小说文本框设计。 |
| EXTRA / 回想系统 | 可用 | 支持图鉴馆、回想馆、成就馆、章节回放、结局回放与语音回听；可解锁内容清单会检查缺失图库文件、语音回听缺口、角色图鉴视觉素材和不可达结局。 |
| 粒子与演出 | 可用 | 支持高级粒子预设、项目级自定义粒子、场景演出配方、镜头、滤镜、闪屏、震动等演出配置。 |
| Live2D / 3D 资产 | Preview | 支持 Live2D、3D 角色模型和 3D 场景素材导入；原生 Runtime 会生成 3D 资产结构、材质贴图槽、动画通道和依赖清单，并可把风险定位回编辑器素材库。 |
| 网页 / 桌面导出 | Preview | 网页试玩包与三平台桌面包可用；签名、公证和安装器状态以 Release notes 为准。 |
| 原生 Runtime | Preview | 已覆盖核心播放链、存档、设置、历史文本、自动播放、视频兜底、3D 资产清单与第一批资料馆；编辑器巡检会生成 Web / 原生 Runtime 覆盖矩阵、导出验收清单和 VN 基础能力成熟度摘要，帮助确认当前项目使用的卡片是否都能在导出包中播放、BGM 范围 / 淡入淡出、文本框可读性、存档位、UI 皮肤和字体绑定等基础项是否需要发布前补齐。 |
| 手机端 Runtime | 实验规划 | 当前处于触控、音频策略和界面适配验证阶段。 |

## 界面预览

| 剧情编辑与智能助手 | 试玩与导出 |
| --- | --- |
| ![Canvasia Engine story editor with assistant](docs/github/canvasia-screenshot-story-assistant.png) | ![Canvasia Engine preview and export screen](docs/github/canvasia-screenshot-preview-export.png) |
| 剧情页支持可视化卡片、场景结构、Canvasia Assistant、灵感盒和勾选式插入。 | 试玩页集中处理预览、设置、发布前问题提示和多平台导出入口。 |

## 项目主页与传播素材

- 项目主页源码：[`docs/index.html`](docs/index.html)
- GitHub 社交预览图：[`docs/github/canvasia-social-preview.png`](docs/github/canvasia-social-preview.png)
- 对外介绍与发布文案：[`docs/marketing/exposure-kit.md`](docs/marketing/exposure-kit.md)
- 如果在 GitHub Pages 中把发布目录设为 `/docs`，预期主页地址是：`https://tonyna-code.github.io/canvasia-engine/`

## 仓库结构

- [`run_editor.py`](run_editor.py)
  本地编辑器服务、导出链、项目管理、打包链的主入口

- [`editor_static_cache.py`](editor_static_cache.py)
  本地编辑器静态文件 ETag / 304 复用辅助模块，用于减少刷新时重复传输前端模块和素材预览文件

- [`export_package_guide.py`](export_package_guide.py)
  导出包侧试玩 / 发布验收说明生成器

- [`export_localization_audit.py`](export_localization_audit.py)
  导出包侧本地化覆盖审计生成器，用于检查多语言项目漏译位置

- [`export_quality_reports.py`](export_quality_reports.py)
  导出包侧质量报告组合入口，统一生成剧情路线图、本地化审计和发布就绪摘要

- [`export_asset_rights.py`](export_asset_rights.py)
  导出包侧素材授权、署名、AI 来源和 Staff 草稿报告生成器

- [`export_audio_cue_sheet.py`](export_audio_cue_sheet.py)
  导出包侧 BGM / 音效 / 语音调度表和试听复查报告生成器

- [`export_stage_direction_sheet.py`](export_stage_direction_sheet.py)
  导出包侧角色舞台调度、立绘演出、站位、缩放、透明度和图层复查报告生成器

- [`export_presentation_timeline.py`](export_presentation_timeline.py)
  导出包侧演出时间轴、阅读时长、节奏锚点和硬切问题复查报告生成器

- [`export_voice_production.py`](export_voice_production.py)
  导出包侧配音录制表、角色进度和补录问题报告生成器

- [`export_release_readiness.py`](export_release_readiness.py)
  导出包侧发布试玩就绪摘要和测试员交付门禁生成器

- [`export_story_route_map.py`](export_story_route_map.py)
  导出包侧剧情路线图、坏跳转和入口不可达场景报告生成器

- [`export_unlockable_manifest.py`](export_unlockable_manifest.py)
  导出包侧可解锁内容、图鉴、回想、结局和成就覆盖清单生成器

- [`export_runtime_preload.py`](export_runtime_preload.py)
  导出包侧 Runtime 资源预热清单和性能报告生成器

- [`renpy_export.py`](renpy_export.py)
  Ren'Py Starter Bundle 与 `.rpy` 迁移导出生成器

- [`prototype_editor`](prototype_editor)
  编辑器前端

- [`prototype_editor/modules`](prototype_editor/modules)
  前端纯逻辑模块，覆盖素材目录、创作助手、路线分析、项目医生、成品目标路线、发布总控、变量、外观主题、项目历史等可单独测试的能力

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

## AI 素材生成

素材页内置可选的 OpenAI Image 生图入口：

- 支持生成 `背景`、`立绘`、`CG` 和 `界面素材`
- 可设置素材名、提示词、画风补充、画风预设、模型、尺寸、质量、背景和输出格式
- 生成 `立绘` 时，可以选择已有角色和表情，生成后直接设为该角色的表情立绘或默认立绘
- 生成成功后会自动写入当前项目素材库，不需要再手动下载再导入
- API Key 只随本次生成请求发送，不会写入项目文件或素材元数据
- 会提前拦截超长提示词、超长画风补充、非法模型名、透明背景 + JPEG 这类不兼容组合，并校验返回图片确实是目标格式
- 没有 OpenAI API Key 时，仍可继续使用普通上传素材和本地模板助手

## 快速开始

第一次使用建议先看这份面向创作者的零代码教程：[`Canvasia Engine 创作者零代码使用教程`](docs/creator_quick_start_zh-CN.md)。它会从下载、启动、新建项目、导入素材、写第一段剧情、试玩到导出，按普通用户视角走一遍。

如果只想先做出一个小 Demo，建议在项目中心直接新建“可试玩 Demo”。它会创建项目、第一章、基础占位素材和可预览入口；之后再把占位素材和台词替换成正式内容即可。想完全从零开始时，也可以新建空白项目，再用故事页的新手上手顺序、故事页模板区或 Cmd/Ctrl+K 搜索“第一段可试玩”，先预览将插入的卡片，再套用一段包含背景、BGM、角色登场、对白、选择项和淡出收束的剧情骨架。已经在文档或备忘录里写好的台本，也可以在故事页粘贴到“手写剧本转剧情卡片”面板，预览识别结果后一次插入当前场景。

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

- `网页试玩包`：适合快速预览、网页分发和轻量测试；导出包会附带 `runtime_preload_manifest.json` 与 `RUNTIME_PRELOAD_REPORT.md`，Runtime 会优先预热首屏和早期路线素材，减少第一次切背景、立绘、BGM 时的卡顿。编辑器“项目巡检”页也可在导出前生成 Runtime 首屏加载预算报告，提前发现入口场景大素材、缺文件和场景热点。
- `Ren'Py Starter Bundle`：会导出 zip，内含 `game/script.rpy`、`game/options.rpy`、复制后的 `game/assets/` 素材、迁移 manifest、自定义演出复核备注、包内自检报告和本地校验脚本，适合把项目迁移到 Ren'Py 后继续开发。
- `Windows / macOS / Linux 桌面包`：当前主要基于 NW.js 桌面 Runtime。
- `原生 Runtime 包`：Preview 路线，已覆盖标题页主菜单、基础剧情主链、正式存档/读档、系统菜单设置项、语言切换、文本历史、自动播放、已读快进、项目字体、资源预热清单读取、玩家档案/自动续玩、基础粒子与镜头演出、3D 资产结构 / 依赖清单、可选 PyAV/FFmpeg 音画同步内嵌视频播放、OpenCV 画面兜底、系统播放器桥接兜底、第一批资料馆，以及随包生成的发布候选总报告、发布总控报告与三系统验收清单；启动时会优先缓存关键图片和短音频，后续素材则以小步后台队列继续预热，并确认 BGM / 视频这类流媒体路径是否就绪。
- `手机端 Runtime`：实验规划阶段，当前重点是触控、音频策略和界面适配验证。

所有可试玩 / 可运行导出包都会随包生成 `README_试玩验收先看这里.md`、`story_route_map.json`、`story_route_map.md`、`localization_audit.json`、`localization_audit.md`、`release_readiness_summary.json`、`release_readiness_summary.md`、`unlockable_content_manifest.json`、`unlockable_content_report.md`、`asset-rights-manifest.json`、`asset-rights-report.md`、`asset-rights-table.csv`、`audio-cue-sheet.json`、`audio-cue-report.md`、`audio-cue-table.csv`、`stage-direction-sheet.json`、`stage-direction-report.md`、`stage-direction-table.csv`、`presentation-timeline.json`、`presentation-timeline-report.md`、`presentation-timeline-table.csv`、`voice-production-sheet.json`、`voice-production-report.md` 和 `voice-production-lines.csv`。README 负责告诉测试员怎么打开、先验哪些基础功能；剧情路线图负责检查坏跳转、入口不可达场景和结局候选；本地化审计负责检查多语言项目的漏译位置；发布就绪摘要负责快速判断这包能不能交给别人试玩；可解锁内容 JSON / Markdown 报告适合直接查看 CG 图鉴、音乐回想、语音回听、角色 / 地点 / 旁白 / 关系图鉴、章节回放、结局收集和成就覆盖情况；素材授权报告会检查商用状态、来源、署名、占位素材和 AI 生成记录；音频调度表会检查 BGM 文本范围、淡入淡出、停止点、缺文件音效和语音 Cue；角色舞台调度表会检查背景、立绘、表情、站位、缩放、透明度、图层和登退场转场；演出时间轴会检查预计阅读 / 演出时长、长静态对白、视觉 / 音频锚点、硬切音乐、空选项和不可用媒体；语音制作清单会给出配音录制表、建议文件名、角色进度、缺绑定语音和长句复查项。

### 原生 Runtime 发布体检

导出的原生 Runtime 包会随包生成：

- `native-runtime-release-check.json`：发布前自检，覆盖入口、缺失素材、格式风险、存档位、UI 引用等。
- `native-runtime-3d-asset-report.json`：3D 模型 / 3D 场景清单，统计 glTF/GLB/VRM 节点、网格、材质、贴图槽、动画通道、相机灯光、二进制容器、性能预算、内部索引、外部依赖和引用位置。
- `native-runtime-3d-asset-summary.md`：同一份 3D 清单的 Markdown 摘要，适合创作者直接打开阅读或贴到 Issue / Release notes。
- `native-runtime-3d-risk-digest.json`：面向编辑器和发布页的精简 3D 风险摘要，汇总性能预算、容器、内部引用、贴图槽和依赖风险，并保留素材 ID 供编辑器一键定位。
- `native-runtime-release-candidate-report.json`：发布候选总报告，汇总 doctor、打包脚手架、视频后端、3D 资产和下一步建议。
- `native-runtime-release-control-report.md`：面向人工验收的发布总控报告，汇总自检、RC、3D 风险、发布状态和下一步顺序。
- `native-runtime-release-control-report.json`：同一份总控结论的机器可读版本，适合接 CI、发布脚本或自动化验收。
- `native-runtime-vn-baseline-quality.md` / `native-runtime-vn-baseline-quality.json`：视觉小说基础质感体检，检查立绘兜底、背景覆盖、BGM 进入点、选项、空文本、占位素材和轻量演出润色。
- `生成原生Runtime发布总控报告.command` / `generate_native_runtime_release_control.sh` / `generate_native_runtime_release_control.bat`：三系统刷新脚本，可在不打开编辑器的情况下重新生成发布总控 Markdown / JSON。
- `native-runtime-release-acceptance.md` / `native-runtime-release-acceptance.json`：发布前验收清单，汇总自动检查、三系统人工点测项、启动/读档/音画/资料馆/分发确认项。
- `生成原生Runtime发布验收清单.command` / `generate_native_runtime_acceptance_checklist.sh` / `generate_native_runtime_acceptance_checklist.bat`：三系统验收清单刷新脚本。
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
python3 runtime_player.py --vn-baseline-quality-report .
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
py -3 runtime_player.py --vn-baseline-quality-report .
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
