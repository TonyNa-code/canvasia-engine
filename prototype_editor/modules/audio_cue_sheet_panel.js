(function attachAudioCueSheetPanelTools(global) {
  const commonTools = global.CanvasiaEditorCommon || {};
  const audioCueSheetTools = global.CanvasiaEditorAudioCueSheet || {};

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

  function getAudioCueSheetToneClass(status) {
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

  function getAudioCueSheetDigest(sheet = {}) {
    if (typeof audioCueSheetTools.getAudioCueSheetStatusDigest === "function") {
      return audioCueSheetTools.getAudioCueSheetStatusDigest(sheet);
    }
    return {
      status: "empty",
      title: "还没有音频调度",
      detail: "项目里暂时没有播放音乐或音效卡。",
    };
  }

  function renderAudioCueIssueCard(issue = {}) {
    const severityClass = issue.severity === "blocker" ? "danger" : issue.severity === "warn" ? "warn" : "soft";
    const toneClass = issue.severity === "blocker" ? "danger-text" : issue.severity === "warn" ? "warn-text" : "";
    const severityLabel = issue.severity === "blocker" ? "先修" : issue.severity === "warn" ? "复查" : "润色";

    return `
      <article class="preview-sprint-card is-${severityClass}">
        <div class="preview-sprint-head">
          <strong>${escapeHtml(issue.title)}</strong>
          <span class="issue-tag ${toneClass}">${escapeHtml(severityLabel)}</span>
        </div>
        <p>${escapeHtml(`${issue.cueType === "voice" ? "语音" : issue.cueType === "sfx" ? "音效" : "BGM"} · ${issue.chapterName ?? "未分章"} · ${issue.sceneName ?? "未命名场景"} · ${issue.assetName ?? "未选择音频素材"}`)}</p>
        <div class="helper-text">${escapeHtml(issue.detail)}</div>
      </article>
    `;
  }

  function renderAudioCueRangeRow(row = {}) {
    return `
      <div class="route-testing-item">
        <div>
          <b>${escapeHtml(row.assetName)}</b>
          <span>${escapeHtml(`${row.chapterName ?? "未分章"} · ${row.sceneName ?? "未命名场景"} · ${row.spanLabel ?? "0 张卡"}`)}</span>
        </div>
        <span>${escapeHtml(`${row.handoffLabel ?? "等待接管"} · ${row.auditionHint ?? "发布前试听这一段。"}`)}</span>
      </div>
    `;
  }

  function renderSfxCueRow(row = {}) {
    return `
      <div class="route-testing-item">
        <div>
          <b>${escapeHtml(row.assetName)}</b>
          <span>${escapeHtml(`${row.chapterName ?? "未分章"} · ${row.sceneName ?? "未命名场景"} · ${row.volumeLabel ?? "100%"}`)}</span>
        </div>
        <span>${escapeHtml(`${row.cueLabel ?? "音效触发点"} · ${row.reviewHint ?? "发布前试听这一声。"}`)}</span>
      </div>
    `;
  }

  function renderVoiceCueRow(row = {}) {
    return `
      <div class="route-testing-item">
        <div>
          <b>${escapeHtml(row.assetName)}</b>
          <span>${escapeHtml(`${row.chapterName ?? "未分章"} · ${row.sceneName ?? "未命名场景"} · ${row.speakerName ?? "旁白"}`)}</span>
        </div>
        <span>${escapeHtml(`${row.cueLabel ?? "语音触发点"} · ${row.reviewHint ?? "发布前试听这一句。"}`)}</span>
      </div>
    `;
  }

  function renderAudioCueSheetPreview(sheet = {}) {
    const topIssues = (Array.isArray(sheet.issues) ? sheet.issues : []).slice(0, 4);
    const rangePreview = (Array.isArray(sheet.rangeRows) ? sheet.rangeRows : []).slice(0, 4);
    const sfxPreview = (Array.isArray(sheet.sfxRows) ? sheet.sfxRows : []).slice(0, Math.max(0, 4 - rangePreview.length));
    const voicePreview = (Array.isArray(sheet.voiceRows) ? sheet.voiceRows : []).slice(
      0,
      Math.max(0, 4 - rangePreview.length - sfxPreview.length)
    );

    if (topIssues.length > 0) {
      return `
        <div class="preview-sprint-grid">
          ${topIssues.map(renderAudioCueIssueCard).join("")}
        </div>
      `;
    }
    if (rangePreview.length > 0 || sfxPreview.length > 0 || voicePreview.length > 0) {
      return `
        <div class="list-stack compact-stack">
          ${rangePreview.map(renderAudioCueRangeRow).join("")}
          ${sfxPreview.map(renderSfxCueRow).join("")}
          ${voicePreview.map(renderVoiceCueRow).join("")}
        </div>
      `;
    }
    return renderEmpty("当前项目还没有播放音乐、音效或已绑定语音。可以先在剧情页给入口场景加一首 BGM，再补关键音效和语音。");
  }

  function renderAudioCueSheetPanel(sheet = {}) {
    const digest = getAudioCueSheetDigest(sheet);
    const summary = sheet.summary ?? {};

    return `
      <article class="detail-card preview-sprint-panel">
        <div class="panel-heading">
          <h2>音频调度表</h2>
          <span class="badge badge-soft ${getAudioCueSheetToneClass(digest.status)}">${escapeHtml(digest.title)}</span>
        </div>
        <p class="helper-text">${escapeHtml(digest.detail)} 适合发布前把“哪首歌覆盖哪段剧情、哪些音效和语音在哪触发、哪里需要试听”一次看清。</p>
        <div class="preview-sprint-metrics">
          ${renderRouteMetricCard("BGM 卡", `${summary.cueCount ?? 0} 张`, "项目中所有播放音乐卡")}
          ${renderRouteMetricCard("音效卡", `${summary.sfxCueCount ?? 0} 张`, "门铃、脚步、心跳等触发音效")}
          ${renderRouteMetricCard("语音卡", `${summary.voiceCueCount ?? 0} 句`, "已绑定语音的台词和旁白")}
          ${renderRouteMetricCard("覆盖段", `${summary.rangeSegmentCount ?? 0} 段`, "每首 BGM 实际覆盖的剧情范围")}
          ${renderRouteMetricCard("阻塞 / 提醒", `${summary.blockerCount ?? 0} / ${summary.warningCount ?? 0}`, "缺素材、坏范围或提前接管")}
        </div>
        <div class="detail-actions">
          <button class="toolbar-button toolbar-button-primary" data-action="export-audio-cue-sheet-markdown">
            导出音频调度表
          </button>
          <button class="toolbar-button" data-action="export-audio-cue-sheet-csv">
            导出音频 CSV
          </button>
          <button class="toolbar-button" data-action="switch-screen" data-screen="story">
            去剧情页调整音乐
          </button>
        </div>
        ${renderAudioCueSheetPreview(sheet)}
      </article>
    `;
  }

  global.CanvasiaEditorAudioCueSheetPanel = Object.freeze({
    getAudioCueSheetToneClass,
    renderAudioCueIssueCard,
    renderAudioCueRangeRow,
    renderSfxCueRow,
    renderVoiceCueRow,
    renderAudioCueSheetPreview,
    renderAudioCueSheetPanel,
  });
})(typeof window !== "undefined" ? window : globalThis);
