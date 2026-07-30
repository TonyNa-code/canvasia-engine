export const MOBILE_READER_MODE_LABELS = Object.freeze({
  auto: "自动识别",
  on: "始终开启",
  off: "关闭触控栏",
});

export const MOBILE_READER_GESTURE_DEFAULTS = Object.freeze({
  minimumDistance: 56,
  maximumDurationMs: 900,
  axisDominance: 1.18,
});

const INTERACTIVE_TARGET_SELECTOR = [
  "button",
  "input",
  "select",
  "textarea",
  "label",
  "a",
  "[role='button']",
  "[contenteditable='true']",
  "[data-mobile-gesture-ignore]",
].join(",");

function getFiniteNumber(value, fallback = 0) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : fallback;
}

function clamp(value, minimum, maximum) {
  return Math.min(maximum, Math.max(minimum, value));
}

export function getSafeMobileReaderMode(value) {
  const mode = String(value ?? "auto").trim().toLowerCase();
  return Object.hasOwn(MOBILE_READER_MODE_LABELS, mode) ? mode : "auto";
}

export function detectMobileReaderEnvironment(globalObject = globalThis) {
  const viewport = globalObject?.visualViewport;
  const width = Math.max(0, getFiniteNumber(viewport?.width, globalObject?.innerWidth ?? 0));
  const height = Math.max(0, getFiniteNumber(viewport?.height, globalObject?.innerHeight ?? 0));
  const matchMedia = typeof globalObject?.matchMedia === "function"
    ? globalObject.matchMedia.bind(globalObject)
    : null;
  const coarsePointer = Boolean(matchMedia?.("(pointer: coarse)")?.matches);
  const anyCoarsePointer = Boolean(matchMedia?.("(any-pointer: coarse)")?.matches);
  const hoverUnavailable = Boolean(matchMedia?.("(hover: none)")?.matches);
  const standalone = Boolean(
    matchMedia?.("(display-mode: standalone)")?.matches ||
    globalObject?.navigator?.standalone
  );
  const narrowViewport = width > 0 && width <= 860;

  return {
    width,
    height,
    coarsePointer,
    anyCoarsePointer,
    hoverUnavailable,
    standalone,
    narrowViewport,
    touchCapable: coarsePointer || anyCoarsePointer || Number(globalObject?.navigator?.maxTouchPoints) > 0,
  };
}

export function resolveMobileReaderEnabled(mode, environment = {}) {
  const safeMode = getSafeMobileReaderMode(mode);
  if (safeMode === "on") {
    return true;
  }
  if (safeMode === "off") {
    return false;
  }
  return Boolean(
    environment.narrowViewport ||
    environment.coarsePointer ||
    environment.anyCoarsePointer ||
    environment.standalone
  );
}

export function shouldIgnoreMobileReaderTarget(target) {
  if (!target || typeof target.closest !== "function") {
    return false;
  }
  return Boolean(target.closest(INTERACTIVE_TARGET_SELECTOR));
}

export function classifyMobileReaderGesture(start = {}, end = {}, options = {}) {
  const minimumDistance = clamp(
    getFiniteNumber(options.minimumDistance, MOBILE_READER_GESTURE_DEFAULTS.minimumDistance),
    24,
    180
  );
  const maximumDurationMs = clamp(
    getFiniteNumber(options.maximumDurationMs, MOBILE_READER_GESTURE_DEFAULTS.maximumDurationMs),
    180,
    1800
  );
  const axisDominance = clamp(
    getFiniteNumber(options.axisDominance, MOBILE_READER_GESTURE_DEFAULTS.axisDominance),
    1,
    2.5
  );
  const deltaX = getFiniteNumber(end.x) - getFiniteNumber(start.x);
  const deltaY = getFiniteNumber(end.y) - getFiniteNumber(start.y);
  const distanceX = Math.abs(deltaX);
  const distanceY = Math.abs(deltaY);
  const durationMs = Math.max(0, getFiniteNumber(end.timeMs) - getFiniteNumber(start.timeMs));

  if (durationMs > maximumDurationMs || distanceY < minimumDistance) {
    return "";
  }
  if (distanceY < distanceX * axisDominance) {
    return "";
  }
  return deltaY < 0 ? "history" : "dialog";
}

export function buildMobileReaderControlGroup(status = {}) {
  const active = Boolean(status.active);
  return {
    title: "手机触控阅读",
    description: active
      ? "当前已启用沉浸式触控栏；手势只在剧情画面空白处生效，不会抢走选项或输入框操作。"
      : "在窄屏、触屏或独立安装的网页游戏中自动启用，也可在系统菜单手动开关。",
    shortcuts: [
      { keys: ["轻点画面"], label: "继续阅读", detail: "打字中先显示整句，再次轻点继续；点选项和按钮不会误触推进。" },
      { keys: ["画面上滑"], label: "剧情回看", detail: "打开最近剧情记录，可重播语音或安全回到经过的位置。" },
      { keys: ["画面下滑"], label: "隐藏 / 恢复对话框", detail: "用于查看 CG 与立绘；底部触控栏会继续保留。" },
      { keys: ["底部触控栏"], label: "回看 / 自动 / 隐框 / 菜单", detail: "常用动作始终落在拇指可达区域。" },
    ],
  };
}

