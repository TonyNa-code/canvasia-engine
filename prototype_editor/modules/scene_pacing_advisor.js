(function attachScenePacingAdvisorTools(global) {
  "use strict";

  const storyBlockCatalogTools = global.CanvasiaEditorStoryBlockCatalog || {};
  const readabilityTools = global.CanvasiaEditorScriptReadability || {};
  const CHOICE_CONTINUE_TARGET = "__continue__";
  const LONG_TEXT_LENGTH = Number(readabilityTools.VN_TEXT_LONG_WARNING_LENGTH) || 260;
  const LONG_TEXT_LINES = Number(readabilityTools.VN_TEXT_LONG_WARNING_LINES) || 5;
  const MANY_CHOICE_OPTIONS = Number(readabilityTools.VN_CHOICE_MANY_OPTIONS) || 6;
  const FALLBACK_EFFECT_BLOCK_TYPES = Object.freeze([
    "particle_effect",
    "wait",
    "screen_shake",
    "screen_flash",
    "screen_fade",
    "camera_zoom",
    "camera_pan",
    "screen_filter",
    "depth_blur",
  ]);
  const EFFECT_BLOCK_TYPES = Object.freeze(
    typeof storyBlockCatalogTools.getEffectBlockTypes === "function"
      ? storyBlockCatalogTools.getEffectBlockTypes()
      : FALLBACK_EFFECT_BLOCK_TYPES
  );
  const STORY_TEXT_TYPES = Object.freeze(["dialogue", "narration"]);
  const STORY_CONTENT_TYPES = Object.freeze(["dialogue", "narration", "choice", "condition", "video_play", "credits_roll"]);
  const OUTRO_BLOCK_TYPES = Object.freeze(["jump", "credits_roll", "music_stop", "screen_fade"]);
  const SCRIPT_QUALITY_PACING_CODES = Object.freeze([
    "script_empty_text",
    "script_duplicate_nearby_text",
    "script_choice_empty_options",
    "script_choice_empty_text",
    "script_choice_text_too_long",
  ]);

  function toArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function cleanText(value, fallback = "") {
    const text = String(value ?? "").replace(/\s+/g, " ").trim();
    return text || fallback;
  }

  function clamp(value, min, max) {
    return Math.min(Math.max(Number(value) || 0, min), max);
  }

  function getBlocks(sceneOrBlocks) {
    return Array.isArray(sceneOrBlocks) ? sceneOrBlocks : toArray(sceneOrBlocks?.blocks);
  }

  function getBlockText(block = {}) {
    return cleanText(block.text ?? block.fields?.text);
  }

  function getChoiceOptions(block = {}) {
    return toArray(block.options?.length ? block.options : block.choiceOptions?.length ? block.choiceOptions : block.fields?.options);
  }

  function getChoiceEffects(option = {}) {
    return toArray(option.effects?.length ? option.effects : option.choiceEffects);
  }

  function isChoiceContinueTarget(value) {
    return cleanText(value) === CHOICE_CONTINUE_TARGET;
  }

  function getTextMetrics(text) {
    const safeText = String(text ?? "").trim();
    return {
      length: safeText.length,
      lineCount: safeText ? safeText.split(/\r?\n/).length : 0,
    };
  }

  function getReadableState(text) {
    if (typeof readabilityTools.getReadableTextToolState === "function") {
      return readabilityTools.getReadableTextToolState(text);
    }
    const metrics = getTextMetrics(text);
    const isLong = metrics.length > LONG_TEXT_LENGTH || metrics.lineCount > LONG_TEXT_LINES;
    return {
      metrics,
      isLong,
      canSplit: isLong,
      statusText: isLong ? "建议拆卡" : "长度舒适",
      toneClass: isLong ? "warn-text" : "good-text",
    };
  }

  function getScriptQualityPacingIssues(sceneOrBlocks) {
    if (typeof readabilityTools.buildScriptQualitySceneReport !== "function") {
      return [];
    }
    const report = readabilityTools.buildScriptQualitySceneReport(sceneOrBlocks);
    return toArray(report.issues)
      .filter((issue) => SCRIPT_QUALITY_PACING_CODES.includes(issue.code))
      .slice(0, 4)
      .map((issue) =>
        buildIssue(
          issue.severity === "blocker" ? "blocker" : "warn",
          `pacing_${issue.code}`,
          issue.title,
          issue.detail,
          issue.suggestion || "修台词"
        )
      );
  }

  function hasVariableEffect(option = {}) {
    return getChoiceEffects(option).some((effect) => ["variable_add", "variable_set"].includes(effect?.type));
  }

  function getMaxConsecutiveTextBlocks(blocks = []) {
    let current = 0;
    let max = 0;
    toArray(blocks).forEach((block) => {
      if (STORY_TEXT_TYPES.includes(block?.type)) {
        current += 1;
        max = Math.max(max, current);
        return;
      }
      current = 0;
    });
    return max;
  }

  function buildIssue(severity, code, title, detail, actionLabel) {
    return Object.freeze({ severity, code, title, detail, actionLabel });
  }

  function getIssuePenalty(issue = {}) {
    if (issue.severity === "blocker") {
      return 28;
    }
    if (issue.severity === "warn") {
      return 12;
    }
    return 6;
  }

  function getScenePacingGrade(score) {
    const safeScore = clamp(score, 0, 100);
    if (safeScore >= 86) {
      return { id: "ready", label: "节奏成熟", tone: "good" };
    }
    if (safeScore >= 72) {
      return { id: "solid", label: "可以试玩", tone: "good" };
    }
    if (safeScore >= 52) {
      return { id: "needs_polish", label: "需要打磨", tone: "warn" };
    }
    return { id: "rough", label: "还像草稿", tone: "danger" };
  }

  function getPacingHeadline(analysis = {}) {
    const gradeLabel = analysis.grade?.label ?? "待分析";
    const issueCount = analysis.issues?.length ?? 0;
    if (issueCount <= 0) {
      return `${gradeLabel}：这场戏已经具备清晰的试玩节奏。`;
    }
    return `${gradeLabel}：还有 ${issueCount} 个节奏点建议处理。`;
  }

  function analyzeScenePacing(sceneOrBlocks, options = {}) {
    const blocks = getBlocks(sceneOrBlocks);
    const effectBlockTypes = new Set(options.effectBlockTypes ?? EFFECT_BLOCK_TYPES);
    const textBlocks = blocks.filter((block) => STORY_TEXT_TYPES.includes(block?.type));
    const choiceBlocks = blocks.filter((block) => block?.type === "choice");
    const conditionBlocks = blocks.filter((block) => block?.type === "condition");
    const routeBlocks = blocks.filter((block) => ["choice", "condition", "jump"].includes(block?.type));
    const effectBlocks = blocks.filter((block) => effectBlockTypes.has(block?.type));
    const backgroundBlocks = blocks.filter((block) => block?.type === "background");
    const musicBlocks = blocks.filter((block) => block?.type === "music_play");
    const dialogueBlocks = blocks.filter((block) => block?.type === "dialogue");
    const choiceOptions = choiceBlocks.flatMap(getChoiceOptions);
    const routedChoiceOptions = choiceOptions.filter((option) => !isChoiceContinueTarget(option?.gotoSceneId));
    const variableChoiceOptions = choiceOptions.filter(hasVariableEffect);
    const longTextBlocks = textBlocks.filter((block) => getReadableState(getBlockText(block)).isLong);
    const manyChoiceBlocks = choiceBlocks.filter((block) => getChoiceOptions(block).length > MANY_CHOICE_OPTIONS);
    const missingVoiceCount = dialogueBlocks.filter((block) => !cleanText(block.voiceAssetId)).length;
    const hasStoryContent = blocks.some((block) => STORY_CONTENT_TYPES.includes(block?.type));
    const hasBackground = backgroundBlocks.some((block) => cleanText(block.assetId));
    const hasMusic = musicBlocks.some((block) => cleanText(block.assetId));
    const hasEffect = effectBlocks.length > 0;
    const hasBranching = choiceBlocks.length > 0 || conditionBlocks.length > 0;
    const hasMeaningfulChoice = routedChoiceOptions.length > 0 || variableChoiceOptions.length > 0;
    const hasOutroCue = blocks.slice(-4).some((block) => OUTRO_BLOCK_TYPES.includes(block?.type));
    const maxConsecutiveTextBlocks = getMaxConsecutiveTextBlocks(blocks);
    const issues = [];
    const scriptQualityPacingIssues = getScriptQualityPacingIssues(sceneOrBlocks);

    if (!blocks.length) {
      issues.push(buildIssue("blocker", "pacing_empty_scene", "场景没有内容", "玩家进入后不会看到任何剧情卡片。", "插入可试玩段落"));
    }
    if (blocks.length > 0 && !hasStoryContent) {
      issues.push(buildIssue("blocker", "pacing_no_story_content", "缺少剧情内容", "当前只有演出或控制卡，还没有台词、旁白、选项或结尾内容。", "补剧情卡"));
    }
    if (hasStoryContent && !hasBackground) {
      issues.push(buildIssue("warn", "pacing_missing_background", "缺少视觉锚点", "有正文的场景建议至少放一张背景或 CG，让玩家知道自己在哪里。", "补背景"));
    }
    if (hasStoryContent && !hasMusic) {
      issues.push(buildIssue("tip", "pacing_missing_music", "氛围音频偏空", "可以给这段指定 BGM 范围，避免第一版试玩显得干。", "补 BGM 范围"));
    }
    if (hasStoryContent && textBlocks.length >= 3 && !hasEffect) {
      issues.push(buildIssue("tip", "pacing_flat_presentation", "演出起伏偏少", "连续阅读时最好穿插淡入淡出、镜头、滤镜、停顿或粒子效果。", "补演出节拍"));
    }
    if (longTextBlocks.length > 0) {
      issues.push(buildIssue("warn", "pacing_long_text", "文本卡偏长", `有 ${longTextBlocks.length} 张台词或旁白建议拆卡。`, "拆长文本"));
    }
    if (maxConsecutiveTextBlocks >= 7) {
      issues.push(buildIssue("warn", "pacing_text_run_too_long", "连续文本过长", `连续 ${maxConsecutiveTextBlocks} 张文本卡没有演出或交互，玩家容易疲劳。`, "插入节奏点"));
    }
    if (manyChoiceBlocks.length > 0) {
      issues.push(buildIssue("warn", "pacing_many_choices", "选项过多", `有 ${manyChoiceBlocks.length} 张选项卡超过 ${MANY_CHOICE_OPTIONS} 个选项。`, "拆成二级选择"));
    }
    if (choiceBlocks.length > 0 && !hasMeaningfulChoice) {
      issues.push(buildIssue("tip", "pacing_choice_without_consequence", "选择缺少后果", "选项都只继续当前段落，建议至少绑定变量或通向不同场景。", "补变量后果"));
    }
    if (hasBranching && conditionBlocks.length === 0 && variableChoiceOptions.length > 0) {
      issues.push(buildIssue("tip", "pacing_branch_without_payoff", "变量还没有回收", "选项已经记录变量，但本场景或后续场景还需要条件判断来兑现选择。", "补条件判断"));
    }
    if (hasStoryContent && blocks.length >= 6 && !hasOutroCue) {
      issues.push(buildIssue("tip", "pacing_missing_outro", "收尾提示不足", "接近完整的场景最好补一个跳转、淡出、停 BGM 或片尾卡，方便试玩确认。", "补场景收尾"));
    }
    issues.push(...scriptQualityPacingIssues);

    const baseScore =
      (blocks.length > 0 ? 8 : 0) +
      (hasStoryContent ? 24 : 0) +
      (hasBackground ? 14 : hasStoryContent ? 0 : 14) +
      (hasMusic ? 10 : hasStoryContent ? 0 : 10) +
      (hasEffect ? 12 : hasStoryContent ? 0 : 12) +
      (hasMeaningfulChoice || !hasBranching ? 12 : 4) +
      (hasOutroCue || blocks.length < 6 ? 10 : 4) +
      (missingVoiceCount === 0 ? 10 : Math.max(2, 10 - missingVoiceCount * 2));
    const score = clamp(baseScore - issues.reduce((total, issue) => total + getIssuePenalty(issue), 0), 0, 100);
    const grade = getScenePacingGrade(score);
    const actions = issues.map((issue) => issue.actionLabel).filter(Boolean).slice(0, 4);
    const analysis = {
      score,
      grade,
      issues,
      actions,
      metrics: {
        blockCount: blocks.length,
        textBlockCount: textBlocks.length,
        dialogueCount: dialogueBlocks.length,
        choiceCount: choiceBlocks.length,
        optionCount: choiceOptions.length,
        conditionCount: conditionBlocks.length,
        routeBlockCount: routeBlocks.length,
        effectBlockCount: effectBlocks.length,
        longTextBlockCount: longTextBlocks.length,
        manyChoiceBlockCount: manyChoiceBlocks.length,
        missingVoiceCount,
        scriptQualityIssueCount: scriptQualityPacingIssues.length,
        maxConsecutiveTextBlocks,
        hasStoryContent,
        hasBackground,
        hasMusic,
        hasEffect,
        hasBranching,
        hasMeaningfulChoice,
        hasOutroCue,
      },
    };

    return Object.freeze({
      ...analysis,
      headline: getPacingHeadline(analysis),
    });
  }

  function buildScenePacingDigest(analysis = {}) {
    const metrics = analysis.metrics ?? {};
    const issueTitles = toArray(analysis.issues).slice(0, 3).map((issue) => issue.title).join(" / ");
    return {
      score: analysis.score ?? 0,
      gradeId: analysis.grade?.id ?? "rough",
      gradeLabel: analysis.grade?.label ?? "还像草稿",
      headline: analysis.headline ?? getPacingHeadline(analysis),
      issueSummary: issueTitles || "暂无明显节奏问题",
      actionSummary: toArray(analysis.actions).join(" / ") || "试玩确认",
      metricSummary: `${metrics.blockCount ?? 0} 卡 / ${metrics.textBlockCount ?? 0} 文本 / ${metrics.effectBlockCount ?? 0} 演出`,
    };
  }

  function aggregateScenePacingAnalyses(analyses = []) {
    const safeAnalyses = toArray(analyses);
    const issueMap = new Map();
    safeAnalyses.forEach((analysis) => {
      toArray(analysis.issues).forEach((issue) => {
        const entry = issueMap.get(issue.code) ?? { code: issue.code, title: issue.title, count: 0 };
        entry.count += 1;
        issueMap.set(issue.code, entry);
      });
    });

    return {
      sceneCount: safeAnalyses.length,
      averageScore: safeAnalyses.length
        ? Math.round(safeAnalyses.reduce((total, analysis) => total + (analysis.score ?? 0), 0) / safeAnalyses.length)
        : 0,
      roughSceneCount: safeAnalyses.filter((analysis) => ["rough", "needs_polish"].includes(analysis.grade?.id)).length,
      readySceneCount: safeAnalyses.filter((analysis) => ["ready", "solid"].includes(analysis.grade?.id)).length,
      topIssues: Array.from(issueMap.values()).sort((left, right) => right.count - left.count || left.title.localeCompare(right.title, "zh-CN")),
    };
  }

  global.CanvasiaEditorScenePacingAdvisor = Object.freeze({
    CHOICE_CONTINUE_TARGET,
    LONG_TEXT_LENGTH,
    LONG_TEXT_LINES,
    MANY_CHOICE_OPTIONS,
    EFFECT_BLOCK_TYPES,
    getBlocks,
    getReadableState,
    getScenePacingGrade,
    getPacingHeadline,
    analyzeScenePacing,
    buildScenePacingDigest,
    aggregateScenePacingAnalyses,
  });
})(typeof window !== "undefined" ? window : globalThis);
