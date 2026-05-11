# Beginner-First Galgame Engine Blueprint

## 中文速览

这是一套给“完全不会编程的人”使用的 galgame 引擎蓝图。

它的核心目标不是让你学习代码，而是把做游戏变成这些简单动作：

- 上传背景图、立绘、CG、音乐、音效、语音
- 输入角色名字和台词
- 点击按钮插入“选项”“跳转”“切换背景”“播放音乐”
- 直接预览剧情效果
- 一键导出成可玩的游戏

这套引擎正式命名为 `Canvasia Engine`。

第一版最重要的设计思路只有一句话：

> 你负责写故事和整理素材，引擎负责处理程序。

第一版先做这些：

- 章节与场景管理
- 台词、旁白、选项、跳转
- 背景、立绘、CG、BGM、音效、语音
- 存档、读档、回看日志、自动、快进
- 预览和导出

第一版先不做这些：

- Live2D
- 战斗系统
- 3D 场景
- 复杂粒子特效
- 一开始就同时兼容所有平台

编辑器会分成 5 个主要页面：

- 首页：新建项目、打开项目、导出
- 剧情编辑器：写台词、插入选项和跳转
- 资源库：管理图片和音频
- 角色管理：管理人物名字、颜色、表情、立绘
- 游戏预览：直接试玩当前剧情

最关键的界面会是“剧情编辑器”：

- 左边是章节和场景列表
- 中间是一张张剧情卡片
- 右边是当前卡片的设置

这样你看到的会更像“做PPT + 写小说”，而不是“写程序”。

如果这份蓝图方向你喜欢，下一步最适合做的是：

1. 先把第一版界面结构画出来
2. 再开始做最核心的“剧情编辑器”

## 1. Engine Positioning

Working name: `Canvasia Engine`

Target:

- A visual-novel engine made for creators with zero programming knowledge.
- The creator should be able to make a playable galgame mainly by:
  - uploading files
  - typing character names and dialogue
  - clicking buttons to insert choices and jumps
  - previewing and exporting
- The engine should hide technical details by default and keep advanced options optional.

Core promise:

> "You make the story. The engine handles the program."

## 2. Who This Engine Is For

Primary user:

- Someone creating an original galgame alone
- May not understand programming, folders, file formats, or command lines
- Needs a stable, guided workflow with low mental pressure

This means the engine must:

- avoid code editing
- use plain language instead of technical terms where possible
- warn clearly when a file is missing or a jump target is broken
- auto-save often
- make it hard to "break the project"

## 3. Design Principles

1. No-code first
The user should finish most work without seeing script files, JSON, or terminal commands.

2. One task, one panel
Each screen should do one clear job: write story, manage assets, edit characters, test game, export game.

3. Human words over technical words
Use labels like "Background", "Character", "Choice", "Go to scene", and "Play music".
Avoid labels like "node graph", "asset binding", or "event dispatch" in the main UI.

4. Safe by default
Auto-save, undo, duplicate scene, version snapshots, and missing-file checks should be built in early.

5. Powerful through building blocks
Instead of asking users to write logic, offer reusable blocks:
- dialogue
- narration
- background change
- show character
- hide character
- play BGM
- play sound effect
- voice line
- choice
- jump
- condition
- variable change

## 4. What The User Will Actually Do

Ideal workflow:

1. Create a new project
2. Enter game title, resolution, and language
3. Add characters with name, color, and portrait defaults
4. Drag images, audio, and video into the asset library
5. Create chapters and scenes
6. Add story blocks line by line
7. Insert choices and branch jumps with buttons
8. Click preview to test instantly
9. Click export to build a playable game package

The user should feel like they are using a mix of:

- a story-writing tool
- a media organizer
- a slideshow editor

Not like they are programming.

## 5. V1 Feature Scope

V1 goal:

> Let one beginner build a complete short galgame chapter without code.

### Must-have features

Story editing:

- Chapter list
- Scene list
- Dialogue block
- Narration block
- Choice block
- Jump block
- Simple condition block
- Variable add/set block

Visual control:

- Set background
- Show up to 3 characters on screen
- Character positions: left, center, right
- Character expressions
- CG display
- Screen fade in/out

Audio control:

- Play BGM
- Stop BGM
- Play sound effect
- Voice line per dialogue
- Volume settings

Player features:

- Save / load
- Auto mode
- Skip read text
- Backlog
- Hide UI
- Title menu
- Settings menu

Editor quality-of-life:

- Drag-and-drop asset import
- Auto-save
- Undo / redo
- Missing asset warnings
- Broken jump warnings
- One-click preview
- One-click export

### Good to have in V1 if time allows

- Simple affection system
- Chapter unlock settings
- Text speed presets
- Theme presets for message box UI
- Quick template project

### Should NOT be in V1

To keep the first version realistic and beginner-friendly, do not start with:

- Live2D editing
- combat systems
- 3D scenes
- complex particle editor
- mobile touch adaptation as a main target
- cloud collaboration
- online patch launcher

These can wait until the engine is stable.

## 6. Core Editor Screens

The editor should have five main screens.

### 6.1 Dashboard

Purpose:

- create project
- open project
- see recent projects
- export game

Should show:

- project name
- cover image
- last edited time
- export button
- preview button

### 6.2 Story Editor

This is the heart of the engine.

Layout:

- Left: chapter and scene tree
- Center: story block timeline
- Right: properties panel for the selected block

Each block should be a visible card with plain labels.

Example blocks:

