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
    const renderQuickActionButton =
      typeof helpers.renderQuickActionButton === "function" ? helpers.renderQuickActionButton : fallbackRenderQuickActionButton;
    const renderRouteMetricCard =
      typeof helpers.renderRouteMetricCard === "function"
        ? helpers.renderRouteMetricCard
        : (label, value, hint = "") => `
            <article class="preview-sprint-metric">
              <span>${escapeHtml(label)}</span>
              <strong>${escapeHtml(value)}</strong>
              ${hint ? `<small>${escapeHtml(hint)}</small>` : ""}
            </article>
          `;
    const renderProjectMilestoneActions =
      typeof helpers.renderProjectMilestoneActions === "function"
        ? helpers.renderProjectMilestoneActions
        : (actions = []) => actions.map((action, index) => renderQuickActionButton(action, index === 0)).join("");
    return {
      escapeHtml,
      renderQuickActionButton,
      renderRouteMetricCard,
      renderProjectMilestoneActions,
      getDashboardTaskToneClass:
        typeof helpers.getDashboardTaskToneClass === "function"
          ? helpers.getDashboardTaskToneClass
          : (tone) => (tone === "danger" ? "danger-text" : tone === "warn" ? "warn-text" : tone === "good" ? "good-text" : ""),
      buildReleaseChecklistItems:
        typeof helpers.buildReleaseChecklistItems === "function" ? helpers.buildReleaseChecklistItems : () => [],
      buildReleaseChecklistSummary:
        typeof helpers.buildReleaseChecklistSummary === "function"
          ? helpers.buildReleaseChecklistSummary
          : (items = []) => {
              const blockerCount = items.filter((item) => item.severity === "blocker").length;
              const warnCount = items.filter((item) => item.severity === "warn").length;
              const readyCount = items.filter((item) => item.severity === "good").length;
              return {
                toneClass: blockerCount ? "danger-text" : warnCount ? "warn-text" : "good-text",
                badge: blockerCount ? "先补阻塞项" : warnCount ? "基本可发" : "可以交付",
                title: blockerCount ? `当前还有 ${blockerCount} 个发布阻塞项` : "当前发布检查没有硬阻塞",
                description: blockerCount
                  ? "这几个问题最容易直接影响正式交付，处理完成后再打正式包会更稳。"
                  : "继续按清单完成最后确认即可。",
                metrics: [
                  ["阻塞项", `${blockerCount} 个`],
                  ["提醒项", `${warnCount} 个`],
                  ["已就绪", `${readyCount} 项`],
                ],
              };
            },
      buildReleaseFixOrder:
        typeof helpers.buildReleaseFixOrder === "function" ? helpers.buildReleaseFixOrder : () => ({ steps: [] }),
      buildFinalPublishGate:
        typeof helpers.buildFinalPublishGate === "function"
          ? helpers.buildFinalPublishGate
          : (items = [], releaseFixOrder = null) => {
              const blockerItems = items.filter((item) => item.severity === "blocker");
              const warnItems = items.filter((item) => item.severity === "warn");
              const status = blockerItems.length ? "blocked" : warnItems.length ? "preview" : "ready";
              return {
                status,
                tone: status === "blocked" ? "danger" : status === "preview" ? "warn" : "good",
                badge: status === "blocked" ? "暂缓发布" : status === "preview" ? "可发 Preview" : "可以公开发布",
                title: status === "blocked" ? `暂缓公开发布：还有 ${blockerItems.length} 个阻塞项` : "可以进入公开发布流程",
                description:
                  status === "blocked"
                    ? "这些问题可能造成断线、缺素材、包体异常或回归失败。"
                    : "当前发布检查比较干净，可以开始整理发布附件和发布说明。",
                metrics: [
                  { label: "阻塞", value: `${blockerItems.length} 个`, hint: "公开发布前建议清零" },
                  { label: "提醒", value: `${warnItems.length} 个`, hint: "Preview 可带说明发布" },
                  { label: "修复步骤", value: `${releaseFixOrder?.steps?.length ?? 0} 项`, hint: "来自发布前修复顺序" },
                ],
                checklist: (status === "blocked" ? blockerItems : warnItems).slice(0, 3).map((item) => ({
                  label: item.title,
                  detail: item.description,
                  done: false,
                  action: item.action,
                })),
              };
            },
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
      <article class="detail-card preview-sprint-panel" data-inspection-section="release-control">
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

  function renderFinalPublishGateChecklist(items = [], helpers = {}) {
    const { escapeHtml } = getHelperFunctions(helpers);
    if (!items.length) {
      return `
        <div class="project-milestone-gap-list final-publish-gate-list">
          <article class="project-milestone-gap-item is-done">
            <strong>关键发布门槛已达标</strong>
            <span>可以进入附件整理、发布说明和最后人工验收。</span>
          </article>
        </div>
      `;
    }

    return `
      <div class="project-milestone-gap-list final-publish-gate-list">
        ${items
          .map(
            (item) => `
              <article class="project-milestone-gap-item ${item.done ? "is-done" : ""}">
                <strong>${escapeHtml(item.label ?? "发布前待处理项")}</strong>
                <span>${escapeHtml(item.detail ?? "继续补齐这个发布门槛。")}</span>
              </article>
            `
          )
          .join("")}
      </div>
    `;
  }

  function renderFinalPublishGatePanel(routeOverview = {}, helpers = {}) {
    const resolved = getHelperFunctions(helpers);
    const releaseItems = resolved.buildReleaseChecklistItems();
    const releaseFixOrder = resolved.buildReleaseFixOrder(routeOverview);
    const gate = resolved.buildFinalPublishGate(releaseItems, releaseFixOrder, routeOverview);
    const actions = [gate.primaryAction, ...(gate.secondaryActions ?? [])].filter(Boolean).slice(0, 3);
    const toneClass = gate.tone === "danger" ? "danger-text" : gate.tone === "warn" ? "warn-text" : "good-text";

    return `
      <article class="detail-card preview-sprint-panel final-publish-gate is-${resolved.escapeHtml(gate.tone ?? "soft")}">
        <div class="preview-sprint-head">
          <div>
            <span class="eyebrow">最终发表门禁</span>
            <strong>${resolved.escapeHtml(gate.title ?? "发布前最终确认")}</strong>
          </div>
          <span class="issue-tag ${toneClass}">${resolved.escapeHtml(gate.badge ?? "待确认")}</span>
        </div>
        <p>${resolved.escapeHtml(gate.description ?? "按这里的结论完成最后发布前确认。")}</p>
        <div class="preview-sprint-metrics">
          ${(gate.metrics ?? []).map((metric) => resolved.renderRouteMetricCard(metric.label, metric.value, metric.hint)).join("")}
        </div>
        ${renderFinalPublishGateChecklist(gate.checklist, helpers)}
        <div class="script-entry-actions">
          ${resolved.renderProjectMilestoneActions(actions)}
        </div>
      </article>
    `;
  }

  function renderReleaseChecklistCard(item = {}, helpers = {}) {
    const { escapeHtml, renderQuickActionButton } = getHelperFunctions(helpers);
    return `
      <article class="issue-card">
        <span class="issue-tag ${escapeHtml(item.toneClass ?? "")}">${escapeHtml(item.status)}</span>
        <strong>${escapeHtml(item.title)}</strong>
        <div class="issue-meta">${escapeHtml(item.description)}</div>
        ${item.action ? `<div class="issue-card-footer">${renderQuickActionButton(item.action, true)}</div>` : ""}
      </article>
    `;
  }

  function renderReleaseChecklistPanel(helpers = {}) {
    const resolved = getHelperFunctions(helpers);
    const items = resolved.buildReleaseChecklistItems();
    const summary = resolved.buildReleaseChecklistSummary(items);
    return `
      <article class="detail-card preview-sprint-panel">
        <div class="panel-heading">
          <h2>发布检查清单</h2>
          <span class="badge badge-soft">导出前最后看一眼</span>
        </div>
        <p class="helper-text">这里会把最容易影响正式交付的检查项集中列出来，每一项都尽量给你一个马上可点的动作。</p>
        <div class="detail-actions">
          <button class="toolbar-button toolbar-button-primary" data-action="export-release-control-report">
            导出发布总控报告
          </button>
          <button class="toolbar-button toolbar-button-primary" data-action="export-release-evidence-pack">
            导出发布证据包
          </button>
          <button class="toolbar-button" data-action="export-release-control-json">
            导出 JSON 数据
          </button>
          <button class="toolbar-button" data-action="export-inspection-report">
            导出巡检报告
          </button>
        </div>
        <article class="preview-sprint-card is-soft">
          <div class="preview-sprint-head">
            <strong>${resolved.escapeHtml(summary.title)}</strong>
            <span class="issue-tag ${resolved.escapeHtml(summary.toneClass)}">${resolved.escapeHtml(summary.badge)}</span>
          </div>
          <p>${resolved.escapeHtml(summary.description)}</p>
          <div class="preview-sprint-metrics">
            ${(summary.metrics ?? [])
              .map((metric) => {
                const label = Array.isArray(metric) ? metric[0] : metric.label;
                const value = Array.isArray(metric) ? metric[1] : metric.value;
                return `
                  <article class="preview-sprint-metric">
                    <span>${resolved.escapeHtml(label)}</span>
                    <strong>${resolved.escapeHtml(value)}</strong>
                  </article>
                `;
              })
              .join("")}
          </div>
        </article>
        <div class="preview-sprint-grid">${items.map((item) => renderReleaseChecklistCard(item, helpers)).join("")}</div>
      </article>
    `;
  }

  global.CanvasiaEditorReleaseControlPanel = Object.freeze({
    renderReleaseRouteIssueQueue,
    renderReleaseProductionBacklogTask,
    renderReleaseNextActionCard,
    renderReleaseFixOrderStep,
    renderReleaseFixOrderPanel,
    renderFinalPublishGateChecklist,
    renderFinalPublishGatePanel,
    renderReleaseChecklistCard,
    renderReleaseChecklistPanel,
  });
})(typeof window !== "undefined" ? window : globalThis);
