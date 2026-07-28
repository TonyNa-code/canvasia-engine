// Inline dialogue pacing shared by the editor preview and exported Web Runtime.

export const TEXT_PACING_PAUSE_MIN_MS = 50;
export const TEXT_PACING_PAUSE_MAX_MS = 5000;
export const TEXT_PACING_SPEEDS = Object.freeze(["slow", "normal", "fast", "instant", "inherit"]);

const TEXT_PACING_MARKER_PATTERN = /\[\[\s*(pause|speed)\s*=\s*([^\[\]]+?)\s*\]\]/gi;
const TEXT_PACING_SPEED_SET = new Set(TEXT_PACING_SPEEDS);

function clamp(value, minimum, maximum) {
  return Math.min(Math.max(value, minimum), maximum);
}

function freezeCue(cue) {
  return Object.freeze({ ...cue });
}

function buildEmptyPlan(sourceText = "") {
  const text = String(sourceText ?? "");
  return Object.freeze({
    sourceText: text,
    plainText: text,
    cues: Object.freeze([]),
    hasCues: false,
  });
}

export function getSafeTextPacingSpeed(value, fallback = "normal") {
  const safeFallback = TEXT_PACING_SPEED_SET.has(fallback) && fallback !== "inherit" ? fallback : "normal";
  const speed = String(value ?? "").trim().toLowerCase();
  return TEXT_PACING_SPEED_SET.has(speed) ? speed : safeFallback;
}

export function getSafeTextPacingPauseMs(value, fallback = 0) {
  const raw = String(value ?? "").trim();
  if (!/^\d+(?:\.\d+)?$/.test(raw)) {
    return Math.max(0, Number(fallback) || 0);
  }
  const milliseconds = Number.parseFloat(raw) * 1000;
  if (!Number.isFinite(milliseconds) || milliseconds <= 0) {
    return 0;
  }
  return Math.round(clamp(milliseconds, TEXT_PACING_PAUSE_MIN_MS, TEXT_PACING_PAUSE_MAX_MS));
}

export function parseRuntimeTextPacing(value) {
  const sourceText = String(value ?? "");
  if (!sourceText.includes("[[")) {
    return buildEmptyPlan(sourceText);
  }

  const cues = [];
  let plainText = "";
  let sourceIndex = 0;
  let match;
  TEXT_PACING_MARKER_PATTERN.lastIndex = 0;

  while ((match = TEXT_PACING_MARKER_PATTERN.exec(sourceText)) !== null) {
    plainText += sourceText.slice(sourceIndex, match.index);
    const command = String(match[1] ?? "").toLowerCase();
    const rawValue = String(match[2] ?? "").trim();
    let cue = null;

    if (command === "pause") {
      const pauseMs = getSafeTextPacingPauseMs(rawValue);
      if (pauseMs > 0) {
        cue = { index: plainText.length, type: "pause", pauseMs };
      }
    } else if (command === "speed") {
      const speed = rawValue.toLowerCase();
      if (TEXT_PACING_SPEED_SET.has(speed)) {
        cue = { index: plainText.length, type: "speed", speed };
      }
    }

    if (cue) {
      cues.push(freezeCue(cue));
    } else {
      plainText += match[0];
    }
    sourceIndex = TEXT_PACING_MARKER_PATTERN.lastIndex;
  }

  plainText += sourceText.slice(sourceIndex);
  return Object.freeze({
    sourceText,
    plainText,
    cues: Object.freeze(cues),
    hasCues: cues.length > 0,
  });
}

export function stripRuntimeTextPacing(value) {
  return parseRuntimeTextPacing(value).plainText;
}

export function getTextPacingPauseMsAt(plan, index) {
  const safeIndex = Math.max(0, Number(index) || 0);
  return (plan?.cues ?? []).reduce(
    (total, cue) => total + (cue.type === "pause" && cue.index === safeIndex ? cue.pauseMs : 0),
    0
  );
}

export function getTextPacingSpeedAt(plan, index, fallbackSpeed = "normal") {
  const fallback = getSafeTextPacingSpeed(fallbackSpeed);
  if (fallback === "instant") {
    return "instant";
  }

  const safeIndex = Math.max(0, Number(index) || 0);
  let speed = fallback;
  for (const cue of plan?.cues ?? []) {
    if (cue.index > safeIndex) break;
    if (cue.type === "speed") {
      speed = cue.speed === "inherit" ? fallback : getSafeTextPacingSpeed(cue.speed, fallback);
    }
  }
  return speed;
}

export function getNextTextPacingIndex(plan, currentIndex, getNextIndex) {
  const text = String(plan?.plainText ?? "");
  const safeIndex = Math.max(0, Math.min(Number(currentIndex) || 0, text.length));
  if (safeIndex >= text.length) {
    return text.length;
  }

  const nextIndex = Math.max(safeIndex, Math.min(Number(getNextIndex?.(text, safeIndex)) || 0, text.length));
  const boundary = (plan?.cues ?? [])
    .map((cue) => cue.index)
    .find((cueIndex) => cueIndex > safeIndex && cueIndex < nextIndex);
  return boundary ?? nextIndex;
}

export function getInitialTextPacingIndex(plan, getNextIndex) {
  if (getTextPacingPauseMsAt(plan, 0) > 0) {
    return 0;
  }
  return getNextTextPacingIndex(plan, 0, getNextIndex);
}

export function getTextPacingStepDelay(
  plan,
  currentIndex,
  fallbackSpeed,
  visibleText,
  fullText,
  getBaseDelay
) {
  if (getSafeTextPacingSpeed(fallbackSpeed) === "instant") {
    return 0;
  }
  const speed = getTextPacingSpeedAt(plan, currentIndex, fallbackSpeed);
  const baseDelay = speed === "instant"
    ? 0
    : Math.max(0, Number(getBaseDelay?.(speed, visibleText, fullText)) || 0);
  return baseDelay + getTextPacingPauseMsAt(plan, currentIndex);
}

export function buildTextPacingSummary(value) {
  const plan = parseRuntimeTextPacing(value);
  const pauseCount = plan.cues.filter((cue) => cue.type === "pause").length;
  const speedCount = plan.cues.filter((cue) => cue.type === "speed").length;
  if (!pauseCount && !speedCount) {
    return Object.freeze({ label: "尚未加入句内节奏", pauseCount: 0, speedCount: 0, hasCues: false });
  }
  const parts = [];
  if (pauseCount) parts.push(`${pauseCount} 处停顿`);
  if (speedCount) parts.push(`${speedCount} 次语速变化`);
  return Object.freeze({
    label: parts.join(" · "),
    pauseCount,
    speedCount,
    hasCues: true,
  });
}

const runtimeTextPacingApi = Object.freeze({
  TEXT_PACING_PAUSE_MIN_MS,
  TEXT_PACING_PAUSE_MAX_MS,
  TEXT_PACING_SPEEDS,
  getSafeTextPacingSpeed,
  getSafeTextPacingPauseMs,
  parseRuntimeTextPacing,
  stripRuntimeTextPacing,
  getTextPacingPauseMsAt,
  getTextPacingSpeedAt,
  getNextTextPacingIndex,
  getInitialTextPacingIndex,
  getTextPacingStepDelay,
  buildTextPacingSummary,
});

globalThis.CanvasiaRuntimeTextPacing = runtimeTextPacingApi;
