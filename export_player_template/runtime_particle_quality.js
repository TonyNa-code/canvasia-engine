const PROFILE_DEFINITIONS = Object.freeze({
  mobile_low: Object.freeze({
    key: "mobile_low",
    label: "低配 / 移动端",
    densityScale: 0.52,
    maxPerLayer: 42,
    maxTotal: 84,
    targetFrameMs: 30,
  }),
  web: Object.freeze({
    key: "web",
    label: "网页轻量",
    densityScale: 0.78,
    maxPerLayer: 72,
    maxTotal: 144,
    targetFrameMs: 24,
  }),
  standard: Object.freeze({
    key: "standard",
    label: "标准 PC / 网页",
    densityScale: 1,
    maxPerLayer: 180,
    maxTotal: 260,
    targetFrameMs: 21,
  }),
  high_quality_pc: Object.freeze({
    key: "high_quality_pc",
    label: "高画质 PC",
    densityScale: 1.18,
    maxPerLayer: 220,
    maxTotal: 420,
    targetFrameMs: 19,
  }),
});

const QUALITY_LEVELS = Object.freeze([
  Object.freeze({ key: "full", label: "完整", scale: 1 }),
  Object.freeze({ key: "balanced", label: "平衡", scale: 0.72 }),
  Object.freeze({ key: "recovery", label: "保帧", scale: 0.48 }),
]);

function clamp(value, minimum, maximum) {
  const numeric = Number(value);
  return Math.min(maximum, Math.max(minimum, Number.isFinite(numeric) ? numeric : minimum));
}

function getSafePerformanceProfile(value) {
  const key = String(value ?? "standard").trim().toLowerCase();
  return Object.hasOwn(PROFILE_DEFINITIONS, key) ? key : "standard";
}

function getParticlePerformanceProfile(value) {
  return PROFILE_DEFINITIONS[getSafePerformanceProfile(value)];
}

function getSafeQualityLevelIndex(value) {
  const numeric = Math.round(Number(value));
  return Number.isFinite(numeric) ? clamp(numeric, 0, QUALITY_LEVELS.length - 1) : 0;
}

function getParticleQualityLevel(value) {
  return QUALITY_LEVELS[getSafeQualityLevelIndex(value)];
}

function getParticleDeviceScale(capabilities = {}, profile = "standard") {
  const reducedMotionScale = capabilities.reducedMotion ? 0.72 : 1;
  if (getSafePerformanceProfile(profile) === "high_quality_pc") {
    return reducedMotionScale;
  }

  const hardwareConcurrency = Number(capabilities.hardwareConcurrency);
  const deviceMemory = Number(capabilities.deviceMemory);
  let scale = reducedMotionScale;

  if (Number.isFinite(hardwareConcurrency) && hardwareConcurrency > 0) {
    scale = Math.min(scale, hardwareConcurrency <= 2 ? 0.56 : hardwareConcurrency <= 4 ? 0.76 : 1);
  }
  if (Number.isFinite(deviceMemory) && deviceMemory > 0) {
    scale = Math.min(scale, deviceMemory <= 2 ? 0.58 : deviceMemory <= 4 ? 0.8 : 1);
  }
  return scale;
}

function getBaseParticleItemCount(config = {}, options = {}) {
  const intensityMultiplier = {
    light: 0.72,
    medium: 1,
    heavy: 1.28,
  }[config.intensity] ?? 1;
  const areaMultiplier = config.area === "full" ? 1 : 0.64;
  const presetMultiplier = Number(options.getPresetDensityMultiplier?.(config.preset) ?? 1);
  const density = clamp(config.density, 0, 240);
  const previewOffset = options.large ? 8 : options.editorPreview ? -4 : 0;
  const count = Math.round(density * intensityMultiplier * areaMultiplier * presetMultiplier) + previewOffset;
  return density > 0 ? Math.max(6, count) : 0;
}

