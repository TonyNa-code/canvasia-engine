(function attachCanvasiaRuntimeConditions(global) {
  "use strict";

  const STRING_CONDITION_OPERATORS = Object.freeze(["contains", "not_contains", "starts_with", "ends_with"]);
  const NUMERIC_CONDITION_OPERATORS = Object.freeze([">", ">=", "<", "<="]);
  const EQUALITY_CONDITION_OPERATORS = Object.freeze(["==", "=", "!="]);

  function cleanText(value, fallback = "") {
    const text = String(value ?? "").trim();
    return text || fallback;
  }

  function normalizeConditionOperator(operator) {
    const safeOperator = cleanText(operator, "==");
    return safeOperator === "=" ? "==" : safeOperator;
  }

  function evaluateConditionOperator(leftValue, operator, rightValue) {
    const safeOperator = normalizeConditionOperator(operator);

    switch (safeOperator) {
      case ">":
        return leftValue > rightValue;
      case ">=":
        return leftValue >= rightValue;
      case "<":
        return leftValue < rightValue;
      case "<=":
        return leftValue <= rightValue;
      case "!=":
        return leftValue !== rightValue;
      case "contains":
        return String(leftValue ?? "").includes(String(rightValue ?? ""));
      case "not_contains":
        return !String(leftValue ?? "").includes(String(rightValue ?? ""));
      case "starts_with":
        return String(leftValue ?? "").startsWith(String(rightValue ?? ""));
      case "ends_with":
        return String(leftValue ?? "").endsWith(String(rightValue ?? ""));
      case "==":
      default:
        return leftValue === rightValue;
    }
  }

  function getConditionVariableValue(variableId, variableValues = {}, options = {}) {
    if (typeof options.getVariableValue === "function") {
      return options.getVariableValue(variableId, variableValues, options);
    }
    if (variableValues && typeof variableValues.get === "function") {
      return variableValues.get(variableId);
    }
    if (variableValues && Object.hasOwn(variableValues, variableId)) {
      return variableValues[variableId];
    }
    if (typeof options.getVariableDefaultValue === "function") {
      return options.getVariableDefaultValue(variableId, options);
    }
    return undefined;
  }

  function normalizeConditionValue(variableId, value, options = {}) {
    if (typeof options.normalizeVariableValue === "function") {
      return options.normalizeVariableValue(variableId, value, options);
    }
    return value;
  }

  function evaluateConditionRule(rule = {}, variableValues = {}, options = {}) {
    const variableId = cleanText(rule?.variableId);
    const leftValue = normalizeConditionValue(
      variableId,
      getConditionVariableValue(variableId, variableValues, options),
      options
    );
    const rightValue = normalizeConditionValue(variableId, rule?.value, options);
    return evaluateConditionOperator(leftValue, rule?.operator, rightValue);
  }

  global.CanvasiaRuntimeConditions = Object.freeze({
    STRING_CONDITION_OPERATORS,
    NUMERIC_CONDITION_OPERATORS,
    EQUALITY_CONDITION_OPERATORS,
    normalizeConditionOperator,
    evaluateConditionOperator,
    evaluateConditionRule,
  });
})(typeof window !== "undefined" ? window : globalThis);
