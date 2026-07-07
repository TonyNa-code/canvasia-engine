(function attachProjectPolishReceiptPanelTools(global) {
  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function normalizeProjectOneClickPolishNextAction(action, index = 0) {
    if (typeof action === "string") {
      return {
        label: action,
        action: index === 0 ? "run-project-inspection" : "switch-screen",
        screen: index === 0 ? undefined : "preview",
        detail: action,
      };
    }
    if (!action || typeof action !== "object") {
      return null;
    }
    return action;
  }

  function renderFallbackRouteMetricCard(label, value, hint) {
    return `
      <article class="route-metric-card">
        <span>${escapeHtml(label)}</span>
        <strong>${escapeHtml(value)}</strong>
        <small>${escapeHtml(hint)}</small>
      </article>
    `;
  }

  function renderFallbackQuickActionButton(action = {}, emphasized = false) {
    const className = `toolbar-button${emphasized ? " toolbar-button-primary" : ""}`;
    const label = escapeHtml(action.label ?? "继续确认");
    const dataset = {
      ...(action.dataset ?? {}),
      ...(action.screen ? { screen: action.screen } : {}),
    };
    const datasetMarkup = Object.entries(dataset)
      .map(([key, value]) => ` data-${key}="${escapeHtml(value)}"`)
      .join("");
    return `
      <button type="button" class="${className}" data-action="${escapeHtml(action.action ?? "")}"${datasetMarkup}>
        ${label}
      </button>
    `;
  }

  function renderProjectOneClickPolishReceiptPanel(receipt = null, helpers = {}) {
    if (!receipt) {
      return "";
    }

    const html = typeof helpers.escapeHtml === "function" ? helpers.escapeHtml : escapeHtml;
    const renderMetric =
      typeof helpers.renderRouteMetricCard === "function" ? helpers.renderRouteMetricCard : renderFallbackRouteMetricCard;
    const renderAction =
      typeof helpers.renderQuickActionButton === "function" ? helpers.renderQuickActionButton : renderFallbackQuickActionButton;
    const scenePlans = Array.isArray(receipt.scenePlans) ? receipt.scenePlans : [];
    const projectOperationCount = Math.max(0, Number(receipt.projectOperationCount) || 0);
    const projectOperations = Array.isArray(receipt.projectOperations) ? receipt.projectOperations.slice(0, 4) : [];
    const pacingSnapshot = receipt.pacingSnapshot && typeof receipt.pacingSnapshot === "object" ? receipt.pacingSnapshot : null;
    const pacingHighlights = Array.isArray(pacingSnapshot?.sceneHighlights) ? pacingSnapshot.sceneHighlights.slice(0, 3) : [];
    const visibleScenes = scenePlans.slice(0, 4);
    const hiddenSceneCount = Math.max(0, scenePlans.length - visibleScenes.length);
    const nextActions = Array.isArray(receipt.nextActions)
      ? receipt.nextActions.map(normalizeProjectOneClickPolishNextAction).filter(Boolean).slice(0, 3)
      : [];
    const sceneListMarkup = visibleScenes.length
      ? visibleScenes
          .map(
            (scenePlan) => `
              <article class="project-doctor-receipt-item project-one-click-polish-scene">
                <strong>${html(scenePlan.sceneName || scenePlan.sceneId || "未命名场景")}</strong>
                <span>${html(
                  `长文本 ${scenePlan.readableSplitCount ?? 0} / 新增 ${
                    scenePlan.readableAddedBlockCount ?? 0
                  }，演出 ${scenePlan.presentationChangedFieldCount ?? 0}，音频 ${scenePlan.audioOperationCount ?? 0}`
                )}</span>
              </article>
            `
          )
          .join("")
      : '<div class="empty-note">这次没有可列出的场景明细。</div>';
    const overflowMarkup =
      hiddenSceneCount > 0
        ? `
          <article class="project-doctor-receipt-item project-one-click-polish-scene">
            <strong>还有 ${hiddenSceneCount} 个场景</strong>
            <span>导出完整回执可以看到全部处理明细。</span>
          </article>
        `
        : "";
    const projectOperationMarkup = projectOperations.length
      ? projectOperations
          .map(
            (operation) => `
              <article class="project-doctor-receipt-item project-one-click-polish-scene">
                <strong>${html(operation.label || operation.field || "项目设置")}</strong>
                <span>${html(operation.detail || "已补齐一项发布前安全默认值。")}</span>
              </article>
            `
          )
          .join("")
      : projectOperationCount > 0
        ? `
          <article class="project-doctor-receipt-item project-one-click-polish-scene">
            <strong>项目级设置 ${projectOperationCount} 项</strong>
            <span>导出完整回执可以看到全部项目级补全明细。</span>
          </article>
        `
        : '<div class="empty-note">这次没有项目级设置补全。</div>';
    const pacingMarkup = pacingHighlights.length
      ? pacingHighlights
          .map(
            (scene) => `
              <article class="project-doctor-receipt-item project-one-click-polish-scene">
                <strong>${html(scene.sceneName || scene.sceneId || "未命名场景")} · ${html(scene.gradeLabel || "待打磨")}</strong>
                <span>${html(scene.issueSummary || scene.headline || scene.actionSummary || "建议试玩复看。")}</span>
              </article>
            `
          )
          .join("")
      : pacingSnapshot
        ? '<div class="empty-note">节奏体检没有发现需要优先复看的场景。</div>'
        : '<div class="empty-note">本次没有启用节奏体检。</div>';

    return `
      <section class="panel project-one-click-polish-receipt-panel">
        <div class="panel-heading">
          <h2>最近发布前整理</h2>
          <span class="badge badge-soft good-text">已生成回执</span>
        </div>
        <article class="preview-sprint-card project-one-click-polish-receipt is-good">
          <div class="preview-sprint-head">
            <strong>${html(receipt.summary || "发布前整理完成")}</strong>
            <span class="issue-tag good-text">${html(receipt.receiptId || "polish-receipt")}</span>
          </div>
          <p>${
            receipt.safetySnapshotLabel
              ? `已先创建安全检查点「${html(receipt.safetySnapshotLabel)}」，不满意可以从项目历史里回退。`
              : "建议整理后立即巡检并试玩一遍，确认发布前体验没有回退。"
          }</p>
          <div class="preview-sprint-metrics">
            ${renderMetric("涉及场景", `${receipt.changedSceneCount ?? scenePlans.length} 个`, "本次自动整理范围")}
            ${renderMetric("总处理项", `${receipt.totalOperationCount ?? 0} 项`, "长文本 / 演出 / 音频 / 设置")}
            ${renderMetric("长文本", `${receipt.readableSplitCount ?? 0} 处`, `新增 ${receipt.readableAddedBlockCount ?? 0} 张卡片`)}
            ${renderMetric("演出与音频", `${receipt.presentationChangedFieldCount ?? 0} / ${receipt.audioOperationCount ?? 0}`, "演出参数 / 音频参数")}
            ${renderMetric("项目设置", `${projectOperationCount} 项`, "存档 / 文本框 / UI")}
            ${renderMetric(
              "节奏体检",
              receipt.pacingAverageScore === null || typeof receipt.pacingAverageScore === "undefined"
                ? "未启用"
                : `${receipt.pacingAverageScore} 分`,
              pacingSnapshot
                ? `待打磨 ${receipt.pacingRoughSceneCount ?? 0} / 可试玩 ${receipt.pacingReadySceneCount ?? 0}`
                : "可在完整打磨中启用"
            )}
          </div>
          <div class="preview-sprint-actions project-one-click-polish-actions">
            ${nextActions.map((action, index) => renderAction(action, index === 0)).join("")}
            <button class="toolbar-button" data-action="copy-project-one-click-polish-receipt-summary">
              复制摘要
            </button>
          </div>
          <div class="project-doctor-receipt-columns project-one-click-polish-columns">
            <div>
              <strong class="project-doctor-receipt-heading">处理过的场景</strong>
              <div class="project-doctor-receipt-list">
                ${sceneListMarkup}
                ${overflowMarkup}
              </div>
            </div>
            <div>
              <strong class="project-doctor-receipt-heading">项目级补全</strong>
              <div class="project-doctor-receipt-list">
                ${projectOperationMarkup}
              </div>
            </div>
            <div>
              <strong class="project-doctor-receipt-heading">建议下一步</strong>
              <div class="project-doctor-receipt-list">
                ${
                  nextActions.length
                    ? nextActions
                        .map(
                          (action) => `
                            <article class="project-doctor-receipt-item">
                              <strong>${html(action.label ?? "继续确认")}</strong>
                              <span>${html(action.detail ?? "按顺序确认发布前状态。")}</span>
                            </article>
                          `
                        )
                        .join("")
                    : '<div class="empty-note">打开项目巡检并重新试玩一遍。</div>'
                }
              </div>
            </div>
            <div>
              <strong class="project-doctor-receipt-heading">节奏复看</strong>
              <div class="project-doctor-receipt-list">
                ${pacingMarkup}
              </div>
            </div>
          </div>
        </article>
      </section>
    `;
  }

  global.CanvasiaEditorProjectPolishReceiptPanel = Object.freeze({
    normalizeProjectOneClickPolishNextAction,
    renderProjectOneClickPolishReceiptPanel,
  });
})(typeof window !== "undefined" ? window : globalThis);
