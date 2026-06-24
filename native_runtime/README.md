# 原生 Runtime 包

这是 Canvasia Engine 在“先原生化 Runtime，编辑器先保留网页技术”路线上的第一阶段预览。

当前目标不是一次性替换现有网页播放器，而是先把最核心的剧情播放主链迁到真正不依赖 HTML 的桌面运行时里。

## 当前已覆盖

- 背景切换
- 角色显示 / 隐藏
- 台词 / 旁白
- 选项
- 跳转 / 条件分支
- 基础变量修改
- BGM / SFX / 语音播放
- 第一版正式存档 / 快速存档
- 可视化存档 / 读档面板
- 基础系统菜单
- 主题 / 显示模式 / 文字速度 / 四路音量设置
- 玩家档案 / 自动续玩记录
- 原生标题页 / 主菜单入口
- 多馆标签页资料馆
- 章节回放 / 音乐鉴赏 / CG 回想
- 地点图鉴 / 角色图鉴 / 结局回放 / 成就馆
- CG / 地点 / 角色 / 旁白 / 关系 / 成就详情查看页
- 项目级正式存档位数量
- 项目级文本框样式基础同步
- 项目级成品 UI 皮肤颜色 / 标题资源同步
- 项目级 UI 九宫格绘制、存档卡片皮肤与按钮多状态贴图
- 项目级字体族 / 字体素材同步
- 文本历史、自动播放、已读快进
- 基础粒子特效表现
- 基础镜头 / 闪屏 / 淡入淡出 / 滤镜 / 景深演出
- Live2D / 3D 角色模型元数据预览桥
- 3D 场景交互预览桥
- 3D 模型 / 3D 场景资产结构、材质贴图槽、动画通道与依赖清单
- 视频卡片的影院式原生预览卡 / 可选 PyAV 音画同步内嵌播放 / OpenCV 画面兜底 / 系统播放器桥接兜底
- PyInstaller 独立 App 打包脚手架

## Preview 路线图

原生 Runtime 已经可以承担第一版桌面预览和小型项目试玩导出；后续增强会按“先稳定主链，再补高级演出”的顺序推进：

| 模块 | 当前状态 | 后续增强方向 |
| --- | --- | --- |
| 剧情主链 | 已支持背景、角色、台词、选项、跳转、条件与变量 | 持续对齐网页 Runtime 的高级演出边角场景 |
| 存档与系统菜单 | 已支持正式存档、快速存档、主题、显示模式、文字速度、文字大小、文本框透明度、四路音量和操作帮助 | 增加更细的按键映射、辅助功能和项目级菜单扩展 |
| 阅读体验 | 已支持项目字体族、项目字体素材、文本历史、语音回听、自动播放语音等待、持久化已读快进、清屏隐藏和截图 | 后续补更多可访问性选项、手柄/触控映射和阅读偏好预设 |
| 项目 UI 皮肤 | 已在 Pygame 中绘制基础颜色、标题资源、面板九宫格、存档卡片和按钮多状态贴图 | 后续补 UI Kit 部件库、皮肤包导入导出和更多控件级绑定 |
| 资料馆 / 回想馆 | 已支持章节、音乐、CG、地点、角色、结局、成就及详情页 | 增加高级筛选、排序、专属转场和更多馆内互动 |
| 粒子与镜头 | 已支持基础粒子、镜头、闪屏、淡入淡出、滤镜和景深 | 补齐组合层、更多物理参数和复杂粒子表现 |
| 3D 模型 / 场景 | 已支持 3D 角色模型元数据桥、3D 场景交互预览桥、glTF 结构统计、材质贴图槽探针、动画通道探针、依赖检查和引用位置清单 | 后续接真实 3D 渲染后端、材质预览视窗、动画选择器和场景碰撞 / 镜头轨道 |
| 视频卡片 | 已支持影院式原生预览卡、可选 PyAV/FFmpeg 音画同步内嵌播放、OpenCV 画面兜底、剪辑区间停止和系统播放器桥接兜底 | 继续补时间轴裁切 UI、更多编码实机矩阵和平台原生播放器方案 |

