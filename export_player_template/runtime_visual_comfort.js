export const VISUAL_COMFORT_LABELS = Object.freeze({
  standard: "原始演出",
  gentle: "柔和模式",
  static: "静态模式",
});

export const VISUAL_COMFORT_PROFILES = Object.freeze({
  standard: Object.freeze({ motionScale: 1, flashScale: 1, transitionScale: 1 }),
  gentle: Object.freeze({ motionScale: 0.35, flashScale: 0.3, transitionScale: 0.55 }),
  static: Object.freeze({ motionScale: 0, flashScale: 0, transitionScale: 0 }),
});

export function getSafeVisualComfortMode(value, fallback = "standard") {
  const safeFallback = Object.hasOwn(VISUAL_COMFORT_PROFILES, fallback) ? fallback : "standard";
  const mode = String(value ?? safeFallback).trim().toLowerCase();
  return Object.hasOwn(VISUAL_COMFORT_PROFILES, mode) ? mode : safeFallback;
}

export function getVisualComfortLabel(value) {
  return VISUAL_COMFORT_LABELS[getSafeVisualComfortMode(value)];
}

export function getVisualComfortProfile(value) {
  return VISUAL_COMFORT_PROFILES[getSafeVisualComfortMode(value)];
}

function getSafeNonNegativeNumber(value, fallback = 0) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? Math.max(0, numeric) : Math.max(0, Number(fallback) || 0);
}

export function scaleVisualMotion(value, mode, fallback = 0) {
  return getSafeNonNegativeNumber(value, fallback) * getVisualComfortProfile(mode).motionScale;
}

export function scaleVisualFlash(value, mode, fallback = 0) {
  return getSafeNonNegativeNumber(value, fallback) * getVisualComfortProfile(mode).flashScale;
}

export function scaleVisualTransitionMs(value, mode, fallback = 0) {
  const scaled = getSafeNonNegativeNumber(value, fallback) * getVisualComfortProfile(mode).transitionScale;
  return Math.max(0, Math.round(scaled));
}

export function getVisualComfortSummary(value) {
  const mode = getSafeVisualComfortMode(value);
  const profile = getVisualComfortProfile(mode);
  return {
    mode,
    label: getVisualComfortLabel(mode),
    motionPercent: Math.round(profile.motionScale * 100),
    flashPercent: Math.round(profile.flashScale * 100),
    transitionPercent: Math.round(profile.transitionScale * 100),
    disablesTransientEffects: mode === "static",
  };
}

const runtimeVisualComfortApi = Object.freeze({
  VISUAL_COMFORT_LABELS,
  VISUAL_COMFORT_PROFILES,
  getSafeVisualComfortMode,
  getVisualComfortLabel,
  getVisualComfortProfile,
  scaleVisualMotion,
  scaleVisualFlash,
  scaleVisualTransitionMs,
  getVisualComfortSummary,
});

globalThis.CanvasiaRuntimeVisualComfort = runtimeVisualComfortApi;
