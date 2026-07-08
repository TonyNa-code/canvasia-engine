(function attachStoryBlockActionTools(global) {
  const ADD_BLOCK_ACTIONS = Object.freeze({
    "add-dialogue": Object.freeze({ blockType: "dialogue" }),
    "add-narration": Object.freeze({ blockType: "narration" }),
    "add-choice": Object.freeze({ blockType: "choice" }),
    "add-background": Object.freeze({ blockType: "background" }),
    "add-character-show": Object.freeze({ blockType: "character_show" }),
    "add-character-hide": Object.freeze({ blockType: "character_hide" }),
    "add-music-play": Object.freeze({ blockType: "music_play" }),
    "add-music-stop": Object.freeze({ blockType: "music_stop" }),
    "add-sfx-play": Object.freeze({ blockType: "sfx_play" }),
    "add-video-play": Object.freeze({ blockType: "video_play" }),
    "add-credits-roll": Object.freeze({ blockType: "credits_roll" }),
    "add-wait": Object.freeze({ blockType: "wait" }),
    "add-particle-effect": Object.freeze({ blockType: "particle_effect" }),
    "add-screen-shake": Object.freeze({ blockType: "screen_shake" }),
    "add-screen-flash": Object.freeze({ blockType: "screen_flash" }),
    "add-screen-fade": Object.freeze({ blockType: "screen_fade" }),
    "add-camera-zoom": Object.freeze({ blockType: "camera_zoom" }),
    "add-camera-pan": Object.freeze({ blockType: "camera_pan" }),
    "add-screen-filter": Object.freeze({ blockType: "screen_filter" }),
    "add-depth-blur": Object.freeze({ blockType: "depth_blur" }),
    "add-jump": Object.freeze({ blockType: "jump" }),
    "add-variable-set": Object.freeze({
      blockType: "variable_set",
      variableRequirement: Object.freeze({ reason: "变量设置卡片需要先有变量。" }),
    }),
    "add-variable-add": Object.freeze({
      blockType: "variable_add",
      variableRequirement: Object.freeze({
        requireNumber: true,
        reason: "数字变量变化卡片需要先有数字变量。",
      }),
    }),
    "add-condition": Object.freeze({
      blockType: "condition",
      variableRequirement: Object.freeze({ reason: "条件判断需要先有变量。" }),
    }),
  });

  function cloneActionConfig(config) {
    return config
      ? {
          ...config,
          variableRequirement: config.variableRequirement ? { ...config.variableRequirement } : null,
        }
      : null;
  }

  function getAddBlockActionConfig(action) {
    return cloneActionConfig(ADD_BLOCK_ACTIONS[String(action ?? "").trim()]);
  }

  function getAddBlockActionEntries() {
    return Object.entries(ADD_BLOCK_ACTIONS).map(([action, config]) => ({
      action,
      ...cloneActionConfig(config),
    }));
  }

  global.CanvasiaEditorStoryBlockActions = Object.freeze({
    ADD_BLOCK_ACTIONS,
    getAddBlockActionConfig,
    getAddBlockActionEntries,
  });
})(typeof window !== "undefined" ? window : globalThis);
