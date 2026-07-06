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
    backgroundBatchSize: 3,
    backgroundBatchDelayMs: 120,
    phaseDelayMs: Object.freeze({
      early: 0,
      deferred: 900,
      library: 2400,
    }),
  }),
  web: Object.freeze({
    key: "web",
    label: "网页轻量",
    maxConcurrent: 3,
    timeoutMs: 10000,
    idleTimeoutMs: 2200,
    fallbackDelayMs: 180,
    deferredDelayMs: 120,
    backgroundBatchSize: 2,
    backgroundBatchDelayMs: 220,
    phaseDelayMs: Object.freeze({
      early: 120,
      deferred: 1600,
      library: 4200,
    }),
  }),
  mobile_low: Object.freeze({
    key: "mobile_low",
    label: "低配 / 移动端",
    maxConcurrent: 2,
    timeoutMs: 9000,
    idleTimeoutMs: 2800,
    fallbackDelayMs: 260,
    deferredDelayMs: 360,
    backgroundBatchSize: 1,
    backgroundBatchDelayMs: 420,
    phaseDelayMs: Object.freeze({
      early: 360,
      deferred: 3200,
      library: 8000,
    }),
  }),
  high_quality_pc: Object.freeze({
    key: "high_quality_pc",
    label: "高画质 PC",
    maxConcurrent: 6,
    timeoutMs: 15000,
    idleTimeoutMs: 1200,
    fallbackDelayMs: 80,
    deferredDelayMs: 0,
    backgroundBatchSize: 5,
    backgroundBatchDelayMs: 80,
    phaseDelayMs: Object.freeze({
      early: 0,
      deferred: 420,
      library: 1200,
    }),
  }),
});

const PRELOAD_PHASE_ORDER = Object.freeze(["critical", "early", "deferred", "library"]);
const BACKGROUND_PRELOAD_PHASES = Object.freeze(["early", "deferred", "library"]);

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

function normalizeAssetIdSet(value) {
  if (!value) {
    return new Set();
  }
  const source =
    value instanceof Set
      ? Array.from(value)
      : Array.isArray(value)
        ? value
        : typeof value?.[Symbol.iterator] === "function"
          ? Array.from(value)
          : [];
  return new Set(source.map(safeText).filter(Boolean));
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

function clampPercent(numerator, denominator) {
  const safeNumerator = Number(numerator);
  const safeDenominator = Number(denominator);
  if (!Number.isFinite(safeNumerator) || !Number.isFinite(safeDenominator) || safeDenominator <= 0) {
    return 0;
  }
  return Math.max(0, Math.min(100, Math.round((safeNumerator / safeDenominator) * 100)));
}

function getStatusReadyCount(status) {
  if (!status || typeof status !== "object") {
    return 0;
  }
  if (Number.isFinite(Number(status.readyCount))) {
    return Math.max(0, Number(status.readyCount));
  }
  return Math.max(0, Number(status.loadedCount) || 0);
}

function getStatusTotalCount(status) {
  if (!status || typeof status !== "object") {
    return 0;
  }
  return Math.max(0, Number(status.totalCount) || 0);
}

function getStatusSkippedCount(status) {
  if (!status || typeof status !== "object") {
    return 0;
  }
  return Math.max(0, Number(status.skippedCount) || 0);
}

function getStatusPendingCount(status) {
  if (!status || typeof status !== "object") {
    return 0;
  }
  return Math.max(0, Number(status.pendingCount) || 0);
}

export function buildRuntimePreloadCacheEfficiencySummary(statuses = {}) {
  const source = statuses && typeof statuses === "object" ? statuses : {};
  const preloadStatus = source.preloadStatus ?? source.runtimePreloadStatus ?? null;
  const prefetchStatus = source.prefetchStatus ?? source.runtimeScenePrefetchStatus ?? null;
  const preloadTotal = getStatusTotalCount(preloadStatus);
  const prefetchTotal = getStatusTotalCount(prefetchStatus);
  const preloadReady = getStatusReadyCount(preloadStatus);
  const prefetchReady = getStatusReadyCount(prefetchStatus);
  const preloadSkipped = getStatusSkippedCount(preloadStatus);
  const prefetchSkipped = getStatusSkippedCount(prefetchStatus);
  const preloadPending = getStatusPendingCount(preloadStatus);
  const prefetchPending = getStatusPendingCount(prefetchStatus);
  const totalCount = preloadTotal + prefetchTotal;
  const readyCount = preloadReady + prefetchReady;
  const skippedCount = preloadSkipped + prefetchSkipped;
  return Object.freeze({
    status: totalCount <= 0 ? "empty" : preloadPending + prefetchPending > 0 ? "warming" : "ready",
    totalCount,
    readyCount,
    pendingCount: preloadPending + prefetchPending,
    skippedCount,
    preloadSkippedCount: preloadSkipped,
    prefetchSkippedCount: prefetchSkipped,
    readyPercent: clampPercent(readyCount, totalCount),
    reusePercent: clampPercent(skippedCount, totalCount),
  });
}

function coerceRuntimePreloadSummary(value) {
  const source = value?.summary ?? value;
  if (source && typeof source === "object" && Number.isFinite(Number(source.totalCount))) {
    return source;
  }
  return getRuntimePreloadSummary(source);
}

export function formatRuntimePreloadBytes(bytes) {
  const units = ["B", "KB", "MB", "GB"];
  let value = Number(bytes);
  if (!Number.isFinite(value) || value <= 0) {
    return "0 B";
  }
  let unitIndex = 0;
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }
  if (unitIndex === 0) {
    return `${Math.round(value)} B`;
  }
  return `${value.toFixed(1)} ${units[unitIndex]}`;
}

