// Timed choice configuration and lifecycle shared by the editor and Web Runtime.

export const TIMED_CHOICE_MIN_SECONDS = 1;
export const TIMED_CHOICE_MAX_SECONDS = 300;
export const TIMED_CHOICE_PRESET_SECONDS = Object.freeze([5, 10, 15, 30]);

function clamp(value, minimum, maximum) {
  return Math.min(Math.max(value, minimum), maximum);
}

function getSafeNumber(value, fallback = 0) {
  const number = Number.parseFloat(value ?? "");
  return Number.isFinite(number) ? number : fallback;
}

function cleanText(value) {
  return String(value ?? "").trim();
}

export function getSafeTimedChoiceSeconds(value, fallback = 0) {
  const seconds = getSafeNumber(value, fallback);
  if (seconds <= 0) return 0;
  return Math.round(clamp(seconds, TIMED_CHOICE_MIN_SECONDS, TIMED_CHOICE_MAX_SECONDS) * 10) / 10;
}

export function sanitizeTimedChoiceConfig(value = {}) {
  const source = value && typeof value === "object" ? value : {};
  const timeoutSeconds = getSafeTimedChoiceSeconds(
    source.timeoutSeconds ?? source.choiceTimeoutSeconds,
    0
  );
  return Object.freeze({
    enabled: timeoutSeconds > 0,
    timeoutSeconds,
    timeoutMs: Math.round(timeoutSeconds * 1000),
    timeoutOptionId: cleanText(source.timeoutOptionId ?? source.choiceTimeoutOptionId),
  });
}

export function isTimedChoiceOptionSelectable(option = {}) {
  return option.choiceVisible !== false && option.choiceEnabled !== false && option.disabled !== true;
}

export function resolveTimedChoiceTarget(choiceOptions = [], configuredOptionId = "") {
  const options = Array.isArray(choiceOptions) ? choiceOptions : [];
  const safeOptionId = cleanText(configuredOptionId);
  const configured = safeOptionId
    ? options.find((option) => cleanText(option?.id) === safeOptionId)
    : null;
  const target = configured && isTimedChoiceOptionSelectable(configured)
    ? configured
    : options.find(isTimedChoiceOptionSelectable);
  return target ? cleanText(target.id) : "";
}

export function sanitizeTimedChoiceState(value, configValue = {}) {
  if (!value || typeof value !== "object") return null;
  const config = sanitizeTimedChoiceConfig(configValue);
  const choiceKey = cleanText(value.choiceKey);
  if (!config.enabled || !choiceKey) return null;
  return Object.freeze({
    choiceKey,
    targetOptionId: cleanText(value.targetOptionId),
    durationMs: config.timeoutMs,
    remainingMs: Math.round(clamp(getSafeNumber(value.remainingMs, config.timeoutMs), 0, config.timeoutMs)),
  });
}

export function formatTimedChoiceRemaining(remainingMs) {
  const seconds = Math.max(0, getSafeNumber(remainingMs, 0)) / 1000;
  if (seconds >= 10) return `${Math.ceil(seconds)} 秒`;
  return `${Math.max(0, Math.ceil(seconds * 10) / 10).toFixed(1)} 秒`;
}

