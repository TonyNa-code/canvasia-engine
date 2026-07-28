(function attachTimedChoiceEditor(global) {
  "use strict";

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function getRuntimeTools(options = {}) {
    return options.runtimeTools ?? global.CanvasiaRuntimeTimedChoices;
  }

  function renderTimedChoiceEditor(block = {}, options = {}) {
    const runtimeTools = getRuntimeTools(options);
    const config = runtimeTools.sanitizeTimedChoiceConfig(block);
    const choiceOptions = Array.isArray(options.choiceOptions) ? options.choiceOptions : [];
    const presetValues = runtimeTools.TIMED_CHOICE_PRESET_SECONDS;
    const usesPreset = presetValues.includes(config.timeoutSeconds);
    const selectValue = !config.enabled ? "0" : usesPreset ? String(config.timeoutSeconds) : "custom";
    return `
      <article class="editor-card timed-choice-editor">
        <div class="editor-card-heading-row">
          <div>
            <h3>限时选择</h3>
            <p>可选功能。倒计时结束后自动走指定分支；打开菜单、历史或切到后台时会暂停。</p>
          </div>
          <span class="detail-meta">${config.enabled ? `已启用 · ${escapeHtml(config.timeoutSeconds)} 秒` : "默认关闭"}</span>
        </div>
        <div class="field-grid">
          <div class="detail-row">
            <label for="editorChoiceTimeoutSeconds">倒计时</label>
            <select id="editorChoiceTimeoutSeconds">
              <option value="0" ${selectValue === "0" ? "selected" : ""}>关闭，不限制思考时间</option>
              ${presetValues.map((seconds) => `<option value="${seconds}" ${selectValue === String(seconds) ? "selected" : ""}>${seconds} 秒</option>`).join("")}
              <option value="custom" ${selectValue === "custom" ? "selected" : ""}>自定义秒数</option>
            </select>
          </div>
          <div class="detail-row">
            <label for="editorChoiceTimeoutCustomSeconds">自定义秒数（1–300）</label>
            <input id="editorChoiceTimeoutCustomSeconds" type="number" min="1" max="300" step="0.1" value="${escapeHtml(config.enabled ? config.timeoutSeconds : 10)}" />
          </div>
          <div class="detail-row">
            <label for="editorChoiceTimeoutOptionId">超时后自动选择</label>
            <select id="editorChoiceTimeoutOptionId">
              <option value="" ${config.timeoutOptionId ? "" : "selected"}>第一个当前可选的分支（推荐）</option>
              ${choiceOptions.map((option, index) => {
                const optionId = String(option?.id ?? "").trim();
                const label = String(option?.text ?? option?.label ?? `选项 ${index + 1}`).trim();
                return `<option value="${escapeHtml(optionId)}" ${config.timeoutOptionId === optionId ? "selected" : ""}>${escapeHtml(label)}</option>`;
              }).join("")}
            </select>
            <p class="helper-text">若指定分支届时被隐藏或锁定，Runtime 会安全回退到第一个可选分支。</p>
          </div>
        </div>
      </article>
    `;
  }

  function readTimedChoiceEditor(block = {}, options = {}) {
    const runtimeTools = getRuntimeTools(options);
    const documentRef = options.document ?? global.document;
    const mode = documentRef?.getElementById("editorChoiceTimeoutSeconds")?.value ?? "0";
    const rawSeconds = mode === "custom"
      ? documentRef?.getElementById("editorChoiceTimeoutCustomSeconds")?.value
      : mode;
    const timeoutSeconds = runtimeTools.getSafeTimedChoiceSeconds(rawSeconds, 0);
    const nextBlock = { ...block };
    if (timeoutSeconds <= 0) {
      delete nextBlock.timeoutSeconds;
      delete nextBlock.timeoutOptionId;
      delete nextBlock.choiceTimeoutSeconds;
      delete nextBlock.choiceTimeoutOptionId;
      return nextBlock;
    }
    nextBlock.timeoutSeconds = timeoutSeconds;
    const timeoutOptionId = String(
      documentRef?.getElementById("editorChoiceTimeoutOptionId")?.value ?? ""
    ).trim();
    if (timeoutOptionId) nextBlock.timeoutOptionId = timeoutOptionId;
    else delete nextBlock.timeoutOptionId;
    delete nextBlock.choiceTimeoutSeconds;
    delete nextBlock.choiceTimeoutOptionId;
    return nextBlock;
  }

  global.CanvasiaEditorTimedChoice = Object.freeze({
    renderTimedChoiceEditor,
    readTimedChoiceEditor,
  });
})(typeof window !== "undefined" ? window : globalThis);