## 启动要求

- Python 3.10+
- `pygame-ce`

安装命令：

```bash
python3 -m pip install -r requirements.txt
```

如果是在编辑器导出的原生 Runtime 包里运行，依赖文件会被改名为：

```bash
python3 -m pip install -r requirements-native-runtime.txt
```

## 快速验证

```bash
python3 runtime_player.py --validate-bundle .
```

## 维护者渲染 smoke

如果是在源码仓库里验证原生 Runtime 的真实 Pygame 绘制链，可以回到仓库根目录运行：

```bash
./run_native_runtime_smoke.sh
```

这条命令会创建 `.native_runtime_smoke_venv` 隔离环境、安装 `pygame-ce`，并使用 dummy 音频/视频驱动运行 `tests/test_native_runtime_render_smoke.py`。macOS 也可以双击 `run_native_runtime_smoke.command`，Windows 可运行 `run_native_runtime_smoke.cmd`。

## 一键发布体检

不启动窗口，集中运行导出包结构、发布前自检、标题页、正式存档面板、存档/设置/资料馆/玩家档案、粒子、演出、视频桥接和视频内嵌画面探针：

```bash
python3 runtime_player.py --doctor .
```

这条命令会输出 JSON 总报告。涉及存档和设置写入的检查会使用临时用户目录，不会覆盖玩家或创作者机器上的真实存档。

## 发布候选总报告

不启动窗口，在 `--doctor` 的基础上输出更接近发版决策的 Release Candidate 报告。报告会汇总阻塞项、警告项、三系统打包矩阵、视频后端策略、商业发布缺口和下一步建议：

```bash
python3 runtime_player.py --release-candidate-report .
```

导出包也会自动附带一份 `native-runtime-release-candidate-report.json`。如果想重新生成报告，可以直接运行随包脚本：

- macOS：双击 `检查原生Runtime发布候选.command`
- Linux：运行 `./check_native_runtime_release_candidate.sh`
- Windows：双击 `check_native_runtime_release_candidate.bat`

如果只想输入短命令，也可以使用：

```bash
python3 runtime_player.py --rc-report .
```

报告中的 `status` 含义：

- `preview_ready`：可进入桌面 Preview RC 的三系统实机打包阶段。
- `preview_ready_with_warnings`：主链可进入 Preview RC，但仍有发布警告需要在 Release notes 或实机点测中处理。
- `preview_ready_with_optional_failures`：Preview 主链不阻塞，但存在非核心能力失败。
- `blocked`：存在 Preview 阻塞项，应先修复再打包。

## 发布总控报告

编辑器导出的完整原生 Runtime 包会额外附带：

- `native-runtime-release-control-report.md`：给人工验收看的总控报告，汇总发布自检、RC 状态、3D 风险摘要、发布门禁和下一步处理顺序。
- `native-runtime-release-control-report.json`：给自动化脚本或 CI 读取的同一份结论，字段包含 `qualityGate`、`releaseCheck`、`releaseCandidate`、`asset3d`、`vnBaselineQuality` 和 `nextSteps`。
- `native-runtime-vn-baseline-quality.md` / `native-runtime-vn-baseline-quality.json`：检查视觉小说基础体验是否像完整作品，覆盖立绘兜底、背景覆盖、BGM 进入点、选项、空文本、占位素材和轻量演出润色。

这两份文件会在导出包生成时自动写入。若需要重新计算底层检查，可以先运行 `--release-check`、`--doctor`、`--release-candidate-report` 和 `--describe-3d-assets`，再重新从编辑器导出一版包。

也可以直接在导出的原生 Runtime 包里刷新总控报告：

```bash
python3 runtime_player.py --write-release-control-reports .
```

或分别输出到终端：

```bash
python3 runtime_player.py --release-control-json .
python3 runtime_player.py --release-control-report .
python3 runtime_player.py --vn-baseline-quality-report .
```

随包脚本会自动调用同一条刷新命令：

- macOS：双击 `生成原生Runtime发布总控报告.command`
- Linux：运行 `./generate_native_runtime_release_control.sh`
- Windows：双击 `generate_native_runtime_release_control.bat`

