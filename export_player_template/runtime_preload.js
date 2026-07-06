const IMAGE_TYPES = new Set(["background", "sprite", "cg", "ui"]);
const AUDIO_TYPES = new Set(["bgm", "sfx", "voice"]);
const VIDEO_TYPES = new Set(["video"]);

export const RUNTIME_PRELOAD_PERFORMANCE_PROFILES = Object.freeze({
  standard: Object.freeze({
    key: "standard",
    label: "标准 PC / 网页",
    maxConcurrent: 4,
    timeoutMs: 12000,
    idleTimeoutMs: 1800,
    fallbackDelayMs: 120,
    deferredDelayMs: 0,
  }),
  web: Object.freeze({
    key: "web",
    label: "网页轻量",
    maxConcurrent: 3,
    timeoutMs: 10000,
    idleTimeoutMs: 2200,
    fallbackDelayMs: 180,
    deferredDelayMs: 120,
  }),
  mobile_low: Object.freeze({
    key: "mobile_low",
    label: "低配 / 移动端",
    maxConcurrent: 2,
    timeoutMs: 9000,
    idleTimeoutMs: 2800,
    fallbackDelayMs: 260,
    deferredDelayMs: 360,
  }),
  high_quality_pc: Object.freeze({
    key: "high_quality_pc",
    label: "高画质 PC",
    maxConcurrent: 6,
    timeoutMs: 15000,
    idleTimeoutMs: 1200,
    fallbackDelayMs: 80,
    deferredDelayMs: 0,
  }),
});

function toArray(value) {
  return Array.isArray(value) ? value : [];
}

function safeText(value) {
  return String(value ?? "").trim();
}

function normalizeSizeBytes(value) {
  const size = Number(value);
  return Number.isFinite(size) ? Math.max(0, Math.floor(size)) : 0;
}

function normalizePreloadPhase(value) {
  return ["critical", "early", "deferred", "library"].includes(value) ? value : "deferred";
}

export function getSafeRuntimePreloadPerformanceProfile(value, fallback = "standard") {
  const key = safeText(value || fallback).toLowerCase();
  return Object.hasOwn(RUNTIME_PRELOAD_PERFORMANCE_PROFILES, key) ? key : fallback;
}

export function getRuntimePreloadPerformanceProfileDefinition(value) {
  return RUNTIME_PRELOAD_PERFORMANCE_PROFILES[getSafeRuntimePreloadPerformanceProfile(value)];
}

function pickRuntimePreloadPerformanceProfile(options = {}) {
  return getSafeRuntimePreloadPerformanceProfile(
    options.performanceProfile ??
      options.runtimeSettings?.performanceProfile ??
      options.project?.runtimeSettings?.performanceProfile ??
      options.project?.performanceProfile
  );
}

function clampOption(value, fallback, minimum, maximum) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return fallback;
  }
  return Math.max(minimum, Math.min(maximum, Math.floor(numeric)));
}

export function resolveRuntimePreloadOptions(options = {}) {
  const profileKey = pickRuntimePreloadPerformanceProfile(options);
  const profile = getRuntimePreloadPerformanceProfileDefinition(profileKey);
  return {
    ...options,
    performanceProfile: profile.key,
    performanceProfileLabel: profile.label,
    maxConcurrent: clampOption(options.maxConcurrent, profile.maxConcurrent, 1, 8),
    timeoutMs: clampOption(options.timeoutMs, profile.timeoutMs, 2500, 60000),
    idleTimeoutMs: clampOption(options.idleTimeoutMs, profile.idleTimeoutMs, 250, 10000),
    fallbackDelayMs: clampOption(options.fallbackDelayMs, profile.fallbackDelayMs, 0, 5000),
    deferredDelayMs: clampOption(options.deferredDelayMs, profile.deferredDelayMs, 0, 10000),
  };
}

function normalizePreloadEntry(entry, index = 0) {
  if (!entry || typeof entry !== "object") {
    return null;
  }

  const assetId = safeText(entry.assetId);
  const url = safeText(entry.url);
  const type = safeText(entry.type);
  if (!assetId || !url || ![...IMAGE_TYPES, ...AUDIO_TYPES, ...VIDEO_TYPES].includes(type)) {
    return null;
  }

  return {
    assetId,
    url,
    type,
    name: safeText(entry.name) || assetId,
    phase: normalizePreloadPhase(entry.phase),
    priority: Number.isFinite(Number(entry.priority)) ? Number(entry.priority) : 0,
    sizeBytes: normalizeSizeBytes(entry.sizeBytes),
    sizeLabel: safeText(entry.sizeLabel),
    reason: safeText(entry.reason),
    preloadIndex: Number.isFinite(Number(entry.preloadIndex)) ? Number(entry.preloadIndex) : index + 1,
  };
}