function allocateParticleCounts(requestedCounts, budget, minimumPerLayer) {
  const safeRequests = requestedCounts.map((value) => Math.max(0, Math.round(Number(value) || 0)));
  const requestedTotal = safeRequests.reduce((sum, value) => sum + value, 0);
  const safeBudget = Math.max(0, Math.round(Number(budget) || 0));
  if (requestedTotal <= safeBudget) {
    return safeRequests;
  }
  if (safeBudget === 0 || requestedTotal === 0) {
    return safeRequests.map(() => 0);
  }

  const activeIndices = safeRequests
    .map((value, index) => (value > 0 ? index : -1))
    .filter((index) => index >= 0);
  const floorPerLayer = activeIndices.length
    ? Math.min(Math.max(0, Math.round(minimumPerLayer)), Math.floor(safeBudget / activeIndices.length))
    : 0;
  const counts = safeRequests.map((value) => (value > 0 ? Math.min(value, floorPerLayer) : 0));
  let remaining = safeBudget - counts.reduce((sum, value) => sum + value, 0);
  const unmetTotal = safeRequests.reduce((sum, value, index) => sum + Math.max(0, value - counts[index]), 0);
  if (remaining <= 0 || unmetTotal <= 0) {
    return counts;
  }

  const fractions = safeRequests.map((value, index) => {
    const unmet = Math.max(0, value - counts[index]);
    const exact = (unmet / unmetTotal) * remaining;
    const addition = Math.min(unmet, Math.floor(exact));
    counts[index] += addition;
    return { index, fraction: exact - addition };
  });
  remaining = safeBudget - counts.reduce((sum, value) => sum + value, 0);
  fractions
    .sort((left, right) => right.fraction - left.fraction || left.index - right.index)
    .forEach(({ index }) => {
      if (remaining > 0 && counts[index] < safeRequests[index]) {
        counts[index] += 1;
        remaining -= 1;
      }
    });
  return counts;
}

function buildParticleRenderPlan(layerConfigs = [], options = {}) {
  const layers = Array.isArray(layerConfigs) ? layerConfigs : [];
  const profile = getParticlePerformanceProfile(options.performanceProfile);
  const qualityLevel = getParticleQualityLevel(options.qualityLevelIndex);
  const deviceScale = clamp(options.deviceScale ?? 1, 0.35, 1);
  const adaptiveScale = clamp(options.adaptiveScale ?? qualityLevel.scale, 0.35, 1);
  const scale = profile.densityScale * deviceScale * adaptiveScale;
  const requestedCounts = layers.map((config) => getBaseParticleItemCount(config, options));
  const perLayerCounts = requestedCounts.map((count) => Math.min(profile.maxPerLayer, Math.max(0, Math.round(count * scale))));
  const totalBudget = Math.max(4, Math.round(profile.maxTotal * deviceScale * adaptiveScale));
  const counts = allocateParticleCounts(perLayerCounts, totalBudget, profile.key === "mobile_low" ? 2 : 4);
  const requestedTotal = requestedCounts.reduce((sum, value) => sum + value, 0);
  const renderedTotal = counts.reduce((sum, value) => sum + value, 0);

  return {
    performanceProfile: profile.key,
    performanceProfileLabel: profile.label,
    qualityLevel: qualityLevel.key,
    qualityLevelLabel: qualityLevel.label,
    requestedTotal,
    renderedTotal,
    totalBudget,
    wasLimited: renderedTotal < requestedTotal,
    densityScale: Number(scale.toFixed(3)),
    entries: layers.map((config, index) => ({
      config,
      requestedCount: requestedCounts[index],
      count: counts[index],
    })),
  };
}

function detectBrowserParticleCapabilities(globalObject = globalThis) {
  const navigatorObject = globalObject?.navigator ?? {};
  const matchMedia = typeof globalObject?.matchMedia === "function" ? globalObject.matchMedia.bind(globalObject) : null;
  return {
    hardwareConcurrency: Number(navigatorObject.hardwareConcurrency) || null,
    deviceMemory: Number(navigatorObject.deviceMemory) || null,
    reducedMotion: Boolean(matchMedia?.("(prefers-reduced-motion: reduce)")?.matches),
  };
}

