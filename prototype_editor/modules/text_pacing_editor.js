(function attachTextPacingEditor(global) {
  "use strict";

  const ACTIONS = Object.freeze({
    "pause-short": Object.freeze({ marker: "[[pause=0.35]]", label: "已加入 0.35 秒停顿", mode: "insert" }),
    "pause-long": Object.freeze({ marker: "[[pause=0.8]]", label: "已加入 0.8 秒停顿", mode: "insert" }),
    "speed-slow": Object.freeze({ marker: "[[speed=slow]]", label: "已加入慢速表达", mode: "wrap" }),
    "speed-fast": Object.freeze({ marker: "[[speed=fast]]", label: "已加入快速表达", mode: "wrap" }),
    "speed-instant": Object.freeze({ marker: "[[speed=instant]]", label: "已加入瞬间显示", mode: "wrap" }),
    "speed-reset": Object.freeze({ marker: "[[speed=inherit]]", label: "已恢复默认语速", mode: "insert" }),
  });

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function getRuntimeTools(options = {}) {
    return options.runtimeTools ?? global.CanvasiaRuntimeTextPacing;
  }

  function renderTextPacingEditor(textareaId, text = "", options = {}) {
    const summary = getRuntimeTools(options).buildTextPacingSummary(text);
    const safeTextareaId = escapeHtml(textareaId);
    const button = (label, action, title) => `
      <button
        type="button"
        class="toolbar-button"
        data-action="insert-text-pacing"
        data-text-pacing-action="${action}"
        data-textarea-id="${safeTextareaId}"
        title="${escapeHtml(title)}"
      >${escapeHtml(label)}</button>
    `;

    return `
      <article class="editor-card text-pacing-editor" data-text-pacing-editor data-textarea-id="${safeTextareaId}">
        <div class="editor-card-heading-row">
          <div>
            <h3>句内节奏</h3>
            <p>把光标放到停顿位置，或先选中想变速的一段文字，再点下面的按钮。试玩和导出时不会显示控制标记。</p>
          </div>
          <span class="detail-meta" data-text-pacing-summary>${escapeHtml(summary.label)}</span>
        </div>
        <div class="detail-actions text-pacing-actions">
          ${button("稍停一下", "pause-short", "在光标处停顿 0.35 秒")}
          ${button("停久一点", "pause-long", "在光标处停顿 0.8 秒")}
          ${button("这段慢慢说", "speed-slow", "让选中文字慢速显示")}
          ${button("这段快速说", "speed-fast", "让选中文字快速显示")}
          ${button("瞬间亮出", "speed-instant", "让选中文字立即显示")}
          ${button("恢复默认语速", "speed-reset", "从光标处恢复项目或卡片语速")}
        </div>
        <p class="helper-text">玩家选择“瞬间显示”时会优先尊重玩家设置，句内停顿和变速不会强迫等待。</p>
      </article>
    `;
  }

  function replaceSelection(textarea, replacement, selectionStart, selectionEnd) {
    const source = String(textarea.value ?? "");
    textarea.value = `${source.slice(0, selectionStart)}${replacement}${source.slice(selectionEnd)}`;
  }

  function updateSummary(textarea, options = {}) {
    const card = textarea.closest?.(".detail-row")?.querySelector?.("[data-text-pacing-editor]")
      ?? textarea.parentElement?.querySelector?.("[data-text-pacing-editor]");
    const summaryNode = card?.querySelector?.("[data-text-pacing-summary]");
    if (summaryNode) {
      summaryNode.textContent = getRuntimeTools(options).buildTextPacingSummary(textarea.value).label;
    }
  }

  function applyTextPacingAction(actionTarget, options = {}) {
    const documentRef = options.document ?? global.document;
    const textareaId = String(actionTarget?.dataset?.textareaId ?? "").trim();
    const actionId = String(actionTarget?.dataset?.textPacingAction ?? "").trim();
    const config = ACTIONS[actionId];
    const textarea = textareaId ? documentRef?.getElementById?.(textareaId) : null;
    if (!config || !textarea || textarea.tagName?.toLowerCase() !== "textarea") {
      return Object.freeze({ ok: false, label: "没有找到可编辑的正文输入框。" });
    }

    const selectionStart = Math.max(0, Number(textarea.selectionStart) || 0);
    const selectionEnd = Math.max(selectionStart, Number(textarea.selectionEnd) || selectionStart);
    const selectedText = String(textarea.value ?? "").slice(selectionStart, selectionEnd);

    if (config.mode === "wrap" && !selectedText) {
      textarea.focus();
      return Object.freeze({
        ok: false,
        label: "请先选中想变速的文字，再点击语速按钮。",
        actionId,
        textareaId,
      });
    }

    if (config.mode === "wrap") {
      const resetMarker = "[[speed=inherit]]";
      replaceSelection(textarea, `${config.marker}${selectedText}${resetMarker}`, selectionStart, selectionEnd);
      const contentStart = selectionStart + config.marker.length;
      const contentEnd = contentStart + selectedText.length;
      textarea.setSelectionRange(contentStart, contentEnd || contentStart);
    } else {
      replaceSelection(textarea, config.marker, selectionStart, selectionEnd);
      const caret = selectionStart + config.marker.length;
      textarea.setSelectionRange(caret, caret);
    }

    textarea.focus();
    textarea.dispatchEvent(new Event("input", { bubbles: true }));
    updateSummary(textarea, options);
    return Object.freeze({ ok: true, label: config.label, actionId, textareaId });
  }

  global.CanvasiaEditorTextPacing = Object.freeze({
    ACTIONS,
    renderTextPacingEditor,
    applyTextPacingAction,
  });
})(typeof window !== "undefined" ? window : globalThis);
