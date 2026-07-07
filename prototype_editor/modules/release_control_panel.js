(function attachReleaseControlPanelTools(global) {
  const commonTools = global.CanvasiaEditorCommon || {};

  function fallbackEscapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  const fallbackRenderQuickActionButton =
    commonTools.renderQuickActionButton ||
    ((action = {}, emphasized = false) => {
      const className = `toolbar-button${emphasized ? " toolbar-button-primary" : ""}`;
      const dataset = {
        ...(action.dataset ?? {}),
        ...(action.screen ? { screen: action.screen } : {}),
      };
      const datasetMarkup = Object.entries(dataset)
        .map(([key, value]) => ` data-${key}="${fallbackEscapeHtml(value)}"`)
        .join("");
      return `
        <button type="button" class="${className}" data-action="${fallbackEscapeHtml(action.action ?? "")}"${datasetMarkup}>
          ${fallbackEscapeHtml(action.label ?? "继续")}
        </button>
      `;
    });

  function getHelperFunctions(helpers = {}) {
    const escapeHtml = typeof helpers.escapeHtml === "function" ? helpers.escapeHtml : commonTools.escapeHtml || fallbackEscapeHtml;
    return {
      escapeHtml,
      renderQuickActionButton:
        typeof helpers.renderQuickActionButton === "function" ? helpers.renderQuickActionButton : fallbackRenderQuickActionButton,
      getDashboardTaskToneClass:
        typeof helpers.getDashboardTaskToneClass === "function"
          ? helpers.getDashboardTaskToneClass
          : (tone) => (tone === "danger" ? "danger-text" : tone === "warn" ? "warn-text" : tone === "good" ? "good-text" : ""),
      buildReleaseFixOrder:
        typeof helpers.buildReleaseFixOrder === "function" ? helpers.buildReleaseFixOrder : () => ({ steps: [] }),
      buildProjectMilestonePlan:
        typeof helpers.buildProjectMilestonePlan === "function" ? helpers.buildProjectMilestonePlan : () => ({}),
      buildProjectMilestoneGapDigest:
        typeof helpers.buildProjectMilestoneGapDigest === "function"
          ? helpers.buildProjectMilestoneGapDigest
          : () => ({ status: "ready" }),
      buildReleaseReportNextStep:
        typeof helpers.buildReleaseReportNextStep === "function"
          ? helpers.buildReleaseReportNextStep
          : () => ({ source: "release_ready" }),
      buildReleaseNextActionCard:
        typeof helpers.buildReleaseNextActionCard === "function"
          ? helpers.buildReleaseNextActionCard
          : () => ({
              tone: "good",
              sourceLabel: "最终确认",
              title: "现在可以做最终试玩和正式导出",
              badge: "可以进入最终确认",
              description: "当前没有明显阻塞，可以直接做最终试玩和正式导出。",
              verification: "先做最终人工试玩，再导出 Web / 原生 Runtime / 桌面包并整理发布附件。",
            }),
    };
  }

  function renderReleaseRouteIssueQueue(routeIssueQueue = [], helpers = {}) {
    const { escapeHtml } = getHelperFunctions(helpers);
    const issues = (routeIssueQueue ?? []).slice(0, 4);
    if (!issues.length) {
      return "";
    }

    return `
      <div class="project-doctor-recovery">
        <strong>具体路线问题</strong>
        <span>
          ${issues
            .map((issue, index) => {
              const issueLabel = [issue.sceneName, issue.routeLabel, issue.targetLabel]
                .filter(Boolean)
                .join(" / ");
              return `${index + 1}. ${escapeHtml(issue.title ?? "路线待处理")}：${escapeHtml(issueLabel || issue.statusLabel || "未标注位置")}`;
            })
            .join("<br>")}
        </span>
      </div>
    `;
  }

  function renderReleaseProductionBacklogTask(task = null, helpers = {}) {
    const { escapeHtml } = getHelperFunctions(helpers);
    if (!task) {
      return "";
    }
    const meta = [task.areaLabel, task.source, task.severityLabel].filter(Boolean).join(" · ");
    const actionLabel = task.action?.label ? `建议动作：${task.action.label}` : "";
    return `
      <div class="project-doctor-recovery">
        <strong>生产待办下一项</strong>
        <span>
          ${escapeHtml(task.title ?? "生产待办")}
          ${meta ? `<br>${escapeHtml(meta)}` : ""}
          ${task.detail ? `<br>${escapeHtml(task.detail)}` : ""}
          ${actionLabel ? `<br>${escapeHtml(actionLabel)}` : ""}
        </span>
      </div>
    `;
  }

  function renderReleaseNextActionCard(card = {}, helpers = {}) {
    const { escapeHtml, renderQuickActionButton, getDashboardTaskToneClass } = getHelperFunctions(helpers);
    const tone = card.tone ?? "soft";
    const actions = card.action ? [card.action] : [];
    return `
      <article class="preview-sprint-card is-${escapeHtml(tone)}">
        <div class="preview-sprint-head">
          <div>
            <span class="eyebrow">${escapeHtml(card.sourceLabel ?? "当前下一步")}</span>
            <strong>${escapeHtml(card.title ?? "继续发布前收尾")}</strong>
          </div>
          <span class="issue-tag ${getDashboardTaskToneClass(tone)}">${escapeHtml(card.badge ?? "下一步")}</span>
        </div>
        <p>${escapeHtml(card.description ?? "完成这一步后，再回到发布总控复查。")}</p>
        <div class="project-doctor-recovery">
          <strong>完成后验证</strong>
          <span>${escapeHtml(card.verification ?? "重新巡检、试玩并导出发布总控报告。")}</span>
        </div>
        ${
          actions.length
            ? `<div class="preview-sprint-actions">${actions.map((action, index) => renderQuickActionButton(action, index === 0)).join("")}</div>`
            : ""
        }
      </article>
    `;
  }

  function renderReleaseFixOrderStep(step, index, helpers = {}) {
    const { escapeHtml, renderQuickActionButton, getDashboardTaskToneClass } = getHelperFunctions(helpers);
    return `
      <article class="preview-sprint-card is-${escapeHtml(step?.tone ?? "soft")}">
        <div class="preview-sprint-head">
          <strong>第 ${index + 1} 步 · ${escapeHtml(step?.title ?? "发布前收尾")}</strong>
          <span class="issue-tag ${getDashboardTaskToneClass(step?.tone)}">${escapeHtml(step?.statusLabel ?? "待确认")}</span>
        </div>
        <p>${escapeHtml(step?.description ?? "继续完成这一步。")}</p>
        ${renderReleaseRouteIssueQueue(step?.routeIssueQueue, helpers)}
        ${renderReleaseProductionBacklogTask(step?.productionBacklogTask, helpers)}
        <div class="preview-sprint-actions">
          ${(step?.actions ?? []).map((action, actionIndex) => renderQuickActionButton(action, actionIndex === 0)).join("")}
        </div>
      </article>
    `;
  }

  function renderReleaseFixOrderPanel(routeOverview = {}, helpers = {}) {
    const resolved = getHelperFunctions(helpers);
    const plan = resolved.buildReleaseFixOrder(routeOverview);
    const projectMilestonePlan = resolved.buildProjectMilestonePlan(routeOverview);
    const projectMilestoneGapDigest = resolved.buildProjectMilestoneGapDigest(projectMilestonePlan);
    const nextStep = resolved.buildReleaseReportNextStep(plan, projectMilestoneGapDigest);
    const nextActionCard = resolved.buildReleaseNextActionCard(nextStep);

    return `
      <article class="detail-card preview-sprint-panel">
        <div class="panel-heading">
          <h2>发布前修复顺序</h2>
          <span class="badge badge-soft">按这个顺序做最省力</span>
        </div>
        <p class="helper-text">这里会把现在最值得先做的修复动作排成一条顺序，尽量避免你东补一点、西补一点，结果最后还得返工。</p>
        <div class="detail-actions">
          <button class="toolbar-button toolbar-button-primary" data-action="generate-release-fix-order">
            一键生成修复顺序
          </button>
          <button class="toolbar-button" data-action="export-release-control-report">
            导出发布总控报告
          </button>
          <button class="toolbar-button toolbar-button-primary" data-action="export-release-evidence-pack">
            导出发布证据包
          </button>
          <button class="toolbar-button" data-action="export-release-control-json">
            导出 JSON 数据
          </button>
          <button class="toolbar-button" data-action="export-inspection-report">
            导出带修复顺序的巡检报告
          </button>
        </div>
        <div class="preview-sprint-grid">
          ${renderReleaseNextActionCard(nextActionCard, helpers)}
          ${(plan.steps ?? []).map((step, index) => renderReleaseFixOrderStep(step, index, helpers)).join("")}
        </div>
        ${(plan.steps ?? []).length > 0 ? "" : '<p class="helper-text">当前没有明显阻塞，已经接近可以直接做最终试玩和正式导出。</p>'}
      </article>
    `;
  }

  global.CanvasiaEditorReleaseControlPanel = Object.freeze({
    renderReleaseRouteIssueQueue,
    renderReleaseProductionBacklogTask,
    renderReleaseNextActionCard,
    renderReleaseFixOrderStep,
    renderReleaseFixOrderPanel,
  });
})(typeof window !== "undefined" ? window : globalThis);
