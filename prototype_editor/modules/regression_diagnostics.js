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

  global.CanvasiaEditorRegressionDiagnostics = Object.freeze({
    cleanText,
    compactText,
    formatRegressionDiagnosticLine,
    getRegressionConditionTraceSummaries,
    getRegressionDiagnosticItems,
    getRegressionVariablePresetSummary,
    serializeRegressionDiagnostics,
  });
})(typeof window !== "undefined" ? window : globalThis);
