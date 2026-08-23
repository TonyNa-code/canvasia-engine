import {
  getSafeTextInputMaxLength,
  normalizeTextInputBlock,
  sanitizeTextInputValue,
} from "./runtime_text_variables.js";

export function createRuntimeTextInputController(options = {}) {
  const refs = options.refs ?? {};
  const windowRef = options.windowRef ?? globalThis.window;
  const listeners = [];
  let attached = false;
  let open = false;
  let snapshotKey = "";

  function getSnapshot() {
    return options.getSnapshot?.() ?? null;
  }

  function getVariable(variableId) {
    const variables = options.variablesById;
    if (variables instanceof Map) {
      return variables.get(variableId) ?? null;
    }
    return variables?.[variableId] ?? null;
  }

  function focus() {
    refs.input?.focus?.();
  }

  function close() {
    open = false;
    snapshotKey = "";
    if (refs.dialog) {
      refs.dialog.hidden = true;
    }
  }

  function renderCounter() {
    const snapshot = getSnapshot();
    const maxLength = getSafeTextInputMaxLength(snapshot?.block?.maxLength);
    const length = Array.from(refs.input?.value ?? "").length;
    if (refs.counter) {
      refs.counter.textContent = `${length} / ${maxLength}`;
    }
  }

  function showError(message = "") {
    if (!refs.error) {
      return;
    }
    refs.error.textContent = message;
    refs.error.hidden = !message;
  }

  function sync(snapshot = getSnapshot()) {
    if (!snapshot || snapshot.blockType !== "text_input" || !snapshot.block) {
      close();
      return false;
    }
    const nextSnapshotKey = String(options.getSnapshotKey?.(snapshot) ?? "");
    const config = normalizeTextInputBlock(snapshot.block);
    const variable = getVariable(config.variableId) ?? {};
    const localizedPrompt = options.getLocalizedValue?.(
      snapshot.block,
      "prompt",
      config.prompt
    ) ?? config.prompt;
    const prompt = options.interpolateLocalizedText?.(localizedPrompt, snapshot.variables) ?? localizedPrompt;
    const placeholder = options.getLocalizedValue?.(
      snapshot.block,
      "placeholder",
      config.placeholder
    ) ?? config.placeholder;

    if (refs.title) {
      refs.title.textContent = prompt;
    }
    if (refs.summary) {
      refs.summary.textContent = config.allowEmpty
        ? "可以留空；确认后答案会写入剧情变量并随存档保存。"
        : "填写后确认；答案会写入剧情变量并随存档保存。";
    }
    if (refs.label) {
      refs.label.textContent = variable.name || config.variableId || "你的答案";
    }
    if (refs.variable) {
      refs.variable.textContent = `保存到：${variable.name || config.variableId || "未选择变量"}`;
    }
    if (refs.input) {
      refs.input.type = variable.type === "number" ? "number" : "text";
      if (variable.type === "number") {
        refs.input.removeAttribute("maxlength");
      } else {
        refs.input.maxLength = config.maxLength;
      }
      refs.input.placeholder = placeholder;
      if (snapshotKey !== nextSnapshotKey) {
        const currentValue = Object.hasOwn(snapshot.variables ?? {}, config.variableId)
          ? snapshot.variables[config.variableId]
          : variable.defaultValue ?? "";
        refs.input.value = config.defaultValue || String(currentValue ?? "");
        showError();
      }
    }
    open = true;
    snapshotKey = nextSnapshotKey;
    if (refs.dialog) {
      refs.dialog.hidden = false;
    }
    renderCounter();
    if (typeof windowRef?.requestAnimationFrame === "function") {
      windowRef.requestAnimationFrame(focus);
    } else {
      focus();
    }
    return true;
  }

  function submit(event) {
    event?.preventDefault?.();
    const snapshot = getSnapshot();
    if (!snapshot || snapshot.blockType !== "text_input" || !snapshot.block) {
      close();
      return false;
    }
    const config = normalizeTextInputBlock(snapshot.block);
    const variable = getVariable(config.variableId);
    const result = sanitizeTextInputValue(refs.input?.value, config, variable, {
      normalizeValue: (value) => options.normalizeValue?.(config.variableId, value) ?? value,
    });
    if (!result.ok) {
      showError(result.error);
      focus();
      return false;
    }

    snapshot.variables[config.variableId] = result.value;
    options.persistVariables?.(snapshot.variables);
    snapshot.visualState.speakerName = "玩家输入";
    snapshot.visualState.dialogueText = `${variable?.name ?? config.variableId} 已保存。`;
    close();
    options.stopAutoAdvance?.();
    options.moveForward?.();
    options.render?.();
    options.onSubmitted?.({ config, result, snapshot });
    return true;
  }

  function addListener(target, eventName, callback) {
    if (typeof target?.addEventListener !== "function") {
      return;
    }
    target.addEventListener(eventName, callback);
    listeners.push([target, eventName, callback]);
  }

  function attach() {
    if (attached) {
      return;
    }
    attached = true;
    addListener(refs.form, "submit", submit);
    addListener(refs.input, "input", renderCounter);
  }

  function detach() {
    listeners.splice(0).forEach(([target, eventName, callback]) => {
      target.removeEventListener?.(eventName, callback);
    });
    attached = false;
  }

  function getState() {
    return Object.freeze({ attached, open, snapshotKey });
  }

  return Object.freeze({
    attach,
    detach,
    close,
    focus,
    sync,
    submit,
    renderCounter,
    showError,
    isOpen: () => open,
    getState,
  });
}
