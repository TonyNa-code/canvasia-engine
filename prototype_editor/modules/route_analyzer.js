(function attachRouteAnalyzerTools(global) {
  "use strict";

  const DEFAULT_EFFECT_BLOCK_TYPES = Object.freeze([
    "particle_effect",
    "screen_shake",
    "screen_flash",
    "screen_fade",
    "camera_zoom",
    "camera_pan",
    "screen_filter",
    "depth_blur",
  ]);

  function clamp(value, min, max) {
    return Math.min(Math.max(Number(value) || 0, min), max);
  }

  function getProgressPercent(done, total) {
    if (!total || total <= 0) {
      return 100;
    }
    return clamp(Math.round((done / total) * 100), 0, 100);
  }

  function truncateText(value, maxLength = 20) {
    const text = String(value ?? "").trim();
    const safeMax = Math.max(4, Number.parseInt(maxLength, 10) || 20);
    if (text.length <= safeMax) {
      return text;
    }
    return `${text.slice(0, safeMax - 1).trim()}…`;
  }

  function getMapValue(collection, key) {
    if (!collection || !key) {
      return null;
    }
    if (typeof collection.get === "function") {
      return collection.get(key) ?? null;
    }
    return Object.prototype.hasOwnProperty.call(collection, key) ? collection[key] ?? null : null;
  }

  function getSceneById(data, sceneId, options = {}) {
    if (typeof options.getSceneById === "function") {
      return options.getSceneById(sceneId);
    }
    return getMapValue(data?.scenesById, sceneId);
  }

  function buildRouteValidationSceneIndex(validation = {}) {
    const sceneIndex = new Map();

    function bumpIssue(sceneId, tone) {
      if (!sceneId) {
        return;
      }

      const entry = sceneIndex.get(sceneId) ?? { errorCount: 0, warningCount: 0 };
      if (tone === "error") {
        entry.errorCount += 1;
      } else {
        entry.warningCount += 1;
      }
      sceneIndex.set(sceneId, entry);
    }

    (validation.errors ?? []).forEach((issue) => {
      const context = issue?.context;
      if (context?.type === "story" || context?.type === "scene") {
        bumpIssue(context.sceneId, "error");
      }
    });

    (validation.warnings ?? []).forEach((issue) => {
      const context = issue?.context;
      if (context?.type === "story" || context?.type === "scene") {
        bumpIssue(context.sceneId, "warning");
      }
    });

    return sceneIndex;
  }

  function buildRouteSceneProduction(scene, issueCounts = null, options = {}) {
    const blocks = scene?.blocks ?? [];
    const effectBlockTypes = new Set(options.effectBlockTypes ?? DEFAULT_EFFECT_BLOCK_TYPES);
    const dialogueBlocks = blocks.filter((block) => block.type === "dialogue");
    const hasStoryContent = blocks.some((block) => ["dialogue", "narration", "choice"].includes(block.type));
    const hasBackground = blocks.some((block) => block.type === "background" && block.assetId);
    const hasMusic = blocks.some((block) => block.type === "music_play" && block.assetId);
    const hasEffects = blocks.some((block) => effectBlockTypes.has(block.type));
    const missingVoiceCount = dialogueBlocks.filter((block) => !block.voiceAssetId).length;
    const voicedDialogueCount = Math.max(dialogueBlocks.length - missingVoiceCount, 0);
    const voiceProgress = dialogueBlocks.length > 0 ? getProgressPercent(voicedDialogueCount, dialogueBlocks.length) : 100;
    const baseScore =
      (hasStoryContent ? 34 : 0) +
      (hasBackground ? 18 : 0) +
      (hasMusic ? 12 : 0) +
      (hasEffects ? 15 : 0) +
      (hasStoryContent ? Math.round((voiceProgress / 100) * 21) : 0);
    const errorCount = issueCounts?.errorCount ?? 0;
    const warningCount = issueCounts?.warningCount ?? 0;
    const issuePenalty = Math.min(24, errorCount * 10 + warningCount * 4);

    return {
      hasStoryContent,
      hasBackground,
      hasMusic,
      hasEffects,
      missingVoiceCount,
      voicedDialogueCount,
      voiceProgress,
      completionScore: clamp(baseScore - issuePenalty, 0, 100),
      errorCount,
      warningCount,
    };
  }

  function buildRouteChapterProduction(sceneNodes = []) {
    if (!sceneNodes.length) {
      return {
        averageCompletion: 0,
        readyCount: 0,
        missingBackgroundCount: 0,
        missingVoiceSceneCount: 0,
        flatSceneCount: 0,
        issueSceneCount: 0,
      };
    }

    return {
      averageCompletion: Math.round(
        sceneNodes.reduce((sum, node) => sum + (node.completionScore ?? 0), 0) / sceneNodes.length
      ),
      readyCount: sceneNodes.filter((node) => (node.completionScore ?? 0) >= 80).length,
      missingBackgroundCount: sceneNodes.filter((node) => node.hasStoryContent && !node.hasBackground).length,
      missingVoiceSceneCount: sceneNodes.filter((node) => node.missingVoiceCount > 0).length,
      flatSceneCount: sceneNodes.filter((node) => node.hasStoryContent && !node.hasEffects).length,
      issueSceneCount: sceneNodes.filter((node) => (node.errorCount ?? 0) > 0 || (node.warningCount ?? 0) > 0).length,
    };
  }

  function createSceneRoute(scene, config = {}, options = {}) {
    const data = options.data ?? {};
    const targetScene = getSceneById(data, config.targetSceneId, options);
    const missingTargetLabel = options.missingTargetLabel ?? "未设置目标";

    return {
      id: `${scene.id}-${config.blockIndex}-${config.routeKind}-${config.targetSceneId ?? "missing"}-${config.meta}`,
      sourceSceneId: scene.id,
      sourceSceneName: scene.name,
      targetSceneId: config.targetSceneId ?? "",
      targetSceneName: targetScene?.name ?? (config.targetSceneId || missingTargetLabel),
      targetExists: Boolean(targetScene),
      routeKind: config.routeKind,
      label: config.label,
      shortLabel: config.shortLabel,
      meta: config.meta,
    };
  }

  function collectSceneRoutes(scene, options = {}) {
    const routes = [];
    const safeTruncate = typeof options.truncateText === "function" ? options.truncateText : truncateText;
    const summarizeConditionBranch =
      typeof options.summarizeConditionBranch === "function"
        ? options.summarizeConditionBranch
        : () => "满足条件时";

    (scene?.blocks ?? []).forEach((block, blockIndex) => {
      if (block.type === "jump") {
        routes.push(
          createSceneRoute(scene, {
            blockIndex,
            routeKind: "jump",
            targetSceneId: block.targetSceneId,
            label: "直接跳转",
            shortLabel: "跳转",
            meta: `第 ${blockIndex + 1} 张卡片`,
          }, options)
        );
      }

      if (block.type === "choice") {
        (block.options ?? []).forEach((option, optionIndex) => {
          routes.push(
            createSceneRoute(scene, {
              blockIndex,
              routeKind: "choice",
              targetSceneId: option.gotoSceneId,
              label: safeTruncate(option.text || `选项 ${optionIndex + 1}`, 20),
              shortLabel: "选项",
              meta: `第 ${blockIndex + 1} 张卡片 / 选项 ${optionIndex + 1}`,
            }, options)
          );
        });
      }

      if (block.type === "condition") {
        (block.branches ?? []).forEach((branch, branchIndex) => {
          routes.push(
            createSceneRoute(scene, {
              blockIndex,
              routeKind: "condition",
              targetSceneId: branch.gotoSceneId,
              label: summarizeConditionBranch(branch),
              shortLabel: "条件",
              meta: `第 ${blockIndex + 1} 张卡片 / 条件分支 ${branchIndex + 1}`,
            }, options)
          );
        });

        routes.push(
          createSceneRoute(scene, {
            blockIndex,
            routeKind: "fallback",
            targetSceneId: block.elseGotoSceneId,
            label: "都不满足时",
            shortLabel: "否则",
            meta: `第 ${blockIndex + 1} 张卡片 / 否则`,
          }, options)
        );
      }
    });

    return routes;
  }

  function getRouteAlertPriority(tone) {
    if (tone === "danger") {
      return 0;
    }
    if (tone === "warn") {
      return 1;
    }
    return 2;
  }

  function buildSceneRouteOverview(data = {}, validation = {}, options = {}) {
    const entrySceneId = data.project?.entrySceneId;
    const incomingCounts = new Map();
    const brokenRoutes = [];
    const validationSceneIndex = buildRouteValidationSceneIndex(validation);
    const getSafeSceneStatus = typeof options.getSafeSceneStatus === "function" ? options.getSafeSceneStatus : (value) => value ?? "drafting";
    const getSafeScenePriority = typeof options.getSafeScenePriority === "function" ? options.getSafeScenePriority : (value) => value ?? "normal";
    const routeOptions = { ...options, data };

    const chapters = (data.chapters ?? []).map((chapter, chapterIndex) => {
      const sceneNodes = (chapter.sceneOrder ?? [])
        .map((sceneId, sceneIndex) => {
          const scene = getSceneById(data, sceneId, options);
          if (!scene) {
            return null;
          }

          const routes = collectSceneRoutes(scene, routeOptions);
          return {
            id: scene.id,
            name: scene.name,
            status: getSafeSceneStatus(scene.status),
            priority: getSafeScenePriority(scene.priority),
            notes: String(scene.notes ?? "").trim(),
            chapterId: chapter.chapterId,
            chapterName: chapter.name,
            chapterIndex,
            sceneIndex,
            blockCount: scene.blocks?.length ?? 0,
            dialogueCount: (scene.blocks ?? []).filter((block) => block.type === "dialogue").length,
            narrationCount: (scene.blocks ?? []).filter((block) => block.type === "narration").length,
            choiceCount: (scene.blocks ?? []).filter((block) => block.type === "choice").length,
            conditionCount: (scene.blocks ?? []).filter((block) => block.type === "condition").length,
            routes,
            isEntry: scene.id === entrySceneId,
            ...buildRouteSceneProduction(scene, validationSceneIndex.get(scene.id), options),
          };
        })
        .filter(Boolean);

      return {
        chapterId: chapter.chapterId,
        name: chapter.name,
        chapterIndex,
        scenes: sceneNodes,
        production: buildRouteChapterProduction(sceneNodes),
      };
    });

    const nodes = chapters.flatMap((chapter) => chapter.scenes);
    nodes.forEach((node) => {
      node.routes.forEach((route) => {
        if (route.targetExists) {
          incomingCounts.set(route.targetSceneId, (incomingCounts.get(route.targetSceneId) ?? 0) + 1);
        } else {
          brokenRoutes.push(route);
        }
      });
    });

    nodes.forEach((node) => {
      const validRoutes = node.routes.filter((route) => route.targetExists);
      node.incomingCount = incomingCounts.get(node.id) ?? 0;
      node.branchTargetCount = new Set(validRoutes.map((route) => route.targetSceneId)).size;
      node.brokenRouteCount = node.routes.length - validRoutes.length;
      node.isOrphan = !node.isEntry && node.incomingCount === 0;
      node.isEnding = validRoutes.length === 0;
    });

    const alerts = [
      ...brokenRoutes.map((route) => ({
        sceneId: route.sourceSceneId,
        sceneName: route.sourceSceneName,
        label: "坏链",
        tone: "danger",
        message: `${route.shortLabel} 指向了一个不存在的场景。`,
        meta: `${route.meta} -> ${route.targetSceneName}`,
      })),
      ...nodes
        .filter((node) => node.isOrphan)
        .map((node) => ({
          sceneId: node.id,
          sceneName: node.name,
          label: "孤立",
          tone: "warn",
          message: "目前没有任何分支、跳转或条件会走到这个场景。",
          meta: "如果这不是隐藏路线，可从别的场景补一条入口。",
        })),
      ...nodes
        .filter((node) => node.isEnding && !node.isEntry)
        .map((node) => ({
          sceneId: node.id,
          sceneName: node.name,
          label: "收束",
          tone: "soft",
          message: "这个场景没有继续跳往别处的路线。",
          meta: "如果它就是结局或章节收尾，那现在这样完全没问题。",
        })),
    ].sort((left, right) => getRouteAlertPriority(left.tone) - getRouteAlertPriority(right.tone));

    return {
      chapters,
      nodes,
      alerts,
      metrics: {
        entrySceneName: getSceneById(data, entrySceneId, options)?.name ?? "未设置",
        branchingScenes: nodes.filter((node) => node.branchTargetCount > 1).length,
        endingScenes: nodes.filter((node) => node.isEnding).length,
        orphanScenes: nodes.filter((node) => node.isOrphan).length,
        brokenRoutes: brokenRoutes.length,
      },
    };
  }

  global.CanvasiaEditorRouteAnalyzer = Object.freeze({
    DEFAULT_EFFECT_BLOCK_TYPES,
    buildRouteValidationSceneIndex,
    buildRouteSceneProduction,
    buildRouteChapterProduction,
    createSceneRoute,
    collectSceneRoutes,
    getRouteAlertPriority,
    buildSceneRouteOverview,
  });
})(typeof window !== "undefined" ? window : globalThis);