## 发布验收清单

编辑器导出的完整原生 Runtime 包会额外附带：

- `native-runtime-release-acceptance.md`：面向发布前人工点测的清单，包含自动检查结果、macOS / Windows / Linux 三系统验收项，以及启动、读档、音画、回想馆、成品分发等逐项确认框。
- `native-runtime-release-acceptance.json`：同一份清单的机器可读版本，可供 CI、发布脚本或外部工具读取。

这份清单会在导出包生成时自动写入。建议在正式分享或发布前打开 Markdown 版本，按目标系统完成最后一轮人工点测。

重新生成验收清单：

```bash
python3 runtime_player.py --write-acceptance-reports .
```

或分别输出到终端：

```bash
python3 runtime_player.py --acceptance-check .
python3 runtime_player.py --acceptance-report .
```

随包脚本：

- macOS：双击 `生成原生Runtime发布验收清单.command`
- Linux：运行 `./generate_native_runtime_acceptance_checklist.sh`
- Windows：双击 `generate_native_runtime_acceptance_checklist.bat`

## 文件完整性校验

编辑器导出的完整原生 Runtime 包会附带：

- `native-runtime-file-integrity.json`：核心文件 SHA-256 清单，覆盖 `game_data.json`、Runtime 脚本、启动脚本、requirements、素材和 `export_manifest.json`。
- `native-runtime-file-integrity.md`：同一份清单的人类可读摘要，包含文件数量、总大小、最大文件和校验命令。

这份清单默认不包含可重新生成的诊断报告、完整性报告本身、缓存目录和本机 App 构建输出，避免刷新报告或打包 App 后造成误报。

验证当前包：

```bash
python3 runtime_player.py --verify-file-integrity .
```

重新生成完整性清单：

```bash
python3 runtime_player.py --write-file-integrity-reports .
```

随包脚本：

- macOS：双击 `校验原生Runtime文件完整性.command`
- Linux：运行 `./verify_native_runtime_file_integrity.sh`
- Windows：双击 `verify_native_runtime_file_integrity.bat`

如果下载页面同时提供 `.zip.sha256` 或 `.zip.checksum.json`，可以先用它们校验压缩包本身；解压后再运行上面的包内完整性校验，能覆盖“下载损坏”和“解压后文件缺失/被改动”两层风险。

如果同时提供 `.zip.verify.command`、`.zip.verify.sh` 或 `.zip.verify.bat`，下载者可以把脚本和 zip 放在同一目录，直接运行对应系统脚本完成压缩包 SHA-256 校验。

如果下载页面提供 `.zip.release-artifacts.md` 或 `.zip.release-artifacts.json`，它们是维护者生成的发布附件索引：里面会列出这次 Release 建议上传的 zip、校验文件、机器可读索引，以及解压后应查看的包内报告。

如果下载页面提供 `.zip.release-notes.md`，它是维护者可直接复制到 GitHub Release 正文的发布说明草稿，通常会包含主包、SHA-256、三系统一键校验脚本和包内完整性校验步骤。

## 3D 资产清单

不启动窗口，输出 3D 模型和 3D 场景的发布前资产清单：

```bash
python3 runtime_player.py --describe-3d-assets .
```

导出包会自动附带一份 `native-runtime-3d-asset-report.json`。这份报告会列出：

- 资产类型、导出路径、是否被角色或剧情场景引用
- glTF 节点、网格、primitive、材质、贴图槽、动画通道、相机、灯光数量
- `.glb / .vrm` 二进制容器的文件头、声明长度、JSON chunk 和 BIN chunk 状态
- 顶点、三角面、draw call、材质、贴图和动画通道的静态性能预算估算
- 材质里的基础色、法线、遮蔽、自发光、金属/粗糙度贴图槽是否能解析到图片
- 动画名称、通道数量、采样器数量、目标节点和 transform 路径
- scene、node、mesh、material、texture、skin、animation 等 glTF 内部索引是否断链
- `.gltf` 外部 `bin / 图片 / 贴图` 依赖是否缺失或越界
- `fbx / obj` 等建议转换格式的提示
- 每个问题对应的修复建议

