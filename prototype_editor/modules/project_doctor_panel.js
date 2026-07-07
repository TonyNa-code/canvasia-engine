(function attachProjectDoctorPanelTools(global) {
  const commonTools = global.CanvasiaEditorCommon || {};

  function fallbackEscapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function getHelpers(helpers = {}) {
    const escapeHtml =
      typeof helpers.escapeHtml === "function" ? helpers.escapeHtml : commonTools.escapeHtml || fallbackEscapeHtml;
    const renderQuickActionButton =
      typeof helpers.renderQuickActionButton === "function"
        ? helpers.renderQuickActionButton
        : (action = {}, emphasized = false) => {
            const className = `toolbar-button${emphasized ? " toolbar-button-primary" : ""}`;
            const dataset = {
              ...(action.dataset ?? {}),
              ...(action.screen ? { screen: action.screen } : {}),
            };
            const datasetMarkup = Object.entries(dataset)
              .map(([key, value]) => ` data-${key}="${escapeHtml(value)}"`)
              .join("");
            return `<button type="button" class="${className}" data-action="${escapeHtml(action.action ?? "")}"${datasetMarkup}>${escapeHtml(action.label ?? "去处理")}</button>`;
          };

    return {
      escapeHtml,
      renderQuickActionButton,
      renderRouteMetricCard:
        typeof helpers.renderRouteMetricCard === "function"
          ? helpers.renderRouteMetricCard
          : (label, value, hint = "") => `
              <article class="preview-sprint-metric">
                <span>${escapeHtml(label)}</span>
                <strong>${escapeHtml(value)}</strong>
                ${hint ? `<small>${escapeHtml(hint)}</small>` : ""}
              </article>
            `,
      getDashboardTaskToneClass:
        typeof helpers.getDashboardTaskToneClass === "function"
          ? helpers.getDashboardTaskToneClass
          : (tone) => (tone === "danger" ? "danger-text" : tone === "warn" ? "warn-text" : tone === "good" ? "good-text" : ""),
      renderEmpty:
        typeof helpers.renderEmpty === "function"
          ? helpers.renderEmpty
          : (message) => `<div class="empty-note">${escapeHtml(message)}</div>`,
      renderProjectDoctorRepairReceiptPanel:
        typeof helpers.renderProjectDoctorRepairReceiptPanel === "function"
          ? helpers.renderProjectDoctorRepairReceiptPanel
          : () => "",
      buildProjectDoctorQueue:
        typeof helpers.buildProjectDoctorQueue === "function" ? helpers.buildProjectDoctorQueue : () => [],
      buildProjectDoctorSummary:
        typeof helpers.buildProjectDoctorSummary === "function"
          ? helpers.buildProjectDoctorSummary
          : (queue = []) => ({
              status: queue.length ? "soft" : "clean",
              badge: queue.length ? "整理收尾" : "很干净",
              title: queue.length ? `项目医生排出了 ${queue.length} 个优先步骤` : "项目医生没有发现需要优先处理的事项",
              description: queue.length ? "按这个顺序处理，通常更省时间。" : "当前可以继续试玩、补内容或导出一版做最终确认。",
              dangerCount: 0,
              warnCount: 0,
              softCount: queue.length,
              autoRepairableCount: 0,
            }),
      getCurrentProjectDoctorPreviewRepairCodes:
        typeof helpers.getCurrentProjectDoctorPreviewRepairCodes === "function"
          ? helpers.getCurrentProjectDoctorPreviewRepairCodes
          : () => [],
    };
  }

  function renderProjectDoctorStepCard(step = {}, helpers = {}) {
    const { escapeHtml, renderQuickActionButton, getDashboardTaskToneClass } = getHelpers(helpers);
    const toneClass = getDashboardTaskToneClass(step.tone);
    const actions = (step.actions ?? []).filter(Boolean).slice(0, 3);

    return `
      <article class="preview-sprint-card project-doctor-step is-${escapeHtml(step.tone ?? "soft")}">
        <div class="preview-sprint-head">
          <strong>第 ${Number(step.order ?? 0)} 步 · ${escapeHtml(step.title)}</strong>
          <span class="issue-tag ${toneClass}">${escapeHtml(step.badge ?? step.label ?? "处理")}</span>
        </div>
        <div class="detail-meta">${escapeHtml(`${step.label ?? "待处理"} · ${step.meta ?? "未标注位置"}`)}</div>
        <p>${escapeHtml(step.why ?? "这一步会影响试玩、导出或后续排查效率。")}</p>
        <div class="project-doctor-recovery">
          <strong>建议怎么修</strong>
          <span>${escapeHtml(step.recovery ?? "点开对应位置，按提示补内容、补引用或调整设置。")}</span>
        </div>
        ${
          step.diagnostic
            ? `<div class="project-doctor-diagnostic">
                <strong>条件/变量诊断</strong>
                <span>${escapeHtml(step.diagnostic)}</span>
              </div>`
            : ""
        }
        <div class="project-doctor-done">
          <strong>修完应该看到</strong>
          <span>${escapeHtml(step.doneWhen ?? "重新巡检后，这条问题会消失或变成可确认的提醒。")}</span>
        </div>
        <div class="preview-sprint-actions">
          ${actions.map((action, index) => renderQuickActionButton(action, index === 0)).join("")}
        </div>
      </article>
    `;
  }

  function renderProjectDoctorPanel(routeOverview = {}, issueItems = [], helpers = {}) {
    const resolved = getHelpers(helpers);
    const queue = resolved.buildProjectDoctorQueue(routeOverview, issueItems);
    const summary = resolved.buildProjectDoctorSummary(queue);
    const summaryTone = summary.status === "danger" ? "danger" : summary.status === "warn" ? "warn" : "soft";
    const previewRepairCodes = resolved.getCurrentProjectDoctorPreviewRepairCodes();
    const previewRepairDataset = previewRepairCodes.length
      ? ` data-repair-codes="${resolved.escapeHtml(previewRepairCodes.join(","))}"`
      : "";
    const confirmRepairDisabled = previewRepairCodes.length
      ? ""
      : ` disabled aria-disabled="true" title="${resolved.escapeHtml("先点“先预览安全修复”，确认预览结果后再执行")}"`;
    const confirmRepairLabel = previewRepairCodes.length ? "确认并执行预览的修复" : "预览后可执行修复";

    return `
      <article class="detail-card preview-sprint-panel project-doctor-panel">
        <div class="panel-heading">
          <h2>项目医生 / 小白修复向导</h2>
          <span class="badge badge-soft">把巡检结果变成可执行步骤</span>
        </div>
        <article class="preview-sprint-card is-${summaryTone}">
          <div class="preview-sprint-head">
            <strong>${resolved.escapeHtml(summary.title)}</strong>
            <span class="issue-tag ${resolved.getDashboardTaskToneClass(summaryTone)}">${resolved.escapeHtml(summary.badge)}</span>
          </div>
          <p>${resolved.escapeHtml(summary.description)}</p>
          <div class="preview-sprint-metrics">
            ${resolved.renderRouteMetricCard("硬阻塞", `${summary.dangerCount ?? 0} 个`, "优先清掉")}
            ${resolved.renderRouteMetricCard("建议复看", `${summary.warnCount ?? 0} 个`, "发布前处理")}
            ${resolved.renderRouteMetricCard("整理项", `${summary.softCount ?? 0} 个`, "收尾时清理")}
            ${resolved.renderRouteMetricCard("可安全修复", `${summary.autoRepairableCount ?? 0} 项`, "先预览再确认")}
          </div>
        </article>
        <div class="detail-actions">
          <button class="toolbar-button toolbar-button-primary" data-action="preview-project-doctor-repair">
            先预览安全修复
          </button>
          <button class="toolbar-button" data-action="repair-project-doctor"${previewRepairDataset}${confirmRepairDisabled}>
            ${resolved.escapeHtml(confirmRepairLabel)}
          </button>
          <button class="toolbar-button toolbar-button-primary" data-action="run-project-inspection">
            重新巡检并刷新队列
          </button>
          <button class="toolbar-button" data-action="run-preview-regression">
            跑自动回归后再排序
          </button>
          <button class="toolbar-button" data-action="export-inspection-report">
            导出给测试人员
          </button>
        </div>
        ${resolved.renderProjectDoctorRepairReceiptPanel()}
        ${
          queue.length > 0
            ? `<div class="preview-sprint-grid">${queue.map((step) => renderProjectDoctorStepCard(step, helpers)).join("")}</div>`
            : resolved.renderEmpty("项目医生暂时没有排出修复队列。可以继续写剧情、试玩，或导出一版做最终确认。")
        }
      </article>
    `;
  }

  global.CanvasiaEditorProjectDoctorPanel = Object.freeze({
    renderProjectDoctorStepCard,
    renderProjectDoctorPanel,
  });
})(typeof window !== "undefined" ? window : globalThis);
