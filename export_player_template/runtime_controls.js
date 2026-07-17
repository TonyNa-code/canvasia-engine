export const RUNTIME_KEY_BINDING_ACTIONS = Object.freeze([
  Object.freeze({ id: "advance", label: "推进剧情", detail: "显示整句或进入下一张剧情卡。", defaultCode: "Space" }),
  Object.freeze({ id: "system", label: "系统菜单", detail: "打开存档、设置和返回标题页入口。", defaultCode: "Tab" }),
  Object.freeze({ id: "rollback", label: "回退剧情", detail: "回到上一个可恢复的剧情状态。", defaultCode: "PageUp" }),
  Object.freeze({ id: "auto", label: "自动播放", detail: "按文字、语音和等待节奏连续阅读。", defaultCode: "KeyA" }),
  Object.freeze({ id: "skip", label: "跳过已读", detail: "只快进已经读过的内容。", defaultCode: "KeyS" }),
  Object.freeze({ id: "hide", label: "隐藏界面", detail: "隐藏对话框以欣赏背景、CG 或立绘。", defaultCode: "KeyU" }),
  Object.freeze({ id: "quickSave", label: "快速存档", detail: "保存当前剧情状态到快速存档。", defaultCode: "KeyQ" }),
  Object.freeze({ id: "quickLoad", label: "快速读档", detail: "读取最近一次快速存档。", defaultCode: "KeyL" }),
]);

export const DEFAULT_RUNTIME_KEY_BINDINGS = Object.freeze(
  Object.fromEntries(RUNTIME_KEY_BINDING_ACTIONS.map((action) => [action.id, action.defaultCode]))
);

export const RESERVED_RUNTIME_KEY_CODES = Object.freeze([
  "Escape",
  "Enter",
  "ArrowRight",
  "PageDown",
  "KeyH",
  "KeyO",
  "KeyP",
  "KeyR",
  "KeyV",
  "F1",
  "F2",
  "F5",
  "F6",
  "F7",
  "F8",
  "F9",
  "F11",
  "F12",
]);

const RESERVED_RUNTIME_KEY_CODE_SET = new Set(RESERVED_RUNTIME_KEY_CODES);
const RUNTIME_KEY_ACTION_IDS = new Set(RUNTIME_KEY_BINDING_ACTIONS.map((action) => action.id));
const SPECIAL_RUNTIME_KEY_CODES = new Set([
  "Space",
  "Tab",
  "Backspace",
  "Delete",
  "Insert",
  "Home",
  "End",
  "PageUp",
  "PageDown",
  "ArrowUp",
  "ArrowDown",
  "ArrowLeft",
]);

export function isRuntimeKeyCodeAllowed(value) {
  const code = typeof value === "string" ? value.trim() : "";
  if (!code || RESERVED_RUNTIME_KEY_CODE_SET.has(code)) {
    return false;
  }
  return SPECIAL_RUNTIME_KEY_CODES.has(code) || /^(?:Key[A-Z]|Digit[0-9]|Numpad[0-9])$/.test(code);
}

export function getRuntimeKeyLabel(value) {
  const code = typeof value === "string" ? value.trim() : "";
  const labels = {
    Space: "Space",
    Tab: "Tab",
    Backspace: "Backspace",
    Delete: "Delete",
    Insert: "Insert",
    Home: "Home",
    End: "End",
    PageUp: "PageUp",
    PageDown: "PageDown",
    ArrowUp: "↑",
    ArrowDown: "↓",
    ArrowLeft: "←",
  };
  if (labels[code]) {
    return labels[code];
  }
  if (/^Key[A-Z]$/.test(code)) {
    return code.slice(3);
  }
  if (/^(?:Digit|Numpad)[0-9]$/.test(code)) {
    return code.slice(code.startsWith("Digit") ? 5 : 6);
  }
  return code || "未设置";
}

function assignBindingWithoutSanitizing(bindings, actionId, code) {
  const previousCode = bindings[actionId];
  const conflictingAction = Object.keys(bindings).find(
    (candidateId) => candidateId !== actionId && bindings[candidateId] === code
  );
  bindings[actionId] = code;
  if (conflictingAction) {
    bindings[conflictingAction] = previousCode;
  }
  return conflictingAction ?? "";
}

export function sanitizeRuntimeKeyBindings(source = {}) {
  const result = { ...DEFAULT_RUNTIME_KEY_BINDINGS };
  if (!source || typeof source !== "object" || Array.isArray(source)) {
    return result;
  }
  RUNTIME_KEY_BINDING_ACTIONS.forEach((action) => {
    const code = source[action.id];
    if (isRuntimeKeyCodeAllowed(code)) {
      assignBindingWithoutSanitizing(result, action.id, code.trim());
    }
  });
  return result;
}

