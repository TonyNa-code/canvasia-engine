export const RUNTIME_VARIABLE_SCOPES = Object.freeze(["save", "persistent"]);
export const PERSISTENT_VARIABLE_STORE_FORMAT_VERSION = 1;

export function getSafeRuntimeVariableScope(value) {
  return String(value ?? "").trim().toLowerCase() === "persistent" ? "persistent" : "save";
}

export function isPersistentRuntimeVariable(variable) {
  return getSafeRuntimeVariableScope(variable?.scope) === "persistent";
}

export function getPersistentRuntimeVariables(variables = []) {
  return (Array.isArray(variables) ? variables : []).filter(
    (variable) => variable?.id && isPersistentRuntimeVariable(variable)
  );
}

function getSafeNumber(value, fallback = 0) {
  const parsed = typeof value === "number" ? value : Number.parseFloat(value ?? "");
  return Number.isFinite(parsed) ? parsed : fallback;
}

function getNumberBound(value) {
  if (value === null || value === undefined || typeof value === "boolean") {
    return null;
  }
  const parsed = Number.parseFloat(value);
  return Number.isFinite(parsed) ? parsed : null;
}

export function coercePersistentRuntimeVariableValue(variable, value) {
  const rawType = String(variable?.type ?? "string").trim().toLowerCase();
  const type = rawType === "number" || rawType === "boolean" ? rawType : "string";
  const fallback = variable?.defaultValue;

  if (type === "number") {
    let nextValue = getSafeNumber(value, getSafeNumber(fallback, 0));
    const minValue = getNumberBound(variable?.min ?? variable?.minValue);
    const maxValue = getNumberBound(variable?.max ?? variable?.maxValue);
    if (minValue !== null) {
      nextValue = Math.max(nextValue, minValue);
    }
    if (maxValue !== null) {
      nextValue = Math.min(nextValue, maxValue);
    }
    return nextValue;
  }

  if (type === "boolean") {
    if (typeof value === "boolean") {
      return value;
    }
    if (typeof value === "string") {
      const normalized = value.trim().toLowerCase();
      if (["true", "1", "yes", "on"].includes(normalized)) return true;
      if (["false", "0", "no", "off", ""].includes(normalized)) return false;
    }
    return typeof fallback === "boolean" ? fallback : Boolean(value);
  }

  return value === null || value === undefined
    ? typeof fallback === "string"
      ? fallback
      : ""
    : String(value);
}

function getPersistentValueSource(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return {};
  }
  return value.values && typeof value.values === "object" && !Array.isArray(value.values)
    ? value.values
    : value;
}

export function sanitizePersistentRuntimeVariableState(value, variables = []) {
  const source = getPersistentValueSource(value);
  return getPersistentRuntimeVariables(variables).reduce((result, variable) => {
    const rawValue = Object.hasOwn(source, variable.id) ? source[variable.id] : variable.defaultValue;
    result[variable.id] = coercePersistentRuntimeVariableValue(variable, rawValue);
    return result;
  }, {});
}

export function mergePersistentRuntimeVariableState(variableState, variables = [], persistentState = {}) {
  return {
    ...(variableState && typeof variableState === "object" ? variableState : {}),
    ...sanitizePersistentRuntimeVariableState(persistentState, variables),
  };
}

export function collectPersistentRuntimeVariableState(variableState, variables = []) {
  return sanitizePersistentRuntimeVariableState(variableState, variables);
}

export function buildPersistentRuntimeVariableStore(variableState, variables = [], options = {}) {
  const now = typeof options.now === "function" ? options.now() : new Date().toISOString();
  return {
    formatVersion: PERSISTENT_VARIABLE_STORE_FORMAT_VERSION,
    updatedAt: String(now || ""),
    values: collectPersistentRuntimeVariableState(variableState, variables),
  };
}

export function getPersistentRuntimeVariableSummary(variableState, variables = []) {
  const definitions = getPersistentRuntimeVariables(variables);
  const values = sanitizePersistentRuntimeVariableState(variableState, variables);
  return {
    count: definitions.length,
    values,
    changedCount: definitions.filter(
      (variable) =>
        JSON.stringify(values[variable.id]) !==
        JSON.stringify(coercePersistentRuntimeVariableValue(variable, variable.defaultValue))
    ).length,
  };
}
