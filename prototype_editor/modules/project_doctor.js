(function attachProjectDoctor(global) {
  "use strict";

  const ISSUE_KIND_PRIORITY = Object.freeze({
    errors: 0,
    regression_fail: 6,
    route_danger: 8,
    export_missing: 12,
    warnings: 24,
    regression_warn: 28,
    media_budget: 34,
    route_warn: 42,
    unused_assets: 70,
  });

  const ISSUE_KIND_LABELS = Object.freeze({
    errors: "结构错误",
    regression_fail: "回归失败",
    route_danger: "坏链",
    export_missing: "缺素材",
    warnings: "补充提醒",
    regression_warn: "回归复看",
    media_budget: "素材预算",
    route_warn: "路线提醒",
    unused_assets: "闲置素材",
  });

  const ISSUE_KIND_BADGES = Object.freeze({
    errors: "先修",
    regression_fail: "先修",
    route_danger: "先修",
    export_missing: "补齐",
    warnings: "复看",
    regression_warn: "复看",
    media_budget: "压缩",
    route_warn: "确认",
    unused_assets: "整理",
  });

  function cleanText(value, fallback = "") {
    return String(value ?? fallback).trim();
  }

  function compactText(value, maxLength = 80) {
    const text = cleanText(value).replace(/\s+/g, " ");
    const safeMax = Math.max(Number(maxLength) || 80, 8);
    if (text.length <= safeMax) {
      return text;
    }
    return `${text.slice(0, safeMax - 1).trim()}…`;
  }

  function getIssueKindPriority(kind) {
    const safeKind = cleanText(kind, "warnings");
    return Object.prototype.hasOwnProperty.call(ISSUE_KIND_PRIORITY, safeKind)
      ? ISSUE_KIND_PRIORITY[safeKind]
      : 50;
  }

  function getDoctorStepTone(kind) {
    if (["errors", "regression_fail", "route_danger"].includes(kind)) {
      return "danger";
    }
    if (["export_missing", "warnings", "regression_warn", "media_budget", "route_warn"].includes(kind)) {
      return "warn";
    }
    return "soft";
  }

  function getDoctorStepLabel(kind) {
    return ISSUE_KIND_LABELS[kind] ?? "待处理";
  }

  function getDoctorStepBadge(kind) {
    return ISSUE_KIND_BADGES[kind] ?? "处理";
  }

  function buildFallbackAction(kind) {
    const filterKinds = new Set(["errors", "warnings", "export_missing", "media_budget", "unused_assets"]);
    if (filterKinds.has(kind)) {
      return {
        label: "只看这一类",
        action: "set-inspection-filter",
        dataset: { "inspection-issue-filter": kind },
      };
    }
    return {
      label: "回到巡检页",
      action: "switch-screen",
      screen: "inspection",
    };
  }

  function inferIssueRecovery(item) {
    const kind = cleanText(item?.kind, "warnings");
    const title = cleanText(item?.title);
    const meta = cleanText(item?.meta || item?.location);
    const searchText = `${title} ${meta}`;

    if (cleanText(item?.recovery)) {
      return cleanText(item.recovery);
    }
    if (searchText.includes("章节排序") || searchText.includes("章节没有进入排序") || searchText.includes("chapterOrder")) {
      return "先点项目医生的“先预览安全修复”，确认后再执行；系统会清理无效或重复章节排序，并把遗漏章节补回排序表。";
    }
    if (searchText.includes("场景排序") || searchText.includes("场景没有进入排序") || searchText.includes("sceneOrder")) {
      return "先点项目医生的“先预览安全修复”，确认后再执行；系统会清理无效或重复场景排序，并把遗漏场景补回本章顺序表。";
    }
    if (kind === "errors") {
      if (title.includes("入口场景")) {
        return "先把项目入口改成真实存在的场景，或者恢复被删掉的入口场景；修完后重新巡检。";
      }
      if (title.includes("素材") || title.includes("立绘") || title.includes("模型")) {
        return "点开对应素材或角色，把引用换成现有素材；如果文件丢了，先在素材页重新导入。";
      }
      if (title.includes("场景") || title.includes("跳转")) {
        return "打开对应卡片，把跳转、选项或条件分支指向真实存在的场景。";
      }
      return "先点定位按钮打开具体位置，把缺失引用或错误配置修好，再重新巡检确认。";
    }
    if (kind === "export_missing") {
      return "去素材页补回缺失文件，或者用替换素材功能换成真实存在的文件，然后重新导出一版。";
    }
    if (kind === "media_budget") {
      return "优先压缩最大的视频、音频和图片素材；保留源文件归档，项目里放发布用压缩版。";
    }
    if (kind === "unused_assets") {
      return "确认这些素材是否只是备用；不需要的可以删除或移到项目外归档，让素材库更清爽。";
    }
    return "如果这是刻意设计可以暂时跳过；如果不是，按提示补内容、补引用或调整设置。";
  }

  function inferIssueDoneWhen(item) {
    const kind = cleanText(item?.kind, "warnings");
    const title = cleanText(item?.title);
    const meta = cleanText(item?.meta || item?.location);
    const searchText = `${title} ${meta}`;

    if (searchText.includes("章节排序") || searchText.includes("章节没有进入排序") || searchText.includes("chapterOrder")) {
      return "重新巡检后章节排序的重复、无效引用或遗漏提示消失，章节列表顺序保持稳定。";
    }
    if (searchText.includes("场景排序") || searchText.includes("场景没有进入排序") || searchText.includes("sceneOrder")) {
      return "重新巡检后场景排序的重复、无效引用或遗漏提示消失，本章场景能按正确顺序浏览。";
    }

    if (kind === "errors") {
      if (title.includes("入口场景")) {
        return "重新巡检后不再出现入口场景错误，试玩会从正确的第一幕开始。";
      }
      if (title.includes("素材") || title.includes("立绘") || title.includes("模型")) {
        return "素材或角色预览能正常显示，导出缺失素材数量减少。";
      }
      if (title.includes("场景") || title.includes("跳转")) {
        return "路线图里这条跳转变成有效连线，玩家不会走到不存在的场景。";
      }
      return "重新巡检后这条结构错误消失，相关试玩路线可以继续向下走。";
    }
    if (kind === "export_missing") {
      return "重新导出时缺失素材数量减少，导出的试玩包能带上对应文件。";
    }
    if (kind === "media_budget") {
      return "素材预算提示降低到可接受范围，发布包体更适合上传和下载。";
    }
    if (kind === "unused_assets") {
      return "素材库只保留会用到或明确备用的资源，测试人员更容易找到真正素材。";
    }
    if (kind === "warnings" && title.includes("语音")) {
      return "台词台本里这句不再标记待配音，或确认它属于暂时可跳过的无语音内容。";
    }
    return "重新巡检后提醒数量减少，或这条提醒被确认成有意保留的设计。";
  }

  function collectRepairCodesFromText(value) {
    const text = cleanText(value);
    const codes = [];

    if (text.includes("入口场景")) {
      codes.push("entry_scene");
    }
    if (text.includes("场景顺序") || text.includes("场景排序") || text.includes("sceneOrder")) {
      codes.push("scene_order");
    }
    if (text.includes("章节顺序") || text.includes("章节排序") || text.includes("chapterOrder")) {
      codes.push("chapter_order");
    }
    return [...new Set(codes)];
  }

  function inferRepairCodes(item) {
    const primaryCodes = collectRepairCodesFromText(`${item?.kind ?? ""} ${item?.title ?? ""} ${item?.meta ?? ""}`);
    if (primaryCodes.length) {
      return primaryCodes;
    }
    return collectRepairCodesFromText(item?.recovery ?? "");
  }

  function normalizeAction(action, fallbackKind) {
    if (!action || typeof action !== "object") {
      return buildFallbackAction(fallbackKind);
    }
    return {
      label: cleanText(action.label, "去处理"),
      action: cleanText(action.action),
      href: cleanText(action.href),
      screen: cleanText(action.screen),
      sceneId: cleanText(action.sceneId),
      blockId: cleanText(action.blockId),
      characterId: cleanText(action.characterId),
      chapterId: cleanText(action.chapterId),
      assetId: cleanText(action.assetId),
      dataset: action.dataset && typeof action.dataset === "object" ? { ...action.dataset } : {},
    };
  }

  function normalizeIssueStep(item, index = 0) {
    const kind = cleanText(item?.kind, "warnings");
    const priority = getIssueKindPriority(kind);
    const title = compactText(item?.title || getDoctorStepLabel(kind), 96);
    const meta = compactText(item?.meta || item?.location || "未标注位置", 120);
    const action = normalizeAction(item?.action, kind);
    const recovery = inferIssueRecovery({ ...item, kind });

    return {
      id: cleanText(item?.id) || `${kind}-${index}-${title}`,
      source: "issue",
      kind,
      label: getDoctorStepLabel(kind),
      badge: getDoctorStepBadge(kind),
      tone: getDoctorStepTone(kind),
      priority,
      title,
      meta,
      why: kind === "unused_assets" ? "它不会立刻卡死发布，但会让素材库和包体变乱。" : "它会影响试玩、导出或后续排查效率。",
      recovery,
      doneWhen: inferIssueDoneWhen({ ...item, kind, title }),
      repairCodes: inferRepairCodes({ ...item, kind, title, meta, recovery }),
      actions: [
        action,
        buildFallbackAction(kind),
      ],
      searchText: cleanText(item?.searchText || `${title} ${meta} ${recovery}`),
    };
  }

  function normalizeRouteAlertStep(alert, index = 0) {
    const tone = cleanText(alert?.tone, "warn");
    const kind = tone === "danger" ? "route_danger" : "route_warn";
    const sceneId = cleanText(alert?.sceneId);
    const title = compactText(alert?.message || "路线需要检查", 96);
    const meta = compactText(`${alert?.sceneName ?? "未命名场景"} · ${alert?.meta ?? ""}`, 120);

    return {
      id: `route-${sceneId || index}-${kind}`,
      source: "route",
      kind,
      label: getDoctorStepLabel(kind),
      badge: getDoctorStepBadge(kind),
      tone: getDoctorStepTone(kind),
      priority: getIssueKindPriority(kind),
      title,
      meta,
      why: kind === "route_danger" ? "坏链会让玩家走到不存在的位置。" : "孤立场景可能是隐藏线，也可能是忘记接入口。",
      recovery:
        kind === "route_danger"
          ? "打开源场景，检查跳转、选项或条件分支，把目标改成真实存在的场景。"
          : "如果它不是隐藏路线，就从前面的场景补一条选项、跳转或条件入口接到这里。",
      doneWhen:
        kind === "route_danger"
          ? "路线图里的坏链数量减少，自动试玩不会再卡在这条跳转上。"
          : "路线图能看见它的入口，或者它被明确保留为隐藏路线。",
      repairCodes: [],
      actions: [
        sceneId
          ? { label: "打开这个场景", action: "open-scene-from-map", sceneId }
          : { label: "查看路线图", action: "switch-screen", screen: "dashboard" },
        { label: "查看路线图", action: "switch-screen", screen: "dashboard" },
      ],
      searchText: cleanText(`${title} ${meta}`),
    };
  }

  function normalizeRegressionStep(caseResult, index = 0) {
    const status = cleanText(caseResult?.status, "warn");
    const kind = status === "fail" ? "regression_fail" : "regression_warn";
    const title = compactText(caseResult?.reason || caseResult?.statusLabel || "回归路线需要复看", 96);
    const meta = compactText(
      `${caseResult?.sceneName ?? "未命名场景"} · ${caseResult?.chapterName ?? "未分章"} · ${
        caseResult?.detail ?? ""
      }`,
      130
    );

    return {
      id: `regression-${caseResult?.id ?? index}`,
      source: "regression",
      kind,
      label: getDoctorStepLabel(kind),
      badge: getDoctorStepBadge(kind),
      tone: getDoctorStepTone(kind),
      priority: getIssueKindPriority(kind) + Math.min(Number(caseResult?.steps ?? 0), 10) / 100,
      title,
      meta,
      why: status === "fail" ? "自动试玩已经跑出了真实路线问题。" : "这条路线没有硬崩，但发布前值得人工复看一次。",
      recovery:
        cleanText(caseResult?.recommendation) ||
        (status === "fail"
          ? "优先打开问题位置，检查坏跳转、空场景、无选项或循环条件。"
          : "打开对应路线试玩一次，确认节奏、结尾和分支去向符合预期。"),
      doneWhen:
        status === "fail"
          ? "重新跑自动回归后，这条路线从失败变为通过或只剩人工复看提醒。"
          : "人工试玩确认这条路线节奏、结尾和分支去向都符合预期。",
      repairCodes: [],
      actions: Array.isArray(caseResult?.actions) && caseResult.actions.length
        ? caseResult.actions.slice(0, 2).map((action) => normalizeAction(action, kind))
        : [
            caseResult?.anchorSceneId || caseResult?.seedSceneId
              ? {
                  label: "打开问题场景",
                  action: "open-scene-from-map",
                  sceneId: caseResult.anchorSceneId || caseResult.seedSceneId,
                }
              : buildFallbackAction(kind),
          ],
      searchText: cleanText(`${title} ${meta}`),
    };
  }

  function dedupeDoctorSteps(steps) {
    const seen = new Set();
    return steps.filter((step) => {
      const key = [step.kind, step.title, step.meta].join("|");
      if (seen.has(key)) {
        return false;
      }
      seen.add(key);
      return true;
    });
  }

  function buildProjectDoctorQueue({
    issueItems = [],
    routeOverview = null,
    regressionResult = null,
    limit = 8,
  } = {}) {
    const steps = [];
    issueItems.forEach((item, index) => steps.push(normalizeIssueStep(item, index)));
    (routeOverview?.alerts ?? [])
      .filter((alert) => ["danger", "warn"].includes(cleanText(alert?.tone)))
      .forEach((alert, index) => steps.push(normalizeRouteAlertStep(alert, index)));
    (regressionResult?.cases ?? [])
      .filter((caseResult) => cleanText(caseResult?.status) !== "pass")
      .forEach((caseResult, index) => steps.push(normalizeRegressionStep(caseResult, index)));

    const numericLimit = limit == null ? 8 : Number(limit);
    const safeLimit = Number.isFinite(numericLimit) ? Math.max(Math.floor(numericLimit), 0) : 8;
    return dedupeDoctorSteps(steps)
      .sort((left, right) => {
        if (left.priority !== right.priority) {
          return left.priority - right.priority;
        }
        return left.title.localeCompare(right.title, "zh-CN");
      })
      .slice(0, safeLimit)
      .map((step, index) => ({
        ...step,
        order: index + 1,
      }));
  }

  function buildProjectDoctorSummary(queue = []) {
    const dangerCount = queue.filter((step) => step.tone === "danger").length;
    const warnCount = queue.filter((step) => step.tone === "warn").length;
    const softCount = queue.filter((step) => step.tone === "soft").length;
    const autoRepairableCount = queue.filter((step) => Array.isArray(step.repairCodes) && step.repairCodes.length > 0).length;
    const nextStep = queue[0] ?? null;

    if (!queue.length) {
      return {
        status: "clean",
        badge: "很干净",
        title: "项目医生没有发现需要优先处理的事项",
        description: "当前可以继续试玩、补内容或导出一版做最终确认。",
        dangerCount,
        warnCount,
        softCount,
        autoRepairableCount,
        autoRepairLabel: "暂无可预览修复项",
        nextStepTitle: "",
      };
    }

    if (dangerCount > 0) {
      return {
        status: "danger",
        badge: "先修硬阻塞",
        title: `建议先处理 ${dangerCount} 个硬阻塞`,
        description: "这些问题最可能让玩家卡住、跳错或导出不完整，先清它们最省返工。",
        dangerCount,
        warnCount,
        softCount,
        autoRepairableCount,
        autoRepairLabel: autoRepairableCount ? `可先预览安全修复 ${autoRepairableCount} 项` : "暂无可预览修复项",
        nextStepTitle: nextStep.title,
      };
    }

    if (warnCount > 0) {
      return {
        status: "warn",
        badge: "可边做边修",
        title: `还有 ${warnCount} 个发布前建议复看的事项`,
        description: "当前没有明显硬阻塞，但这些项目会影响成品质感、包体或测试效率。",
        dangerCount,
        warnCount,
        softCount,
        autoRepairableCount,
        autoRepairLabel: autoRepairableCount ? `可先预览安全修复 ${autoRepairableCount} 项` : "暂无可预览修复项",
        nextStepTitle: nextStep.title,
      };
    }

    return {
      status: "soft",
      badge: "整理收尾",
      title: "剩下多是整理类事项",
      description: "这些不会立刻阻塞试玩，适合在发布前顺手清一轮。",
      dangerCount,
      warnCount,
      softCount,
      autoRepairableCount,
      autoRepairLabel: autoRepairableCount ? `可先预览安全修复 ${autoRepairableCount} 项` : "暂无可预览修复项",
      nextStepTitle: nextStep.title,
    };
  }

  function normalizeRepairReceiptItem(item, index = 0, type = "repair") {
    return {
      code: cleanText(item?.code, `${type}_${index + 1}`),
      title: compactText(item?.title || (type === "repair" ? "已完成安全修复" : "已跳过"), 88),
      detail: compactText(item?.detail || (type === "repair" ? "这个结构问题已被项目医生处理。" : "这个项目当前无需处理。"), 140),
    };
  }

  function buildProjectDoctorRepairNextActions(status = "clean", repairCodes = []) {
    const repaired = status === "repaired";
    const preview = status === "preview";
    const unknown = status === "unknown";
    const repairCodeText = Array.isArray(repairCodes) ? repairCodes.filter(Boolean).join(",") : "";
    if (preview) {
      return [
        {
          label: "确认执行安全修复",
          action: "repair-project-doctor",
          dataset: repairCodeText ? { "repair-codes": repairCodeText } : {},
        },
        { label: "重新巡检确认", action: "run-project-inspection" },
        { label: "导出巡检报告", action: "export-inspection-report" },
      ];
    }
    if (unknown) {
      return [
        { label: "重新巡检刷新修复码", action: "run-project-inspection" },
        { label: "重新预览安全修复", action: "preview-project-doctor-repair" },
        { label: "导出巡检报告", action: "export-inspection-report" },
      ];
    }
    return [
      { label: "重新巡检确认", action: "run-project-inspection" },
      repaired
        ? { label: "跑自动回归确认", action: "run-preview-regression" }
        : { label: "去预览导出", action: "switch-screen", screen: "preview" },
      { label: "导出巡检报告", action: "export-inspection-report" },
    ];
  }

  function buildProjectDoctorRepairReceipt(result = null) {
    if (!result || typeof result !== "object") {
      return null;
    }

    const repairs = Array.isArray(result.repairs)
      ? result.repairs.map((item, index) => normalizeRepairReceiptItem(item, index, "repair"))
      : [];
    const dryRun = Boolean(result.dryRun);
    const changed = Boolean(result.changed);
    const requestedCodes = Array.isArray(result.requestedCodes)
      ? result.requestedCodes.map((code) => cleanText(code)).filter(Boolean)
      : [];
    const ignoredCodes = Array.isArray(result.ignoredCodes)
      ? result.ignoredCodes.map((code) => cleanText(code)).filter(Boolean)
      : [];
    const skipped = [
      ...(Array.isArray(result.skipped)
        ? result.skipped.map((item, index) => normalizeRepairReceiptItem(item, index, "skip"))
        : []),
      ...ignoredCodes.map((code, index) =>
        normalizeRepairReceiptItem(
          {
            code: `ignored_${code}`,
            title: `未识别修复码：${code}`,
            detail: "这个修复码不属于当前安全修复范围，可能来自过期按钮或手动输入；请重新巡检后再点项目医生按钮。",
          },
          index,
          "skip"
        )
      ),
    ];
    const repairCount = repairs.length;
    const skippedCount = skipped.length;
    const wouldChange = Boolean(result.wouldChange) || repairCount > 0;
    const status = ignoredCodes.length && !wouldChange && !changed
      ? "unknown"
      : dryRun && wouldChange ? "preview" : changed ? "repaired" : "clean";
    const ignoredNote = ignoredCodes.length ? `；另有 ${ignoredCodes.length} 个未识别修复码已列在跳过区` : "";

    return {
      generatedAt: cleanText(result.savedAt || result.generatedAt || new Date().toISOString()),
      status,
      badge: status === "unknown" ? "未识别" : status === "preview" ? "预览未写入" : changed ? "已自动修复" : "无需自动修复",
      title: status === "preview"
        ? `项目医生预览到 ${repairCount} 项可安全修复`
        : status === "unknown"
        ? `项目医生未识别 ${ignoredCodes.length} 个修复码`
        : changed
        ? `项目医生完成 ${repairCount} 项安全修复`
        : "项目医生没有发现可自动修复的低风险结构问题",
      description: status === "preview"
        ? `这只是预览，不会写入项目文件；确认列表无误后再执行安全修复${ignoredNote}。`
        : status === "unknown"
        ? `这些修复码不属于当前安全修复范围：${ignoredCodes.join(" / ")}。请重新巡检后再点项目医生按钮。`
        : changed
        ? `修复已写入项目并进入自动快照链；建议重新巡检或跑一次自动回归确认结果${ignoredNote}。`
        : `这通常代表入口、章节顺序和场景顺序已经比较干净，剩余事项需要人工判断${ignoredNote}。`,
      repairCount,
      skippedCount,
      dryRun,
      wouldChange,
      requestedCodes,
      ignoredCodes,
      repairs,
      skipped,
      nextActions: buildProjectDoctorRepairNextActions(status, requestedCodes),
    };
  }

  global.TonyNaEditorProjectDoctor = Object.freeze({
    buildProjectDoctorRepairNextActions,
    buildProjectDoctorRepairReceipt,
    buildProjectDoctorQueue,
    buildProjectDoctorSummary,
    compactText,
    getDoctorStepBadge,
    getDoctorStepLabel,
    getDoctorStepTone,
    getIssueKindPriority,
    inferIssueDoneWhen,
    inferRepairCodes,
  });
})(typeof window !== "undefined" ? window : globalThis);
