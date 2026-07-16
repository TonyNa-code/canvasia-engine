export const RUNTIME_GAMEPAD_AXIS_DEAD_ZONE = 0.62;
export const RUNTIME_GAMEPAD_CONNECTED_POLL_INTERVAL_MS = 32;
export const RUNTIME_GAMEPAD_IDLE_POLL_INTERVAL_MS = 500;

export const RUNTIME_GAMEPAD_BUTTON_ACTIONS = Object.freeze({
  0: "confirm",
  1: "back",
  2: "history",
  3: "system",
  4: "history",
  5: "auto",
  6: "skip",
  7: "system",
  12: "up",
  13: "down",
  14: "left",
  15: "right",
});

const RUNTIME_FOCUSABLE_SELECTOR = [
  "button:not([disabled])",
  "[href]",
  "input:not([disabled])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  "[tabindex]:not([tabindex='-1'])",
].join(",");

function getAxisDirection(value, deadZone = RUNTIME_GAMEPAD_AXIS_DEAD_ZONE) {
  const numericValue = Number(value);
  const safeDeadZone = Math.min(0.95, Math.max(0.25, Number(deadZone) || RUNTIME_GAMEPAD_AXIS_DEAD_ZONE));
  if (!Number.isFinite(numericValue)) {
    return 0;
  }
  if (numericValue <= -safeDeadZone) {
    return -1;
  }
  if (numericValue >= safeDeadZone) {
    return 1;
  }
  return 0;
}

function isButtonPressed(button) {
  if (typeof button === "number") {
    return button >= 0.5;
  }
  return Boolean(button?.pressed || Number(button?.value) >= 0.5);
}

function getConnectedGamepads(gamepads) {
  return Array.from(gamepads ?? []).filter((gamepad) => gamepad && gamepad.connected !== false);
}

export function buildRuntimeGamepadState() {
  return { pads: {} };
}

export function buildRuntimeGamepadStatus(gamepads = []) {
  const names = getConnectedGamepads(gamepads).map((gamepad) => String(gamepad.id || "Gamepad").trim().slice(0, 80));
  const connectedCount = names.length;
  const label = connectedCount === 0
    ? "未连接"
    : connectedCount === 1
      ? `1 个 · ${names[0]}`
      : `${connectedCount} 个 · ${names[0]} 等`;
  return {
    connected: connectedCount > 0,
    connectedCount,
    names,
    label,
    signature: `${connectedCount}:${names.join("|")}`,
  };
}

export function translateRuntimeGamepads(gamepads, previousState = buildRuntimeGamepadState(), options = {}) {
  const deadZone = options.deadZone ?? RUNTIME_GAMEPAD_AXIS_DEAD_ZONE;
  const previousPads = previousState?.pads && typeof previousState.pads === "object" ? previousState.pads : {};
  const nextState = buildRuntimeGamepadState();
  const actions = [];

  getConnectedGamepads(gamepads).forEach((gamepad, fallbackIndex) => {
    const gamepadIndex = Number.isInteger(gamepad.index) ? gamepad.index : fallbackIndex;
    const gamepadKey = String(gamepadIndex);
    const previousPad = previousPads[gamepadKey] ?? { buttons: [], axes: [0, 0] };
    const nextButtons = Array.from(gamepad.buttons ?? [], isButtonPressed);
    const emittedActions = new Set();

    Object.entries(RUNTIME_GAMEPAD_BUTTON_ACTIONS).forEach(([buttonIndex, action]) => {
      const index = Number(buttonIndex);
      if (nextButtons[index] && !previousPad.buttons?.[index] && !emittedActions.has(action)) {
        actions.push(action);
        emittedActions.add(action);
      }
    });

    const nextAxes = [
      getAxisDirection(gamepad.axes?.[0], deadZone),
      getAxisDirection(gamepad.axes?.[1], deadZone),
    ];
    nextAxes.forEach((direction, axisIndex) => {
      if (!direction || direction === Number(previousPad.axes?.[axisIndex] || 0)) {
        return;
      }
      const action = axisIndex === 0
        ? (direction < 0 ? "left" : "right")
        : (direction < 0 ? "up" : "down");
      if (!emittedActions.has(action)) {
        actions.push(action);
        emittedActions.add(action);
      }
    });

    nextState.pads[gamepadKey] = {
      buttons: nextButtons,
      axes: nextAxes,
    };
  });

  return {
    actions,
    state: nextState,
    status: buildRuntimeGamepadStatus(gamepads),
  };
}

