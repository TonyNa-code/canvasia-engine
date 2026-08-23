import {
  buildRuntimePreloadMetaText,
  buildRuntimePreloadStatusText,
  startRuntimePreload,
} from "./runtime_preload.js";
import { buildRuntimeScenePrefetchManifest } from "./runtime_scene_prefetch.js";

function cleanText(value) {
  return String(value ?? "").trim();
}

function toArray(value) {
  return Array.isArray(value) ? value : [];
}

function rememberReadyAssets(status, target) {
  if (!status || !(target instanceof Set)) {
    return;
  }
  [...toArray(status.loadedAssetIds), ...toArray(status.skippedAssetIds)].forEach((assetId) => {
    const normalizedAssetId = cleanText(assetId);
    if (normalizedAssetId) {
      target.add(normalizedAssetId);
    }
  });
}

export function buildRuntimeScenePrefetchRequestKey(snapshot, choiceContinueTarget = "__continue__") {
  if (!snapshot || snapshot.completed) {
    return "";
  }
  const current = [snapshot.sceneId, snapshot.blockId, snapshot.blockIndex].map(cleanText).join(":");
  const targetIds = [
    snapshot.transitionTargetSceneId,
    ...toArray(snapshot.choiceOptions).map((option) => option?.gotoSceneId ?? option?.targetSceneId),
  ]
    .map(cleanText)
    .filter((targetId) => targetId && targetId !== choiceContinueTarget)
    .sort();
  return `${current}|${Array.from(new Set(targetIds)).join(",")}`;
}

export function createRuntimeAssetPipeline(options = {}) {
  const preloadManifest = options.preloadManifest ?? { formatVersion: 1, entries: [] };
  const runtimeSettings = options.runtimeSettings ?? {};
  const context = options.context ?? {};
  const choiceContinueTarget = cleanText(options.choiceContinueTarget) || "__continue__";
  const onStatusChange = typeof options.onStatusChange === "function" ? options.onStatusChange : null;
  const createPreload = options.startPreload ?? startRuntimePreload;
  const createPrefetchManifest = options.buildPrefetchManifest ?? buildRuntimeScenePrefetchManifest;
  const now = typeof options.now === "function" ? options.now : Date.now;
  const retryDelayMs = Math.max(250, Number(options.prefetchRetryDelayMs) || 2000);
  const preloadOptions = options.preloadOptions ?? {};
  const prefetchOptions = options.prefetchOptions ?? {};

  let preloadController = null;
  let prefetchController = null;
  let preloadStatus = null;
  let prefetchStatus = null;
  let prefetchRequestKey = "";
  let prefetchFinishedAtMs = 0;
  const preloadedAssetIds = new Set();
  const prefetchedAssetIds = new Set();

  const getCachedAssetIds = () => new Set([...preloadedAssetIds, ...prefetchedAssetIds]);

  function emit(kind, status) {
    onStatusChange?.(kind, status, getStatus());
  }

  function start() {
    preloadController?.stop?.();
    preloadController = null;
    preloadedAssetIds.clear();
    preloadStatus = null;
    const externalProgress = preloadOptions.onProgress;
    preloadController = createPreload(preloadManifest, {
      ...preloadOptions,
      runtimeSettings,
      onProgress(status) {
        preloadStatus = status;
        rememberReadyAssets(status, preloadedAssetIds);
        externalProgress?.(status);
        emit("preload", status);
      },
    });
    preloadStatus = preloadController?.getStatus?.() ?? null;
    rememberReadyAssets(preloadStatus, preloadedAssetIds);
    emit("preload", preloadStatus);
    return preloadStatus;
  }

  function canRetryCurrentPrefetch(requestKey) {
    if (!requestKey || requestKey !== prefetchRequestKey) {
      return true;
    }
    if (!prefetchStatus?.finished || !prefetchStatus?.failedCount) {
      return false;
    }
    const currentTime = Number(now());
    return Number.isFinite(currentTime) && currentTime - prefetchFinishedAtMs >= retryDelayMs;
  }

  function prefetch(snapshot) {
    const requestKey = buildRuntimeScenePrefetchRequestKey(snapshot, choiceContinueTarget);
    if (!requestKey || !canRetryCurrentPrefetch(requestKey)) {
      return prefetchStatus;
    }

    const cachedAssetIds = getCachedAssetIds();
    const manifest = createPrefetchManifest(
      snapshot,
      {
        ...context,
        excludeAssetIds: cachedAssetIds,
      },
      {
        choiceContinueTarget,
        blockLookahead: 8,
        targetBlockLookahead: 10,
        maxEntries: 24,
        ...(options.prefetchManifestOptions ?? {}),
      }
    );

    prefetchController?.stop?.();
    prefetchController = null;
    prefetchStatus = null;
    prefetchRequestKey = requestKey;
    prefetchFinishedAtMs = 0;

    if (!toArray(manifest?.entries).length) {
      emit("prefetch", null);
      return null;
    }

    const externalProgress = prefetchOptions.onProgress;
    prefetchController = createPreload(manifest, {
      maxConcurrent: 1,
      backgroundBatchSize: 1,
      backgroundBatchDelayMs: 240,
      phaseDelayMs: {
        early: 120,
        deferred: 900,
        library: 1800,
      },
      ...prefetchOptions,
      runtimeSettings,
      skipAssetIds: cachedAssetIds,
      onProgress(status) {
        prefetchStatus = status;
        rememberReadyAssets(status, prefetchedAssetIds);
        if (status?.finished) {
          const finishedAt = Number(now());
          prefetchFinishedAtMs = Number.isFinite(finishedAt) ? finishedAt : Date.now();
        }
        externalProgress?.(status);
        emit("prefetch", status);
      },
    });
    prefetchStatus = prefetchController?.getStatus?.() ?? null;
    rememberReadyAssets(prefetchStatus, prefetchedAssetIds);
    emit("prefetch", prefetchStatus);
    return prefetchStatus;
  }

  function resetPrefetch({ clearCache = false } = {}) {
    prefetchController?.stop?.();
    prefetchController = null;
    prefetchStatus = null;
    prefetchRequestKey = "";
    prefetchFinishedAtMs = 0;
    if (clearCache) {
      prefetchedAssetIds.clear();
    }
    emit("prefetch", null);
  }

  function stop() {
    preloadController?.stop?.();
    prefetchController?.stop?.();
    preloadController = null;
    prefetchController = null;
  }

  function getStatus() {
    const livePreloadStatus = preloadController?.getStatus?.() ?? preloadStatus;
    const livePrefetchStatus = prefetchController?.getStatus?.() ?? prefetchStatus;
    rememberReadyAssets(livePreloadStatus, preloadedAssetIds);
    rememberReadyAssets(livePrefetchStatus, prefetchedAssetIds);
    return {
      preloadStatus: livePreloadStatus,
      prefetchStatus: livePrefetchStatus,
      prefetchRequestKey,
      preloadedAssetIds: Array.from(preloadedAssetIds),
      prefetchedAssetIds: Array.from(prefetchedAssetIds),
      cachedAssetIds: Array.from(getCachedAssetIds()),
    };
  }

  return Object.freeze({
    start,
    prefetch,
    resetPrefetch,
    stop,
    getStatus,
    getCachedAssetIds,
    getStatusText() {
      const status = getStatus();
      return buildRuntimePreloadStatusText({
        manifest: preloadManifest,
        preloadStatus: status.preloadStatus,
        prefetchStatus: status.prefetchStatus,
      });
    },
    getMetaText() {
      return buildRuntimePreloadMetaText(preloadManifest);
    },
  });
}
