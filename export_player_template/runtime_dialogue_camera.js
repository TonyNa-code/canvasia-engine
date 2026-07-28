// Shared stage-camera policy for editor preview and the exported Web Runtime.
// Explicit camera blocks keep priority while automatic dialogue framing fills the gaps.

import {
  CAMERA_PAN_STRENGTH_LABELS,
  CAMERA_PAN_TARGET_LABELS,
  CAMERA_ZOOM_ACTION_LABELS,
  CAMERA_ZOOM_FOCUS_LABELS,
  CAMERA_ZOOM_STRENGTH_LABELS,
} from "./runtime_visual_constants.js";

export const DIALOGUE_CAMERA_MODE_LABELS = Object.freeze({
  off: "关闭自动镜头",
  soft: "柔和跟拍",
  cinematic: "电影切镜",
});

export const DEFAULT_DIALOGUE_CAMERA_CONFIG = Object.freeze({
  dialogueCameraMode: "soft",
  dialogueCameraIntensity: 58,
  dialogueCameraTransitionMs: 520,
});

export const DIALOGUE_CAMERA_PROFILES = Object.freeze({
  off: Object.freeze({ panFactor: 0, zoomBoost: 0 }),
  soft: Object.freeze({ panFactor: 0.15, zoomBoost: 0.022 }),
  cinematic: Object.freeze({ panFactor: 0.28, zoomBoost: 0.05 }),
});

const CHARACTER_POSITION_PERCENT = Object.freeze({ left: 24, center: 50, right: 76 });
const MANUAL_CAMERA_TRANSITION_MS = 320;

function clamp(value, minimum, maximum) {
  return Math.min(Math.max(value, minimum), maximum);
}

function getSafeNumber(value, fallback) {
  const numericValue = Number.parseFloat(value ?? "");
  return Number.isFinite(numericValue) ? numericValue : fallback;
}

function roundPoseValue(value) {
  return Math.round(Number(value) * 1000) / 1000;
}

function getConfigSource(value) {
  if (value?.gameUiConfig && typeof value.gameUiConfig === "object") {
    return value.gameUiConfig;
  }
  return value && typeof value === "object" ? value : {};
}

function getVisualComfortMotionScale(value) {
  if (value === "static") return 0;
  if (value === "gentle") return 0.35;
  return 1;
}

function getCharacterPositionPercent(characterState = {}) {
  const base = CHARACTER_POSITION_PERCENT[characterState.position] ?? CHARACTER_POSITION_PERCENT.center;
  const stage = characterState.stage && typeof characterState.stage === "object" ? characterState.stage : {};
  return clamp(base + getSafeNumber(stage.offsetX, 0), 8, 92);
}

export function getSafeDialogueCameraMode(value) {
  const mode = String(value ?? DEFAULT_DIALOGUE_CAMERA_CONFIG.dialogueCameraMode).trim().toLowerCase();
  return Object.hasOwn(DIALOGUE_CAMERA_PROFILES, mode)
    ? mode
    : DEFAULT_DIALOGUE_CAMERA_CONFIG.dialogueCameraMode;
}

export function getDialogueCameraConfig(value = {}) {
  const source = getConfigSource(value);
  return Object.freeze({
    dialogueCameraMode: getSafeDialogueCameraMode(source.dialogueCameraMode),
    dialogueCameraIntensity: Math.round(
      clamp(
        getSafeNumber(source.dialogueCameraIntensity, DEFAULT_DIALOGUE_CAMERA_CONFIG.dialogueCameraIntensity),
        0,
        100
      )
    ),
    dialogueCameraTransitionMs: Math.round(
      clamp(
        getSafeNumber(source.dialogueCameraTransitionMs, DEFAULT_DIALOGUE_CAMERA_CONFIG.dialogueCameraTransitionMs),
        0,
        1600
      )
    ),
  });
}

export function buildDialogueCameraPose({
  activeCharacterId,
  visibleCharacters = [],
  gameUiConfig = {},
  visualComfortMode = "standard",
} = {}) {
  const config = getDialogueCameraConfig(gameUiConfig);
  const safeActiveCharacterId = String(activeCharacterId ?? "").trim();
  const activeCharacter = (Array.isArray(visibleCharacters) ? visibleCharacters : []).find(
    (item) => String(item?.characterId ?? "").trim() === safeActiveCharacterId && !item?.__ghostMode && !item?.__leaving
  );
  const motionScale = getVisualComfortMotionScale(visualComfortMode);
  const active = Boolean(
    config.dialogueCameraMode !== "off" && activeCharacter && motionScale > 0
  );
  const focusPercent = active ? getCharacterPositionPercent(activeCharacter) : 50;
  const profile = DIALOGUE_CAMERA_PROFILES[config.dialogueCameraMode];
  const intensity = config.dialogueCameraIntensity / 100;
  const panPercent = active
    ? clamp((50 - focusPercent) * profile.panFactor * intensity * motionScale, -10, 10)
    : 0;
  const zoomScale = active
    ? 1 + profile.zoomBoost * intensity * motionScale
    : 1;
  const transitionMs = visualComfortMode === "static"
    ? 0
    : Math.round(config.dialogueCameraTransitionMs * (visualComfortMode === "gentle" ? 0.7 : 1));

  return Object.freeze({
    mode: config.dialogueCameraMode,
    active,
    focusPercent: roundPoseValue(focusPercent),
    panPercent: roundPoseValue(panPercent),
    zoomScale: roundPoseValue(zoomScale),
    transitionMs,
  });
}

