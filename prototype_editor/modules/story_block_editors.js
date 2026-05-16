(function attachStoryBlockEditorTools(global) {
  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function getEscapeHtml(options = {}) {
    return typeof options.escapeHtml === "function" ? options.escapeHtml : escapeHtml;
  }

  function getRenderer(options, key, fallback = () => "") {
    return typeof options[key] === "function" ? options[key] : fallback;
  }

  function getEditableChoiceEffects(effectList, options = {}) {
    const reader = getRenderer(options, "getEditableChoiceEffects", (effects = []) => effects ?? []);
    const result = reader(effectList ?? []);
    return Array.isArray(result) ? result : [];
  }

  function renderJumpEditor(block, options = {}) {
    const getSafeSceneId = getRenderer(options, "getSafeSceneId", (sceneId) => sceneId ?? "");
    const renderSceneOptions = getRenderer(options, "renderSceneOptions");
    const targetSceneId = getSafeSceneId(block?.targetSceneId);

    return `
    <article class="editor-card">
      <h3>编辑场景跳转</h3>
      <p>这里决定这张卡片执行完以后，直接跳到哪个场景。</p>
    </article>
    <div class="field-grid">
      <div class="detail-row">
        <label for="editorJumpTargetSceneId">跳到哪个场景</label>
        <select id="editorJumpTargetSceneId">
          ${renderSceneOptions(targetSceneId)}
        </select>
      </div>
    </div>
    <div class="detail-actions">
      <button class="toolbar-button toolbar-button-primary" data-action="save-block">保存这张卡片</button>
    </div>
  `;
  }

  function renderVariableStarterPrompt(title, description, options = {}) {
    const escape = getEscapeHtml(options);

    return `
    <article class="editor-card">
      <h3>${escape(title)}</h3>
      <p>${escape(description)}</p>
      <div class="detail-actions">
        <button class="toolbar-button toolbar-button-primary" data-action="create-starter-variables">
          一键创建基础变量库
        </button>
      </div>
    </article>
    <article class="editor-card">
      <h3>会创建什么</h3>
      <p>基础变量库会加入“好感度”（数字）、“路线标记”（文本）和“剧情开关”（是/否），足够支撑常见分支、数值变化和条件判断。</p>
    </article>
  `;
  }

  function renderVariableSetEditor(block, options = {}) {
    const escape = getEscapeHtml(options);
    const getSafeVariableId = getRenderer(options, "getSafeVariableId", (variableId) => variableId ?? "");
    const getVariableType = getRenderer(options, "getVariableType", () => "string");
    const getVariableTypeLabel = getRenderer(options, "getVariableTypeLabel", (type) => type ?? "");
    const renderVariableOptions = getRenderer(options, "renderVariableOptions");
    const renderVariableSetValueFields = getRenderer(options, "renderVariableSetValueFields");
    const variableId = getSafeVariableId(block?.variableId);

    return `
    <article class="editor-card">
      <h3>编辑变量设置</h3>
      <p>这里会把某个变量直接改成指定值，适合开关、路线名或固定状态。</p>
    </article>
    <div class="field-grid">
      <div class="detail-row">
        <label for="editorVariableId">要设置哪个变量</label>
        <select id="editorVariableId">
          ${renderVariableOptions(variableId)}
        </select>
      </div>
      <div class="detail-row">
        <label>变量类型</label>
        <div id="editorVariableTypeValue" class="value">${escape(
          getVariableTypeLabel(getVariableType(variableId))
        )}</div>
      </div>
      <div id="editorVariableValueFields" class="field-grid">
        ${renderVariableSetValueFields(variableId, block?.value)}
      </div>
    </div>
    <div class="detail-actions">
      <button class="toolbar-button toolbar-button-primary" data-action="save-block">保存这张卡片</button>
    </div>
  `;
  }

  function renderVariableAddEditor(block, options = {}) {
    const escape = getEscapeHtml(options);
    const getSafeVariableId = getRenderer(options, "getSafeVariableId", (variableId) => variableId ?? "");
    const getSafeNumber = getRenderer(options, "getSafeNumber", (value, fallback = 0) => {
      const parsed = Number.parseFloat(value ?? "");
      return Number.isFinite(parsed) ? parsed : fallback;
    });
    const renderVariableOptions = getRenderer(options, "renderVariableOptions");
    const variableId = getSafeVariableId(block?.variableId, "number");

    return `
    <article class="editor-card">
      <h3>编辑数字变量变化</h3>
      <p>这里会给数字变量加减数值，最适合好感度、分数和进度条。</p>
    </article>
    <div class="field-grid">
      <div class="detail-row">
        <label for="editorVariableAddId">要修改哪个数字变量</label>
        <select id="editorVariableAddId">
          ${renderVariableOptions(variableId, "number")}
        </select>
      </div>
      <div class="detail-row">
        <label for="editorVariableAddValue">变化值</label>
        <input
          id="editorVariableAddValue"
          type="number"
          step="1"
          value="${escape(String(getSafeNumber(block?.value, 1)))}"
        />
      </div>
      <div class="helper-text">正数表示增加，负数表示减少。这里只会列出数字类型的变量。</div>
    </div>
    <div class="detail-actions">
      <button class="toolbar-button toolbar-button-primary" data-action="save-block">保存这张卡片</button>
    </div>
  `;
  }

  function renderChoiceEffectEditorRow(effect, index, effectCount = 1, options = {}) {
    const normalizeChoiceEffect = getRenderer(options, "normalizeChoiceEffect", (value) => value ?? {});
    const renderChoiceEffectTypeOptions = getRenderer(options, "renderChoiceEffectTypeOptions");
    const renderVariableOptions = getRenderer(options, "renderVariableOptions");
    const renderChoiceEffectValueFields = getRenderer(options, "renderChoiceEffectValueFields");
    const safeEffect = normalizeChoiceEffect(effect);
    const safeIndex = Number.isFinite(Number(index)) ? Number(index) : 0;
    const safeEffectCount = Math.max(Number.isFinite(Number(effectCount)) ? Number(effectCount) : 1, 1);
    const variableFilter = safeEffect.type === "variable_add" ? "number" : null;

    return `
    <div class="effect-editor" data-choice-effect>
      <strong data-choice-effect-title>附加效果 ${safeIndex + 1}</strong>
      <div class="field-grid">
        <div class="detail-row">
          <label>效果类型</label>
          <select data-field="choice-effect-type">
            ${renderChoiceEffectTypeOptions(safeEffect.type)}
          </select>
        </div>
        <div class="detail-row">
          <label>作用到哪个变量</label>
          <select data-field="choice-effect-variable">
            ${renderVariableOptions(safeEffect.variableId, variableFilter)}
          </select>
        </div>
        <div class="field-grid" data-choice-effect-value-fields>
          ${renderChoiceEffectValueFields(safeEffect.type, safeEffect.variableId, safeEffect.value)}
        </div>
      </div>
      <div class="detail-actions">
        <button class="toolbar-button" data-action="move-choice-effect-up" ${safeIndex <= 0 ? "disabled" : ""}>上移效果</button>
        <button class="toolbar-button" data-action="move-choice-effect-down" ${safeIndex >= safeEffectCount - 1 ? "disabled" : ""}>下移效果</button>
        <button class="toolbar-button" data-action="remove-choice-effect">删除这条效果</button>
      </div>
    </div>
  `;
  }

  function renderChoiceEffectEmptyState() {
    return `<div class="helper-text" data-choice-effects-empty>这个选项暂时没有附加效果。需要的话，点下面按钮就能继续加。</div>`;
  }

  function renderConditionRuleEditorRow(rule, index, ruleCount = 1, options = {}) {
    const getSafeVariableId = getRenderer(options, "getSafeVariableId", (variableId) => variableId ?? "");
    const getSafeConditionOperator = getRenderer(options, "getSafeConditionOperator", (_variableId, operator) => operator ?? "==");
    const renderVariableOptions = getRenderer(options, "renderVariableOptions");
    const renderConditionOperatorOptions = getRenderer(options, "renderConditionOperatorOptions");
    const renderConditionValueFields = getRenderer(options, "renderConditionValueFields");
    const safeRule = rule ?? {};
    const safeIndex = Number.isFinite(Number(index)) ? Number(index) : 0;
    const safeRuleCount = Math.max(Number.isFinite(Number(ruleCount)) ? Number(ruleCount) : 1, 1);
    const variableId = getSafeVariableId(safeRule.variableId);
    const operator = getSafeConditionOperator(variableId, safeRule.operator);

    return `
    <div class="option-editor" data-condition-rule>
      <strong data-condition-rule-title>判断 ${safeIndex + 1}</strong>
      <div class="field-grid">
        <div class="detail-row">
          <label>检查哪个变量</label>
          <select data-field="condition-variable">
            ${renderVariableOptions(variableId)}
          </select>
        </div>
        <div class="detail-row">
          <label>比较方式</label>
          <select data-field="condition-operator">
            ${renderConditionOperatorOptions(variableId, operator)}
          </select>
        </div>
        <div class="field-grid" data-condition-value-fields>
          ${renderConditionValueFields(variableId, safeRule.value)}
        </div>
      </div>
      <div class="detail-actions">
        <button class="toolbar-button" data-action="move-condition-rule-up" ${safeIndex <= 0 ? "disabled" : ""}>上移判断</button>
        <button class="toolbar-button" data-action="move-condition-rule-down" ${safeIndex >= safeRuleCount - 1 ? "disabled" : ""}>下移判断</button>
        <button class="toolbar-button" data-action="remove-condition-rule">删除这个判断</button>
      </div>
    </div>
  `;
  }

  function renderConditionBranchEditorRow(branch, index, branchCount = 1, options = {}) {
    const escape = getEscapeHtml(options);
    const createConditionBranchId = getRenderer(
      options,
      "createConditionBranchId",
      (_blockId, branchIndex) => `condition_branch_${Number(branchIndex) + 1}`
    );
    const createDefaultConditionRule = getRenderer(options, "createDefaultConditionRule", () => ({}));
    const getSafeSceneId = getRenderer(options, "getSafeSceneId", (sceneId) => sceneId ?? "");
    const getDefaultJumpTargetSceneId = getRenderer(options, "getDefaultJumpTargetSceneId", () => "");
    const renderSceneOptions = getRenderer(options, "renderSceneOptions");
    const renderRuleRow = getRenderer(options, "renderConditionRuleEditorRow", renderConditionRuleEditorRow);
    const safeBranch = branch ?? {};
    const safeIndex = Number.isFinite(Number(index)) ? Number(index) : 0;
    const safeBranchCount = Math.max(Number.isFinite(Number(branchCount)) ? Number(branchCount) : 1, 1);
    const branchId = String(safeBranch.id ?? createConditionBranchId("condition", safeIndex));
    const rules = Array.isArray(safeBranch.when) && safeBranch.when.length > 0
      ? safeBranch.when
      : [createDefaultConditionRule()];
    const gotoSceneId = getSafeSceneId(
      safeBranch.gotoSceneId,
      getDefaultJumpTargetSceneId(options.selectedSceneId)
    );

    return `
    <div class="option-editor" data-condition-branch data-branch-id="${escape(branchId)}">
      <strong data-condition-branch-title>条件分支 ${safeIndex + 1}</strong>
      <div class="field-grid">
        <div class="detail-row">
          <label>满足这条分支后跳到哪里</label>
          <select data-field="condition-goto">
            ${renderSceneOptions(gotoSceneId)}
          </select>
        </div>
      </div>
      <div class="option-editor-list" data-condition-rules>
        ${rules.map((item, ruleIndex) => renderRuleRow(item, ruleIndex, rules.length)).join("")}
      </div>
      <div class="detail-actions">
        <button class="toolbar-button" data-action="move-condition-branch-up" ${safeIndex <= 0 ? "disabled" : ""}>上移分支</button>
        <button class="toolbar-button" data-action="move-condition-branch-down" ${safeIndex >= safeBranchCount - 1 ? "disabled" : ""}>下移分支</button>
        <button class="toolbar-button" data-action="add-condition-rule" data-branch-id="${escape(branchId)}">再加一个判断</button>
        <button class="toolbar-button" data-action="remove-condition-branch" data-branch-id="${escape(branchId)}">删除这条分支</button>
      </div>
    </div>
  `;
  }

  function renderChoiceOptionEditorRow(option, index, optionCount = 1, options = {}) {
    const escape = getEscapeHtml(options);
    const safeOption = option ?? {};
    const scenes = Array.isArray(options.scenes) ? options.scenes : [];
    const renderChoiceTextQualityTools = getRenderer(options, "renderChoiceTextQualityTools");
    const renderEffectRow = getRenderer(options, "renderChoiceEffectEditorRow", renderChoiceEffectEditorRow);
    const renderEmptyState = getRenderer(options, "renderChoiceEffectEmptyState", renderChoiceEffectEmptyState);
    const editableEffects = getEditableChoiceEffects(safeOption.effects, options);
    const effectCount = Array.isArray(safeOption.effects) ? safeOption.effects.length : 0;
    const unsupportedEffectCount = Math.max(effectCount - editableEffects.length, 0);
    const safeIndex = Number.isFinite(Number(index)) ? Number(index) : 0;
    const safeOptionCount = Math.max(Number.isFinite(Number(optionCount)) ? Number(optionCount) : 1, 1);
    const optionId = String(safeOption.id ?? "");

    return `
    <div class="option-editor" data-choice-option data-option-id="${escape(optionId)}">
      <strong data-choice-option-title>选项 ${safeIndex + 1}</strong>
      <div class="field-grid">
        <div class="detail-row">
          <label>选项文案</label>
          <input
            type="text"
            data-field="choice-text"
            value="${escape(safeOption.text ?? "")}"
            placeholder="例如：一起回家吧"
          />
          ${renderChoiceTextQualityTools(safeOption.text)}
        </div>
        <div class="detail-row">
          <label>跳转到哪个场景</label>
          <select data-field="choice-goto">
            ${scenes
              .map(
                (scene) => `
                  <option value="${escape(scene.id ?? "")}" ${scene.id === safeOption.gotoSceneId ? "selected" : ""}>
                    ${escape(scene.name ?? "")}
                  </option>
                `
              )
              .join("")}
          </select>
        </div>
        <div class="detail-row">
          <label>这个选项触发时还要做什么</label>
          <div class="value">当前共有 ${effectCount} 条附加效果</div>
        </div>
        <div class="effect-editor-list" data-choice-effects>
          ${
            editableEffects.length > 0
              ? editableEffects
                  .map((effect, effectIndex) => renderEffectRow(effect, effectIndex, editableEffects.length))
                  .join("")
              : renderEmptyState()
          }
        </div>
        ${
          unsupportedEffectCount > 0
            ? `<div class="helper-text">这个选项里还有 ${unsupportedEffectCount} 条暂时不支持可视化编辑的旧效果，保存时会继续保留。</div>`
            : ""
        }
        <div class="detail-actions">
          <button
            class="toolbar-button"
            data-action="move-choice-option-up"
            data-option-id="${escape(optionId)}"
            ${safeIndex <= 0 ? "disabled" : ""}
          >
            上移选项
          </button>
          <button
            class="toolbar-button"
            data-action="move-choice-option-down"
            data-option-id="${escape(optionId)}"
            ${safeIndex >= safeOptionCount - 1 ? "disabled" : ""}
          >
            下移选项
          </button>
          <button class="toolbar-button" data-action="add-choice-effect" data-option-id="${escape(optionId)}">给这个选项加效果</button>
          <button class="toolbar-button" data-action="remove-choice-option" data-option-id="${escape(optionId)}">删除这个选项</button>
        </div>
      </div>
    </div>
  `;
  }

  global.CanvasiaEditorStoryBlockEditors = Object.freeze({
    renderJumpEditor,
    renderVariableStarterPrompt,
    renderVariableSetEditor,
    renderVariableAddEditor,
    renderConditionBranchEditorRow,
    renderConditionRuleEditorRow,
    renderChoiceEffectEditorRow,
    renderChoiceEffectEmptyState,
    renderChoiceOptionEditorRow,
  });
})(typeof window !== "undefined" ? window : globalThis);