function createAdaptiveParticleQualityController(options = {}) {
  const profile = getParticlePerformanceProfile(options.performanceProfile);
  const capabilities = options.capabilities ?? detectBrowserParticleCapabilities(options.globalObject ?? globalThis);
  const deviceScale = getParticleDeviceScale(capabilities, profile.key);
  let qualityLevelIndex = deviceScale < 0.62 ? 2 : deviceScale < 0.86 ? 1 : 0;
  let averageFrameMs = profile.targetFrameMs;
  let slowFrames = 0;
  let fastFrames = 0;
  let animationFrameId = null;
  let previousTimestamp = null;

  const emit = (reason) => {
    const snapshot = controller.getSnapshot();
    if (typeof options.onChange === "function") {
      options.onChange(snapshot, reason);
    }
    return snapshot;
  };

  const controller = {
    observeFrame(frameMs) {
      const safeFrameMs = clamp(frameMs, 1, 250);
      averageFrameMs = averageFrameMs * 0.92 + safeFrameMs * 0.08;
      const slowThreshold = profile.targetFrameMs * 1.22;
      const fastThreshold = profile.targetFrameMs * 0.82;
      slowFrames = averageFrameMs > slowThreshold ? slowFrames + 1 : Math.max(0, slowFrames - 2);
      fastFrames = averageFrameMs < fastThreshold ? fastFrames + 1 : Math.max(0, fastFrames - 1);

      if (slowFrames >= 48 && qualityLevelIndex < QUALITY_LEVELS.length - 1) {
        qualityLevelIndex += 1;
        slowFrames = 0;
        fastFrames = 0;
        return emit("frame_pressure");
      }
      if (fastFrames >= 240 && qualityLevelIndex > 0) {
        qualityLevelIndex -= 1;
        slowFrames = 0;
        fastFrames = 0;
        return emit("frame_recovered");
      }
      return controller.getSnapshot();
    },
    getSnapshot() {
      const level = getParticleQualityLevel(qualityLevelIndex);
      return {
        performanceProfile: profile.key,
        performanceProfileLabel: profile.label,
        qualityLevelIndex,
        qualityLevel: level.key,
        qualityLevelLabel: level.label,
        adaptiveScale: level.scale,
        deviceScale,
        averageFrameMs: Number(averageFrameMs.toFixed(2)),
      };
    },
    start(globalObject = options.globalObject ?? globalThis) {
      if (animationFrameId !== null || typeof globalObject?.requestAnimationFrame !== "function") {
        return controller.getSnapshot();
      }
      const sample = (timestamp) => {
        if (previousTimestamp !== null) {
          controller.observeFrame(timestamp - previousTimestamp);
        }
        previousTimestamp = timestamp;
        animationFrameId = globalObject.requestAnimationFrame(sample);
      };
      animationFrameId = globalObject.requestAnimationFrame(sample);
      return emit("started");
    },
    stop(globalObject = options.globalObject ?? globalThis) {
      if (animationFrameId !== null && typeof globalObject?.cancelAnimationFrame === "function") {
        globalObject.cancelAnimationFrame(animationFrameId);
      }
      animationFrameId = null;
      previousTimestamp = null;
    },
  };

  return controller;
}

export {
  PROFILE_DEFINITIONS as PARTICLE_PERFORMANCE_PROFILES,
  QUALITY_LEVELS as PARTICLE_QUALITY_LEVELS,
  allocateParticleCounts,
  buildParticleRenderPlan,
  createAdaptiveParticleQualityController,
  detectBrowserParticleCapabilities,
  getBaseParticleItemCount,
  getParticleDeviceScale,
  getParticlePerformanceProfile,
  getParticleQualityLevel,
  getSafePerformanceProfile,
};
