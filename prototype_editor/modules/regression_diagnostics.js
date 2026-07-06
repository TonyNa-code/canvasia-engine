(function attachRegressionDiagnostics(global) {
  "use strict";

  const DEFAULT_TRACE_LIMIT = 3;
  const DEFAULT_TRACE_TEXT_LIMIT = 180;
  const DEFAULT_LINE_LIMIT = 260;

  function toArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function cleanText(value, fallback = "") {
    return String(value ?? fallback).trim();
  }

  function compactText(value, maxLength = DEFAULT_TRACE_TEXT_LIMIT) {
    const text = cleanText(value).replace(/\s+/g, " ");
    const safeMax = Math.max(Number(maxLength) || DEFAULT_TRACE_TEXT_LIMIT, 12);
    if (text.length <= safeMax) {
      return text;
    }
    return `${text.slice(0, safeMax - 1).trim()}…`;
  }

  function getPositiveLimit(value, fallback) {
    const numberValue = Number(value);
    return Number.isFinite(numberValue) ? Math.max(0, Math.floor(numberValue)) : fallback;
  }

  function getRegressionVariablePresetSummary(caseResult = {}) {
    return cleanText(caseResult.variableOverrideSummary);
  }

  function getRegressionConditionTraceSummaries(caseResult = {}, options = {}) {
    const limit = getPositiveLimit(options.maxItems, DEFAULT_TRACE_LIMIT);
    const traceMaxLength = getPositiveLimit(options.traceMaxLength, DEFAULT_TRACE_TEXT_LIMIT);
    return toArray(caseResult.conditionTraceSummaries)
      .map((item) => compactText(item, traceMaxLength))
      .filter(Boolean)
      .slice(0, limit);
  }

  function getRegressionDiagnosticItems(caseResult = {}, options = {}) {
    const includeVariable = options.includeVariable !== false;
    const items = [];
    const variableSummary = getRegressionVariablePresetSummary(caseResult);
    if (includeVariable && variableSummary) {
      items.push(compactText(`测试预设：${variableSummary}`, options.variableMaxLength ?? DEFAULT_TRACE_TEXT_LIMIT));
    }
    items.push(...getRegressionConditionTraceSummaries(caseResult, options));
    return items;
  }

  function formatRegressionDiagnosticLine(caseResult = {}, options = {}) {
    const separator = cleanText(options.separator, " / ");
    return compactText(getRegressionDiagnosticItems(caseResult, options).join(separator), options.maxLength ?? DEFAULT_LINE_LIMIT);
  }

  function serializeRegressionDiagnostics(caseResult = {}, options = {}) {
    const conditionTraceSummaries = getRegressionConditionTraceSummaries(caseResult, options);
    const variableOverrideSummary = getRegressionVariablePresetSummary(caseResult);
    const diagnosticLine = formatRegressionDiagnosticLine(caseResult, options);
    return {
      variableOverrideSummary,
      conditionTraceSummaries,
      diagnosticLine,
      hasDiagnostics: Boolean(diagnosticLine),
    };
  }

  function joinRegressionParts(parts = [], separator = " · ") {
    return toArray(parts).map((part) => cleanText(part)).filter(Boolean).join(separator);
  }

  function formatRegressionCaseLocation(caseResult = {}) {
    return joinRegressionParts([
      caseResult.anchorSceneId || caseResult.seedSceneId,
      caseResult.anchorBlockId,
    ], " / ");
  }

  function buildRegressionDiagnosticClipboardSummary(caseResult = {}, options = {}) {
    const diagnostics = serializeRegressionDiagnostics(caseResult, {
      maxItems: options.maxItems ?? 5,
      maxLength: options.maxLength ?? 800,
      traceMaxLength: options.traceMaxLength ?? 240,
    });
    const selectedOptions = toArray(caseResult.selectedOptionTexts).filter(Boolean).join(" / ");
    const conditionLines = toArray(diagnostics.conditionTraceSummaries)
      .map((item, index) => `${index + 1}. ${item}`)
      .join("\n");
    const recommendation = cleanText(options.recommendation || caseResult.recommendation);
    const location = formatRegressionCaseLocation(caseResult);
    const heading = cleanText(options.heading, "# 自动回归诊断");

    return [
      `${heading}：${cleanText(caseResult.sceneName, "未命名路线")}`,
      `状态：${cleanText(caseResult.statusLabel || caseResult.status, "未记录")}`,
      `来源：${joinRegressionParts([caseResult.chapterName, caseResult.sourceLabel]) || "未记录"}`,
      cleanText(caseResult.reason) ? `原因：${cleanText(caseResult.reason)}` : "",
      cleanText(caseResult.detail) ? `细节：${cleanText(caseResult.detail)}` : "",
      `步数：${caseResult.steps ?? 0} / 到过场景：${caseResult.visitedSceneCount ?? 0} / 选择次数：${caseResult.choiceCount ?? 0}`,
      diagnostics.variableOverrideSummary ? `测试预设：${diagnostics.variableOverrideSummary}` : "",
      selectedOptions ? `选择路线：${selectedOptions}` : "",
      conditionLines ? `条件判断：\n${conditionLines}` : "",
      recommendation ? `建议动作：${recommendation}` : "",
      location ? `定位：${location}` : "",
    ].filter(Boolean).join("\n");
  }

  function getRegressionSummary(regressionResult = {}) {
    return regressionResult.summary && typeof regressionResult.summary === "object"
      ? regressionResult.summary
      : {
          total: toArray(regressionResult.cases).length,
          passCount: toArray(regressionResult.cases).filter((caseResult) => caseResult?.status === "pass").length,
          warnCount: toArray(regressionResult.cases).filter((caseResult) => caseResult?.status === "warn").length,
          failCount: toArray(regressionResult.cases).filter((caseResult) => caseResult?.status === "fail").length,
        };
  }

  function buildRegressionDiagnosticBundleMarkdown({
    projectTitle = "Canvasia Project",
    generatedAt = new Date().toISOString(),
    regressionResult = null,
    fixQueue = [],
  } = {}) {
    const cases = toArray(regressionResult?.cases);
    const queue = toArray(fixQueue);
    const summary = getRegressionSummary(regressionResult ?? { cases });
    const queueCases = queue.length ? queue : cases.filter((caseResult) => caseResult?.status && caseResult.status !== "pass");
    const caseSections = queueCases.map((caseResult, index) =>
      buildRegressionDiagnosticClipboardSummary(caseResult, {
        heading: `## ${index + 1}. ${caseResult?.status === "fail" ? "优先修复" : "发布前复看"}`,
        recommendation: caseResult?.recommendation,
      })
    );

    return [
      `# ${cleanText(projectTitle, "Canvasia Project")} 自动回归诊断包`,
      "",
      `生成时间：${cleanText(generatedAt)}`,
      "",
      "## 总览",
      "",
      `- 已测试：${summary.total ?? cases.length} 条`,
      `- 通过：${summary.passCount ?? 0} 条`,
      `- 需要复看：${summary.warnCount ?? 0} 条`,
      `- 失败：${summary.failCount ?? 0} 条`,
      `- 优先修复 / 复看队列：${queueCases.length} 条`,
      "",
      "## 使用建议",
      "",
      "1. 先处理“优先修复”里的失败路线，再处理“发布前复看”。",
      "2. 每修完一条后重新跑自动回归，确认同一路线不再出现。",
      "3. 如果条件判断里出现变量预设，优先检查变量默认值、选项效果和条件分支。",
      "",
      "## 优先路线诊断",
      "",
      caseSections.length ? caseSections.join("\n\n") : "当前没有失败或需要复看的回归路线。",
      "",
    ].join("\n");
  }

  global.CanvasiaEditorRegressionDiagnostics = Object.freeze({
    buildRegressionDiagnosticBundleMarkdown,
    buildRegressionDiagnosticClipboardSummary,
    cleanText,
    compactText,
    formatRegressionCaseLocation,
    formatRegressionDiagnosticLine,
    getRegressionConditionTraceSummaries,
    getRegressionDiagnosticItems,
    getRegressionVariablePresetSummary,
    serializeRegressionDiagnostics,
  });
})(typeof window !== "undefined" ? window : globalThis);
