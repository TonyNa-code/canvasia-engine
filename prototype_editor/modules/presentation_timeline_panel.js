(function attachPresentationTimelinePanelTools(global) {
  const commonTools = global.CanvasiaEditorCommon || {};
  const presentationTimelineTools = global.CanvasiaEditorPresentationTimeline || {};

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

  function getPresentationTimelineToneClass(status) {
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

  function getPresentationTimelineDigest(timeline = {}) {
    if (typeof presentationTimelineTools.getPresentationTimelineStatusDigest === "function") {
      return presentationTimelineTools.getPresentationTimelineStatusDigest(timeline);
    }
    return {
      status: "empty",
      title: "还没有演出时间轴",
      detail: "项目里暂时没有可整理的画面、文本或音频事件。",
    };
  }

  function getIssueSeverityLabel(issue = {}) {
    if (issue.severity === "blocker") {
      return "先修";
    }
    if (issue.severity === "warn") {
      return "复查";
    }
    return "润色";
  }

  function getIssueSeverityClass(issue = {}) {
    if (issue.severity === "blocker") {
      return "danger";
    }
    if (issue.severity === "warn") {
      return "warn";
    }
    return "soft";
  }

  function buildPresentationRehearsalRows(timeline = {}, limit = 6) {
    const issueRows = toArray(timeline.issues).map((issue) => ({
      kind: "issue",
      priority: issue.severity === "blocker" ? 100 : issue.severity === "warn" ? 70 : 35,
      title: issue.title ?? "演出问题",
      targetLabel: [issue.chapterName, issue.sceneName, issue.blockLabel].filter(Boolean).join(" · "),
      actionLabel: getIssueSeverityLabel(issue),
      detail: issue.detail ?? "发布前复查这一处演出。",
    }));
    const sceneRows = toArray(timeline.sceneReports)
      .filter((scene) => scene.hasStoryContent && scene.eventCount > 0)
      .map((scene) => ({
        kind: "scene",
        priority: Math.max(5, Math.round((Number(scene.estimatedDurationMs) || 0) / 1000)),
        title: `完整排练：${scene.sceneName ?? "未命名场景"}`,
        targetLabel: `${scene.chapterName ?? "未分章"} · ${scene.eventCount ?? 0} 个演出事件`,
        actionLabel: scene.statusLabel ?? "排练",
        detail: `${scene.estimatedDurationLabel ?? "0 秒"} · 检查文本、立绘、BGM、音效和镜头是否自然接上。`,
      }));
    return [...issueRows, ...sceneRows]
      .sort((left, right) => right.priority - left.priority || String(left.title).localeCompare(String(right.title), "zh-CN"))
      .slice(0, Math.max(0, Number(limit) || 0));
  }

  function renderPresentationRehearsalRow(row = {}) {
    return `
      <div class="route-testing-item">
        <div>
          <b>${escapeHtml(row.title ?? "排练项")}</b>
          <span>${escapeHtml(row.targetLabel ?? "未定位")}</span>
        </div>
        <span>${escapeHtml(`${row.actionLabel ?? "复查"} · ${row.detail ?? "发布前完整跑一遍。"}`)}</span>
      </div>
    `;
  }

  function renderPresentationRehearsalQueue(timeline = {}) {
    const rows = buildPresentationRehearsalRows(timeline, 6);
    if (!rows.length) {
      return "";
    }
    return `
      <section class="preview-sprint-section">
        <div class="panel-heading panel-heading-compact">
          <h3>排练优先队列</h3>
          <span class="badge badge-soft">先修阻塞，再跑最长段落</span>
        </div>
        <div class="list-stack compact-stack">
          ${rows.map(renderPresentationRehearsalRow).join("")}
        </div>
      </section>
    `;
  }

  function renderPresentationTimelineIssueCard(issue = {}) {
    const severityClass = getIssueSeverityClass(issue);
    const toneClass = issue.severity === "blocker" ? "danger-text" : issue.severity === "warn" ? "warn-text" : "";
    return `
      <article class="preview-sprint-card is-${severityClass}">
        <div class="preview-sprint-head">
          <strong>${escapeHtml(issue.title)}</strong>
          <span class="issue-tag ${toneClass}">${escapeHtml(getIssueSeverityLabel(issue))}</span>
        </div>
        <p>${escapeHtml([issue.chapterName, issue.sceneName, issue.blockLabel].filter(Boolean).join(" · "))}</p>
        <div class="helper-text">${escapeHtml(issue.detail ?? "")}</div>
      </article>
    `;
  }

  function renderPresentationTimelineSceneRow(scene = {}) {
    return `
      <div class="route-testing-item">
        <div>
          <b>${escapeHtml(scene.sceneName)}</b>
          <span>${escapeHtml(`${scene.chapterName ?? "未分章"} · ${scene.eventCount ?? 0} 个演出事件`)}</span>
        </div>
        <span>${escapeHtml(`${scene.estimatedDurationLabel ?? "0 秒"} · ${scene.statusLabel ?? "待复查"}`)}</span>
      </div>
    `;
  }

  function renderPresentationTimelinePreview(timeline = {}) {
    const topIssues = toArray(timeline.issues).slice(0, 4);
    const scenePreview = toArray(timeline.sceneReports)
      .filter((scene) => scene.eventCount > 0)
      .slice(0, 4);
    if (topIssues.length > 0) {
      return `
        <div class="preview-sprint-grid">
          ${topIssues.map(renderPresentationTimelineIssueCard).join("")}
        </div>
      `;
    }
    if (scenePreview.length > 0) {
      return `
        <div class="list-stack compact-stack">
          ${scenePreview.map(renderPresentationTimelineSceneRow).join("")}
        </div>
      `;
    }
    return renderEmpty("当前项目还没有可列出的演出时间轴。可以先在剧情页添加背景、角色、正文或 BGM。");
  }

  function renderPresentationTimelinePanel(timeline = {}) {
    const digest = getPresentationTimelineDigest(timeline);
    const summary = timeline.summary ?? {};

    return `
      <article class="detail-card preview-sprint-panel">
        <div class="panel-heading">
          <h2>演出时间轴</h2>
          <span class="badge badge-soft ${getPresentationTimelineToneClass(digest.status)}">${escapeHtml(digest.title)}</span>
        </div>
        <p class="helper-text">${escapeHtml(digest.detail)} 它会把正文、背景、立绘、BGM、视频和镜头效果按场景整理，帮助发布前检查节奏是不是像正式作品。</p>
        <div class="preview-sprint-metrics">
          ${renderRouteMetricCard("演出事件", `${summary.eventCount ?? 0} 个`, "正文、画面、音频和镜头卡")}
          ${renderRouteMetricCard("预计时长", summary.estimatedDurationLabel ?? "0 秒", "按文字速度和演出卡估算")}
          ${renderRouteMetricCard("长静态段", `${summary.longStaticTextRunCount ?? 0} 段`, "连续文本缺少画面变化")}
          ${renderRouteMetricCard("硬切音频", `${summary.abruptAudioCount ?? 0} 处`, "BGM 淡入淡出不足")}
          ${renderRouteMetricCard("视觉 / 音频锚点", `${summary.missingVisualAnchorCount ?? 0} / ${summary.missingAudioAnchorCount ?? 0}`, "缺画面变化 / 缺声音提示")}
          ${renderRouteMetricCard("阻塞 / 提醒", `${summary.blockerCount ?? 0} / ${summary.warningCount ?? 0}`, "发布前优先清理")}
        </div>
        <div class="detail-actions">
          <button class="toolbar-button toolbar-button-primary" data-action="export-presentation-timeline-markdown">
            导出演出时间轴
          </button>
          <button class="toolbar-button" data-action="export-presentation-timeline-csv">
            导出时间轴 CSV
          </button>
          <button class="toolbar-button" data-action="switch-screen" data-screen="story">
            去剧情页调整演出
          </button>
        </div>
        ${renderPresentationRehearsalQueue(timeline)}
        ${renderPresentationTimelinePreview(timeline)}
      </article>
    `;
  }

  global.CanvasiaEditorPresentationTimelinePanel = Object.freeze({
    getPresentationTimelineToneClass,
    getPresentationTimelineDigest,
    buildPresentationRehearsalRows,
    renderPresentationRehearsalRow,
    renderPresentationRehearsalQueue,
    renderPresentationTimelineIssueCard,
    renderPresentationTimelineSceneRow,
    renderPresentationTimelinePreview,
    renderPresentationTimelinePanel,
  });
})(typeof window !== "undefined" ? window : globalThis);
