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

  global.CanvasiaEditorRegressionDiagnostics = Object.freeze({
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
