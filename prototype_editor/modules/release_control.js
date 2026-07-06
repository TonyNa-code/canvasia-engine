(function attachReleaseControlTools(global) {
  const DEFAULT_PROJECT_RELEASE_VERSION = "1.0.0-preview";
  const MISSING_VOICE_WARNING_MESSAGE = "这句台词还没有绑定语音。";
  const DESKTOP_EXPORT_TARGETS = Object.freeze(["windows_nwjs", "macos_nwjs", "linux_nwjs"]);

  function toCount(value, fallback = 0) {
    const numberValue = Number(value);
    if (!Number.isFinite(numberValue)) {
      return fallback;
    }
    return Math.max(0, Math.round(numberValue));
  }

  function toArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function normalizeResolution(resolution = {}) {
    return {
      width: toCount(resolution.width),
      height: toCount(resolution.height),
    };
  }

  function getReleaseSeverityLabel(severity) {
    switch (severity) {
      case "blocker":
        return "阻塞";
      case "warn":
        return "提醒";
      case "good":
        return "通过";
      default:
        return severity ? String(severity) : "未分级";
    }
  }

  function getReleaseStepToneLabel(tone) {
    switch (tone) {
      case "danger":
        return "先修";
      case "warn":
        return "优先";
      case "good":
        return "确认";
      default:
        return "收尾";
    }
  }

  function serializeReleaseReportAction(action) {
    if (!action) {
      return null;
    }
    return {
      label: action.label ?? "",
      action: action.action ?? "",
      href: action.href ?? "",
      screen: action.screen ?? "",
      sceneId: action.sceneId ?? "",
      blockId: action.blockId ?? "",
      characterId: action.characterId ?? "",
      chapterId: action.chapterId ?? "",
      assetId: action.assetId ?? "",
      dataset: action.dataset ?? {},
    };
  }

  function buildReleaseChecklistSummary(items = []) {
    const safeItems = Array.isArray(items) ? items : [];
    const blockerCount = safeItems.filter((item) => item?.severity === "blocker").length;
    const warnCount = safeItems.filter((item) => item?.severity === "warn").length;
    const readyCount = safeItems.filter((item) => item?.severity === "good").length;

    if (blockerCount > 0) {
      return {
        toneClass: "danger-text",
        badge: "先补阻塞项",
        title: `当前还有 ${blockerCount} 个发布阻塞项`,
        description: "这几个问题最容易直接影响正式交付，处理完成后再打正式包会更稳。",
        metrics: [
          ["阻塞项", `${blockerCount} 个`],
          ["提醒项", `${warnCount} 个`],
          ["已就绪", `${readyCount} 项`],
        ],
      };
    }

    if (warnCount > 0) {
      return {
        toneClass: "warn-text",
        badge: "基本可发",
        title: `当前没有硬阻塞，但还有 ${warnCount} 个待确认项`,
        description: "现在已经能继续导出，只是还有几项内容适合在正式交付前再确认一遍。",
        metrics: [
          ["阻塞项", "0 个"],
          ["提醒项", `${warnCount} 个`],
          ["已就绪", `${readyCount} 项`],
        ],
      };
    }

    return {
      toneClass: "good-text",
      badge: "可以交付",
      title: "当前这轮发布检查已经全部通过",
      description: "版本、分辨率、结构、素材缺口和桌面包状态目前都没有明显问题，可以继续打正式包。",
      metrics: [
        ["阻塞项", "0 个"],
        ["提醒项", "0 个"],
        ["已就绪", `${readyCount} 项`],
      ],
    };
  }

  function getReleaseChecklistCounts(items = []) {
    const safeItems = Array.isArray(items) ? items : [];
    return {
      blockerCount: safeItems.filter((item) => item?.severity === "blocker").length,
      warnCount: safeItems.filter((item) => item?.severity === "warn").length,
      readyCount: safeItems.filter((item) => item?.severity === "good").length,
      totalCount: safeItems.length,
    };
  }

  function getFirstReleaseAction(items = [], severity = "blocker") {
    const match = (Array.isArray(items) ? items : []).find((item) => item?.severity === severity && item?.action);
    return match?.action ?? null;
  }

  function hasObjectKey(source, key) {
    return Boolean(source && typeof source === "object" && Object.prototype.hasOwnProperty.call(source, key));
  }

  function getProductionBacklogGateSignal(context = {}) {
    const backlog = context.productionBacklog && typeof context.productionBacklog === "object" ? context.productionBacklog : {};
    const summary =
      context.productionBacklogSummary && typeof context.productionBacklogSummary === "object"
        ? context.productionBacklogSummary
        : backlog.summary && typeof backlog.summary === "object"
          ? backlog.summary
          : {};
    const nextTask =
      context.productionBacklogNextTask && typeof context.productionBacklogNextTask === "object"
        ? context.productionBacklogNextTask
        : backlog.nextTask && typeof backlog.nextTask === "object"
          ? backlog.nextTask
          : null;
    const available =
      hasObjectKey(summary, "taskCount") ||
      hasObjectKey(summary, "blockerCount") ||
      hasObjectKey(summary, "warningCount") ||
      hasObjectKey(summary, "tipCount");

    return {
      available,
      taskCount: available ? toCount(summary.taskCount) : 0,
      blockerCount: available ? toCount(summary.blockerCount) : 0,
      warningCount: available ? toCount(summary.warningCount) : 0,
      tipCount: available ? toCount(summary.tipCount) : 0,
      nextTask,
    };
  }

  function getProductionBacklogGateDetail(signal = {}) {
    if (!signal.available) {
      return "生产待办尚未生成。";
    }
    if (signal.taskCount <= 0) {
      return "生产待办已经清空。";
    }
    return `生产待办还有 ${signal.blockerCount} 个先修、${signal.warningCount} 个优先、${signal.tipCount} 个润色。`;
  }

  function getProductionBacklogGateAction(signal = {}) {
    const taskAction = signal.nextTask?.action;
    if (taskAction && typeof taskAction === "object") {
      return taskAction;
    }
    return { label: "打开项目巡检", action: "switch-screen", screen: "inspection" };
  }

  function serializeProductionBacklogTask(task = null) {
    if (!task || typeof task !== "object") {
      return null;
    }
    return {
      title: task.title ?? "",
      source: task.source ?? "",
      detail: task.detail ?? "",
      areaLabel: task.areaLabel ?? "",
      severityLabel: task.severityLabel ?? "",
      action: serializeReleaseReportAction(task.action),
    };
  }

  function formatProductionBacklogTaskHint(task = null) {
    const serialized = serializeProductionBacklogTask(task);
    if (!serialized) {
      return "";
    }
    const source = serialized.source ? `位置：${serialized.source}。` : "";
    const detail = serialized.detail ? `说明：${serialized.detail}` : "";
    return [source, detail].filter(Boolean).join(" ");
  }

  function buildProductionBacklogGateItems(signal = {}, status = "blocked") {
    if (!signal.available) {
      return [];
    }
    if (status === "blocked" && signal.blockerCount > 0) {
      return [
        {
          title: signal.nextTask?.title ? `生产待办：${signal.nextTask.title}` : "清空生产待办先修项",
          description: `${getProductionBacklogGateDetail(signal)}公开发布前建议先清空先修任务。`,
          action: getProductionBacklogGateAction(signal),
        },
      ];
    }
    if (status === "preview" && signal.warningCount > 0) {
      return [
        {
          title: "确认生产待办优先项",
          description: `${getProductionBacklogGateDetail(signal)}Preview 可以带说明发布，但正式发布前建议继续处理。`,
          action: getProductionBacklogGateAction(signal),
        },
      ];
    }
    return [];
  }

  function buildProductionBacklogFixStep(context = {}) {
    const signal = getProductionBacklogGateSignal(context);
    if (!signal.available || signal.taskCount <= 0) {
      return null;
    }
    const primaryAction = getProductionBacklogGateAction(signal);
    const actions = [
      {
        ...primaryAction,
        label: primaryAction.label || "处理下一项生产待办",
      },
      { label: "导出生产待办队列", action: "export-production-backlog-markdown" },
    ];
    const statusLabel = `先修 ${signal.blockerCount} / 优先 ${signal.warningCount} / 润色 ${signal.tipCount}`;
    const nextTaskLabel = signal.nextTask?.title ? `下一项：${signal.nextTask.title}。` : "";
    const nextTaskHint = formatProductionBacklogTaskHint(signal.nextTask);
    const productionBacklogTask = serializeProductionBacklogTask(signal.nextTask);

    if (signal.blockerCount > 0) {
      return {
        tone: "danger",
        title: "处理生产待办先修项",
        statusLabel,
        description: `${nextTaskLabel}${nextTaskHint ? `${nextTaskHint} ` : ""}这些先修项来自跨模块制作队列，可能包含缺文件、坏引用、授权、节奏或 Runtime 交付风险。`,
        productionBacklogTask,
        actions,
      };
    }
    if (signal.warningCount > 0) {
      return {
        tone: "warn",
        title: "确认生产待办优先项",
        statusLabel,
        description: `${nextTaskLabel}${nextTaskHint ? `${nextTaskHint} ` : ""}当前没有生产先修项，但这些优先项会影响 Preview 的完成度和观感。`,
        productionBacklogTask,
        actions,
      };
    }
    if (signal.tipCount > 0) {
      return {
        tone: "soft",
        title: "收尾生产待办润色项",
        statusLabel,
        description: `${nextTaskLabel}${nextTaskHint ? `${nextTaskHint} ` : ""}剩余多为润色项，适合在正式发布前做最后一轮体验打磨。`,
        productionBacklogTask,
        actions,
      };
    }
    return null;
  }

  function buildGateChecklistItems(items = [], releaseFixOrder = null, status = "blocked", productionBacklogSignal = {}) {
    const safeItems = Array.isArray(items) ? items : [];
    const priorityItems =
      status === "blocked"
        ? safeItems.filter((item) => item?.severity === "blocker")
        : safeItems.filter((item) => item?.severity === "warn");
    const productionItems = buildProductionBacklogGateItems(productionBacklogSignal, status);
    const combinedItems = [...priorityItems, ...productionItems];
    if (combinedItems.length > 0) {
      return combinedItems.slice(0, 3).map((item) => ({
        label: item.title ?? "待处理项",
        detail: item.description ?? item.status ?? "发布前建议处理。",
        done: false,
        action: serializeReleaseReportAction(item.action),
      }));
    }
    const fixSteps = Array.isArray(releaseFixOrder?.steps) ? releaseFixOrder.steps : [];
    return fixSteps.slice(0, 3).map((step) => ({
      label: step.title ?? "发布前收尾",
      detail: step.description ?? step.statusLabel ?? "继续完成这一步。",
      done: step.tone === "good",
      action: serializeReleaseReportAction(step.actions?.[0]),
    }));
  }

  function buildFinalPublishGate(context = {}) {
    const releaseChecklistItems = Array.isArray(context.releaseChecklistItems) ? context.releaseChecklistItems : [];
    const releaseFixOrder = context.releaseFixOrder ?? null;
    const exportResult = context.exportResult ?? null;
    const regressionSummary = context.regressionResult?.summary ?? context.regressionSummary ?? null;
    const hasRegressionRun = Boolean(context.regressionResult || context.hasRegressionRun);
    const regressionFailCount = toCount(regressionSummary?.failCount);
    const regressionWarnCount = toCount(regressionSummary?.warnCount);
    const { blockerCount, warnCount, readyCount, totalCount } = getReleaseChecklistCounts(releaseChecklistItems);
    const productionBacklogSignal = getProductionBacklogGateSignal(context);
    const productionBlockerCount = productionBacklogSignal.blockerCount;
    const productionWarnCount = productionBacklogSignal.warningCount;
    const totalBlockerCount = blockerCount + regressionFailCount + productionBlockerCount;
    const totalWarnCount = warnCount + regressionWarnCount + (hasRegressionRun ? 0 : 1) + productionWarnCount;
    const hasBlockers = totalBlockerCount > 0;
    const hasWarnings = totalWarnCount > 0;
    const status = hasBlockers ? "blocked" : hasWarnings ? "preview" : "ready";
    const firstBlockerAction = getFirstReleaseAction(releaseChecklistItems, "blocker");
    const firstWarnAction = getFirstReleaseAction(releaseChecklistItems, "warn");
    const productionBacklogAction = getProductionBacklogGateAction(productionBacklogSignal);
    const exportLabel = exportResult?.targetLabel || exportResult?.target || "尚未导出";
    const primaryAction =
      status === "blocked"
        ? firstBlockerAction || (productionBlockerCount > 0 ? productionBacklogAction : null) || releaseFixOrder?.steps?.[0]?.actions?.[0] || { label: "一键生成修复顺序", action: "generate-release-fix-order" }
        : status === "preview"
          ? (!hasRegressionRun
              ? { label: "先跑自动回归试玩", action: "run-preview-regression" }
              : firstWarnAction || (productionWarnCount > 0 ? productionBacklogAction : null) || { label: "导出发布总控报告", action: "export-release-control-report" })
          : { label: "导出发布总控报告", action: "export-release-control-report" };
    const secondaryActions =
      status === "ready"
        ? [
            { label: "导出网页包", action: "export-build", dataset: { "export-target": "web" } },
            { label: "导出原生 Runtime", action: "export-build", dataset: { "export-target": "native_runtime" } },
          ]
        : [
            { label: "导出巡检报告", action: "export-inspection-report" },
            { label: "导出发布总控 JSON", action: "export-release-control-json" },
          ];

    return {
      status,
      tone: status === "blocked" ? "danger" : status === "preview" ? "warn" : "good",
      badge: status === "blocked" ? "暂缓发布" : status === "preview" ? "可发 Preview" : "可以公开发布",
      title:
        status === "blocked"
          ? `暂缓公开发布：还有 ${totalBlockerCount} 个阻塞项`
          : status === "preview"
            ? "可以发布 Preview，但建议先确认提醒项"
            : "可以进入公开发布流程",
      description:
        status === "blocked"
          ? "这些问题可能造成断线、缺素材、制作先修未完成、包体异常或回归失败。建议先按门禁里的主按钮处理，再重新导出。"
          : status === "preview"
            ? "当前没有硬阻塞，适合按 Preview / Early Access 口径发布；如果想更稳，先把提醒和回归试玩补齐。"
            : "当前发布检查、回归和导出状态都比较干净，可以开始整理 GitHub Release 附件和发布说明。",
      metrics: [
        { label: "阻塞", value: `${totalBlockerCount} 个`, hint: "公开发布前建议清零" },
        { label: "提醒", value: `${totalWarnCount} 个`, hint: "Preview 可带说明发布" },
        { label: "通过", value: `${readyCount}/${totalCount}`, hint: "发布检查清单已就绪项" },
        { label: "最近导出", value: exportLabel, hint: hasRegressionRun ? "已跑过自动回归" : "还没跑自动回归" },
        ...(productionBacklogSignal.available
          ? [
              {
                label: "生产待办",
                value: `${productionBacklogSignal.taskCount} 项`,
                hint: getProductionBacklogGateDetail(productionBacklogSignal),
              },
            ]
          : []),
      ],
      primaryAction: serializeReleaseReportAction(primaryAction),
      secondaryActions: secondaryActions.map(serializeReleaseReportAction).filter(Boolean),
      checklist: buildGateChecklistItems(releaseChecklistItems, releaseFixOrder, status, productionBacklogSignal),
    };
  }

  function formatReleaseReportNextStepActionHint(nextStep) {
    const actionLabel = nextStep?.action?.label;
    return actionLabel ? `建议按钮：${actionLabel}。` : "";
  }

  function formatReleaseReportNextStepAdvice(nextStep) {
    const actionHint = formatReleaseReportNextStepActionHint(nextStep);
    if (nextStep?.source === "release_fix_order") {
      return `先处理「${nextStep.title}」，再重新导出一版原生 Runtime / 桌面包确认。${actionHint}`;
    }
    if (nextStep?.source === "project_milestone_gap") {
      return `发布修复队列暂时没有硬阻塞；先补「${nextStep.title}」，再重新巡检和试玩。${actionHint}`;
    }
    return "当前没有明显阻塞，可以直接做最终试玩和正式导出。";
  }

  function completeReleaseReportNextStep(nextStep) {
    const actionHint = formatReleaseReportNextStepActionHint(nextStep);
    const advice = formatReleaseReportNextStepAdvice(nextStep);
    return {
      ...nextStep,
      actionHint,
      advice,
      sourceLabel:
        nextStep?.source === "release_fix_order"
          ? "发布修复顺序"
          : nextStep?.source === "project_milestone_gap"
            ? "成品目标路线"
            : "最终确认",
      tone:
        nextStep?.source === "release_fix_order"
          ? "warn"
          : nextStep?.source === "project_milestone_gap"
            ? "soft"
            : "good",
    };
  }

  function buildReleaseReportNextStep(releaseFixOrder = null, projectMilestoneGapDigest = null) {
    const firstReleaseStep = releaseFixOrder?.steps?.[0];
    if (firstReleaseStep) {
      return completeReleaseReportNextStep({
        title: firstReleaseStep.title,
        description: firstReleaseStep.description,
        statusLabel: firstReleaseStep.statusLabel,
        action: serializeReleaseReportAction(firstReleaseStep.actions?.[0] ?? null),
        source: "release_fix_order",
      });
    }

    if (projectMilestoneGapDigest && projectMilestoneGapDigest.status !== "ready") {
      const primaryGap = projectMilestoneGapDigest?.primaryGap;
      const action = primaryGap?.action ?? projectMilestoneGapDigest?.nextAction ?? null;
      return completeReleaseReportNextStep({
        title: primaryGap?.label ?? projectMilestoneGapDigest?.title ?? "继续推进成品目标路线",
        description:
          primaryGap?.missing ??
          projectMilestoneGapDigest?.description ??
          "先按成品目标路线补齐当前阶段，再重新巡检和试玩。",
        statusLabel: projectMilestoneGapDigest?.eyebrow ?? "当前阶段缺口",
        action: serializeReleaseReportAction(action),
        source: "project_milestone_gap",
      });
    }

    return completeReleaseReportNextStep({
      title: "最终试玩和正式导出",
      description: "当前没有明显阻塞，可以直接做最终试玩和正式导出。",
      statusLabel: "可以继续",
      action: null,
      source: "release_ready",
    });
  }

  function splitReleaseWarnings(warningIssues = []) {
    const safeWarnings = Array.isArray(warningIssues) ? warningIssues : [];
    return {
      missingVoiceWarnings: safeWarnings.filter((issue) => issue?.message === MISSING_VOICE_WARNING_MESSAGE),
      nonVoiceWarnings: safeWarnings.filter((issue) => issue?.message !== MISSING_VOICE_WARNING_MESSAGE),
    };
  }

  function isDesktopExportReady(exportResult = null) {
    return (
      DESKTOP_EXPORT_TARGETS.includes(exportResult?.target) &&
      exportResult?.runtimeMode === "nwjs" &&
      toCount(exportResult?.missingAssets) === 0
    );
  }

  function getRuntimePreloadBudgetRiskCount(report = {}) {
    const totals = report?.totals ?? {};
    const countedWarnings = toCount(totals.dangerCount) + toCount(totals.warnCount);
    if (countedWarnings > 0) {
      return countedWarnings;
    }
    return toArray(report?.warnings).filter((warning) => ["danger", "warn"].includes(warning?.severity)).length;
  }

  function getRuntimePreloadBudgetBlockerCount(report = {}) {
    const totals = report?.totals ?? {};
    const countedDangers = toCount(totals.dangerCount);
    if (countedDangers > 0) {
      return countedDangers;
    }
    return toArray(report?.warnings).filter((warning) => warning?.severity === "danger").length;
  }

  function getRuntimePreloadBudgetPrimaryIssue(report = {}) {
    const warnings = toArray(report?.warnings);
    const warningIssue = warnings.find((warning) => warning?.severity === "danger") || warnings.find((warning) => warning?.severity === "warn");
    if (warningIssue) {
      return warningIssue;
    }

    const topEntry = toArray(report?.topEntries).find((entry) => entry?.name);
    if (!topEntry) {
      return null;
    }

    return {
      title: "首屏预热素材偏重",
      detail: `${topEntry.name} 当前 ${topEntry.sizeLabel ?? "未知体积"}，位于 ${topEntry.sceneName || "首屏 / 早期路线"}。`,
      actionHint: "优先压缩入口场景的大图、长 BGM、OP 视频，或把非首屏素材延后到实际使用时加载。",
      assetId: topEntry.id,
    };
  }

  function getRuntimePreloadBudgetReleaseTitle(report = {}, digest = {}) {
    if (digest?.title) {
      return digest.title;
    }
    const level = report?.releaseRiskLevel ?? "ready";
    return level === "danger" ? "首屏压力偏高" : level === "warn" ? "开局建议瘦身" : "首屏加载健康";
  }

  function getRuntimePreloadBudgetReleaseDetail(report = {}, digest = {}) {
    if (digest?.detail) {
      return digest.detail;
    }
    const level = report?.releaseRiskLevel ?? "ready";
    if (level === "danger") {
      return "正式发包前建议先处理入口场景的大素材和缺文件。";
    }
    if (level === "warn") {
      return "当前没有硬阻塞，但开局路线值得做一轮压缩或延后加载。";
    }
    return "首屏和早期路线没有明显预热压力。";
  }

  function serializeRuntimePreloadBudgetForRelease(report = {}, digest = {}) {
    const critical = report?.phases?.critical ?? {};
    const early = report?.phases?.early ?? {};
    const totals = report?.totals ?? {};
    const title = getRuntimePreloadBudgetReleaseTitle(report, digest);
    const detail = getRuntimePreloadBudgetReleaseDetail(report, digest);
    const warningCount = getRuntimePreloadBudgetRiskCount(report);
    const dangerCount = getRuntimePreloadBudgetBlockerCount(report);
    const warnCount = Math.max(0, warningCount - dangerCount);
    const criticalBytesLabel = critical.bytesLabel ?? "0 B";
    const earlyBytesLabel = early.bytesLabel ?? "0 B";
    const totalLabel = totals.totalLabel ?? "0 B";
    const profileAdvice = report?.profileAdvice && typeof report.profileAdvice === "object" ? report.profileAdvice : {};
    const selectedProfileLabel = profileAdvice.selectedProfileLabel ?? report?.performanceProfile?.label ?? report?.budgets?.performanceProfileLabel ?? "标准 PC / 网页";
    const recommendedProfileLabel = profileAdvice.recommendedProfileLabel ?? selectedProfileLabel;
    const profileAdviceAction = toArray(profileAdvice.actions)[0] ?? "保持当前档位并继续复查首屏体积。";

    return {
      releaseRiskLevel: report?.releaseRiskLevel ?? "ready",
      title,
      detail,
      summaryLine: `${title}，首屏 ${criticalBytesLabel} / 早期 ${earlyBytesLabel}`,
      budgetLine: `${criticalBytesLabel} / ${earlyBytesLabel} / ${totalLabel}`,
      profileAdviceLine: `当前 ${selectedProfileLabel} / 推荐 ${recommendedProfileLabel}`,
      warningCount,
      dangerCount,
      warnCount,
      totalEntries: toCount(totals.totalEntries),
      totalBytes: toCount(totals.totalBytes),
      totalLabel,
      criticalBytes: toCount(critical.bytes),
      criticalBytesLabel,
      earlyBytes: toCount(early.bytes),
      earlyBytesLabel,
      phaseRows: toArray(report?.phaseList).map((phase) => [
        phase?.label ?? "",
        `${phase?.count ?? 0}`,
        phase?.bytesLabel ?? "0 B",
        phase?.budgetLabel ?? "未设置",
        `${phase?.missingFileCount ?? 0}`,
        phase?.overBudget ? "超过建议预算" : "正常",
      ]),
      warningRows: toArray(report?.warnings).slice(0, 12).map((warning) => [
        warning?.severity === "danger" ? "高风险" : warning?.severity === "warn" ? "提醒" : "提示",
        warning?.title ?? "",
        warning?.assetName || warning?.sceneName || "首屏 / 早期路线",
        warning?.detail ?? "",
        warning?.actionHint ?? "",
      ]),
      profileAdvice: {
        status: profileAdvice.status ?? "ok",
        severity: profileAdvice.severity ?? "pass",
        selectedProfile: profileAdvice.selectedProfile ?? "",
        selectedProfileLabel,
        recommendedProfile: profileAdvice.recommendedProfile ?? "",
        recommendedProfileLabel,
        criticalLabel: profileAdvice.criticalLabel ?? criticalBytesLabel,
        totalLabel: profileAdvice.totalLabel ?? totalLabel,
        videoEntryCount: toCount(profileAdvice.videoEntryCount),
        action: profileAdviceAction,
        reasons: toArray(profileAdvice.reasons),
        actions: toArray(profileAdvice.actions),
      },
      profileAdviceRows: [
        [
          profileAdvice.status ?? "ok",
          selectedProfileLabel,
          recommendedProfileLabel,
          profileAdvice.criticalLabel ?? criticalBytesLabel,
          profileAdvice.totalLabel ?? totalLabel,
          `${toCount(profileAdvice.videoEntryCount)}`,
          profileAdviceAction,
        ],
      ],
      warnings: toArray(report?.warnings).slice(0, 20).map((warning) => ({
        code: warning?.code ?? "",
        severity: warning?.severity ?? "",
        title: warning?.title ?? "",
        detail: warning?.detail ?? "",
        actionHint: warning?.actionHint ?? "",
        assetId: warning?.assetId ?? "",
        assetName: warning?.assetName ?? "",
        sceneId: warning?.sceneId ?? "",
        sceneName: warning?.sceneName ?? "",
      })),
      topEntries: toArray(report?.topEntries).slice(0, 20).map((entry) => ({
        assetId: entry?.id ?? "",
        name: entry?.name ?? "",
        type: entry?.type ?? "",
        typeLabel: entry?.typeLabel ?? "",
        phase: entry?.phase ?? "",
        sizeBytes: toCount(entry?.sizeBytes),
        sizeLabel: entry?.sizeLabel ?? "",
        fileExists: entry?.fileExists !== false,
        sceneId: entry?.sceneId ?? "",
        sceneName: entry?.sceneName ?? "",
        reason: entry?.reason ?? "",
      })),
    };
  }

  function getProductionBacklogOverviewValue(context = {}) {
    const backlog = context.productionBacklog && typeof context.productionBacklog === "object" ? context.productionBacklog : {};
    const summary =
      context.productionBacklogSummary && typeof context.productionBacklogSummary === "object"
        ? context.productionBacklogSummary
        : backlog.summary && typeof backlog.summary === "object"
          ? backlog.summary
          : null;
    if (!summary) {
      return "";
    }
    const taskCount = toCount(summary.taskCount);
    const blockerCount = toCount(summary.blockerCount);
    const warningCount = toCount(summary.warningCount);
    const tipCount = toCount(summary.tipCount);
    const readinessPercent = toCount(summary.readinessPercent);
    return taskCount > 0
      ? `${taskCount} 项，先修 ${blockerCount} / 优先 ${warningCount} / 润色 ${tipCount}，就绪度 ${readinessPercent}%`
      : `0 项，就绪度 ${readinessPercent || 100}%`;
  }

  function buildReleaseControlOverviewRows(context = {}) {
    const routeMetrics = context.routeMetrics ?? context.routeOverview?.metrics ?? {};
    const endingPaths = toArray(context.endingPaths ?? context.routeOverview?.endingPaths);
    const routeTestingSummary = context.routeTestingSummary ?? context.routeOverview?.routeTestingPlan?.summary ?? {};
    const projectMilestonePlan = context.projectMilestonePlan ?? {};
    const projectMilestoneGapDigest = context.projectMilestoneGapDigest ?? {};
    const mediaBudgetReport = context.mediaBudgetReport ?? {};
    const runtimePreloadBudgetRelease = context.runtimePreloadBudgetRelease ?? {};
    const productionBacklogOverviewValue = getProductionBacklogOverviewValue(context);
    const firstReachableEndingPathLabel =
      context.firstReachableEndingPathLabel ?? endingPaths.find((path) => path?.isReachable)?.pathLabel ?? "暂未接通";
    const nextMilestoneTitle = projectMilestonePlan.nextMilestone?.title ?? "继续推进当前项目";
    const milestoneScore = toCount(projectMilestonePlan.overallScore);

    return [
      ["结构错误", `${toCount(context.errorCount)} 项`],
      ["补充提醒", `${toCount(context.warningCount)} 项`],
      ["已引用缺口素材", `${toCount(context.urgentMissingAssetsCount)} 个`],
      ["素材预算风险", `${toCount(mediaBudgetReport.count)} 个，合计 ${mediaBudgetReport.totalLabel ?? "0 B"}`],
      ["首屏加载压力", runtimePreloadBudgetRelease.summaryLine ?? "首屏加载健康，首屏 0 B / 早期 0 B"],
      ["闲置素材", `${toCount(context.unusedAssetCount)} 个`],
      ...(productionBacklogOverviewValue ? [["生产待办", productionBacklogOverviewValue]] : []),
      ["入口场景", routeMetrics.entrySceneName ?? "暂未设置"],
      [
        "分支 / 收束 / 孤立场景",
        `${toCount(routeMetrics.branchingScenes)} / ${toCount(routeMetrics.endingScenes)} / ${toCount(routeMetrics.orphanScenes)}`,
      ],
      ["可打到结局", `${toCount(routeMetrics.reachableEndingScenes)} / ${toCount(routeMetrics.endingScenes)}`],
      ["第一条结局路径", firstReachableEndingPathLabel],
      [
        "可达 / 不可达 / 最长深度",
        `${toCount(routeMetrics.reachableScenes)} / ${toCount(routeMetrics.unreachableScenes)} / ${toCount(routeMetrics.maxRouteDepth)} 步`,
      ],
      [
        "路线试玩手册",
        `${toCount(routeTestingSummary.decisionPointCount)} 个分支点 / ${toCount(routeTestingSummary.routeCaseCount)} 条路线用例 / ${toCount(routeTestingSummary.endingTestCaseCount)} 个结局用例`,
      ],
      ["坏链数量", `${toCount(routeMetrics.brokenRoutes)} 条`],
      ["成品目标路线", `${nextMilestoneTitle}（${milestoneScore}%）`],
      [projectMilestoneGapDigest.eyebrow ?? "当前阶段缺口", projectMilestoneGapDigest.title ?? "继续补齐当前阶段"],
    ];
  }

  function buildRuntimePreloadBudgetFixStep(report = {}) {
    const riskCount = getRuntimePreloadBudgetRiskCount(report);
    if (riskCount <= 0) {
      return null;
    }

    const blockerCount = getRuntimePreloadBudgetBlockerCount(report);
    const primaryIssue = getRuntimePreloadBudgetPrimaryIssue(report);
    const critical = report?.phases?.critical ?? {};
    const early = report?.phases?.early ?? {};
    const totalLabel = report?.totals?.totalLabel ?? "未统计";

    return {
      tone: blockerCount > 0 ? "warn" : "soft",
      title: "处理首屏加载压力",
      statusLabel: blockerCount > 0 ? `高风险 ${blockerCount} 项` : `建议优化 ${riskCount} 项`,
      description: primaryIssue
        ? `${primaryIssue.detail}${primaryIssue.actionHint ? ` ${primaryIssue.actionHint}` : ""}`
        : `首屏 ${critical.bytesLabel ?? "0 B"}，早期路线 ${early.bytesLabel ?? "0 B"}，预热合计 ${totalLabel}；发布前建议先做一轮瘦身。`,
      actions: [
        { label: "查看首屏预算", action: "switch-screen", screen: "inspection" },
        { label: "导出瘦身建议", action: "export-runtime-preload-budget-markdown" },
      ],
    };
  }

  function buildCreativeQualityAudit(context = {}) {
    const quality = context.creativeQuality ?? {};
    const storySceneCount = toCount(quality.storySceneCount);
    const dialogueCount = toCount(quality.dialogueCount);
    const narrationCount = toCount(quality.narrationCount);
    const choiceCount = toCount(quality.choiceCount);
    const characterCount = toCount(quality.characterCount);
    const charactersWithSpriteCount = toCount(quality.charactersWithSpriteCount);
    const characterShowCount = toCount(quality.characterShowCount);
    const characterHideCount = toCount(quality.characterHideCount);
    const scenesWithBackground = toCount(quality.scenesWithBackground);
    const scenesWithMusic = toCount(quality.scenesWithMusic);
    const scenesWithEffects = toCount(quality.scenesWithEffects);
    const placeholderAssetCount = toCount(quality.placeholderAssetCount);
    const placeholderScriptCount = toCount(quality.placeholderScriptCount);
    const placeholderContentCount = placeholderAssetCount + placeholderScriptCount;
    const textBlockCount = dialogueCount + narrationCount + choiceCount;
    const textDensity = storySceneCount > 0 ? textBlockCount / storySceneCount : 0;
    const steps = [];

    if (placeholderContentCount > 0) {
      steps.push({
        tone: "warn",
        title: "替换 Demo 占位内容",
        statusLabel: `占位素材 ${placeholderAssetCount} 个 / 待补正文 ${placeholderScriptCount} 条`,
        description: "这些内容最容易让玩家觉得还停在样板阶段；发布前先换成自己的正式素材和正式台词。",
        actions: [
          placeholderScriptCount > 0
            ? { label: "去替换待补正文", action: "switch-screen", screen: "story" }
            : { label: "去替换占位素材", action: "switch-screen", screen: "assets" },
          {
            label: "重新巡检确认",
            action: "run-project-inspection",
          },
        ],
      });
    }

    if (characterCount > 0 && charactersWithSpriteCount < characterCount) {
      steps.push({
        tone: "warn",
        title: "补齐角色兜底立绘",
        statusLabel: `已配置 ${charactersWithSpriteCount}/${characterCount} 个角色`,
        description: "即使以后接 Live2D 或 3D，兜底立绘也能保证截图、存档、低配回退和导出包不空屏。",
        actions: [
          { label: "去角色页补立绘", action: "switch-screen", screen: "characters" },
          { label: "去素材页导入立绘", action: "switch-screen", screen: "assets" },
        ],
      });
    }

    if (dialogueCount >= 3 && characterShowCount === 0) {
      steps.push({
        tone: "warn",
        title: "补角色显示/隐藏演出",
        statusLabel: "还没有角色出场卡",
        description: "角色只在台词里说话但没有立绘入场，会让视觉小说的第一眼完成度偏低；先给主要角色补显示卡和位置。",
        actions: [
          { label: "去剧情页补角色显示", action: "switch-screen", screen: "story" },
          { label: "检查角色立绘", action: "switch-screen", screen: "characters" },
        ],
      });
    } else if (characterShowCount > 0 && characterHideCount === 0 && storySceneCount >= 2) {
      steps.push({
        tone: "soft",
        title: "补角色退场节奏",
        statusLabel: `已有 ${characterShowCount} 次出场 / 0 次隐藏`,
        description: "角色入场后适当退场，能减少后面场景立绘状态混乱，也方便做切场和分支。",
        actions: [
          { label: "去剧情页补隐藏卡", action: "switch-screen", screen: "story" },
          { label: "打开试玩确认", action: "switch-screen", screen: "preview" },
        ],
      });
    }

    if (storySceneCount > 0 && scenesWithBackground < storySceneCount) {
      steps.push({
        tone: "warn",
        title: "补齐场景背景覆盖",
        statusLabel: `已有背景 ${scenesWithBackground}/${storySceneCount} 场`,
        description: "有正文却没有背景的场景会显得像未完成草稿；发布前至少给每个有内容的场景一张背景。",
        actions: [
          { label: "只看缺背景场景", action: "set-route-map-filter", dataset: { "route-filter": "missing_background" } },
          { label: "去素材页补背景", action: "switch-screen", screen: "assets" },
        ],
      });
    }

    if (storySceneCount > 0 && scenesWithMusic < Math.max(1, Math.ceil(storySceneCount * 0.6))) {
      steps.push({
        tone: "soft",
        title: "补关键场景 BGM 规划",
        statusLabel: `已有 BGM ${scenesWithMusic}/${storySceneCount} 场`,
        description: "不一定每一场都要换曲，但至少开场、情绪转折和结尾最好有明确 BGM 范围，避免音乐机械地一首接一首。",
        actions: [
          { label: "只看缺 BGM 场景", action: "set-route-map-filter", dataset: { "route-filter": "missing_music" } },
          { label: "去剧情页补音乐卡", action: "switch-screen", screen: "story" },
        ],
      });
    }

    if (storySceneCount >= 2 && choiceCount === 0) {
      steps.push({
        tone: "soft",
        title: "补一个玩家选择节点",
        statusLabel: "还没有选项分支",
        description: "如果作品不是纯线性短篇，至少给 Demo 放一个选择节点，会更像可玩的视觉小说而不是只读脚本。",
        actions: [
          { label: "去剧情页加选项", action: "switch-screen", screen: "story" },
          { label: "查看路线图", action: "switch-screen", screen: "dashboard" },
        ],
      });
    }

    if (storySceneCount >= 2 && textDensity < 2) {
      steps.push({
        tone: "soft",
        title: "补一点正文密度",
        statusLabel: `平均每场 ${textDensity.toFixed(1)} 张正文卡`,
        description: "场景已经搭起来但正文偏少时，玩家会很快跑完；发布前可以先补每场开场句、角色反应和收束句。",
        actions: [
          { label: "去剧情页补正文", action: "switch-screen", screen: "story" },
          { label: "打开台本总览", action: "switch-screen", screen: "script" },
        ],
      });
    }

    if (storySceneCount >= 3 && scenesWithEffects === 0) {
      steps.push({
        tone: "soft",
        title: "补基础演出点缀",
        statusLabel: "还没有镜头/滤镜/粒子演出",
        description: "哪怕只在关键句加一次淡入、镜头推近、粒子或滤镜，也会明显提升 Demo 的第一眼完成度。",
        actions: [
          { label: "去剧情页加演出卡", action: "switch-screen", screen: "story" },
          { label: "打开台本演出灵感", action: "switch-screen", screen: "script" },
        ],
      });
    }

    return steps;
  }

  function buildVnEssentialsReleaseSteps(essentials = {}) {
    const releaseCodes = new Set([
      "bgm_scope_missing",
      "bgm_fade_in_missing",
      "bgm_fade_out_missing",
      "dialog_box_readability",
      "game_ui_skin_default",
      "font_asset_unbound",
      "video_asset_unused",
      "choice_consequence_missing",
    ]);
    const actionByArea = {
      audio: { label: "去剧情页调 BGM", action: "switch-screen", screen: "story" },
      textbox: { label: "去项目设置调文本框", action: "switch-screen", screen: "project" },
      ui: { label: "去项目设置调游戏 UI", action: "switch-screen", screen: "project" },
      media: { label: "去剧情页安排视频", action: "switch-screen", screen: "story" },
      branch: { label: "去剧情页补选项后果", action: "switch-screen", screen: "story" },
    };

    return toArray(essentials?.issues)
      .filter((issue) => releaseCodes.has(issue?.code))
      .slice(0, 6)
      .map((issue) => {
        const area = String(issue?.area ?? "").trim();
        return {
          tone: issue?.severity === "warn" ? "warn" : "soft",
          title: issue?.title ?? "补齐视觉小说基础能力",
          statusLabel: issue?.severityLabel ?? (issue?.severity === "warn" ? "基础缺口" : "体验打磨"),
          description: `${issue?.detail ?? ""}${issue?.suggestion ? ` ${issue.suggestion}` : ""}`.trim() || "发布前建议补齐这项基础能力。",
          actions: [
            actionByArea[area] ?? { label: "查看 Runtime 基础成熟度", action: "switch-screen", screen: "inspection" },
            { label: "导出 Runtime 矩阵", action: "export-runtime-capability-markdown" },
          ],
        };
      });
  }

  function getRouteTestingPlanFromContext(context = {}) {
    return context.routeTestingPlan ?? context.routeOverview?.routeTestingPlan ?? {};
  }

  function getRoutePlaytestIssueTone(status = "") {
    return status === "broken" ? "danger" : "warn";
  }

  function getRoutePlaytestIssueWeight(issue = {}) {
    const toneWeight = issue.tone === "danger" ? 1000 : 700;
    const kindWeight = issue.kind === "branch" ? 80 : 60;
    const depth = Number.isFinite(Number(issue.routeDepth)) ? Number(issue.routeDepth) : 999;
    return toneWeight + kindWeight - Math.min(depth, 20);
  }

  function buildRoutePlaytestFixQueue(routeTestingPlan = {}) {
    const queue = [];

    toArray(routeTestingPlan.decisionPoints).forEach((point, pointIndex) => {
      toArray(point.routeCases).forEach((routeCase, routeIndex) => {
        const status = String(routeCase?.status ?? "ready").trim() || "ready";
        if (status === "ready") {
          return;
        }
        queue.push({
          id: `route_${point.sceneId || pointIndex}_${routeIndex + 1}`,
          kind: "branch",
          tone: getRoutePlaytestIssueTone(status),
          status,
          statusLabel: routeCase.statusLabel ?? (status === "broken" ? "坏链" : "目标不可达"),
          title: status === "broken" ? "修复分支坏链" : "接通不可达分支目标",
          chapterName: point.chapterName,
          sceneId: routeCase.sourceSceneId ?? point.sceneId,
          sceneName: routeCase.sourceSceneName ?? point.sceneName,
          routeDepth: point.routeDepth,
          routeLabel: routeCase.label,
          targetSceneId: routeCase.targetSceneId,
          targetLabel: routeCase.targetSceneName,
          blockIndex: Number.isInteger(routeCase.blockIndex) ? routeCase.blockIndex : null,
          optionIndex: Number.isInteger(routeCase.optionIndex) ? routeCase.optionIndex : null,
          branchIndex: Number.isInteger(routeCase.branchIndex) ? routeCase.branchIndex : null,
        });
      });
    });

    toArray(routeTestingPlan.endingTestCases).forEach((testCase, index) => {
      const status = String(testCase?.status ?? "ready").trim() || "ready";
      if (status === "ready") {
        return;
      }
      queue.push({
        id: `ending_${testCase.sceneId || index}`,
        kind: "ending",
        tone: getRoutePlaytestIssueTone(status),
        status,
        statusLabel: testCase.statusLabel ?? (status === "broken" ? "坏链" : "未接通"),
        title: status === "broken" ? "修复结局路径坏链" : "接通结局入口",
        chapterName: testCase.chapterName,
        sceneId: testCase.sceneId,
        sceneName: testCase.sceneName,
        routeDepth: testCase.routeDepth,
        routeLabel: "结局路径",
        targetSceneId: testCase.sceneId,
        targetLabel: testCase.sceneName,
        actionHint: testCase.testingHint,
      });
    });

    return queue
      .sort((left, right) => {
        const weightDelta = getRoutePlaytestIssueWeight(right) - getRoutePlaytestIssueWeight(left);
        if (weightDelta !== 0) {
          return weightDelta;
        }
        return String(left.sceneName ?? "").localeCompare(String(right.sceneName ?? ""), "zh-CN");
      })
      .map((item, index) => ({ ...item, rank: index + 1 }));
  }

  function buildRoutePlaytestFixStep(routeTestingPlan = {}) {
    const queue = buildRoutePlaytestFixQueue(routeTestingPlan);
    if (!queue.length) {
      return null;
    }

    const brokenCount = queue.filter((item) => item.status === "broken").length;
    const unreachableCount = queue.filter((item) => item.status === "unreachable").length;
    const otherCount = Math.max(queue.length - brokenCount - unreachableCount, 0);
    const firstIssue = queue[0];
    const firstLabel = [firstIssue.sceneName, firstIssue.routeLabel, firstIssue.targetLabel]
      .filter(Boolean)
      .join(" / ");
    const statusParts = [
      brokenCount > 0 ? `坏链 ${brokenCount} 条` : "",
      unreachableCount > 0 ? `不可达 ${unreachableCount} 条` : "",
      otherCount > 0 ? `待确认 ${otherCount} 条` : "",
    ].filter(Boolean);

    return {
      tone: brokenCount > 0 ? "danger" : "warn",
      title: brokenCount > 0 ? "先修路线坏链" : "接通路线试玩入口",
      statusLabel: statusParts.join(" / ") || `${queue.length} 条路线待确认`,
      description: firstLabel
        ? `先处理「${firstLabel}」。修完后重新生成路线试玩手册，再继续正式试玩。`
        : "路线试玩手册里还有坏链或不可达目标，发布前建议先把这些路线接通。",
      actions: [
        firstIssue.sceneId
          ? { label: "打开第一条路线问题", action: "preview-story-location", sceneId: firstIssue.sceneId }
          : { label: "去剧情页修路线", action: "switch-screen", screen: "story" },
        { label: "导出路线试玩手册", action: "export-route-testing-plan-markdown" },
      ],
      routeIssueQueue: queue.slice(0, 8),
    };
  }

  function buildReleaseFixOrder(context = {}) {
    const routeMetrics = context.routeMetrics ?? context.routeOverview?.metrics ?? {};
    const routeTestingPlan = getRouteTestingPlanFromContext(context);
    const resolution = normalizeResolution(context.resolution);
    const releaseVersion = String(context.releaseVersion ?? DEFAULT_PROJECT_RELEASE_VERSION).trim() || DEFAULT_PROJECT_RELEASE_VERSION;
    const hasStoredReleaseVersion = Boolean(context.hasStoredReleaseVersion);
    const errorCount = toCount(context.errorCount ?? context.validationErrors?.length);
    const { missingVoiceWarnings, nonVoiceWarnings } = splitReleaseWarnings(context.warningIssues);
    const missingVoiceWarningsCount = toCount(context.missingVoiceWarningsCount ?? missingVoiceWarnings.length);
    const nonVoiceWarningsCount = toCount(context.nonVoiceWarningsCount ?? nonVoiceWarnings.length);
    const urgentMissingAssetsCount = toCount(context.urgentMissingAssetsCount);
    const unusedAssetCount = toCount(context.unusedAssetCount);
    const mediaBudgetReport = context.mediaBudgetReport ?? {};
    const mediaBudgetCount = toCount(mediaBudgetReport.count);
    const mediaBudgetBlockerCount = toCount(mediaBudgetReport.blockerCount);
    const runtimePreloadBudget = context.runtimePreloadBudget ?? {};
    const desktopReady = isDesktopExportReady(context.exportResult);
    const firstErrorAction = context.firstErrorAction ?? null;
    const firstVoiceAction = context.firstVoiceAction ?? null;
    const firstWarningAction = context.firstWarningAction ?? null;
    const steps = [];

    if (errorCount > 0) {
      steps.push({
        tone: "danger",
        title: "先清结构错误",
        statusLabel: `还有 ${errorCount} 项结构错误`,
        description: "这些问题最容易直接打断剧情推进、跳错场景，或者让正式导出后的流程不完整。",
        actions: [
          {
            label: "只看结构错误",
            action: "set-preview-issue-filter",
            dataset: { "preview-issue-filter": "errors" },
          },
          firstErrorAction
            ? { ...firstErrorAction, label: "打开第一条错误" }
            : { label: "去剧情页修", action: "switch-screen", screen: "story" },
        ],
      });
    }

    const routePlaytestFixStep = buildRoutePlaytestFixStep(routeTestingPlan);
    if (routePlaytestFixStep) {
      steps.push(routePlaytestFixStep);
    }

    const productionBacklogFixStep = buildProductionBacklogFixStep(context);
    if (productionBacklogFixStep) {
      steps.push(productionBacklogFixStep);
    }

    const orphanSceneCount = toCount(routeMetrics.orphanScenes);
    const unreachableSceneCount = toCount(routeMetrics.unreachableScenes);
    if (orphanSceneCount > 0 || unreachableSceneCount > 0) {
      steps.push({
        tone: "warn",
        title: "检查孤立场景和路线入口",
        statusLabel:
          orphanSceneCount > 0 && unreachableSceneCount > 0
            ? `还有 ${orphanSceneCount} 个孤立场景 / ${unreachableSceneCount} 个不可达场景`
            : orphanSceneCount > 0
              ? `还有 ${orphanSceneCount} 个孤立场景`
              : `还有 ${unreachableSceneCount} 个入口不可达场景`,
        description: "这些场景可能没有入口，或者虽然有入口线、但从项目入口试玩时仍然走不到。",
        actions: [
          { label: "回首页看路线图", action: "switch-screen", screen: "dashboard" },
          { label: "去剧情页补跳转", action: "switch-screen", screen: "story" },
        ],
      });
    }

    if (urgentMissingAssetsCount > 0) {
      steps.push({
        tone: "warn",
        title: "补齐已引用缺口素材",
        statusLabel: `还有 ${urgentMissingAssetsCount} 个引用缺口`,
        description: "这些素材已经被剧情使用，但真实文件还没准备好，正式导出后会直接缺图、缺音或缺视频。",
        actions: [
          {
            label: "去补缺口素材",
            action: "focus-asset-gap",
            dataset: { "asset-filter-mode": "urgent_missing" },
          },
          {
            label: "只看导出缺失",
            action: "set-preview-issue-filter",
            dataset: { "preview-issue-filter": "export_missing" },
          },
        ],
      });
    }

    steps.push(...buildCreativeQualityAudit(context));
    steps.push(...buildVnEssentialsReleaseSteps(context.runtimeCapabilityMatrix?.essentials));

    if (mediaBudgetCount > 0) {
      const largest = mediaBudgetReport.largest ?? null;
      steps.push({
        tone: mediaBudgetBlockerCount > 0 ? "warn" : "soft",
        title: "压缩超预算素材",
        statusLabel:
          mediaBudgetBlockerCount > 0
            ? `明显超预算 ${mediaBudgetBlockerCount} 个`
            : `建议压缩 ${mediaBudgetCount} 个素材`,
        description: largest
          ? `先从最大素材「${largest.name}」开始处理。当前风险素材合计 ${mediaBudgetReport.totalLabel ?? "未统计"}，压一轮会直接改善包体和加载体验。`
          : "发布前建议压缩体积偏大的素材，降低包体和加载风险。",
        actions: [
          {
            label: "只看体积风险素材",
            action: "focus-asset-gap",
            dataset: { "asset-filter-mode": "media_budget" },
          },
          largest
            ? {
                label: "打开最大素材",
                action: "open-asset-from-issue",
                assetId: largest.assetId,
              }
            : { label: "去素材页", action: "switch-screen", screen: "assets" },
        ],
      });
    }

    const runtimePreloadStep = buildRuntimePreloadBudgetFixStep(runtimePreloadBudget);
    if (runtimePreloadStep) {
      steps.push(runtimePreloadStep);
    }

    if (missingVoiceWarningsCount > 0) {
      steps.push({
        tone: "warn",
        title: "集中补待绑语音",
        statusLabel: `还有 ${missingVoiceWarningsCount} 句待绑语音`,
        description: "如需准备正式版本，这一批最好先集中清掉，后面的配音整理和最终试玩都会轻很多。",
        actions: [
          { label: "只看待绑语音", action: "focus-script-missing-voice" },
          firstVoiceAction
            ? { ...firstVoiceAction, label: "打开第一句" }
            : { label: "去台本页处理", action: "switch-screen", screen: "script" },
        ],
      });
    }

    if (!hasStoredReleaseVersion || resolution.width !== 1920 || resolution.height !== 1080) {
      steps.push({
        tone: "soft",
        title: "确认发布版本和分辨率",
        statusLabel:
          !hasStoredReleaseVersion
            ? `当前版本 ${releaseVersion} 还没正式写入`
            : `${resolution.width} × ${resolution.height}`,
        description: "在正式导出前，先把版本号和桌面分辨率定下来，后面的发布清单、桌面包和交付说明会更一致。",
        actions: [
          !hasStoredReleaseVersion
            ? { label: "保存发布版本", action: "save-release-version" }
            : { label: "去预览导出页", action: "switch-screen", screen: "preview" },
          resolution.width === 1920 && resolution.height === 1080
            ? { label: "查看导出设置", action: "switch-screen", screen: "preview" }
            : {
                label: "切到 1920×1080",
                action: "set-resolution",
                dataset: { width: "1920", height: "1080" },
              },
        ],
      });
    }

    if (nonVoiceWarningsCount > 0) {
      steps.push({
        tone: "soft",
        title: "顺手处理补充提醒",
        statusLabel: `还有 ${nonVoiceWarningsCount} 项补充提醒`,
        description: "这些不一定会卡死项目，但修完以后最终试玩手感和导出稳定度通常会更好。",
        actions: [
          {
            label: "只看补充提醒",
            action: "set-preview-issue-filter",
            dataset: { "preview-issue-filter": "warnings" },
          },
          firstWarningAction
            ? { ...firstWarningAction, label: "打开第一条提醒" }
            : { label: "去巡检结果里看", action: "switch-screen", screen: "inspection" },
        ],
      });
    }

    if (unusedAssetCount > 0) {
      steps.push({
        tone: "soft",
        title: "清一轮闲置素材",
        statusLabel: `当前有 ${unusedAssetCount} 个闲置素材`,
        description: "这一步不会阻塞发布，但清掉无用条目后，工程会更干净，后面找素材也轻很多。",
        actions: [
          { label: "去素材页定位", action: "focus-unused-assets" },
          {
            label: "只看闲置素材",
            action: "set-preview-issue-filter",
            dataset: { "preview-issue-filter": "unused_assets" },
          },
        ],
      });
    }

    steps.push({
      tone: desktopReady ? "good" : "warn",
      title: desktopReady ? "最后导出正式桌面包确认" : "再导一版正式桌面包",
      statusLabel: desktopReady ? "最近一版已经接近正式交付" : "用最新内容再验证一次桌面包",
      description: desktopReady
        ? "最后再导一次桌面包，确认发布版本、启动画面、图标和素材缺口都没有回退。"
        : "前面的修复做完后，最后一定要重新导一版原生桌面包，确认真壳、图标和素材都跟上了。",
      actions: [
        {
          label: "导出 Windows 桌面包",
          action: "export-build",
          dataset: { "export-target": "windows_nwjs" },
        },
        {
          label: "导出 macOS 桌面包",
          action: "export-build",
          dataset: { "export-target": "macos_nwjs" },
        },
        {
          label: "导出 Linux 桌面包",
          action: "export-build",
          dataset: { "export-target": "linux_nwjs" },
        },
        { label: "去预览导出页", action: "switch-screen", screen: "preview" },
      ],
    });

    return {
      steps,
      blockerCount: steps.filter((step) => step.tone === "danger").length,
      urgentCount: steps.filter((step) => step.tone === "warn").length,
    };
  }

  global.CanvasiaEditorReleaseControl = Object.freeze({
    MISSING_VOICE_WARNING_MESSAGE,
    DESKTOP_EXPORT_TARGETS,
    getReleaseSeverityLabel,
    getReleaseStepToneLabel,
    serializeReleaseReportAction,
    buildReleaseChecklistSummary,
    buildFinalPublishGate,
    buildReleaseReportNextStep,
    formatReleaseReportNextStepActionHint,
    formatReleaseReportNextStepAdvice,
    serializeProductionBacklogTask,
    formatProductionBacklogTaskHint,
    splitReleaseWarnings,
    isDesktopExportReady,
    getRuntimePreloadBudgetRiskCount,
    getRuntimePreloadBudgetBlockerCount,
    getRuntimePreloadBudgetPrimaryIssue,
    serializeRuntimePreloadBudgetForRelease,
    buildReleaseControlOverviewRows,
    buildRuntimePreloadBudgetFixStep,
    buildCreativeQualityAudit,
    buildVnEssentialsReleaseSteps,
    buildRoutePlaytestFixQueue,
    buildRoutePlaytestFixStep,
    buildReleaseFixOrder,
  });
})(typeof window !== "undefined" ? window : globalThis);
