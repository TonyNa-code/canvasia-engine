(function attachEditorFilterTools(global) {
  const DASHBOARD_SEARCH_MODE_LABELS = Object.freeze({
    all: "全部结果",
    scenes: "场景",
    characters: "角色",
    lines: "台词和选项",
  });

  const ROUTE_MAP_FILTER_LABELS = Object.freeze({
    all: "全部场景",
    issues: "有问题",
    missing_background: "缺背景",
    missing_music: "缺 BGM",
    missing_voice: "缺语音",
    unreachable: "不可达",
    flat: "演出偏素",
    empty: "正文未开始",
    ready: "完成度高",
  });

  const SCENE_STATUS_LABELS = Object.freeze({
    outline: "待开写",
    drafting: "写作中",
    polishing: "润色中",
    ready: "可试玩",
  });

  const SCENE_PRIORITY_LABELS = Object.freeze({
    normal: "正常",
    focus: "优先处理",
    rush: "马上处理",
    parked: "先放一放",
  });

  const STORY_BLOCK_TYPE_FILTER_LABELS = Object.freeze({
    all: "全部卡片",
    story: "只看正文",
    effect: "只看演出",
    logic: "只看逻辑",
    video: "只看视频",
    dialogue: "只看台词",
    choice: "只看选项",
  });

  const STORY_BLOCK_ISSUE_FILTER_LABELS = Object.freeze({
    all: "全部状态",
    any: "只看有问题",
    missing_voice: "待绑语音",
    missing_asset: "待补素材",
    broken_target: "跳转待修",
    variable_logic: "变量待修",
    achievement_setup: "成就待补",
    too_long: "偏长文本",
  });

  const STORY_SCENE_TREE_FILTER_LABELS = Object.freeze({
    all: "全部场景",
    focus: "重点场景",
    ready: "可试玩",
    issues: "有问题",
    notes: "有便签",
  });

  const CHARACTER_FILTER_LABELS = Object.freeze({
    all: "全部角色",
    missing_voice: "待配音",
    voiced: "语音已齐",
    major: "台词较多",
    silent: "暂无台词",
  });

  const PREVIEW_ISSUE_FILTER_LABELS = Object.freeze({
    all: "全部检查",
    errors: "结构错误",
    warnings: "补充提醒",
    export_missing: "导出缺失",
    media_budget: "素材预算",
    unused_assets: "未使用素材",
  });

  const PREVIEW_SCENE_FILTER_LABELS = Object.freeze({
    all: "全部起点",
    focus: "重点场景",
    ready: "可试玩",
    issues: "有问题",
  });

  const SCRIPT_TYPE_LABELS = Object.freeze({
    dialogue: "台词",
    narration: "旁白",
    choice: "选项",
  });

  const SCRIPT_VOICE_FILTER_LABELS = Object.freeze({
    all: "全部状态",
    missing: "待绑语音",
    voiced: "已绑语音",
    not_required: "不需要语音",
  });

  const SCRIPT_ISSUE_FILTER_LABELS = Object.freeze({
    all: "全部问题状态",
    any: "只看有问题",
    placeholder: "待补正文",
    too_long: "偏长内容",
    duplicate: "疑似重复",
    missing_voice: "待绑语音",
  });

  function hasOwn(source, key) {
    return Object.prototype.hasOwnProperty.call(source, key);
  }

  function hasCollectionEntry(collection, key) {
    if (!key || !collection) {
      return false;
    }
    if (typeof collection.has === "function") {
      return collection.has(key);
    }
    return hasOwn(collection, key);
  }

  function getCollectionEntry(collection, key) {
    if (!key || !collection) {
      return null;
    }
    if (typeof collection.get === "function") {
      return collection.get(key) ?? null;
    }
    return hasOwn(collection, key) ? collection[key] ?? null : null;
  }

  function getSafeValue(labels, value, fallback) {
    return hasOwn(labels, value) ? value : fallback;
  }

  function getLabel(labels, value, fallback) {
    return labels[getSafeValue(labels, value, fallback)] ?? labels[fallback];
  }

  function getSafeDashboardSearchMode(mode) {
    return getSafeValue(DASHBOARD_SEARCH_MODE_LABELS, mode, "all");
  }

  function getDashboardSearchModeLabel(mode) {
    return getLabel(DASHBOARD_SEARCH_MODE_LABELS, mode, "all");
  }

  function getSafeRouteMapFilter(mode) {
    return getSafeValue(ROUTE_MAP_FILTER_LABELS, mode, "all");
  }

  function getRouteMapFilterLabel(mode) {
    return getLabel(ROUTE_MAP_FILTER_LABELS, mode, "all");
  }

  function doesRouteNodeMatchFilter(node = {}, filterMode = "all") {
    const safeFilter = getSafeRouteMapFilter(filterMode);

    if (safeFilter === "all") {
      return true;
    }

    if (safeFilter === "issues") {
      return (
        (node.errorCount ?? 0) > 0 ||
        (node.warningCount ?? 0) > 0 ||
        (node.brokenRouteCount ?? 0) > 0 ||
        node.isUnreachable === true
      );
    }

    if (safeFilter === "missing_background") {
      return Boolean(node.hasStoryContent) && !node.hasBackground;
    }

    if (safeFilter === "missing_music") {
      return Boolean(node.hasStoryContent) && !node.hasMusic;
    }

    if (safeFilter === "missing_voice") {
      return (node.missingVoiceCount ?? 0) > 0;
    }

    if (safeFilter === "unreachable") {
      return node.isUnreachable === true;
    }

    if (safeFilter === "flat") {
      return Boolean(node.hasStoryContent) && !node.hasEffects;
    }

    if (safeFilter === "empty") {
      return !node.hasStoryContent;
    }

    if (safeFilter === "ready") {
      return (node.completionScore ?? 0) >= 80;
    }

    return true;
  }

  function getRouteMapFilterCount(routeOverview = {}, filterMode = "all") {
    return (Array.isArray(routeOverview.nodes) ? routeOverview.nodes : [])
      .filter((node) => doesRouteNodeMatchFilter(node, filterMode)).length;
  }

  function getSafeSceneStatus(value) {
    return getSafeValue(SCENE_STATUS_LABELS, value, "drafting");
  }

  function getSceneStatusLabel(value) {
    return getLabel(SCENE_STATUS_LABELS, value, "drafting");
  }

  function getSafeScenePriority(value) {
    return getSafeValue(SCENE_PRIORITY_LABELS, value, "normal");
  }

  function getScenePriorityLabel(value) {
    return getLabel(SCENE_PRIORITY_LABELS, value, "normal");
  }

  function getSceneStatusToneClass(status) {
    const safeStatus = getSafeSceneStatus(status);
    if (safeStatus === "ready") {
      return "good-text";
    }
    if (safeStatus === "polishing") {
      return "warn-text";
    }
    return "";
  }

  function getScenePriorityToneClass(priority) {
    const safePriority = getSafeScenePriority(priority);
    if (safePriority === "rush") {
      return "danger-text";
    }
    if (safePriority === "focus") {
      return "warn-text";
    }
    return "";
  }

  function getSceneQuickButtonToneClass(kind, value) {
    if (kind === "status") {
      return getSafeSceneStatus(value) === "ready" ? "is-good" : "is-soft";
    }

    const safePriority = getSafeScenePriority(value);
    if (safePriority === "rush") {
      return "is-danger";
    }
    if (safePriority === "focus") {
      return "is-warn";
    }
    if (safePriority === "parked") {
      return "is-muted";
    }
    return "is-soft";
  }

  function getSafeStoryBlockTypeFilter(value) {
    return getSafeValue(STORY_BLOCK_TYPE_FILTER_LABELS, value, "all");
  }

  function getStoryBlockTypeFilterLabel(value) {
    return getLabel(STORY_BLOCK_TYPE_FILTER_LABELS, value, "all");
  }

  function getSafeStoryBlockIssueFilter(value) {
    return getSafeValue(STORY_BLOCK_ISSUE_FILTER_LABELS, value, "all");
  }

  function getStoryBlockIssueFilterLabel(value) {
    return getLabel(STORY_BLOCK_ISSUE_FILTER_LABELS, value, "all");
  }

  function getStoryBlockGroup(type) {
    if (type === "dialogue" || type === "narration" || type === "choice") {
      return "story";
    }

    if (
      type === "jump" ||
      type === "scene_call" ||
      type === "scene_return" ||
      type === "variable_set" ||
      type === "variable_add" ||
      type === "text_input" ||
      type === "condition" ||
      type === "achievement_unlock"
    ) {
      return "logic";
    }

    return "effect";
  }

  function getStoryBlockGroupLabel(type) {
    const group = getStoryBlockGroup(type);
    if (group === "story") {
      return "正文";
    }
    if (group === "logic") {
      return "逻辑";
    }
    return "演出";
  }

  function isRawVariableValueMatchingType(variable, value) {
    if (!variable) {
      return false;
    }
    if (variable.type === "number") {
      return typeof value === "number" && Number.isFinite(value);
    }
    if (variable.type === "boolean") {
      return typeof value === "boolean";
    }
    return typeof value === "string";
  }

  function isConditionOperatorAllowedForVariable(variable, operator) {
    const safeOperator = String(operator ?? "==").trim() || "==";
    if (["==", "=", "!="].includes(safeOperator)) {
      return true;
    }
    if ([">", ">=", "<", "<="].includes(safeOperator)) {
      return variable?.type === "number";
    }
    if (["contains", "not_contains", "starts_with", "ends_with"].includes(safeOperator)) {
      return variable?.type === "string";
    }
    return false;
  }

  function hasVariableReferenceIssue(
    variablesById,
    variableId,
    { expectedType = null, value = null, validateValue = false, operator = null } = {}
  ) {
    const variable = getCollectionEntry(variablesById, variableId);
    if (!variable) {
      return true;
    }
    if (expectedType && variable.type !== expectedType) {
      return true;
    }
    if (validateValue && !isRawVariableValueMatchingType(variable, value)) {
      return true;
    }
    if (operator !== null && !isConditionOperatorAllowedForVariable(variable, operator)) {
      return true;
    }
    return false;
  }

  function blockHasVariableLogicIssue(block = {}, options = {}) {
    const variablesById = options.variablesById ?? null;
    const choiceAvailabilityTools = options.choiceAvailabilityTools ?? {};
    const normalizeChoiceAvailabilityMode =
      choiceAvailabilityTools.normalizeChoiceAvailabilityMode ||
      ((value) => (["hide_when_false", "disable_when_false"].includes(value) ? value : "always"));
    const getChoiceAvailabilityRules =
      choiceAvailabilityTools.getChoiceAvailabilityRules ||
      ((option) => (Array.isArray(option?.choiceAvailabilityRules) ? option.choiceAvailabilityRules : []));
    const hasIssue = (variableId, issueOptions = {}) =>
      hasVariableReferenceIssue(variablesById, variableId, issueOptions);

    if (block.type === "variable_set") {
      return hasIssue(block.variableId, { value: block.value, validateValue: true });
    }
    if (block.type === "variable_add") {
      return hasIssue(block.variableId, {
        expectedType: "number",
        value: block.value,
        validateValue: true,
      });
    }
    if (block.type === "choice") {
      return (block.options ?? []).some((option) => {
        const availabilityMode = normalizeChoiceAvailabilityMode(option.choiceAvailabilityMode);
        const availabilityRules = getChoiceAvailabilityRules(option);
        const hasAvailabilityIssue =
          availabilityMode !== "always" &&
          (availabilityRules.length === 0 ||
            availabilityRules.some((rule) =>
              hasIssue(rule.variableId, {
                value: rule.value,
                validateValue: true,
                operator: rule.operator,
              })
            ));
        const hasEffectIssue = (option.effects ?? []).some((effect) => {
          if (effect.type === "variable_add") {
            return hasIssue(effect.variableId, {
              expectedType: "number",
              value: effect.value,
              validateValue: true,
            });
          }
          if (effect.type === "variable_set") {
            return hasIssue(effect.variableId, { value: effect.value, validateValue: true });
          }
          return true;
        });
        return hasAvailabilityIssue || hasEffectIssue;
      });
    }
    if (block.type === "condition") {
      return (block.branches ?? []).some((branch) =>
        (branch.when ?? []).some((rule) =>
          hasIssue(rule.variableId, {
            value: rule.value,
            validateValue: true,
            operator: rule.operator,
          })
        )
      );
    }
    return false;
  }

  function getStoryBlockIssueItems(block = {}, options = {}) {
    const items = [];
    const pushIssue = (key, label, toneClass = "warn-text") => {
      if (!items.some((item) => item.key === key)) {
        items.push({ key, label, toneClass });
      }
    };
    const {
      assetsById = null,
      scenesById = null,
      getExpressionAssetId = () => "",
      getSafeParticleAction = (action) => action,
      isReadableTextLong = () => false,
      choiceManyOptions = 6,
      choiceLongWarningLength = 42,
      hasVariableLogicIssue = null,
      variablesById = null,
      choiceAvailabilityTools = null,
    } = options;

    if (block.type === "dialogue" && !block.voiceAssetId) {
      pushIssue("missing_voice", "待绑语音");
    }

    if (
      ((block.type === "dialogue" || block.type === "narration") && isReadableTextLong(block.text)) ||
      (block.type === "choice" &&
        ((block.options ?? []).length > choiceManyOptions ||
          (block.options ?? []).some((option) => String(option.text ?? "").trim().length > choiceLongWarningLength)))
    ) {
      pushIssue("too_long", "偏长文本");
    }

    const assetIdsToCheck = [];
    if (["background", "music_play", "sfx_play", "video_play"].includes(block.type)) {
      assetIdsToCheck.push(block.assetId);
    }
    if (block.type === "particle_effect" && getSafeParticleAction(block.action) !== "stop" && block.assetId) {
      assetIdsToCheck.push(block.assetId);
    }
    if (block.type === "achievement_unlock" && block.iconAssetId) {
      assetIdsToCheck.push(block.iconAssetId);
    }
    const expressionAssetId = getExpressionAssetId(block);
    if (expressionAssetId) {
      assetIdsToCheck.push(expressionAssetId);
    }

    if (
      assetIdsToCheck.some((assetId) => {
        if (!assetId) {
          return true;
        }
        const asset = getCollectionEntry(assetsById, assetId);
        return !asset || !asset.fileExists;
      })
    ) {
      pushIssue("missing_asset", "待补素材");
    }

    if (block.type === "jump" && !hasCollectionEntry(scenesById, block.targetSceneId)) {
      pushIssue("broken_target", "跳转待修", "danger-text");
    }

    if (block.type === "scene_call" && !hasCollectionEntry(scenesById, block.targetSceneId)) {
      pushIssue("broken_target", "调用待修", "danger-text");
    }

    if (
      block.type === "choice" &&
      (block.options ?? []).some((option) => option.gotoSceneId && !hasCollectionEntry(scenesById, option.gotoSceneId))
    ) {
      pushIssue("broken_target", "跳转待修", "danger-text");
    }

    if (
      block.type === "condition" &&
      (
        !hasCollectionEntry(scenesById, block.elseGotoSceneId) ||
        (block.branches ?? []).some((branch) => branch.gotoSceneId && !hasCollectionEntry(scenesById, branch.gotoSceneId))
      )
    ) {
      pushIssue("broken_target", "跳转待修", "danger-text");
    }

    const variableLogicIssue =
      typeof hasVariableLogicIssue === "function"
        ? hasVariableLogicIssue(block)
        : blockHasVariableLogicIssue(block, { variablesById, choiceAvailabilityTools });
    if (variableLogicIssue) {
      pushIssue("variable_logic", "变量待修", "danger-text");
    }

    if (
      block.type === "achievement_unlock" &&
      (!String(block.achievementId ?? "").trim() || !String(block.title ?? "").trim())
    ) {
      pushIssue("achievement_setup", "成就待补", "danger-text");
    }

    return items;
  }

  function getSafeStorySceneTreeFilter(value) {
    return getSafeValue(STORY_SCENE_TREE_FILTER_LABELS, value, "all");
  }

  function getStorySceneTreeFilterLabel(value) {
    return getLabel(STORY_SCENE_TREE_FILTER_LABELS, value, "all");
  }

  function getSafeCharacterFilterMode(value) {
    return getSafeValue(CHARACTER_FILTER_LABELS, value, "all");
  }

  function getCharacterFilterLabel(value) {
    return getLabel(CHARACTER_FILTER_LABELS, value, "all");
  }

  function getSafePreviewIssueFilterMode(value) {
    return getSafeValue(PREVIEW_ISSUE_FILTER_LABELS, value, "all");
  }

  function getPreviewIssueFilterLabel(value) {
    return getLabel(PREVIEW_ISSUE_FILTER_LABELS, value, "all");
  }

  function getSafePreviewSceneFilterMode(value) {
    return getSafeValue(PREVIEW_SCENE_FILTER_LABELS, value, "all");
  }

  function getPreviewSceneFilterLabel(value) {
    return getLabel(PREVIEW_SCENE_FILTER_LABELS, value, "all");
  }

  function getSafeScriptTypeFilter(type) {
    return type === "all" || hasOwn(SCRIPT_TYPE_LABELS, type) ? type : "all";
  }

  function getScriptTypeLabel(type) {
    return type === "all" ? "全部内容" : SCRIPT_TYPE_LABELS[getSafeScriptTypeFilter(type)] ?? "全部内容";
  }

  function getSafeScriptVoiceFilter(value) {
    return getSafeValue(SCRIPT_VOICE_FILTER_LABELS, value, "all");
  }

  function getScriptVoiceFilterLabel(value) {
    return getLabel(SCRIPT_VOICE_FILTER_LABELS, value, "all");
  }

  function getSafeScriptIssueFilter(value) {
    return getSafeValue(SCRIPT_ISSUE_FILTER_LABELS, value, "all");
  }

  function getScriptIssueFilterLabel(value) {
    return getLabel(SCRIPT_ISSUE_FILTER_LABELS, value, "all");
  }

  function normalizeDashboardSearchQuery(value) {
    return String(value ?? "")
      .trim()
      .toLowerCase()
      .replace(/\s+/g, " ");
  }

  function getDashboardSearchTerms(value) {
    const query = normalizeDashboardSearchQuery(value);
    return query ? query.split(" ").filter(Boolean) : [];
  }

  function doesSearchTextMatchTerms(searchText, terms) {
    const safeTerms = Array.isArray(terms)
      ? terms.map((term) => normalizeDashboardSearchQuery(term)).filter(Boolean)
      : getDashboardSearchTerms(terms);
    if (!safeTerms.length) {
      return true;
    }
    const haystack = normalizeDashboardSearchQuery(searchText);
    return safeTerms.every((term) => haystack.includes(term));
  }

  function normalizeScriptSearchQuery(value) {
    return normalizeDashboardSearchQuery(value);
  }

  function getScriptSearchTerms(value) {
    return getDashboardSearchTerms(value);
  }

  function scoreDashboardSearchMatch(primaryText, searchFields, normalizedQuery, terms) {
    const safeTerms = Array.isArray(terms)
      ? terms.map((term) => normalizeDashboardSearchQuery(term)).filter(Boolean)
      : getDashboardSearchTerms(normalizedQuery);
    if (!safeTerms.length) {
      return -1;
    }

    const fields = Array.isArray(searchFields) ? searchFields : [searchFields];
    const haystack = normalizeDashboardSearchQuery(fields.filter(Boolean).join(" "));
    if (!doesSearchTextMatchTerms(haystack, safeTerms)) {
      return -1;
    }

    const safeQuery = normalizeDashboardSearchQuery(normalizedQuery);
    const primary = normalizeDashboardSearchQuery(primaryText);
    let score = 0;

    if (safeQuery && primary.startsWith(safeQuery)) {
      score += 18;
    } else if (safeQuery && primary.includes(safeQuery)) {
      score += 10;
    } else if (safeQuery && haystack.includes(safeQuery)) {
      score += 5;
    }

    score += safeTerms.reduce(
      (total, term) => total + (primary.includes(term) ? 4 : haystack.includes(term) ? 1 : 0),
      0
    );

    return score;
  }

  function sortDashboardSearchResults(items) {
    return (Array.isArray(items) ? [...items] : []).sort(
      (left, right) =>
        (Number(right?.score) || 0) - (Number(left?.score) || 0) ||
        String(left?.title ?? "").localeCompare(String(right?.title ?? ""), "zh-CN")
    );
  }

  global.CanvasiaEditorFilters = Object.freeze({
    DASHBOARD_SEARCH_MODE_LABELS,
    ROUTE_MAP_FILTER_LABELS,
    SCENE_STATUS_LABELS,
    SCENE_PRIORITY_LABELS,
    STORY_BLOCK_TYPE_FILTER_LABELS,
    STORY_BLOCK_ISSUE_FILTER_LABELS,
    STORY_SCENE_TREE_FILTER_LABELS,
    CHARACTER_FILTER_LABELS,
    PREVIEW_ISSUE_FILTER_LABELS,
    PREVIEW_SCENE_FILTER_LABELS,
    SCRIPT_TYPE_LABELS,
    SCRIPT_VOICE_FILTER_LABELS,
    SCRIPT_ISSUE_FILTER_LABELS,
    getSafeDashboardSearchMode,
    getDashboardSearchModeLabel,
    getSafeRouteMapFilter,
    getRouteMapFilterLabel,
    doesRouteNodeMatchFilter,
    getRouteMapFilterCount,
    getSafeSceneStatus,
    getSceneStatusLabel,
    getSafeScenePriority,
    getScenePriorityLabel,
    getSceneStatusToneClass,
    getScenePriorityToneClass,
    getSceneQuickButtonToneClass,
    getSafeStoryBlockTypeFilter,
    getStoryBlockTypeFilterLabel,
    getSafeStoryBlockIssueFilter,
    getStoryBlockIssueFilterLabel,
    getStoryBlockGroup,
    getStoryBlockGroupLabel,
    isRawVariableValueMatchingType,
    isConditionOperatorAllowedForVariable,
    hasVariableReferenceIssue,
    blockHasVariableLogicIssue,
    getStoryBlockIssueItems,
    getSafeStorySceneTreeFilter,
    getStorySceneTreeFilterLabel,
    getSafeCharacterFilterMode,
    getCharacterFilterLabel,
    getSafePreviewIssueFilterMode,
    getPreviewIssueFilterLabel,
    getSafePreviewSceneFilterMode,
    getPreviewSceneFilterLabel,
    getSafeScriptTypeFilter,
    getScriptTypeLabel,
    getSafeScriptVoiceFilter,
    getScriptVoiceFilterLabel,
    getSafeScriptIssueFilter,
    getScriptIssueFilterLabel,
    normalizeDashboardSearchQuery,
    getDashboardSearchTerms,
    doesSearchTextMatchTerms,
    normalizeScriptSearchQuery,
    getScriptSearchTerms,
    scoreDashboardSearchMatch,
    sortDashboardSearchResults,
  });
})(typeof window !== "undefined" ? window : globalThis);
