export const TEXT_INPUT_VARIABLE_TYPES = Object.freeze(["string", "number"]);
export const TEXT_INPUT_MIN_LENGTH = 1;
export const TEXT_INPUT_MAX_LENGTH = 200;
export const TEXT_INPUT_DEFAULT_LENGTH = 32;

const TEXT_VARIABLE_TOKEN_PATTERN = /\{\{\s*([0-9A-Za-z_\-\u3400-\u9fff]{1,64})\s*\}\}/g;

function clampInteger(value, minimum, maximum, fallback) {
  const parsed = Number(value);
  const safeValue = Number.isFinite(parsed) ? Math.round(parsed) : fallback;
  return Math.min(maximum, Math.max(minimum, safeValue));
}

function hasOwn(source, key) {
  return Object.prototype.hasOwnProperty.call(source || {}, key);
}

function getCollectionValue(collection, key) {
  if (collection instanceof Map) {
    return collection.get(key);
  }
  return collection?.[key];
}

export function getSafeTextInputMaxLength(value, fallback = TEXT_INPUT_DEFAULT_LENGTH) {
  return clampInteger(value, TEXT_INPUT_MIN_LENGTH, TEXT_INPUT_MAX_LENGTH, fallback);
}

export function normalizeTextInputBlock(block = {}) {
  const prompt = String(block.prompt ?? "").trim();
  return {
    variableId: String(block.variableId ?? "").trim(),
    prompt: prompt || "请输入内容",
    placeholder: String(block.placeholder ?? "").trim(),
    defaultValue: block.defaultValue == null ? "" : String(block.defaultValue),
    maxLength: getSafeTextInputMaxLength(block.maxLength),
    allowEmpty: block.allowEmpty === true,
  };
}

export function collectRuntimeTextVariableIds(...values) {
  const ids = new Set();
  values.flat(Infinity).forEach((value) => {
    const text = String(value ?? "");
    for (const match of text.matchAll(TEXT_VARIABLE_TOKEN_PATTERN)) {
      ids.add(match[1]);
    }
  });
  return [...ids];
}

export function formatRuntimeVariableValue(value, variable = {}, options = {}) {
  if (typeof options.formatValue === "function") {
    return String(options.formatValue(value, variable));
  }
  if (typeof value === "boolean") {
    return value ? String(options.trueLabel ?? "是") : String(options.falseLabel ?? "否");
  }
  return value == null ? "" : String(value);
}

export function interpolateRuntimeText(text, variableValues = {}, options = {}) {
  const variablesById = options.variablesById;
  const keepUnknown = options.keepUnknown !== false;
  return String(text ?? "").replace(TEXT_VARIABLE_TOKEN_PATTERN, (token, variableId) => {
    const variable = getCollectionValue(variablesById, variableId);
    const hasValue = hasOwn(variableValues, variableId);
    if (!hasValue && !variable) {
      return keepUnknown ? token : "";
    }
    const fallback = variable?.defaultValue ?? "";
    const value = hasValue ? variableValues[variableId] : fallback;
    return formatRuntimeVariableValue(value, variable, options);
  });
}

export function sanitizeTextInputValue(rawValue, block = {}, variable = {}, options = {}) {
  const config = normalizeTextInputBlock(block);
  const variableType = String(variable?.type ?? "string").trim().toLowerCase();
  if (!TEXT_INPUT_VARIABLE_TYPES.includes(variableType)) {
    return {
      ok: false,
      error: "玩家输入只支持文本或数字变量。",
      value: null,
      text: "",
    };
  }

  let text = String(rawValue ?? "");
  if (options.trim !== false) {
    text = text.trim();
  }
  if (!text && config.defaultValue) {
    text = options.trim === false ? config.defaultValue : config.defaultValue.trim();
  }
  if (!text && !config.allowEmpty) {
    return {
      ok: false,
      error: "请先填写内容，或在卡片中允许留空。",
      value: null,
      text,
    };
  }
  if (Array.from(text).length > config.maxLength) {
    return {
      ok: false,
      error: `最多可以输入 ${config.maxLength} 个字符。`,
      value: null,
      text,
    };
  }

  let value = text;
  if (variableType === "number") {
    if (!text || !Number.isFinite(Number(text))) {
      return {
        ok: false,
        error: "这里需要填写一个有效数字。",
        value: null,
        text,
      };
    }
    value = Number(text);
  }
  if (typeof options.normalizeValue === "function") {
    value = options.normalizeValue(value, variable);
  }
  return {
    ok: true,
    error: "",
    value,
    text,
  };
}

const runtimeTextVariablesApi = Object.freeze({
  TEXT_INPUT_VARIABLE_TYPES,
  TEXT_INPUT_MIN_LENGTH,
  TEXT_INPUT_MAX_LENGTH,
  TEXT_INPUT_DEFAULT_LENGTH,
  getSafeTextInputMaxLength,
  normalizeTextInputBlock,
  collectRuntimeTextVariableIds,
  formatRuntimeVariableValue,
  interpolateRuntimeText,
  sanitizeTextInputValue,
});

globalThis.CanvasiaRuntimeTextVariables = runtimeTextVariablesApi;
