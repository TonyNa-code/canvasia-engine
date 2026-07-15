(function attachCommandPaletteTools(global) {
  const COMMAND_PALETTE_RECENT_LIMIT = 6;
  const storyBlockActionTools = global.CanvasiaEditorStoryBlockActions || {};
  const sceneMoodRecipeTools = global.CanvasiaEditorSceneMoodRecipes || {};

  const SCREEN_COMMANDS = [
    { id: "screen-dashboard", title: "回到制作首页", screen: "dashboard", section: "导航", keywords: ["首页", "路线", "dashboard"] },
    { id: "screen-story", title: "写剧情 / 编排场景", screen: "story", section: "导航", keywords: ["剧情", "台词", "场景", "story"] },
    { id: "screen-assets", title: "管理素材", screen: "assets", section: "导航", keywords: ["素材", "背景", "音乐", "assets"] },
    { id: "screen-characters", title: "管理角色", screen: "characters", section: "导航", keywords: ["角色", "立绘", "人物"] },
    { id: "screen-script", title: "打开台词台本", screen: "script", section: "导航", keywords: ["台本", "语音", "script"] },
    { id: "screen-inspection", title: "打开项目巡检", screen: "inspection", section: "质量", keywords: ["检查", "错误", "doctor"] },
    { id: "screen-preview", title: "试玩与导出", screen: "preview", section: "发布", keywords: ["预览", "导出", "试玩"] },
  ];

  const STORY_BLOCK_COMMAND_ID_BY_ACTION = Object.freeze({
    "add-dialogue": "insert-dialogue",
    "add-narration": "insert-narration",
    "add-choice": "insert-choice",
    "add-background": "insert-background",
    "add-character-show": "insert-character-show",
    "add-character-move": "insert-character-move",
    "add-character-hide": "insert-character-hide",
    "add-music-play": "insert-music-play",
    "add-music-stop": "insert-music-stop",
    "add-sfx-play": "insert-sfx",
    "add-video-play": "insert-video",
    "add-credits-roll": "insert-credits",
    "add-wait": "insert-wait",
    "add-particle-effect": "insert-particle",
    "add-screen-shake": "insert-shake",
    "add-screen-flash": "insert-flash",
    "add-screen-fade": "insert-fade",
    "add-camera-zoom": "insert-camera-zoom",
    "add-camera-pan": "insert-camera-pan",
    "add-screen-filter": "insert-filter",
    "add-depth-blur": "insert-depth-blur",
    "add-jump": "insert-jump",
    "add-variable-set": "insert-variable-set",
    "add-variable-add": "insert-variable-add",
    "add-condition": "insert-condition",
  });

  const STORY_BLOCK_COMMAND_KEYWORDS = Object.freeze({
    "add-dialogue": Object.freeze(["台词", "对白", "dialogue", "角色"]),
    "add-narration": Object.freeze(["旁白", "叙述", "narration", "文字"]),
    "add-choice": Object.freeze(["选项", "分支", "choice", "路线"]),
    "add-background": Object.freeze(["背景", "场景", "background", "bg", "cg", "3d"]),
    "add-character-show": Object.freeze(["立绘", "角色", "显示", "show", "淡入", "位置", "大小"]),
    "add-character-move": Object.freeze(["立绘", "角色", "移动", "走位", "move", "缩放", "换表情", "缓动"]),
    "add-character-hide": Object.freeze(["立绘", "角色", "隐藏", "hide", "淡出"]),
    "add-music-play": Object.freeze(["bgm", "音乐", "播放", "music", "淡入", "范围"]),
    "add-music-stop": Object.freeze(["bgm", "音乐", "停止", "stop", "淡出"]),
    "add-sfx-play": Object.freeze(["音效", "sfx", "sound", "效果音"]),
    "add-video-play": Object.freeze(["视频", "op", "ed", "movie", "video"]),
    "add-credits-roll": Object.freeze(["片尾", "字幕", "staff", "credits", "ed"]),
    "add-wait": Object.freeze(["等待", "停顿", "节奏", "wait", "pause"]),
    "add-particle-effect": Object.freeze(["粒子", "下雪", "下雨", "particle", "特效"]),
    "add-screen-shake": Object.freeze(["震动", "shake", "冲击", "镜头"]),
    "add-screen-flash": Object.freeze(["闪屏", "flash", "白闪", "红闪"]),
    "add-screen-fade": Object.freeze(["黑场", "淡入", "淡出", "fade", "转场"]),
    "add-camera-zoom": Object.freeze(["镜头", "推近", "拉远", "zoom", "camera"]),
    "add-camera-pan": Object.freeze(["镜头", "平移", "pan", "camera"]),
    "add-screen-filter": Object.freeze(["滤镜", "回忆", "调色", "filter", "color"]),
    "add-depth-blur": Object.freeze(["景深", "模糊", "blur", "焦点"]),
    "add-jump": Object.freeze(["跳转", "场景", "jump", "goto"]),
    "add-variable-set": Object.freeze(["变量", "flag", "好感度", "set"]),
    "add-variable-add": Object.freeze(["变量", "数值", "加分", "add"]),
    "add-condition": Object.freeze(["条件", "判断", "if", "condition", "分支"]),
  });

  const STORY_TEMPLATE_COMMANDS = [
    {
      id: "template-playable-scene",
      title: "套用：第一段可试玩",
      subtitle: "背景、BGM、角色登场、对白、选择项和收束淡出",
      templateId: "playable_scene",
      keywords: ["模板", "可试玩", "闭环", "demo", "playable", "第一段"],
    },
    {
      id: "template-opening-intro",
      title: "套用：开场铺垫",
      subtitle: "背景、BGM、旁白、角色登场和第一句对白",
      templateId: "opening_intro",
      keywords: ["模板", "开场", "opening", "intro"],
    },
    {
      id: "template-memory-entry",
      title: "套用：进入回忆",
      subtitle: "黑场、回忆滤镜、旁白和回忆对白",
      templateId: "memory_entry",
      keywords: ["模板", "回忆", "memory", "filter"],
    },
    {
      id: "template-emotion-burst",
      title: "套用：情绪爆点",
      subtitle: "镜头、震动、闪屏和情绪台词",
      templateId: "emotion_burst",
      keywords: ["模板", "爆点", "情绪", "演出"],
    },
    {
      id: "template-branch-choice",
      title: "套用：选项分支",
      subtitle: "旁白、选择项和分支提示",
      templateId: "branch_choice",
      keywords: ["模板", "选项", "分支", "choice"],
    },
    {
      id: "template-scene-outro",
      title: "套用：场景收尾",
      subtitle: "收束旁白、淡出、跳转或段落结束",
      templateId: "scene_outro",
      keywords: ["模板", "收尾", "outro", "结尾"],
    },
    {
      id: "template-op-movie-hook",
      title: "套用：OP 前导",
      subtitle: "OP 视频、黑场过渡和正式开场衔接",
      templateId: "op_movie_hook",
      keywords: ["模板", "op", "opening", "视频", "片头"],
    },
    {
      id: "template-daily-conversation",
      title: "套用：日常对话节奏",
      subtitle: "带 BGM 范围、立绘登场和日常对白节奏",
      templateId: "daily_conversation",
      keywords: ["模板", "日常", "对话", "节奏", "bgm"],
    },
    {
      id: "template-affection-choice",
      title: "套用：好感度选项",
      subtitle: "带变量变化和条件判断的分支段落",
      templateId: "affection_choice",
      keywords: ["模板", "好感度", "变量", "选项", "condition"],
    },
    {
      id: "template-climax-sequence",
      title: "套用：高潮演出段",
      subtitle: "音乐、镜头、闪屏、震动和景深组合演出",
      templateId: "climax_sequence",
      keywords: ["模板", "高潮", "演出", "镜头", "shake", "flash"],
    },
    {
      id: "template-ending-credits",
      title: "套用：ED 与片尾",
      subtitle: "ED 黑场、收束旁白、片尾字幕和停音乐",
      templateId: "ending_credits",
      keywords: ["模板", "ed", "ending", "片尾", "credits"],
    },
    {
      id: "template-mystery-clue",
      title: "套用：悬念线索",
      subtitle: "冷色滤镜、镜头移动、线索发现和变量记录",
      templateId: "mystery_clue",
      keywords: ["模板", "悬念", "线索", "mystery", "clue"],
    },
    {
      id: "template-relationship-reveal",
      title: "套用：关系揭露",
      subtitle: "角色居中、镜头推进、关系真相和条件分支",
      templateId: "relationship_reveal",
      keywords: ["模板", "关系", "揭露", "真相", "relationship"],
    },
    {
      id: "template-branch-merge",
      title: "套用：分支汇合",
      subtitle: "两组选项回到同一汇合点，适合收束分线",
      templateId: "branch_merge",
      keywords: ["模板", "分支", "汇合", "merge", "route"],
    },
  ];

  const TEMPLATE_COMMAND_ID_BY_TEMPLATE_ID = new Map(
    STORY_TEMPLATE_COMMANDS.map((command) => [command.templateId, command.id])
  );

  const RELEASE_WORKFLOW_COMMANDS = [
    {
      id: "release-one-click-polish",
      title: "一键发布前整理",
      subtitle: "批量整理长文本、基础演出和音频范围，并生成整理回执",
      action: "run-project-one-click-polish",
      keywords: ["发布", "整理", "一键", "回执", "polish"],
    },
    {
      id: "release-run-inspection",
      title: "重新巡检项目",
      subtitle: "刷新错误、提醒和发布前修复顺序",
      action: "run-project-inspection",
      keywords: ["巡检", "检查", "错误", "发布"],
    },
    {
      id: "release-preview-regression",
      title: "跑自动试玩回归",
      subtitle: "按路线抽样检查可试玩流程",
      action: "run-preview-regression",
      keywords: ["试玩", "回归", "自动", "测试"],
    },
    {
      id: "release-copy-polish-receipt",
      title: "复制发布前整理摘要",
      subtitle: "把最近一次整理回执复制到剪贴板",
      action: "copy-project-one-click-polish-receipt-summary",
      requiresPolishReceipt: true,
      keywords: ["复制", "摘要", "整理", "回执"],
    },
    {
      id: "release-export-polish-receipt",
      title: "导出发布前整理回执",
      subtitle: "保存最近一次发布前整理明细 Markdown",
      action: "export-project-one-click-polish-receipt",
      requiresPolishReceipt: true,
      keywords: ["导出", "markdown", "整理", "回执"],
    },
  ];

  const PROJECT_SAFETY_COMMANDS = [
    {
      id: "safety-create-checkpoint",
      title: "创建安全快照",
      subtitle: "给当前项目手动存一份可回退版本",
      action: "create-history-checkpoint",
      keywords: ["快照", "安全", "备份", "checkpoint", "save"],
    },
    {
      id: "safety-undo-history",
      title: "撤销上一步项目操作",
      subtitle: "回到项目历史里的上一份状态",
      action: "undo-project-history",
      requiresUndo: true,
      keywords: ["撤销", "回退", "undo", "历史"],
    },
    {
      id: "safety-redo-history",
      title: "重做下一步项目操作",
      subtitle: "重新应用刚撤销的项目状态",
      action: "redo-project-history",
      requiresRedo: true,
      keywords: ["重做", "redo", "历史"],
    },
    {
      id: "safety-restore-previous",
      title: "恢复到上个版本",
      subtitle: "从项目历史里恢复最近一次更早版本",
      action: "restore-previous-version",
      requiresUndo: true,
      keywords: ["恢复", "上个版本", "版本", "history", "rollback"],
    },
  ];

  function normalizeSearchText(value) {
    return String(value ?? "").trim().toLowerCase();
  }

  function buildCommandSearchText(command) {
    return [
      command.title,
      command.subtitle,
      command.section,
      ...(command.keywords ?? []),
    ]
      .map((item) => normalizeSearchText(item))
      .filter(Boolean)
      .join(" ");
  }

  function getSafeRecentLimit(limit = COMMAND_PALETTE_RECENT_LIMIT) {
    const numericLimit = Number.parseInt(limit ?? COMMAND_PALETTE_RECENT_LIMIT, 10);
    return Number.isFinite(numericLimit) && numericLimit >= 0 ? numericLimit : COMMAND_PALETTE_RECENT_LIMIT;
  }

  function sanitizeCommandPaletteCommandId(commandId) {
    const safeId = String(commandId ?? "").trim();
    return /^[a-z0-9][a-z0-9_-]{0,96}$/i.test(safeId) ? safeId : "";
  }

  function sanitizeCommandPaletteRecentIds(source = [], options = {}) {
    const limit = getSafeRecentLimit(options.limit);
    const availableIds = Array.isArray(options.availableIds) ? new Set(options.availableIds) : null;
    const rawItems = Array.isArray(source) ? source : Array.isArray(source?.items) ? source.items : [];
    const seen = new Set();
    const result = [];

    rawItems.forEach((item) => {
      const id = sanitizeCommandPaletteCommandId(item);
      if (!id || seen.has(id) || (availableIds && !availableIds.has(id))) {
        return;
      }
      seen.add(id);
      result.push(id);
    });

    return result.slice(0, limit);
  }

  function mergeCommandPaletteRecentId(recentIds = [], commandId = "", options = {}) {
    const id = sanitizeCommandPaletteCommandId(commandId);
    const limit = getSafeRecentLimit(options.limit);
    const existing = sanitizeCommandPaletteRecentIds(recentIds, { ...options, limit: Math.max(limit, recentIds.length) });
    if (!id || (Array.isArray(options.availableIds) && !options.availableIds.includes(id))) {
      return existing.slice(0, limit);
    }
    return [id, ...existing.filter((item) => item !== id)].slice(0, limit);
  }

  function getCommandPaletteRecentStorageKey(scope = "global") {
    const safeScope = String(scope ?? "global")
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9\u4e00-\u9fa5_-]+/g, "-")
      .replace(/-+/g, "-")
      .slice(0, 72) || "global";
    return `canvasia-engine:editor-command-recent:${safeScope}`;
  }

  function loadStoredCommandPaletteRecentIds(storage, key, options = {}) {
    if (!storage || !key) {
      return [];
    }

    try {
      const raw = storage.getItem(key);
      if (!raw) {
        return [];
      }
      return sanitizeCommandPaletteRecentIds(JSON.parse(raw), options);
    } catch (error) {
      return [];
    }
  }

  function persistStoredCommandPaletteRecentIds(storage, key, recentIds = [], options = {}) {
    if (!storage || !key) {
      return false;
    }

    try {
      storage.setItem(key, JSON.stringify(sanitizeCommandPaletteRecentIds(recentIds, options)));
      return true;
    } catch (error) {
      return false;
    }
  }

  function mergeRecommendedCommandIds(...groups) {
    const seen = new Set();
    const result = [];
    groups.flat().forEach((id) => {
      const safeId = sanitizeCommandPaletteCommandId(id);
      if (!safeId || seen.has(safeId)) {
        return;
      }
      seen.add(safeId);
      result.push(safeId);
    });
    return result;
  }

  function getStoryBlockActionTools(context = {}) {
    return context.storyBlockActionTools ?? global.CanvasiaEditorStoryBlockActions ?? storyBlockActionTools ?? null;
  }

  function getStoryBlockCommandId(action) {
    const safeAction = String(action ?? "").trim();
    if (!safeAction) {
      return "";
    }
    return STORY_BLOCK_COMMAND_ID_BY_ACTION[safeAction] ?? sanitizeCommandPaletteCommandId(`insert-${safeAction.replace(/^add-/, "")}`);
  }

  function getStoryBlockCommandEntries(context = {}) {
    const actionSource = getStoryBlockActionTools(context);
    if (typeof actionSource?.getAddBlockActionEntries !== "function") {
      return [];
    }

    return actionSource
      .getAddBlockActionEntries()
      .map((entry) => ({
        ...entry,
        id: getStoryBlockCommandId(entry.action),
      }))
      .filter((entry) => entry.id && entry.action && entry.blockType);
  }

  function buildStoryBlockCommands(context = {}) {
    return getStoryBlockCommandEntries(context).map((entry) => {
      const label = String(entry.label ?? entry.blockType ?? "剧情卡片").trim() || "剧情卡片";
      const groupLabel = String(entry.groupLabel ?? entry.group ?? "插卡").trim() || "插卡";
      const description = String(entry.description ?? "").trim() || `插入一张${label}剧情卡片。`;
      const keywords = [
        ...(STORY_BLOCK_COMMAND_KEYWORDS[entry.action] ?? []),
        entry.action,
        entry.blockType,
        entry.label,
        entry.groupLabel,
        entry.description,
        entry.beginnerVisible ? "新手常用" : "高级卡片",
      ]
        .map((keyword) => String(keyword ?? "").trim())
        .filter(Boolean);

      return {
        id: entry.id,
        title: `插入${label}卡`,
        subtitle: description,
        action: entry.action,
        section: groupLabel,
        blockType: entry.blockType,
        blockGroup: entry.group ?? "",
        keywords,
      };
    });
  }

  function getStoryTemplateTools(context = {}) {
    return context.storyTemplateTools ?? global.CanvasiaEditorStoryTemplates ?? null;
  }

  function getStoryTemplateSceneForRecommendations(context = {}) {
    if (context.selectedScene && typeof context.selectedScene === "object") {
      return context.selectedScene;
    }

    return {
      blocks: Array.isArray(context.selectedSceneBlocks) ? context.selectedSceneBlocks : [],
    };
  }

  function getStoryTemplateRecommendationCommandIds(context = {}) {
    if (!context.hasSelectedScene) {
      return [];
    }

    const storyTemplateTools = getStoryTemplateTools(context);
    if (typeof storyTemplateTools?.getStoryTemplateRecommendedPanelItems !== "function") {
      return [];
    }

    const panelItems = storyTemplateTools.getStoryTemplateRecommendedPanelItems(
      getStoryTemplateSceneForRecommendations(context),
      { limit: context.storyTemplateRecommendationLimit ?? 4 }
    );

    return panelItems
      .filter((item) => item?.isRecommended)
      .map((item) => TEMPLATE_COMMAND_ID_BY_TEMPLATE_ID.get(item.templateId))
      .filter(Boolean);
  }

  function getRecommendedCommandIds(context = {}) {
    const hasProject = Boolean(context.hasProject);
    const hasSelectedScene = Boolean(context.hasSelectedScene);
    const blockCount = Number(context.selectedSceneBlockCount ?? 0);
    const selectedBlockType = normalizeSearchText(context.selectedBlockType);

    if (!hasProject) {
      return ["create-playable-demo", "open-project-center", "open-beginner-tutorial"];
    }

    if (!hasSelectedScene) {
      return ["create-first-chapter", "create-starter-kit", "screen-story", "release-one-click-polish", "open-beginner-tutorial"];
    }

    const templateRecommendationIds = getStoryTemplateRecommendationCommandIds(context);

    if (blockCount <= 0) {
      return mergeRecommendedCommandIds(
        templateRecommendationIds,
        ["template-playable-scene", "template-opening-intro", "insert-background", "insert-music-play", "insert-character-show"]
      );
    }

    if (selectedBlockType === "background") {
      return mergeRecommendedCommandIds(
        ["insert-character-show", "insert-music-play"],
        templateRecommendationIds,
        ["insert-narration", "insert-dialogue"]
      );
    }
    if (selectedBlockType === "music_play") {
      return mergeRecommendedCommandIds(
        ["insert-character-show", "insert-narration"],
        templateRecommendationIds,
        ["insert-dialogue", "insert-choice"]
      );
    }
    if (selectedBlockType === "character_show") {
      return mergeRecommendedCommandIds(
        ["insert-dialogue", "insert-camera-zoom"],
        templateRecommendationIds,
        ["template-emotion-burst", "mood-recipe-warm-confession", "insert-choice"]
      );
    }
    if (selectedBlockType === "dialogue") {
      return mergeRecommendedCommandIds(
        ["insert-dialogue", "insert-choice"],
        templateRecommendationIds,
        ["template-emotion-burst", "mood-recipe-climax-pulse", "mood-recipe-warm-confession", "insert-narration"]
      );
    }
    if (selectedBlockType === "narration") {
      return mergeRecommendedCommandIds(
        ["insert-dialogue", "insert-background", "insert-fade"],
        templateRecommendationIds,
        ["template-memory-entry", "mood-recipe-rain-memory"]
      );
    }
    if (selectedBlockType === "choice") {
      return mergeRecommendedCommandIds(
        ["insert-jump", "insert-condition"],
        templateRecommendationIds,
        ["insert-dialogue", "template-branch-choice"]
      );
    }
    if (selectedBlockType === "condition") {
      return mergeRecommendedCommandIds(
        ["insert-dialogue", "insert-jump"],
        templateRecommendationIds,
        ["insert-variable-set", "screen-preview"]
      );
    }
    if (selectedBlockType === "video_play" || selectedBlockType === "credits_roll" || selectedBlockType === "wait") {
      return mergeRecommendedCommandIds(
        ["insert-narration", "insert-music-stop"],
        templateRecommendationIds,
        ["screen-preview", "export-web"]
      );
    }
    if (selectedBlockType === "screen_fade" || selectedBlockType === "screen_filter" || selectedBlockType === "depth_blur") {
      return mergeRecommendedCommandIds(
        ["insert-narration", "insert-dialogue"],
        templateRecommendationIds,
        ["mood-recipe-quiet-ending", "insert-character-show", "insert-fade"]
      );
    }
    if (selectedBlockType === "music_stop" || selectedBlockType === "character_hide" || selectedBlockType === "jump") {
      return mergeRecommendedCommandIds(
        templateRecommendationIds,
        ["template-scene-outro", "screen-preview", "insert-narration", "insert-dialogue"]
      );
    }

    return mergeRecommendedCommandIds(
      ["insert-dialogue", "insert-narration"],
      templateRecommendationIds,
      ["insert-choice", "screen-preview", "release-one-click-polish"]
    );
  }

  function buildReleaseWorkflowCommands(context = {}) {
    const hasProject = Boolean(context.hasProject);
    const hasPolishReceipt = Boolean(context.hasOneClickPolishReceipt);
    const oneClickPolishDigest = context.oneClickPolishDigest ?? null;
    const polishCanApply = oneClickPolishDigest ? Boolean(oneClickPolishDigest.canApply) : hasProject;
    const disabledProjectTitle = "先新建或打开项目后可用";

    return RELEASE_WORKFLOW_COMMANDS.map((command) => {
      const requiresPolishReceipt = Boolean(command.requiresPolishReceipt);
      const disabled =
        !hasProject ||
        (command.id === "release-one-click-polish" && !polishCanApply) ||
        (command.id === "release-one-click-polish" && Boolean(context.projectOneClickPolishInFlight)) ||
        (requiresPolishReceipt && !hasPolishReceipt);
      const disabledReason = !hasProject
        ? disabledProjectTitle
        : command.id === "release-one-click-polish" && context.projectOneClickPolishInFlight
          ? "发布前整理正在进行中"
          : command.id === "release-one-click-polish" && !polishCanApply
            ? "当前项目基础内容已经整理过，可直接巡检或试玩"
            : requiresPolishReceipt && !hasPolishReceipt
              ? "先执行一次一键发布前整理后才有回执"
              : "";
      return {
        ...command,
        section: "发布收尾",
        title:
          command.id === "release-one-click-polish" && oneClickPolishDigest?.actionLabel
            ? oneClickPolishDigest.actionLabel
            : command.title,
        subtitle:
          command.id === "release-one-click-polish" && oneClickPolishDigest?.helperText
            ? oneClickPolishDigest.helperText
            : command.subtitle,
        disabled,
        disabledReason,
      };
    });
  }

  function buildProjectSafetyCommands(context = {}) {
    const hasProject = Boolean(context.hasProject);
    const canUndo = Boolean(context.projectHistoryCanUndo);
    const canRedo = Boolean(context.projectHistoryCanRedo);
    const disabledProjectTitle = "先新建或打开项目后可用";

    return PROJECT_SAFETY_COMMANDS.map((command) => {
      const disabled =
        !hasProject ||
        (Boolean(command.requiresUndo) && !canUndo) ||
        (Boolean(command.requiresRedo) && !canRedo);
      const disabledReason = !hasProject
        ? disabledProjectTitle
        : Boolean(command.requiresUndo) && !canUndo
          ? "现在没有更早的项目版本可以恢复"
          : Boolean(command.requiresRedo) && !canRedo
            ? "现在没有可重做的项目版本"
            : "";
      return {
        ...command,
        section: "安全网",
        disabled,
        disabledReason,
      };
    });
  }

  function getSceneMoodRecipeCommandSource(context = {}) {
    const source = Array.isArray(context.sceneMoodRecipeSuggestions) && context.sceneMoodRecipeSuggestions.length
      ? context.sceneMoodRecipeSuggestions
      : Array.isArray(sceneMoodRecipeTools.SCENE_MOOD_RECIPES)
        ? sceneMoodRecipeTools.SCENE_MOOD_RECIPES
        : [];

    return source
      .map((recipe) => ({
        id: String(recipe?.id ?? "").trim(),
        title: String(recipe?.title ?? "").trim(),
        subtitle: String(recipe?.subtitle ?? "").trim(),
        tags: Array.isArray(recipe?.tags) ? recipe.tags.map((tag) => String(tag ?? "").trim()).filter(Boolean) : [],
      }))
      .filter((recipe) => recipe.id && recipe.title);
  }

  function buildSceneMoodRecipeCommands(context = {}) {
    const hasProject = Boolean(context.hasProject);
    const hasSelectedScene = Boolean(context.hasSelectedScene);
    const hasExplicitReadiness = Object.prototype.hasOwnProperty.call(context, "sceneMoodCanApply");
    const sceneMoodCanApply = hasExplicitReadiness
      ? Boolean(context.sceneMoodCanApply)
      : hasSelectedScene && Number(context.selectedSceneBlockCount ?? 0) > 0;
    const disabledProjectTitle = "先新建或打开项目后可用";
    const disabledSceneTitle = hasProject ? "先创建或选择一个场景后可用" : disabledProjectTitle;
    const disabledReason = !hasSelectedScene
      ? disabledSceneTitle
      : !sceneMoodCanApply
        ? context.sceneMoodEmptyReason || "先写一两句正文或补背景，再套演出配方会更自然"
        : "";
    const sceneSubtitle = context.selectedSceneTitle
      ? `套到当前场景：${context.selectedSceneTitle}`
      : "套到当前选中的场景";

    return getSceneMoodRecipeCommandSource(context).map((recipe) => ({
      id: `mood-recipe-${recipe.id}`,
      title: `套用演出配方：${recipe.title}`,
      subtitle: sceneMoodCanApply ? `${recipe.subtitle} · ${sceneSubtitle}` : disabledReason,
      section: "演出配方",
      action: "apply-scene-mood-recipe",
      dataset: { "recipe-id": recipe.id },
      disabled: !hasSelectedScene || !sceneMoodCanApply,
      disabledReason,
      keywords: ["演出", "配方", "氛围", "mood", "recipe", recipe.title, recipe.subtitle, ...recipe.tags],
    }));
  }

  function prioritizeRecommendedCommands(commands = [], context = {}) {
    const recommendedIds = getRecommendedCommandIds(context);
    if (!recommendedIds.length || !commands.length) {
      return commands;
    }

    const commandById = new Map(commands.map((command) => [command.id, command]));
    const recommendedCommands = recommendedIds
      .map((id) => commandById.get(id))
      .filter((command) => command && !command.disabled)
      .map((command) => ({
        ...command,
        originalSection: command.originalSection ?? command.section,
        section: "推荐",
        recommended: true,
      }));
    if (!recommendedCommands.length) {
      return commands;
    }

    const recommendedIdSet = new Set(recommendedCommands.map((command) => command.id));
    return [
      ...recommendedCommands,
      ...commands.filter((command) => !recommendedIdSet.has(command.id)),
    ];
  }

  function prioritizeRecentCommands(commands = [], context = {}) {
    const availableIds = commands.map((command) => command.id);
    const recentIds = sanitizeCommandPaletteRecentIds(context.recentCommandIds, {
      availableIds,
      limit: context.recentLimit ?? COMMAND_PALETTE_RECENT_LIMIT,
    });
    if (!recentIds.length || !commands.length) {
      return commands;
    }

    const commandById = new Map(commands.map((command) => [command.id, command]));
    const recommendedIds = new Set(commands.filter((command) => command.recommended).map((command) => command.id));
    const recentCommands = recentIds
      .map((id) => commandById.get(id))
      .filter((command) => command && !command.disabled && !recommendedIds.has(command.id))
      .map((command) => ({
        ...command,
        originalSection: command.originalSection ?? command.section,
        section: "最近",
        recent: true,
      }));
    if (!recentCommands.length) {
      return commands;
    }

    const recentIdSet = new Set(recentCommands.map((command) => command.id));
    const recommendedCommands = commands.filter((command) => command.recommended);
    const remainingCommands = commands.filter((command) => !command.recommended && !recentIdSet.has(command.id));
    return [
      ...recommendedCommands,
      ...recentCommands,
      ...remainingCommands,
    ];
  }

  function prioritizeCommandPaletteCommands(commands = [], context = {}) {
    return prioritizeRecentCommands(prioritizeRecommendedCommands(commands, context), context);
  }

  function buildCommandPaletteCommands(context = {}) {
    const hasProject = Boolean(context.hasProject);
    const hasSelectedScene = Boolean(context.hasSelectedScene);
    const hasStructure = Number(context.chapterCount ?? 0) > 0 && Number(context.sceneCount ?? 0) > 0;
    const needsStarterKit = Boolean(context.needsStarterKit);
    const hasValidationErrors = Number(context.errorCount ?? 0) > 0;
    const canExport = hasProject && !hasValidationErrors;
    const disabledProjectTitle = "先新建或打开项目后可用";
    const disabledSceneTitle = hasProject ? "先创建或选择一个场景后可用" : disabledProjectTitle;
    const sceneSubtitle = context.selectedSceneTitle
      ? `插入到当前场景：${context.selectedSceneTitle}`
      : "插入到当前选中的场景";
    const commands = [
      {
        id: "open-project-center",
        title: "打开项目中心",
        subtitle: hasProject ? "切换、复制或新建作品" : "从 Demo 或空白项目开始",
        section: "项目",
        action: "open-project-center",
        keywords: ["项目", "打开", "新建"],
      },
      {
        id: "create-playable-demo",
        title: "新建可试玩 Demo",
        subtitle: "先拿一条完整链路跑起来",
        section: "项目",
        action: "create-playable-demo-project",
        disabled: hasProject,
        disabledReason: hasProject ? "当前已有打开项目，回到项目中心后再创建 Demo" : "",
        keywords: ["demo", "新手", "示例"],
      },
      {
        id: "open-beginner-tutorial",
        title: "打开新手教程",
        subtitle: "按第一次开工顺序完成作品",
        section: "学习",
        action: "open-beginner-tutorial",
        keywords: ["教程", "帮助", "新手"],
      },
      {
        id: "mode-beginner",
        title: "切到新手模式",
        subtitle: "收起高阶入口，先完成可试玩闭环",
        section: "模式",
        action: "set-editor-mode",
        dataset: { "editor-mode": "beginner" },
        keywords: ["beginner", "新手"],
      },
      {
        id: "mode-advanced",
        title: "切到高级模式",
        subtitle: "显示变量、分支、演出和高级整理入口",
        section: "模式",
        action: "set-editor-mode",
        dataset: { "editor-mode": "advanced" },
        keywords: ["advanced", "高级"],
      },
      {
        id: "theme-auto",
        title: "界面外观：自动",
        subtitle: "按时间在浅色和深色之间切换",
        section: "外观",
        action: "set-ui-theme-mode",
        dataset: { "ui-theme-mode": "auto" },
        keywords: ["外观", "主题", "auto"],
      },
      {
        id: "theme-dark",
        title: "界面外观：深色",
        subtitle: "适合夜间写作和沉浸式编辑",
        section: "外观",
        action: "set-ui-theme-mode",
        dataset: { "ui-theme-mode": "dark" },
        keywords: ["外观", "主题", "dark"],
      },
      {
        id: "theme-light",
        title: "界面外观：浅色",
        subtitle: "适合白天整理素材和阅读台本",
        section: "外观",
        action: "set-ui-theme-mode",
        dataset: { "ui-theme-mode": "light" },
        keywords: ["外观", "主题", "light"],
      },
      ...SCREEN_COMMANDS.map((command) => ({
        ...command,
        subtitle: hasProject ? `跳到${command.title}` : disabledProjectTitle,
        action: "switch-screen",
        dataset: { screen: command.screen },
        disabled: !hasProject,
        disabledReason: hasProject ? "" : disabledProjectTitle,
      })),
      ...buildStoryBlockCommands(context).map((command) => ({
        ...command,
        subtitle: hasSelectedScene ? `${command.subtitle} · ${sceneSubtitle}` : disabledSceneTitle,
        disabled: !hasSelectedScene,
        disabledReason: hasSelectedScene ? "" : disabledSceneTitle,
      })),
      ...STORY_TEMPLATE_COMMANDS.map((command) => ({
        ...command,
        section: "模板",
        action: "apply-story-template",
        dataset: { "template-id": command.templateId },
        subtitle: hasSelectedScene ? `${command.subtitle} · ${sceneSubtitle}` : disabledSceneTitle,
        disabled: !hasSelectedScene,
        disabledReason: hasSelectedScene ? "" : disabledSceneTitle,
      })),
      ...buildSceneMoodRecipeCommands(context),
      {
        id: "create-first-chapter",
        title: "一键创建第一章和第一场景",
        subtitle: hasStructure ? "项目已经有基础结构" : "空白项目最快开工入口",
        section: "开工",
        action: "create-first-chapter",
        disabled: !hasProject || hasStructure,
        disabledReason: !hasProject ? disabledProjectTitle : hasStructure ? "当前项目已有章节和场景" : "",
        keywords: ["章节", "场景", "空白"],
      },
      {
        id: "create-starter-kit",
        title: "补齐起步骨架",
        subtitle: needsStarterKit ? "生成第一位角色、第一张背景和第一首 BGM" : "角色、背景和 BGM 骨架已经够用",
        section: "开工",
        action: "create-starter-kit",
        disabled: !hasProject || !needsStarterKit,
        disabledReason: !hasProject ? disabledProjectTitle : !needsStarterKit ? "当前项目暂不需要起步骨架" : "",
        keywords: ["角色", "背景", "bgm", "起步"],
      },
      ...buildProjectSafetyCommands(context),
      ...buildReleaseWorkflowCommands(context),
      {
        id: "export-web",
        title: "导出 Web 试玩包",
        subtitle: canExport ? "生成最容易分享的一版" : hasProject ? "先处理项目巡检错误" : disabledProjectTitle,
        section: "发布",
        action: "export-build",
        dataset: { "export-target": "web" },
        disabled: !canExport,
        disabledReason: !hasProject ? disabledProjectTitle : "项目仍有结构错误，先打开项目巡检",
        keywords: ["导出", "web", "试玩"],
      },
    ];

    return prioritizeCommandPaletteCommands(commands, context);
  }

  function filterCommandPaletteCommands(commands = [], query = "") {
    const normalizedQuery = normalizeSearchText(query);
    if (!normalizedQuery) {
      return commands;
    }
    const terms = normalizedQuery.split(/\s+/).filter(Boolean);
    return commands.filter((command) => {
      const haystack = buildCommandSearchText(command);
      return terms.every((term) => haystack.includes(term));
    });
  }

  function clampCommandPaletteIndex(index, commands = []) {
    if (!commands.length) {
      return 0;
    }
    const numericIndex = Number.parseInt(index ?? 0, 10);
    if (!Number.isFinite(numericIndex)) {
      return 0;
    }
    return Math.max(0, Math.min(commands.length - 1, numericIndex));
  }

  function renderCommandPaletteList(commands = [], selectedIndex = 0, helpers = {}) {
    const escapeHtml = helpers.escapeHtml ?? ((value) => String(value ?? ""));
    if (!commands.length) {
      return `
        <div class="command-palette-empty">
          <strong>没有找到匹配的指令</strong>
          <span>换个关键词试试，比如“剧情”“导出”“素材”。</span>
        </div>
      `;
    }
    return commands
      .map((command, index) => {
        const disabled = Boolean(command.disabled);
        const selectedClass = index === selectedIndex ? " is-selected" : "";
        const disabledClass = disabled ? " is-disabled" : "";
        const recommendedClass = command.recommended ? " is-recommended" : "";
        const recentClass = command.recent ? " is-recent" : "";
        const reason = disabled && command.disabledReason ? ` · ${command.disabledReason}` : "";
        const sectionLabel = (command.recommended || command.recent) && command.originalSection
          ? `${command.section} · ${command.originalSection}`
          : command.section ?? "指令";
        return `
          <button
            type="button"
            class="command-palette-item${selectedClass}${disabledClass}${recommendedClass}${recentClass}"
            data-action="run-command-palette-command"
            data-command-id="${escapeHtml(command.id)}"
            role="option"
            aria-selected="${index === selectedIndex ? "true" : "false"}"
            ${disabled ? 'aria-disabled="true"' : ""}
          >
            <span class="command-palette-section">${escapeHtml(sectionLabel)}</span>
            <strong>${escapeHtml(command.title)}</strong>
            <small>${escapeHtml(`${command.subtitle ?? ""}${reason}`)}</small>
          </button>
        `;
      })
      .join("");
  }

  global.CanvasiaEditorCommandPalette = {
    COMMAND_PALETTE_RECENT_LIMIT,
    STORY_BLOCK_COMMAND_ID_BY_ACTION,
    STORY_BLOCK_COMMAND_KEYWORDS,
    buildCommandPaletteCommands,
    buildStoryBlockCommands,
    getStoryBlockCommandId,
    getStoryBlockCommandEntries,
    filterCommandPaletteCommands,
    clampCommandPaletteIndex,
    renderCommandPaletteList,
    buildReleaseWorkflowCommands,
    buildProjectSafetyCommands,
    buildSceneMoodRecipeCommands,
    getRecommendedCommandIds,
    getStoryTemplateRecommendationCommandIds,
    prioritizeRecommendedCommands,
    prioritizeRecentCommands,
    prioritizeCommandPaletteCommands,
    sanitizeCommandPaletteRecentIds,
    mergeCommandPaletteRecentId,
    getCommandPaletteRecentStorageKey,
    loadStoredCommandPaletteRecentIds,
    persistStoredCommandPaletteRecentIds,
  };
})(window);
