(function attachBeginnerAssetsGuideTools(global) {
  function fallbackEscapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function fallbackActionButton(action, emphasized = false) {
    const datasetMarkup = Object.entries(action?.dataset ?? {})
      .map(([key, value]) => ` data-${key}="${fallbackEscapeHtml(value)}"`)
      .join("");
    return `<button type="button" class="${emphasized ? "primary" : "secondary"}" data-action="${fallbackEscapeHtml(
      action?.action ?? ""
    )}"${datasetMarkup}>${fallbackEscapeHtml(action?.label ?? "继续")}</button>`;
  }

  function fallbackMetricCard(label, value, hint) {
    return `
      <article class="route-metric-card">
        <span>${fallbackEscapeHtml(label)}</span>
        <strong>${fallbackEscapeHtml(value)}</strong>
        <small>${fallbackEscapeHtml(hint)}</small>
      </article>
    `;
  }

  function getHelper(helpers, key, fallback) {
    return typeof helpers?.[key] === "function" ? helpers[key] : fallback;
  }

  function getSafeCount(value) {
    const count = Number(value ?? 0);
    return Number.isFinite(count) ? Math.max(0, count) : 0;
  }

  function buildBeginnerAssetsGuideModel(context = {}) {
    const overview = context.overview ?? {};
    const selectedAsset = context.selectedAsset ?? null;
    const selectedAssetType = String(context.selectedAssetType ?? "");
    const selectedTypeLabel = String(context.selectedTypeLabel ?? "素材");
    const selectedAssetName = String(context.selectedAssetName ?? selectedAsset?.name ?? `当前${selectedTypeLabel}`);
    const voiceMatchTargetCount = getSafeCount(context.voiceMatchTargetCount);
    const currentTypeSummaryText = String(context.currentTypeSummaryText ?? "这一类暂时还没有素材");
    const readyCount = getSafeCount(overview.readyCount);
    const missingCount = getSafeCount(overview.missingCount);
    const urgentMissingCount = getSafeCount(overview.urgentMissingCount);

    let title = "导入第一批素材";
    let description = "新手模式下，素材页优先处理导入、补齐和替换；标签整理、批量清理和重复分析可后续再处理。";
    let actions = [
      { label: "上传素材", action: "pick-assets" },
      { label: "去剧情页继续写", action: "switch-screen", dataset: { screen: "story" } },
    ];

    if (selectedAssetType === "voice" && voiceMatchTargetCount > 0) {
      title = "匹配待导入语音条目";
      description = `当前已选中 ${voiceMatchTargetCount} 个待导入语音条目，可直接执行批量文件匹配。`;
      actions = [
        { label: "批量匹配语音文件", action: "pick-voice-placeholder-files" },
        { label: "只看待导入", action: "focus-asset-gap", dataset: { "asset-filter-mode": "missing_file", "asset-type": "voice" } },
      ];
    } else if (selectedAsset && !selectedAsset.fileExists) {
      title = `补齐“${selectedAssetName}”的真实文件`;
      description = `当前选中的${selectedTypeLabel}条目还没有真实文件，补齐后预览和导出才会生效。`;
      actions = [
        { label: "补/替换文件", action: "replace-asset-file" },
        { label: "只看这类待导入", action: "focus-asset-gap", dataset: { "asset-filter-mode": "missing_file", "asset-type": selectedAssetType } },
      ];
    } else if (urgentMissingCount > 0) {
      title = "补齐已被引用的缺口素材";
      description = `当前有 ${urgentMissingCount} 个素材已被剧情或角色引用，但尚未提供真实文件。`;
      actions = [
        { label: "只看已引用缺口", action: "focus-asset-gap", dataset: { "asset-filter-mode": "urgent_missing" } },
        { label: "上传素材", action: "pick-assets" },
      ];
    } else if (missingCount > 0) {
      title = "继续补齐待导入素材";
      description = `当前还有 ${missingCount} 个素材条目缺少真实文件，可优先补当前剧情会使用到的分类。`;
      actions = [
        { label: "只看待导入", action: "focus-asset-gap", dataset: { "asset-filter-mode": "missing_file" } },
        { label: "上传素材", action: "pick-assets" },
      ];
    } else if (readyCount > 0) {
      title = "素材基础已具备";
      description = `当前已有 ${readyCount} 个素材具备真实文件，可返回剧情页继续搭建内容。`;
      actions = [
        { label: "去剧情页继续写", action: "switch-screen", dataset: { screen: "story" } },
        { label: "去试玩页看看", action: "switch-screen", dataset: { screen: "preview" } },
      ];
    }

    return {
      title,
      description,
      selectedTypeLabel,
      actions,
      metrics: {
        readyCount,
        missingCount,
        urgentMissingCount,
        currentTypeSummaryText,
      },
    };
  }

  function renderBeginnerAssetsGuidePanel(model = {}, helpers = {}) {
    const escapeHtml = getHelper(helpers, "escapeHtml", fallbackEscapeHtml);
    const renderQuickActionButton = getHelper(helpers, "renderQuickActionButton", fallbackActionButton);
    const renderRouteMetricCard = getHelper(helpers, "renderRouteMetricCard", fallbackMetricCard);
    const metrics = model.metrics ?? {};
    const actions = Array.isArray(model.actions) ? model.actions : [];

    return `
    <section class="detail-card beginner-guide-panel">
      <div class="panel-heading">
        <div>
          <h3>新手素材顺序</h3>
          <span class="panel-note">优先处理当前内容已经使用到的素材</span>
        </div>
        <span class="badge badge-soft">${escapeHtml(model.selectedTypeLabel ?? "素材")}</span>
      </div>
      <article class="beginner-guide-card beginner-guide-focus-card">
        <strong>${escapeHtml(model.title ?? "导入第一批素材")}</strong>
        <p>${escapeHtml(model.description ?? "")}</p>
        <div class="detail-actions">
          ${actions.map((action, index) => renderQuickActionButton(action, index === 0)).join("")}
        </div>
      </article>
      <div class="route-summary-strip beginner-guide-metrics">
        ${renderRouteMetricCard("已就绪", metrics.readyCount ?? 0, "已经能直接预览和导出的素材")}
        ${renderRouteMetricCard("待导入", metrics.missingCount ?? 0, "还没有真实文件的素材条目")}
        ${renderRouteMetricCard("已引用缺口", metrics.urgentMissingCount ?? 0, "当前优先处理的缺口")}
        ${renderRouteMetricCard("当前分类", model.selectedTypeLabel ?? "素材", metrics.currentTypeSummaryText ?? "这一类暂时还没有素材")}
      </div>
    </section>
  `;
  }

  global.CanvasiaEditorBeginnerAssetsGuide = Object.freeze({
    buildBeginnerAssetsGuideModel,
    renderBeginnerAssetsGuidePanel,
  });
})(typeof window !== "undefined" ? window : globalThis);