export function createTimedChoiceController(options = {}) {
  const scope = options.scope ?? globalThis;
  const now = typeof options.now === "function" ? options.now : () => scope.performance?.now?.() ?? Date.now();
  const setIntervalFn = options.setInterval ?? scope.setInterval?.bind(scope);
  const clearIntervalFn = options.clearInterval ?? scope.clearInterval?.bind(scope);
  const onTick = typeof options.onTick === "function" ? options.onTick : () => {};
  const onTimeout = typeof options.onTimeout === "function" ? options.onTimeout : () => {};
  const tickIntervalMs = clamp(Math.round(getSafeNumber(options.tickIntervalMs, 100)), 50, 1000);
  let timer = null;
  let state = null;

  function clearTimer() {
    if (timer != null && clearIntervalFn) clearIntervalFn(timer);
    timer = null;
  }

  function buildSnapshot(currentNow = now()) {
    if (!state) {
      return Object.freeze({ active: false, paused: false, expired: false, choiceKey: "", targetOptionId: "", durationMs: 0, remainingMs: 0, progress: 0 });
    }
    if (state.active && !state.paused) {
      state.remainingMs = Math.max(0, state.deadlineMs - currentNow);
    }
    const progress = state.durationMs > 0
      ? clamp(1 - state.remainingMs / state.durationMs, 0, 1)
      : 0;
    return Object.freeze({
      active: state.active,
      paused: state.paused,
      expired: state.expired,
      choiceKey: state.choiceKey,
      targetOptionId: state.targetOptionId,
      durationMs: state.durationMs,
      remainingMs: Math.round(state.remainingMs),
      progress: Math.round(progress * 1000) / 1000,
    });
  }

  function emitTick(currentNow = now()) {
    const snapshot = buildSnapshot(currentNow);
    onTick(snapshot);
    return snapshot;
  }

  function handleTick() {
    if (!state?.active || state.paused) return;
    const snapshot = emitTick();
    if (snapshot.remainingMs > 0) return;
    state.active = false;
    state.expired = true;
    clearTimer();
    const expiredSnapshot = buildSnapshot();
    onTick(expiredSnapshot);
    onTimeout(state.targetOptionId, expiredSnapshot);
  }

  function schedule() {
    clearTimer();
    if (state?.active && !state.paused && setIntervalFn) {
      timer = setIntervalFn(handleTick, tickIntervalMs);
    }
  }

  function stop() {
    clearTimer();
    state = null;
    onTick(buildSnapshot());
  }

  function start({ choiceKey, block, config, choiceOptions, remainingMs, paused = false } = {}) {
    const safeConfig = sanitizeTimedChoiceConfig(config ?? block);
    const targetOptionId = resolveTimedChoiceTarget(choiceOptions, safeConfig.timeoutOptionId);
    const safeChoiceKey = cleanText(choiceKey);
    if (!safeConfig.enabled || !safeChoiceKey || !targetOptionId) {
      stop();
      return buildSnapshot();
    }
    if (state?.active && state.choiceKey === safeChoiceKey) {
      state.targetOptionId = targetOptionId;
      if (state.paused !== Boolean(paused)) return setPaused(paused);
      return emitTick();
    }
    const initialRemainingMs = Number.isFinite(Number(remainingMs))
      ? clamp(Number(remainingMs), 0, safeConfig.timeoutMs)
      : safeConfig.timeoutMs;
    const currentNow = now();
    state = {
      active: initialRemainingMs > 0,
      paused: Boolean(paused),
      expired: initialRemainingMs <= 0,
      choiceKey: safeChoiceKey,
      targetOptionId,
      durationMs: safeConfig.timeoutMs,
      remainingMs: initialRemainingMs,
      deadlineMs: currentNow + initialRemainingMs,
    };
    schedule();
    const snapshot = emitTick(currentNow);
    if (snapshot.expired) onTimeout(targetOptionId, snapshot);
    return snapshot;
  }

  function setPaused(paused) {
    if (!state?.active || state.paused === Boolean(paused)) return buildSnapshot();
    const currentNow = now();
    if (paused) {
      buildSnapshot(currentNow);
      state.paused = true;
      clearTimer();
    } else {
      state.paused = false;
      state.deadlineMs = currentNow + state.remainingMs;
      schedule();
    }
    return emitTick(currentNow);
  }

  function serialize() {
    const snapshot = buildSnapshot();
    if (!snapshot.active && !snapshot.expired) return null;
    return {
      choiceKey: snapshot.choiceKey,
      targetOptionId: snapshot.targetOptionId,
      durationMs: snapshot.durationMs,
      remainingMs: snapshot.remainingMs,
    };
  }

  return Object.freeze({ start, stop, setPaused, tick: handleTick, snapshot: buildSnapshot, serialize });
}

const runtimeTimedChoicesApi = Object.freeze({
  TIMED_CHOICE_MIN_SECONDS,
  TIMED_CHOICE_MAX_SECONDS,
  TIMED_CHOICE_PRESET_SECONDS,
  getSafeTimedChoiceSeconds,
  sanitizeTimedChoiceConfig,
  isTimedChoiceOptionSelectable,
  resolveTimedChoiceTarget,
  sanitizeTimedChoiceState,
  formatTimedChoiceRemaining,
  createTimedChoiceController,
});

globalThis.CanvasiaRuntimeTimedChoices = runtimeTimedChoicesApi;
