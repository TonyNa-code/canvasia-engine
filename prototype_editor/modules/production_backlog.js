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
    unlockable: Object.freeze({ label: "看可解锁清单", action: "switch-screen", screen: "inspection" }),
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

  function addRouteExecutionTasks(tasks, routeTestingPlan = {}) {
    toArray(routeTestingPlan.executionQueue)
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
    addIssueTasks(tasks, "voice", context.voiceSheet?.issues, { fallbackTitle: "处理语音制作问题", fallbackSource: "语音制作清单" });
    addIssueTasks(tasks, "choice", context.choiceConsequenceSheet?.issues, { fallbackTitle: "处理选项问题", fallbackSource: "选项后果表" });
    addIssueTasks(tasks, "variable", context.variableInfluenceSheet?.issues, { fallbackTitle: "处理变量问题", fallbackSource: "变量影响表" });
    addIssueTasks(tasks, "asset", context.assetDependencySheet?.issues, { fallbackTitle: "处理素材依赖问题", fallbackSource: "素材依赖表" });
    addIssueTasks(tasks, "rights", context.assetRightsSheet?.issues, { fallbackTitle: "补素材授权信息", fallbackSource: "素材授权清单", maxItems: 8 });
    addAudioProductionTasks(tasks, context.audioCueSheet);
    addIssueTasks(tasks, "audio", context.audioCueSheet?.issues, { fallbackTitle: "处理音频调度问题", fallbackSource: "音频调度表" });
    addIssueTasks(tasks, "stage", context.stageDirectionSheet?.issues, { fallbackTitle: "处理角色调度问题", fallbackSource: "角色舞台调度表" });
    addIssueTasks(tasks, "presentation", context.presentationTimeline?.issues, { fallbackTitle: "处理演出节奏问题", fallbackSource: "演出时间轴" });
    addIssueTasks(tasks, "localization", context.localizationCoverage?.issues, { fallbackTitle: "处理翻译覆盖问题", fallbackSource: "多语言覆盖报告", maxItems: 8 });
    addIssueTasks(tasks, "runtime", context.runtimeCapabilityMatrix?.issues, { fallbackTitle: "处理 Runtime 覆盖风险", fallbackSource: "Runtime 覆盖矩阵", maxItems: 8, priorityBoost: 16 });
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
    addAudioProductionTasks,
    addDirectorCueTasks,
    getSeverityLabel,
  });
})(typeof window !== "undefined" ? window : globalThis);
