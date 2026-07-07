(function attachStoryTemplatePanelTools(global) {
  const DEFAULT_TEMPLATE_TOOLS = global.CanvasiaEditorStoryTemplates || {};

  function escapeHtmlFallback(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function getStoryTemplateTools(options = {}) {
    return options.storyTemplateTools || DEFAULT_TEMPLATE_TOOLS;
  }

  function getStoryTemplatePanelItems(scene = null, options = {}) {
    const storyTemplateTools = getStoryTemplateTools(options);
    const fallbackTemplateIds = Array.isArray(options.fallbackTemplateIds) ? options.fallbackTemplateIds : [];
    const fallbackItems = fallbackTemplateIds.map((templateId) => ({ templateId }));

    if (typeof storyTemplateTools.getStoryTemplateRecommendedPanelItems === "function") {
      return storyTemplateTools.getStoryTemplateRecommendedPanelItems(scene, {
        limit: options.limit ?? 4,
      });
    }

    return typeof storyTemplateTools.getStoryTemplatePanelItems === "function"
      ? storyTemplateTools.getStoryTemplatePanelItems()
      : fallbackItems;
  }

  function getStoryTemplateButtonDescription(item = {}, summary = {}) {
    const recommendationReason = String(item?.recommendationReason ?? "").trim();
    if (recommendationReason) {
      return `推荐：${recommendationReason}`;
    }

    const description = String(item?.description ?? "").trim();
    if (description) {
      return description;
    }

    return Array.isArray(summary.labels) && summary.labels.length
      ? summary.labels.slice(0, 4).join(" + ")
      : "插入一组剧情卡片";
  }

  function buildStoryTemplateButtonPlan(summary = {}, requirement = {}) {
    const labels = Array.isArray(summary.labels) ? summary.labels : [];
    const blockCount = Number(summary.blockCount ?? 0);
    const labelPreview = labels.slice(0, 3).join(" / ");
    const summaryText = labelPreview
      ? `预计插入 ${blockCount} 张：${labelPreview}`
      : `预计插入 ${blockCount} 张剧情卡片`;
    const requirementLabel = requirement.requiresAny
      ? requirement.requiresNumber
        ? "需要数值变量"
        : "需要变量"
      : "不改变量";

    return Object.freeze({
      summaryText,
      requirementLabel,
      labels: Object.freeze(labels.slice(0, 3)),
    });
  }

  function renderStoryTemplateButton(item = {}, options = {}) {
    const escapeHtml = typeof options.escapeHtml === "function" ? options.escapeHtml : escapeHtmlFallback;
    const storyTemplateTools = getStoryTemplateTools(options);
    const getStoryTemplatePreset =
      typeof options.getStoryTemplatePreset === "function"
        ? options.getStoryTemplatePreset
        : storyTemplateTools.getStoryTemplatePreset?.bind(storyTemplateTools);
    const getStoryTemplateSummary =
      typeof options.getStoryTemplateSummary === "function"
        ? options.getStoryTemplateSummary
        : storyTemplateTools.getStoryTemplateSummary?.bind(storyTemplateTools);
    const getStoryTemplateVariableRequirement =
      typeof options.getStoryTemplateVariableRequirement === "function"
        ? options.getStoryTemplateVariableRequirement
        : storyTemplateTools.getStoryTemplateVariableRequirement?.bind(storyTemplateTools);
    const getBlockLabel = typeof options.getBlockLabel === "function" ? options.getBlockLabel : (type) => type;
    const templateId = String(item.templateId ?? "").trim();
    const preset = getStoryTemplatePreset?.(templateId);

    if (!templateId || !preset || typeof getStoryTemplateSummary !== "function") {
      return "";
    }

    const summary = getStoryTemplateSummary(templateId, { getBlockLabel });
    const requirement =
      typeof getStoryTemplateVariableRequirement === "function"
        ? getStoryTemplateVariableRequirement(templateId)
        : { requiresAny: false, requiresNumber: false };
    const plan = buildStoryTemplateButtonPlan(summary, requirement);
    const tone = String(item.tone ?? "").trim();
    const toneClass = tone ? ` is-${escapeHtml(tone)}` : "";
    const isRecommended = Boolean(item.isRecommended);
    const recommendedClass = isRecommended ? " is-recommended" : "";
    const badgeLabel = String(item.badgeLabel ?? "").trim();

    return `
      <button
        class="story-template-button${toneClass}${recommendedClass}"
        type="button"
        data-action="apply-story-template"
        data-template-id="${escapeHtml(templateId)}"
      >
        ${isRecommended && badgeLabel ? `<span class="story-template-recommendation-badge">${escapeHtml(badgeLabel)}</span>` : ""}
        <strong>${escapeHtml(summary.title || preset.title)}</strong>
        <span>${escapeHtml(getStoryTemplateButtonDescription(item, summary))}</span>
        <div class="story-template-button-plan">
          <span>${escapeHtml(plan.summaryText)}</span>
          <span>${escapeHtml(plan.requirementLabel)}</span>
        </div>
        <div class="story-template-button-meta">
          <span>${Number(summary.blockCount ?? 0)} 张卡片</span>
          ${plan.labels.map((label) => `<span>${escapeHtml(label)}</span>`).join("")}
        </div>
      </button>
    `;
  }

  function renderStoryTemplateGrid(scene = null, options = {}) {
    return getStoryTemplatePanelItems(scene, options)
      .map((item) => renderStoryTemplateButton(item, options))
      .join("");
  }

  global.CanvasiaEditorStoryTemplatePanel = Object.freeze({
    buildStoryTemplateButtonPlan,
    getStoryTemplateButtonDescription,
    getStoryTemplatePanelItems,
    renderStoryTemplateButton,
    renderStoryTemplateGrid,
  });
})(window);