export function formatRuntimePreloadSize(summary) {
  const source = coerceRuntimePreloadSummary(summary);
  const criticalSizeBytes = Number(source?.criticalSizeBytes ?? 0);
  const totalSizeBytes = Number(source?.totalSizeBytes ?? 0);
  if (!Number.isFinite(totalSizeBytes) || totalSizeBytes <= 0) {
    return "";
  }
  const criticalLabel = formatRuntimePreloadBytes(Math.max(0, criticalSizeBytes));
  const totalLabel = formatRuntimePreloadBytes(totalSizeBytes);
  return `首屏体积 ${criticalLabel} / 预热合计 ${totalLabel}`;
}

export function buildRuntimeScenePrefetchStatusText(status) {
  if (!status?.totalCount) {
    return "";
  }
  const readyCount = getStatusReadyCount(status);
  const failedCount = Math.max(0, Number(status.failedCount) || 0);
  const pendingCount = getStatusPendingCount(status);
  const skippedCount = getStatusSkippedCount(status);
  const pendingText = pendingCount > 0 ? `，待处理 ${pendingCount} 个` : "";
  const failureText = failedCount > 0 ? `，${failedCount} 个稍后重试` : "";
  const skippedText = skippedCount > 0 ? `，复用 ${skippedCount} 个` : "";
  return `路线预取 ${readyCount}/${status.totalCount}${pendingText}${skippedText}${failureText}`;
}

export function buildRuntimePreloadStatusDigest(options = {}) {
  const source = options && typeof options === "object" ? options : {};
  const summary = coerceRuntimePreloadSummary(source.summary ?? source.manifest ?? source.runtimePreloadManifest);
  const preloadStatus = source.preloadStatus ?? source.runtimePreloadStatus ?? null;
  const prefetchStatus = source.prefetchStatus ?? source.runtimeScenePrefetchStatus ?? null;
  const prefetchText = buildRuntimeScenePrefetchStatusText(prefetchStatus);

  if (!summary.totalCount) {
    const fallbackText = prefetchText || "没有需要预热的素材";
    return Object.freeze({
      status: prefetchText ? "prefetching" : "empty",
      text: fallbackText,
      lines: Object.freeze([fallbackText]),
      sizeText: "",
      prefetchText,
      efficiency: buildRuntimePreloadCacheEfficiencySummary({ preloadStatus, prefetchStatus }),
    });
  }

  const cacheEfficiency = buildRuntimePreloadCacheEfficiencySummary({
    preloadStatus,
    prefetchStatus,
  });
  const readyCount = getStatusReadyCount(preloadStatus);
  const failedCount = Math.max(0, Number(preloadStatus?.failedCount) || 0);
  const pendingCount = getStatusPendingCount(preloadStatus);
  const skippedCount = getStatusSkippedCount(preloadStatus);
  const failureText = failedCount > 0 ? ` · ${failedCount} 个稍后重试` : "";
  const skippedText = skippedCount > 0 ? ` · 复用 ${skippedCount} 个` : "";
  const pendingText = pendingCount > 0 ? ` · 待处理 ${pendingCount} 个` : "";
  const sizeText = formatRuntimePreloadSize(summary);
  const profileText = preloadStatus?.performanceProfileLabel ? `档位 ${preloadStatus.performanceProfileLabel}` : "";
  const readyPhaseCount = Array.isArray(preloadStatus?.readyPhases) ? preloadStatus.readyPhases.length : 0;
  const stagedText = readyPhaseCount > 0 ? `分阶段预热 ${readyPhaseCount}/4` : "";
  const efficiencyText =
    cacheEfficiency.totalCount > 0
      ? `准备率 ${cacheEfficiency.readyPercent}% · 复用率 ${cacheEfficiency.reusePercent}%`
      : "";
  const lines = [
    `首屏 ${summary.criticalCount} 个`,
    `全局 ${summary.totalCount} 个`,
    profileText,
    stagedText,
    sizeText,
    `图片 ${summary.imageCount}`,
    `音频 ${summary.audioCount}`,
    `视频 ${summary.videoCount}`,
    `已准备 ${readyCount}/${summary.totalCount}${pendingText}${skippedText}${failureText}`,
    efficiencyText,
    prefetchText,
  ].filter(Boolean);
  const statusLabel = failedCount > 0 ? "retrying" : pendingCount > 0 || readyCount < summary.totalCount ? "warming" : "ready";
  return Object.freeze({
    status: statusLabel,
    text: lines.join(" · "),
    lines: Object.freeze(lines),
    sizeText,
    prefetchText,
    efficiency: cacheEfficiency,
  });
}