export function assignRuntimeKeyBinding(source, actionId, code) {
  const bindings = sanitizeRuntimeKeyBindings(source);
  const safeActionId = typeof actionId === "string" ? actionId.trim() : "";
  const safeCode = typeof code === "string" ? code.trim() : "";
  if (!RUNTIME_KEY_ACTION_IDS.has(safeActionId) || !isRuntimeKeyCodeAllowed(safeCode)) {
    return { bindings, changed: false, displacedAction: "" };
  }
  const displacedAction = assignBindingWithoutSanitizing(bindings, safeActionId, safeCode);
  return { bindings, changed: true, displacedAction };
}

export function getRuntimeActionForCode(source, code) {
  const safeCode = typeof code === "string" ? code.trim() : "";
  if (!safeCode) {
    return "";
  }
  const bindings = sanitizeRuntimeKeyBindings(source);
  return Object.keys(bindings).find((actionId) => bindings[actionId] === safeCode) ?? "";
}

export function buildRuntimeShortcutGroups(source = DEFAULT_RUNTIME_KEY_BINDINGS) {
  const bindings = sanitizeRuntimeKeyBindings(source);
  const label = (actionId) => getRuntimeKeyLabel(bindings[actionId]);
  return [
    {
      title: "剧情推进",
      description: "最常用的阅读、回看和显示控制。",
      shortcuts: [
        { keys: [label("advance"), "Enter", "→"], label: "继续 / 显示整句", detail: "打字机播放中会先显示整句，之后再推进剧情。" },
        { keys: [label("rollback")], label: "回退剧情", detail: "回到上一个可恢复的剧情状态。" },
        { keys: [label("hide"), "右键"], label: "隐藏 / 显示对话框", detail: "适合欣赏背景、CG 或人物立绘。" },
        { keys: ["F1", "Shift + ?"], label: "打开操作指南", detail: "随时查看当前 Runtime 支持的玩家操作。" },
      ],
    },
    {
      title: "存档与系统",
      description: "关键分支前后最容易用到的安全操作。",
      shortcuts: [
        { keys: [label("quickSave")], label: "快速存档", detail: "把当前节点保存到快速存档位。" },
        { keys: [label("quickLoad")], label: "快速读档", detail: "回到最近一次快速存档。" },
        { keys: [label("system")], label: "打开系统菜单", detail: "进入存档、设置、操作指南和标题页入口。" },
        { keys: ["Esc"], label: "关闭当前面板", detail: "优先关闭最上层弹窗，再回到游戏。" },
      ],
    },
    {
      title: "自动播放",
      description: "适合录屏、演示或连续阅读的操作。",
      shortcuts: [
        { keys: [label("auto")], label: "自动播放", detail: "按文字长度、语音和等待卡节奏自动推进。" },
        { keys: [label("skip")], label: "跳过已读开关", detail: "只跳过已经读过的文本，遇到未读内容会自动停下。" },
        { keys: ["重播语音"], label: "重播当前语音", detail: "当前台词有语音时可重新播放。" },
      ],
    },
  ];
}

export const RUNTIME_SHORTCUT_GROUPS = Object.freeze(buildRuntimeShortcutGroups());

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderShortcutKeys(keys) {
  return (Array.isArray(keys) ? keys : [])
    .map((key) => `<kbd>${escapeHtml(key)}</kbd>`)
    .join("");
}

export function renderOperationGuideGroup(group) {
  return `
    <article class="operation-guide-group">
      <div class="operation-guide-group-head">
        <h3>${escapeHtml(group.title)}</h3>
        <p>${escapeHtml(group.description)}</p>
      </div>
      <div class="operation-shortcut-list">
        ${(group.shortcuts ?? [])
          .map(
            (shortcut) => `
              <div class="operation-shortcut-row">
                <div class="operation-shortcut-keys">${renderShortcutKeys(shortcut.keys)}</div>
                <div>
                  <strong>${escapeHtml(shortcut.label)}</strong>
                  <p>${escapeHtml(shortcut.detail)}</p>
                </div>
              </div>
            `
          )
          .join("")}
      </div>
    </article>
  `;
}

export function renderOperationGuideGroups(groups = RUNTIME_SHORTCUT_GROUPS) {
  return groups.map(renderOperationGuideGroup).join("");
}

export function renderRuntimeKeyBindingRows(source = {}, options = {}) {
  const escape = typeof options.escapeHtml === "function" ? options.escapeHtml : escapeHtml;
  const captureAction = typeof options.captureAction === "string" ? options.captureAction : "";
  const bindings = sanitizeRuntimeKeyBindings(source);
  return RUNTIME_KEY_BINDING_ACTIONS.map((action) => {
    const isCapturing = captureAction === action.id;
    return `
      <article class="key-binding-row ${isCapturing ? "is-capturing" : ""}" data-key-binding-row="${escape(action.id)}">
        <div class="key-binding-copy">
          <strong>${escape(action.label)}</strong>
          <span>${escape(action.detail)}</span>
        </div>
        <button
          class="pill-button is-secondary key-binding-button"
          type="button"
          data-runtime-key-binding="${escape(action.id)}"
          aria-pressed="${isCapturing ? "true" : "false"}"
        >${escape(isCapturing ? "请按新按键…" : getRuntimeKeyLabel(bindings[action.id]))}</button>
      </article>
    `;
  }).join("");
}

