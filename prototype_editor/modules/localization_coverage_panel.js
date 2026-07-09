(function attachLocalizationCoveragePanelTools(global) {
  const commonTools = global.CanvasiaEditorCommon || {};
  const localizationCoverageTools = global.CanvasiaEditorLocalizationCoverage || {};

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

  function getLocalizationCoverageToneClass(status) {
    if (status === "warn") {
      return "warn-text";
    }
    if (status === "ready") {
      return "good-text";
    }
    return "";
  }

  function getLocalizationCoverageDigest(coverage = {}) {
    if (typeof localizationCoverageTools.getLocalizationCoverageStatusDigest === "function") {
      return localizationCoverageTools.getLocalizationCoverageStatusDigest(coverage);
    }
    return {
      status: "empty",
      title: "还没有多语言目标",
      detail: "当前项目仍是单语言流程。",
    };
  }

  function buildTranslationPriorityRows(coverage = {}, limit = 6) {
    return toArray(coverage.issues)
      .map((issue) => ({
        priority: issue.status === "missing" ? 100 : issue.status === "same_as_source" ? 60 : 20,
        title: issue.statusLabel ?? issue.title ?? "翻译待处理",
        languageLabel: issue.languageLabel ?? issue.language ?? "目标语言",
        targetLabel: [issue.chapterName, issue.sceneName, issue.locationLabel].filter(Boolean).join(" · "),
        fieldLabel: issue.fieldLabel ?? "文本",
        sourceText: issue.sourceText ?? "",
        status: issue.status ?? "review",
      }))
      .sort((left, right) => right.priority - left.priority || String(left.targetLabel).localeCompare(String(right.targetLabel), "zh-CN"))
      .slice(0, Math.max(0, Number(limit) || 0));
  }

  function renderTranslationPriorityRow(row = {}) {
    const toneClass = row.status === "missing" ? "warn-text" : "";
    return `
      <div class="route-testing-item">
        <div>
          <b>${escapeHtml(`${row.title ?? "翻译待处理"} · ${row.languageLabel ?? "目标语言"}`)}</b>
          <span>${escapeHtml(row.targetLabel || "未定位")}</span>
        </div>
        <span class="${toneClass}">${escapeHtml(`${row.fieldLabel ?? "文本"}：${row.sourceText ?? ""}`)}</span>
      </div>
    `;
  }

  function renderTranslationPriorityQueue(coverage = {}) {
    const rows = buildTranslationPriorityRows(coverage, 6);
    if (!rows.length) {
      return "";
    }
    return `
      <section class="preview-sprint-section">
        <div class="panel-heading panel-heading-compact">
          <h3>翻译优先队列</h3>
          <span class="badge badge-soft">先补缺翻译，再查同文占位</span>
        </div>
        <div class="list-stack compact-stack">
          ${rows.map(renderTranslationPriorityRow).join("")}
        </div>
      </section>
    `;
  }

  function renderLocalizationIssueCard(issue = {}) {
    const isMissing = issue.status === "missing";
    return `
      <article class="preview-sprint-card is-${isMissing ? "warn" : "soft"}">
        <div class="preview-sprint-head">
          <strong>${escapeHtml(issue.statusLabel)}</strong>
          <span class="issue-tag ${isMissing ? "warn-text" : ""}">
            ${escapeHtml(issue.languageLabel)}
          </span>
        </div>
        <p>${escapeHtml([issue.chapterName, issue.sceneName, issue.locationLabel].filter(Boolean).join(" · "))}</p>
        <div class="helper-text">${escapeHtml(`${issue.fieldLabel}：${issue.sourceText}`)}</div>
      </article>
    `;
  }

  function renderLanguageBreakdownRow(item = {}) {
    return `
      <div class="route-testing-item">
        <div>
          <b>${escapeHtml(item.languageLabel)}</b>
          <span>${escapeHtml(`${item.language} · 完成 ${item.readyCount}/${item.totalCount}`)}</span>
        </div>
        <span>${escapeHtml(`${item.completionPercent}%`)}</span>
      </div>
    `;
  }

  function renderLocalizationCoveragePreview(coverage = {}) {
    const topIssues = toArray(coverage.issues).slice(0, 4);
    const languageBreakdown = toArray(coverage.languageBreakdown).slice(0, 4);
    if (topIssues.length > 0) {
      return `
        <div class="preview-sprint-grid">
          ${topIssues.map(renderLocalizationIssueCard).join("")}
        </div>
      `;
    }
    if (languageBreakdown.length > 0) {
      return `
        <div class="list-stack compact-stack">
          ${languageBreakdown.map(renderLanguageBreakdownRow).join("")}
        </div>
      `;
    }
    return renderEmpty("当前项目仍是单语言流程。需要国际化时，先到项目设置里勾选目标语言。");
  }

  function renderLocalizationCoveragePanel(coverage = {}) {
    const digest = getLocalizationCoverageDigest(coverage);
    const summary = coverage.summary ?? {};

    return `
      <article class="detail-card preview-sprint-panel">
        <div class="panel-heading">
          <h2>多语言覆盖检查</h2>
          <span class="badge badge-soft ${getLocalizationCoverageToneClass(digest.status)}">${escapeHtml(digest.title)}</span>
        </div>
        <p class="helper-text">${escapeHtml(digest.detail)} 它会检查章节名、场景名、角色名、台词、旁白、选项和标题文本，适合发给翻译或校对人员。</p>
        <div class="preview-sprint-metrics">
          ${renderRouteMetricCard("目标语言", `${summary.targetLanguageCount ?? 0} 种`, "默认语言之外")}
          ${renderRouteMetricCard("可翻译文本", `${summary.sourceTextCount ?? 0} 条`, "章节、场景、角色和正文")}
          ${renderRouteMetricCard("缺翻译 / 疑似占位", `${summary.missingCount ?? 0} / ${summary.sameAsSourceCount ?? 0}`, "发布前建议复核")}
          ${renderRouteMetricCard("覆盖率", `${summary.completionPercent ?? 0}%`, "只统计真正完成的译文")}
          ${renderRouteMetricCard("应填翻译", `${summary.expectedTranslationCount ?? 0} 条`, "目标语言 x 可翻译文本")}
          ${renderRouteMetricCard("已完成", `${summary.readyCount ?? 0} 条`, "可进入试玩校对")}
        </div>
        <div class="detail-actions">
          <button class="toolbar-button toolbar-button-primary" data-action="export-localization-coverage-markdown">
            导出多语言报告
          </button>
          <button class="toolbar-button" data-action="export-localization-coverage-csv">
            导出翻译 CSV
          </button>
          <button class="toolbar-button" data-action="import-localization-coverage-csv">
            导入翻译 CSV
          </button>
          <button class="toolbar-button" data-action="switch-screen" data-screen="preview">
            去预览切语言
          </button>
        </div>
        ${renderTranslationPriorityQueue(coverage)}
        ${renderLocalizationCoveragePreview(coverage)}
      </article>
    `;
  }

  global.CanvasiaEditorLocalizationCoveragePanel = Object.freeze({
    getLocalizationCoverageToneClass,
    getLocalizationCoverageDigest,
    buildTranslationPriorityRows,
    renderTranslationPriorityRow,
    renderTranslationPriorityQueue,
    renderLocalizationIssueCard,
    renderLanguageBreakdownRow,
    renderLocalizationCoveragePreview,
    renderLocalizationCoveragePanel,
  });
})(typeof window !== "undefined" ? window : globalThis);