export function buildRuntimePreloadStatusText(options = {}) {
  return buildRuntimePreloadStatusDigest(options).text;
}

export function buildRuntimePreloadMetaText(manifestOrSummary) {
  const summary = coerceRuntimePreloadSummary(manifestOrSummary);
  if (!summary.totalCount) {
    return "";
  }
  const sizeText = formatRuntimePreloadSize(summary);
  return ` · 预热 ${summary.criticalCount}/${summary.totalCount} 个素材${sizeText ? ` · ${sizeText}` : ""}`;
}

function resolvePhaseDelayOptions(options = {}, profile = {}) {
  const customPhaseDelayMs = options.phaseDelayMs ?? options.phaseDelaysMs ?? {};
  const profilePhaseDelayMs = profile.phaseDelayMs ?? {};
  const legacyDeferredDelayMs = Number.isFinite(Number(options.deferredDelayMs)) ? Number(options.deferredDelayMs) : null;
  return {
    early: clampOption(
      customPhaseDelayMs.early,
      legacyDeferredDelayMs ?? profilePhaseDelayMs.early ?? profile.deferredDelayMs ?? 0,
      0,
      60000
    ),
    deferred: clampOption(
      customPhaseDelayMs.deferred,
      legacyDeferredDelayMs ?? profilePhaseDelayMs.deferred ?? profile.deferredDelayMs ?? 0,
      0,
      60000
    ),
    library: clampOption(
      customPhaseDelayMs.library,
      legacyDeferredDelayMs ?? profilePhaseDelayMs.library ?? profilePhaseDelayMs.deferred ?? profile.deferredDelayMs ?? 0,
      0,
      60000
    ),
  };
}

