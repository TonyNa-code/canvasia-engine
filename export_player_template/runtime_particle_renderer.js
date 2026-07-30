import { buildParticleRenderPlan } from "./runtime_particle_quality.js";


function renderRuntimeParticleLayer(particleEffect, stageContext = null, options = {}) {
  if (!particleEffect) {
    return "";
  }

  const normalizeConfig = options.normalizeParticleEffectConfig;
  const config = normalizeConfig(particleEffect);
  const combos = options.buildParticleComboVariants(config);
  const layerConfigs = combos.flatMap((comboConfig) =>
    options.buildParticleLayerVariants(comboConfig).map((layerConfig) => ({
      ...layerConfig,
      __comboIndex: comboConfig.__comboIndex ?? 0,
    }))
  );
  const qualityStatus = options.qualityStatus ?? {};
  const renderPlan = buildParticleRenderPlan(layerConfigs, {
    performanceProfile: options.performanceProfile,
    qualityLevelIndex: qualityStatus.qualityLevelIndex,
    adaptiveScale: qualityStatus.adaptiveScale,
    deviceScale: qualityStatus.deviceScale,
    getPresetDensityMultiplier: options.getPresetDensityMultiplier,
  });

  return `
    <div
      class="particle-layer"
      data-particle-preset="${config.preset}"
      data-particle-intensity="${config.intensity}"
      data-particle-speed="${config.speed}"
      data-particle-wind="${config.wind}"
      data-particle-area="${config.area}"
      data-particle-combo="${config.comboPreset}"
      data-particle-emission="${config.emissionMode}"
      data-particle-emitter-shape="${config.emitterShape}"
      data-particle-follow="${config.follow}"
      data-particle-blend="${config.blend}"
      data-particle-layers="${config.layerCount}"
      data-has-custom-image="${config.assetId ? "true" : "false"}"
      data-particle-performance-profile="${renderPlan.performanceProfile}"
      data-particle-quality="${renderPlan.qualityLevel}"
      data-particle-requested="${renderPlan.requestedTotal}"
      data-particle-rendered="${renderPlan.renderedTotal}"
      data-particle-limited="${renderPlan.wasLimited ? "true" : "false"}"
      aria-hidden="true"
    >
      ${renderPlan.entries
        .map(({ config: layerConfig, count }) =>
          Array.from({ length: count }, (_, index) =>
            renderRuntimeParticleItem(
              layerConfig,
              layerConfig.__comboIndex * 10000 + layerConfig.__layerIndex * 1000 + index,
              stageContext,
              options
            )
          ).join("")
        )
        .join("")}
    </div>
  `;
}


