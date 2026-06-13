# Canvasia Engine Exposure Kit

This kit keeps the public-facing growth work in one place: repository topics, social preview assets, project-site setup, and copy-paste launch posts.

## Repository Setup Checklist

Use the GitHub repository sidebar and settings:

- About description:
  `A no-code visual novel / galgame engine prototype with a visual editor, runtime exports, UI skins, archives, particles, i18n, and release checks.`
- Website:
  `https://tonyna-code.github.io/canvasia-engine/`
- Social preview image:
  [`docs/github/canvasia-social-preview.png`](../github/canvasia-social-preview.png)
- Suggested topics:
  `visual-novel`, `galgame`, `game-engine`, `no-code`, `story-editor`, `vn-engine`, `interactive-fiction`, `gamedev`, `python`, `pygame`, `nwjs`, `live2d`, `i18n`, `creator-tools`

## GitHub Pages

The project landing page lives at:

- [`docs/index.html`](../index.html)

Recommended Pages setting:

- Source: `Deploy from a branch`
- Branch: `main`
- Folder: `/docs`

After Pages is enabled, the expected project-site URL is:

```text
https://tonyna-code.github.io/canvasia-engine/
```

## Social Preview

The current share card is:

- [`docs/github/canvasia-social-preview.png`](../github/canvasia-social-preview.png)

Regenerate it with:

```bash
python3 tools/marketing/generate_social_preview.py
```

Upload the generated PNG in GitHub repository settings under `Social preview`.

## Short Pitch

English:

```text
Canvasia Engine is a no-code visual novel / galgame engine prototype for creators.

It includes a visual story editor, asset workflow, UI skins, archives, particles, Web/Desktop/Native runtime exports, i18n, and release-readiness checks.

Repo: https://github.com/TonyNa-code/canvasia-engine
```

Chinese:

```text
我做了一个源码可见的视觉小说 / galgame 制作引擎 Canvasia Engine。

它偏小白友好：可视化写剧情、导入素材、调 UI、做回想馆/图鉴馆、粒子和演出、导出网页/桌面/原生 Runtime，还带发布前检查。

仓库：https://github.com/TonyNa-code/canvasia-engine
```

Japanese:

```text
Canvasia Engine は、ビジュアルノベル / Galgame 制作者向けの no-code エンジン prototype です。

ビジュアルストーリーエディタ、素材管理、UI スキン、回想システム、パーティクル、Web/Desktop/Native Runtime 書き出し、i18n、公開前チェックを含みます。

Repo: https://github.com/TonyNa-code/canvasia-engine
```

## Longer Launch Post

English:

```text
I am building Canvasia Engine, a creator-friendly visual novel / galgame engine prototype.

The goal is simple: let non-programmers build playable visual novel projects with a visual editor instead of writing scripts from scratch.

Current preview features include:
- visual story cards, choices, variables, and scene graph tools
- asset management for backgrounds, sprites, CGs, BGM, SFX, voice, fonts, Live2D, and 3D assets
- custom game UI skins and visual novel textbox design
- archives / extras such as CG replay, music room, character archive, endings, achievements, and voice replay
- particles, camera effects, filters, flashes, shakes, and fades
- Web, desktop, and native Runtime preview exports
- i18n workflow and release-readiness checks

It is still Preview / Early Access, but feedback is very welcome.

GitHub: https://github.com/TonyNa-code/canvasia-engine
```

Chinese:

```text
Ciallo～我最近在做一个视觉小说 / galgame 制作引擎 Canvasia Engine。

定位是尽量让不会写代码的人，也能通过可视化编辑、上传素材、输入台词、点按钮预览和导出的方式，做出可以试玩的视觉小说 Demo。

目前已经有：
- 可视化剧情卡片、选项、变量、分支和场景图
- 背景、立绘、CG、BGM、音效、语音、字体、Live2D / 3D 素材管理
- 成品 UI 皮肤、按钮状态、九宫格贴图和文本框设计
- CG 回想、音乐鉴赏、角色图鉴、章节回放、结局回收、成就和语音回听
- 粒子、镜头、滤镜、闪屏、震动、淡入淡出等演出
- 网页、桌面、原生 Runtime 预览导出
- 多语言和发布前检查

现在还是 Preview / Early Access，欢迎体验和提建议。

GitHub: https://github.com/TonyNa-code/canvasia-engine
```

## Channel Plan

Recommended order:

1. GitHub polish: topics, social preview, About link, pinned release.
2. Creator demo: publish a tiny downloadable demo project and a short GIF.
3. Chinese communities: Bilibili, galgame groups, TapTap developer community, Zhihu, Xiaohongshu.
4. International communities: Reddit, itch.io devlog, Discord VN developer servers, interactive-fiction forums.
5. Follow-up content: weekly development notes, before/after UI posts, short tutorial clips, and release changelogs.

## Demo Ideas

- `Campus Confession`: one background, one heroine, one choice, one ending.
- `Rainy Memory`: particle rain, narration archive, CG replay.
- `Mystery Hallway`: variables, condition branches, SFX, screen filter.
- `Multilingual Micro Demo`: zh-CN / en-US / ja-JP language switching in one short scene.

## What Not To Promise Yet

Keep public messaging honest:

- Do not call it a fully stable commercial engine yet.
- Mention Preview / Early Access for unsigned builds and native Runtime.
- Avoid promising mobile runtime until touch/audio/layout validation is ready.
- Do not imply generated AI assets are free or bundled; creators provide their own API keys.
