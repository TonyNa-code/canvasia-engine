(function attachStoryTemplateTools(global) {
  const STORY_TEMPLATE_PRESETS = Object.freeze({
    playable_scene: Object.freeze({
      title: "第一段可试玩",
    }),
    opening_intro: Object.freeze({
      title: "开场铺垫",
    }),
    memory_entry: Object.freeze({
      title: "进入回忆",
    }),
    emotion_burst: Object.freeze({
      title: "情绪爆点",
    }),
    branch_choice: Object.freeze({
      title: "选项分支",
    }),
    scene_outro: Object.freeze({
      title: "场景收尾",
    }),
    op_movie_hook: Object.freeze({
      title: "OP 前导",
    }),
    daily_conversation: Object.freeze({
      title: "日常对话节奏",
    }),
    affection_choice: Object.freeze({
      title: "好感度选项",
    }),
    climax_sequence: Object.freeze({
      title: "高潮演出段",
    }),
    ending_credits: Object.freeze({
      title: "ED 与片尾",
    }),
    mystery_clue: Object.freeze({
      title: "悬念线索",
    }),
    relationship_reveal: Object.freeze({
      title: "关系揭露",
    }),
    branch_merge: Object.freeze({
      title: "分支汇合",
    }),
  });

  const STORY_TEMPLATE_BLOCK_RECIPES = deepFreeze({
    playable_scene: [
      {
        type: "background",
        fields: {
          transition: "fade",
        },
      },
      {
        type: "music_play",
        fields: {
          loop: true,
          fadeInMs: 900,
          fadeOutMs: 900,
        },
      },
      {
        type: "character_show",
        speaker: true,
        fields: {
          transition: "fade",
        },
      },
      {
        type: "narration",
        fields: {
          text: "傍晚的空气安静得像在等一个答案。",
        },
      },
      {
        type: "dialogue",
        speaker: true,
        fields: {
          text: "你终于来了。",
        },
      },
      {
        type: "dialogue",
        speaker: true,
        fields: {
          text: "我还以为你不会再回到这里。",
        },
      },
      {
        type: "choice",
        choiceTexts: ["认真回应她", "先转移话题"],
      },
      {
        type: "dialogue",
        speaker: true,
        fields: {
          text: "不管怎样，故事已经从这里开始了。",
        },
      },
      {
        type: "music_stop",
        fields: {
          fadeOutMs: 900,
        },
      },
      {
        type: "screen_fade",
        fields: {
          "action": "fade_out",
          color: "black",
          duration: "medium",
        },
      },
    ],
    opening_intro: [
      {
        type: "background",
        fields: {
          transition: "fade",
        },
      },
      {
        type: "music_play",
        fields: {
          loop: true,
          fadeInMs: 900,
        },
      },
      {
        type: "narration",
        fields: {
          text: "空气轻轻沉下来，故事就在这一刻真正开始。",
        },
      },
      {
        type: "character_show",
        speaker: true,
        fields: {
          transition: "fade",
        },
      },
      {
        type: "dialogue",
        speaker: true,
        fields: {
          text: "今天，会发生什么呢？",
        },
      },
    ],
    memory_entry: [
      {
        type: "screen_fade",
        fields: {
          "action": "fade_out",
          color: "black",
          duration: "medium",
        },
      },
      {
        type: "screen_filter",
        fields: {
          "action": "apply",
          preset: "memory",
          strength: "medium",
        },
      },
      {
        type: "narration",
        fields: {
          text: "记忆像潮水一样慢慢涌了上来。",
        },
      },
      {
        type: "screen_fade",
        fields: {
          "action": "fade_in",
          color: "black",
          duration: "medium",
        },
      },
    ],
    emotion_burst: [
      {
        type: "camera_zoom",
        fields: {
          "action": "zoom_in",
          strength: "medium",
          focus: "center",
        },
      },
      {
        type: "screen_flash",
        fields: {
          color: "white",
          intensity: "medium",
          duration: "short",
        },
      },
      {
        type: "screen_shake",
        fields: {
          intensity: "light",
          duration: "short",
        },
      },
      {
        type: "dialogue",
        speaker: true,
        fields: {
          text: "那句话像被重重敲进心口一样。",
        },
      },
    ],
    branch_choice: [
      {
        type: "dialogue",
        speaker: true,
        fields: {
          text: "接下来，你想怎么做？",
        },
      },
      {
        type: "choice",
        choiceTexts: ["立刻回应她", "先把情绪藏起来"],
      },
    ],
    scene_outro: [
      {
        type: "narration",
        fields: {
          text: "这一段暂时落下帷幕，情绪却还没有真正散去。",
        },
      },
      {
        type: "music_stop",
        fields: {
          fadeOutMs: 900,
        },
      },
      {
        type: "character_hide",
        speaker: true,
        fields: {
          transition: "fade",
        },
      },
      {
        type: "jump",
        defaultJumpTarget: true,
      },
    ],
    op_movie_hook: [
      {
        type: "screen_fade",
        fields: {
          action: "fade_out",
          color: "black",
          duration: "short",
        },
      },
      {
        type: "video_play",
        fields: {
          title: "Opening Movie",
          fit: "contain",
          volume: 100,
          skippable: true,
        },
      },
      {
        type: "screen_fade",
        fields: {
          action: "fade_in",
          color: "black",
          duration: "medium",
        },
      },
      {
        type: "background",
        fields: {
          transition: "fade",
        },
      },
      {
        type: "narration",
        fields: {
          text: "片头的余音散去，新的日常从这一刻接上。",
        },
      },
    ],
    daily_conversation: [
      {
        type: "background",
        fields: {
          transition: "fade",
        },
      },
      {
        type: "music_play",
        endAfterRecipeIndex: 6,
        fields: {
          loop: true,
          volume: 82,
          fadeInMs: 800,
          fadeOutMs: 700,
        },
      },
      {
        type: "character_show",
        speaker: true,
        fields: {
          transition: "rise",
          stage: {
            offsetX: 0,
            offsetY: 4,
            scale: 104,
            opacity: 100,
            layer: 1,
            flipX: false,
          },
        },
      },
      {
        type: "narration",
        fields: {
          text: "她把书包往桌上一放，像是终于松了一口气。",
        },
      },
      {
        type: "dialogue",
        speaker: true,
        fields: {
          text: "今天也辛苦啦。",
        },
      },
      {
        type: "dialogue",
        speaker: true,
        fields: {
          text: "不过，真正麻烦的事情好像才刚刚开始。",
        },
      },
      {
        type: "narration",
        fields: {
          text: "窗外的光线慢慢偏暗，教室里只剩下两个人的呼吸声。",
        },
      },
    ],
    affection_choice: [
      {
        type: "dialogue",
        speaker: true,
        fields: {
          text: "如果是你的话，会怎么回答我？",
        },
      },
      {
        type: "choice",
        choiceOptions: [
          {
            text: "坦率地说出心意",
            gotoSceneId: "__continue__",
            effects: [{ type: "variable_add", value: 2 }],
          },
          {
            text: "先观察她的反应",
            gotoSceneId: "__continue__",
            effects: [{ type: "variable_add", value: 1 }],
          },
        ],
      },
      {
        type: "condition",
        numberVariableCondition: {
          operator: ">=",
          value: 2,
        },
      },
    ],
    climax_sequence: [
      {
        type: "music_play",
        endAfterRecipeIndex: 7,
        fields: {
          loop: true,
          volume: 92,
          fadeInMs: 400,
          fadeOutMs: 900,
        },
      },
      {
        type: "screen_fade",
        fields: {
          action: "fade_in",
          color: "black",
          duration: "short",
        },
      },
      {
        type: "camera_zoom",
        fields: {
          action: "zoom_in",
          strength: "strong",
          focus: "center",
        },
      },
      {
        type: "screen_flash",
        fields: {
          color: "white",
          intensity: "strong",
          duration: "short",
        },
      },
      {
        type: "screen_shake",
        fields: {
          intensity: "medium",
          duration: "short",
        },
      },
      {
        type: "depth_blur",
        fields: {
          action: "apply",
          focus: "center",
          strength: "medium",
        },
      },
      {
        type: "dialogue",
        speaker: true,
        fields: {
          text: "这一刻，我终于明白自己真正想守住的是什么。",
        },
      },
      {
        type: "depth_blur",
        fields: {
          action: "clear",
        },
      },
    ],
    ending_credits: [
      {
        type: "screen_fade",
        fields: {
          action: "fade_out",
          color: "black",
          duration: "medium",
        },
      },
      {
        type: "music_play",
        endAfterRecipeIndex: 3,
        fields: {
          loop: false,
          volume: 88,
          fadeInMs: 1200,
          fadeOutMs: 1200,
        },
      },
      {
        type: "narration",
        fields: {
          text: "故事到这里暂时告一段落，但她留下的声音还在心里回响。",
        },
      },
      {
        type: "credits_roll",
        fields: {
          title: "STAFF",
          subtitle: "Thank you for playing",
          durationSeconds: 22,
          background: "dark",
          skippable: true,
        },
      },
      {
        type: "music_stop",
        fields: {
          fadeOutMs: 1200,
        },
      },
    ],
    mystery_clue: [
      {
        type: "music_play",
        endAfterRecipeIndex: 7,
        fields: {
          loop: true,
          volume: 72,
          fadeInMs: 700,
          fadeOutMs: 900,
        },
      },
      {
        type: "screen_filter",
        fields: {
          action: "apply",
          preset: "cold",
          strength: "soft",
        },
      },
      {
        type: "camera_pan",
        fields: {
          target: "right",
          strength: "light",
        },
      },
      {
        type: "narration",
        fields: {
          text: "那张被折过的纸条，正安静地躺在窗台边。",
        },
      },
      {
        type: "wait",
        fields: {
          durationSeconds: 0.6,
        },
      },
      {
        type: "dialogue",
        speaker: true,
        fields: {
          text: "等等，这不是昨天出现过的字迹吗？",
        },
      },
      {
        type: "choice",
        choiceOptions: [
          {
            text: "把线索收起来",
            gotoSceneId: "__continue__",
            effects: [{ type: "variable_add", value: 1 }],
          },
          {
            text: "暂时装作没看见",
            gotoSceneId: "__continue__",
            effects: [{ type: "variable_add", value: 0 }],
          },
        ],
      },
      {
        type: "screen_filter",
        fields: {
          action: "clear",
        },
      },
    ],
    relationship_reveal: [
      {
        type: "character_show",
        speaker: true,
        fields: {
          transition: "fade",
          position: "center",
          stage: {
            offsetX: 0,
            offsetY: 0,
            scale: 108,
            opacity: 100,
            layer: 2,
            flipX: false,
          },
        },
      },
      {
        type: "camera_zoom",
        fields: {
          action: "zoom_in",
          strength: "medium",
          focus: "center",
        },
      },
      {
        type: "dialogue",
        speaker: true,
        fields: {
          text: "其实，我一直有件事没有告诉你。",
        },
      },
      {
        type: "screen_shake",
        fields: {
          intensity: "light",
          duration: "short",
        },
      },
      {
        type: "dialogue",
        speaker: true,
        fields: {
          text: "那天救下我的人，就是你吧？",
        },
      },
      {
        type: "choice",
        choiceOptions: [
          {
            text: "承认并说出真相",
            gotoSceneId: "__continue__",
            effects: [{ type: "variable_add", value: 2 }],
          },
          {
            text: "先问她为什么知道",
            gotoSceneId: "__continue__",
            effects: [{ type: "variable_add", value: 1 }],
          },
        ],
      },
      {
        type: "condition",
        numberVariableCondition: {
          operator: ">=",
          value: 2,
        },
      },
      {
        type: "narration",
        fields: {
          text: "两个人之间那条看不见的线，终于被轻轻拉紧了。",
        },
      },
    ],
    branch_merge: [
      {
        type: "choice",
        choiceOptions: [
          {
            text: "沿着熟悉的路回去",
            gotoSceneId: "__continue__",
            effects: [{ type: "variable_add", value: 1 }],
          },
          {
            text: "绕到旧教学楼后面",
            gotoSceneId: "__continue__",
            effects: [{ type: "variable_add", value: 1 }],
          },
        ],
      },
      {
        type: "narration",
        fields: {
          text: "无论选择哪条路，最后都通向同一个被月光照亮的操场。",
        },
      },
      {
        type: "condition",
        numberVariableCondition: {
          operator: ">=",
          value: 1,
        },
      },
      {
        type: "dialogue",
        speaker: true,
        fields: {
          text: "看来，我们还是在这里碰面了。",
        },
      },
      {
        type: "jump",
        defaultJumpTarget: true,
      },
    ],
  });

  const STORY_TEMPLATE_PANEL_ITEMS = deepFreeze([
    {
      templateId: "playable_scene",
      tone: "hero",
      description: "先生成一段能直接试玩的完整小场景",
    },
    {
      templateId: "opening_intro",
      tone: "good",
      description: "背景、BGM、角色亮相和第一轮对白",
    },
    {
      templateId: "memory_entry",
      tone: "",
      description: "黑场转入、回忆滤镜和回忆旁白",
    },
    {
      templateId: "emotion_burst",
      tone: "warn",
      description: "镜头推近、闪屏、震动和冲击台词",
    },
    {
      templateId: "branch_choice",
      tone: "",
      description: "一句提问加一组选项，适合做分线入口",
    },
    {
      templateId: "scene_outro",
      tone: "",
      description: "收尾旁白、停音乐、退场和跳下一场",
    },
    {
      templateId: "op_movie_hook",
      tone: "hero",
      description: "OP 视频、黑场过渡和正式开场衔接",
    },
    {
      templateId: "daily_conversation",
      tone: "good",
      description: "带 BGM 范围、立绘登场和日常对话节奏",
    },
    {
      templateId: "affection_choice",
      tone: "warn",
      description: "带好感度变化和条件判断的选项段落",
    },
    {
      templateId: "climax_sequence",
      tone: "warn",
      description: "音乐、镜头、闪屏、震动和景深组合演出",
    },
    {
      templateId: "ending_credits",
      tone: "",
      description: "ED 黑场、收束旁白、片尾字幕和停音乐",
    },
    {
      templateId: "mystery_clue",
      tone: "good",
      description: "冷色滤镜、镜头移动、线索发现和变量记录",
    },
    {
      templateId: "relationship_reveal",
      tone: "warn",
      description: "角色居中、镜头推进、关系真相和条件分支",
    },
    {
      templateId: "branch_merge",
      tone: "",
      description: "两组选项回到同一汇合点，适合收束分线",
    },
  ]);

  const PROJECT_TEMPLATE_LABELS = Object.freeze({
    blank: "空白项目",
    campus_romance: "校园恋爱模板",
  });

  function deepFreeze(source) {
    if (!source || typeof source !== "object" || Object.isFrozen(source)) {
      return source;
    }

    Object.freeze(source);
    Object.values(source).forEach((value) => deepFreeze(value));
    return source;
  }

  function toArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function getStoryTemplatePreset(templateId) {
    return STORY_TEMPLATE_PRESETS[templateId] ?? null;
  }

  function getStoryTemplateBlockRecipes(templateId) {
    return STORY_TEMPLATE_BLOCK_RECIPES[templateId] ?? [];
  }

  function getStoryTemplateBlockTypeCounts(templateId) {
    return getStoryTemplateBlockRecipes(templateId).reduce((counts, recipe) => {
      if (recipe?.type) {
        counts[recipe.type] = (counts[recipe.type] ?? 0) + 1;
      }
      return counts;
    }, {});
  }

  function getStoryTemplateSummary(templateId, options = {}) {
    const recipes = getStoryTemplateBlockRecipes(templateId);
    const getBlockLabel =
      typeof options.getBlockLabel === "function" ? options.getBlockLabel : (type) => type;
    const orderedTypes = [];
    const counts = {};

    recipes.forEach((recipe) => {
      if (!recipe?.type) {
        return;
      }
      if (!orderedTypes.includes(recipe.type)) {
        orderedTypes.push(recipe.type);
      }
      counts[recipe.type] = (counts[recipe.type] ?? 0) + 1;
    });

    const labels = orderedTypes.map((type) => {
      const count = counts[type] ?? 0;
      const label = getBlockLabel(type);
      return count > 1 ? `${label} x ${count}` : label;
    });

    return Object.freeze({
      templateId,
      title: getStoryTemplatePreset(templateId)?.title ?? templateId,
      blockCount: recipes.length,
      labels: Object.freeze(labels),
      typeCounts: Object.freeze({ ...counts }),
    });
  }

  function getStoryTemplateVariableRequirement(templateId) {
    return getStoryTemplateBlockRecipes(templateId).reduce(
      (requirement, recipe) => {
        if (!recipe?.type) {
          return requirement;
        }
        if (recipe.type === "variable_set" || recipe.type === "condition") {
          requirement.requiresAny = true;
        }
        if (recipe.type === "variable_add" || recipe.numberVariableCondition) {
          requirement.requiresAny = true;
          requirement.requiresNumber = true;
        }
        toArray(recipe.choiceOptions).forEach((option) => {
          toArray(option?.effects).forEach((effect) => {
            if (effect?.type === "variable_add") {
              requirement.requiresAny = true;
              requirement.requiresNumber = true;
            } else if (effect?.type === "variable_set") {
              requirement.requiresAny = true;
            }
          });
        });
        return requirement;
      },
      { requiresAny: false, requiresNumber: false }
    );
  }

  function getStoryTemplatePanelItems() {
    return STORY_TEMPLATE_PANEL_ITEMS;
  }

  function uniqueValues(values) {
    return Array.from(new Set(toArray(values).filter(Boolean)));
  }

  function getStoryTemplateRegistryHealth() {
    const presetIds = Object.keys(STORY_TEMPLATE_PRESETS);
    const recipeIds = Object.keys(STORY_TEMPLATE_BLOCK_RECIPES);
    const panelIds = STORY_TEMPLATE_PANEL_ITEMS.map((item) => item?.templateId).filter(Boolean);
    const allKnownIds = uniqueValues([...presetIds, ...recipeIds, ...panelIds]);
    const duplicatePanelIds = uniqueValues(panelIds.filter((id, index) => panelIds.indexOf(id) !== index));
    const missingPresetIds = allKnownIds.filter((id) => !STORY_TEMPLATE_PRESETS[id]);
    const missingRecipeIds = allKnownIds.filter((id) => !Array.isArray(STORY_TEMPLATE_BLOCK_RECIPES[id]));
    const emptyRecipeIds = recipeIds.filter((id) => !getStoryTemplateBlockRecipes(id).length);
    const issues = [
      ...duplicatePanelIds.map((id) => `duplicate_panel:${id}`),
      ...missingPresetIds.map((id) => `missing_preset:${id}`),
      ...missingRecipeIds.map((id) => `missing_recipe:${id}`),
      ...emptyRecipeIds.map((id) => `empty_recipe:${id}`),
    ];

    return Object.freeze({
      isHealthy: issues.length === 0,
      issueCount: issues.length,
      presetIds: Object.freeze([...presetIds]),
      recipeIds: Object.freeze([...recipeIds]),
      panelIds: Object.freeze([...panelIds]),
      duplicatePanelIds: Object.freeze(duplicatePanelIds),
      missingPresetIds: Object.freeze(missingPresetIds),
      missingRecipeIds: Object.freeze(missingRecipeIds),
      emptyRecipeIds: Object.freeze(emptyRecipeIds),
      issues: Object.freeze(issues),
    });
  }

  function getTemplateLabel(template) {
    return PROJECT_TEMPLATE_LABELS[template] ?? template;
  }

  global.CanvasiaEditorStoryTemplates = Object.freeze({
    STORY_TEMPLATE_PRESETS,
    STORY_TEMPLATE_BLOCK_RECIPES,
    STORY_TEMPLATE_PANEL_ITEMS,
    PROJECT_TEMPLATE_LABELS,
    getStoryTemplatePreset,
    getStoryTemplateBlockRecipes,
    getStoryTemplateBlockTypeCounts,
    getStoryTemplateSummary,
    getStoryTemplateVariableRequirement,
    getStoryTemplatePanelItems,
    getStoryTemplateRegistryHealth,
    getTemplateLabel,
  });
})(typeof window !== "undefined" ? window : globalThis);
