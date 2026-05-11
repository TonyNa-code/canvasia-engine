# Canvasia Engine V1 数据格式设计

## 1. 这份文档解决什么问题

这份文档回答的是：

> Canvasia Engine 第一版，项目内容在电脑里到底怎么保存？

这一步很重要，因为后面的编辑器、预览器、导出器，都会建立在这套格式上。

## 2. V1 数据格式的目标

这套格式需要同时满足 4 件事：

- 对程序来说足够稳定
- 对开发来说足够简单
- 出错时容易检查
- 以后升级格式时容易迁移

所以 V1 采用最稳妥的方案：

- 用 JSON 保存数据
- 用清晰的独立文件分开管理不同内容
- 用固定 ID 连接角色、素材、场景、变量
- 用“剧情卡片数组”保存每个场景里的内容顺序

## 3. 为什么不用一大坨文件全塞一起

如果把所有内容都塞进一个超大文件，会出现几个问题：

- 一改就容易乱
- 很难排查错误
- 后面做自动检查会很痛苦
- 未来加新功能时容易把旧项目搞坏

所以 V1 拆成下面这些核心文件：

- `project.json`：项目基本信息
- `data/assets.json`：素材清单
- `data/characters.json`：角色清单
- `data/variables.json`：变量清单
- `data/chapters/chapter_01.json`：章节和场景内容

## 4. 推荐目录结构

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
    assets.json
    characters.json
    variables.json
    chapters/
      chapter_01.json
      chapter_02.json
