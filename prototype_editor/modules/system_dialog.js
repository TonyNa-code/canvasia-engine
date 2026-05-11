(function attachSystemDialogTools(global) {
  const DEFAULT_TOAST_HIDE_MS = 1800;

  function normalizeSystemDialogOptions(options = {}) {
    const message = Array.isArray(options.message)
      ? options.message.filter(Boolean).join("\n")
      : String(options.message ?? "");
    const input = options.input && typeof options.input === "object" ? options.input : null;
    const copyText =
      options.copyText === false
        ? ""
        : String(
            options.copyText ??
              (options.copyable || message.length > 90 || message.includes("\n") ? message : "")
          );
    return {
      title: String(options.title ?? "提示"),
      eyebrow: String(options.eyebrow ?? "Canvasia Engine"),
      message,
      tone: ["danger", "warning", "success", "info"].includes(options.tone) ? options.tone : "info",
      confirmLabel: String(options.confirmLabel ?? "知道了"),
      cancelLabel: String(options.cancelLabel ?? "取消"),
      showCancel: Boolean(options.showCancel),
      allowBackdropClose: options.allowBackdropClose !== false,
      copyText,
      copyLabel: String(options.copyLabel ?? "复制详情"),
      copySuccessMessage: String(options.copySuccessMessage ?? "弹窗详情已复制"),
      input: input
        ? {
            value: String(input.value ?? ""),
            placeholder: String(input.placeholder ?? ""),
            maxLength: Number.isFinite(Number(input.maxLength)) ? Number(input.maxLength) : 80,
            required: input.required !== false,
            requiredMessage: String(input.requiredMessage ?? "这里需要填写内容。"),
          }
        : null,
    };
  }

  function inferSystemAlertOptions(message) {
    const text = String(message ?? "");
    const isFailure = /失败|没有成功|错误|异常|Error|Exception|Traceback/i.test(text);
    const isWarning = /不能|无法|暂时|先选|先填|缺失|找不到/.test(text);
    const tone = isFailure ? "danger" : isWarning ? "warning" : "info";
    const title = isFailure ? "操作失败" : isWarning ? "需要处理" : "提示";
    return {
      title,
      message: text,
      tone,
      copyable: isFailure || text.length > 90 || text.includes("\n"),
    };
  }

  function getSystemDialogToneMark(tone) {
    if (tone === "danger") {
      return "!";
    }
    if (tone === "warning") {
      return "?";
    }
    if (tone === "success") {
      return "✓";
    }
    return "i";
  }

  function createSystemDialogController(options = {}) {
    const rootWindow = options.window ?? global;
    const rootDocument = options.document ?? rootWindow?.document ?? global.document;
    const toastElement = options.toastElement ?? null;
    const copyTextToClipboard =
      typeof options.copyTextToClipboard === "function"
        ? options.copyTextToClipboard
        : async () => false;
    const fallbackAlert =
      typeof options.fallbackAlert === "function"
        ? options.fallbackAlert
        : typeof rootWindow?.alert === "function"
          ? rootWindow.alert.bind(rootWindow)
          : null;

    let toastTimer = null;
    let dialogRoot = null;
    let activeDialog = null;
    const dialogQueue = [];

    function showToast(message, tone = "soft") {
      if (!toastElement || !message) {
        return;
      }

      toastElement.textContent = message;
      toastElement.className =
        tone === "error" ? "interaction-toast is-visible is-error" : "interaction-toast is-visible";

      if (toastTimer) {
        rootWindow.clearTimeout(toastTimer);
      }

      toastTimer = rootWindow.setTimeout(() => {
        toastElement.className = tone === "error" ? "interaction-toast is-error" : "interaction-toast";
      }, DEFAULT_TOAST_HIDE_MS);
    }

    function ensureDialogRoot() {
      if (dialogRoot?.isConnected) {
        return dialogRoot;
      }
      if (!rootDocument?.body) {
        return null;
      }

      dialogRoot = rootDocument.createElement("div");
      dialogRoot.className = "system-dialog-backdrop";
      dialogRoot.setAttribute("role", "presentation");
      dialogRoot.hidden = true;
      rootDocument.body.append(dialogRoot);
      return dialogRoot;
    }

    function installAlertBridge() {
      if (!rootWindow || rootWindow.__tonyNaEngineDialogBridgeInstalled) {
        return;
      }

      rootWindow.__tonyNaEngineDialogBridgeInstalled = true;
      rootWindow.alert = (message) => {
        void showAlert(inferSystemAlertOptions(message));
      };
    }

    function showAlert(alertOptions = {}) {
      if (!rootDocument?.body) {
        fallbackAlert?.(String(alertOptions?.message ?? alertOptions ?? ""));
        return Promise.resolve(true);
      }

      const normalizedOptions =
        typeof alertOptions === "object" && alertOptions !== null
          ? alertOptions
          : {
              message: alertOptions,
            };
      return showDialog({
        title: "提示",
        tone: "info",
        confirmLabel: "知道了",
        ...normalizedOptions,
        showCancel: false,
      });
    }

    function showConfirm(confirmOptions = {}) {
      return showDialog({
        title: "确认操作",
        tone: "warning",
        confirmLabel: "确认继续",
        cancelLabel: "先不动",
        ...confirmOptions,
        showCancel: true,
      });
    }

    async function showPrompt(promptOptions = {}) {
      const result = await showDialog({
        title: "输入内容",
        tone: "info",
        confirmLabel: "确认",
        cancelLabel: "取消",
        ...promptOptions,
        showCancel: true,
        input: {
          value: promptOptions.defaultValue ?? promptOptions.value ?? "",
          placeholder: promptOptions.placeholder ?? "",
          maxLength: promptOptions.maxLength ?? 80,
          required: promptOptions.required ?? true,
          requiredMessage: promptOptions.requiredMessage ?? "先填一个名称，再继续。",
          ...(promptOptions.input ?? {}),
        },
      });
      return result === null || result === false ? null : String(result ?? "");
    }

    function showDialog(dialogOptions = {}) {
      return new Promise((resolve) => {
        dialogQueue.push({
          options: normalizeSystemDialogOptions(dialogOptions),
          previousFocus: rootWindow.HTMLElement && rootDocument?.activeElement instanceof rootWindow.HTMLElement
            ? rootDocument.activeElement
            : null,
          resolve,
        });
        renderNextDialog();
      });
    }

    function renderNextDialog() {
      if (activeDialog || dialogQueue.length === 0) {
        return;
      }

      const root = ensureDialogRoot();
      if (!root) {
        const request = dialogQueue.shift();
        fallbackAlert?.(request?.options?.message ?? "");
        request?.resolve(true);
        renderNextDialog();
        return;
      }
      const request = dialogQueue.shift();
      const close = (confirmed) => {
        if (activeDialog?.close !== close) {
          return;
        }

        root.hidden = true;
        root.replaceChildren();
        activeDialog = null;
        if (request.previousFocus?.isConnected) {
          request.previousFocus.focus({ preventScroll: true });
        }
        request.resolve(confirmed);
        renderNextDialog();
      };

      activeDialog = {
        close,
        options: request.options,
      };

      renderDialog(root, request.options, close);
    }

    function renderDialog(root, dialogOptions, close) {
      root.hidden = false;
      root.dataset.tone = dialogOptions.tone;
      root.replaceChildren();

      const dialog = rootDocument.createElement("section");
      dialog.className = "system-dialog";
      dialog.setAttribute("role", "dialog");
      dialog.setAttribute("aria-modal", "true");
      dialog.setAttribute("aria-labelledby", "systemDialogTitle");
      dialog.addEventListener("click", (event) => event.stopPropagation());

      const halo = rootDocument.createElement("div");
      halo.className = "system-dialog-halo";
      halo.setAttribute("aria-hidden", "true");

      const header = rootDocument.createElement("div");
      header.className = "system-dialog-header";

      const mark = rootDocument.createElement("div");
      mark.className = "system-dialog-mark";
      mark.setAttribute("aria-hidden", "true");
      mark.textContent = getSystemDialogToneMark(dialogOptions.tone);

      const titleWrap = rootDocument.createElement("div");
      const eyebrow = rootDocument.createElement("span");
      eyebrow.className = "system-dialog-eyebrow";
      eyebrow.textContent = dialogOptions.eyebrow;
      const title = rootDocument.createElement("h2");
      title.id = "systemDialogTitle";
      title.textContent = dialogOptions.title;
      titleWrap.append(eyebrow, title);

      header.append(mark, titleWrap);

      const message = rootDocument.createElement("p");
      message.className = "system-dialog-message";
      message.textContent = dialogOptions.message || "操作已经完成。";

      let input = null;
      let inputHint = null;
      if (dialogOptions.input) {
        input = rootDocument.createElement("input");
        input.className = "system-dialog-input";
        input.type = "text";
        input.value = dialogOptions.input.value;
        input.placeholder = dialogOptions.input.placeholder;
        input.maxLength = dialogOptions.input.maxLength;
        input.autocomplete = "off";
        input.spellcheck = false;
        input.setAttribute("aria-label", dialogOptions.title);

        inputHint = rootDocument.createElement("div");
        inputHint.className = "system-dialog-input-hint";
        inputHint.textContent = dialogOptions.input.requiredMessage;
      }

      const actions = rootDocument.createElement("div");
      actions.className = "system-dialog-actions";

      if (dialogOptions.copyText) {
        const copyButton = rootDocument.createElement("button");
        copyButton.type = "button";
        copyButton.className = "toolbar-button";
        copyButton.textContent = dialogOptions.copyLabel;
        copyButton.addEventListener("click", async () => {
          const copied = await copyTextToClipboard(dialogOptions.copyText);
          showToast(copied ? dialogOptions.copySuccessMessage : "复制失败，请手动选择文本", copied ? "soft" : "error");
        });
        actions.append(copyButton);
      }

      if (dialogOptions.showCancel) {
        const cancelButton = rootDocument.createElement("button");
        cancelButton.type = "button";
        cancelButton.className = "toolbar-button";
        cancelButton.textContent = dialogOptions.cancelLabel;
        cancelButton.addEventListener("click", () => close(dialogOptions.input ? null : false));
        actions.append(cancelButton);
      }

      const confirmButton = rootDocument.createElement("button");
      confirmButton.type = "button";
      confirmButton.className =
        dialogOptions.tone === "danger" ? "toolbar-button toolbar-button-danger" : "toolbar-button toolbar-button-primary";
      confirmButton.textContent = dialogOptions.confirmLabel;
      confirmButton.addEventListener("click", () => {
        if (dialogOptions.input && dialogOptions.input.required && !input.value.trim()) {
          input.focus({ preventScroll: true });
          inputHint.classList.add("is-visible");
          return;
        }
        close(dialogOptions.input ? input.value : true);
      });
      actions.append(confirmButton);

      if (input) {
        const syncInputState = () => {
          const isInvalid = dialogOptions.input.required && !input.value.trim();
          input.classList.toggle("is-invalid", isInvalid);
          inputHint.classList.toggle("is-visible", isInvalid);
          confirmButton.disabled = isInvalid;
        };
        input.addEventListener("input", syncInputState);
        syncInputState();
      }

      dialog.append(halo, header, message);
      if (input) {
        dialog.append(input);
        dialog.append(inputHint);
      }
      dialog.append(actions);
      root.append(dialog);

      root.onclick = dialogOptions.allowBackdropClose ? () => close(dialogOptions.input ? null : false) : null;

      const requestFrame =
        typeof rootWindow.requestAnimationFrame === "function"
          ? rootWindow.requestAnimationFrame.bind(rootWindow)
          : (callback) => rootWindow.setTimeout(callback, 0);
      requestFrame(() => {
        const focusTarget = input ?? confirmButton;
        focusTarget.focus({ preventScroll: true });
        if (input) {
          input.select();
        }
      });
    }

    function closeActive(result = false) {
      activeDialog?.close(result);
    }

    function hasActiveDialog() {
      return Boolean(activeDialog);
    }

    function handleKeydown(event, helpers = {}) {
      if (!activeDialog) {
        return false;
      }

      if (event.code === "Escape") {
        event.preventDefault();
        closeActive(false);
        return true;
      }

      const isTypingTarget =
        typeof helpers.isKeyboardTypingTarget === "function"
          ? helpers.isKeyboardTypingTarget(event.target)
          : false;
      const engineDialogButton =
        rootWindow.Element && event.target instanceof rootWindow.Element
          ? event.target.closest(".system-dialog button")
          : null;
      const engineDialogInput =
        rootWindow.HTMLInputElement &&
        event.target instanceof rootWindow.HTMLInputElement &&
        event.target.classList.contains("system-dialog-input")
          ? event.target
          : null;

      if (event.code === "Enter" && !event.shiftKey && engineDialogInput) {
        event.preventDefault();
        if (activeDialog?.options?.input?.required && !engineDialogInput.value.trim()) {
          engineDialogInput.classList.add("is-invalid");
          engineDialogInput
            .closest(".system-dialog")
            ?.querySelector(".system-dialog-input-hint")
            ?.classList.add("is-visible");
          return true;
        }
        closeActive(engineDialogInput.value);
        return true;
      }

      if (event.code === "Enter" && !event.shiftKey && !engineDialogButton && !isTypingTarget) {
        event.preventDefault();
        closeActive(true);
        return true;
      }

      if (event.code === "Tab" || event.code === "Space") {
        return true;
      }

      if (!isTypingTarget) {
        event.preventDefault();
      }
      return true;
    }

    return Object.freeze({
      showToast,
      installAlertBridge,
      showAlert,
      showConfirm,
      showPrompt,
      showDialog,
      closeActive,
      hasActiveDialog,
      handleKeydown,
    });
  }

  global.CanvasiaEditorSystemDialog = Object.freeze({
    DEFAULT_TOAST_HIDE_MS,
    normalizeSystemDialogOptions,
    inferSystemAlertOptions,
    getSystemDialogToneMark,
    createSystemDialogController,
  });
})(typeof window !== "undefined" ? window : globalThis);
