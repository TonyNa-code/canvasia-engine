(function attachPreviewRegressionTools(global) {
  "use strict";

  const DEFAULT_MAX_CASES = 12;
  const DEFAULT_BRANCHING_SEED_LIMIT = 4;
  const DEFAULT_ROUTE_CASE_SEED_LIMIT = 8;

  function toArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function cleanText(value, fallback = "") {
    const text = String(value ?? "").replace(/\s+/g, " ").trim();
    return text || fallback;
  }

  function toLimit(value, fallback) {
    const numberValue = Number.parseInt(value, 10);
    return Number.isFinite(numberValue) && numberValue > 0 ? numberValue : fallback;
  }

  function getSceneById(sceneId, options = {}) {
    const safeSceneId = cleanText(sceneId);
    if (!safeSceneId) {
      return null;
    }
    if (typeof options.getSceneById === "function") {
      return options.getSceneById(safeSceneId);
    }
    const scenesById = options.scenesById;
    if (scenesById && typeof scenesById.get === "function") {
      return scenesById.get(safeSceneId) ?? null;
    }
    if (scenesById && typeof scenesById === "object") {
      return scenesById[safeSceneId] ?? null;
    }
    return null;
  }

  function getRouteSeedScore(routeCase = {}) {
    if (routeCase.status === "broken") {
      return 118;
    }
    if (routeCase.status === "unreachable") {
      return 108;
    }
    if (routeCase.routeKind === "choice") {
      return 94;
    }
    if (routeCase.routeKind === "condition" || routeCase.routeKind === "fallback") {
      return 90;
    }
    return 86;
  }

  function buildRouteCaseSeed(point = {}, routeCase = {}) {
    const routeLabel = cleanText(routeCase.label, `路线 ${routeCase.order ?? ""}`.trim());
    return {
      seedId: `route:${routeCase.routeId || `${point.sceneId}:${routeCase.order ?? routeLabel}`}`,
      sceneId: point.sceneId,
      sceneName: point.sceneName,
      chapterName: point.chapterName ?? "未分章",
      sourceLabel: `分支用例 · ${routeLabel}`,
      reason:
        routeCase.status === "broken"
          ? "这条分支目标缺失，自动试玩会直接暴露坏链。"
          : routeCase.status === "unreachable"
            ? "这条分支目前不能从入口自然到达，需要确认路线接入。"
            : "这条分支来自路线试玩手册，应该单独跑一次而不是只测默认选项。",
      score: getRouteSeedScore(routeCase),
      seedKind: "route_case",
      routeCaseId: routeCase.routeId ?? "",
      routeKind: routeCase.routeKind ?? "",
      sourceSceneId: routeCase.sourceSceneId ?? point.sceneId,
      sourceSceneName: routeCase.sourceSceneName ?? point.sceneName,
      targetSceneId: routeCase.targetSceneId ?? "",
      targetSceneName: routeCase.targetSceneName ?? "",
      targetExists: Boolean(routeCase.targetExists),
      routeStatus: routeCase.status ?? "",
      routeStatusLabel: routeCase.statusLabel ?? "",
      routeLabel,
      blockIndex: Number.isInteger(routeCase.blockIndex) ? routeCase.blockIndex : null,
      optionIndex: Number.isInteger(routeCase.optionIndex) ? routeCase.optionIndex : null,
      branchIndex: Number.isInteger(routeCase.branchIndex) ? routeCase.branchIndex : null,
    };
  }

  function buildRouteCaseSeeds(routeOverview = {}, options = {}) {
    const limit = toLimit(options.routeCaseSeedLimit, DEFAULT_ROUTE_CASE_SEED_LIMIT);
    const decisionPoints = toArray(routeOverview.routeTestingPlan?.decisionPoints);
    return decisionPoints
      .flatMap((point) =>
        toArray(point.routeCases).map((routeCase) => buildRouteCaseSeed(point, routeCase))
      )
      .sort((left, right) => {
        if (right.score !== left.score) {
          return right.score - left.score;
        }
        return cleanText(left.routeLabel).localeCompare(cleanText(right.routeLabel), "zh-CN");
      })
      .slice(0, limit);
  }

  function buildPreviewRegressionSeeds(routeOverview = {}, options = {}) {
    const seeds = [];
    const seenSeedIds = new Set();
    const seenSceneBaselineIds = new Set();
    const maxCases = toLimit(options.maxCases, DEFAULT_MAX_CASES);
    const branchingSeedLimit = toLimit(options.branchingSeedLimit, DEFAULT_BRANCHING_SEED_LIMIT);
    const getSafeSceneId = typeof options.getSafeSceneId === "function" ? options.getSafeSceneId : (sceneId) => cleanText(sceneId);

    function appendSeed(seed, { sceneBaseline = false } = {}) {
      const safeSceneId = getSafeSceneId(seed?.sceneId);
      const scene = getSceneById(safeSceneId, options);
      const seedId = cleanText(seed?.seedId, `scene:${safeSceneId}:${seed?.sourceLabel ?? ""}`);

      if (!scene || seenSeedIds.has(seedId)) {
        return;
      }
      if (sceneBaseline && seenSceneBaselineIds.has(scene.id)) {
        return;
      }

      seenSeedIds.add(seedId);
      if (sceneBaseline) {
        seenSceneBaselineIds.add(scene.id);
      }
      seeds.push({
        ...seed,
        seedId,
        sceneId: scene.id,
        sceneName: scene.name,
        chapterName: seed.chapterName ?? scene.chapterName ?? "未分章",
      });
    }

    appendSeed(
      {
        seedId: "entry",
        sceneId: options.entrySceneId,
        sourceLabel: "项目入口",
        reason: "从游戏真正开始的位置先跑一遍，是最基础也最关键的一条烟测路线。",
        score: 120,
        seedKind: "entry",
      },
      { sceneBaseline: true }
    );

    toArray(routeOverview.chapters).forEach((chapter) => {
      const firstScene = toArray(chapter.scenes)[0];
      if (!firstScene) {
        return;
      }
      appendSeed(
        {
          seedId: `chapter:${chapter.chapterId ?? chapter.name ?? firstScene.id}`,
          sceneId: firstScene.id,
          chapterName: chapter.name,
          sourceLabel: `章节起点 · ${chapter.name}`,
          reason: "把每一章的第一场先跑通，最容易提前发现章节切换和起手坏链。",
          score: 92,
          seedKind: "chapter_start",
        },
        { sceneBaseline: true }
      );
    });

    buildRouteCaseSeeds(routeOverview, options).forEach((seed) => appendSeed(seed));

    toArray(routeOverview.nodes)
      .filter((node) => node.branchTargetCount > 1)
      .sort((left, right) => {
        if (right.branchTargetCount !== left.branchTargetCount) {
          return right.branchTargetCount - left.branchTargetCount;
        }
        return (right.errorCount ?? 0) - (left.errorCount ?? 0);
      })
      .slice(0, branchingSeedLimit)
      .forEach((node) => {
        appendSeed(
          {
            seedId: `branching:${node.id}`,
            sceneId: node.id,
            chapterName: node.chapterName,
            sourceLabel: "分支场景",
            reason: `这里有 ${node.branchTargetCount} 条去向，先按默认选项烟测一遍，最容易提前发现跳转断裂。`,
            score: 80,
            seedKind: "branching_scene",
          },
          { sceneBaseline: true }
        );
      });

    toArray(routeOverview.nodes)
      .filter((node) => (node.errorCount ?? 0) > 0 || node.brokenRouteCount > 0 || node.isOrphan || node.isUnreachable)
      .sort((left, right) => {
        const leftScore =
          (left.errorCount ?? 0) * 10 +
          left.brokenRouteCount * 6 +
          (left.isOrphan ? 4 : 0) +
          (left.isUnreachable ? 4 : 0);
        const rightScore =
          (right.errorCount ?? 0) * 10 +
          right.brokenRouteCount * 6 +
          (right.isOrphan ? 4 : 0) +
          (right.isUnreachable ? 4 : 0);
        return rightScore - leftScore;
      })
      .forEach((node) => {
        appendSeed(
          {
            seedId: `risk:${node.id}`,
            sceneId: node.id,
            chapterName: node.chapterName,
            sourceLabel: "问题高发场景",
            reason: "这段本身已经带问题信号，适合在正式导出前顺手做一次重点回归。",
            score: 70,
            seedKind: "risk_scene",
          },
          { sceneBaseline: true }
        );
      });

    const fallbackSceneId = options.fallbackSceneId;
    if (!seeds.length && fallbackSceneId) {
      appendSeed(
        {
          seedId: "fallback",
          sceneId: fallbackSceneId,
          sourceLabel: "默认起点",
          reason: "项目里暂时没有更明显的关键节点，就先从第一场开始回归。",
          score: 60,
          seedKind: "fallback",
        },
        { sceneBaseline: true }
      );
    }

    return seeds
      .sort((left, right) => {
        if (right.score !== left.score) {
          return right.score - left.score;
        }
        return cleanText(left.sceneName).localeCompare(cleanText(right.sceneName), "zh-CN");
      })
      .slice(0, maxCases);
  }

  function isTargetChoiceContext(seed = {}, context = {}) {
    const hasContext = cleanText(context.sceneId) || Number.isInteger(context.blockIndex);
    if (!hasContext) {
      return true;
    }
    if (cleanText(seed.sourceSceneId) && cleanText(context.sceneId) && cleanText(seed.sourceSceneId) !== cleanText(context.sceneId)) {
      return false;
    }
    if (Number.isInteger(seed.blockIndex) && Number.isInteger(context.blockIndex) && seed.blockIndex !== context.blockIndex) {
      return false;
    }
    return true;
  }

  function chooseRegressionOption(choiceOptions = [], seed = {}, context = {}) {
    const options = toArray(choiceOptions);
    if (!options.length) {
      return null;
    }
    const canTargetChoice = seed.routeKind === "choice" && isTargetChoiceContext(seed, context);
    if (canTargetChoice && Number.isInteger(seed.optionIndex) && options[seed.optionIndex]) {
      return options[seed.optionIndex];
    }
    if (canTargetChoice && seed.targetSceneId) {
      return options.find((option) => cleanText(option?.gotoSceneId) === cleanText(seed.targetSceneId)) ?? options[0];
    }
    return options[0];
  }

  global.CanvasiaEditorPreviewRegression = Object.freeze({
    buildRouteCaseSeeds,
    buildPreviewRegressionSeeds,
    chooseRegressionOption,
  });
})(typeof window !== "undefined" ? window : globalThis);