```

## 5. 全局规则

### 5.1 每个项目都要有格式版本号

这样以后引擎升级时，能够知道旧项目是不是要自动迁移。

V1 统一使用：

- `formatVersion: 1`

### 5.2 每个对象都要有稳定 ID

比如：

- 角色 ID：`char_linruoxi`
- 场景 ID：`scene_classroom_sunset`
- 素材 ID：`bg_classroom_sunset`

原因：

- 用户可以改显示名字
- 但程序内部引用不能跟着乱掉

### 5.3 显示名字和内部 ID 必须分开

例如：

- 显示名字可以是“林若曦”
- 但内部 ID 应该是 `char_linruoxi`

这样用户改名不会导致场景引用全部失效。

### 5.4 素材路径统一使用相对路径

例如：

- `assets/backgrounds/classroom_sunset.png`

不要保存成电脑上的绝对路径，否则一换电脑就会坏。

### 5.5 场景内容按顺序保存

场景里的剧情卡片用数组按顺序保存，谁在前谁在后，一眼就能确定。

这样最适合：

- 可视化卡片编辑器
- 导出检查
- 场景复制
- 撤销和恢复

## 6. `project.json`

这个文件保存整个项目最顶层的信息。

建议字段：

- `formatVersion`
- `projectId`
- `title`
- `language`
- `resolution`
- `template`
- `editorMode`
- `chapterOrder`
- `entrySceneId`
- `createdAt`
- `updatedAt`

示例：

```json
{
  "formatVersion": 1,
  "projectId": "project_heart_delay",
  "title": "心跳时差",
  "language": "zh-CN",
  "resolution": {
    "width": 1280,
    "height": 720
  },
  "template": "campus_romance",
  "editorMode": "beginner",
  "chapterOrder": [
    "chapter_opening"
  ],
  "entrySceneId": "scene_classroom_sunset",
  "createdAt": "2026-04-13T18:00:00+08:00",
  "updatedAt": "2026-04-13T18:00:00+08:00"
}
```

## 7. `data/assets.json`

这个文件保存所有素材的登记信息。

每个素材建议包含：

- `id`
- `type`
- `name`
- `path`
- `tags`

V1 素材类型建议固定为：

- `background`
- `sprite`
- `cg`
- `bgm`
- `sfx`
- `voice`
- `video`
- `ui`

示例结构：

```json
{
  "formatVersion": 1,
  "assets": [
    {
      "id": "bg_classroom_sunset",
      "type": "background",
      "name": "教室黄昏",
      "path": "assets/backgrounds/classroom_sunset.png",
      "tags": ["校园", "黄昏"]
    }
  ]
}
```

## 8. `data/characters.json`

这个文件保存角色设定和角色可用表情。

每个角色建议包含：

- `id`
- `displayName`
- `nameColor`
- `defaultPosition`
- `bio`
- `defaultSpriteId`
- `expressions`

`expressions` 里每项建议包含：

- `id`
- `name`
- `spriteAssetId`

这样编辑器里就能先选角色，再选表情，不需要用户自己记文件名。

## 9. `data/variables.json`

这个文件保存剧情分支会用到的变量。

V1 建议支持三种变量类型：

- `number`
- `boolean`
- `string`

每个变量建议包含：

- `id`
- `name`
- `type`
- `defaultValue`

数字变量还可以带：

- `min`
- `max`

如果设置了 `min` / `max`，编辑器预览、网页导出和原生 Runtime 都会在变量初始化、`variable_set`、`variable_add` 以及读档恢复时把数字夹回范围内。正式发布前建议保证 `min <= max`，并让 `defaultValue` 落在这个范围里。

## 10. `chapter_01.json`

章节文件保存：

- 章节基本信息
- 场景顺序
- 场景内容

推荐字段：

- `formatVersion`
- `chapterId`
- `name`
- `order`
- `sceneOrder`
- `scenes`

每个场景建议包含：

- `id`
- `name`
- `notes`
- `blocks`

`blocks` 就是这个场景里的剧情卡片数组。

## 11. V1 卡片类型设计

### `background`

作用：

- 切换背景图

核心字段：

- `assetId`
- `transition`

### `dialogue`

作用：

- 显示角色名和台词

核心字段：

- `speakerId`
- `expressionId`
- `text`
- `voiceAssetId`

### `narration`

作用：

- 显示旁白

核心字段：

- `text`

### `character_show`

作用：

- 让角色出现在画面上

核心字段：

- `characterId`
- `expressionId`
- `position`
- `transition`

### `character_hide`

作用：

- 让角色从画面上消失

核心字段：

- `characterId`
- `transition`

### `music_play`

作用：

- 播放 BGM

核心字段：

- `assetId`
- `loop`
- `fadeInMs`

### `music_stop`

作用：

- 停止 BGM

核心字段：

- `fadeOutMs`

### `sfx_play`

作用：

- 播放音效

核心字段：

- `assetId`

### `jump`

作用：

- 直接跳到另一个场景

核心字段：

- `targetSceneId`

### `variable_set`

作用：

- 把某个变量直接设成一个值

核心字段：

- `variableId`
- `value`

### `variable_add`

作用：

- 给数字变量加减数值
- 如果该数字变量设置了 `min` / `max`，计算后的结果会自动限制在范围内

核心字段：

- `variableId`
- `value`

### `choice`

作用：

- 显示多个选项，让玩家选择

核心字段：

- `options`

每个选项建议包含：

- `id`
- `text`
- `gotoSceneId`
- `effects`

`effects` 用来描述选了这个选项后变量要怎么变化。

### `condition`

作用：

- 按变量结果决定跳去哪里

核心字段：

- `branches`
- `elseGotoSceneId`

每个分支建议包含：

- `id`
- `when`
- `gotoSceneId`

## 12. `choice` 和 `condition` 为什么要单独设计

这是因为视觉小说的分支核心就是这两类逻辑：

- 玩家主动选择路线
- 系统根据变量自动分线

把这两类逻辑做成单独卡片，会有 3 个好处：

- 编辑器更好做
- 错误检查更直观
- 新手更容易理解“为什么跳到这里”

## 13. 选项效果 `effects` 的设计

V1 里，选项后的附加效果建议只支持这两种：

- `variable_set`
- `variable_add`

原因很简单：

- 足够覆盖好感度和分线需求
- 逻辑简单
- 不容易出错

示例：

```json
{
  "type": "variable_add",
  "variableId": "affection_linruoxi",
  "value": 1
}
```

## 14. 条件判断 `when` 的设计

V1 条件判断建议支持这些比较符号：

- `==`
- `!=`
- `>`
- `>=`
- `<`
- `<=`

示例：

```json
{
  "variableId": "affection_linruoxi",
  "operator": ">=",
  "value": 1
}
```

## 15. V1 必做校验规则

导出前至少要检查这些：

- 有没有重复 ID
- `entrySceneId` 是否存在
- `gotoSceneId` 是否存在
- `targetSceneId` 是否存在
- 角色引用是否存在
- 表情引用是否存在
- 素材引用是否存在
- 变量引用是否存在
- 数字变量是否被加减了非数字
- 选项文案是否为空
- 场景名是否为空

## 16. 为什么这套格式适合现在的我们

因为它有三个很现实的优点：

1. 简单
不需要复杂脚本语言就能表达一部基础视觉小说。

2. 稳
后面做编辑器的时候，卡片、右侧属性面板、预览器都很好对接。

3. 好扩展
以后想加转场、动画、好感度模板、章节锁，都能往这个结构上继续加。

## 17. 这一步完成后我们能马上做什么

现在有了数据格式，下一步就能进入真正开发原型的阶段。

最适合立刻开始的是：

1. 先搭项目首页和导航
2. 再把“剧情卡片编辑器”做出来
3. 先支持读取这套 JSON 模板
4. 能显示场景树和卡片列表就算跑通第一步

## 18. 对你来说最重要的一句人话

虽然引擎内部会用 JSON 保存这些东西，但以后你正常开发游戏时，不需要直接碰这些文件。

你会看到的应该始终是：

- 角色列表
- 素材缩略图
- 剧情卡片
- 选项按钮
- 预览画面

这些数据文件主要是给“引擎本身”和“我后续帮你开发编辑器”用的。