如果项目包含 3D 场景或 3D 角色模型，建议在打包 App 前先看这份清单，再运行 `--doctor` 和 `--release-candidate-report`。

导出包还会自动附带 `native-runtime-3d-asset-summary.md`。它和 JSON 清单内容一致，但排版更适合人直接阅读、复制到 Issue，或作为 Release notes 的资产检查摘要。也可以手动重新生成：

```bash
python3 runtime_player.py --describe-3d-assets-markdown .
```

编辑器导出的完整原生 Runtime 包还会附带 `native-runtime-3d-risk-digest.json`。这份文件是给发布页和自动化工具读取的精简风险摘要，会把性能预算、GLB/VRM 容器、内部引用、贴图槽和依赖风险浓缩成少量指标与优先问题，并保留 `assetId`、导出路径和引用位置预览，方便编辑器把风险直接定位回素材库。

## 发布前自检

不启动窗口，输出发布前诊断报告。这个检查会覆盖入口场景、缺失素材、素材格式风险、大文件风险、存档位数量、成品 UI 皮肤素材引用等：

```bash
python3 runtime_player.py --release-check .
```

## 视频后端状态

原生 Runtime 默认保留“影院式预览卡 + 系统播放器桥接”兜底；安装可选视频依赖后，会优先尝试 PyAV/FFmpeg 音画同步内嵌播放。如果 PyAV 不可用、音频解码失败或目标编码不兼容，会继续回落到 OpenCV 窗口内画面播放，再回落到系统播放器桥接。

查看当前机器的视频后端能力：

```bash
python3 runtime_player.py --describe-video-backends .
```

如果想检查当前导出包是否能生成窗口内视频帧并支持内嵌画面播放，可以运行：

```bash
python3 runtime_player.py --probe-video-preview .
```

如果想启用窗口内音画同步播放和 OpenCV 画面兜底，可以额外安装可选依赖：

```bash
python3 -m pip install -r requirements-native-runtime-video.txt
```

安装后，视频卡片可按 `V` 优先在窗口内进行 PyAV 音画同步播放 / 暂停，按 `O` 调用系统播放器兜底；如果 PyAV 打不开，会自动尝试 OpenCV 画面播放，再回落到默认桥接方案。`--probe-video-preview` 会输出每个视频的探针状态，方便发布前确认是缺依赖、缺 pygame、文件缺失还是编码无法读取。

这条路线目前仍是商业化候选实现：PyAV 路径已经负责解码音频缓冲并按播放时钟驱动画面帧，OpenCV 负责无音频画面兜底；正式发布前仍需要在目标 macOS / Windows / Linux 机器上做 OP / ED / PV 编码兼容性实机验证。

## 快速启动

```bash
python3 runtime_player.py game_data.json
```

如果你下载的是已经打包好的 Native Runtime Preview zip，先解压，再按平台启动：

- macOS：优先打开 `.app`；如果系统提示未签名，可右键选择“打开”并确认来源是官方 Release 页面。
- Windows：打开解压目录里的 `.exe`；如果 SmartScreen 提示未知发布者，先用随包 `.sha256`、`.checksum.json` 或 `.verify.bat` 校验压缩包。
- Linux：运行解压目录里的可执行文件；如果没有执行权限，先给启动文件加执行权限。

如果你下载的是编辑器导出的源码式 Runtime 包，还没有打成 App，可以用随包脚本启动：

- macOS：双击 `启动原生Runtime预览.command`
- Linux：运行 `./run_native_runtime_preview.sh`
- Windows：双击 `run_native_runtime_preview.bat`

## 打包成独立 App

导出的原生 Runtime 包已经包含 PyInstaller 打包入口。创作者在目标系统上执行对应脚本，就可以把 `runtime_player.py + game_data.json + 素材` 打进 `native_app_dist/`，同时生成 `native_app_package_manifest.json` 和一个用于上传到 Release 的 Preview zip：

- macOS：双击 `打包原生Runtime应用.command`
- Linux：运行 `./build_native_runtime_app.sh`
- Windows：双击 `build_native_runtime_app.bat`