export function buildRuntimeGamepadControlGroup(status = buildRuntimeGamepadStatus()) {
  return {
    title: "手柄操作",
    description: status.connected
      ? `已连接：${status.label}。当前页面可以直接用手柄操作。`
      : "支持标准布局手柄；连接后按任意键即可开始操作。",
    shortcuts: [
      { keys: ["左摇杆 / 十字键"], label: "移动焦点", detail: "按屏幕方向操作标题页、选项、存档、设置与回想馆。" },
      { keys: ["A / ×", "B / ○"], label: "确认 / 返回", detail: "确认当前按钮；返回键关闭面板，阅读中则打开系统菜单。" },
      { keys: ["X / □", "LB / L1"], label: "回看上一句", detail: "回到已经经过的上一条剧情文本。" },
      { keys: ["Y / △ / Menu", "RB / R1", "View"], label: "菜单 / 自动 / 已读快进", detail: "覆盖长篇视觉小说常用的阅读辅助动作。" },
    ],
  };
}

function isRuntimeFocusableElementVisible(element) {
  if (!element || element.disabled || element.hidden || element.getAttribute?.("aria-hidden") === "true") {
    return false;
  }
  if (element.closest?.("[hidden], [aria-hidden='true']")) {
    return false;
  }
  const rect = element.getBoundingClientRect?.();
  return !rect || rect.width > 0 || rect.height > 0;
}

export function getRuntimeFocusableElements(root) {
  if (!root?.querySelectorAll) {
    return [];
  }
  return Array.from(root.querySelectorAll(RUNTIME_FOCUSABLE_SELECTOR)).filter(isRuntimeFocusableElementVisible);
}

export function chooseRuntimeGamepadConfirmTarget(root, preferredElements = [], options = {}) {
  const documentRef = options.documentRef ?? globalThis.document;
  const candidates = getRuntimeFocusableElements(root);
  const activeElement = documentRef?.activeElement;
  if (candidates.includes(activeElement)) {
    return activeElement;
  }
  const preferredTarget = Array.from(preferredElements ?? []).find((element) => candidates.includes(element));
  return preferredTarget ?? candidates[0] ?? null;
}

function getRectCenter(element) {
  const rect = element?.getBoundingClientRect?.() ?? {};
  const left = Number(rect.left) || 0;
  const top = Number(rect.top) || 0;
  const width = Number(rect.width) || 0;
  const height = Number(rect.height) || 0;
  return { x: left + width / 2, y: top + height / 2 };
}

export function chooseDirectionalFocusTarget(currentElement, candidates, direction) {
  const safeCandidates = Array.from(candidates ?? []).filter(Boolean);
  if (!safeCandidates.length) {
    return null;
  }
  if (!currentElement || !safeCandidates.includes(currentElement)) {
    return safeCandidates[0];
  }

  const currentCenter = getRectCenter(currentElement);
  const horizontal = direction === "left" || direction === "right";
  const sign = direction === "left" || direction === "up" ? -1 : 1;
  let best = null;
  let bestScore = Number.POSITIVE_INFINITY;

  safeCandidates.forEach((candidate) => {
    if (candidate === currentElement) {
      return;
    }
    const center = getRectCenter(candidate);
    const primaryDelta = horizontal ? center.x - currentCenter.x : center.y - currentCenter.y;
    if (primaryDelta * sign <= 2) {
      return;
    }
    const secondaryDelta = horizontal ? Math.abs(center.y - currentCenter.y) : Math.abs(center.x - currentCenter.x);
    const score = Math.abs(primaryDelta) + secondaryDelta * 2.25;
    if (score < bestScore) {
      best = candidate;
      bestScore = score;
    }
  });

  if (best) {
    return best;
  }
  const currentIndex = safeCandidates.indexOf(currentElement);
  const step = sign < 0 ? -1 : 1;
  return safeCandidates[(currentIndex + step + safeCandidates.length) % safeCandidates.length];
}

export function moveRuntimeGamepadFocus(root, direction, options = {}) {
  const documentRef = options.documentRef ?? globalThis.document;
  const candidates = getRuntimeFocusableElements(root);
  const activeElement = root?.contains?.(documentRef?.activeElement) ? documentRef.activeElement : null;
  const nextElement = chooseDirectionalFocusTarget(activeElement, candidates, direction);
  if (!nextElement) {
    return null;
  }
  try {
    nextElement.focus({ preventScroll: true });
  } catch (error) {
    nextElement.focus?.();
  }
  nextElement.scrollIntoView?.({ block: "nearest", inline: "nearest" });
  return nextElement;
}

function dispatchRuntimeControlEvent(element, eventName, EventCtor = globalThis.Event) {
  if (!element?.dispatchEvent || typeof EventCtor !== "function") {
    return;
  }
  element.dispatchEvent(new EventCtor(eventName, { bubbles: true }));
}

