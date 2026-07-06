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

  function formatAudioSegmentDuration(seconds) {
    if (typeof audioCueSheetTools.formatAudioSegmentDuration === "function") {
      return audioCueSheetTools.formatAudioSegmentDuration(seconds);
    }
    const safeSeconds = Math.max(0, Math.round(Number(seconds) || 0));
    if (safeSeconds < 60) {
      return `约 ${safeSeconds} 秒`;
    }
    const minutes = Math.floor(safeSeconds / 60);
    const remainingSeconds = safeSeconds % 60;
    return remainingSeconds > 0 ? `约 ${minutes}分${remainingSeconds}秒` : `约 ${minutes} 分钟`;
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
          <span>${escapeHtml(`${row.chapterName ?? "未分章"} · ${row.sceneName ?? "未命名场景"} · ${row.spanLabel ?? "0 张卡"} · ${row.durationLabel ?? "约 0 秒"}`)}</span>
        </div>
        <span>${escapeHtml(`${row.textLoadLabel ?? "0 字 / 0 段正文"} · ${row.handoffLabel ?? "等待接管"} · ${row.auditionHint ?? "发布前试听这一段。"}`)}</span>
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

  function renderVoiceMixRow(row = {}) {
    const toneClass = row.risk === "warn" ? "warn-text" : row.risk === "tip" ? "soft-text" : "good-text";
    return `
      <div class="route-testing-item">
        <div>
          <b>${escapeHtml(`${row.assetName ?? "BGM"} · ${row.riskLabel ?? "安全"}`)}</b>
          <span>${escapeHtml(`${row.chapterName ?? "未分章"} · ${row.sceneName ?? "未命名场景"} · ${row.voiceCount ?? 0} 句语音`)}</span>
        </div>
        <span class="${toneClass}">${escapeHtml(`${row.duckingLabel ?? "语音焦点"} · BGM ${row.bgmVolume ?? 100}% -> ${row.effectiveBgmVolume ?? 45}% · ${row.reviewHint ?? "发布前试听人声清晰度。"}`)}</span>
      </div>
    `;
  }

  function renderAudioProductionTaskCard(task = {}) {
    const severityClass = task.severity === "blocker" ? "danger" : task.severity === "warn" ? "warn" : "soft";
    const toneClass = task.severity === "blocker" ? "danger-text" : task.severity === "warn" ? "warn-text" : "";

    return `
      <article class="preview-sprint-card is-${severityClass}">
        <div class="preview-sprint-head">
          <strong>${escapeHtml(`${task.rank ?? "-"} · ${task.title ?? "音频制作任务"}`)}</strong>
          <span class="issue-tag ${toneClass}">${escapeHtml(task.phase ?? "处理")}</span>
        </div>
        <p>${escapeHtml(`${task.targetLabel ?? "未定位"} · ${task.actionLabel ?? "打开对应位置复查"}`)}</p>
        <div class="helper-text">${escapeHtml(task.detail ?? "")}</div>
      </article>
    `;
  }

  function renderAudioRangeSuggestionCard(suggestion = {}) {
    const toneClass = suggestion.tone === "warn" ? "warn-text" : "";
    return `
      <article class="preview-sprint-card is-${suggestion.tone === "warn" ? "warn" : "soft"}">
        <div class="preview-sprint-head">
          <strong>${escapeHtml(suggestion.title ?? "建议明确 BGM 文本范围")}</strong>
          <span class="issue-tag ${toneClass}">${escapeHtml(suggestion.tone === "warn" ? "建议先修" : "可优化")}</span>
        </div>
        <p>${escapeHtml(`${suggestion.assetName ?? "BGM"} · ${suggestion.chapterName ?? "未分章"} · ${suggestion.sceneName ?? "未命名场景"}`)}</p>
        <div class="helper-text">${escapeHtml(`${suggestion.startLabel ?? "开始卡"} -> ${suggestion.endLabel ?? "建议结束卡"}。${suggestion.detail ?? ""}`)}</div>
        <div class="detail-actions compact-actions">
          <button
            type="button"
            class="toolbar-button"
            data-action="apply-audio-range-suggestion"
            data-scene-id="${escapeHtml(suggestion.sceneId ?? "")}"
            data-block-id="${escapeHtml(suggestion.blockId ?? "")}"
            data-end-block-id="${escapeHtml(suggestion.endBlockId ?? "")}"
            data-fade-out-ms="${escapeHtml(String(suggestion.fadeOutMs ?? 900))}"
          >
            ${escapeHtml(suggestion.actionLabel ?? "套用这个范围")}
          </button>
        </div>
      </article>
    `;
  }

  function renderAudioRangeSuggestions(suggestions = []) {
    const rows = Array.isArray(suggestions) ? suggestions.slice(0, 4) : [];
    if (!rows.length) {
      return "";
    }
    return `
      <section class="preview-sprint-section">
        <div class="panel-heading panel-heading-compact">
          <h3>BGM 文本范围建议</h3>
          <span class="badge badge-soft">${escapeHtml(`${suggestions.length} 条`)}</span>
        </div>
        <div class="preview-sprint-grid">
          ${rows.map(renderAudioRangeSuggestionCard).join("")}
        </div>
      </section>
    `;
  }

  function renderAudioAuditionChecklistRow(row = {}) {
    return `
      <div class="route-testing-item">
        <div>
          <b>${escapeHtml(`${row.rank ?? "-"} · ${row.type ?? "Audio"} · ${row.assetName ?? "未命名素材"}`)}</b>
          <span>${escapeHtml(`${row.targetLabel ?? "未定位"} · ${row.cueLabel ?? "触发点待确认"}`)}</span>
        </div>
        <span>${escapeHtml(`${row.priority ?? "抽查"} · ${row.actionLabel ?? "发布前试听"}`)}</span>
      </div>
    `;
  }

  function renderAudioProductionQueue(queue = []) {
    const rows = Array.isArray(queue) ? queue.slice(0, 6) : [];
    if (!rows.length) {
      return "";
    }
    return `
      <section class="preview-sprint-section">
        <div class="panel-heading panel-heading-compact">
          <h3>制作优先队列</h3>
          <span class="badge badge-soft">先修阻塞，再复查听感</span>
        </div>
        <div class="preview-sprint-grid">
          ${rows.map(renderAudioProductionTaskCard).join("")}
        </div>
      </section>
    `;
  }

  function renderAudioAuditionChecklist(checklist = []) {
    const rows = Array.isArray(checklist) ? checklist.slice(0, 8) : [];
    if (!rows.length) {
      return "";
    }
    return `
      <section class="preview-sprint-section">
        <div class="panel-heading panel-heading-compact">
          <h3>发布前试听清单</h3>
          <span class="badge badge-soft">${escapeHtml(`${checklist.length} 项`)}</span>
        </div>
        <div class="list-stack compact-stack">
          ${rows.map(renderAudioAuditionChecklistRow).join("")}
        </div>
      </section>
    `;
  }

  function renderVoiceMixSection(rows = []) {
    const previewRows = Array.isArray(rows) ? rows.slice(0, 6) : [];
    if (!previewRows.length) {
      return "";
    }
    return `
      <section class="preview-sprint-section">
        <div class="panel-heading panel-heading-compact">
          <h3>人声混音检查</h3>
          <span class="badge badge-soft">${escapeHtml(`${rows.length} 段 BGM 覆盖语音`)}</span>
        </div>
        <div class="list-stack compact-stack">
          ${previewRows.map(renderVoiceMixRow).join("")}
        </div>
      </section>
    `;
  }

  function getAudioCueAutoFixPlan(sheet = {}) {
    return sheet.autoFixPlan && typeof sheet.autoFixPlan === "object"
      ? sheet.autoFixPlan
      : {
          changed: false,
          changedSceneCount: 0,
          changedBlockCount: 0,
          operationCount: 0,
          summary: "音频基础参数已经比较完整",
        };
  }

  function renderAudioCueAutoFixButton(sheet = {}) {
    const plan = getAudioCueAutoFixPlan(sheet);
    const label = plan.changed ? `一键补齐 ${plan.operationCount ?? 0} 个音频参数` : "音频基础参数已完整";
    const title = plan.changed
      ? `会处理 ${plan.changedSceneCount ?? 0} 个场景、${plan.changedBlockCount ?? 0} 张音频卡。`
      : "当前项目的 BGM 淡入淡出、停止淡出和基础范围参数已经比较完整。";
    return `
      <button
        class="toolbar-button"
        data-action="apply-audio-cue-autofix"
        title="${escapeHtml(title)}"
        ${plan.changed ? "" : 'disabled aria-disabled="true"'}
      >
        ${escapeHtml(label)}
      </button>
    `;
  }

  function renderAudioCueSheetPreview(sheet = {}) {
    const topIssues = (Array.isArray(sheet.issues) ? sheet.issues : [])
      .filter((issue) => ["blocker", "warn"].includes(issue.severity))
      .slice(0, 4);
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
          ${renderRouteMetricCard("BGM 预计", formatAudioSegmentDuration(summary.totalEstimatedMusicSeconds ?? 0), "按正文、等待和媒体卡粗略估算")}
          ${renderRouteMetricCard("范围建议", `${summary.rangeSuggestionCount ?? 0} 条`, "可一键绑定到具体文本段落")}
          ${renderRouteMetricCard("短/长/空段", `${summary.shortMusicSegmentCount ?? 0}/${summary.longMusicSegmentCount ?? 0}/${summary.silentMusicSegmentCount ?? 0}`, "帮助定位需要试听的 BGM 段")}
          ${renderRouteMetricCard("人声混音", `${summary.voiceMusicSegmentCount ?? 0} / ${summary.voiceMixWarningCount ?? 0}`, "BGM 覆盖语音段 / 可能盖过台词")}
          ${renderRouteMetricCard("阻塞 / 提醒", `${summary.blockerCount ?? 0} / ${summary.warningCount ?? 0}`, "缺素材、坏范围或提前接管")}
          ${renderRouteMetricCard("就绪度", `${summary.releaseReadinessPercent ?? 0}%`, "按阻塞、提醒和缺 BGM 场景估算")}
          ${renderRouteMetricCard("制作任务", `${summary.productionTaskCount ?? 0} 项`, "按发布优先级自动排序")}
          ${renderRouteMetricCard("试听清单", `${summary.auditionChecklistCount ?? 0} 项`, "发布前建议抽查的音频点")}
        </div>
        <div class="detail-actions">
          <button class="toolbar-button toolbar-button-primary" data-action="export-audio-cue-sheet-markdown">
            导出音频调度表
          </button>
          <button class="toolbar-button" data-action="export-audio-cue-sheet-csv">
            导出音频 CSV
          </button>
          ${renderAudioCueAutoFixButton(sheet)}
          <button class="toolbar-button" data-action="switch-screen" data-screen="story">
            去剧情页调整音乐
          </button>
        </div>
        ${renderAudioCueSheetPreview(sheet)}
        ${renderVoiceMixSection(sheet.voiceMixRows)}
        ${renderAudioRangeSuggestions(sheet.rangeSuggestions)}
        ${renderAudioProductionQueue(sheet.productionQueue)}
        ${renderAudioAuditionChecklist(sheet.auditionChecklist)}
      </article>
    `;
  }

  global.CanvasiaEditorAudioCueSheetPanel = Object.freeze({
    getAudioCueSheetToneClass,
    renderAudioCueIssueCard,
    renderAudioCueRangeRow,
    renderSfxCueRow,
    renderVoiceCueRow,
    renderVoiceMixRow,
    renderAudioProductionTaskCard,
    renderAudioRangeSuggestionCard,
    renderAudioRangeSuggestions,
    renderAudioAuditionChecklistRow,
    renderAudioProductionQueue,
    renderAudioAuditionChecklist,
    renderVoiceMixSection,
    getAudioCueAutoFixPlan,
    renderAudioCueAutoFixButton,
    renderAudioCueSheetPreview,
    renderAudioCueSheetPanel,
  });
})(typeof window !== "undefined" ? window : globalThis);
