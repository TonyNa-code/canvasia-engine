(function attachStoryBlockCatalogTools(global) {
  function freezeDefinition(definition) {
    return Object.freeze({
      ...definition,
      tags: Object.freeze([...(definition.tags ?? [])]),
    });
  }

  const STORY_BLOCK_DEFINITIONS = Object.freeze(
    [
      {
        type: "background",
        label: "切换背景",
        compactLabel: "背景",
        group: "画面",
        webStatus: "full",
        nativeStatus: "full",
        note: "背景 / CG 在 Web 与原生 Runtime 中播放；3D 场景会走原生结构检查与预览兜底。",
        tags: ["timelineVisualBeat", "storyContent"],
      },
      {
        type: "character_show",
        label: "显示角色",
        compactLabel: "角色登场",
        group: "角色",
        webStatus: "full",
        nativeStatus: "full",
        note: "支持角色登场、表情、站位、舞台参数和基础转场。",
        tags: ["timelineVisualBeat", "storyContent"],
      },
      {
        type: "character_hide",
        label: "隐藏角色",
        compactLabel: "角色退场",
        group: "角色",
        webStatus: "full",
        nativeStatus: "full",
        note: "支持角色离场和基础转场。",
        tags: ["timelineVisualBeat"],
      },
      {
        type: "dialogue",
        label: "台词",
        compactLabel: "台词",
        group: "文本",
        webStatus: "full",
        nativeStatus: "full",
        note: "支持说话人、表情同步、打字机、语音和文本历史。",
        tags: ["timelineText", "storyContent", "localizable"],
      },
      {
        type: "narration",
        label: "旁白",
        compactLabel: "旁白",
        group: "文本",
        webStatus: "full",
        nativeStatus: "full",
        note: "支持旁白文本、打字机、语音和文本历史。",
        tags: ["timelineText", "storyContent", "localizable"],
      },
      {
        type: "choice",
        label: "选项",
        compactLabel: "选项",
        group: "分支",
        webStatus: "full",
        nativeStatus: "full",
        note: "支持玩家选项、变量效果和目标场景跳转。",
        tags: ["timelineText", "storyContent", "branch", "localizable"],
      },
      {
        type: "condition",
        label: "条件判断",
        compactLabel: "条件",
        group: "分支",
        webStatus: "full",
        nativeStatus: "full",
        note: "支持条件分支、否则分支和变量判断。",
        tags: ["timeline", "branch"],
      },
      {
        type: "jump",
        label: "跳转",
        compactLabel: "跳转",
        group: "分支",
        webStatus: "full",
        nativeStatus: "full",
        note: "支持显式场景跳转。",
        tags: ["timeline", "branch"],
      },
      {
        type: "variable_set",
        label: "设置变量",
        compactLabel: "设置变量",
        group: "变量",
        webStatus: "full",
        nativeStatus: "full",
        note: "支持变量赋值。",
        tags: ["variable"],
      },
      {
        type: "variable_add",
        label: "修改变量",
        compactLabel: "修改变量",
        group: "变量",
        webStatus: "full",
        nativeStatus: "full",
        note: "支持数值变量增减。",
        tags: ["variable"],
      },
      {
        type: "music_play",
        label: "播放音乐",
        compactLabel: "播放 BGM",
        group: "音频",
        webStatus: "full",
        nativeStatus: "full",
        note: "支持 BGM 播放、循环、音量、淡入和范围调度。",
        tags: ["timelineAudioBeat", "audioCue"],
      },
      {
        type: "music_stop",
        label: "停止音乐",
        compactLabel: "停止 BGM",
        group: "音频",
        webStatus: "full",
        nativeStatus: "full",
        note: "支持 BGM 淡出停止。",
        tags: ["timelineAudioBeat", "audioCue"],
      },
      {
        type: "sfx_play",
        label: "播放音效",
        compactLabel: "音效",
        group: "音频",
        webStatus: "full",
        nativeStatus: "full",
        note: "支持音效播放与音量控制。",
        tags: ["timelineAudioBeat", "audioCue"],
      },
      {
        type: "video_play",
        label: "播放视频",
        compactLabel: "视频",
        group: "视频",
        webStatus: "full",
        nativeStatus: "partial",
        note: "Web Runtime 支持内嵌播放；原生 Runtime 支持 PyAV / OpenCV / 系统播放器兜底，需按目标平台验收。",
        tags: ["timelineVisualBeat", "timelineAudioBeat", "storyContent", "localizable"],
      },
      {
        type: "credits_roll",
        label: "片尾字幕",
        compactLabel: "片尾字幕",
        group: "结尾",
        webStatus: "full",
        nativeStatus: "full",
        note: "支持片尾字幕与回想 / 发布检查。",
        tags: ["timelineVisualBeat", "storyContent", "localizable"],
      },
      {
        type: "wait",
        label: "等待停顿",
        compactLabel: "等待停顿",
        group: "演出",
        webStatus: "full",
        nativeStatus: "full",
        note: "支持等待 / 停顿节奏卡；自动播放会按设定时长等待。",
        tags: ["timelineVisualBeat", "storyContent", "runtimeVisualEffect", "effect"],
      },
      {
        type: "particle_effect",
        label: "粒子特效",
        compactLabel: "粒子",
        group: "演出",
        webStatus: "full",
        nativeStatus: "full",
        note: "支持项目粒子预设、图片粒子、密度、速度、重力和颜色等参数。",
        tags: ["timelineVisualBeat", "effect"],
      },
      {
        type: "screen_shake",
        label: "屏幕震动",
        compactLabel: "震动",
        group: "演出",
        webStatus: "full",
        nativeStatus: "full",
        note: "支持屏幕震动。",
        tags: ["timelineVisualBeat", "runtimeVisualEffect", "effect"],
      },
      {
        type: "screen_flash",
        label: "闪屏",
        compactLabel: "闪屏",
        group: "演出",
        webStatus: "full",
        nativeStatus: "full",
        note: "支持闪屏。",
        tags: ["timelineVisualBeat", "runtimeVisualEffect", "effect"],
      },
      {
        type: "screen_fade",
        label: "黑场淡入淡出",
        compactLabel: "淡入淡出",
        group: "演出",
        webStatus: "full",
        nativeStatus: "full",
        note: "支持淡入淡出。",
        tags: ["timelineVisualBeat", "runtimeVisualEffect", "effect"],
      },
      {
        type: "camera_zoom",
        label: "镜头推近拉远",
        compactLabel: "镜头缩放",
        group: "演出",
        webStatus: "full",
        nativeStatus: "full",
        note: "支持镜头推近、拉远和重置。",
        tags: ["timelineVisualBeat", "runtimeVisualEffect", "effect"],
      },
      {
        type: "camera_pan",
        label: "镜头平移",
        compactLabel: "镜头平移",
        group: "演出",
        webStatus: "full",
        nativeStatus: "full",
        note: "支持镜头平移和回中。",
        tags: ["timelineVisualBeat", "runtimeVisualEffect", "effect"],
      },
      {
        type: "screen_filter",
        label: "回忆滤镜",
        compactLabel: "滤镜",
        group: "演出",
        webStatus: "full",
        nativeStatus: "full",
        note: "支持滤镜、色调和清除。",
        tags: ["timelineVisualBeat", "runtimeVisualEffect", "effect"],
      },
      {
        type: "depth_blur",
        label: "景深模糊",
        compactLabel: "景深",
        group: "演出",
        webStatus: "full",
        nativeStatus: "full",
        note: "支持景深模糊和清除。",
        tags: ["timelineVisualBeat", "runtimeVisualEffect", "effect"],
      },
    ].map(freezeDefinition)
  );

  const STORY_BLOCK_DEFINITION_MAP = Object.freeze(
    Object.fromEntries(STORY_BLOCK_DEFINITIONS.map((definition) => [definition.type, definition]))
  );

  const BLOCK_LABELS = Object.freeze(
    Object.fromEntries(STORY_BLOCK_DEFINITIONS.map((definition) => [definition.type, definition.label]))
  );

  const BLOCK_COMPACT_LABELS = Object.freeze(
    Object.fromEntries(STORY_BLOCK_DEFINITIONS.map((definition) => [definition.type, definition.compactLabel ?? definition.label]))
  );

  const RUNTIME_CAPABILITY_ROWS = Object.freeze(
    STORY_BLOCK_DEFINITIONS.map((definition) =>
      Object.freeze({
        type: definition.type,
        group: definition.group,
        webStatus: definition.webStatus,
        nativeStatus: definition.nativeStatus,
        note: definition.note,
      })
    )
  );

  function getStoryBlockDefinition(type) {
    return STORY_BLOCK_DEFINITION_MAP[type] ?? null;
  }

  function getBlockTypesByTag(tag) {
    const safeTag = String(tag ?? "").trim();
    if (!safeTag) {
      return [];
    }
    return STORY_BLOCK_DEFINITIONS.filter((definition) => definition.tags.includes(safeTag)).map((definition) => definition.type);
  }

  function getRuntimeCapabilityRows() {
    return RUNTIME_CAPABILITY_ROWS.map((row) => ({ ...row }));
  }

  function getRuntimeVisualEffectBlockTypes() {
    return getBlockTypesByTag("runtimeVisualEffect");
  }

  function getTimelineTextBlockTypes() {
    return getBlockTypesByTag("timelineText");
  }

  function getTimelineVisualBeatBlockTypes() {
    return getBlockTypesByTag("timelineVisualBeat");
  }

  function getTimelineAudioBeatBlockTypes() {
    return getBlockTypesByTag("timelineAudioBeat");
  }

  function getEffectBlockTypes() {
    return getBlockTypesByTag("effect");
  }

  function getStoryContentBlockTypes() {
    return getBlockTypesByTag("storyContent");
  }

  function getLocalizableBlockTypes() {
    return getBlockTypesByTag("localizable");
  }

  const MUSIC_END_MODE_LABELS = Object.freeze({
    until_next_music: "播到下一首或停止卡",
    scene_end: "播完整个场景",
    after_block: "播到指定卡片后",
  });

  const CHOICE_CONTINUE_TARGET = "__continue__";

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function getEscapeHtml(options = {}) {
    return typeof options.escapeHtml === "function" ? options.escapeHtml : escapeHtml;
  }

  function hasOwn(source, key) {
    return Object.prototype.hasOwnProperty.call(source || {}, key);
  }

  function getBlockLabel(type) {
    return BLOCK_LABELS[type] ?? type ?? "步骤";
  }

  function getCompactBlockLabel(type) {
    return BLOCK_COMPACT_LABELS[type] ?? getBlockLabel(type);
  }

  function getSafeMusicEndMode(mode) {
    return hasOwn(MUSIC_END_MODE_LABELS, mode) ? mode : "until_next_music";
  }

  function getMusicEndModeLabel(mode) {
    return MUSIC_END_MODE_LABELS[getSafeMusicEndMode(mode)];
  }

  function isChoiceContinueTarget(value) {
    return String(value ?? "").trim() === CHOICE_CONTINUE_TARGET;
  }

  function renderMusicEndModeOptions(selectedMode, options = {}) {
    const escape = getEscapeHtml(options);
    const safeMode = getSafeMusicEndMode(selectedMode);
    return Object.entries(MUSIC_END_MODE_LABELS)
      .map(
        ([mode, label]) => `
          <option value="${mode}" ${mode === safeMode ? "selected" : ""}>${escape(label)}</option>
        `
      )
      .join("");
  }

  function createChoiceOptionId(blockId, index) {
    return `${blockId}_option_${Number(index) + 1}`;
  }

  function createConditionBranchId(blockId, index) {
    return `${blockId}_branch_${Number(index) + 1}`;
  }

  function createDefaultChoiceOptions(blockId, options = {}) {
    const targetSceneId = options.targetSceneId ?? "";
    return [
      {
        id: createChoiceOptionId(blockId, 0),
        text: "第一个选项",
        gotoSceneId: targetSceneId,
        effects: [],
      },
      {
        id: createChoiceOptionId(blockId, 1),
        text: "第二个选项",
        gotoSceneId: targetSceneId,
        effects: [],
      },
    ];
  }

  function createDefaultChoiceEffect(options = {}) {
    if (options.numberVariableId) {
      return {
        type: "variable_add",
        variableId: options.numberVariableId,
        value: 1,
      };
    }

    return {
      type: "variable_set",
      variableId: options.variableId ?? "",
      value: options.value,
    };
  }

  function createDefaultConditionRule(options = {}) {
    return {
      variableId: options.variableId ?? "",
      operator: options.operator ?? "==",
      value: options.value,
    };
  }

  function createDefaultConditionBranch(blockId, index, options = {}) {
    return {
      id: createConditionBranchId(blockId, index),
      when: [options.rule ?? createDefaultConditionRule()],
      gotoSceneId: options.targetSceneId ?? "",
    };
  }

  function createDefaultConditionBranches(blockId, options = {}) {
    return [createDefaultConditionBranch(blockId, 0, options)];
  }

  global.CanvasiaEditorStoryBlockCatalog = Object.freeze({
    STORY_BLOCK_DEFINITIONS,
    STORY_BLOCK_DEFINITION_MAP,
    BLOCK_LABELS,
    BLOCK_COMPACT_LABELS,
    RUNTIME_CAPABILITY_ROWS,
    MUSIC_END_MODE_LABELS,
    CHOICE_CONTINUE_TARGET,
    getStoryBlockDefinition,
    getBlockTypesByTag,
    getRuntimeCapabilityRows,
    getRuntimeVisualEffectBlockTypes,
    getTimelineTextBlockTypes,
    getTimelineVisualBeatBlockTypes,
    getTimelineAudioBeatBlockTypes,
    getEffectBlockTypes,
    getStoryContentBlockTypes,
    getLocalizableBlockTypes,
    getBlockLabel,
    getCompactBlockLabel,
    getSafeMusicEndMode,
    getMusicEndModeLabel,
    isChoiceContinueTarget,
    renderMusicEndModeOptions,
    createChoiceOptionId,
    createConditionBranchId,
    createDefaultChoiceOptions,
    createDefaultChoiceEffect,
    createDefaultConditionRule,
    createDefaultConditionBranch,
    createDefaultConditionBranches,
  });
})(typeof window !== "undefined" ? window : globalThis);