function renderRuntimeParticleItem(particleEffect, index, stageContext, options) {
  const config = options.normalizeParticleEffectConfig(particleEffect);
  const motion = options.getParticleMotionProfile(config.preset);
  const areaLayout = options.getParticleAreaLayout(config.area, 100);
  const anchor = options.getParticleEmitterAnchor(config, stageContext);
  const emitterShape = options.getSafeParticleEmitterShape(config.emitterShape);
  const curves = options.getParticleCurveProfile(config);
  const colorCurve = options.getParticleColorCurveProfile(config);
  const speedMultiplier = options.getParticleSpeedMultiplier(config.speed);
  const duration =
    (config.lifeMin + (config.lifeMax - config.lifeMin) * options.getParticleRandom(index, 2)) * speedMultiplier;
  const baseSize = config.sizeMin + (config.sizeMax - config.sizeMin) * options.getParticleRandom(index, 3);
  const depthShift =
    (options.getParticleRandom(index, 4) - 0.5) * 2 * (config.spreadZ / 100) + anchor.z / 100;
  const profileAspect = motion.aspect;
  const width =
    profileAspect === "rain"
      ? Math.max(1.5, baseSize * 0.28)
      : profileAspect === "petal"
        ? baseSize * 1.08
        : profileAspect === "confetti"
          ? baseSize * 0.76
          : baseSize;
  const height =
    profileAspect === "rain"
      ? Math.max(18, baseSize * 8.6)
      : profileAspect === "petal"
        ? Math.max(6, baseSize * 0.82)
        : profileAspect === "confetti"
          ? Math.max(6, baseSize * 1.34)
          : width;
  const seedX = options.getParticleRandom(index, 5);
  const seedY = options.getParticleRandom(index, 6);
  const seedAngle = options.getParticleRandom(index, 13) * Math.PI * 2;
  const seedRadius = Math.sqrt(options.getParticleRandom(index, 14));
  let left = anchor.x;
  let startY = anchor.y;

  if (emitterShape === "point") {
    left += (seedX - 0.5) * Math.max(4, config.spreadX * 0.12);
    startY += (seedY - 0.5) * Math.max(4, config.spreadY * 0.12);
  } else if (emitterShape === "line") {
    left += (seedX - 0.5) * config.spreadX;
    startY += (seedY - 0.5) * Math.max(4, config.spreadY * 0.12);
  } else if (emitterShape === "box") {
    left += (seedX - 0.5) * config.spreadX;
    startY += (seedY - 0.5) * config.spreadY;
  } else if (emitterShape === "circle") {
    left += Math.cos(seedAngle) * (config.spreadX * 0.5) * seedRadius;
    startY += Math.sin(seedAngle) * (config.spreadY * 0.5) * seedRadius;
  }

  left = options.clamp(left, areaLayout.start, areaLayout.start + areaLayout.width);
  startY = options.clamp(startY, -24, 124);

  const travelY = motion.endBase - motion.startBase;
  const fieldX = options.clamp(config.fieldX, 0, 100);
  const fieldY = options.clamp(config.fieldY, -20, 120);
  const fieldDeltaX = fieldX - left;
  const fieldDeltaY = fieldY - startY;
  const endY =
    startY +
    travelY +
    config.gravityY * 0.18 +
    config.attractionY * 0.34 +
    fieldDeltaY * curves.force.y * 0.22 +
    (options.getParticleRandom(index, 15) - 0.5) * config.spreadY * 0.35;
  const windBias = options.getParticleWindBias(config.wind, config.preset);
  const driftX =
    windBias +
    config.gravityX * 0.88 +
    config.attractionX * 0.58 +
    fieldDeltaX * curves.force.x * 0.24 +
    (options.getParticleRandom(index, 7) - 0.5) * config.turbulence * 1.9 +
    (options.getParticleRandom(index, 16) - 0.5) * config.vortex * (0.42 + curves.force.orbit) +
    fieldDeltaY * curves.force.orbit * 0.18 +
    depthShift * config.spreadZ * 0.35;
  const opacityStart =
    config.opacityMin + (config.opacityMax - config.opacityMin) * options.getParticleRandom(index, 8);
  const opacityMid = options.clamp(opacityStart * curves.opacity.mid, 0, 1);
  const opacityEnd = options.clamp(
    opacityStart * curves.opacity.end * (config.preset === "bubbles" ? 1.16 : config.preset === "embers" ? 0.92 : 1),
    0,
    1
  );
  const rotationStart =
    config.rotationMin + (config.rotationMax - config.rotationMin) * options.getParticleRandom(index, 9);
  const rotationEnd =
    rotationStart +
    config.spin * (0.45 + options.getParticleRandom(index, 10) * 0.75) +
    config.vortex * (0.4 + options.getParticleRandom(index, 17) * 0.35);
  const midY = startY + (endY - startY) * (0.5 + options.getParticleRandom(index, 19) * 0.12);
  const rotationMid =
    rotationStart + (rotationEnd - rotationStart) * (0.48 + options.getParticleRandom(index, 20) * 0.14);
  const blur = Math.max(
    0,
    Math.abs(depthShift) * (config.spreadZ / 100) * 4.2 +
      (config.preset === "dust" ? 1.1 : 0) +
      (config.preset === "bubbles" ? 0.8 : 0)
  );
  const scaleBase = 0.68 + depthShift * 0.28 + config.gravityZ * 0.002 + anchor.z * 0.002;
  const scaleStart = options.clamp(scaleBase * curves.size.start, 0.22, 2.8);
  const scaleMid = options.clamp(scaleBase * curves.size.mid, 0.18, 3.2);
  const scaleEnd = options.clamp(
    scaleBase * curves.size.end + config.gravityZ * 0.004 + (motion.endBase < motion.startBase ? 0.16 : 0.05),
    0.16,
    3.4
  );
  const particleColor = options.mixParticleColors(
    config.color,
    config.colorAccent,
    options.getParticleRandom(index, 11)
  );
  const particleAccent = options.mixParticleColors(
    config.colorAccent,
    config.colorEnd,
    options.getParticleRandom(index, 12) * 0.32
  );
  const particleEnd = options.mixParticleColors(
    config.colorEnd,
    config.colorAccent,
    options.getParticleRandom(index, 21) * 0.24
  );
  const filterStart = `blur(calc(var(--particle-blur, 0px) + var(--particle-blur-extra, 0px))) hue-rotate(${colorCurve.hue.start}deg) saturate(${colorCurve.saturation.start.toFixed(
    3
  )}) brightness(${colorCurve.brightness.start.toFixed(3)})`;
  const filterMid = `blur(calc(var(--particle-blur, 0px) + var(--particle-blur-extra, 0px))) hue-rotate(${colorCurve.hue.mid}deg) saturate(${colorCurve.saturation.mid.toFixed(
    3
  )}) brightness(${colorCurve.brightness.mid.toFixed(3)})`;
  const filterEnd = `blur(calc(var(--particle-blur, 0px) + var(--particle-blur-extra, 0px))) hue-rotate(${colorCurve.hue.end}deg) saturate(${colorCurve.saturation.end.toFixed(
    3
  )}) brightness(${colorCurve.brightness.end.toFixed(3)})`;
  const imageUrl = options.resolveParticleImageUrl(config.assetId);
  const imageStyle = imageUrl
    ? `--particle-image:url("${options.escapeHtml(encodeURI(imageUrl))}");`
    : "";
  const emissionDelay =
    config.emissionMode === "burst"
      ? -(options.getParticleRandom(index, 18) * Math.min(0.9, Math.max(0.18, duration * 0.18)))
      : -((index * 0.35) % Math.max(duration * 0.72, 1.2));

  return `
    <span
      class="particle-item ${imageStyle ? "has-custom-image" : ""}"
      style="
        --particle-left:${left.toFixed(2)}%;
        --particle-start-y:${startY.toFixed(2)}%;
        --particle-mid-y:${midY.toFixed(2)}%;
        --particle-end-y:${endY.toFixed(2)}%;
        --particle-duration:${duration.toFixed(2)}s;
        --particle-delay:${emissionDelay.toFixed(2)}s;
        --particle-width:${width.toFixed(2)}px;
        --particle-height:${height.toFixed(2)}px;
        --particle-drift-x:${driftX.toFixed(2)}px;
        --particle-opacity-start:${opacityStart.toFixed(3)};
        --particle-opacity-mid:${opacityMid.toFixed(3)};
        --particle-opacity-end:${opacityEnd.toFixed(3)};
        --particle-scale-start:${scaleStart.toFixed(3)};
        --particle-scale-mid:${scaleMid.toFixed(3)};
        --particle-scale-end:${scaleEnd.toFixed(3)};
        --particle-rotate-start:${rotationStart.toFixed(2)}deg;
        --particle-rotate-mid:${rotationMid.toFixed(2)}deg;
        --particle-rotate-end:${rotationEnd.toFixed(2)}deg;
        --particle-blur:${blur.toFixed(2)}px;
        --particle-color:${particleColor};
        --particle-color-accent:${particleAccent};
        --particle-color-end:${particleEnd};
        --particle-filter-start:${filterStart};
        --particle-filter-mid:${filterMid};
        --particle-filter-end:${filterEnd};
        --particle-blend:${options.getParticleBlendCssValue(config.blend)};
        ${imageStyle}
      "
    ></span>
  `;
}


export { renderRuntimeParticleLayer };
