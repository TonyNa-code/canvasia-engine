(function attachParticlePerformance(global) {
  "use strict";

  const PARTICLE_PERFORMANCE_PROFILES = Object.freeze({
    mobile_low: Object.freeze({ key: "mobile_low", label: "低配 / 移动端", densityScale: 0.52, maxPerLayer: 42, maxTotal: 84 }),
    web: Object.freeze({ key: "web", label: "网页轻量", densityScale: 0.78, maxPerLayer: 72, maxTotal: 144 }),
    standard: Object.freeze({ key: "standard", label: "标准 PC / 网页", densityScale: 1, maxPerLayer: 180, maxTotal: 260 }),
    high_quality_pc: Object.freeze({ key: "high_quality_pc", label: "高画质 PC", densityScale: 1.18, maxPerLayer: 220, maxTotal: 420 }),
  });

  function clamp(value, minimum, maximum) {
    const numeric = Number(value);
    return Math.min(maximum, Math.max(minimum, Number.isFinite(numeric) ? numeric : minimum));
  }

  function getSafePerformanceProfile(value) {
    const key = String(value ?? "standard").trim().toLowerCase();
    return Object.hasOwn(PARTICLE_PERFORMANCE_PROFILES, key) ? key : "standard";
  }

  function getParticlePerformanceProfile(value) {
    return PARTICLE_PERFORMANCE_PROFILES[getSafePerformanceProfile(value)];
  }

  function getBaseParticleItemCount(config = {}, options = {}) {
    const intensityMultiplier = { light: 0.72, medium: 1, heavy: 1.28 }[config.intensity] ?? 1;
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
    const adaptiveScale = clamp(options.adaptiveScale ?? 1, 0.35, 1);
    const scale = profile.densityScale * adaptiveScale;
    const requestedCounts = layers.map((config) => getBaseParticleItemCount(config, options));
    const perLayerCounts = requestedCounts.map((count) =>
      Math.min(profile.maxPerLayer, Math.max(0, Math.round(count * scale)))
    );
    const totalBudget = Math.max(4, Math.round(profile.maxTotal * adaptiveScale));
    const counts = allocateParticleCounts(perLayerCounts, totalBudget, profile.key === "mobile_low" ? 2 : 4);
    const requestedTotal = requestedCounts.reduce((sum, value) => sum + value, 0);
    const renderedTotal = counts.reduce((sum, value) => sum + value, 0);
    return {
      performanceProfile: profile.key,
      performanceProfileLabel: profile.label,
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

  function buildParticlePerformanceReport(effect, options = {}) {
    const normalizeEffect = options.normalizeParticleEffectConfig;
    const buildCombos = options.buildParticleComboVariants;
    const buildLayers = options.buildParticleLayerVariants;
    if (typeof normalizeEffect !== "function" || typeof buildCombos !== "function" || typeof buildLayers !== "function") {
      return buildParticleRenderPlan([], options);
    }
    const config = normalizeEffect(effect);
    const layerConfigs = buildCombos(config).flatMap((combo) =>
      buildLayers(combo).map((layer) => ({ ...layer, __comboIndex: combo.__comboIndex ?? 0 }))
    );
    return buildParticleRenderPlan(layerConfigs, options);
  }

  function renderParticlePerformanceCard(report = {}, options = {}) {
    const escapeHtml = typeof options.escapeHtml === "function" ? options.escapeHtml : (value) => String(value ?? "");
    const status = report.wasLimited ? "已自动控量" : "无需降级";
    const tone = report.wasLimited ? "is-limited" : "is-clear";
    return `
      <article class="editor-card particle-performance-card ${tone}">
        <div class="particle-performance-heading">
          <div>
            <span class="eyebrow">实时性能预算</span>
            <h3>${escapeHtml(report.performanceProfileLabel || "标准 PC / 网页")} · ${escapeHtml(status)}</h3>
          </div>
          <strong>${Number(report.renderedTotal || 0)} / ${Number(report.requestedTotal || 0)} 颗</strong>
        </div>
        <p>成品会按项目性能档位限制整组叠层粒子的总量，避免多个图层各自拉满后突然卡顿。低帧率设备还会继续动态降档，剧情和音频不会被中断。</p>
        <div class="particle-performance-meter" aria-label="粒子性能预算">
          <span style="width:${Math.min(100, Math.round((Number(report.renderedTotal || 0) / Math.max(1, Number(report.totalBudget || 1))) * 100))}%"></span>
        </div>
        <div class="detail-meta">本档总上限 ${Number(report.totalBudget || 0)} 颗 · ${Number(report.entries?.length || 0)} 个发射层 · 密度倍率 ${Number(report.densityScale || 1).toFixed(2)}</div>
      </article>
    `;
  }

  global.CanvasiaEditorParticlePerformance = Object.freeze({
    PARTICLE_PERFORMANCE_PROFILES,
    allocateParticleCounts,
    buildParticlePerformanceReport,
    buildParticleRenderPlan,
    getBaseParticleItemCount,
    getParticlePerformanceProfile,
    getSafePerformanceProfile,
    renderParticlePerformanceCard,
  });
})(window);
