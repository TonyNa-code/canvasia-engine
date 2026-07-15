(function attachStoryBlockActionTools(global) {
  const GROUP_LABELS = Object.freeze({
    story: "剧情文本",
    stage: "角色与画面",
    audio: "声音",
    media: "视频与字幕",
    performance: "镜头与演出",
    flow: "路线与逻辑",
  });

  const ADD_BLOCK_ACTIONS = Object.freeze({
    "add-dialogue": Object.freeze({
      blockType: "dialogue",
      label: "台词",
      group: "story",
      beginnerVisible: true,
      description: "插入一条角色对白，可设置说话人、表情、语音和打字速度。",
    }),
    "add-narration": Object.freeze({
      blockType: "narration",
      label: "旁白",
      group: "story",
      beginnerVisible: true,
      description: "插入一段无说话人的叙述文字，适合心理描写、环境铺垫或转场。",
    }),
    "add-choice": Object.freeze({
      blockType: "choice",
      label: "选项",
      group: "flow",
      beginnerVisible: true,
      description: "插入玩家选择，可连接分支场景或附加变量影响。",
    }),
    "add-background": Object.freeze({
      blockType: "background",
      label: "切背景",
      group: "stage",
      beginnerVisible: true,
      description: "切换背景、CG 或 3D 场景，让当前段落先有画面落点。",
    }),
    "add-stage-image": Object.freeze({
      blockType: "stage_image",
      label: "道具 / 前景贴图",
      group: "stage",
      beginnerVisible: true,
      description: "放入道具、窗框、Cut-in 或光影图层，可自由调整位置、大小、透明度和前后关系。",
    }),
    "add-character-show": Object.freeze({
      blockType: "character_show",
      label: "显示角色",
      group: "stage",
      beginnerVisible: true,
      description: "让角色立绘出场，可控制位置、大小、透明度和进场方式。",
    }),
    "add-character-move": Object.freeze({
      blockType: "character_move",
      label: "角色动作",
      group: "stage",
      beginnerVisible: true,
      description: "让已登场角色平滑移动、换表情或调整大小，适合走位和情绪特写。",
    }),
    "add-character-hide": Object.freeze({
      blockType: "character_hide",
      label: "隐藏角色",
      group: "stage",
      description: "让角色退场，适合角色离开、镜头切换或情绪收束。",
    }),
    "add-music-play": Object.freeze({
      blockType: "music_play",
      label: "播放音乐",
      group: "audio",
      beginnerVisible: true,
      description: "播放 BGM，可配合淡入、音量和范围卡控制场景氛围。",
    }),
    "add-music-stop": Object.freeze({
      blockType: "music_stop",
      label: "停止音乐",
      group: "audio",
      description: "停止当前 BGM，可用于转场、静默、情绪断点或结尾。",
    }),
    "add-sfx-play": Object.freeze({
      blockType: "sfx_play",
      label: "播放音效",
      group: "audio",
      description: "播放一次性音效，适合门铃、脚步、点击、闪回等瞬间反馈。",
    }),
    "add-video-play": Object.freeze({
      blockType: "video_play",
      label: "播放视频",
      group: "media",
      beginnerVisible: true,
      description: "插入 OP、ED、PV 或过场视频，可控制适配方式和音量。",
    }),
    "add-credits-roll": Object.freeze({
      blockType: "credits_roll",
      label: "片尾字幕",
      group: "media",
      description: "插入滚动演职员表，适合 Demo 结尾、ED 或发布版本署名。",
    }),
    "add-wait": Object.freeze({
      blockType: "wait",
      label: "等待停顿",
      group: "performance",
      beginnerVisible: true,
      description: "插入节奏停顿，让演出、音乐或角色反应有呼吸感。",
    }),
    "add-particle-effect": Object.freeze({
      blockType: "particle_effect",
      label: "粒子特效",
      group: "performance",
      description: "添加雨、雪、光点、烟雾等粒子效果，可进一步自定义速度和密度。",
    }),
    "add-screen-shake": Object.freeze({
      blockType: "screen_shake",
      label: "屏幕震动",
      group: "performance",
      description: "制造冲击、惊吓或重击感，适合情绪爆点和动作反馈。",
    }),
    "add-screen-flash": Object.freeze({
      blockType: "screen_flash",
      label: "闪屏",
      group: "performance",
      description: "添加瞬间闪白或闪色，适合回忆、惊讶、拍照和冲击转场。",
    }),
    "add-screen-fade": Object.freeze({
      blockType: "screen_fade",
      label: "黑场淡入淡出",
      group: "performance",
      description: "控制黑场、白场或颜色淡入淡出，常用于章节转场和时间跳跃。",
    }),
    "add-camera-zoom": Object.freeze({
      blockType: "camera_zoom",
      label: "镜头推拉",
      group: "performance",
      description: "让镜头推近或拉远，把注意力压到角色、道具或关键台词上。",
    }),
    "add-camera-pan": Object.freeze({
      blockType: "camera_pan",
      label: "镜头平移",
      group: "performance",
      description: "让镜头轻微移动，适合扫过背景、制造不安或跟随角色视线。",
    }),
    "add-screen-filter": Object.freeze({
      blockType: "screen_filter",
      label: "画面滤镜",
      group: "performance",
      description: "添加回忆、梦境、紧张、故障等滤镜，统一当前段落的画面情绪。",
    }),
    "add-depth-blur": Object.freeze({
      blockType: "depth_blur",
      label: "景深模糊",
      group: "performance",
      description: "用模糊和聚焦强调主体，适合告白、回忆、悬疑和沉浸镜头。",
    }),
    "add-jump": Object.freeze({
      blockType: "jump",
      label: "跳场景",
      group: "flow",
      beginnerVisible: true,
      description: "跳转到另一个场景，用于路线推进、分支合流或章节切换。",
    }),
    "add-variable-set": Object.freeze({
      blockType: "variable_set",
      label: "设置变量",
      group: "flow",
      description: "设置好感度、旗标、路线状态等变量，让选择和剧情有后果。",
      variableRequirement: Object.freeze({ reason: "变量设置卡片需要先有变量。" }),
    }),
    "add-variable-add": Object.freeze({
      blockType: "variable_add",
      label: "修改数值",
      group: "flow",
      description: "让数字变量增加或减少，适合好感度、调查点数和路线进度。",
      variableRequirement: Object.freeze({
        requireNumber: true,
        reason: "数字变量变化卡片需要先有数字变量。",
      }),
    }),
    "add-condition": Object.freeze({
      blockType: "condition",
      label: "条件判断",
      group: "flow",
      description: "根据变量决定后续剧情走向，是制作多路线和隐藏剧情的基础卡片。",
      variableRequirement: Object.freeze({ reason: "条件判断需要先有变量。" }),
    }),
  });

  function getGroupLabel(group) {
    return GROUP_LABELS[String(group ?? "").trim()] ?? "";
  }

  function cloneActionConfig(config) {
    return config
      ? {
          ...config,
          groupLabel: getGroupLabel(config.group),
          beginnerVisible: Boolean(config.beginnerVisible),
          variableRequirement: config.variableRequirement ? { ...config.variableRequirement } : null,
        }
      : null;
  }

  function getAddBlockActionConfig(action) {
    return cloneActionConfig(ADD_BLOCK_ACTIONS[String(action ?? "").trim()]);
  }

  function getAddBlockActionConfigByBlockType(blockType) {
    const safeBlockType = String(blockType ?? "").trim();
    if (!safeBlockType) {
      return null;
    }

    const match = Object.values(ADD_BLOCK_ACTIONS).find((config) => config.blockType === safeBlockType);
    return cloneActionConfig(match);
  }

  function getAddBlockActionEntries() {
    return Object.entries(ADD_BLOCK_ACTIONS).map(([action, config]) => ({
      action,
      ...cloneActionConfig(config),
    }));
  }

  function getBeginnerAddBlockActionEntries() {
    return getAddBlockActionEntries().filter((entry) => entry.beginnerVisible);
  }

  function getBeginnerAddBlockActions() {
    return getBeginnerAddBlockActionEntries().map((entry) => entry.action);
  }

  function buildButtonTitle(config) {
    if (!config) {
      return "";
    }
    return [config.label, config.description, config.groupLabel ? `分类：${config.groupLabel}` : ""]
      .filter(Boolean)
      .join("｜");
  }

  function buildAddBlockSuccessFeedback(config) {
    const label = String(config?.label ?? "").trim() || "剧情卡片";
    const description = String(config?.description ?? "").trim();
    const statusMessage = description ? `已新增${label}：${description}` : `已新增${label}`;
    return {
      label,
      statusMessage,
      toastMessage: `已新增${label}`,
    };
  }

  global.CanvasiaEditorStoryBlockActions = Object.freeze({
    ADD_BLOCK_ACTIONS,
    GROUP_LABELS,
    buildAddBlockSuccessFeedback,
    buildButtonTitle,
    getAddBlockActionConfig,
    getAddBlockActionConfigByBlockType,
    getAddBlockActionEntries,
    getBeginnerAddBlockActionEntries,
    getBeginnerAddBlockActions,
    getGroupLabel,
  });
})(typeof window !== "undefined" ? window : globalThis);
