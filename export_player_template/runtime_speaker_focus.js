// Shared speaker-focus policy for editor preview and the exported Web Runtime.
// Rendering code consumes the numeric pose so future sprite backends can reuse it.

export const SPEAKER_FOCUS_MODE_LABELS = Object.freeze({
  off: "关闭聚焦",
  soft: "柔和聚焦",
  cinematic: "电影感聚焦",
});

export const DEFAULT_SPEAKER_FOCUS_CONFIG = Object.freeze({
  speakerFocusMode: "soft",
  speakerFocusIntensity: 65,
  speakerFocusTransitionMs: 240,
});

export const SPEAKER_FOCUS_PROFILES = Object.freeze({
  off: Object.freeze({ opacityDrop: 0, brightnessDrop: 0, saturationDrop: 0, activeScaleBoost: 0 }),
  soft: Object.freeze({ opacityDrop: 0.2, brightnessDrop: 0.18, saturationDrop: 0.12, activeScaleBoost: 0.018 }),
  cinematic: Object.freeze({ opacityDrop: 0.42, brightnessDrop: 0.34, saturationDrop: 0.28, activeScaleBoost: 0.04 }),
});

function clamp(value, minimum, maximum) {
  return Math.min(Math.max(value, minimum), maximum);
}

function getSafeNumber(value, fallback) {
  const numericValue = Number.parseFloat(value ?? "");
  return Number.isFinite(numericValue) ? numericValue : fallback;
}

function roundPoseValue(value) {
  return Math.round(value * 1000) / 1000;
}

function getConfigSource(value) {
  if (value?.gameUiConfig && typeof value.gameUiConfig === "object") {
    return value.gameUiConfig;
  }
  return value && typeof value === "object" ? value : {};
}

export function getSafeSpeakerFocusMode(value) {
  const mode = String(value ?? DEFAULT_SPEAKER_FOCUS_CONFIG.speakerFocusMode).trim().toLowerCase();
  return Object.hasOwn(SPEAKER_FOCUS_PROFILES, mode)
    ? mode
    : DEFAULT_SPEAKER_FOCUS_CONFIG.speakerFocusMode;
}

export function getSpeakerFocusConfig(value = {}) {
  const source = getConfigSource(value);
  return {
    speakerFocusMode: getSafeSpeakerFocusMode(source.speakerFocusMode),
    speakerFocusIntensity: Math.round(
      clamp(
        getSafeNumber(source.speakerFocusIntensity, DEFAULT_SPEAKER_FOCUS_CONFIG.speakerFocusIntensity),
        0,
        100
      )
    ),
    speakerFocusTransitionMs: Math.round(
      clamp(
        getSafeNumber(source.speakerFocusTransitionMs, DEFAULT_SPEAKER_FOCUS_CONFIG.speakerFocusTransitionMs),
        0,
        1200
      )
    ),
  };
}

function getVisualComfortMotionScale(value) {
  if (value === "static") return 0;
  if (value === "gentle") return 0.35;
  return 1;
}

function getVisibleCharacterIds(value) {
  return [...new Set((Array.isArray(value) ? value : []).map((item) => String(item ?? "").trim()).filter(Boolean))];
}

export function buildSpeakerFocusPose({
  characterId,
  activeCharacterId,
  visibleCharacterIds = [],
  gameUiConfig = {},
  visualComfortMode = "standard",
  isLeaving = false,
} = {}) {
  const config = getSpeakerFocusConfig(gameUiConfig);
  const safeCharacterId = String(characterId ?? "").trim();
  const safeActiveCharacterId = String(activeCharacterId ?? "").trim();
  const visibleIds = getVisibleCharacterIds(visibleCharacterIds);
  const canFocus =
    config.speakerFocusMode !== "off" &&
    !isLeaving &&
    safeCharacterId &&
    visibleIds.includes(safeCharacterId) &&
    visibleIds.length > 1 &&
    visibleIds.includes(safeActiveCharacterId);
  const role = canFocus ? (safeCharacterId === safeActiveCharacterId ? "active" : "muted") : "neutral";
  const profile = SPEAKER_FOCUS_PROFILES[config.speakerFocusMode];
  const intensity = config.speakerFocusIntensity / 100;
  const motionScale = getVisualComfortMotionScale(visualComfortMode);
  const activeScale = role === "active"
    ? 1 + profile.activeScaleBoost * intensity * motionScale
    : 1;
  const transitionMs = visualComfortMode === "static"
    ? 0
    : Math.round(config.speakerFocusTransitionMs * (visualComfortMode === "gentle" ? 0.7 : 1));

  return Object.freeze({
    role,
    active: role === "active",
    muted: role === "muted",
    opacityMultiplier: roundPoseValue(role === "muted" ? 1 - profile.opacityDrop * intensity : 1),
    brightnessMultiplier: roundPoseValue(role === "muted" ? 1 - profile.brightnessDrop * intensity : 1),
    saturationMultiplier: roundPoseValue(role === "muted" ? 1 - profile.saturationDrop * intensity : 1),
    scaleMultiplier: roundPoseValue(activeScale),
    transitionMs,
    layerBoost: role === "active" ? 100 : 0,
  });
}

export function buildSpeakerFocusPresentation(options = {}) {
  const pose = buildSpeakerFocusPose(options);
  const classNames = [];
  if (pose.active) classNames.push("is-speaker-focus-active");
  if (pose.muted) classNames.push("is-speaker-focus-muted");
  return Object.freeze({
    ...pose,
    classNames: Object.freeze(classNames),
    style: [
      `--speaker-focus-opacity:${pose.opacityMultiplier.toFixed(3)};`,
      `--speaker-focus-brightness:${pose.brightnessMultiplier.toFixed(3)};`,
      `--speaker-focus-saturation:${pose.saturationMultiplier.toFixed(3)};`,
      `--speaker-focus-scale:${pose.scaleMultiplier.toFixed(3)};`,
      `--speaker-focus-transition-ms:${pose.transitionMs}ms;`,
    ].join(""),
  });
}

const runtimeSpeakerFocusApi = Object.freeze({
  SPEAKER_FOCUS_MODE_LABELS,
  DEFAULT_SPEAKER_FOCUS_CONFIG,
  SPEAKER_FOCUS_PROFILES,
  getSafeSpeakerFocusMode,
  getSpeakerFocusConfig,
  buildSpeakerFocusPose,
  buildSpeakerFocusPresentation,
});

globalThis.CanvasiaRuntimeSpeakerFocus = runtimeSpeakerFocusApi;