function addMediaListener(mediaQuery, listener) {
  if (typeof mediaQuery?.addEventListener === "function") {
    mediaQuery.addEventListener("change", listener);
    return () => mediaQuery.removeEventListener?.("change", listener);
  }
  if (typeof mediaQuery?.addListener === "function") {
    mediaQuery.addListener(listener);
    return () => mediaQuery.removeListener?.(listener);
  }
  return () => {};
}

export function createMobileReaderController(options = {}) {
  const root = options.root;
  const gestureTarget = options.gestureTarget;
  const globalObject = options.globalObject ?? globalThis;
  const documentRef = options.documentRef ?? globalObject?.document;
  const onModeChange = typeof options.onModeChange === "function" ? options.onModeChange : () => {};
  const onGesture = typeof options.onGesture === "function" ? options.onGesture : () => {};
  const getMode = typeof options.getMode === "function" ? options.getMode : () => "auto";
  let active = false;
  let started = false;
  let pointerStart = null;
  let suppressClickUntil = 0;
  const cleanups = [];

  function updateViewportHeight(environment = detectMobileReaderEnvironment(globalObject)) {
    if (!root?.style?.setProperty || environment.height <= 0) {
      return;
    }
    root.style.setProperty("--runtime-mobile-viewport-height", `${Math.round(environment.height)}px`);
  }

  function refresh(reason = "refresh") {
    const environment = detectMobileReaderEnvironment(globalObject);
    const nextActive = resolveMobileReaderEnabled(getMode(), environment);
    updateViewportHeight(environment);
    if (nextActive !== active || reason === "started") {
      active = nextActive;
      onModeChange({ active, mode: getSafeMobileReaderMode(getMode()), environment, reason });
    }
    return { active, mode: getSafeMobileReaderMode(getMode()), environment };
  }

  function handlePointerDown(event) {
    if (!active || event?.isPrimary === false || shouldIgnoreMobileReaderTarget(event?.target)) {
      pointerStart = null;
      return;
    }
    const pointerType = String(event?.pointerType ?? "touch");
    if (pointerType === "mouse") {
      pointerStart = null;
      return;
    }
    pointerStart = {
      pointerId: event?.pointerId,
      x: getFiniteNumber(event?.clientX),
      y: getFiniteNumber(event?.clientY),
      timeMs: getFiniteNumber(event?.timeStamp, Date.now()),
    };
  }

  function handlePointerUp(event) {
    if (!active || !pointerStart || pointerStart.pointerId !== event?.pointerId) {
      pointerStart = null;
      return;
    }
    const gesture = classifyMobileReaderGesture(pointerStart, {
      x: getFiniteNumber(event?.clientX),
      y: getFiniteNumber(event?.clientY),
      timeMs: getFiniteNumber(event?.timeStamp, Date.now()),
    }, options.gestureOptions);
    pointerStart = null;
    if (!gesture) {
      return;
    }
    suppressClickUntil = Date.now() + 450;
    event?.preventDefault?.();
    onGesture(gesture, event);
  }

  function handlePointerCancel() {
    pointerStart = null;
  }

  function handleClickCapture(event) {
    if (Date.now() >= suppressClickUntil) {
      return;
    }
    event?.preventDefault?.();
    event?.stopImmediatePropagation?.();
  }

  function start() {
    if (started) {
      return refresh();
    }
    started = true;
    gestureTarget?.addEventListener?.("pointerdown", handlePointerDown, { passive: true });
    gestureTarget?.addEventListener?.("pointerup", handlePointerUp, { passive: false });
    gestureTarget?.addEventListener?.("pointercancel", handlePointerCancel, { passive: true });
    gestureTarget?.addEventListener?.("click", handleClickCapture, true);
    cleanups.push(
      () => gestureTarget?.removeEventListener?.("pointerdown", handlePointerDown),
      () => gestureTarget?.removeEventListener?.("pointerup", handlePointerUp),
      () => gestureTarget?.removeEventListener?.("pointercancel", handlePointerCancel),
      () => gestureTarget?.removeEventListener?.("click", handleClickCapture, true)
    );
    const refreshFromViewport = () => refresh("viewport");
    globalObject?.addEventListener?.("resize", refreshFromViewport, { passive: true });
    globalObject?.addEventListener?.("orientationchange", refreshFromViewport, { passive: true });
    globalObject?.visualViewport?.addEventListener?.("resize", refreshFromViewport, { passive: true });
    cleanups.push(
      () => globalObject?.removeEventListener?.("resize", refreshFromViewport),
      () => globalObject?.removeEventListener?.("orientationchange", refreshFromViewport),
      () => globalObject?.visualViewport?.removeEventListener?.("resize", refreshFromViewport)
    );
    if (typeof globalObject?.matchMedia === "function") {
      ["(pointer: coarse)", "(any-pointer: coarse)", "(hover: none)"].forEach((query) => {
        cleanups.push(addMediaListener(globalObject.matchMedia(query), refreshFromViewport));
      });
    }
    documentRef?.addEventListener?.("visibilitychange", refreshFromViewport);
    cleanups.push(() => documentRef?.removeEventListener?.("visibilitychange", refreshFromViewport));
    return refresh("started");
  }

  function stop() {
    cleanups.splice(0).forEach((cleanup) => cleanup());
    pointerStart = null;
    suppressClickUntil = 0;
    started = false;
    active = false;
  }

  return Object.freeze({
    start,
    stop,
    refresh,
    getStatus: () => ({ active, mode: getSafeMobileReaderMode(getMode()) }),
  });
}
