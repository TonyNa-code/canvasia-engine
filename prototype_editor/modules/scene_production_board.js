(function attachSceneProductionBoardTools(global) {
  const storyBlockCatalogTools = global.CanvasiaEditorStoryBlockCatalog || {};
  const scenePacingAdvisorTools = global.CanvasiaEditorScenePacingAdvisor || {};
  const scriptReadabilityTools = global.CanvasiaEditorScriptReadability || {};
  const storyTemplateTools = global.CanvasiaEditorStoryTemplates || {};

  const EFFECT_BLOCK_TYPES = Object.freeze(
    typeof storyBlockCatalogTools.getEffectBlockTypes === "function"
      ? storyBlockCatalogTools.getEffectBlockTypes()
      : [
          "particle_effect",
          "wait",
          "screen_shake",
          "screen_flash",
          "screen_fade",
          "camera_zoom",
          "camera_pan",
          "screen_filter",
          "depth_blur",
        ]
  );

  const STORY_BLOCK_TYPES = Object.freeze(
    typeof storyBlockCatalogTools.getTimelineTextBlockTypes === "function"
      ? [...storyBlockCatalogTools.getTimelineTextBlockTypes(), "condition"]
      : ["dialogue", "narration", "choice", "condition"]
  );

  const FALLBACK_BLOCK_LABELS = Object.freeze({
    background: "切换背景",
    dialogue: "台词",
    narration: "旁白",
    character_show: "显示角色",
    character_move: "角色动作",
    character_hide: "隐藏角色",
    music_play: "播放音乐",
    music_stop: "停止音乐",
    sfx_play: "播放音效",
    video_play: "播放视频",
    credits_roll: "片尾字幕",
    wait: "等待停顿",
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

  const BLOCK_LABELS = Object.freeze({
    ...FALLBACK_BLOCK_LABELS,
    ...(storyBlockCatalogTools.BLOCK_LABELS ?? {}),
  });

  const TEXT_LONG_WARNING_LENGTH = 260;
  const TEXT_LONG_WARNING_LINES = 5;
  const CHOICE_LONG_WARNING_LENGTH = 42;
  const CHOICE_MANY_OPTIONS = 6;
  const CHOICE_CONTINUE_TARGET = "__continue__";

  const SCENE_RECIPE_SUGGESTIONS = Object.freeze({
    playable_scene: Object.freeze({
      templateId: "playable_scene",
      title: "先生成可试玩骨架",
      actionLabel: "插入可试玩段落",
      detail: "这个场景还没站起来，先用可试玩段落把背景、角色、台词、选项和收尾串成一段。",
      priority: 95,
    }),
    daily_conversation: Object.freeze({
      templateId: "daily_conversation",
      title: "补日常对话节奏",
      actionLabel: "插入日常节奏",
      detail: "这个场景已经有内容，但基础画面或 BGM 氛围不够完整，适合补一组日常对话节奏。",
      priority: 72,
    }),
    opening_intro: Object.freeze({
      templateId: "opening_intro",
      title: "补开场铺垫",
      actionLabel: "插入开场铺垫",
      detail: "先建立地点、音乐、旁白和第一句对白，让场景入口更清楚。",
      priority: 70,
    }),
    branch_choice: Object.freeze({
      templateId: "branch_choice",
      title: "补一个选择入口",
      actionLabel: "插入选项分支",
      detail: "当前段落已经有对白，可以补一个玩家选择点，让剧情从阅读进入互动。",
      priority: 66,
    }),
    affection_choice: Object.freeze({
      templateId: "affection_choice",
      title: "加一个有后果的选项",
      actionLabel: "插入好感选项",
      detail: "正文已经能读了，可以加一组带变量后果的选项，让玩家感觉选择真的有意义。",
      priority: 64,
    }),
    emotion_burst: Object.freeze({
      templateId: "emotion_burst",
      title: "补情绪爆点",
      actionLabel: "插入情绪爆点",
      detail: "角色和对白已经就位，可以用镜头、震动和闪屏把关键句顶起来。",
      priority: 62,
    }),
    climax_sequence: Object.freeze({
      templateId: "climax_sequence",
      title: "补高潮演出段",
      actionLabel: "插入高潮演出",
      detail: "这个场景演出变化偏少，适合用镜头、闪屏、震动和景深把关键句抬起来。",
      priority: 58,
    }),
    memory_entry: Object.freeze({
      templateId: "memory_entry",
      title: "转入回忆段落",
      actionLabel: "插入回忆入口",
      detail: "旁白较多时可以补黑场、回忆滤镜和回忆对白，让段落更有画面层次。",
      priority: 56,
    }),
    scene_outro: Object.freeze({
      templateId: "scene_outro",
      title: "补场景收尾",
      actionLabel: "插入场景收尾",
      detail: "这段已经比较完整，接下来可以补一个收束和转场，让试玩段落更像正式作品。",
      priority: 42,
    }),
    ending_credits: Object.freeze({
      templateId: "ending_credits",
      title: "补 ED 与片尾",
      actionLabel: "插入片尾字幕",
      detail: "视频或结尾段落后可以补收束旁白、片尾字幕和音乐停止，形成完整发布感。",
      priority: 60,
    }),
    op_movie_hook: Object.freeze({
      templateId: "op_movie_hook",
      title: "补 OP 衔接",
      actionLabel: "插入 OP 前导",
      detail: "适合把片头视频、黑场过渡和正式第一幕衔接成更像商业作品的入口。",
      priority: 54,
    }),
    mystery_clue: Object.freeze({
      templateId: "mystery_clue",
      title: "补一个悬念钩子",
      actionLabel: "插入悬念线索",
      detail: "这段已经能读，但还缺一个记忆点；可以补线索、冷色滤镜和变量记录，让玩家有继续点下去的理由。",
      priority: 61,
    }),
    relationship_reveal: Object.freeze({
      templateId: "relationship_reveal",
      title: "补关系揭露段",
      actionLabel: "插入关系揭露",
      detail: "角色互动已经有基础，可以补一段居中立绘、镜头推进和关系真相，让场景有更明确的情绪锚点。",
      priority: 59,
    }),
    branch_merge: Object.freeze({
      templateId: "branch_merge",
      title: "补分支回收点",
      actionLabel: "插入分支汇合",
      detail: "选项已经记录了变量，但还缺兑现选择的条件或汇合点；先补一个分支回收骨架，避免选择像摆设。",
      priority: 68,
    }),
  });

  function toArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function cleanText(value, fallback = "") {
    const text = String(value ?? "").replace(/\s+/g, " ").trim();
    return text || fallback;
  }

  function isChoiceContinueTarget(value) {
    return cleanText(value) === CHOICE_CONTINUE_TARGET;
  }

  function clamp(value, min, max) {
    return Math.min(Math.max(Number(value) || 0, min), max);
  }

  function getProgressPercent(done, total) {
    if (!total || total <= 0) {
      return 100;
    }
    return clamp(Math.round((done / total) * 100), 0, 100);
  }

  function buildCollectionMap(source, idField = "id") {
    const result = new Map();
    if (source instanceof Map) {
      source.forEach((value, id) => {
        if (id) {
          result.set(String(id), value);
        }
      });
      return result;
    }
    if (source && typeof source === "object" && !Array.isArray(source)) {
      Object.entries(source).forEach(([id, value]) => {
        if (id) {
          result.set(String(id), value);
        }
      });
      return result;
    }
    toArray(source).forEach((item) => {
      if (item?.[idField]) {
        result.set(String(item[idField]), item);
      }
    });
    return result;
  }

  function buildSceneMap(data = {}) {
    const sceneMap = new Map();
    toArray(data.scenes).forEach((scene) => {
      if (scene?.id) {
        sceneMap.set(String(scene.id), scene);
      }
    });
    buildCollectionMap(data.scenesById).forEach((scene, id) => sceneMap.set(id, scene));
    toArray(data.chapters).forEach((chapter) => {
      toArray(chapter.scenes).forEach((scene) => {
        if (scene?.id) {
          sceneMap.set(String(scene.id), scene);
        }
      });
    });
    return sceneMap;
  }

  function buildChapterMap(data = {}) {
    return new Map(
      toArray(data.chapters).map((chapter, index) => [
        String(chapter?.id ?? chapter?.chapterId ?? ""),
        {
          id: String(chapter?.id ?? chapter?.chapterId ?? ""),
          name: cleanText(chapter?.name ?? chapter?.title, `章节 ${index + 1}`),
          order: index,
          sceneOrder: toArray(chapter?.sceneOrder).map((sceneId) => String(sceneId ?? "")).filter(Boolean),
        },
      ])
    );
  }

  function getSceneRecords(data = {}) {
    const sceneMap = buildSceneMap(data);
    const chapterMap = buildChapterMap(data);
    const records = [];
    const seenSceneIds = new Set();

    toArray(data.chapters).forEach((chapter, chapterIndex) => {
      const chapterId = String(chapter?.id ?? chapter?.chapterId ?? "");
      const chapterName = cleanText(chapter?.name ?? chapter?.title, `章节 ${chapterIndex + 1}`);
      const directScenes = toArray(chapter?.scenes);
      const orderedIds = toArray(chapter?.sceneOrder).map((sceneId) => String(sceneId ?? "")).filter(Boolean);
      const scenes = directScenes.length
        ? directScenes
        : orderedIds.map((sceneId) => sceneMap.get(sceneId)).filter(Boolean);

      scenes.forEach((scene, sceneIndex) => {
        if (!scene?.id || seenSceneIds.has(String(scene.id))) {
          return;
        }
        seenSceneIds.add(String(scene.id));
        records.push({ scene, sceneIndex, chapterId, chapterName, chapterOrder: chapterIndex });
      });
    });

    toArray(data.scenes).forEach((scene, sceneIndex) => {
      if (!scene?.id || seenSceneIds.has(String(scene.id))) {
        return;
      }
      const chapter = chapterMap.get(String(scene.chapterId ?? ""));
      seenSceneIds.add(String(scene.id));
      records.push({
        scene,
        sceneIndex,
        chapterId: String(scene.chapterId ?? ""),
        chapterName: chapter?.name ?? "未分章",
        chapterOrder: chapter?.order ?? 9999,
      });
    });

    return records.sort((left, right) => {
      if (left.chapterOrder !== right.chapterOrder) {
        return left.chapterOrder - right.chapterOrder;
      }
      return left.sceneIndex - right.sceneIndex;
    });
  }

  function getBlockLabel(type = "") {
    return BLOCK_LABELS[type] ?? cleanText(type, "卡片");
  }

  function getTextMetrics(text) {
    const safeText = String(text ?? "").trim();
    return {
      length: safeText.length,
      lineCount: safeText ? safeText.split(/\r?\n/).length : 0,
    };
  }

  function isLongTextBlock(block = {}) {
    if (!["dialogue", "narration"].includes(block.type)) {
      return false;
    }
    const metrics = getTextMetrics(block.text);
    return metrics.length > TEXT_LONG_WARNING_LENGTH || metrics.lineCount > TEXT_LONG_WARNING_LINES;
  }

  function isLongChoiceText(text = "") {
    return cleanText(text).length > CHOICE_LONG_WARNING_LENGTH;
  }

  function pushIssue(issues, severity, code, title, detail, context = {}) {
    issues.push({ severity, code, title, detail, ...context });
  }

  function getIssueWeight(issue = {}) {
    if (issue.severity === "blocker") {
      return 100;
    }
    if (issue.severity === "warn") {
      return 60;
    }
    return 20;
  }

  function getSceneStatus(issues = [], completionScore = 0) {
    if (issues.some((issue) => issue.severity === "blocker")) {
      return "blocked";
    }
    if (issues.some((issue) => issue.severity === "warn")) {
      return "warn";
    }
    if (completionScore >= 80) {
      return "ready";
    }
    return "draft";
  }

  function getSceneStatusLabel(status = "draft") {
    if (status === "blocked") {
      return "先修";
    }
    if (status === "warn") {
      return "复查";
    }
    if (status === "ready") {
      return "可试玩";
    }
    return "制作中";
  }

  function getSceneNextAction(report = {}) {
    const issue = toArray(report.issues)[0];
    if (issue) {
      if (issue.code === "scene_bad_route_target") {
        return "先修坏跳转";
      }
      if (issue.code === "scene_missing_background") {
        return "补背景";
      }
      if (issue.code === "scene_missing_music") {
        return "补 BGM";
      }
      if (issue.code === "scene_missing_voice") {
        return "绑语音";
      }
      if (issue.code === "scene_long_text") {
        return "拆长文本";
      }
      if (issue.code === "scene_script_empty_text") {
        return "补空台词";
      }
      if (issue.code === "scene_script_duplicate_text") {
        return "查重复文本";
      }
      if (issue.code === "scene_script_choice_empty_text") {
        return "补选项文字";
      }
      if (issue.code === "scene_flat_presentation") {
        return "补演出";
      }
      return issue.title;
    }
    if (report.status === "ready") {
      return "试玩确认";
    }
    if (!report.hasStoryContent) {
      return "补剧情";
    }
    return "继续打磨";
  }

  function getPacingIssueCodes(report = {}) {
    return new Set(toArray(report.pacingIssueCodes));
  }

  function getSceneScriptQualityReport(scene = {}) {
    if (typeof scriptReadabilityTools.buildScriptQualitySceneReport !== "function") {
      return {
        status: "ready",
        summary: {
          issueCount: 0,
          blockerCount: 0,
          warningCount: 0,
          tipCount: 0,
          emptyTextCount: 0,
          longTextCount: 0,
          duplicateTextCount: 0,
          missingPunctuationCount: 0,
          missingSpeakerCount: 0,
          missingExpressionCount: 0,
          choiceIssueCount: 0,
        },
        issues: [],
      };
    }
    return scriptReadabilityTools.buildScriptQualitySceneReport(scene);
  }

  function pushScriptQualityProductionIssues(issues, scriptQualityReport = {}, baseContext = {}) {
    toArray(scriptQualityReport.issues).forEach((issue) => {
      const context = {
        ...baseContext,
        blockId: issue.blockId,
        blockIndex: issue.blockIndex,
        blockType: issue.blockType,
      };
      if (issue.code === "script_empty_text") {
        pushIssue(issues, "blocker", "scene_script_empty_text", "有空台词 / 空旁白", "空文本会让试玩像卡住或空跳，发布前必须补正文或删卡。", context);
        return;
      }
      if (issue.code === "script_duplicate_nearby_text") {
        pushIssue(issues, "warn", "scene_script_duplicate_text", "附近有重复文本", issue.detail || "可能是误复制的台词或旁白。", context);
        return;
      }
      if (issue.code === "script_choice_empty_text") {
        pushIssue(issues, "warn", "scene_script_choice_empty_text", "有空选项按钮", issue.detail || "选项按钮没有文字，玩家无法理解这个选择。", context);
      }
    });
  }

  function getSceneRecipeSuggestionByTemplateId(templateId, overrides = {}) {
    const safeTemplateId = cleanText(templateId);
    if (!safeTemplateId) {
      return null;
    }

    const base = SCENE_RECIPE_SUGGESTIONS[safeTemplateId];
    const preset =
      typeof storyTemplateTools.getStoryTemplatePreset === "function"
        ? storyTemplateTools.getStoryTemplatePreset(safeTemplateId)
        : null;
    if (!base && !preset) {
      return null;
    }

    return Object.freeze({
      templateId: safeTemplateId,
      title: preset?.title ? `套用：${preset.title}` : safeTemplateId,
      actionLabel: "插入推荐配方",
      detail: "按当前场景状态补一组更完整的剧情卡片。",
      priority: 50,
      ...(base ?? {}),
      ...overrides,
    });
  }

  function getStoryTemplateRecommendationSuggestion(scene = null) {
    if (!scene || typeof storyTemplateTools.getStoryTemplateRecommendationPlan !== "function") {
      return null;
    }

    const plan = storyTemplateTools.getStoryTemplateRecommendationPlan(scene, { limit: 4 });
    return (
      toArray(plan?.recommendations)
        .map((item) => {
          const reason = cleanText(item?.reason);
          return getSceneRecipeSuggestionByTemplateId(item?.templateId, {
            ...(reason ? { detail: reason } : {}),
            priority: Math.max(Number(item?.score) || 0, SCENE_RECIPE_SUGGESTIONS[item?.templateId]?.priority ?? 0),
            source: "story_template_recommendation",
            recommendationRank: item?.rank ?? null,
            recommendationScore: item?.score ?? null,
          });
        })
        .find(Boolean) ?? null
    );
  }

  function getSceneRecipeSuggestion(report = {}, scene = null) {
    const issues = toArray(report.issues);
    const pacingIssueCodes = getPacingIssueCodes(report);
    const hasBlockingRoute = issues.some((issue) => issue.code === "scene_bad_route_target");
    if (hasBlockingRoute) {
      return null;
    }
    const storyTemplateSuggestion = getStoryTemplateRecommendationSuggestion(scene);
    if (!report.hasStoryContent || (report.blockCount ?? 0) === 0) {
      if ((report.blockCount ?? 0) > 0 && storyTemplateSuggestion) {
        return storyTemplateSuggestion;
      }
      return SCENE_RECIPE_SUGGESTIONS.playable_scene;
    }
    if (pacingIssueCodes.has("pacing_branch_without_payoff")) {
      return SCENE_RECIPE_SUGGESTIONS.branch_merge;
    }
    if (pacingIssueCodes.has("pacing_missing_outro")) {
      return SCENE_RECIPE_SUGGESTIONS.scene_outro;
    }
    if (pacingIssueCodes.has("pacing_choice_without_consequence")) {
      return SCENE_RECIPE_SUGGESTIONS.affection_choice;
    }
    if (!report.hasBackground || !report.hasMusic) {
      return SCENE_RECIPE_SUGGESTIONS.daily_conversation;
    }
    if ((report.choiceCount ?? 0) === 0 && ((report.dialogueCount ?? 0) + (report.narrationCount ?? 0)) >= 2) {
      if ((report.hasEffects || (report.pacingScore ?? 0) >= 72) && report.dialogueCount >= 2) {
        return SCENE_RECIPE_SUGGESTIONS.relationship_reveal;
      }
      return SCENE_RECIPE_SUGGESTIONS.mystery_clue;
    }
    if (!report.hasEffects) {
      return SCENE_RECIPE_SUGGESTIONS.climax_sequence;
    }
    if (report.status === "ready" && (report.choiceCount ?? 0) > 0) {
      return SCENE_RECIPE_SUGGESTIONS.scene_outro;
    }
    return storyTemplateSuggestion;
  }

  function getRouteTargetIssues(scene, blocks = [], sceneMap = new Map(), baseContext = {}) {
    const issues = [];
    function inspectTarget(targetSceneId, context) {
      const cleanTarget = cleanText(targetSceneId);
      if (isChoiceContinueTarget(cleanTarget)) {
        return;
      }
      if (!cleanTarget || !sceneMap.has(cleanTarget)) {
        pushIssue(
          issues,
          "blocker",
          "scene_bad_route_target",
          cleanTarget ? "跳转目标不存在" : "跳转目标未设置",
          cleanTarget ? `目标场景 ${cleanTarget} 不在项目场景列表中。` : "这个分支还没有选择要去的场景。",
          {
            ...baseContext,
            ...context,
            targetSceneId: cleanTarget,
          }
        );
      }
    }

    blocks.forEach((block, blockIndex) => {
      const blockContext = {
        blockId: block?.id,
        blockIndex,
        blockLabel: getBlockLabel(block?.type),
      };
      if (block?.type === "jump") {
        inspectTarget(block.targetSceneId, blockContext);
      }
      if (block?.type === "choice") {
        const options = toArray(block.options);
        if (!options.length) {
          pushIssue(issues, "warn", "scene_empty_choice", "选项卡没有选项", "玩家会看到一个没有可点选项的选择段。", {
            ...baseContext,
            ...blockContext,
          });
        }
        options.forEach((option, optionIndex) => {
          inspectTarget(option.gotoSceneId, {
            ...blockContext,
            optionIndex,
            optionText: cleanText(option.text, `选项 ${optionIndex + 1}`),
          });
        });
      }
      if (block?.type === "condition") {
        toArray(block.branches).forEach((branch, branchIndex) => {
          inspectTarget(branch.gotoSceneId, {
            ...blockContext,
            branchIndex,
            branchLabel: `条件分支 ${branchIndex + 1}`,
          });
        });
        inspectTarget(block.elseGotoSceneId, {
          ...blockContext,
          branchIndex: -1,
          branchLabel: "否则分支",
        });
      }
    });

    return issues;
  }

  function scoreSceneProduction(metrics = {}, issueCounts = {}) {
    const routeOk = issueCounts.blockerCount === 0;
    let score = 0;
    if (metrics.blockCount > 0) {
      score += 8;
    }
    if (metrics.hasStoryContent) {
      score += 22;
    }
    if (!metrics.hasStoryContent || metrics.hasBackground) {
      score += 14;
    }
    if (!metrics.hasStoryContent || metrics.hasMusic) {
      score += 10;
    }
    if (!metrics.hasStoryContent || metrics.hasEffects) {
      score += 10;
    }
    score += metrics.dialogueCount > 0 ? Math.round(metrics.voiceProgress * 0.18) : 18;
    score += routeOk ? 14 : 0;
    score += Math.max(0, 14 - issueCounts.warningCount * 3 - issueCounts.tipCount);
    return clamp(score - issueCounts.blockerCount * 18, 0, 100);
  }

  function analyzeScene(record = {}, data = {}, sceneMap = new Map()) {
    const scene = record.scene ?? {};
    const blocks = toArray(scene.blocks);
    const chapterName = record.chapterName ?? "未分章";
    const sceneName = cleanText(scene.name ?? scene.title, scene.id ?? "未命名场景");
    const baseContext = {
      sceneId: scene.id,
      sceneName,
      chapterId: record.chapterId,
      chapterName,
    };
    const dialogueBlocks = blocks.filter((block) => block.type === "dialogue");
    const narrationBlocks = blocks.filter((block) => block.type === "narration");
    const choiceBlocks = blocks.filter((block) => block.type === "choice");
    const conditionBlocks = blocks.filter((block) => block.type === "condition");
    const hasStoryContent = blocks.some((block) => STORY_BLOCK_TYPES.includes(block.type));
    const hasBackground = blocks.some((block) => block.type === "background" && block.assetId);
    const hasMusic = blocks.some((block) => block.type === "music_play" && block.assetId);
    const hasEffects = blocks.some((block) => EFFECT_BLOCK_TYPES.includes(block.type));
    const voicedDialogueCount = dialogueBlocks.filter((block) => block.voiceAssetId).length;
    const missingVoiceCount = Math.max(dialogueBlocks.length - voicedDialogueCount, 0);
    const voiceProgress = dialogueBlocks.length > 0 ? getProgressPercent(voicedDialogueCount, dialogueBlocks.length) : 100;
    const longTextBlocks = blocks.filter(isLongTextBlock);
    const manyChoiceBlocks = choiceBlocks.filter((block) => toArray(block.options).length > CHOICE_MANY_OPTIONS);
    const longChoiceOptions = choiceBlocks.flatMap((block) =>
      toArray(block.options)
        .map((option, optionIndex) => ({ option, optionIndex, block }))
        .filter((item) => isLongChoiceText(item.option?.text))
    );
    const scriptQualityReport = getSceneScriptQualityReport(scene);
    const scriptQualitySummary = scriptQualityReport.summary ?? {};
    const routeIssues = getRouteTargetIssues(scene, blocks, sceneMap, baseContext);
    const issues = [...routeIssues];

    if (blocks.length === 0) {
      pushIssue(issues, "warn", "scene_empty", "场景还是空的", "这个场景没有任何剧情卡片，玩家进入后不会看到内容。", baseContext);
    }
    if (hasStoryContent && !hasBackground) {
      pushIssue(issues, "warn", "scene_missing_background", "缺少背景", "有正文或选项的场景建议先放一张背景，避免试玩时像灰盒。", baseContext);
    }
    if (hasStoryContent && !hasMusic) {
      pushIssue(issues, "tip", "scene_missing_music", "可以补一首 BGM", "没有 BGM 不一定阻塞发布，但第一版试玩会显得偏干。", baseContext);
    }
    if (missingVoiceCount > 0) {
      pushIssue(issues, "tip", "scene_missing_voice", "台词还有未绑定语音", `这个场景还有 ${missingVoiceCount} 句台词没有语音。`, baseContext);
    }
    if (longTextBlocks.length > 0) {
      pushIssue(issues, "warn", "scene_long_text", "存在过长文本卡", `有 ${longTextBlocks.length} 张台词或旁白卡偏长，建议拆成更适合点击阅读的短卡。`, baseContext);
    }
    if (manyChoiceBlocks.length > 0) {
      pushIssue(issues, "warn", "scene_many_choices", "选项数量偏多", `有 ${manyChoiceBlocks.length} 张选项卡超过 ${CHOICE_MANY_OPTIONS} 个选项，按钮区可能拥挤。`, baseContext);
    }
    if (longChoiceOptions.length > 0) {
      pushIssue(issues, "tip", "scene_long_choice_text", "选项文案偏长", `有 ${longChoiceOptions.length} 个选项超过 ${CHOICE_LONG_WARNING_LENGTH} 字，建议把解释放进前一句台词。`, baseContext);
    }
    if (hasStoryContent && !hasEffects) {
      pushIssue(issues, "tip", "scene_flat_presentation", "演出变化偏少", "可以补一个淡入淡出、镜头、滤镜或粒子，让场景更像正式作品。", baseContext);
    }
    pushScriptQualityProductionIssues(issues, scriptQualityReport, baseContext);

    issues.sort((left, right) => getIssueWeight(right) - getIssueWeight(left) || cleanText(left.title).localeCompare(cleanText(right.title), "zh-CN"));

    const metrics = {
      blockCount: blocks.length,
      dialogueCount: dialogueBlocks.length,
      narrationCount: narrationBlocks.length,
      choiceCount: choiceBlocks.length,
      conditionCount: conditionBlocks.length,
      hasStoryContent,
      hasBackground,
      hasMusic,
      hasEffects,
      voicedDialogueCount,
      missingVoiceCount,
      voiceProgress,
      longTextBlockCount: longTextBlocks.length,
      manyChoiceBlockCount: manyChoiceBlocks.length,
      longChoiceOptionCount: longChoiceOptions.length,
      scriptQualityStatus: scriptQualityReport.status ?? "ready",
      scriptQualityIssueCount: scriptQualitySummary.issueCount ?? 0,
      scriptQualityBlockerCount: scriptQualitySummary.blockerCount ?? 0,
      scriptQualityWarningCount: scriptQualitySummary.warningCount ?? 0,
      scriptQualityTipCount: scriptQualitySummary.tipCount ?? 0,
      scriptEmptyTextCount: scriptQualitySummary.emptyTextCount ?? 0,
      scriptDuplicateTextCount: scriptQualitySummary.duplicateTextCount ?? 0,
      scriptMissingPunctuationCount: scriptQualitySummary.missingPunctuationCount ?? 0,
      scriptMissingSpeakerCount: scriptQualitySummary.missingSpeakerCount ?? 0,
      scriptMissingExpressionCount: scriptQualitySummary.missingExpressionCount ?? 0,
      scriptChoiceIssueCount: scriptQualitySummary.choiceIssueCount ?? 0,
    };
    const issueCounts = {
      blockerCount: issues.filter((issue) => issue.severity === "blocker").length,
      warningCount: issues.filter((issue) => issue.severity === "warn").length,
      tipCount: issues.filter((issue) => issue.severity === "tip").length,
    };
    const pacingAnalysis =
      typeof scenePacingAdvisorTools.analyzeScenePacing === "function"
        ? scenePacingAdvisorTools.analyzeScenePacing(scene)
        : null;
    const pacingDigest =
      pacingAnalysis && typeof scenePacingAdvisorTools.buildScenePacingDigest === "function"
        ? scenePacingAdvisorTools.buildScenePacingDigest(pacingAnalysis)
        : null;
    const pacingIssueCodes = toArray(pacingAnalysis?.issues).map((issue) => issue?.code).filter(Boolean);
    const completionScore = scoreSceneProduction(metrics, issueCounts);
    const status = getSceneStatus(issues, completionScore);
    const report = {
      ...baseContext,
      sceneOrder: record.sceneIndex ?? 0,
      status,
      statusLabel: getSceneStatusLabel(status),
      completionScore,
      issues,
      ...metrics,
      ...issueCounts,
      pacingScore: pacingDigest?.score ?? completionScore,
      pacingGrade: pacingDigest?.gradeLabel ?? getSceneStatusLabel(status),
      pacingHeadline: pacingDigest?.headline ?? "",
      pacingIssueSummary: pacingDigest?.issueSummary ?? "",
      pacingActionSummary: pacingDigest?.actionSummary ?? "",
      pacingIssueCodes,
      nextAction: "",
      recipeSuggestion: null,
    };
    report.nextAction = getSceneNextAction(report);
    report.recipeSuggestion = getSceneRecipeSuggestion(report, scene);
    return report;
  }

  function buildSceneProductionBoard(data = {}) {
    const sceneMap = buildSceneMap(data);
    const scenes = getSceneRecords(data).map((record) => analyzeScene(record, data, sceneMap));
    const issues = scenes.flatMap((scene) =>
      scene.issues.map((issue) => ({
        ...issue,
        sceneId: scene.sceneId,
        sceneName: scene.sceneName,
        chapterName: scene.chapterName,
        completionScore: scene.completionScore,
      }))
    );
    const summary = {
      sceneCount: scenes.length,
      readySceneCount: scenes.filter((scene) => scene.status === "ready").length,
      blockedSceneCount: scenes.filter((scene) => scene.status === "blocked").length,
      warningSceneCount: scenes.filter((scene) => scene.status === "warn").length,
      draftSceneCount: scenes.filter((scene) => scene.status === "draft").length,
      emptySceneCount: scenes.filter((scene) => scene.blockCount === 0).length,
      missingBackgroundSceneCount: scenes.filter((scene) => scene.hasStoryContent && !scene.hasBackground).length,
      missingMusicSceneCount: scenes.filter((scene) => scene.hasStoryContent && !scene.hasMusic).length,
      missingVoiceLineCount: scenes.reduce((total, scene) => total + scene.missingVoiceCount, 0),
      longTextSceneCount: scenes.filter((scene) => scene.longTextBlockCount > 0).length,
      scriptQualityIssueCount: scenes.reduce((total, scene) => total + (scene.scriptQualityIssueCount ?? 0), 0),
      scriptQualitySceneCount: scenes.filter((scene) => (scene.scriptQualityIssueCount ?? 0) > 0).length,
      scriptEmptyTextSceneCount: scenes.filter((scene) => (scene.scriptEmptyTextCount ?? 0) > 0).length,
      scriptDuplicateTextSceneCount: scenes.filter((scene) => (scene.scriptDuplicateTextCount ?? 0) > 0).length,
      scriptChoiceIssueSceneCount: scenes.filter((scene) => (scene.scriptChoiceIssueCount ?? 0) > 0).length,
      flatSceneCount: scenes.filter((scene) => scene.hasStoryContent && !scene.hasEffects).length,
      blockerCount: issues.filter((issue) => issue.severity === "blocker").length,
      warningCount: issues.filter((issue) => issue.severity === "warn").length,
      tipCount: issues.filter((issue) => issue.severity === "tip").length,
      recipeSuggestionCount: scenes.filter((scene) => Boolean(scene.recipeSuggestion)).length,
      averageCompletion: scenes.length
        ? Math.round(scenes.reduce((total, scene) => total + scene.completionScore, 0) / scenes.length)
        : 0,
      averagePacingScore: scenes.length
        ? Math.round(scenes.reduce((total, scene) => total + (scene.pacingScore ?? 0), 0) / scenes.length)
        : 0,
      weakPacingSceneCount: scenes.filter((scene) => (scene.pacingScore ?? 0) < 72).length,
    };

    scenes.sort((left, right) => {
      if (right.blockerCount !== left.blockerCount) {
        return right.blockerCount - left.blockerCount;
      }
      if (right.warningCount !== left.warningCount) {
        return right.warningCount - left.warningCount;
      }
      if (left.completionScore !== right.completionScore) {
        return left.completionScore - right.completionScore;
      }
      return left.sceneName.localeCompare(right.sceneName, "zh-CN");
    });
    issues.sort((left, right) => getIssueWeight(right) - getIssueWeight(left) || left.sceneName.localeCompare(right.sceneName, "zh-CN"));

    return {
      projectTitle: cleanText(data.project?.title, "Canvasia Project"),
      scenes,
      issues,
      summary,
    };
  }

  function getSceneProductionBoardStatusDigest(board = {}) {
    const summary = board.summary ?? {};
    if ((summary.sceneCount ?? 0) === 0) {
      return {
        status: "empty",
        title: "还没有场景生产看板",
        detail: "项目里暂时没有场景。创建第一章和入口场景后，这里会列出制作任务。",
      };
    }
    if ((summary.blockedSceneCount ?? 0) > 0) {
      return {
        status: "blocked",
        title: `${summary.blockedSceneCount} 个场景需要先修`,
        detail: "优先处理坏跳转、空目标和会阻塞试玩路线的场景问题。",
      };
    }
    if ((summary.warningSceneCount ?? 0) > 0) {
      return {
        status: "warn",
        title: `${summary.warningSceneCount} 个场景建议复查`,
        detail: "项目可继续制作，但建议补背景、拆长文本、整理台词质量、选项数量和基础演出。",
      };
    }
    return {
      status: "ready",
      title: "场景生产节奏比较稳定",
      detail: "当前场景没有明显阻塞项，可以进入试玩确认和细节润色。",
    };
  }

  function escapeMarkdownTableCell(value) {
    return String(value ?? "")
      .replace(/\|/g, "\\|")
      .replace(/\r?\n/g, "<br />")
      .trim();
  }

  function buildMarkdownTable(headers = [], rows = []) {
    const safeRows = toArray(rows);
    if (!safeRows.length) {
      return "";
    }
    return [
      `| ${toArray(headers).map(escapeMarkdownTableCell).join(" | ")} |`,
      `| ${toArray(headers).map(() => "---").join(" | ")} |`,
      ...safeRows.map((row) => `| ${toArray(row).map(escapeMarkdownTableCell).join(" | ")} |`),
    ].join("\n");
  }

  function csvCell(value) {
    return `"${String(value ?? "").replace(/"/g, '""')}"`;
  }

  function buildCsv(headers = [], rows = []) {
    return [headers, ...rows].map((row) => toArray(row).map(csvCell).join(",")).join("\n");
  }

  function buildSceneProductionBoardMarkdown(board = {}, options = {}) {
    const summary = board.summary ?? {};
    const digest = getSceneProductionBoardStatusDigest(board);
    const generatedAt = cleanText(options.generatedAt);
    const projectTitle = cleanText(options.projectTitle ?? board.projectTitle, "Canvasia Project");
    const sceneRows = toArray(board.scenes).map((scene) => [
      scene.statusLabel,
      scene.chapterName,
      scene.sceneName,
      `${scene.completionScore}%`,
      scene.nextAction,
      `${scene.pacingScore ?? 0}%`,
      scene.pacingGrade ?? "",
      scene.pacingActionSummary ?? "",
      scene.scriptQualityIssueCount ?? 0,
      scene.scriptEmptyTextCount ?? 0,
      scene.scriptDuplicateTextCount ?? 0,
      scene.scriptChoiceIssueCount ?? 0,
      scene.blockCount,
      scene.dialogueCount,
      scene.missingVoiceCount,
      scene.hasBackground ? "有" : "缺",
      scene.hasMusic ? "有" : "缺",
      scene.hasEffects ? "有" : "少",
      scene.recipeSuggestion?.title ?? "",
    ]);
    const issueRows = toArray(board.issues).slice(0, 40).map((issue, index) => [
      index + 1,
      issue.severity === "blocker" ? "先修" : issue.severity === "warn" ? "复查" : "整理",
      issue.chapterName,
      issue.sceneName,
      issue.title,
      issue.detail,
    ]);

    return [
      `# ${projectTitle} 场景生产看板`,
      "",
      generatedAt ? `生成时间：${generatedAt}` : "",
      "",
      `状态：${digest.title}`,
      "",
      digest.detail,
      "",
      "## 总览",
      "",
      buildMarkdownTable(
        ["场景", "平均完成度", "平均节奏分", "可试玩", "先修场景", "复查场景", "空场景", "缺背景", "缺 BGM", "待绑语音", "台词体检问题"],
        [
          [
            summary.sceneCount ?? 0,
            `${summary.averageCompletion ?? 0}%`,
            `${summary.averagePacingScore ?? 0}%`,
            summary.readySceneCount ?? 0,
            summary.blockedSceneCount ?? 0,
            summary.warningSceneCount ?? 0,
            summary.emptySceneCount ?? 0,
            summary.missingBackgroundSceneCount ?? 0,
            summary.missingMusicSceneCount ?? 0,
            summary.missingVoiceLineCount ?? 0,
            summary.scriptQualityIssueCount ?? 0,
          ],
        ]
      ),
      "",
      "## 场景任务",
      "",
      buildMarkdownTable(["状态", "章节", "场景", "完成度", "下一步", "节奏分", "节奏等级", "节奏建议", "台词体检", "空文本", "重复文本", "选项文案", "卡片", "台词", "待绑语音", "背景", "BGM", "演出", "推荐配方"], sceneRows) || "当前没有可列出的场景。",
      "",
      "## 优先问题",
      "",
      buildMarkdownTable(["序号", "级别", "章节", "场景", "问题", "说明"], issueRows) || "当前没有明显场景生产问题。",
      "",
    ].join("\n");
  }

  function buildSceneProductionBoardCsv(board = {}) {
    const rows = toArray(board.scenes).map((scene, index) => [
      index + 1,
      scene.statusLabel,
      scene.chapterName,
      scene.sceneName,
      `${scene.completionScore}%`,
      scene.nextAction,
      `${scene.pacingScore ?? 0}%`,
      scene.pacingGrade ?? "",
      scene.pacingActionSummary ?? "",
      scene.scriptQualityIssueCount ?? 0,
      scene.scriptEmptyTextCount ?? 0,
      scene.scriptDuplicateTextCount ?? 0,
      scene.scriptChoiceIssueCount ?? 0,
      scene.blockCount,
      scene.dialogueCount,
      scene.narrationCount,
      scene.choiceCount,
      scene.conditionCount,
      scene.missingVoiceCount,
      scene.voiceProgress,
      scene.hasBackground ? "有" : "缺",
      scene.hasMusic ? "有" : "缺",
      scene.hasEffects ? "有" : "少",
      scene.recipeSuggestion?.title ?? "",
      scene.recipeSuggestion?.templateId ?? "",
      scene.issues.map((issue) => issue.title).join(" / "),
    ]);
    return `\uFEFF${buildCsv(
      ["序号", "状态", "章节", "场景", "完成度", "下一步", "节奏分", "节奏等级", "节奏建议", "台词体检", "空文本", "重复文本", "选项文案", "卡片", "台词", "旁白", "选项", "条件", "待绑语音", "语音完成度", "背景", "BGM", "演出", "推荐配方", "配方 ID", "问题"],
      rows
    )}\n`;
  }

  global.CanvasiaEditorSceneProductionBoard = Object.freeze({
    buildSceneProductionBoard,
    getSceneProductionBoardStatusDigest,
    buildSceneProductionBoardMarkdown,
    buildSceneProductionBoardCsv,
    getSceneStatusLabel,
    getSceneNextAction,
    getSceneRecipeSuggestion,
    getStoryTemplateRecommendationSuggestion,
  });
})(typeof window !== "undefined" ? window : globalThis);
