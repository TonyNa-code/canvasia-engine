(function attachCanvasiaRuntimeChoiceAvailability(global) {
  "use strict";

  const CHOICE_CONTINUE_TARGET = "__continue__";
  const CHOICE_SAFETY_OPTION_ID = "__canvasia_choice_safety_continue__";
  const CHOICE_AVAILABILITY_MODES = Object.freeze({
    ALWAYS: "always",
    HIDE_WHEN_FALSE: "hide_when_false",
    DISABLE_WHEN_FALSE: "disable_when_false",
  });
  const CHOICE_AVAILABILITY_MODE_LABELS = Object.freeze({
    always: "始终可选",
    hide_when_false: "条件不满足时隐藏",
    disable_when_false: "条件不满足时锁定",
  });

  function cleanText(value, fallback = "") {
    const text = String(value ?? "").trim();
    return text || fallback;
  }

  function toArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function normalizeChoiceAvailabilityMode(value) {
    const aliases = {
      hide: CHOICE_AVAILABILITY_MODES.HIDE_WHEN_FALSE,
      hidden: CHOICE_AVAILABILITY_MODES.HIDE_WHEN_FALSE,
      disable: CHOICE_AVAILABILITY_MODES.DISABLE_WHEN_FALSE,
      disabled: CHOICE_AVAILABILITY_MODES.DISABLE_WHEN_FALSE,
      locked: CHOICE_AVAILABILITY_MODES.DISABLE_WHEN_FALSE,
    };
    const candidate = aliases[cleanText(value)] ?? cleanText(value, CHOICE_AVAILABILITY_MODES.ALWAYS);
    return Object.hasOwn(CHOICE_AVAILABILITY_MODE_LABELS, candidate)
      ? candidate
      : CHOICE_AVAILABILITY_MODES.ALWAYS;
  }

  function getChoiceAvailabilityRules(option = {}) {
    return toArray(option.choiceAvailabilityWhen ?? option.availabilityWhen ?? option.when);
  }

  function getChoiceLockedReason(option = {}, fallback = "条件尚未满足") {
    return cleanText(option.choiceLockedReason ?? option.lockedReason, fallback);
  }

  function evaluateChoiceAvailabilityRule(rule = {}, variableValues = {}, options = {}) {
    if (typeof options.evaluateRule === "function") {
      return Boolean(options.evaluateRule(rule, variableValues, options));
    }
    const conditionTools = options.conditionTools ?? global.CanvasiaRuntimeConditions;
    if (typeof conditionTools?.evaluateConditionRule !== "function") {
      return false;
    }
    return Boolean(conditionTools.evaluateConditionRule(rule, variableValues, options.conditionOptions ?? options));
  }

  function inspectChoiceOptionAvailability(option = {}, variableValues = {}, options = {}) {
    const mode = normalizeChoiceAvailabilityMode(option.choiceAvailabilityMode ?? option.availabilityMode);
    const rules = getChoiceAvailabilityRules(option);
    const ruleResults = rules.map((rule) => evaluateChoiceAvailabilityRule(rule, variableValues, options));
    const matched = mode === CHOICE_AVAILABILITY_MODES.ALWAYS
      ? true
      : rules.length > 0 && ruleResults.every(Boolean);
    const visible = mode !== CHOICE_AVAILABILITY_MODES.HIDE_WHEN_FALSE || matched;
    const enabled = visible && (mode !== CHOICE_AVAILABILITY_MODES.DISABLE_WHEN_FALSE || matched);

    return {
      mode,
      modeLabel: CHOICE_AVAILABILITY_MODE_LABELS[mode],
      rules,
      ruleResults,
      matched,
      visible,
      enabled,
      lockedReason: enabled ? "" : getChoiceLockedReason(option),
    };
  }

  function createChoiceSafetyOption(options = {}) {
    return {
      id: CHOICE_SAFETY_OPTION_ID,
      text: cleanText(options.safetyText, "继续剧情（安全兜底）"),
      gotoSceneId: CHOICE_CONTINUE_TARGET,
      effects: [],
      choiceAvailabilityMode: CHOICE_AVAILABILITY_MODES.ALWAYS,
      choiceAvailabilityMatched: true,
      choiceVisible: true,
      choiceEnabled: true,
      choiceLockedReason: "",
      isChoiceSafetyFallback: true,
    };
  }

  function resolveChoiceOptions(choiceOptions = [], variableValues = {}, options = {}) {
    const allOptions = toArray(choiceOptions).map((option, index) => {
      const availability = inspectChoiceOptionAvailability(option, variableValues, options);
      return {
        ...option,
        id: cleanText(option?.id, `choice_option_${index + 1}`),
        choiceAvailabilityMode: availability.mode,
        choiceAvailabilityMatched: availability.matched,
        choiceAvailabilityRuleResults: availability.ruleResults,
        choiceVisible: availability.visible,
        choiceEnabled: availability.enabled,
        choiceLockedReason: availability.lockedReason,
        isChoiceSafetyFallback: false,
      };
    });
    const authoredVisibleOptions = allOptions.filter((option) => option.choiceVisible);
    const selectableOptions = authoredVisibleOptions.filter((option) => option.choiceEnabled);
    const allUnavailable = selectableOptions.length === 0;
    const safetyOption = allUnavailable && options.includeSafetyFallback !== false
      ? createChoiceSafetyOption(options)
      : null;
    const runtimeOptions = safetyOption ? [...authoredVisibleOptions, safetyOption] : authoredVisibleOptions;

    return {
      allOptions,
      authoredVisibleOptions,
      selectableOptions,
      runtimeOptions,
      safetyOption,
      allUnavailable,
      hiddenCount: allOptions.filter((option) => !option.choiceVisible).length,
      lockedCount: authoredVisibleOptions.filter((option) => !option.choiceEnabled).length,
    };
  }

  function isChoiceOptionSelectable(option = {}) {
    return option.choiceVisible !== false && option.choiceEnabled !== false;
  }

  function findSelectableChoiceIndex(options = [], startIndex = 0, direction = 1) {
    const items = toArray(options);
    if (!items.length) {
      return -1;
    }
    const step = Number(direction) < 0 ? -1 : 1;
    const safeStart = Number.isFinite(Number(startIndex)) ? Number(startIndex) : 0;
    for (let offset = 0; offset < items.length; offset += 1) {
      const index = ((safeStart + offset * step) % items.length + items.length) % items.length;
      if (isChoiceOptionSelectable(items[index])) {
        return index;
      }
    }
    return -1;
  }

  global.CanvasiaRuntimeChoiceAvailability = Object.freeze({
    CHOICE_CONTINUE_TARGET,
    CHOICE_SAFETY_OPTION_ID,
    CHOICE_AVAILABILITY_MODES,
    CHOICE_AVAILABILITY_MODE_LABELS,
    normalizeChoiceAvailabilityMode,
    getChoiceAvailabilityRules,
    getChoiceLockedReason,
    evaluateChoiceAvailabilityRule,
    inspectChoiceOptionAvailability,
    createChoiceSafetyOption,
    resolveChoiceOptions,
    isChoiceOptionSelectable,
    findSelectableChoiceIndex,
  });
})(typeof window !== "undefined" ? window : globalThis);
