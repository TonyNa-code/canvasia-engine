---
name: Release / package problem
about: 反馈下载、安装、启动、导出包或校验文件问题
title: "[Release] "
labels: release, bug
assignees: ''
---

## 问题类型

- [ ] 下载附件缺失或下载失败
- [ ] 校验文件 / SHA-256 对不上
- [ ] 编辑器预览包无法启动
- [ ] 网页试玩包无法运行
- [ ] Windows / macOS / Linux 桌面包无法运行
- [ ] 原生 Runtime 包无法运行
- [ ] 导出成功，但生成的游戏包有问题
- [ ] 其他：

## 发布版本与附件

- Release tag：
- 下载的附件文件名：
- 是否从本仓库 Release 页面下载：
- 是否校验过 `.sha256` / `.checksum.json` / `verify_release_assets.*`：

## 环境信息

- 系统与版本：
- CPU 架构：Intel / Apple Silicon / x64 / arm64 / 其他
- Python 版本（如果从源码运行）：
- 浏览器版本（如果是网页试玩包）：

## 复现步骤

1.
2.
3.

## 实际结果

请描述看到的错误、弹窗、终端输出或异常表现。

## 预期结果

你原本期待它如何启动、安装、导出或运行？

## 可附上的诊断文件

上传前可以先删掉不想公开的项目名、角色名、路径或截图里的私人信息。

- `local-verify-latest.md`
- `native-runtime-release-control-report.md`
- `native-runtime-release-check.json`
- `*.release-artifacts.md`
- `*.release-notes.md`
- 校验脚本输出截图
- 终端错误截图或日志

## 附加说明

如果是签名、公证、Gatekeeper、SmartScreen 或杀毒软件提示，请附上提示截图和你使用的系统版本。
