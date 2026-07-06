(function attachVariableTools(global) {
  const STARTER_VARIABLE_PRESETS = Object.freeze([
    Object.freeze({
      id: "var_affection",
      name: "好感度",
      type: "number",
      defaultValue: 0,
      min: -100,
      max: 100,
    }),
    Object.freeze({
      id: "var_route",
      name: "路线标记",
      type: "string",
      defaultValue: "common",
    }),
    Object.freeze({
      id: "var_flag",
      name: "剧情开关",
      type: "boolean",
      defaultValue: false,
    }),
  ]);

  function cloneValue(value) {
    return JSON.parse(JSON.stringify(value));
  }

  function getSafeNumber(value, fallback = 0) {
    const parsed = Number.parseFloat(value ?? "");
    return Number.isFinite(parsed) ? parsed : fallback;
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function getEscaper(options = {}) {
    return typeof options.escapeHtml === "function" ? options.escapeHtml : escapeHtml;
  }

  function hasCollectionValue(collection, key) {
    if (!key || !collection) {
      return false;
    }
    if (typeof collection.has === "function") {
      return collection.has(key);
    }
    return Object.prototype.hasOwnProperty.call(collection, key);
  }

  function getCollectionValue(collection, key) {
    if (!key || !collection) {
      return null;
    }
    if (typeof collection.get === "function") {
      return collection.get(key) ?? null;
    }
    return Object.prototype.hasOwnProperty.call(collection, key) ? collection[key] : null;
  }

  function getVariableList(options = {}) {
    return Array.isArray(options.variables) ? options.variables : [];
  }

  function getVariableById(variableOrId, options = {}) {
    if (variableOrId && typeof variableOrId === "object") {
      return variableOrId;
    }
    const variableId = String(variableOrId ?? "");
    return (
      getCollectionValue(options.variablesById, variableId) ??
      getVariableList(options).find((variable) => variable?.id === variableId) ??
      null
    );
  }

  function parseVariableNumberBound(value) {
    if (value === null || value === undefined || typeof value === "boolean") {
      return null;
    }

    const parsed = Number.parseFloat(value);
    return Number.isFinite(parsed) ? parsed : null;
  }

  function getVariableNumberBounds(variableOrId, options = {}) {
    const variable = getVariableById(variableOrId, options);

    if (!variable) {
      return [null, null];
    }

    return [
      parseVariableNumberBound(variable.min ?? variable.minValue),
      parseVariableNumberBound(variable.max ?? variable.maxValue),
    ];
  }

  function clampVariableNumber(variableOrId, value, options = {}) {
    const [minValue, maxValue] = getVariableNumberBounds(variableOrId, options);
    let nextValue = value;

    if (minValue !== null) {
      nextValue = Math.max(nextValue, minValue);
    }

    if (maxValue !== null) {
      nextValue = Math.min(nextValue, maxValue);
    }

    return nextValue;
  }

  function getFilteredVariables(typeFilter = null, options = {}) {
    return getVariableList(options).filter((variable) => !typeFilter || variable.type === typeFilter);
  }

  function hasUsableVariable(typeFilter = null, options = {}) {
    return getFilteredVariables(typeFilter, options).length > 0;
  }

  function createStarterVariableCopy(preset, existingIds = new Set()) {
    const nextVariable = cloneValue(preset);
    const baseId = nextVariable.id;
    let candidateId = baseId;
    let suffix = 2;

    while (existingIds.has(candidateId)) {
      candidateId = `${baseId}_${String(suffix).padStart(2, "0")}`;
      suffix += 1;
    }

    nextVariable.id = candidateId;
    existingIds.add(candidateId);
    return nextVariable;
  }

  function buildStarterVariableLibrary(existingVariables = [], options = {}) {
    const existing = Array.isArray(existingVariables)
      ? existingVariables.map((variable) => cloneValue(variable))
      : [];
    const existingIds = new Set(existing.map((variable) => variable.id).filter(Boolean));
    const shouldAddAll = Boolean(options.forceStarterPack) || existing.length === 0;
    const presets = Array.isArray(options.presets) ? options.presets : STARTER_VARIABLE_PRESETS;
    const nextVariables = [...existing];

    presets.forEach((preset) => {
      const alreadyHasPreset = nextVariables.some(
        (variable) => variable.id === preset.id && variable.type === preset.type
      );
      const alreadyHasType = nextVariables.some((variable) => variable.type === preset.type);
      const shouldAdd =
        shouldAddAll ||
        (options.requireNumber && preset.type === "number" && !alreadyHasType);

      if (shouldAdd && !alreadyHasPreset) {
        nextVariables.push(createStarterVariableCopy(preset, existingIds));
      }
    });

    return nextVariables;
  }

  function getSafeVariableId(variableId, typeFilter = null, options = {}) {
    const variables = getFilteredVariables(typeFilter, options);

    if (variables.some((variable) => variable.id === variableId)) {
      return variableId;
    }

    if (!typeFilter && hasCollectionValue(options.variablesById, variableId)) {
      return variableId;
    }

    return variables[0]?.id ?? (!typeFilter ? getVariableList(options)[0]?.id ?? "" : "");
  }

  function getVariableType(variableId, options = {}) {
    return getVariableById(variableId, options)?.type ?? "string";
  }

  function getVariableTypeLabel(type) {
    if (type === "number") return "数字";
    if (type === "boolean") return "开关";
    return "文本";
  }

  function normalizeVariableValue(variableId, value, options = {}) {
    const variable = getVariableById(variableId, options);
    const type = variable?.type ?? "string";
    const fallback = variable?.defaultValue;

    if (type === "number") {
      const parsed = typeof value === "number" ? value : Number.parseFloat(value ?? "");
      if (Number.isFinite(parsed)) {
        return parsed;
      }
      return typeof fallback === "number" ? fallback : 0;
    }

    if (type === "boolean") {
      if (typeof value === "boolean") {
        return value;
      }
      if (value === "true") {
        return true;
      }
      if (value === "false") {
        return false;
      }
      return typeof fallback === "boolean" ? fallback : false;
    }

    if (value === null || value === undefined) {
      return typeof fallback === "string" ? fallback : "";
    }

    return String(value);
  }

  function formatVariableValue(variableId, value, options = {}) {
    const safeValue = normalizeVariableValue(variableId, value, options);

    if (typeof safeValue === "boolean") {
      return safeValue ? "是" : "否";
    }

    return String(safeValue);
  }

  function getVariableDefaultValue(variableId, options = {}) {
    const variable = getVariableById(variableId, options);
    const value = normalizeVariableValue(variableId, variable?.defaultValue, options);
    return typeof value === "number" ? clampVariableNumber(variableId, value, options) : value;
  }

  function renderVariableOptions(selectedVariableId, typeFilter = null, options = {}) {
    const variables = getFilteredVariables(typeFilter, options);
    const escape = getEscaper(options);

    if (variables.length === 0) {
      return `<option value="">当前没有可用变量</option>`;
    }

    return variables
      .map(
        (variable) => `
        <option value="${variable.id}" ${variable.id === selectedVariableId ? "selected" : ""}>
          ${escape(variable.name)} · ${escape(getVariableTypeLabel(variable.type))}
        </option>
      `
      )
      .join("");
  }

  function renderVariableSetValueFields(variableId, value, options = {}) {
    const escape = getEscaper(options);
    const type = getVariableType(variableId, options);
    const safeValue = normalizeVariableValue(variableId, value, options);

    if (type === "number") {
      return `
      <div class="detail-row">
        <label for="editorVariableValueNumber">要设置成多少</label>
        <input
          id="editorVariableValueNumber"
          type="number"
          step="1"
          value="${escape(String(safeValue))}"
        />
      </div>
      <div class="helper-text">当前变量是数字型，会直接写入这个数值。</div>
    `;
    }

    if (type === "boolean") {
      return `
      <div class="detail-row">
        <label for="editorVariableValueBoolean">要设置成什么状态</label>
        <select id="editorVariableValueBoolean">
          <option value="true" ${safeValue === true ? "selected" : ""}>是</option>
          <option value="false" ${safeValue === false ? "selected" : ""}>否</option>
        </select>
      </div>
      <div class="helper-text">当前变量是开关型，只有“是 / 否”两种结果。</div>
    `;
    }

    return `
    <div class="detail-row">
      <label for="editorVariableValueString">要设置成什么文字</label>
      <input
        id="editorVariableValueString"
        type="text"
        value="${escape(safeValue)}"
        placeholder="例如：walk_home"
      />
    </div>
    <div class="helper-text">当前变量是文本型，适合写路线名、状态名或标记词。</div>
  `;
  }

  function renderConditionValueFields(variableId, value, options = {}) {
    const escape = getEscaper(options);
    const type = getVariableType(variableId, options);
    const safeValue = normalizeVariableValue(variableId, value, options);

    if (type === "number") {
      return `
      <div class="detail-row">
        <label>比较的数值</label>
        <input data-field="condition-value-number" type="number" step="1" value="${escape(
          String(safeValue)
        )}" />
      </div>
    `;
    }

    if (type === "boolean") {
      return `
      <div class="detail-row">
        <label>比较的开关结果</label>
        <select data-field="condition-value-boolean">
          <option value="true" ${safeValue === true ? "selected" : ""}>是</option>
          <option value="false" ${safeValue === false ? "selected" : ""}>否</option>
        </select>
      </div>
    `;
    }

    return `
    <div class="detail-row">
      <label>比较的文字</label>
      <input
        data-field="condition-value-string"
        type="text"
        value="${escape(safeValue)}"
        placeholder="例如：walk_home"
      />
    </div>
  `;
  }

  function getConditionOperators(variableId, options = {}) {
    if (getVariableType(variableId, options) === "number") {
      return [
        [">=", "大于等于"],
        [">", "大于"],
        ["<=", "小于等于"],
        ["<", "小于"],
        ["==", "等于"],
        ["!=", "不等于"],
      ];
    }

    return [
      ["==", "等于"],
      ["!=", "不等于"],
      ["contains", "包含"],
      ["not_contains", "不包含"],
      ["starts_with", "以此开头"],
      ["ends_with", "以此结尾"],
    ];
  }

  function getSafeConditionOperator(variableId, operator, options = {}) {
    const operators = getConditionOperators(variableId, options);
    return operators.some(([value]) => value === operator) ? operator : operators[0]?.[0] ?? "==";
  }

  function renderConditionOperatorOptions(variableId, selectedOperator, options = {}) {
    const escape = getEscaper(options);
    return getConditionOperators(variableId, options)
      .map(
        ([value, label]) => `
        <option value="${value}" ${value === selectedOperator ? "selected" : ""}>
          ${escape(label)}
        </option>
      `
      )
      .join("");
  }

  function isEditableChoiceEffect(effect) {
    return effect?.type === "variable_set" || effect?.type === "variable_add";
  }

  function getEditableChoiceEffects(effects = []) {
    return (effects ?? []).filter((effect) => isEditableChoiceEffect(effect));
  }

  function getSafeChoiceEffectType(effectType) {
    return effectType === "variable_add" ? "variable_add" : "variable_set";
  }

  function getChoiceEffectVariableId(effectType, variableId, options = {}) {
    return effectType === "variable_add"
      ? getSafeVariableId(variableId, "number", options)
      : getSafeVariableId(variableId, null, options);
  }

  function normalizeChoiceEffect(effect = {}, options = {}) {
    const type = getSafeChoiceEffectType(effect.type);
    const variableId = getChoiceEffectVariableId(type, effect.variableId, options);

    if (type === "variable_add") {
      return {
        type,
        variableId,
        value: getSafeNumber(effect.value, 1),
      };
    }

    return {
      type,
      variableId,
      value: normalizeVariableValue(variableId, effect.value, options),
    };
  }

  function renderChoiceEffectTypeOptions(selectedType, options = {}) {
    const escape = getEscaper(options);
    return [
      ["variable_add", "给数字变量加减数值"],
      ["variable_set", "把变量直接改成指定值"],
    ]
      .map(
        ([value, label]) => `
        <option value="${value}" ${value === selectedType ? "selected" : ""}>
          ${escape(label)}
        </option>
      `
      )
      .join("");
  }

  function renderChoiceEffectValueFields(effectType, variableId, value, options = {}) {
    const escape = getEscaper(options);

    if (effectType === "variable_add") {
      return `
      <div class="detail-row">
        <label>变化值</label>
        <input
          data-field="choice-effect-value-number"
          type="number"
          step="1"
          value="${escape(String(getSafeNumber(value, 1)))}"
        />
      </div>
      <div class="helper-text">正数表示增加，负数表示减少。</div>
    `;
    }

    const type = getVariableType(variableId, options);
    const safeValue = normalizeVariableValue(variableId, value, options);

    if (type === "number") {
      return `
      <div class="detail-row">
        <label>设置成多少</label>
        <input
          data-field="choice-effect-value-number"
          type="number"
          step="1"
          value="${escape(String(safeValue))}"
        />
      </div>
    `;
    }

    if (type === "boolean") {
      return `
      <div class="detail-row">
        <label>设置成什么状态</label>
        <select data-field="choice-effect-value-boolean">
          <option value="true" ${safeValue === true ? "selected" : ""}>是</option>
          <option value="false" ${safeValue === false ? "selected" : ""}>否</option>
        </select>
      </div>
    `;
    }

    return `
    <div class="detail-row">
      <label>设置成什么文字</label>
      <input
        data-field="choice-effect-value-string"
        type="text"
        value="${escape(safeValue)}"
        placeholder="例如：walk_home"
      />
    </div>
  `;
  }

  global.CanvasiaEditorVariables = Object.freeze({
    STARTER_VARIABLE_PRESETS,
    parseVariableNumberBound,
    getVariableNumberBounds,
    clampVariableNumber,
    getFilteredVariables,
    hasUsableVariable,
    createStarterVariableCopy,
    buildStarterVariableLibrary,
    getSafeVariableId,
    getVariableType,
    getVariableTypeLabel,
    normalizeVariableValue,
    formatVariableValue,
    getVariableDefaultValue,
    renderVariableOptions,
    renderVariableSetValueFields,
    renderConditionValueFields,
    getConditionOperators,
    getSafeConditionOperator,
    renderConditionOperatorOptions,
    isEditableChoiceEffect,
    getEditableChoiceEffects,
    getSafeChoiceEffectType,
    getChoiceEffectVariableId,
    normalizeChoiceEffect,
    renderChoiceEffectTypeOptions,
    renderChoiceEffectValueFields,
  });
})(typeof window !== "undefined" ? window : globalThis);