export function normalizeRuntimePreloadManifest(manifest) {
  const entries = toArray(manifest?.entries)
    .map((entry, index) => normalizePreloadEntry(entry, index))
    .filter(Boolean)
    .sort((left, right) => {
      if (right.priority !== left.priority) {
        return right.priority - left.priority;
      }
      return left.preloadIndex - right.preloadIndex;
    });

  return {
    formatVersion: Number(manifest?.formatVersion) || 1,
    entrySceneId: safeText(manifest?.entrySceneId),
    entries,
  };
}

export function getRuntimePreloadSummary(manifest) {
  const normalized = normalizeRuntimePreloadManifest(manifest);
  const summary = {
    totalCount: normalized.entries.length,
    criticalCount: 0,
    earlyCount: 0,
    deferredCount: 0,
    libraryCount: 0,
    imageCount: 0,
    audioCount: 0,
    videoCount: 0,
    totalSizeBytes: 0,
    criticalSizeBytes: 0,
    earlySizeBytes: 0,
    deferredSizeBytes: 0,
    librarySizeBytes: 0,
    imageSizeBytes: 0,
    audioSizeBytes: 0,
    videoSizeBytes: 0,
  };

  normalized.entries.forEach((entry) => {
    summary.totalSizeBytes += entry.sizeBytes;
    if (entry.phase === "critical") {
      summary.criticalCount += 1;
      summary.criticalSizeBytes += entry.sizeBytes;
    } else if (entry.phase === "early") {
      summary.earlyCount += 1;
      summary.earlySizeBytes += entry.sizeBytes;
    } else if (entry.phase === "library") {
      summary.libraryCount += 1;
      summary.librarySizeBytes += entry.sizeBytes;
    } else {
      summary.deferredCount += 1;
      summary.deferredSizeBytes += entry.sizeBytes;
    }

    if (IMAGE_TYPES.has(entry.type)) {
      summary.imageCount += 1;
      summary.imageSizeBytes += entry.sizeBytes;
    } else if (AUDIO_TYPES.has(entry.type)) {
      summary.audioCount += 1;
      summary.audioSizeBytes += entry.sizeBytes;
    } else if (VIDEO_TYPES.has(entry.type)) {
      summary.videoCount += 1;
      summary.videoSizeBytes += entry.sizeBytes;
    }
  });

  return summary;
}

function resolveRuntimeUrl(url, baseUrl = globalThis?.location?.href) {
  try {
    return new URL(url, baseUrl).href;
  } catch {
    return url;
  }
}

function settleWithTimeout(settle, timeoutMs) {
  const timeoutId = globalThis.setTimeout(() => settle(false), timeoutMs);
  return () => globalThis.clearTimeout(timeoutId);
}

function preloadImage(entry, options) {
  const ImageCtor = options.ImageCtor ?? globalThis.Image;
  if (typeof ImageCtor !== "function") {
    return Promise.resolve(false);
  }

  return new Promise((resolve) => {
    const image = new ImageCtor();
    const cleanupTimeout = settleWithTimeout(resolve, options.timeoutMs);
    image.onload = () => {
      cleanupTimeout();
      resolve(true);
    };
    image.onerror = () => {
      cleanupTimeout();
      resolve(false);
    };
    image.src = resolveRuntimeUrl(entry.url, options.baseUrl);
  });
}

function preloadAudio(entry, options) {
  const AudioCtor = options.AudioCtor ?? globalThis.Audio;
  if (typeof AudioCtor !== "function") {
    return Promise.resolve(false);
  }

  return new Promise((resolve) => {
    const audio = new AudioCtor();
    const cleanupTimeout = settleWithTimeout(resolve, options.timeoutMs);
    const cleanup = (ok) => {
      cleanupTimeout();
      audio.onloadedmetadata = null;
      audio.oncanplaythrough = null;
      audio.onerror = null;
      resolve(ok);
    };
    audio.preload = "metadata";
    audio.onloadedmetadata = () => cleanup(true);
    audio.oncanplaythrough = () => cleanup(true);
    audio.onerror = () => cleanup(false);
    audio.src = resolveRuntimeUrl(entry.url, options.baseUrl);
    if (typeof audio.load === "function") {
      audio.load();
    }
  });
}

function preloadVideo(entry, options) {
  const documentRef = options.documentRef ?? globalThis.document;
  if (!documentRef || typeof documentRef.createElement !== "function") {
    return Promise.resolve(false);
  }

  return new Promise((resolve) => {
    const video = documentRef.createElement("video");
    const cleanupTimeout = settleWithTimeout(resolve, options.timeoutMs);
    const cleanup = (ok) => {
      cleanupTimeout();
      video.onloadedmetadata = null;
      video.onerror = null;
      video.removeAttribute?.("src");
      resolve(ok);
    };
    video.preload = "metadata";
    video.onloadedmetadata = () => cleanup(true);
    video.onerror = () => cleanup(false);
    video.src = resolveRuntimeUrl(entry.url, options.baseUrl);
    if (typeof video.load === "function") {
      video.load();
    }
  });
}