也可以手动执行：

```bash
python3 -m pip install -r requirements.txt -r requirements-build.txt
python3 build_native_runtime_app.py --mode onedir .
```

打包清单会记录发布前自检、视频后端状态和视频内嵌画面探针结果，方便排查目标系统上的视频/素材问题。
清单也会记录 3D 资产 JSON 清单与 Markdown 摘要的状态，方便确认打包前后 3D 模型、场景、材质贴图槽和动画通道检查结果没有丢失。

在编辑器导出的原生 Runtime 包中，对应命令是：

```bash
python3 -m pip install -r requirements-native-runtime.txt -r requirements-native-runtime-build.txt
python3 build_native_runtime_app.py --mode onedir .
```

打包脚本默认会先运行 `python3 runtime_player.py --release-check .`。如果自检发现错误，会先停止打包，避免把明显缺素材或入口错误的版本发出去。

如果想生成单文件可执行程序：

```bash
python3 build_native_runtime_app.py --mode onefile .
```

如果想覆盖应用名和 macOS Bundle Identifier：

```bash
python3 build_native_runtime_app.py --mode onedir --app-name YourGame --bundle-id com.canvasia.yourgame .
```

macOS 的 `onedir` 模式会在 `native_app_dist/` 下生成 `.app` 和一个同名运行目录。优先把 `.app` 作为本机测试对象；正式分发前再做签名、公证和完整点测。

## 三系统分发状态

PyInstaller 通常需要在目标系统本机打包，不建议期待从 macOS 直接交叉编译 Windows / Linux：

- macOS：生成 `.app`，未签名/未公证时可作为 Preview 下载测试，正式公开分发需要 Developer ID 签名和 notarization。
- Windows：在 Windows 上运行 `build_native_runtime_app.bat`，会生成 `.exe` 或 onedir 目录；未签名时 SmartScreen 可能提示未知发布者。
- Linux：在 Linux 上运行 `./build_native_runtime_app.sh`，会生成 Linux 可执行目录；后续可继续封装 AppImage、deb/rpm 或 Flatpak。

## 手机端状态

手机端不走 PyInstaller，当前不能直接由这个脚本生成 Android APK 或 iOS IPA。可行路线分三档：

- 近期可试：继续使用网页 Runtime / WebView 包装，先验证手机触控、横竖屏、音频策略和存档。
- 中期路线：做独立 Android Runtime，把 `game_data.json` 映射到 Kivy / Python-for-Android 或 Godot 这类移动壳。
- 长期路线：做 iOS / Android 双端原生 Runtime，共用项目格式，但渲染、音频、存档和商店发布链要单独实现。

因此手机端现在应标记为实验规划，不建议和桌面原生 Runtime 混在同一个发布承诺里。

Runtime 启动失败时，会在用户目录写入错误日志：

```text
~/.canvasia-engine/native-runtime-logs/
```

打包脚本不会替你做平台签名、公证或杀毒误报处理；正式公开发布前，仍建议在对应系统上做一次完整人工点测。

## 第一版存档 / 读档

当前已经支持：

- `F5`：快速存档
- `F8 / F9`：读入快速存档
- `F6`：打开正式存档面板
- `F7`：打开读档面板
- `F11`：切换窗口 / 全屏
- `F1 / Tab`：打开系统菜单
- `F2 / ?`：打开操作帮助
- `H`：打开文本历史
- `A`：开启 / 关闭自动播放
- `S`：开启 / 关闭已读快进
- `F12 / P`：保存当前画面截图
- 鼠标左键：推进文本 / 确认
- 鼠标右键：打开系统菜单；弹窗内右键返回 / 关闭
- 鼠标中键 / `U`：隐藏或恢复界面，便于清屏查看 CG / 背景
- 鼠标滚轮上：打开或滚动文本历史
- 鼠标滚轮下：推进当前文本；历史面板内向下滚动
- 系统菜单里的 `体验设置`：主题 / 显示模式 / 文字速度 / 文字大小 / 文本框透明度 / 自动播放语音等待 / 四路音量
- 系统菜单里的 `玩家档案`：本地游玩次数、累计时长、续玩次数
- 系统菜单里的 `续玩记录`：读取或清除自动续玩位置
- 系统菜单里的 `资料馆`：支持章节 / 音乐 / CG / 地点 / 角色 / 结局 / 成就标签切换
- 资料馆里 `← / →`：切换馆页
- `Ctrl + 1 / 2 / 3`：写入前 3 个正式存档位
- `Ctrl + Shift + 1 / 2 / 3`：读入前 3 个正式存档位
- `Esc`：关闭面板 / 退出预览

