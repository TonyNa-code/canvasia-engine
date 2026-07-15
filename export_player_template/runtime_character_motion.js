// Pure character-stage motion helpers for the exported web runtime.
// Keep normalization and CSS variable shaping here so player.js stays focused on playback.

export const CHARACTER_POSITION_PERCENT = Object.freeze({
  left: 24,
  center: 50,
  right: 76,
});

export const CHARACTER_MOTION_EASING_LABELS = Object.freeze({
  linear: "匀速",
  ease_in: "缓慢起步",
  ease_out: "自然收住",
  ease_in_out: "两端柔和",
  spring: "轻微弹性",
});

export const CHARACTER_MOTION_DURATION_DEFAULT_MS = 600;
export const CHARACTER_MOTION_DURATION_MIN_MS = 0;
export const CHARACTER_MOTION_DURATION_MAX_MS = 10000;

export const DEFAULT_CHARACTER_STAGE = Object.freeze({
  offsetX: 0,
  offsetY: 0,
  scale: 100,
  opacity: 100,
  layer: 0,
  flipX: false,
});

function clamp(value, minimum, maximum) {
  return Math.min(Math.max(value, minimum), maximum);
}

function safeNumber(value, fallback) {
  const number = Number.parseFloat(value ?? "");
  return Number.isFinite(number) ? number : fallback;
}

function safeBoolean(value, fallback = false) {
  if (typeof value === "boolean") return value;
  const normalized = String(value ?? "").trim().toLowerCase();
  if (["true", "1", "yes", "on"].includes(normalized)) return true;
  if (["false", "0", "no", "off"].includes(normalized)) return false;
  return fallback;
}

export function getSafeCharacterPosition(value, fallback = "center") {
  const safeFallback = Object.hasOwn(CHARACTER_POSITION_PERCENT, fallback) ? fallback : "center";
  const position = String(value ?? "").trim();
  return Object.hasOwn(CHARACTER_POSITION_PERCENT, position) ? position : safeFallback;
}

export function getCharacterPositionPercent(value) {
  return CHARACTER_POSITION_PERCENT[getSafeCharacterPosition(value)];
}

export function getPositionOrder(value) {
  return getCharacterPositionPercent(value);
}

export function getSafeCharacterStage(source = {}) {
  const raw = source && typeof source === "object" ? source : {};
  return {
    offsetX: Math.round(clamp(safeNumber(raw.offsetX, DEFAULT_CHARACTER_STAGE.offsetX), -60, 60)),
    offsetY: Math.round(clamp(safeNumber(raw.offsetY, DEFAULT_CHARACTER_STAGE.offsetY), -45, 45)),
    scale: Math.round(clamp(safeNumber(raw.scale, DEFAULT_CHARACTER_STAGE.scale), 45, 220)),
    opacity: Math.round(clamp(safeNumber(raw.opacity, DEFAULT_CHARACTER_STAGE.opacity), 0, 100)),
    layer: Math.round(clamp(safeNumber(raw.layer, DEFAULT_CHARACTER_STAGE.layer), -10, 10)),
    flipX: safeBoolean(raw.flipX, DEFAULT_CHARACTER_STAGE.flipX),
  };
}

export function getCharacterStageFromBlock(block = {}) {
  return getSafeCharacterStage(block.stage ?? block.characterStage ?? {});
}

export function getSafeCharacterMotionEasing(value) {
  const easing = String(value ?? "").trim();
  return Object.hasOwn(CHARACTER_MOTION_EASING_LABELS, easing) ? easing : "ease_out";
}

export function getSafeCharacterMotionDurationMs(value, fallback = CHARACTER_MOTION_DURATION_DEFAULT_MS) {
  const safeFallback = clamp(
    safeNumber(fallback, CHARACTER_MOTION_DURATION_DEFAULT_MS),
    CHARACTER_MOTION_DURATION_MIN_MS,
    CHARACTER_MOTION_DURATION_MAX_MS
  );
  return Math.round(
    clamp(
      safeNumber(value, safeFallback),
      CHARACTER_MOTION_DURATION_MIN_MS,
      CHARACTER_MOTION_DURATION_MAX_MS
    )
  );
}

export function getCharacterMotionCssTimingFunction(value) {
  return {
    linear: "linear",
    ease_in: "cubic-bezier(0.42, 0, 1, 1)",
    ease_out: "cubic-bezier(0.16, 1, 0.3, 1)",
    ease_in_out: "cubic-bezier(0.65, 0, 0.35, 1)",
    spring: "cubic-bezier(0.34, 1.56, 0.64, 1)",
  }[getSafeCharacterMotionEasing(value)];
}

export function buildCharacterMotionEvent(previousState = {}, targetState = {}, block = {}) {
  const previous = previousState && typeof previousState === "object" ? previousState : {};
  const target = targetState && typeof targetState === "object" ? targetState : {};
  return {
    mode: "move",
    characterId: String(target.characterId ?? block.characterId ?? previous.characterId ?? "").trim(),
    previousState: {
      characterId: String(previous.characterId ?? block.characterId ?? "").trim(),
      expressionId: previous.expressionId ?? null,
      expressionName: previous.expressionName ?? "",
      position: getSafeCharacterPosition(previous.position),
      stage: getSafeCharacterStage(previous.stage),
    },
    durationMs: getSafeCharacterMotionDurationMs(block.durationMs),
    easing: getSafeCharacterMotionEasing(block.easing),
  };
}

export function getCharacterStageStyle(stageSource = {}, positionSource = "center") {
  const stage = getSafeCharacterStage(stageSource);
  return [
    `--sprite-position-x:${getCharacterPositionPercent(positionSource)}%;`,
    `--sprite-offset-x:${stage.offsetX}%;`,
    `--sprite-offset-y:${stage.offsetY}%;`,
    `--sprite-scale:${(stage.scale / 100).toFixed(3)};`,
    `--sprite-opacity:${(stage.opacity / 100).toFixed(2)};`,
    `--sprite-layer:${stage.layer};`,
    `--sprite-flip-x:${stage.flipX ? -1 : 1};`,
    `z-index:${20 + stage.layer};`,
  ].join("");
}

export function getCharacterMotionStyle(event = null) {
  if (!event || event.mode !== "move") return "";
  const previous = event.previousState ?? {};
  const stage = getSafeCharacterStage(previous.stage);
  return [
    `--sprite-from-position-x:${getCharacterPositionPercent(previous.position)}%;`,
    `--sprite-from-offset-x:${stage.offsetX}%;`,
    `--sprite-from-offset-y:${stage.offsetY}%;`,
    `--sprite-from-scale:${(stage.scale / 100).toFixed(3)};`,
    `--sprite-from-opacity:${(stage.opacity / 100).toFixed(2)};`,
    `--sprite-motion-ms:${getSafeCharacterMotionDurationMs(event.durationMs)}ms;`,
    `--sprite-motion-easing:${getCharacterMotionCssTimingFunction(event.easing)};`,
  ].join("");
}
