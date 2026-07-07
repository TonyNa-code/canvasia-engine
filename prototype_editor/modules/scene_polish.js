(function attachScenePolishTools(global) {
  "use strict";

  const scenePacingAdvisorTools = global.CanvasiaEditorScenePacingAdvisor || {};

  const DEFAULTS = Object.freeze({
    transition: "fade",
    transitionDurationMs: 700,
    characterTransitionDurationMs: 620,
    musicFadeInMs: 900,
    musicFadeOutMs: 900,
    musicStopFadeOutMs: 700,
    musicVolume: 88,
    sfxVolume: 92,
    textSpeed: "normal",
  });

  function cloneValue(value) {
    return JSON.parse(JSON.stringify(value ?? null));
  }

  function toBlocks(sceneOrBlocks) {
    if (Array.isArray(sceneOrBlocks)) {
      return sceneOrBlocks;
    }
    return Array.isArray(sceneOrBlocks?.blocks) ? sceneOrBlocks.blocks : [];
  }

  function toArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function getMapValue(collection, key) {
    if (!key || !collection) {
      return null;
    }
    if (typeof collection.get === "function") {
      return collection.get(key) ?? null;
    }
    return collection[key] ?? null;
  }

  function addSceneToLookup(lookup, scene, fallbackId = "") {
    const sceneId = cleanText(scene?.id) || cleanText(fallbackId);
    if (sceneId && !lookup.has(sceneId)) {
      lookup.set(sceneId, scene);
    }
  }

  function buildSceneLookup(data = {}) {
    const lookup = new Map();
    if (data.scenesById && typeof data.scenesById.forEach === "function") {
      data.scenesById.forEach((scene, id) => addSceneToLookup(lookup, scene, id));
    } else if (data.scenesById && typeof data.scenesById === "object") {
      Object.entries(data.scenesById).forEach(([id, scene]) => addSceneToLookup(lookup, scene, id));
    }
    toArray(data.scenes).forEach((scene) => addSceneToLookup(lookup, scene));
    toArray(data.chapters).forEach((chapter) => {
      toArray(chapter.scenes).forEach((scene) => addSceneToLookup(lookup, scene));
    });
    return lookup;
  }

  function cleanText(value) {
    return String(value ?? "").trim();
  }

  function hasPositiveMs(value) {
    const numberValue = Number(value);
    return Number.isFinite(numberValue) && numberValue > 0;
  }

  function hasVolume(value) {
    const numberValue = Number(value);
    return Number.isFinite(numberValue) && numberValue > 0;
  }

  function pushChange(operation, field, from, to, label) {
    if (from === to) {
      return;
    }
    operation.fields.push({ field, from, to, label });
  }

  function ensureTransition(block, operation, defaults, durationMs) {
    const transition = cleanText(block.transition);
    if (!transition) {
      const nextTransition = defaults.transition;
      pushChange(operation, "transition", block.transition, nextTransition, "补默认转场");
      block.transition = nextTransition;
    }

    if (cleanText(block.transition) !== "none" && !hasPositiveMs(block.transitionDurationMs)) {
      pushChange(operation, "transitionDurationMs", block.transitionDurationMs, durationMs, "补转场时长");
      block.transitionDurationMs = durationMs;
    }
  }

  function ensureFadeMs(block, operation, field, value, label) {
    if (!hasPositiveMs(block[field])) {
      pushChange(operation, field, block[field], value, label);
      block[field] = value;
    }
  }

  function polishBlock(block, index, defaults) {
    const nextBlock = cloneValue(block) ?? {};
    const operation = {
      blockId: cleanText(nextBlock.id),
      blockType: cleanText(nextBlock.type),
      index,
      fields: [],
    };

    if (nextBlock.type === "dialogue" || nextBlock.type === "narration") {
      if (!cleanText(nextBlock.textSpeed)) {
        pushChange(operation, "textSpeed", nextBlock.textSpeed, defaults.textSpeed, "补文字速度");
        nextBlock.textSpeed = defaults.textSpeed;
      }
    } else if (nextBlock.type === "background") {
      ensureTransition(nextBlock, operation, defaults, defaults.transitionDurationMs);
    } else if (nextBlock.type === "character_show" || nextBlock.type === "character_hide") {
      ensureTransition(nextBlock, operation, defaults, defaults.characterTransitionDurationMs);
    } else if (nextBlock.type === "music_play") {
      ensureFadeMs(nextBlock, operation, "fadeInMs", defaults.musicFadeInMs, "补 BGM 淡入");
      ensureFadeMs(nextBlock, operation, "fadeOutMs", defaults.musicFadeOutMs, "补 BGM 淡出");
      if (!hasVolume(nextBlock.volume)) {
        pushChange(operation, "volume", nextBlock.volume, defaults.musicVolume, "补 BGM 音量");
        nextBlock.volume = defaults.musicVolume;
      }
      if (typeof nextBlock.loop !== "boolean") {
        pushChange(operation, "loop", nextBlock.loop, true, "补循环播放");
        nextBlock.loop = true;
      }
      if (!cleanText(nextBlock.endMode)) {
        pushChange(operation, "endMode", nextBlock.endMode, "until_next_music", "补播放范围");
        nextBlock.endMode = "until_next_music";
      }
    } else if (nextBlock.type === "music_stop") {
      ensureFadeMs(nextBlock, operation, "fadeOutMs", defaults.musicStopFadeOutMs, "补停止淡出");
    } else if (nextBlock.type === "sfx_play") {
      if (!hasVolume(nextBlock.volume)) {
        pushChange(operation, "volume", nextBlock.volume, defaults.sfxVolume, "补音效音量");
        nextBlock.volume = defaults.sfxVolume;
      }
    }

    return {
      block: nextBlock,
      operation: operation.fields.length ? operation : null,
    };
  }

  function buildScenePresentationPolishPlan(scene, options = {}) {
    const defaults = Object.freeze({ ...DEFAULTS, ...(options.defaults ?? {}) });
    const sourceBlocks = toBlocks(scene);
    const nextScene = cloneValue(scene) ?? {};
    const operations = [];
    const blocks = sourceBlocks.map((block, index) => {
      const result = polishBlock(block, index, defaults);
      if (result.operation) {
        operations.push(result.operation);
      }
      return result.block;
    });

    nextScene.blocks = blocks;

    return {
      changed: operations.length > 0,
      scene: nextScene,
      operations,
      changedBlockCount: operations.length,
      changedFieldCount: operations.reduce((total, operation) => total + operation.fields.length, 0),
      firstChangedBlockId: operations[0]?.blockId ?? "",
      firstChangedIndex: operations[0]?.index ?? -1,
      summary: buildScenePresentationPolishSummary(operations),
    };
  }

  function buildScenePresentationPolishSummary(operations = []) {
    const safeOperations = Array.isArray(operations) ? operations : [];
    const fieldCount = safeOperations.reduce((total, operation) => total + (operation.fields?.length ?? 0), 0);
    if (!safeOperations.length) {
      return "本场基础演出参数已经比较完整";
    }
    return `已润色 ${safeOperations.length} 张卡片，补齐 ${fieldCount} 个演出参数`;
  }

  function getScenePacingAnalysis(scene, options = {}) {
    if (typeof scenePacingAdvisorTools.analyzeScenePacing !== "function") {
      return null;
    }
    return scenePacingAdvisorTools.analyzeScenePacing(scene, options.pacing ?? {});
  }

  function getScenePacingDigest(analysis = null) {
    if (!analysis) {
      return null;
    }
    if (typeof scenePacingAdvisorTools.buildScenePacingDigest === "function") {
      return scenePacingAdvisorTools.buildScenePacingDigest(analysis);
    }
    return {
      score: analysis.score ?? 0,
      gradeId: analysis.grade?.id ?? "rough",
      gradeLabel: analysis.grade?.label ?? "待打磨",
      headline: analysis.headline ?? "这一场还需要试玩确认。",
      issueSummary: "暂无节奏摘要",
      actionSummary: toArray(analysis.actions).join(" / ") || "试玩确认",
      metricSummary: "",
    };
  }

  function getSceneDirectorPolishPriority(analysis = null) {
    const gradeId = cleanText(analysis?.grade?.id);
    if (gradeId === "rough") {
      return "danger";
    }
    if (gradeId === "needs_polish") {
      return "warn";
    }
    if (gradeId === "solid") {
      return "good";
    }
    return "soft";
  }

  function mergeUniqueLabels(...groups) {
    const labels = [];
    groups.flat().forEach((label) => {
      const safeLabel = cleanText(label);
      if (safeLabel && !labels.includes(safeLabel)) {
        labels.push(safeLabel);
      }
    });
    return labels;
  }

  function buildSceneDirectorPolishBrief(scene, plan = null, options = {}) {
    const polishPlan = plan ?? buildScenePresentationPolishPlan(scene, options);
    const pacingAnalysis = getScenePacingAnalysis(polishPlan.scene ?? scene, options);
    const pacingDigest = getScenePacingDigest(pacingAnalysis);
    const changeLabels = [];
    polishPlan.operations?.forEach((operation) => {
      operation.fields?.forEach((field) => {
        changeLabels.push(field.label);
      });
    });
    const pacingActions = toArray(pacingAnalysis?.actions);
    const issueTitles = toArray(pacingAnalysis?.issues)
      .slice(0, 3)
      .map((issue) => issue.title);
    const tagLimit = Math.max(1, Number(options.tagLimit) || 4);
    const tags = mergeUniqueLabels(changeLabels, pacingActions, issueTitles).slice(0, tagLimit);
    const gradeLabel = pacingDigest?.gradeLabel ?? "待试玩确认";
    const actionSummary = pacingDigest?.actionSummary ?? "";

    let helperText = polishPlan.changed
      ? `会补齐 ${mergeUniqueLabels(changeLabels).slice(0, tagLimit).join("、") || "基础演出参数"}。`
      : "本场的文字速度、转场、淡入淡出和音量已经比较完整。";
    if (pacingDigest) {
      helperText = polishPlan.changed
        ? `${helperText} 节奏体检：${gradeLabel}，建议 ${actionSummary || "试玩确认"}。`
        : `节奏体检：${gradeLabel}，${pacingDigest.issueSummary}；建议 ${actionSummary || "试玩确认"}。`;
    }

    return {
      changed: polishPlan.changed,
      priority: getSceneDirectorPolishPriority(pacingAnalysis),
      tags: tags.length ? tags : polishPlan.changed ? ["基础演出待补齐"] : ["基础演出已完整"],
      helperText,
      pacingAnalysis,
      pacingDigest,
      pacingIssueCount: toArray(pacingAnalysis?.issues).length,
      pacingScore: pacingAnalysis?.score ?? null,
      pacingGradeLabel: pacingDigest?.gradeLabel ?? "",
    };
  }

  function getScenePresentationPolishDigest(scene, options = {}) {
    const plan = buildScenePresentationPolishPlan(scene, options);
    const tagLimit = Math.max(1, Number(options.tagLimit) || 4);
    const changeLabels = [];
    plan.operations.forEach((operation) => {
      operation.fields.forEach((field) => {
        if (field.label && !changeLabels.includes(field.label)) {
          changeLabels.push(field.label);
        }
      });
    });
    const directorBrief = buildSceneDirectorPolishBrief(scene, plan, { ...options, tagLimit });

    return {
      canApply: plan.changed,
      actionLabel: plan.changed ? `润色 ${plan.changedFieldCount} 个演出参数` : "演出参数已完整",
      badgeLabel: plan.changed ? `${plan.changedBlockCount} 张卡片可润色` : "无需处理",
      helperText: directorBrief.helperText,
      tags: directorBrief.tags.length
        ? directorBrief.tags
        : plan.changed
          ? changeLabels.slice(0, tagLimit)
          : ["基础演出已完整"],
      pacing: directorBrief.pacingDigest,
      pacingIssueCount: directorBrief.pacingIssueCount,
      pacingScore: directorBrief.pacingScore,
      priority: directorBrief.priority,
      plan,
    };
  }

  function getProjectSceneList(data = {}) {
    const sceneLookup = buildSceneLookup(data);
    const scenes = [];
    const seen = new Set();
    const pushScene = (scene, chapter = {}) => {
      const sceneId = cleanText(scene?.id);
      if (!sceneId || seen.has(sceneId)) {
        return;
      }
      seen.add(sceneId);
      scenes.push({
        ...(scene ?? {}),
        id: sceneId,
        chapterId: cleanText(scene?.chapterId) || cleanText(chapter.chapterId),
        chapterName: cleanText(scene?.chapterName) || cleanText(chapter.name),
      });
    };

    toArray(data.chapters).forEach((chapter) => {
      const sceneIds = toArray(chapter.sceneOrder).map((sceneId) => cleanText(sceneId)).filter(Boolean);
      if (sceneIds.length) {
        sceneIds.forEach((sceneId) => pushScene(getMapValue(sceneLookup, sceneId), chapter));
        return;
      }
      toArray(chapter.scenes).forEach((scene) => pushScene(scene, chapter));
    });

    toArray(data.scenes).forEach((scene) => pushScene(scene));
    if (data.scenesById && typeof data.scenesById.forEach === "function") {
      data.scenesById.forEach((scene) => pushScene(scene));
    }

    return scenes;
  }

  function buildProjectPresentationPolishSummary(scenePlans = []) {
    const safePlans = Array.isArray(scenePlans) ? scenePlans : [];
    const fieldCount = safePlans.reduce((total, plan) => total + (plan.changedFieldCount ?? 0), 0);
    if (!safePlans.length) {
      return "全项目基础演出参数已经比较完整";
    }
    return `已润色 ${safePlans.length} 个场景，补齐 ${fieldCount} 个演出参数`;
  }

  function buildProjectPresentationPolishPlan(data = {}, options = {}) {
    const scenePlans = getProjectSceneList(data)
      .map((scene) => {
        const plan = buildScenePresentationPolishPlan(scene, options);
        return plan.changed
          ? {
              ...plan,
              sceneId: scene.id,
              sceneName: cleanText(scene.name) || scene.id,
              chapterId: cleanText(scene.chapterId),
              chapterName: cleanText(scene.chapterName),
            }
          : null;
      })
      .filter(Boolean);

    return {
      changed: scenePlans.length > 0,
      scenePlans,
      changedSceneCount: scenePlans.length,
      changedBlockCount: scenePlans.reduce((total, plan) => total + (plan.changedBlockCount ?? 0), 0),
      changedFieldCount: scenePlans.reduce((total, plan) => total + (plan.changedFieldCount ?? 0), 0),
      firstChangedSceneId: scenePlans[0]?.sceneId ?? "",
      firstChangedBlockId: scenePlans[0]?.firstChangedBlockId ?? "",
      firstChangedIndex: scenePlans[0]?.firstChangedIndex ?? -1,
      summary: buildProjectPresentationPolishSummary(scenePlans),
    };
  }

  function getProjectPresentationPolishDigest(data = {}, options = {}) {
    const plan = buildProjectPresentationPolishPlan(data, options);
    const pacingAnalyses =
      typeof scenePacingAdvisorTools.analyzeScenePacing === "function"
        ? getProjectSceneList(data).map((scene) => scenePacingAdvisorTools.analyzeScenePacing(scene, options.pacing ?? {}))
        : [];
    const pacingAggregate =
      pacingAnalyses.length && typeof scenePacingAdvisorTools.aggregateScenePacingAnalyses === "function"
        ? scenePacingAdvisorTools.aggregateScenePacingAnalyses(pacingAnalyses)
        : null;
    const previewNames = plan.scenePlans
      .slice(0, Math.max(1, Number(options.sceneNameLimit) || 3))
      .map((scenePlan) => scenePlan.sceneName)
      .filter(Boolean);

    return {
      canApply: plan.changed,
      actionLabel: plan.changed ? `润色全项目 ${plan.changedFieldCount} 项` : "全项目演出已完整",
      badgeLabel: plan.changed ? `${plan.changedSceneCount} 个场景可润色` : "无需处理",
      helperText: plan.changed
        ? `会处理 ${previewNames.join("、")}${plan.changedSceneCount > previewNames.length ? " 等场景" : ""}。`
        : pacingAggregate?.roughSceneCount
          ? `全项目基础参数已完整，但还有 ${pacingAggregate.roughSceneCount} 个场景节奏需要打磨。`
          : "全项目的基础转场、淡入淡出、音量和文字速度已经比较完整。",
      pacing: pacingAggregate,
      plan,
    };
  }

  global.CanvasiaEditorScenePolish = Object.freeze({
    DEFAULTS,
    buildScenePresentationPolishPlan,
    buildScenePresentationPolishSummary,
    buildSceneDirectorPolishBrief,
    getScenePresentationPolishDigest,
    getProjectSceneList,
    buildProjectPresentationPolishPlan,
    buildProjectPresentationPolishSummary,
    getProjectPresentationPolishDigest,
  });
})(typeof window !== "undefined" ? window : globalThis);