存档文件会写到用户目录下：

```text
~/.canvasia-engine/native-runtime-saves/
```

玩家档案和续玩记录也会写到用户目录下：

```text
~/.canvasia-engine/native-runtime-profiles/
~/.canvasia-engine/native-runtime-autoresume/
```

截图会保存到：

```text
~/.canvasia-engine/native-runtime-screenshots/
```

## 字体与阅读辅助

原生 Runtime 会优先读取项目 `gameUiConfig.fontAssetId` 指向的字体素材，支持 `ttf / otf / ttc`。如果项目没有绑定字体素材，或字体加载失败，会按 `fontFamily`、`fontStyle` 和系统字体候选链回退，不会因为缺字体直接退出。

文本历史会记录已经展示过的台词 / 旁白 / 视频卡片说明 / 片尾字幕说明。如果历史条目绑定了语音，可在历史面板里选中条目后按 `R / V` 回听；语音素材缺失时会给出状态提示。自动播放会在当前文本完全显示后按设置间隔推进，也可设置为等待语音播放结束后再计时；已读快进会读取本机已保存的已读文本记录，遇到未读文本、选项或视频卡片会停下。

已读记录会写入 Runtime 进度文件，并带有文本内容摘要；如果创作者后续修改了同一位置的台词，Runtime 会把它视为新文本，避免快进误跳过新内容。

快速存档、正式存档和自动续玩会保存最近的历史文本快照，读档后仍能打开历史面板查看存档点之前的文本。

## 存档自检

不启动窗口，只验证存档写入和读回：

```bash
python3 runtime_player.py --exercise-save-load .
```

## 存档面板摘要自检

不启动窗口，输出当前项目的正式存档分页摘要：

```bash
python3 runtime_player.py --describe-save-dialog .
```

## 标题页自检

不启动窗口，输出原生标题页的菜单、Logo、续玩与存档摘要：

```bash
python3 runtime_player.py --describe-title-screen .
```

## 设置自检

不启动窗口，验证主题 / 显示模式 / 文字速度 / 音量设置的写入与读回：

```bash
python3 runtime_player.py --exercise-settings .
```

## 资料馆进度自检

不启动窗口，验证章节 / 音乐 / CG / 地点 / 角色 / 结局资料馆进度的写入与读回：

```bash
python3 runtime_player.py --exercise-archives .
```

## 粒子自检

不启动窗口，验证当前项目里的粒子卡能否生成原生 Runtime 可播放条目：

```bash
python3 runtime_player.py --exercise-particles .
```

## 高级演出自检

不启动窗口，验证镜头 / 闪屏 / 淡入淡出 / 滤镜 / 景深这类演出卡能否被原生 Runtime 规范化：

```bash
python3 runtime_player.py --exercise-visual-effects .
```

## 视频桥接自检

原生 Runtime Preview 会优先尝试可选 PyAV/FFmpeg 音画同步内嵌播放，并保留 OpenCV 画面播放和系统默认视频播放器作为兼容性兜底。这个命令可检查导出包里有哪些视频、是否存在、被哪些视频卡引用，以及当前系统是否能唤起默认播放器：

```bash
python3 runtime_player.py --describe-video-bridge .
```

如果项目依赖 OP / ED / PV，正式发布前仍建议同时导出网页包或 NW.js 桌面包实机确认，或在目标系统安装可选视频依赖后完整点测一次。

## 玩家档案自检

不启动窗口，验证玩家档案和自动续玩记录的写入、读回与清除：

```bash
python3 runtime_player.py --exercise-profile .
```
