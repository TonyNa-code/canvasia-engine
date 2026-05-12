(function attachStoryBlockCatalogTools(global) {
  const BLOCK_LABELS = Object.freeze({
    background: "切换背景",
    dialogue: "台词",
    narration: "旁白",
    character_show: "显示角色",
    character_hide: "隐藏角色",
    music_play: "播放音乐",
    music_stop: "停止音乐",
    sfx_play: "播放音效",
    video_play: "播放视频",
    credits_roll: "片尾字幕",
    particle_effect: "粒子特效",
    screen_shake: "屏幕震动",
    screen_flash: "闪屏",
    screen_fade: "黑场淡入淡出",
    camera_zoom: "镜头推近拉远",
    camera_pan: "镜头平移",
    screen_filter: "回忆滤镜",
    depth_blur: "景深模糊",
    jump: "跳转",
    variable_set: "设置变量",
    variable_add: "修改变量",
    choice: "选项",
    condition: "条件判断",
  });

  const MUSIC_END_MODE_LABELS = Object.freeze({
    until_next_music: "播到下一首或停止卡",
    scene_end: "播完整个场景",
    after_block: "播到指定卡片后",
  });

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

  function getSafeMusicEndMode(mode) {
    return hasOwn(MUSIC_END_MODE_LABELS, mode) ? mode : "until_next_music";
  }

  function getMusicEndModeLabel(mode) {
    return MUSIC_END_MODE_LABELS[getSafeMusicEndMode(mode)];
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

  global.CanvasiaEditorStoryBlockCatalog = Object.freeze({
    BLOCK_LABELS,
    MUSIC_END_MODE_LABELS,
    getBlockLabel,
    getSafeMusicEndMode,
    getMusicEndModeLabel,
    renderMusicEndModeOptions,
  });
})(typeof window !== "undefined" ? window : globalThis);
