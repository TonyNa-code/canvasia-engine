(function attachStageDirectionSheetPanelTools(global) {
  const commonTools = global.CanvasiaEditorCommon || {};
  const stageDirectionSheetTools = global.CanvasiaEditorStageDirectionSheet || {};

  function fallbackEscapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  const escapeHtml = commonTools.escapeHtml || fallbackEscapeHtml;
  const renderRouteMetricCard =
    commonTools.renderRouteMetricCard ||
    ((label, value, hint) => `
      <article class="route-metric-card">
        <span>${escapeHtml(label)}</span>
        <strong>${escapeHtml(String(value))}</strong>
        <small>${escapeHtml(hint)}</small>
      </article>
    `);
  const renderEmpty = commonTools.renderEmpty || ((text) => `<div class="empty-note">${escapeHtml(text)}</div>`);

  function toArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function getStageDirectionSheetToneClass(status) {
    if (status === "blocked") {
      return "danger-text";
    }
    if (status === "warn") {
      return "warn-text";
    }
    if (status === "ready") {
      return "good-text";
    }
    return "";
  }

  function getStageDirectionSheetDigest(sheet = {}) {
    if (typeof stageDirectionSheetTools.getStageDirectionStatusDigest === "function") {
      return stageDirectionSheetTools.getStageDirectionStatusDigest(sheet);
    }
    return {
      status: "empty",
      title: "还没有舞台调度",
      detail: "项目里暂时没有背景、角色登场或说话人调度。",
    };
  }

  function getStageDirectionAutoFixPlan(sheet = {}) {
    return sheet.autoFixPlan && typeof sheet.autoFixPlan === "object"
      ? sheet.autoFixPlan
      : {
          changed: false,
          changedSceneCount: 0,
          changedBlockCount: 0,
          operationCount: 0,
          scenePlans: [],
          summary: "角色舞台基础参数已经比较完整",
        };
  }

  function renderStageDirectionAutoFixButton(sheet = {}) {
    const plan = getStageDirectionAutoFixPlan(sheet);
    const label = plan.changed ? `补齐 ${plan.operationCount ?? 0} 个舞台参数` : "舞台基础参数已完整";
    const title = plan.changed
      ? `会处理 ${plan.changedSceneCount ?? 0} 个场景、${plan.changedBlockCount ?? 0} 张角色卡。`
      : "角色登场/退场的基础舞台参数已经比较完整。";
    return `
      <button
        class="toolbar-button"
        data-action="apply-stage-direction-autofix"
        title="${escapeHtml(title)}"
        ${plan.changed ? "" : 'disabled aria-disabled="true"'}
      >
        ${escapeHtml(label)}
      </button>
    `;
  }

  function getStageAutoFixOperationRows(plan = {}, limit = 6) {
    const rows = [];
    toArray(plan.scenePlans).forEach((scenePlan) => {
      toArray(scenePlan.operations).forEach((operation) => {
        rows.push({
          sceneName: scenePlan.sceneName ?? "未命名场景",
          chapterName: scenePlan.chapterName ?? "未分章",
          blockIndex: operation.blockIndex,
          label: operation.label ?? "补齐舞台参数",
          detail: operation.detail ?? "会补齐角色登场/退场的基础演出参数。",
        });
      });
    });
    return rows.slice(0, Math.max(0, Number(limit) || 0));
  }

  function renderStageAutoFixOperationRow(row = {}) {
    const blockLabel = Number.isFinite(Number(row.blockIndex)) ? `第 ${Number(row.blockIndex) + 1} 张` : "目标卡片";
    return `
      <div class="route-testing-item">
        <div>
          <b>${escapeHtml(`${row.label ?? "补齐舞台参数"} · ${row.sceneName ?? "未命名场景"}`)}</b>
          <span>${escapeHtml(`${row.chapterName ?? "未分章"} · ${blockLabel}`)}</span>
        </div>
        <span>${escapeHtml(row.detail ?? "会补齐角色登场/退场的基础演出参数。")}</span>
      </div>
    `;
  }

  function renderStageDirectionAutoFixPreview(sheet = {}) {
    const plan = getStageDirectionAutoFixPlan(sheet);
    if (!plan.changed) {
      return "";
    }
    const rows = getStageAutoFixOperationRows(plan, 6);
    return `
      <section class="preview-sprint-section">
        <div class="panel-heading panel-heading-compact">
          <h3>自动补齐预览</h3>
          <span class="badge badge-soft">${escapeHtml(`${plan.changedSceneCount ?? 0} 场 / ${plan.operationCount ?? 0} 项`)}</span>
        </div>
        <p class="helper-text">${escapeHtml(plan.summary ?? "会补齐角色登场、退场和舞台基础参数，不会替你删除素材或改台词。")}</p>
        <div class="list-stack compact-stack">
          ${rows.map(renderStageAutoFixOperationRow).join("")}
        </div>
      </section>
    `;
  }

  function renderStageContinuityPreview(continuityAudit = {}) {
    const rows = toArray(continuityAudit.reviewRows).slice(0, 3);
    if (!rows.length) {
      return "";
    }
    return `
      <div class="list-stack compact-stack">
        ${rows
          .map(
            (row) => `
              <div class="route-testing-item">
                <div>
                  <b>${escapeHtml(`${row.sceneName} · ${row.nextAction}`)}</b>
                  <span>${escapeHtml(`${row.chapterName} · ${row.reason}`)}</span>
                </div>
                <span>${escapeHtml(row.endingCastLabel ? `结尾在场：${row.endingCastLabel}` : row.openingCue)}</span>
              </div>
            `
          )
          .join("")}
      </div>
    `;
  }

  function renderStageDirectionIssueCard(issue = {}) {
    const severityClass = issue.severity === "blocker" ? "danger" : issue.severity === "warn" ? "warn" : "soft";
    const toneClass = issue.severity === "blocker" ? "danger-text" : issue.severity === "warn" ? "warn-text" : "";
    const severityLabel = issue.severity === "blocker" ? "先修" : issue.severity === "warn" ? "复查" : "润色";
    return `
      <article class="preview-sprint-card is-${severityClass}">
        <div class="preview-sprint-head">
          <strong>${escapeHtml(issue.title)}</strong>
          <span class="issue-tag ${toneClass}">${escapeHtml(severityLabel)}</span>
        </div>
        <p>${escapeHtml(`${issue.chapterName ?? "未分章"} · ${issue.sceneName ?? "未命名场景"}`)}</p>
        <div class="helper-text">${escapeHtml(issue.detail ?? "")}</div>
      </article>
    `;
  }

  function renderStageDirectionEventRow(event = {}) {
    return `
      <div class="route-testing-item">
        <div>
          <b>${escapeHtml(`${event.typeLabel}${event.characterName ? ` · ${event.characterName}` : ""}`)}</b>
          <span>${escapeHtml(`${event.chapterName ?? "未分章"} · ${event.sceneName ?? "未命名场景"} · ${event.positionLabel || event.assetStatusLabel || "舞台事件"}`)}</span>
        </div>
        <span>${escapeHtml(event.cue ?? "")}</span>
      </div>
    `;
  }

  function renderStageDirectionMainPreview(sheet = {}) {
    const topIssues = toArray(sheet.issues).slice(0, 4);
    const eventPreview = toArray(sheet.events).slice(0, 4);
    if (topIssues.length > 0) {
      return `
        <div class="preview-sprint-grid">
          ${topIssues.map(renderStageDirectionIssueCard).join("")}
        </div>
      `;
    }
    if (eventPreview.length > 0) {
      return `
        <div class="list-stack compact-stack">
          ${eventPreview.map(renderStageDirectionEventRow).join("")}
        </div>
      `;
    }
    return renderEmpty("当前项目还没有可列出的角色舞台事件。可以先在剧情页添加背景、角色登场和台词。");
  }

  function getStageContinuityAudit(sheet = {}) {
    if (sheet.continuityAudit && typeof sheet.continuityAudit === "object") {
      return sheet.continuityAudit;
    }
    if (typeof stageDirectionSheetTools.buildStageContinuityAudit === "function") {
      return stageDirectionSheetTools.buildStageContinuityAudit(sheet);
    }
    return { summary: {}, reviewRows: [] };
  }

  function renderStageDirectionSheetPanel(sheet = {}) {
    const digest = getStageDirectionSheetDigest(sheet);
    const summary = sheet.summary ?? {};
    const continuityAudit = getStageContinuityAudit(sheet);
    const continuitySummary = continuityAudit.summary ?? {};

    return `
      <article class="detail-card preview-sprint-panel" data-inspection-section="stage-direction">
        <div class="panel-heading">
          <h2>角色舞台调度表</h2>
          <span class="badge badge-soft ${getStageDirectionSheetToneClass(digest.status)}">${escapeHtml(digest.title)}</span>
        </div>
        <p class="helper-text">${escapeHtml(digest.detail)} 它会检查背景、角色登场 / 退场、说话人是否提前上场、表情和立绘是否可用。</p>
        <div class="preview-sprint-metrics">
          ${renderRouteMetricCard("舞台事件", `${summary.eventCount ?? 0} 个`, "背景、登场、退场和说话")}
          ${renderRouteMetricCard("自动补位", `${summary.speakerAutoPlaceCount ?? 0} 句`, "说话人未提前登场")}
          ${renderRouteMetricCard("立绘 / 表情缺口", `${summary.missingVisualCount ?? 0} 个`, "缺立绘、缺文件或坏表情")}
          ${renderRouteMetricCard("构图风险", `${summary.compositionRiskCount ?? 0} 处`, "遮挡、拥挤、图层或透明度")}
          ${renderRouteMetricCard("连续性复查", `${summary.continuityReviewSceneCount ?? 0} 场`, "开场调度和结尾留场")}
          ${renderRouteMetricCard("结尾仍在场", `${continuitySummary.endingCastSceneCount ?? 0} 场`, "确认是否需要退场或转场")}
          ${renderRouteMetricCard("说话人过淡", `${summary.lowOpacitySpeakerCount ?? 0} 处`, "台词角色不够清晰")}
          ${renderRouteMetricCard("无背景场景", `${summary.missingBackgroundSceneCount ?? 0} 个`, "有内容但没有明确背景")}
          ${renderRouteMetricCard("可自动补齐", `${summary.autoFixOperationCount ?? 0} 项`, "硬切、缺时长、缺舞台参数")}
        </div>
        <div class="detail-actions">
          <button class="toolbar-button toolbar-button-primary" data-action="export-stage-direction-sheet-markdown">
            导出角色舞台调度表
          </button>
          <button class="toolbar-button" data-action="export-stage-direction-sheet-csv">
            导出舞台调度 CSV
          </button>
          ${renderStageDirectionAutoFixButton(sheet)}
          <button class="toolbar-button" data-action="switch-screen" data-screen="story">
            去剧情页调整登场
          </button>
        </div>
        ${renderStageDirectionAutoFixPreview(sheet)}
        ${renderStageContinuityPreview(continuityAudit)}
        ${renderStageDirectionMainPreview(sheet)}
      </article>
    `;
  }

  global.CanvasiaEditorStageDirectionSheetPanel = Object.freeze({
    getStageDirectionSheetToneClass,
    getStageDirectionSheetDigest,
    getStageDirectionAutoFixPlan,
    getStageAutoFixOperationRows,
    renderStageDirectionAutoFixButton,
    renderStageAutoFixOperationRow,
    renderStageDirectionAutoFixPreview,
    renderStageContinuityPreview,
    renderStageDirectionIssueCard,
    renderStageDirectionEventRow,
    renderStageDirectionMainPreview,
    renderStageDirectionSheetPanel,
  });
})(typeof window !== "undefined" ? window : globalThis);
