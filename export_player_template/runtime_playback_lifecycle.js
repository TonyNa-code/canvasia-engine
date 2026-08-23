function getDefaultNow() {
  if (typeof globalThis.performance?.now === "function") {
    return globalThis.performance.now();
  }
  return Date.now();
}

function getSafeNow(now) {
  const value = Number(now());
  return Number.isFinite(value) ? value : 0;
}

function getSafeDelayMs(value) {
  const number = Number(value);
  return Number.isFinite(number) ? Math.max(0, Math.round(number)) : 0;
}

export function createPauseAwareDelayController(options = {}) {
  const now = typeof options.now === "function" ? options.now : getDefaultNow;
  const setTimer = options.setTimeout ?? globalThis.setTimeout?.bind(globalThis);
  const clearTimer = options.clearTimeout ?? globalThis.clearTimeout?.bind(globalThis);
  if (typeof setTimer !== "function" || typeof clearTimer !== "function") {
    throw new TypeError("Pause-aware delays require setTimeout and clearTimeout functions.");
  }

  let timerId = null;
  let task = null;
  let paused = options.paused === true;

  function clearArmedTimer() {
    if (timerId === null) {
      return;
    }
    clearTimer(timerId);
    timerId = null;
  }

  function getRemainingMs() {
    if (!task) {
      return 0;
    }
    if (timerId === null || paused) {
      return task.remainingMs;
    }
    return Math.max(0, Math.round(task.deadlineMs - getSafeNow(now)));
  }

  function getSnapshot() {
    return Object.freeze({
      scheduled: Boolean(task),
      paused,
      key: task?.key ?? "",
      remainingMs: getRemainingMs(),
    });
  }

  function armTask() {
    if (!task || paused || timerId !== null) {
      return;
    }
    task.deadlineMs = getSafeNow(now) + task.remainingMs;
    timerId = setTimer(() => {
      const completedTask = task;
      timerId = null;
      task = null;
      completedTask?.callback?.(Object.freeze({ key: completedTask.key }));
    }, task.remainingMs);
  }

  function cancel() {
    clearArmedTimer();
    task = null;
    return getSnapshot();
  }

  function schedule({ key = "", delayMs = 0, callback } = {}) {
    if (typeof callback !== "function") {
      throw new TypeError("Pause-aware delays require a callback.");
    }
    cancel();
    task = {
      key: String(key ?? ""),
      callback,
      remainingMs: getSafeDelayMs(delayMs),
      deadlineMs: 0,
    };
    armTask();
    return getSnapshot();
  }

  function pause() {
    if (paused) {
      return getSnapshot();
    }
    if (task && timerId !== null) {
      task.remainingMs = getRemainingMs();
    }
    clearArmedTimer();
    paused = true;
    return getSnapshot();
  }

  function resume() {
    if (!paused) {
      return getSnapshot();
    }
    paused = false;
    armTask();
    return getSnapshot();
  }

  return Object.freeze({ schedule, cancel, pause, resume, getSnapshot });
}

export function createDocumentPlaybackLifecycle(options = {}) {
  const documentRef = options.documentRef ?? globalThis.document;
  const windowRef = options.windowRef ?? globalThis.window;
  const now = typeof options.now === "function" ? options.now : getDefaultNow;
  const reasons = new Set();
  const listeners = [];
  let attached = false;
  let suspendedAtMs = null;
  let totalSuspendedMs = 0;
  let lastSuspendedDurationMs = 0;

  function getSnapshot(event = "none") {
    const currentDuration = suspendedAtMs === null
      ? 0
      : Math.max(0, Math.round(getSafeNow(now) - suspendedAtMs));
    return Object.freeze({
      event,
      attached,
      suspended: reasons.size > 0,
      reasons: Object.freeze(Array.from(reasons).sort()),
      currentSuspendedDurationMs: currentDuration,
      lastSuspendedDurationMs,
      totalSuspendedMs: totalSuspendedMs + currentDuration,
    });
  }

  function setSuspendedReason(reason, active) {
    const safeReason = String(reason ?? "").trim();
    if (!safeReason) {
      return getSnapshot();
    }
    const wasSuspended = reasons.size > 0;
    if (active) {
      reasons.add(safeReason);
    } else {
      reasons.delete(safeReason);
    }
    const isSuspended = reasons.size > 0;
    if (!wasSuspended && isSuspended) {
      suspendedAtMs = getSafeNow(now);
      const snapshot = getSnapshot("suspend");
      options.onSuspend?.(snapshot);
      return snapshot;
    }
    if (wasSuspended && !isSuspended) {
      const resumedAtMs = getSafeNow(now);
      lastSuspendedDurationMs = Math.max(0, Math.round(resumedAtMs - (suspendedAtMs ?? resumedAtMs)));
      totalSuspendedMs += lastSuspendedDurationMs;
      suspendedAtMs = null;
      const snapshot = getSnapshot("resume");
      options.onResume?.(snapshot);
      return snapshot;
    }
    return getSnapshot();
  }

  function addListener(target, eventName, callback) {
    if (typeof target?.addEventListener !== "function") {
      return;
    }
    target.addEventListener(eventName, callback);
    listeners.push([target, eventName, callback]);
  }

  function syncVisibility() {
    setSuspendedReason("hidden", documentRef?.hidden === true);
  }

  function attach() {
    if (attached) {
      return getSnapshot();
    }
    attached = true;
    addListener(documentRef, "visibilitychange", syncVisibility);
    addListener(documentRef, "freeze", () => setSuspendedReason("frozen", true));
    addListener(documentRef, "resume", () => setSuspendedReason("frozen", false));
    addListener(windowRef, "blur", () => setSuspendedReason("blurred", true));
    addListener(windowRef, "focus", () => setSuspendedReason("blurred", false));
    addListener(windowRef, "pagehide", () => setSuspendedReason("page-hidden", true));
    addListener(windowRef, "pageshow", () => {
      setSuspendedReason("page-hidden", false);
      syncVisibility();
    });
    syncVisibility();
    return getSnapshot();
  }

  function detach() {
    for (const [target, eventName, callback] of listeners.splice(0)) {
      target.removeEventListener?.(eventName, callback);
    }
    attached = false;
    reasons.clear();
    suspendedAtMs = null;
    return getSnapshot("detach");
  }

  return Object.freeze({
    attach,
    detach,
    getSnapshot,
    setSuspendedReason,
  });
}

const runtimePlaybackLifecycleApi = Object.freeze({
  createPauseAwareDelayController,
  createDocumentPlaybackLifecycle,
});

globalThis.CanvasiaRuntimePlaybackLifecycle = runtimePlaybackLifecycleApi;
