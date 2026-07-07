(function attachProjectMilestonePanelTools(global) {
  const milestoneTools = global.CanvasiaEditorProjectMilestones ?? global.CanvasiaProjectMilestones ?? {};
  const commonTools = global.CanvasiaEditorCommon || {};

  function fallbackEscapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function getProjectMilestoneToneClass(tone) {
    if (tone === "danger") {
      return "danger-text";
    }
    if (tone === "warn") {
      return "warn-text";
    }
    if (tone === "good") {
      return "good-text";
    }
    return "soft-text";
  }

  function getProjectMilestoneGapToneClass(status) {
    if (status === "ready") {
      return "good-text";
    }
    if (status === "close") {
      return "warn-text";
    }
    return "danger-text";
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
              <article class="route-metric-card">
                <span>${escapeHtml(label)}</span>
                <strong>${escapeHtml(value)}</strong>
                ${hint ? `<small>${escapeHtml(hint)}</small>` : ""}
              </article>
            `,
      renderProjectMilestoneActions:
        typeof helpers.renderProjectMilestoneActions === "function"
          ? helpers.renderProjectMilestoneActions
          : (actions = []) =>
              (milestoneTools.renderProjectMilestoneActions
                ? milestoneTools.renderProjectMilestoneActions(actions, { escapeHtml, renderQuickActionButton })
                : actions.map((action, index) => renderQuickActionButton(action, index === 0)).join("")),
      renderProjectMilestoneChecklist:
        typeof helpers.renderProjectMilestoneChecklist === "function"
          ? helpers.renderProjectMilestoneChecklist
          : (checks = []) =>
              milestoneTools.renderProjectMilestoneChecklist
                ? milestoneTools.renderProjectMilestoneChecklist(checks, { escapeHtml })
                : "",
      renderProjectMilestoneGapList:
        typeof helpers.renderProjectMilestoneGapList === "function"
          ? helpers.renderProjectMilestoneGapList
          : (gaps = []) =>
              milestoneTools.renderProjectMilestoneGapList ? milestoneTools.renderProjectMilestoneGapList(gaps, { escapeHtml }) : "",
      buildDashboardProductionOverview:
        typeof helpers.buildDashboardProductionOverview === "function"
          ? helpers.buildDashboardProductionOverview
          : () => ({}),
      buildProjectMilestonePlan:
        typeof helpers.buildProjectMilestonePlan === "function"
          ? helpers.buildProjectMilestonePlan
          : milestoneTools.buildProjectMilestonePlan || (() => ({ milestones: [] })),
      buildProjectMilestoneActionBrief:
        typeof helpers.buildProjectMilestoneActionBrief === "function"
          ? helpers.buildProjectMilestoneActionBrief
          : milestoneTools.buildProjectMilestoneActionBrief || (() => ({})),
      buildProjectMilestoneGapDigest:
        typeof helpers.buildProjectMilestoneGapDigest === "function"
          ? helpers.buildProjectMilestoneGapDigest
          : milestoneTools.buildProjectMilestoneGapDigest || (() => ({})),
      formatProjectMilestonePrimaryBlocker:
        typeof helpers.formatProjectMilestonePrimaryBlocker === "function"
          ? helpers.formatProjectMilestonePrimaryBlocker
          : (milestone = {}) => milestone?.blockers?.[0]?.missing ?? "进入试玩确认手感",
    };
  }

  function renderDashboardActionBriefChecklist(items = [], helpers = {}) {
    const { escapeHtml } = getHelpers(helpers);
    if (!items.length) {
      return `
        <div class="creator-focus-checklist">
          <article class="creator-focus-check is-done">
            <strong>当前没有明显缺口</strong>
            <span>可以继续试玩、导出或进入人工验收。</span>
          </article>
        </div>
      `;
    }

    return `
      <div class="creator-focus-checklist">
        ${items
          .map(
            (item) => `
              <article class="creator-focus-check ${item.done ? "is-done" : ""}">
                <strong>${escapeHtml(item.label ?? "待处理项")}</strong>
                <span>${escapeHtml(item.detail ?? "继续补齐这个条件。")}</span>
              </article>
            `
          )
          .join("")}
      </div>
    `;
  }

  function renderDashboardActionBrief(routeOverview = {}, helpers = {}) {
    const resolved = getHelpers(helpers);
    const overview = resolved.buildDashboardProductionOverview(routeOverview);
    const plan = resolved.buildProjectMilestonePlan(routeOverview, overview);
    const brief = resolved.buildProjectMilestoneActionBrief(plan);
    const actions = [brief.primaryAction, ...(brief.secondaryActions ?? [])].filter(Boolean).slice(0, 3);
    const metrics = Array.isArray(brief.metrics) ? brief.metrics : [];

    return `
      <section class="panel creator-focus-panel is-${resolved.escapeHtml(brief.tone ?? brief.status ?? "soft")}">
        <div class="creator-focus-layout">
          <article class="creator-focus-main">
            <div class="creator-focus-head">
              <span class="eyebrow">${resolved.escapeHtml(brief.eyebrow ?? "今日工作台")}</span>
              <span class="badge badge-soft ${getProjectMilestoneToneClass(brief.tone)}">${resolved.escapeHtml(brief.badge ?? "下一步")}</span>
            </div>
            <h2>${resolved.escapeHtml(brief.title ?? "继续推进当前项目")}</h2>
            <p>${resolved.escapeHtml(brief.description ?? "按当前项目状态选择最短路径，做完后再回到巡检和试玩确认。")}</p>
            <div class="script-entry-actions">
              ${resolved.renderProjectMilestoneActions(actions)}
            </div>
          </article>
          <div class="creator-focus-side">
            <div class="route-summary-strip creator-focus-metrics">
              ${metrics.map((metric) => resolved.renderRouteMetricCard(metric.label, metric.value, metric.hint)).join("")}
            </div>
            ${renderDashboardActionBriefChecklist(brief.checklist, helpers)}
          </div>
        </div>
      </section>
    `;
  }

  function renderProjectMilestoneGapDigest(digest = {}, helpers = {}) {
    const resolved = getHelpers(helpers);
    const action = digest.nextAction ?? { label: "去试玩确认", action: "switch-screen", screen: "preview" };
    const actions = [
      action,
      { label: "打开项目巡检", action: "switch-screen", screen: "inspection" },
    ];

    return `
      <article class="project-milestone-gap-digest is-${resolved.escapeHtml(digest.status)}">
        <div class="project-milestone-gap-head">
          <div>
            <span class="eyebrow">${resolved.escapeHtml(digest.eyebrow ?? "发布候选差距")}</span>
            <strong>${resolved.escapeHtml(digest.title)}</strong>
          </div>
          <span class="issue-tag ${getProjectMilestoneGapToneClass(digest.status)}">${
            digest.status === "ready" ? "可人工验收" : `${digest.activePercent ?? digest.releasePercent}%`
          }</span>
        </div>
        <p>${resolved.escapeHtml(digest.description)}</p>
        <div class="route-summary-strip project-milestone-gap-metrics">
          ${resolved.renderRouteMetricCard("总进度", `${digest.overallScore}%`, `${digest.completedCount}/${digest.totalCount} 个阶段达标`)}
          ${resolved.renderRouteMetricCard(digest.gapMetricLabel ?? "候选缺口", `${digest.activeBlockerCount ?? digest.releaseBlockerCount} 项`, digest.gapMetricHint ?? "发布前建议清零")}
          ${resolved.renderRouteMetricCard("当前阶段", digest.nextMilestoneTitle, "先做当前阶段的第一步")}
        </div>
        ${resolved.renderProjectMilestoneGapList(digest.topGaps)}
        <div class="script-entry-actions">
          ${resolved.renderProjectMilestoneActions(actions)}
        </div>
      </article>
    `;
  }

  function renderProjectMilestoneCard(milestone = {}, options = {}, helpers = {}) {
    const resolved = getHelpers(helpers);
    const isFocus = options.focus === true;
    const toneClass = getProjectMilestoneToneClass(milestone.tone);
    const phaseLabel = options.index ? `阶段 ${options.index}` : milestone.label;

    return `
      <article class="project-milestone-card ${isFocus ? "is-focus" : ""} is-${resolved.escapeHtml(milestone.tone)}">
        <div class="project-milestone-card-head">
          <div>
            <span class="project-milestone-phase">${resolved.escapeHtml(phaseLabel)}</span>
            <strong>${resolved.escapeHtml(milestone.title)}</strong>
            <small>${resolved.escapeHtml(milestone.label)}</small>
          </div>
          <span class="issue-tag ${toneClass}">${milestone.done ? "已达标" : `${milestone.percent}%`}</span>
        </div>
        <p>${resolved.escapeHtml(milestone.summary)}</p>
        <div class="project-milestone-progress-head">
          <span>目标完成度</span>
          <strong>${milestone.percent}%</strong>
        </div>
        <div class="project-milestone-progress" aria-label="${resolved.escapeHtml(milestone.title)}完成度">
          <span style="width:${milestone.percent}%;"></span>
        </div>
        ${resolved.renderProjectMilestoneChecklist(milestone.checks)}
        <div class="script-entry-actions">
          ${resolved.renderProjectMilestoneActions(milestone.actions)}
        </div>
      </article>
    `;
  }

  function renderProjectMilestonePanel(routeOverview = {}, helpers = {}) {
    const resolved = getHelpers(helpers);
    const overview = resolved.buildDashboardProductionOverview(routeOverview);
    const plan = resolved.buildProjectMilestonePlan(routeOverview, overview);
    const focusMilestone = plan.nextMilestone ?? plan.milestones?.[0] ?? null;
    const secondaryMilestones = (plan.milestones ?? []).filter((milestone) => milestone.id !== focusMilestone?.id);

    if (!focusMilestone) {
      return "";
    }

    return `
      <section class="panel project-milestone-panel">
        <div class="panel-heading">
          <div>
            <h2>成品目标路线</h2>
            <span class="panel-note">把“下一步做什么”按 Demo、体验版、发布候选拆成可执行目标</span>
          </div>
          <span class="badge badge-soft">总进度 ${plan.overallScore}% · ${plan.completedCount}/${plan.totalCount}</span>
        </div>
        <div class="route-summary-strip">
          ${resolved.renderRouteMetricCard("当前目标", focusMilestone.title, plan.headline)}
          ${resolved.renderRouteMetricCard("下一步缺口", focusMilestone.blockers?.[0]?.missing ?? "进入试玩确认手感", focusMilestone.summary)}
          ${resolved.renderRouteMetricCard("已完成目标", `${plan.completedCount}/${plan.totalCount}`, "完成的阶段越多，越接近可公开发布")}
        </div>
        <div class="project-milestone-grid">
          ${renderProjectMilestoneCard(focusMilestone, { focus: true, index: (plan.milestones ?? []).findIndex((milestone) => milestone.id === focusMilestone.id) + 1 }, helpers)}
          <div class="project-milestone-stack">
            ${secondaryMilestones
              .map((milestone) =>
                renderProjectMilestoneCard(
                  milestone,
                  {
                    index: (plan.milestones ?? []).findIndex((item) => item.id === milestone.id) + 1,
                  },
                  helpers
                )
              )
              .join("")}
          </div>
        </div>
      </section>
    `;
  }

  function renderCompactProjectMilestonePanel(routeOverview = {}, helpers = {}) {
    const resolved = getHelpers(helpers);
    const overview = resolved.buildDashboardProductionOverview(routeOverview);
    const plan = resolved.buildProjectMilestonePlan(routeOverview, overview);
    const focusMilestone = plan.nextMilestone ?? plan.milestones?.[0] ?? null;
    const gapDigest = resolved.buildProjectMilestoneGapDigest(plan);

    if (!focusMilestone) {
      return "";
    }

    const milestoneActions = (focusMilestone.actions ?? []).length
      ? focusMilestone.actions
      : [{ label: "去试玩确认", action: "switch-screen", screen: "preview" }];
    const actions = [
      ...milestoneActions,
      { label: "回首页看完整路线", action: "switch-screen", screen: "dashboard" },
    ].slice(0, 3);
    const primaryBlocker = resolved.formatProjectMilestonePrimaryBlocker(focusMilestone);

    return `
      <article class="detail-card preview-sprint-panel project-milestone-compact-panel">
        <div class="preview-sprint-head">
          <div>
            <span class="eyebrow">成品目标路线</span>
            <strong>${resolved.escapeHtml(focusMilestone.title)}</strong>
          </div>
          <span class="issue-tag ${getProjectMilestoneToneClass(focusMilestone.tone)}">${
            focusMilestone.done ? "已达标" : `${focusMilestone.percent}%`
          }</span>
        </div>
        <p>${resolved.escapeHtml(plan.headline)}</p>
        <div class="preview-sprint-metrics">
          ${resolved.renderRouteMetricCard("下一步缺口", primaryBlocker, focusMilestone.summary)}
          ${resolved.renderRouteMetricCard("总进度", `${plan.overallScore}%`, `${plan.completedCount}/${plan.totalCount} 个阶段已达标`)}
          ${resolved.renderRouteMetricCard("当前阶段", focusMilestone.label, "按按钮继续推进，不需要手写配置")}
        </div>
        ${renderProjectMilestoneGapDigest(gapDigest, helpers)}
        <div class="script-entry-actions">
          ${resolved.renderProjectMilestoneActions(actions)}
        </div>
      </article>
    `;
  }

  global.CanvasiaEditorProjectMilestonePanel = Object.freeze({
    getProjectMilestoneToneClass,
    getProjectMilestoneGapToneClass,
    renderDashboardActionBriefChecklist,
    renderDashboardActionBrief,
    renderProjectMilestoneGapDigest,
    renderProjectMilestoneCard,
    renderProjectMilestonePanel,
    renderCompactProjectMilestonePanel,
  });
})(typeof window !== "undefined" ? window : globalThis);
