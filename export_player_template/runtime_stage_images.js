export const STAGE_IMAGE_ACTIONS = Object.freeze(["show", "update", "hide"]);
export const STAGE_IMAGE_PLANES = Object.freeze(["back", "front"]);
export const STAGE_IMAGE_POSITIONS = Object.freeze(["left", "center", "right"]);
export const STAGE_IMAGE_EASINGS = Object.freeze(["linear", "ease_in", "ease_out", "ease_in_out", "spring"]);

export const DEFAULT_STAGE_IMAGE_TRANSFORM = Object.freeze({
  offsetX: 0,
  offsetY: 0,
  width: 34,
  opacity: 100,
  rotation: 0,
  layer: 0,
  flipX: false,
});

export const STAGE_IMAGE_DURATION_DEFAULT_MS = 520;

function clamp(value, minimum, maximum) {
  return Math.min(Math.max(value, minimum), maximum);
}

function safeNumber(value, fallback) {
  const parsed = Number.parseFloat(value ?? "");
  return Number.isFinite(parsed) ? parsed : fallback;
}

function safeBoolean(value, fallback = false) {
  if (typeof value === "boolean") return value;
  const normalized = String(value ?? "").trim().toLowerCase();
  if (["true", "1", "yes", "on"].includes(normalized)) return true;
  if (["false", "0", "no", "off"].includes(normalized)) return false;
  return fallback;
}

export function getSafeStageImageAction(value) {
  const action = String(value ?? "").trim();
  return STAGE_IMAGE_ACTIONS.includes(action) ? action : "show";
}

export function getSafeStageImagePlane(value) {
  const plane = String(value ?? "").trim();
  return STAGE_IMAGE_PLANES.includes(plane) ? plane : "front";
}

export function getSafeStageImagePosition(value) {
  const position = String(value ?? "").trim();
  return STAGE_IMAGE_POSITIONS.includes(position) ? position : "center";
}

export function getSafeStageImageEasing(value) {
  const easing = String(value ?? "").trim();
  return STAGE_IMAGE_EASINGS.includes(easing) ? easing : "ease_out";
}

export function getSafeStageImageLayerId(value, fallback = "layer_main") {
  const cleaned = String(value ?? "")
    .replace(/[\u0000-\u001f\u007f]/g, "")
    .trim()
    .replace(/\s+/g, "_")
    .slice(0, 48);
  return cleaned || String(fallback || "layer_main").slice(0, 48);
}

export function getSafeStageImageTransform(source = {}) {
  const raw = source && typeof source === "object" ? source : {};
  return {
    offsetX: Math.round(clamp(safeNumber(raw.offsetX, DEFAULT_STAGE_IMAGE_TRANSFORM.offsetX), -80, 80)),
    offsetY: Math.round(clamp(safeNumber(raw.offsetY, DEFAULT_STAGE_IMAGE_TRANSFORM.offsetY), -70, 70)),
    width: Math.round(clamp(safeNumber(raw.width, DEFAULT_STAGE_IMAGE_TRANSFORM.width), 4, 180)),
    opacity: Math.round(clamp(safeNumber(raw.opacity, DEFAULT_STAGE_IMAGE_TRANSFORM.opacity), 0, 100)),
    rotation: Math.round(clamp(safeNumber(raw.rotation, DEFAULT_STAGE_IMAGE_TRANSFORM.rotation), -180, 180)),
    layer: Math.round(clamp(safeNumber(raw.layer, DEFAULT_STAGE_IMAGE_TRANSFORM.layer), -20, 20)),
    flipX: safeBoolean(raw.flipX, DEFAULT_STAGE_IMAGE_TRANSFORM.flipX),
  };
}

export function getSafeStageImageDurationMs(value, fallback = STAGE_IMAGE_DURATION_DEFAULT_MS) {
  const safeFallback = clamp(safeNumber(fallback, STAGE_IMAGE_DURATION_DEFAULT_MS), 0, 10000);
  return Math.round(clamp(safeNumber(value, safeFallback), 0, 10000));
}

export function normalizeStageImageState(source = {}, fallback = {}) {
  const raw = source && typeof source === "object" ? source : {};
  const previous = fallback && typeof fallback === "object" ? fallback : {};
  const previousTransform = previous.transform ?? previous.stage ?? {};
  const explicitTransform = raw.transform ?? raw.stage;
  const transformSource = explicitTransform && typeof explicitTransform === "object"
    ? { ...previousTransform, ...explicitTransform }
    : previousTransform;
  return {
    layerId: getSafeStageImageLayerId(raw.layerId ?? previous.layerId),
    assetId: String(raw.assetId ?? previous.assetId ?? "").trim(),
    plane: getSafeStageImagePlane(raw.plane ?? previous.plane),
    position: getSafeStageImagePosition(raw.position ?? previous.position),
    transform: getSafeStageImageTransform(transformSource),
  };
}

export function cloneStageImageState(source = {}) {
  const normalized = normalizeStageImageState(source);
  return { ...normalized, transform: { ...normalized.transform } };
}

