(function attachRichTextEditor(global) {
  "use strict";

  const WRAP_ACTIONS = Object.freeze({
    emphasis: Object.freeze({ command: "em", label: "已把选中文字设为强调" }),
    whisper: Object.freeze({ command: "whisper", label: "已把选中文字设为低声表达" }),
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
    return options.runtimeTools ?? global.CanvasiaRuntimeRichText;
  }

  function renderRichTextEditor(textareaId, text = "", options = {}) {
    const summary = getRuntimeTools(options).buildRuntimeRichTextSummary(text);
    const safeTextareaId = escapeHtml(textareaId);
    const readingId = `${safeTextareaId}RubyReading`;
    const colorId = `${safeTextareaId}RichColor`;
    const button = (label, action, title) => `
      <button
        type="button"
        class="toolbar-button"
        data-action="insert-rich-text"
        data-rich-text-action="${action}"
        data-textarea-id="${safeTextareaId}"
        title="${escapeHtml(title)}"
      >${escapeHtml(label)}</button>
    `;

    return `
      <details class="editor-card rich-text-editor" data-rich-text-editor data-textarea-id="${safeTextareaId}">
        <summary>
          <span>
            <strong>文字表现</strong>
            <small>强调、低声、颜色与汉字注音</small>
          </span>
          <span class="detail-meta" data-rich-text-summary>${escapeHtml(summary.label)}</span>
        </summary>
        <div class="rich-text-editor-body">
          <p>先选中正文，再选择表现方式。标记只在编辑器里可见，试玩、历史记录和成品只显示排版后的文字。</p>
          <div class="detail-actions rich-text-actions">
            ${button("强调这段", "emphasis", "让选中文字更醒目")}
            ${button("低声说", "whisper", "让选中文字以更轻、更克制的方式显示")}
            ${button("应用颜色", "color", "把下方颜色应用到选中文字")}
            ${button("加入注音", "ruby", "为选中的汉字或日文加入振假名")}
            ${button("移除所选表现", "clear", "清除选中范围里的文字表现标记")}
          </div>
          <div class="rich-text-inline-fields">
            <label for="${colorId}">
              <span>强调色</span>
              <input id="${colorId}" type="color" value="#ff6b9e" data-rich-text-color />
            </label>
            <label for="${readingId}">
              <span>注音 / 振假名</span>
              <input id="${readingId}" type="text" maxlength="48" placeholder="例如：かんじ / han zi" data-rich-text-reading />
            </label>
          </div>
          <p class="helper-text">颜色只接受安全色值；格式写错时会保留原文，不会静默吞掉台词。</p>
        </div>
      </details>
    `;
  }

  function getEditorCard(textarea) {
    return textarea.closest?.(".detail-row")?.querySelector?.("[data-rich-text-editor]")
      ?? textarea.parentElement?.querySelector?.("[data-rich-text-editor]");
  }

  function replaceSelection(textarea, replacement, selectionStart, selectionEnd) {
    const source = String(textarea.value ?? "");
    textarea.value = `${source.slice(0, selectionStart)}${replacement}${source.slice(selectionEnd)}`;
  }

  function updateSummary(textarea, options = {}) {
    const summaryNode = getEditorCard(textarea)?.querySelector?.("[data-rich-text-summary]");
    if (summaryNode) {
      summaryNode.textContent = getRuntimeTools(options).buildRuntimeRichTextSummary(textarea.value).label;
    }
  }

  function buildMarker(actionId, selectedText, card) {
    if (WRAP_ACTIONS[actionId]) {
      return `[[${WRAP_ACTIONS[actionId].command}=${selectedText}]]`;
    }
    if (actionId === "color") {
      const color = String(card?.querySelector?.("[data-rich-text-color]")?.value ?? "").trim();
      if (!/^#[0-9a-f]{6}$/i.test(color)) return "";
      return `[[color=${color}|${selectedText}]]`;
    }
    if (actionId === "ruby") {
      const reading = String(card?.querySelector?.("[data-rich-text-reading]")?.value ?? "").trim();
      if (!reading || reading.includes("[[") || reading.includes("]]")) return "";
      return `[[ruby=${selectedText}|${reading}]]`;
    }
    return "";
  }

  function applyRichTextAction(actionTarget, options = {}) {
    const documentRef = options.document ?? global.document;
    const textareaId = String(actionTarget?.dataset?.textareaId ?? "").trim();
    const actionId = String(actionTarget?.dataset?.richTextAction ?? "").trim();
    const textarea = textareaId ? documentRef?.getElementById?.(textareaId) : null;
    if (!textarea || textarea.tagName?.toLowerCase() !== "textarea") {
      return Object.freeze({ ok: false, label: "没有找到可编辑的正文输入框。" });
    }

    const selectionStart = Math.max(0, Number(textarea.selectionStart) || 0);
    const selectionEnd = Math.max(selectionStart, Number(textarea.selectionEnd) || selectionStart);
    const selectedText = String(textarea.value ?? "").slice(selectionStart, selectionEnd);
    if (!selectedText) {
      textarea.focus();
      return Object.freeze({ ok: false, label: "请先选中想调整表现的文字。" });
    }

    if (actionId === "clear") {
      const replacement = getRuntimeTools(options).stripRuntimeRichText(selectedText);
      replaceSelection(textarea, replacement, selectionStart, selectionEnd);
      textarea.setSelectionRange(selectionStart, selectionStart + replacement.length);
      textarea.focus();
      textarea.dispatchEvent(new Event("input", { bubbles: true }));
      updateSummary(textarea, options);
      return Object.freeze({ ok: true, label: "已移除选中范围里的文字表现" });
    }

    if (selectedText.includes("[[") || selectedText.includes("]]")) {
      textarea.focus();
      return Object.freeze({ ok: false, label: "请不要跨着已有标记重复套用，先移除旧表现或重新选择正文。" });
    }
    const card = getEditorCard(textarea);
    const marker = buildMarker(actionId, selectedText, card);
    if (!marker) {
      const label = actionId === "ruby" ? "请先填写注音或振假名。" : "当前颜色格式不可用。";
      textarea.focus();
      return Object.freeze({ ok: false, label });
    }

    replaceSelection(textarea, marker, selectionStart, selectionEnd);
    const contentOffset = marker.indexOf(selectedText);
    textarea.setSelectionRange(selectionStart + contentOffset, selectionStart + contentOffset + selectedText.length);
    textarea.focus();
    textarea.dispatchEvent(new Event("input", { bubbles: true }));
    updateSummary(textarea, options);
    return Object.freeze({
      ok: true,
      label: WRAP_ACTIONS[actionId]?.label
        ?? (actionId === "ruby" ? "已加入注音" : "已应用文字颜色"),
    });
  }

  global.CanvasiaEditorRichText = Object.freeze({
    WRAP_ACTIONS,
    renderRichTextEditor,
    applyRichTextAction,
  });
})(typeof window !== "undefined" ? window : globalThis);