export function createRuntimeKeyBindingController(options = {}) {
  const refs = options.refs ?? {};
  const documentRef = options.documentRef ?? globalThis.document;
  const getBindings = typeof options.getBindings === "function" ? options.getBindings : () => ({});
  const setBindings = typeof options.setBindings === "function" ? options.setBindings : () => {};
  const persist = typeof options.persist === "function" ? options.persist : () => {};
  const onChanged = typeof options.onChanged === "function" ? options.onChanged : () => {};
  const escape = typeof options.escapeHtml === "function" ? options.escapeHtml : escapeHtml;
  let captureAction = "";
  let statusMessage = "点击一项后直接按下新按键；如与其他操作冲突，两项会自动交换。";

  function render() {
    const bindings = sanitizeRuntimeKeyBindings(getBindings());
    if (refs.list) {
      refs.list.innerHTML = renderRuntimeKeyBindingRows(bindings, { escapeHtml: escape, captureAction });
    }
    if (refs.summary) {
      const customizedCount = RUNTIME_KEY_BINDING_ACTIONS.filter(
        (action) => bindings[action.id] !== DEFAULT_RUNTIME_KEY_BINDINGS[action.id]
      ).length;
      refs.summary.textContent = customizedCount
        ? `已自定义 ${customizedCount} 项 · 点击按键可继续修改`
        : "当前使用推荐键位，可按习惯逐项修改。";
    }
    if (refs.status) {
      refs.status.textContent = statusMessage;
    }
    if (refs.resetButton) {
      refs.resetButton.disabled = RUNTIME_KEY_BINDING_ACTIONS.every(
        (action) => bindings[action.id] === DEFAULT_RUNTIME_KEY_BINDINGS[action.id]
      );
    }
  }

  function commit(bindings) {
    setBindings(sanitizeRuntimeKeyBindings(bindings));
    persist();
    onChanged();
    render();
  }

  function handleClick(event) {
    const button = event.target?.closest?.("[data-runtime-key-binding]");
    if (!button) {
      return;
    }
    const actionId = button.dataset.runtimeKeyBinding;
    captureAction = captureAction === actionId ? "" : actionId;
    statusMessage = captureAction
      ? "正在等待新按键。再次点击当前项目可取消。"
      : "已取消修改，原按键保持不变。";
    render();
  }

  function handleKeydown(event) {
    if (!captureAction) {
      return false;
    }
    event.preventDefault?.();
    event.stopImmediatePropagation?.();
    if (event.altKey || event.ctrlKey || event.metaKey) {
      statusMessage = "组合键暂不支持，请直接按一个字母、数字或导航键。";
      render();
      return true;
    }
    if (!isRuntimeKeyCodeAllowed(event.code)) {
      statusMessage = "这个按键由关闭、帮助、截图或存档保底操作占用，请换一个按键。";
      render();
      return true;
    }
    const action = RUNTIME_KEY_BINDING_ACTIONS.find((item) => item.id === captureAction);
    const result = assignRuntimeKeyBinding(getBindings(), captureAction, event.code);
    captureAction = "";
    statusMessage = result.displacedAction
      ? `${action?.label ?? "当前操作"}已更新；冲突操作已自动换到原按键。`
      : `${action?.label ?? "当前操作"}已更新。`;
    commit(result.bindings);
    return true;
  }

  function reset() {
    captureAction = "";
    statusMessage = "已恢复推荐键位。";
    commit(DEFAULT_RUNTIME_KEY_BINDINGS);
  }

  function attach() {
    refs.list?.addEventListener("click", handleClick);
    refs.resetButton?.addEventListener("click", reset);
    documentRef?.addEventListener?.("keydown", handleKeydown);
  }

  return Object.freeze({ attach, handleKeydown, render, reset });
}

export function handleRuntimeModalKeydown(event, modalEntries, isTypingTarget = () => false) {
  const activeEntry = (Array.isArray(modalEntries) ? modalEntries : []).find((entry) => {
    const isOpen = typeof entry?.isOpen === "function" ? entry.isOpen() : entry?.isOpen;
    return Boolean(isOpen);
  });
  if (!activeEntry) {
    return false;
  }
  if (event?.code === "Escape") {
    event.preventDefault?.();
    activeEntry.close?.();
    return true;
  }
  if (!isTypingTarget(event?.target)) {
    event?.preventDefault?.();
  }
  return true;
}