export function adjustRuntimeGamepadControl(direction, root, options = {}) {
  if (direction !== "left" && direction !== "right") {
    return false;
  }
  const documentRef = options.documentRef ?? globalThis.document;
  const activeElement = documentRef?.activeElement;
  if (!root?.contains?.(activeElement)) {
    return false;
  }
  const step = direction === "left" ? -1 : 1;
  if (activeElement?.tagName === "SELECT") {
    const nextIndex = Math.min(Math.max(activeElement.selectedIndex + step, 0), activeElement.options.length - 1);
    if (nextIndex === activeElement.selectedIndex) {
      return true;
    }
    activeElement.selectedIndex = nextIndex;
    dispatchRuntimeControlEvent(activeElement, "change", options.EventCtor);
    return true;
  }
  if (activeElement?.tagName === "INPUT" && activeElement.type === "range") {
    if (step < 0) {
      activeElement.stepDown?.();
    } else {
      activeElement.stepUp?.();
    }
    dispatchRuntimeControlEvent(activeElement, "input", options.EventCtor);
    dispatchRuntimeControlEvent(activeElement, "change", options.EventCtor);
    return true;
  }
  return false;
}

export function buildRuntimeGamepadKeyboardEvent(code, target = null) {
  return {
    altKey: false,
    code,
    ctrlKey: false,
    defaultPrevented: false,
    metaKey: false,
    runtimeGamepad: true,
    shiftKey: false,
    target,
    preventDefault() {
      this.defaultPrevented = true;
    },
  };
}

export function createRuntimeGamepadController(options = {}) {
  const navigatorRef = options.navigatorRef ?? globalThis.navigator;
  const eventTarget = options.eventTarget ?? globalThis.window;
  const requestFrame = options.requestFrame ?? globalThis.requestAnimationFrame?.bind(globalThis);
  const cancelFrame = options.cancelFrame ?? globalThis.cancelAnimationFrame?.bind(globalThis);
  const now = options.now ?? (() => globalThis.performance?.now?.() ?? Date.now());
  const isActive = options.isActive ?? (() => true);
  const getGamepads = options.getGamepads ?? (() => navigatorRef?.getGamepads?.() ?? []);
  const onAction = typeof options.onAction === "function" ? options.onAction : () => {};
  const onStatusChange = typeof options.onStatusChange === "function" ? options.onStatusChange : () => {};
  let inputState = buildRuntimeGamepadState();
  let status = buildRuntimeGamepadStatus();
  let running = false;
  let frameId = null;
  let lastPollAt = Number.NEGATIVE_INFINITY;

  function poll(timestamp = now(), force = false) {
    if (!running || !isActive()) {
      return status;
    }
    const interval = status.connected
      ? (options.connectedPollIntervalMs ?? RUNTIME_GAMEPAD_CONNECTED_POLL_INTERVAL_MS)
      : (options.idlePollIntervalMs ?? RUNTIME_GAMEPAD_IDLE_POLL_INTERVAL_MS);
    if (!force && Number(timestamp) - lastPollAt < interval) {
      return status;
    }
    lastPollAt = Number(timestamp);
    const result = translateRuntimeGamepads(getGamepads(), inputState, options);
    inputState = result.state;
    if (result.status.signature !== status.signature) {
      status = result.status;
      onStatusChange({ ...status });
    } else {
      status = result.status;
    }
    result.actions.forEach((action) => onAction(action, { ...status }));
    return status;
  }

  function scheduleNextFrame() {
    if (!running || typeof requestFrame !== "function") {
      return;
    }
    frameId = requestFrame((timestamp) => {
      poll(timestamp);
      scheduleNextFrame();
    });
  }

  function refresh() {
    inputState = buildRuntimeGamepadState();
    return poll(now(), true);
  }

  function start() {
    if (running) {
      return status;
    }
    running = true;
    eventTarget?.addEventListener?.("gamepadconnected", refresh);
    eventTarget?.addEventListener?.("gamepaddisconnected", refresh);
    refresh();
    scheduleNextFrame();
    return status;
  }

  function stop() {
    if (!running) {
      return;
    }
    running = false;
    eventTarget?.removeEventListener?.("gamepadconnected", refresh);
    eventTarget?.removeEventListener?.("gamepaddisconnected", refresh);
    if (frameId != null && typeof cancelFrame === "function") {
      cancelFrame(frameId);
    }
    frameId = null;
  }

  return {
    getStatus: () => ({ ...status }),
    poll,
    refresh,
    start,
    stop,
  };
}