export function getSafeCameraZoomAction(action) {
  return Object.hasOwn(CAMERA_ZOOM_ACTION_LABELS, action) ? action : "zoom_in";
}

export function getCameraZoomActionLabel(action) {
  return CAMERA_ZOOM_ACTION_LABELS[getSafeCameraZoomAction(action)];
}

export function getSafeCameraZoomStrength(strength) {
  return Object.hasOwn(CAMERA_ZOOM_STRENGTH_LABELS, strength) ? strength : "medium";
}

export function getCameraZoomStrengthLabel(strength) {
  return CAMERA_ZOOM_STRENGTH_LABELS[getSafeCameraZoomStrength(strength)];
}

export function getSafeCameraZoomFocus(focus) {
  return Object.hasOwn(CAMERA_ZOOM_FOCUS_LABELS, focus) ? focus : "center";
}

export function getCameraZoomFocusLabel(focus) {
  return CAMERA_ZOOM_FOCUS_LABELS[getSafeCameraZoomFocus(focus)];
}

export function getCameraZoomScale(action, strength) {
  const safeAction = getSafeCameraZoomAction(action);
  const safeStrength = getSafeCameraZoomStrength(strength);
  if (safeAction === "reset") return 1;
  const zoomInScale = { light: 1.08, medium: 1.16, heavy: 1.26 };
  const zoomOutScale = { light: 0.96, medium: 0.92, heavy: 0.88 };
  return safeAction === "zoom_out" ? zoomOutScale[safeStrength] : zoomInScale[safeStrength];
}

export function getCameraZoomOrigin(focus) {
  return {
    left: "28% 52%",
    center: "50% 52%",
    right: "72% 52%",
  }[getSafeCameraZoomFocus(focus)];
}

export function getSafeCameraPanTarget(target) {
  return Object.hasOwn(CAMERA_PAN_TARGET_LABELS, target) ? target : "center";
}

export function getCameraPanTargetLabel(target) {
  return CAMERA_PAN_TARGET_LABELS[getSafeCameraPanTarget(target)];
}

export function getSafeCameraPanStrength(strength) {
  return Object.hasOwn(CAMERA_PAN_STRENGTH_LABELS, strength) ? strength : "medium";
}

export function getCameraPanStrengthLabel(strength) {
  return CAMERA_PAN_STRENGTH_LABELS[getSafeCameraPanStrength(strength)];
}

export function getCameraPanOffset(target, strength) {
  const safeTarget = getSafeCameraPanTarget(target);
  if (safeTarget === "center") return 0;
  const amount = { light: 4, medium: 8, heavy: 12 }[getSafeCameraPanStrength(strength)];
  return safeTarget === "left" ? amount : -amount;
}

export function buildStageCameraPresentation({
  cameraZoom = null,
  cameraPan = null,
  activeCharacterId = null,
  visibleCharacters = [],
  gameUiConfig = {},
  visualComfortMode = "standard",
} = {}) {
  const dialoguePose = buildDialogueCameraPose({
    activeCharacterId,
    visibleCharacters,
    gameUiConfig,
    visualComfortMode,
  });
  const hasManualZoom = Boolean(cameraZoom);
  const hasManualPan = Boolean(cameraPan);
  const zoomScale = hasManualZoom
    ? getCameraZoomScale(cameraZoom.action, cameraZoom.strength)
    : dialoguePose.zoomScale;
  const panPercent = hasManualPan
    ? getCameraPanOffset(cameraPan.target, cameraPan.strength)
    : dialoguePose.panPercent;
  const transformOrigin = hasManualZoom
    ? getCameraZoomOrigin(cameraZoom.focus)
    : `${dialoguePose.focusPercent}% 52%`;
  const transitionMs = visualComfortMode === "static"
    ? 0
    : dialoguePose.mode === "off"
      ? MANUAL_CAMERA_TRANSITION_MS
      : dialoguePose.transitionMs;
  const autoActive = dialoguePose.active && (!hasManualZoom || !hasManualPan);

  return Object.freeze({
    ...dialoguePose,
    autoActive,
    manualZoom: hasManualZoom,
    manualPan: hasManualPan,
    zoomScale: roundPoseValue(zoomScale),
    panPercent: roundPoseValue(panPercent),
    transformOrigin,
    transitionMs,
    style: [
      `transform:translate3d(${roundPoseValue(panPercent).toFixed(2)}%, 0, 0) scale(${roundPoseValue(zoomScale).toFixed(3)})`,
      `transform-origin:${transformOrigin}`,
      `--dialogue-camera-transition-ms:${transitionMs}ms`,
    ].join(";"),
  });
}

const runtimeDialogueCameraApi = Object.freeze({
  DIALOGUE_CAMERA_MODE_LABELS,
  DEFAULT_DIALOGUE_CAMERA_CONFIG,
  DIALOGUE_CAMERA_PROFILES,
  getSafeDialogueCameraMode,
  getDialogueCameraConfig,
  buildDialogueCameraPose,
  buildStageCameraPresentation,
  getSafeCameraZoomAction,
  getCameraZoomActionLabel,
  getSafeCameraZoomStrength,
  getCameraZoomStrengthLabel,
  getSafeCameraZoomFocus,
  getCameraZoomFocusLabel,
  getCameraZoomScale,
  getCameraZoomOrigin,
  getSafeCameraPanTarget,
  getCameraPanTargetLabel,
  getSafeCameraPanStrength,
  getCameraPanStrengthLabel,
  getCameraPanOffset,
});

globalThis.CanvasiaRuntimeDialogueCamera = runtimeDialogueCameraApi;