- `Dialogue`
- `Narration`
- `Choice`
- `Go To Scene`
- `Set Background`
- `Show Character`
- `Play BGM`

This is easier for beginners than raw scripts and less scary than a full node graph.

### 6.3 Asset Library

Categories:

- Backgrounds
- Character sprites
- Expressions
- CG
- BGM
- Sound effects
- Voice
- Video
- UI images

Useful actions:

- drag in files
- rename asset
- preview asset
- replace missing asset
- see which scenes are using the asset

### 6.4 Character Manager

Each character should have:

- display name
- text color
- default side
- sprite collection
- expression collection
- optional voice pack mapping

This allows the user to pick a character first and then choose an expression from a simple menu.

### 6.5 Game Preview

The preview should launch instantly from the current scene.

Helpful controls:

- start from this block
- simulate choice selection
- show variable values
- jump to title

## 7. Story Model

Internally, the story should be stored in a simple block-based structure.

Why:

- easier to edit visually
- easier to validate
- easier to export
- easier to repair if something breaks

Simple internal concept:

- A project contains chapters
- A chapter contains scenes
- A scene contains ordered blocks
- Some blocks jump to another scene
- Variables store route state such as affection or flags

Example block types:

- dialogue
- narration
- background
- character_show
- character_hide
- music_play
- music_stop
- sfx_play
- voice_play
- choice
- jump
- condition
- variable_set
- variable_add

## 8. Suggested Project File Structure

The user does not need to touch these files, but the engine should keep them clean and readable.

```text
MyGame/
  project.json
  assets/
    backgrounds/
    sprites/
    cg/
    bgm/
    sfx/
    voice/
    video/
    ui/
  data/
    characters.json
    variables.json
    chapters/
      chapter_01.json
      chapter_02.json
  saves/
  exports/
```

Why this matters:

- easy backup
- easy recovery
- easy future migration
- users can still move their whole project like a normal folder

## 9. Beginner-Friendly UX Rules

These rules are important enough to shape the whole engine.

### 9.1 Always explain actions in plain words

Bad:

- "Bind target scene"

Good:

- "Choose which scene this option will go to"

### 9.2 Never leave the user stuck

If a scene jump is broken, show:

- where the problem is
- how to fix it
- a button to fix it now

### 9.3 Offer templates instead of blank fear

Examples:

- romance school template
- mystery template
- fantasy template
- empty project template

### 9.4 Prefer dropdowns and buttons over manual typing

For example:

- choose character from list
- choose expression from thumbnails
- choose BGM from library
- choose jump target from scene picker

### 9.5 Preview everything early

The faster the user can preview, the less scary development feels.

## 10. Technical Direction

This section is for implementation planning, not for the end user.

Recommended architecture:

- Desktop editor app
- Built with web-style UI for fast development and cross-platform support
- Runtime separated from editor
- Export target first as HTML5 game package
- Later wrap exports for Windows desktop release

Why this route is strong:

- easier to build a modern visual editor
- easier to support preview inside the editor
- easier to export to multiple platforms later
- faster iteration than building a custom native engine from scratch

Practical implementation split:

- `Editor`: the tool the creator uses
- `Runtime`: the player that runs the story
- `Builder`: the exporter that packages the game

## 11. V1 Runtime Features

The runtime should support:

- text display with name box
- layered backgrounds and character sprites
- transitions
- audio playback
- save/load
- backlog
- skip / auto
- branching logic
- variables and conditions

The runtime should prioritize:

- stability
- clean text rendering
- low loading friction

## 12. Data Safety

Because the user is a beginner, data safety is not optional.

The engine should include:

- auto-save every short interval
- restore project after crash
- export backup package
- snapshot before major changes
- validation before export

Validation checklist before export:

- missing files
- empty dialogue names where required
- broken jump targets
- duplicate IDs
- invalid variable references

## 13. Visual Style Direction For The Editor

The editor should feel:

- soft
- clear
- calm
- not intimidating

UI ideas:

- warm light background
- clean cards
- large readable text
- generous spacing
- image thumbnails for assets
- obvious primary buttons

The editor should look like a creative tool, not an IDE.

## 14. Development Roadmap

### Phase 1: Prototype

Goal:

- load project
- create chapters and scenes
- add dialogue blocks
- preview a simple scene

### Phase 2: Usable V1

Goal:

- full story block system
- asset library
- character manager
- save/load
- export

### Phase 3: Comfort Upgrade

Goal:

- affection system preset
- UI theme presets
- better preview tools
- stronger error checking

### Phase 4: Advanced Expansion

Goal:

- richer animation presets
- resolution presets
- platform packaging
- optional advanced mode

## 15. Recommended First Build Target

The smartest first target is:

> a desktop editor that exports a playable PC galgame with dialogue, choices, saves, and basic effects

Not the smartest first target:

- phone release first
- huge animation system first
- trying to support every platform immediately

## 16. What Success Looks Like

The first version is successful if a complete beginner can:

1. import backgrounds, sprites, and music
2. write a short branching story
3. preview it without help
4. export a playable version

If that works, the engine is already valuable.

## 17. Next Practical Step

After this blueprint, the next step should be:

1. define the exact V1 screens
2. draw the editor page structure
3. choose the project data format
4. build the story editor first

## 18. Plain-Language Summary For The Creator

You should be able to make the game by doing only these kinds of things:

- upload files
- click pictures
- choose from menus
- type names and dialogue
- click preview
- click export

If we stay loyal to that rule, this engine will remain beginner-friendly even as it grows.
