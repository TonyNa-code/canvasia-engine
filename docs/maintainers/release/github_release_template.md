# GitHub Release 文案模板（维护者预览版）

公开发布页正文优先使用：

- [`../../github/preview-release-draft.md`](../../github/preview-release-draft.md)

发布前最后闸门优先使用：

- [`../../../RELEASE_P0.md`](../../../RELEASE_P0.md)

生成上传清单、哈希和可复制 Release 正文：

```bash
python3 tools/release/prepare_preview_release.py
```

如果希望把公开推荐附件和校验清单集中到一个可直接上传的目录：

```bash
python3 tools/release/prepare_preview_release.py --copy-public-assets
```

发布后复查 GitHub Release 页面真实附件是否和本地推荐清单一致：

```bash
python3 tools/release/prepare_preview_release.py --release-tag v0.1.0-preview
```

如果输出里出现 `missing suggested artifacts`、`extra release assets` 或 `size mismatches`，先修正 Release 附件，再把该版本标记为可公开推荐。

`prepare_preview_release.py` 会把公开 Release 推荐附件和本地历史产物分开：公开页面只校验最新推荐下载项，旧导出包仍会留在 upload manifest 里作为维护者复查线索，不要求全部上传。

脚本会额外生成 `preview-release-public-assets.sha256`、`preview-release-public-assets.checksum.json`、`verify_release_assets.sh`、`verify_release_assets.command` 和 `verify_release_assets.cmd`，发布时建议和公开推荐附件一起上传，方便下载者校验压缩包未损坏、未被替换。

如果需要额外扫描旧用户名、真实姓名或其他私密字符串，不要把这些词写进仓库文件；用本地环境变量临时传入：

```bash
CANVASIA_PRIVACY_EXTRA_PATTERNS="old-real-name,old-username" python3 tools/release/prepare_preview_release.py
```

维护者发布时应保持以下口径：

- 使用 `Preview`、`Early Access` 或 `source-available preview`。
- 不把当前版本称为完全稳定商业正式版。
- 如果没有签名 / 公证 / 代码签名，必须在 Release notes 里明确说明。
- 不宣传 Android APK / iOS IPA 正式导出。
- Native Runtime 视频当前说明为可选 PyAV / FFmpeg 窗口内音画同步播放、OpenCV 画面兜底和系统播放器桥接兜底；不要承诺所有编码都已完成三系统实机覆盖。