export function resolveRuntimePreloadOptions(options = {}) {
  const profileKey = pickRuntimePreloadPerformanceProfile(options);
  const profile = getRuntimePreloadPerformanceProfileDefinition(profileKey);
  const phaseDelayMs = resolvePhaseDelayOptions(options, profile);
  return {
    ...options,
    performanceProfile: profile.key,
    performanceProfileLabel: profile.label,
    maxConcurrent: clampOption(options.maxConcurrent, profile.maxConcurrent, 1, 8),
    timeoutMs: clampOption(options.timeoutMs, profile.timeoutMs, 2500, 60000),
    idleTimeoutMs: clampOption(options.idleTimeoutMs, profile.idleTimeoutMs, 250, 10000),
    fallbackDelayMs: clampOption(options.fallbackDelayMs, profile.fallbackDelayMs, 0, 5000),
    deferredDelayMs: phaseDelayMs.early,
    phaseDelayMs,
    backgroundBatchSize: clampOption(options.backgroundBatchSize, profile.backgroundBatchSize, 1, 16),
    backgroundBatchDelayMs: clampOption(options.backgroundBatchDelayMs, profile.backgroundBatchDelayMs, 0, 10000),
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
  const skipAssetIds = normalizeAssetIdSet(resolvedOptions.skipAssetIds ?? resolvedOptions.cachedAssetIds);
  const skippedEntries = normalized.entries.filter((entry) => skipAssetIds.has(entry.assetId));
  const entriesToLoad = normalized.entries.filter((entry) => !skipAssetIds.has(entry.assetId));
  const phaseQueues = PRELOAD_PHASE_ORDER.reduce((queues, phase) => {
    queues[phase] = entriesToLoad.filter((entry) => entry.phase === phase);
    return queues;
  }, {});
  const readyPhases = new Set(["critical"]);
  const scheduledPhases = new Set();
  const skippedAssetIds = skippedEntries.map((entry) => entry.assetId);
  const status = {
    totalCount: normalized.entries.length,
    queuedCount: entriesToLoad.length,
    loadedCount: 0,
    failedCount: 0,
    skippedCount: skippedEntries.length,
    readyCount: skippedEntries.length,
    criticalCount: phaseQueues.critical.length,
    activeCount: 0,
    waitingCount: entriesToLoad.length,
    pendingCount: entriesToLoad.length,
    maxConcurrent,
    backgroundBatchSize: resolvedOptions.backgroundBatchSize,
    backgroundBatchDelayMs: resolvedOptions.backgroundBatchDelayMs,
    performanceProfile: resolvedOptions.performanceProfile,
    performanceProfileLabel: resolvedOptions.performanceProfileLabel,
    readyPhases: ["critical"],
    started: normalized.entries.length > 0,
    finished: entriesToLoad.length === 0,
    loadedAssetIds: [],
    failedAssetIds: [],
    skippedAssetIds,
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
  let backgroundPumpScheduled = false;
  const getStatusSnapshot = () => ({
    ...status,
    loadedAssetIds: [...status.loadedAssetIds],
    failedAssetIds: [...status.failedAssetIds],
    skippedAssetIds: [...status.skippedAssetIds],
  });
  const updateWaitingCount = () => {
    status.waitingCount = PRELOAD_PHASE_ORDER.reduce(
      (total, phase) => total + (readyPhases.has(phase) ? phaseQueues[phase].length : 0),
      0
    );
    status.pendingCount = PRELOAD_PHASE_ORDER.reduce((total, phase) => total + phaseQueues[phase].length, 0);
    status.readyPhases = PRELOAD_PHASE_ORDER.filter((phase) => readyPhases.has(phase));
    status.readyCount = status.loadedCount + status.skippedCount;
  };
  const emitProgress = () => onProgress?.(getStatusSnapshot());

  const mark = (ok, phase = "deferred", entry = null) => {
    if (stopped) {
      return;
    }
    status.activeCount = Math.max(0, status.activeCount - 1);
    if (ok) {
      status.loadedCount += 1;
      if (entry?.assetId) {
        status.loadedAssetIds.push(entry.assetId);
      }
    } else {
      status.failedCount += 1;
      if (entry?.assetId) {
        status.failedAssetIds.push(entry.assetId);
      }
    }
    status.readyCount = status.loadedCount + status.skippedCount;
    status.finished = status.readyCount + status.failedCount >= status.totalCount;
    updateWaitingCount();
    emitProgress();
    if (phase === "critical" || phaseQueues.critical.length) {
      pumpQueue();
    } else {
      scheduleBackgroundPump();
    }
  };

  const takeNextEntry = () => {
    for (const phase of PRELOAD_PHASE_ORDER) {
      if (readyPhases.has(phase) && phaseQueues[phase].length) {
        return phaseQueues[phase].shift();
      }
    }
    return null;
  };

  function scheduleBackgroundPump() {
    if (stopped || backgroundPumpScheduled || status.finished) {
      return;
    }
    backgroundPumpScheduled = true;
    scheduleIdle(
      () => {
        backgroundPumpScheduled = false;
        pumpQueue();
      },
      resolvedOptions.requestIdleCallback,
      {
        ...resolvedOptions,
        deferredDelayMs: resolvedOptions.backgroundBatchDelayMs,
      }
    );
  }

  function schedulePhase(phase) {
    if (!BACKGROUND_PRELOAD_PHASES.includes(phase) || scheduledPhases.has(phase) || !phaseQueues[phase].length) {
      return;
    }
    scheduledPhases.add(phase);
    scheduleIdle(
      () => {
        if (stopped) {
          return;
        }
        readyPhases.add(phase);
        updateWaitingCount();
        emitProgress();
        pumpQueue();
      },
      resolvedOptions.requestIdleCallback,
      {
        ...resolvedOptions,
        deferredDelayMs: resolvedOptions.phaseDelayMs[phase],
      }
    );
  }

  function pumpQueue() {
    if (stopped || status.finished) {
      return;
    }
    updateWaitingCount();
    let backgroundStarted = 0;
    while (status.activeCount < maxConcurrent) {
      const entry = takeNextEntry();
      if (!entry) {
        break;
      }
      if (entry.phase !== "critical" && backgroundStarted >= resolvedOptions.backgroundBatchSize) {
        phaseQueues[entry.phase].unshift(entry);
        scheduleBackgroundPump();
        break;
      }
      status.activeCount += 1;
      if (entry.phase !== "critical") {
        backgroundStarted += 1;
      }
      updateWaitingCount();
      preloadEntry(entry, safeOptions).then((ok) => mark(ok, entry.phase, entry)).catch(() => mark(false, entry.phase, entry));
    }
  }

  pumpQueue();
  BACKGROUND_PRELOAD_PHASES.forEach(schedulePhase);

  return {
    stop() {
      stopped = true;
      PRELOAD_PHASE_ORDER.forEach((phase) => {
        phaseQueues[phase].length = 0;
      });
      status.activeCount = 0;
      status.waitingCount = 0;
      status.pendingCount = 0;
      status.finished = true;
    },
    getStatus() {
      return getStatusSnapshot();
    },
  };
}
