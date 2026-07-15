(function attachChoiceAvailabilityEditor(global) {
  "use strict";

  const runtimeTools = global.CanvasiaRuntimeChoiceAvailability;
  const MODE_LABELS = runtimeTools?.CHOICE_AVAILABILITY_MODE_LABELS ?? {
    always: "始终可选",
    hide_when_false: "条件不满足时隐藏",
    disable_when_false: "条件不满足时锁定",
  };

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function getRenderer(options, name, fallback = () => "") {
    return typeof options?.[name] === "function" ? options[name] : fallback;
  }

  function normalizeMode(value) {
    return runtimeTools?.normalizeChoiceAvailabilityMode?.(value) ?? (Object.hasOwn(MODE_LABELS, value) ? value : "always");
  }

  function renderChoiceAvailabilityRuleEditorRow(rule = {}, index = 0, ruleCount = 1, options = {}) {
    const getSafeVariableId = getRenderer(options, "getSafeVariableId", (value) => value ?? "");
    const getSafeConditionOperator = getRenderer(options, "getSafeConditionOperator", (_variableId, value) => value ?? "==");
    const renderVariableOptions = getRenderer(options, "renderVariableOptions");
    const renderConditionOperatorOptions = getRenderer(options, "renderConditionOperatorOptions");
    const renderConditionValueFields = getRenderer(options, "renderConditionValueFields");
    const safeIndex = Number.isFinite(Number(index)) ? Number(index) : 0;
    const safeCount = Math.max(Number.isFinite(Number(ruleCount)) ? Number(ruleCount) : 1, 1);
    const variableId = getSafeVariableId(rule.variableId);
    const operator = getSafeConditionOperator(variableId, rule.operator);

    return `
      <div class="choice-availability-rule" data-choice-availability-rule>
        <strong data-choice-availability-rule-title>可用条件 ${safeIndex + 1}</strong>
        <div class="field-grid">
          <div class="detail-row">
            <label>检查哪个变量</label>
            <select data-field="condition-variable">${renderVariableOptions(variableId)}</select>
          </div>
          <div class="detail-row">
            <label>比较方式</label>
            <select data-field="condition-operator">${renderConditionOperatorOptions(variableId, operator)}</select>
          </div>
          <div class="field-grid" data-condition-value-fields>
            ${renderConditionValueFields(variableId, rule.value)}
          </div>
        </div>
        <div class="detail-actions">
          <button class="toolbar-button" data-action="move-choice-availability-rule-up" ${safeIndex <= 0 ? "disabled" : ""}>上移条件</button>
          <button class="toolbar-button" data-action="move-choice-availability-rule-down" ${safeIndex >= safeCount - 1 ? "disabled" : ""}>下移条件</button>
          <button class="toolbar-button" data-action="remove-choice-availability-rule">删除条件</button>
        </div>
      </div>
    `;
  }

  function renderChoiceAvailabilityEditor(option = {}, options = {}) {
    const escape = typeof options.escapeHtml === "function" ? options.escapeHtml : escapeHtml;
    const createDefaultRule = getRenderer(options, "createDefaultConditionRule", () => ({}));
    const renderRule = getRenderer(options, "renderChoiceAvailabilityRuleEditorRow", renderChoiceAvailabilityRuleEditorRow);
    const mode = normalizeMode(option.choiceAvailabilityMode ?? option.availabilityMode);
    const storedRules = runtimeTools?.getChoiceAvailabilityRules?.(option) ?? [];
    const rules = storedRules.length ? storedRules : [createDefaultRule()];
    const lockedReason = runtimeTools?.getChoiceLockedReason?.(option, "条件尚未满足") ?? "条件尚未满足";
    const hasVariables = options.hasVariables !== false;

    return `
      <section class="choice-availability-editor" data-choice-availability>
        <div class="detail-row">
          <label>这个选项什么时候出现</label>
          <select data-field="choice-availability-mode">
            ${Object.entries(MODE_LABELS)
              .map(([value, label]) => `<option value="${escape(value)}" ${value === mode ? "selected" : ""}>${escape(label)}</option>`)
              .join("")}
          </select>
          <p class="helper-text">默认始终可选。高级路线可按好感度、道具、开关或其他变量隐藏或锁定选项。</p>
        </div>
        <div data-choice-availability-conditions ${mode === "always" ? "hidden" : ""}>
          ${
            hasVariables
              ? ""
              : `
                <div class="choice-availability-empty" data-choice-availability-empty>
                  <strong>还没有可用于判断的变量</strong>
                  <span>先创建好感度、道具数量或剧情开关，再回来设置解锁条件。</span>
                  <button type="button" class="toolbar-button" data-action="switch-screen" data-screen="preview">去变量库创建变量</button>
                </div>
              `
          }
          <div class="option-editor-list" data-choice-availability-rules>
            ${rules.map((rule, index) => renderRule(rule, index, rules.length)).join("")}
          </div>
          <div class="detail-actions">
            <button class="toolbar-button" data-action="add-choice-availability-rule">再加一个条件</button>
          </div>
          <p class="helper-text">多条条件需要同时满足。条件隐藏不会占按钮位置；条件锁定会保留按钮并显示原因。</p>
        </div>
        <div class="detail-row" data-choice-locked-reason ${mode === "disable_when_false" ? "" : "hidden"}>
          <label>未满足时告诉玩家什么</label>
          <input type="text" data-field="choice-locked-reason" value="${escape(lockedReason)}" placeholder="例如：好感度达到 5 后解锁" />
        </div>
      </section>
    `;
  }

  function readChoiceAvailabilityEditor(optionEditor, options = {}) {
    const availabilityEditor = optionEditor?.querySelector?.("[data-choice-availability]");
    const mode = normalizeMode(availabilityEditor?.querySelector?.('[data-field="choice-availability-mode"]')?.value);
    const getSafeVariableId = getRenderer(options, "getSafeVariableId", (value) => value ?? "");
    const getSafeConditionOperator = getRenderer(options, "getSafeConditionOperator", (_variableId, value) => value ?? "==");
    const readConditionRuleValue = getRenderer(options, "readConditionRuleValue", () => "");
    const rules = mode === "always"
      ? []
      : Array.from(availabilityEditor?.querySelectorAll?.("[data-choice-availability-rule]") ?? []).map((ruleEditor) => {
          const variableId = getSafeVariableId(ruleEditor.querySelector('[data-field="condition-variable"]')?.value);
          return {
            variableId,
            operator: getSafeConditionOperator(variableId, ruleEditor.querySelector('[data-field="condition-operator"]')?.value),
            value: readConditionRuleValue(ruleEditor, variableId),
          };
        });
    const result = {
      choiceAvailabilityMode: mode,
      choiceAvailabilityWhen: rules,
    };
    if (mode === "disable_when_false") {
      result.choiceLockedReason = String(
        availabilityEditor?.querySelector?.('[data-field="choice-locked-reason"]')?.value ?? ""
      ).trim();
    }
    return result;
  }

  function updateChoiceAvailabilityModePanels(availabilityEditor) {
    if (!availabilityEditor) {
      return "always";
    }
    const mode = normalizeMode(availabilityEditor.querySelector('[data-field="choice-availability-mode"]')?.value);
    const conditions = availabilityEditor.querySelector("[data-choice-availability-conditions]");
    const lockedReason = availabilityEditor.querySelector("[data-choice-locked-reason]");
    if (conditions) {
      conditions.hidden = mode === "always";
    }
    if (lockedReason) {
      lockedReason.hidden = mode !== "disable_when_false";
    }
    return mode;
  }

  function updateChoiceAvailabilityRuleControls(container) {
    const rules = Array.from(container?.querySelectorAll?.("[data-choice-availability-rule]") ?? []);
    rules.forEach((rule, index) => {
      const title = rule.querySelector("[data-choice-availability-rule-title]");
      const up = rule.querySelector('[data-action="move-choice-availability-rule-up"]');
      const down = rule.querySelector('[data-action="move-choice-availability-rule-down"]');
      if (title) title.textContent = `可用条件 ${index + 1}`;
      if (up) up.disabled = index === 0;
      if (down) down.disabled = index === rules.length - 1;
    });
    return rules.length;
  }

  function appendChoiceAvailabilityRule(optionEditor, options = {}) {
    const container = optionEditor?.querySelector?.("[data-choice-availability-rules]");
    if (!container) return false;
    const createDefaultRule = getRenderer(options, "createDefaultConditionRule", () => ({}));
    const renderRule = getRenderer(options, "renderChoiceAvailabilityRuleEditorRow", renderChoiceAvailabilityRuleEditorRow);
    const index = container.querySelectorAll("[data-choice-availability-rule]").length;
    container.insertAdjacentHTML("beforeend", renderRule(createDefaultRule(), index, index + 1));
    updateChoiceAvailabilityRuleControls(container);
    return true;
  }

  function removeChoiceAvailabilityRule(actionTarget) {
    const rule = actionTarget?.closest?.("[data-choice-availability-rule]");
    const container = rule?.parentElement;
    if (!rule || !container || container.querySelectorAll("[data-choice-availability-rule]").length <= 1) return false;
    rule.remove();
    updateChoiceAvailabilityRuleControls(container);
    return true;
  }

  function moveChoiceAvailabilityRule(actionTarget, direction) {
    const rule = actionTarget?.closest?.("[data-choice-availability-rule]");
    const container = rule?.parentElement;
    if (!rule || !container) return false;
    const rules = Array.from(container.querySelectorAll("[data-choice-availability-rule]"));
    const currentIndex = rules.indexOf(rule);
    const targetIndex = currentIndex + (Number(direction) < 0 ? -1 : 1);
    if (currentIndex < 0 || targetIndex < 0 || targetIndex >= rules.length) return false;
    if (targetIndex < currentIndex) container.insertBefore(rule, rules[targetIndex]);
    else container.insertBefore(rules[targetIndex], rule);
    updateChoiceAvailabilityRuleControls(container);
    return true;
  }

  global.CanvasiaEditorChoiceAvailability = Object.freeze({
    MODE_LABELS,
    normalizeMode,
    renderChoiceAvailabilityRuleEditorRow,
    renderChoiceAvailabilityEditor,
    readChoiceAvailabilityEditor,
    updateChoiceAvailabilityModePanels,
    updateChoiceAvailabilityRuleControls,
    appendChoiceAvailabilityRule,
    removeChoiceAvailabilityRule,
    moveChoiceAvailabilityRule,
  });
})(typeof window !== "undefined" ? window : globalThis);
