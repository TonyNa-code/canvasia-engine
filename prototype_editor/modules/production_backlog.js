(function attachProductionBacklogTools(global) {
  const AREA_LABELS = Object.freeze({
    route: "路线结构",
    scene: "场景制作",
    director: "导演分镜",
    voice: "语音制作",
    choice: "选项分支",
    variable: "变量逻辑",
    asset: "素材依赖",
    rights: "素材授权",
    audio: "音频调度",
    stage: "角色调度",
    presentation: "演出节奏",
    localization: "多语言",
    runtime: "Runtime 覆盖",
    loading: "首屏加载",
    unlockable: "图鉴回想",
  });

  const AREA_ACTIONS = Object.freeze({
    route: Object.freeze({ label: "看路线图", action: "switch-screen", screen: "dashboard" }),
    scene: Object.freeze({ label: "去剧情页", action: "switch-screen", screen: "story" }),
    director: Object.freeze({ label: "补分镜", action: "switch-screen", screen: "story" }),
    voice: Object.freeze({ label: "去台词台本", action: "switch-screen", screen: "script" }),
    choice: Object.freeze({ label: "调整选项", action: "switch-screen", screen: "story" }),
    variable: Object.freeze({ label: "检查变量", action: "switch-screen", screen: "story" }),
    asset: Object.freeze({ label: "去素材页", action: "switch-screen", screen: "assets" }),
    rights: Object.freeze({ label: "补授权资料", action: "switch-screen", screen: "assets" }),
    audio: Object.freeze({ label: "调 BGM", action: "switch-screen", screen: "story" }),
    stage: Object.freeze({ label: "补角色演出", action: "switch-screen", screen: "story" }),
    presentation: Object.freeze({ label: "补演出卡", action: "switch-screen", screen: "story" }),
    localization: Object.freeze({ label: "看翻译报告", action: "switch-screen", screen: "inspection" }),
    runtime: Object.freeze({ label: "看 Runtime 覆盖", action: "switch-screen", screen: "inspection" }),
    loading: Object.freeze({ label: "看首屏预算", action: "switch-screen", screen: "inspection" }),
    unlockable: Object.freeze({ label: "看可解锁清单", action: "switch-screen", screen: "inspection" }),
  });

  const VN_ESSENTIAL_BACKLOG_AREAS = Object.freeze({
    story: "scene",
    visual: "scene",
    character: "stage",
    audio: "audio",
    branch: "choice",
    textbox: "runtime",
    system: "runtime",
    ui: "runtime",
    media: "runtime",
  });

  function toArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function cleanText(value, fallback = "") {
    const text = String(value ?? "").replace(/\s+/g, " ").trim();
    return text || fallback;
  }

  function toCount(value, fallback = 0) {
    const numberValue = Number(value);
    if (!Number.isFinite(numberValue)) {
      return fallback;
    }
    return Math.max(0, Math.round(numberValue));
  }

  function normalizeSeverity(severity = "") {
    if (["blocker", "danger", "error", "blocked"].includes(severity)) {
      return "blocker";
    }
    if (["warn", "warning", "preview"].includes(severity)) {
      return "warn";
    }
    if (["good", "ready", "ok", "pass"].includes(severity)) {
      return "good";
    }
    return "tip";
  }

  function getSeverityWeight(severity = "") {
    if (severity === "blocker") {
      return 100;
    }
    if (severity === "warn") {
      return 60;
    }
    if (severity === "tip") {
      return 25;
    }
    return 0;
  }

  function getSeverityLabel(severity = "") {
    if (severity === "blocker") {
      return "先修";
    }
    if (severity === "warn") {
      return "优先";
    }
    if (severity === "good") {
      return "通过";
    }
    return "整理";
  }

  function getTaskAction(area, override = null) {
    const action = override || AREA_ACTIONS[area] || AREA_ACTIONS.scene;
    return {
      label: cleanText(action.label, "去处理"),
      action: cleanText(action.action, "switch-screen"),
      screen: cleanText(action.screen),
      sceneId: cleanText(action.sceneId),
      blockId: cleanText(action.blockId),
      assetId: cleanText(action.assetId),
      chapterId: cleanText(action.chapterId),
      dataset: action.dataset && typeof action.dataset === "object" ? action.dataset : {},
    };
  }

  function getTaskSource(issue = {}, fallback = "") {
    return [
      issue.chapterName,
      issue.sceneName,
      issue.speakerName,
      issue.assetName,
      issue.variableName,
      issue.optionText,
      issue.languageLabel,
    ]
      .map((item) => cleanText(item))
      .filter(Boolean)
      .join(" / ") || fallback;
  }

  function makeTaskKey(task = {}) {
    return [
      task.area,
      task.severity,
      task.title,
      task.source,
      task.detail,
    ]
      .map((item) => cleanText(item).toLowerCase())
      .join("|");
  }

  function addTask(tasks, task = {}) {
    const area = cleanText(task.area, "scene");
    const severity = normalizeSeverity(task.severity);
    const title = cleanText(task.title);
    if (!title) {
      return;
    }
    const nextTask = {
      id: "",
      area,
      areaLabel: AREA_LABELS[area] ?? cleanText(area, "制作"),
      severity,
      severityLabel: getSeverityLabel(severity),
      title,
      detail: cleanText(task.detail, "继续处理这个制作项。"),
      source: cleanText(task.source, "全项目"),
      count: toCount(task.count, 1),
      action: getTaskAction(area, task.action),
      priority: getSeverityWeight(severity) + toCount(task.priorityBoost, 0),
    };
    const key = makeTaskKey(nextTask);
    if (tasks.some((item) => item.key === key)) {
      return;
    }
    nextTask.key = key;
    nextTask.id = `task_${tasks.length + 1}`;
    tasks.push(nextTask);
  }

  function addIssueTasks(tasks, area, issues = [], options = {}) {
    const maxItems = toCount(options.maxItems, 10);
    const action = options.action || AREA_ACTIONS[area];
    toArray(issues)
      .filter((issue) => normalizeSeverity(issue?.severity) !== "good")
      .sort((left, right) => getSeverityWeight(normalizeSeverity(right?.severity)) - getSeverityWeight(normalizeSeverity(left?.severity)))
      .slice(0, maxItems)
      .forEach((issue) => {
        addTask(tasks, {
          area,
          severity: issue.severity,
          title: issue.title ?? issue.code ?? options.fallbackTitle,
          detail: issue.detail ?? issue.description ?? issue.status ?? "这个条目需要制作复查。",
          source: getTaskSource(issue, options.fallbackSource),
          action,
          priorityBoost: options.priorityBoost,
        });
      });
  }

  function getStageContinuitySeverity(row = {}) {
    const status = cleanText(row?.status);
    if (status === "blocker") {
      return "blocker";
    }
    if (status === "warn") {
      return "warn";
    }
    return "tip";
  }

  function getStageContinuityTaskTitle(row = {}) {
    const nextAction = cleanText(row?.nextAction, "复查舞台连续性");
    const sceneName = cleanText(row?.sceneName);
    return sceneName ? `${nextAction}：${sceneName}` : nextAction;
  }

  function getStageContinuityTaskSource(row = {}) {
    return [
      row.chapterName,
      row.sceneName,
      row.openingCue ? `开场：${row.openingCue}` : "",
      row.endingCastLabel ? `结尾在场：${row.endingCastLabel}` : "",
    ]
      .map((item) => cleanText(item))
      .filter(Boolean)
      .join(" / ") || "角色舞台调度表";
  }

  function addStageContinuityTasks(tasks, stageDirectionSheet = {}) {
    toArray(stageDirectionSheet?.continuityAudit?.reviewRows)
      .filter((row) => cleanText(row?.status) !== "good")
      .slice(0, 10)
      .forEach((row, index) => {
        const actionLabel = cleanText(row?.nextAction, "复查舞台连续性");
        addTask(tasks, {
          area: "stage",
          severity: getStageContinuitySeverity(row),
          title: getStageContinuityTaskTitle(row),
          detail: cleanText(row?.reason, "开场、登场或退场顺序需要复查。"),
          source: getStageContinuityTaskSource(row),
          action: {
            label: cleanText(row?.sceneId) ? "打开这个场景" : actionLabel,
            action: cleanText(row?.sceneId) ? "open-scene-from-map" : "switch-screen",
            screen: "story",
            sceneId: cleanText(row?.sceneId),
            dataset: { "inspection-section": "stage-direction" },
          },
          priorityBoost: 12 - Math.min(index, 8),
        });
      });
  }

  function getRouteExecutionSeverity(status = "") {
    if (status === "broken") {
      return "blocker";
    }
    if (status === "unreachable") {
      return "warn";
    }
    return "tip";
  }

  function getRouteExecutionTitle(item = {}) {
    if (item.title) {
      return item.title;
    }
    if (item.status === "broken") {
      return "修复分支坏链";
    }
    if (item.status === "unreachable") {
      return item.kind === "ending" ? "接通结局入口" : "接通不可达目标";
    }
    return item.kind === "ending" ? "完整跑通结局" : "覆盖分支用例";
  }

  function getRouteExecutionActionLabel(item = {}) {
    if (item.actionLabel) {
      return item.actionLabel;
    }
    if (item.status === "broken") {
      return "重新选择目标场景";
    }
    if (item.status === "unreachable") {
      return "检查上游入口是否接回主路线";
    }
    return item.kind === "ending" ? "从入口完整跑到该结局" : "从入口跑到这里并点击该分支";
  }

  function getRouteExecutionAcceptance(item = {}) {
    if (item.acceptanceCriteria) {
      return item.acceptanceCriteria;
    }
    if (item.status === "broken") {
      return "修复后重新生成路线试玩手册，确认状态变为可试玩。";
    }
    if (item.status === "unreachable") {
      return "补齐入口后重新检查，确认玩家能自然进入目标场景。";
    }
    return item.kind === "ending"
      ? "确认结尾、解锁、回想、存档和返回标题都正常。"
      : "确认文本、演出、存档和变量后果正常。";
  }

  function buildRouteExecutionQueueFromPlan(routeTestingPlan = {}) {
    const existingQueue = toArray(routeTestingPlan.executionQueue);
    if (existingQueue.length) {
      return existingQueue;
    }

    const queue = [];
    toArray(routeTestingPlan.decisionPoints).forEach((point, pointIndex) => {
      toArray(point.routeCases).forEach((routeCase, routeIndex) => {
        const status = cleanText(routeCase.status, "ready");
        if (status === "ready") {
          return;
        }
        const severity = getRouteExecutionSeverity(status);
        queue.push({
          id: `route_${point.sceneId || pointIndex}_${routeIndex + 1}`,
          kind: "branch",
          severity,
          status,
          title: getRouteExecutionTitle({ status, kind: "branch" }),
          actionLabel: getRouteExecutionActionLabel({ status, kind: "branch" }),
          acceptanceCriteria: getRouteExecutionAcceptance({ status, kind: "branch" }),
          chapterName: point.chapterName,
          sceneName: point.sceneName,
          routeLabel: routeCase.label,
          targetLabel: routeCase.targetSceneName,
        });
      });
    });

    toArray(routeTestingPlan.endingTestCases).forEach((testCase, index) => {
      const status = cleanText(testCase.status, "ready");
      if (status === "ready") {
        return;
      }
      const severity = getRouteExecutionSeverity(status);
      queue.push({
        id: `ending_${testCase.sceneId || index}`,
        kind: "ending",
        severity,
        status,
        title: getRouteExecutionTitle({ status, kind: "ending" }),
        actionLabel: testCase.testingHint || getRouteExecutionActionLabel({ status, kind: "ending" }),
        acceptanceCriteria: getRouteExecutionAcceptance({ status, kind: "ending" }),
        chapterName: testCase.chapterName,
        sceneName: testCase.sceneName,
        routeLabel: "结局路径",
        targetLabel: testCase.sceneName,
      });
    });

    return queue;
  }

  function addRouteExecutionTasks(tasks, routeTestingPlan = {}) {
    buildRouteExecutionQueueFromPlan(routeTestingPlan)
      .filter((item) => item && item.status !== "ready")
      .slice(0, 12)
      .forEach((item) => {
        addTask(tasks, {
          area: "route",
          severity: item.severity === "blocker" ? "blocker" : "warn",
          title: item.title ?? (item.kind === "ending" ? "接通结局路径" : "处理路线点测问题"),
          detail: cleanText(
            `${item.actionLabel ?? "处理路线用例"}。${item.acceptanceCriteria ?? ""}`,
            "处理路线执行队列里的阻塞项。"
          ),
          source: cleanText(`${item.chapterName ?? ""} / ${item.sceneName ?? ""} / ${item.routeLabel ?? ""} -> ${item.targetLabel ?? ""}`, "路线执行队列"),
          action: AREA_ACTIONS.route,
          priorityBoost: item.severity === "blocker" ? 24 : 14,
        });
      });
  }

  function addAudioProductionTasks(tasks, audioCueSheet = {}) {
    toArray(audioCueSheet.productionQueue)
      .filter((item) => item && item.severity !== "good")
      .slice(0, 12)
      .forEach((item) => {
        addTask(tasks, {
          area: "audio",
          severity: item.severity,
          title: item.title ?? "处理音频制作任务",
          detail: cleanText(
            `${item.actionLabel ?? "处理音频任务"}。${item.detail ?? ""}`,
            "处理音频生产队列里的任务。"
          ),
          source: item.targetLabel ?? "音频制作队列",
          action: AREA_ACTIONS.audio,
          priorityBoost: item.severity === "blocker" ? 18 : item.severity === "warn" ? 9 : 4,
        });
      });
  }

  function addDirectorCueTasks(tasks, directorCueSheet = {}) {
    toArray(directorCueSheet.productionQueue)
      .filter((item) => item && item.severity !== "good")
      .slice(0, 12)
      .forEach((item) => {
        addTask(tasks, {
          area: "director",
          severity: item.severity,
          title: item.title ?? "处理导演分镜任务",
          detail: cleanText(
            `${item.actionLabel ?? "处理分镜任务"}。${item.detail ?? ""}`,
            "处理导演分镜清单里的制作任务。"
          ),
          source: item.targetLabel ?? cleanText(`${item.chapterName ?? ""} / ${item.sceneName ?? ""}`, "导演分镜清单"),
          action: AREA_ACTIONS.director,
          priorityBoost: item.severity === "blocker" ? 20 : item.severity === "warn" ? 11 : 5,
        });
      });
  }

  function formatBacklogDuration(seconds) {
    const safeSeconds = Math.max(0, Math.round(Number(seconds) || 0));
    if (safeSeconds <= 0) {
      return "约 0 秒";
    }
    if (safeSeconds < 60) {
      return `约 ${safeSeconds} 秒`;
    }
    const minutes = Math.floor(safeSeconds / 60);
    const remainingSeconds = safeSeconds % 60;
    return remainingSeconds > 0 ? `约 ${minutes}分${remainingSeconds}秒` : `约 ${minutes} 分钟`;
  }

  function getTimingCount(summary = {}, scenes = [], key, tone) {
    return toCount(summary[key], toArray(scenes).filter((scene) => cleanText(scene?.timingTone) === tone).length);
  }

  function getTimingLabel(summary = {}, labelKey, secondsKey) {
    return cleanText(summary[labelKey]) || formatBacklogDuration(summary[secondsKey]);
  }

  function getTimingSceneExamples(directorCueSheet = {}, tone, maxItems = 3) {
    return toArray(directorCueSheet.scenes)
      .filter((scene) => cleanText(scene?.timingTone) === tone)
      .slice(0, maxItems)
      .map((scene) => {
        const target = cleanText(`${scene.chapterName ?? ""} / ${scene.sceneName ?? ""}`, "未命名场景");
        const timing = cleanText(scene.durationLabel ?? scene.timingBrief);
        return timing ? `${target}（${timing}）` : target;
      })
      .join("；");
  }

  function addDirectorTimingTasks(tasks, directorCueSheet = {}) {
    const summary = directorCueSheet.summary ?? {};
    const scenes = toArray(directorCueSheet.scenes);
    const shortSceneCount = getTimingCount(summary, scenes, "shortSceneCount", "short");
    const longSceneCount = getTimingCount(summary, scenes, "longSceneCount", "long");
    const silentSceneCount = getTimingCount(summary, scenes, "silentSceneCount", "silent");
    const sceneCount = toCount(summary.sceneCount, scenes.length);
    const totalEstimatedLabel = getTimingLabel(summary, "totalEstimatedLabel", "totalEstimatedSeconds");
    const averageSceneLabel = getTimingLabel(summary, "averageSceneLabel", "averageSceneSeconds");

    if (silentSceneCount > 0) {
      const examples = getTimingSceneExamples(directorCueSheet, "silent");
      addTask(tasks, {
        area: "presentation",
        severity: "warn",
        title: "补齐空白场景内容",
        detail: cleanText(
          `导演分镜发现 ${silentSceneCount} 个场景几乎没有正文或媒体，可能是占位场景误入发布包。${examples ? `优先检查：${examples}。` : ""}`,
          "复查导演分镜里没有正文或媒体的场景。"
        ),
        source: `${sceneCount} 个场景的时长复查`,
        count: silentSceneCount,
        action: AREA_ACTIONS.presentation,
        priorityBoost: 16,
      });
    }

    if (longSceneCount > 0) {
      const examples = getTimingSceneExamples(directorCueSheet, "long");
      addTask(tasks, {
        area: "presentation",
        severity: "warn",
        title: "拆分过长场景节奏",
        detail: cleanText(
          `预计总时长 ${totalEstimatedLabel}，平均每场 ${averageSceneLabel}；其中 ${longSceneCount} 个场景偏长。${examples ? `优先检查：${examples}。` : ""}`,
          "复查过长场景，必要时拆分为多个镜头、选项或演出段落。"
        ),
        source: "导演分镜时长估算",
        count: longSceneCount,
        action: AREA_ACTIONS.presentation,
        priorityBoost: 12,
      });
    }

    if (shortSceneCount > 0) {
      const examples = getTimingSceneExamples(directorCueSheet, "short");
      addTask(tasks, {
        area: "presentation",
        severity: "tip",
        title: "复查过短场景节奏",
        detail: cleanText(
          `有 ${shortSceneCount} 个场景预计很快结束，发布前建议确认它们是刻意的转场、演出停顿或短分支。${examples ? `优先检查：${examples}。` : ""}`,
          "复查过短场景是否缺少正文、等待时间或转场演出。"
        ),
        source: "导演分镜时长估算",
        count: shortSceneCount,
        action: AREA_ACTIONS.presentation,
        priorityBoost: 6,
      });
    }
  }

  function getRuntimePreloadPriorityBoost(warning = {}) {
    const code = cleanText(warning.code);
    if (code === "critical_missing_assets") {
      return 28;
    }
    if (code === "critical_over_budget") {
      return 24;
    }
    if (code === "single_asset_over_budget") {
      return 18;
    }
    if (code === "early_over_budget" || code === "scene_hotspot") {
      return 14;
    }
    return normalizeSeverity(warning.severity) === "blocker" ? 18 : 8;
  }

  function addRuntimePreloadBudgetTasks(tasks, runtimePreloadBudget = {}) {
    const warnings = toArray(runtimePreloadBudget.warnings)
      .filter((warning) => normalizeSeverity(warning?.severity) !== "good")
      .sort((left, right) => {
        const severityDelta =
          getSeverityWeight(normalizeSeverity(right?.severity)) - getSeverityWeight(normalizeSeverity(left?.severity));
        if (severityDelta !== 0) {
          return severityDelta;
        }
        return getRuntimePreloadPriorityBoost(right) - getRuntimePreloadPriorityBoost(left);
      })
      .slice(0, 10);

    warnings.forEach((warning) => {
      addTask(tasks, {
        area: "loading",
        severity: warning.severity,
        title: warning.title ?? "处理首屏加载压力",
        detail: cleanText(
          `${warning.detail ?? ""}${warning.actionHint ? ` 建议：${warning.actionHint}` : ""}`,
          "处理入口场景或早期路线里的加载压力。"
        ),
        source: cleanText(warning.assetName || warning.sceneName, "Runtime 首屏加载预算"),
        action: AREA_ACTIONS.loading,
        priorityBoost: getRuntimePreloadPriorityBoost(warning),
      });
    });

    if (!warnings.length && normalizeSeverity(runtimePreloadBudget.releaseRiskLevel) !== "good") {
      addTask(tasks, {
        area: "loading",
        severity: runtimePreloadBudget.releaseRiskLevel,
        title: "复核 Runtime 首屏加载预算",
        detail: "当前首屏加载预算存在风险，但没有细分到具体提醒。建议打开预算报告确认入口场景素材压力。",
        source: "Runtime 首屏加载预算",
        action: AREA_ACTIONS.loading,
        priorityBoost: 10,
      });
    }
  }

  function addVnEssentialsTasks(tasks, essentials = {}) {
    toArray(essentials.issues)
      .filter((issue) => normalizeSeverity(issue?.severity) !== "good")
      .slice(0, 12)
      .forEach((issue) => {
        const issueArea = cleanText(issue.area, "runtime");
        const area = VN_ESSENTIAL_BACKLOG_AREAS[issueArea] || "runtime";
        const severity = issue.severity === "warn" ? "warn" : "tip";
        addTask(tasks, {
          area,
          severity,
          title: issue.title ?? "处理视觉小说基础能力缺口",
          detail: cleanText(
            `${issue.detail ?? ""}${issue.suggestion ? ` 建议：${issue.suggestion}` : ""}`,
            "把这项基础能力补齐后，再导出试玩包确认。"
          ),
          source: "VN 基础能力成熟度",
          action: area === "runtime" ? AREA_ACTIONS.runtime : AREA_ACTIONS[area],
          priorityBoost: severity === "warn" ? 18 : 6,
        });
      });
  }

  function addRouteTasks(tasks, routeOverview = {}) {
    const metrics = routeOverview.metrics ?? {};
    const brokenRoutes = toCount(metrics.brokenRoutes);
    const unreachableScenes = toCount(metrics.unreachableScenes);
    const orphanScenes = toCount(metrics.orphanScenes);
    if (brokenRoutes > 0) {
      addTask(tasks, {
        area: "route",
        severity: "blocker",
        title: "修复坏路线",
        detail: `当前还有 ${brokenRoutes} 条跳转目标异常或断链，可能直接打断试玩。`,
        source: "路线图",
        count: brokenRoutes,
        priorityBoost: 18,
      });
    }
    if (unreachableScenes > 0) {
      addTask(tasks, {
        area: "route",
        severity: "warn",
        title: "处理入口不可达场景",
        detail: `入口实际走不到 ${unreachableScenes} 个场景，建议补跳转或确认是否要保留。`,
        source: "路线图",
        count: unreachableScenes,
        priorityBoost: 12,
      });
    }
    if (orphanScenes > 0) {
      addTask(tasks, {
        area: "route",
        severity: "warn",
        title: "处理孤立场景",
        detail: `还有 ${orphanScenes} 个场景没有被路线连接，发布前最好明确入口。`,
        source: "路线图",
        count: orphanScenes,
        priorityBoost: 10,
      });
    }
  }

  function summarizeAreas(tasks = []) {
    const areaMap = new Map();
    toArray(tasks).forEach((task) => {
      const area = task.area || "scene";
      const record =
        areaMap.get(area) ??
        {
          area,
          areaLabel: task.areaLabel || AREA_LABELS[area] || area,
          taskCount: 0,
          blockerCount: 0,
          warningCount: 0,
          tipCount: 0,
          topSeverity: "good",
        };
      record.taskCount += 1;
      if (task.severity === "blocker") {
        record.blockerCount += 1;
        record.topSeverity = "blocker";
      } else if (task.severity === "warn") {
        record.warningCount += 1;
        if (record.topSeverity !== "blocker") {
          record.topSeverity = "warn";
        }
      } else {
        record.tipCount += 1;
        if (record.topSeverity === "good") {
          record.topSeverity = "tip";
        }
      }
      areaMap.set(area, record);
    });
    return Array.from(areaMap.values()).sort((left, right) => {
      if (right.blockerCount !== left.blockerCount) {
        return right.blockerCount - left.blockerCount;
      }
      if (right.warningCount !== left.warningCount) {
        return right.warningCount - left.warningCount;
      }
      return right.taskCount - left.taskCount || left.areaLabel.localeCompare(right.areaLabel, "zh-CN");
    });
  }

  function buildProductionBacklog(context = {}) {
    const tasks = [];
    addRouteTasks(tasks, context.routeOverview);
    addRouteExecutionTasks(tasks, context.routeOverview?.routeTestingPlan);
    addIssueTasks(tasks, "scene", context.sceneBoard?.issues, { fallbackTitle: "处理场景制作问题", fallbackSource: "场景生产看板" });
    addDirectorCueTasks(tasks, context.directorCueSheet);
    addDirectorTimingTasks(tasks, context.directorCueSheet);
    addIssueTasks(tasks, "voice", context.voiceSheet?.issues, { fallbackTitle: "处理语音制作问题", fallbackSource: "语音制作清单" });
    addIssueTasks(tasks, "choice", context.choiceConsequenceSheet?.issues, { fallbackTitle: "处理选项问题", fallbackSource: "选项后果表" });
    addIssueTasks(tasks, "variable", context.variableInfluenceSheet?.issues, { fallbackTitle: "处理变量问题", fallbackSource: "变量影响表" });
    addIssueTasks(tasks, "asset", context.assetDependencySheet?.issues, { fallbackTitle: "处理素材依赖问题", fallbackSource: "素材依赖表" });
    addIssueTasks(tasks, "rights", context.assetRightsSheet?.issues, { fallbackTitle: "补素材授权信息", fallbackSource: "素材授权清单", maxItems: 8 });
    addAudioProductionTasks(tasks, context.audioCueSheet);
    addIssueTasks(tasks, "audio", context.audioCueSheet?.issues, { fallbackTitle: "处理音频调度问题", fallbackSource: "音频调度表" });
    addIssueTasks(tasks, "stage", context.stageDirectionSheet?.issues, { fallbackTitle: "处理角色调度问题", fallbackSource: "角色舞台调度表" });
    addStageContinuityTasks(tasks, context.stageDirectionSheet);
    addIssueTasks(tasks, "presentation", context.presentationTimeline?.issues, { fallbackTitle: "处理演出节奏问题", fallbackSource: "演出时间轴" });
    addIssueTasks(tasks, "localization", context.localizationCoverage?.issues, { fallbackTitle: "处理翻译覆盖问题", fallbackSource: "多语言覆盖报告", maxItems: 8 });
    addIssueTasks(tasks, "runtime", context.runtimeCapabilityMatrix?.issues, { fallbackTitle: "处理 Runtime 覆盖风险", fallbackSource: "Runtime 覆盖矩阵", maxItems: 8, priorityBoost: 16 });
    addVnEssentialsTasks(tasks, context.runtimeCapabilityMatrix?.essentials);
    addRuntimePreloadBudgetTasks(tasks, context.runtimePreloadBudget);
    addIssueTasks(tasks, "unlockable", context.unlockableContentManifest?.issues, {
      fallbackTitle: "处理图鉴 / 回想内容缺口",
      fallbackSource: "可解锁内容清单",
      maxItems: 8,
      priorityBoost: 10,
    });

    tasks.sort((left, right) => {
      if (right.priority !== left.priority) {
        return right.priority - left.priority;
      }
      return left.areaLabel.localeCompare(right.areaLabel, "zh-CN") || left.title.localeCompare(right.title, "zh-CN");
    });
    tasks.forEach((task, index) => {
      task.id = `task_${index + 1}`;
    });

    const areaSummaries = summarizeAreas(tasks);
    const blockerCount = tasks.filter((task) => task.severity === "blocker").length;
    const warningCount = tasks.filter((task) => task.severity === "warn").length;
    const tipCount = tasks.filter((task) => task.severity === "tip").length;
    const readinessPenalty = Math.min(100, blockerCount * 18 + warningCount * 7 + tipCount * 2);

    return {
      projectTitle: cleanText(context.projectTitle, "Canvasia Project"),
      tasks,
      areaSummaries,
      summary: {
        taskCount: tasks.length,
        blockerCount,
        warningCount,
        tipCount,
        areaCount: areaSummaries.length,
        readinessPercent: Math.max(0, 100 - readinessPenalty),
        topAreaLabel: areaSummaries[0]?.areaLabel ?? "无",
        topAreaTaskCount: areaSummaries[0]?.taskCount ?? 0,
      },
      nextTask: tasks[0] ?? null,
    };
  }

  function getProductionBacklogStatusDigest(backlog = {}) {
    const summary = backlog.summary ?? {};
    if ((summary.taskCount ?? 0) === 0) {
      return {
        status: "ready",
        title: "生产待办已清空",
        detail: "当前跨模块巡检没有发现明显制作任务，可以继续写新内容或进入试玩确认。",
      };
    }
    if ((summary.blockerCount ?? 0) > 0) {
      return {
        status: "blocked",
        title: `${summary.blockerCount} 个先修任务`,
        detail: "先处理会断线、缺文件、坏引用或阻塞试玩的任务，再继续做润色项。",
      };
    }
    if ((summary.warningCount ?? 0) > 0) {
      return {
        status: "warn",
        title: `${summary.warningCount} 个优先任务`,
        detail: "项目可以继续制作，但建议先把这些影响完成度的任务按队列处理。",
      };
    }
    return {
      status: "soft",
      title: `${summary.tipCount ?? 0} 个润色任务`,
      detail: "没有明显阻塞项，剩下多是演出、文本密度或发布体验润色。",
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

  function buildProductionBacklogMarkdown(backlog = {}, options = {}) {
    const summary = backlog.summary ?? {};
    const digest = getProductionBacklogStatusDigest(backlog);
    const projectTitle = cleanText(options.projectTitle ?? backlog.projectTitle, "Canvasia Project");
    const generatedAt = cleanText(options.generatedAt);
    const areaRows = toArray(backlog.areaSummaries).map((area) => [
      area.areaLabel,
      area.taskCount,
      area.blockerCount,
      area.warningCount,
      area.tipCount,
      getSeverityLabel(area.topSeverity),
    ]);
    const taskRows = toArray(backlog.tasks).map((task, index) => [
      index + 1,
      task.severityLabel,
      task.areaLabel,
      task.title,
      task.source,
      task.detail,
      task.action?.label,
    ]);

    return [
      `# ${projectTitle} 生产待办队列`,
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
        ["任务", "先修", "优先", "润色", "覆盖模块", "生产就绪度", "最多任务区域"],
        [
          [
            summary.taskCount ?? 0,
            summary.blockerCount ?? 0,
            summary.warningCount ?? 0,
            summary.tipCount ?? 0,
            summary.areaCount ?? 0,
            `${summary.readinessPercent ?? 0}%`,
            `${summary.topAreaLabel ?? "无"} (${summary.topAreaTaskCount ?? 0})`,
          ],
        ]
      ),
      "",
      "## 模块分布",
      "",
      buildMarkdownTable(["模块", "任务", "先修", "优先", "润色", "最高级别"], areaRows) || "当前没有待办模块。",
      "",
      "## 任务队列",
      "",
      buildMarkdownTable(["序号", "优先级", "模块", "任务", "位置", "说明", "建议动作"], taskRows) || "当前没有制作待办。",
      "",
    ].join("\n");
  }

  function buildProductionBacklogCsv(backlog = {}) {
    const rows = toArray(backlog.tasks).map((task, index) => [
      index + 1,
      task.severityLabel,
      task.areaLabel,
      task.title,
      task.source,
      task.detail,
      task.action?.label,
      task.action?.screen,
    ]);
    return `\uFEFF${buildCsv(["序号", "优先级", "模块", "任务", "位置", "说明", "建议动作", "目标页面"], rows)}\n`;
  }

  global.CanvasiaEditorProductionBacklog = Object.freeze({
    buildProductionBacklog,
    getProductionBacklogStatusDigest,
    buildProductionBacklogMarkdown,
    buildProductionBacklogCsv,
    addRouteExecutionTasks,
    buildRouteExecutionQueueFromPlan,
    addAudioProductionTasks,
    addDirectorCueTasks,
    addDirectorTimingTasks,
    addStageContinuityTasks,
    addRuntimePreloadBudgetTasks,
    addVnEssentialsTasks,
    getSeverityLabel,
  });
})(typeof window !== "undefined" ? window : globalThis);