function preloadEntry(entry, options) {
  if (IMAGE_TYPES.has(entry.type)) {
    return preloadImage(entry, options);
  }
  if (AUDIO_TYPES.has(entry.type)) {
    return preloadAudio(entry, options);
  }
  if (VIDEO_TYPES.has(entry.type)) {
    return preloadVideo(entry, options);
  }
  return Promise.resolve(false);
}

function scheduleIdle(callback, idleScheduler = globalThis.requestIdleCallback, options = {}) {
  const runIdle = () => {
    if (typeof idleScheduler === "function") {
      idleScheduler(callback, { timeout: options.idleTimeoutMs ?? 1800 });
      return;
    }
    globalThis.setTimeout(callback, options.fallbackDelayMs ?? 120);
  };
  const deferredDelayMs = Number(options.deferredDelayMs);
  if (Number.isFinite(deferredDelayMs) && deferredDelayMs > 0) {
    globalThis.setTimeout(runIdle, deferredDelayMs);
    return;
  }
  if (typeof idleScheduler === "function") {
    idleScheduler(callback, { timeout: options.idleTimeoutMs ?? 1800 });
    return;
  }
  globalThis.setTimeout(callback, options.fallbackDelayMs ?? 120);
}

export function startRuntimePreload(manifest, options = {}) {
  const normalized = normalizeRuntimePreloadManifest(manifest);
  const resolvedOptions = resolveRuntimePreloadOptions(options);
  const maxConcurrent = resolvedOptions.maxConcurrent;
  const status = {
    totalCount: normalized.entries.length,
    queuedCount: normalized.entries.length,
    loadedCount: 0,
    failedCount: 0,
    criticalCount: normalized.entries.filter((entry) => entry.phase === "critical").length,
    activeCount: 0,
    waitingCount: normalized.entries.length,
    maxConcurrent,
    performanceProfile: resolvedOptions.performanceProfile,
    performanceProfileLabel: resolvedOptions.performanceProfileLabel,
    started: normalized.entries.length > 0,
    finished: normalized.entries.length === 0,
  };
  const safeOptions = {
    timeoutMs: resolvedOptions.timeoutMs,
    baseUrl: resolvedOptions.baseUrl,
    ImageCtor: resolvedOptions.ImageCtor,
    AudioCtor: resolvedOptions.AudioCtor,
    documentRef: resolvedOptions.documentRef,
  };
  const onProgress = typeof resolvedOptions.onProgress === "function" ? resolvedOptions.onProgress : null;
  let stopped = false;
  let deferredReady = false;

  const criticalQueue = normalized.entries.filter((entry) => entry.phase === "critical");
  const deferredQueue = normalized.entries.filter((entry) => entry.phase !== "critical");
  const updateWaitingCount = () => {
    status.waitingCount = criticalQueue.length + (deferredReady ? deferredQueue.length : 0);
  };
  const emitProgress = () => onProgress?.({ ...status });

  const mark = (ok) => {
    if (stopped) {
      return;
    }
    status.activeCount = Math.max(0, status.activeCount - 1);
    if (ok) {
      status.loadedCount += 1;
    } else {
      status.failedCount += 1;
    }
    status.finished = status.loadedCount + status.failedCount >= status.totalCount;
    updateWaitingCount();
    emitProgress();
    pumpQueue();
  };

  const takeNextEntry = () => {
    if (criticalQueue.length) {
      return criticalQueue.shift();
    }
    if (deferredReady && deferredQueue.length) {
      return deferredQueue.shift();
    }
    return null;
  };

  function pumpQueue() {
    if (stopped || status.finished) {
      return;
    }
    updateWaitingCount();
    while (status.activeCount < maxConcurrent) {
      const entry = takeNextEntry();
      if (!entry) {
        break;
      }
      status.activeCount += 1;
      updateWaitingCount();
      preloadEntry(entry, safeOptions).then(mark).catch(() => mark(false));
    }
  }

  pumpQueue();
  scheduleIdle(() => {
    if (!stopped) {
      deferredReady = true;
      pumpQueue();
    }
  }, resolvedOptions.requestIdleCallback, resolvedOptions);

  return {
    stop() {
      stopped = true;
      criticalQueue.length = 0;
      deferredQueue.length = 0;
      status.activeCount = 0;
      status.waitingCount = 0;
      status.finished = true;
    },
    getStatus() {
      return { ...status };
    },
  };
}