export function sortStageImages(images = []) {
  return [...images].sort((left, right) => {
    const planeDifference = (getSafeStageImagePlane(left?.plane) === "back" ? 0 : 1) -
      (getSafeStageImagePlane(right?.plane) === "back" ? 0 : 1);
    if (planeDifference) return planeDifference;
    const layerDifference = getSafeStageImageTransform(left?.transform).layer - getSafeStageImageTransform(right?.transform).layer;
    return layerDifference || getSafeStageImageLayerId(left?.layerId).localeCompare(getSafeStageImageLayerId(right?.layerId));
  });
}

export function applyStageImageBlock(visibleImages = [], block = {}) {
  const action = getSafeStageImageAction(block.action);
  const layerId = getSafeStageImageLayerId(block.layerId);
  const imageMap = new Map(
    (Array.isArray(visibleImages) ? visibleImages : [])
      .map((item) => cloneStageImageState(item))
      .map((item) => [item.layerId, item])
  );
  const previousState = imageMap.get(layerId) ?? null;
  const durationMs = getSafeStageImageDurationMs(block.durationMs);
  const easing = getSafeStageImageEasing(block.easing);
  if (action === "hide") {
    imageMap.delete(layerId);
    return {
      visibleImages: sortStageImages(imageMap.values()),
      event: previousState
        ? { mode: "hide", layerId, previousState: cloneStageImageState(previousState), durationMs, easing }
        : null,
    };
  }
  const targetState = normalizeStageImageState({ ...block, layerId }, previousState ?? {});
  imageMap.set(layerId, targetState);
  return {
    visibleImages: sortStageImages(imageMap.values()),
    event: {
      mode: previousState ? "move" : "show",
      layerId,
      previousState: previousState ? cloneStageImageState(previousState) : null,
      targetState: cloneStageImageState(targetState),
      durationMs,
      easing,
    },
  };
}

export function getStageImagePositionPercent(value) {
  return { left: 24, center: 50, right: 76 }[getSafeStageImagePosition(value)];
}

export function getStageImageStyle(source = {}) {
  const state = normalizeStageImageState(source);
  const transform = state.transform;
  return [
    `--stage-image-position-x:${getStageImagePositionPercent(state.position)}%`,
    `--stage-image-offset-x:${transform.offsetX}%`,
    `--stage-image-offset-y:${transform.offsetY}%`,
    `--stage-image-width:${transform.width}%`,
    `--stage-image-opacity:${transform.opacity / 100}`,
    `--stage-image-rotation:${transform.rotation}deg`,
    `--stage-image-layer:${transform.layer}`,
    `--stage-image-flip:${transform.flipX ? -1 : 1}`,
  ].join(";") + ";";
}

export function getStageImageMotionStyle(event = {}) {
  const previous = event.previousState ? normalizeStageImageState(event.previousState) : null;
  const easingCss = {
    linear: "linear",
    ease_in: "cubic-bezier(0.42, 0, 1, 1)",
    ease_out: "cubic-bezier(0.16, 1, 0.3, 1)",
    ease_in_out: "cubic-bezier(0.65, 0, 0.35, 1)",
    spring: "cubic-bezier(0.34, 1.56, 0.64, 1)",
  }[getSafeStageImageEasing(event.easing)];
  const values = [
    `--stage-image-motion-ms:${getSafeStageImageDurationMs(event.durationMs)}ms`,
    `--stage-image-motion-easing:${easingCss}`,
  ];
  if (previous) {
    values.push(
      `--stage-image-from-position-x:${getStageImagePositionPercent(previous.position)}%`,
      `--stage-image-from-offset-x:${previous.transform.offsetX}%`,
      `--stage-image-from-offset-y:${previous.transform.offsetY}%`,
      `--stage-image-from-width:${previous.transform.width}%`,
      `--stage-image-from-opacity:${previous.transform.opacity / 100}`,
      `--stage-image-from-rotation:${previous.transform.rotation}deg`,
      `--stage-image-from-flip:${previous.transform.flipX ? -1 : 1}`
    );
  }
  return values.join(";") + ";";
}

export function buildStageImageRenderItems(visibleImages = [], event = null, plane = "front") {
  const safePlane = getSafeStageImagePlane(plane);
  const items = (Array.isArray(visibleImages) ? visibleImages : [])
    .filter((item) => getSafeStageImagePlane(item.plane) === safePlane)
    .map((item) => ({ ...cloneStageImageState(item), ghostMode: "" }));
  if (event?.mode === "hide" && event.previousState && getSafeStageImagePlane(event.previousState.plane) === safePlane) {
    items.push({ ...cloneStageImageState(event.previousState), ghostMode: "hide" });
  }
  return items.map((item) => ({
    ...item,
    eventMode: event?.layerId === item.layerId ? event.mode : "",
    style: `${getStageImageStyle(item)}${event?.layerId === item.layerId ? getStageImageMotionStyle(event) : ""}`,
  }));
}
