(function attachPreviewStoryDebuggerPanel(global) {
  "use strict";

  const common = global.CanvasiaEditorCommon || {};
  const escapeHtml = common.escapeHtml || ((value) => String(value ?? ""));
  const truncateText = common.truncateText || ((value, limit = 32) => String(value ?? "").slice(0, limit));

  function toArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function renderPreviewRouteSummaryPanel(routeSummary = null) {
    if (!routeSummary) {
      return `
        <article class="detail-card preview-route-card">
          <strong>路线摘要</strong>
          <p class="helper-text">开始一段试玩后，这里会记录已选选项和命中过的条件。</p>
        </article>
      `;
    }

    const recentItems = toArray(routeSummary.items).slice(-6).reverse();
    return `
      <article class="detail-card preview-route-card">
        <div class="preview-route-head">
          <div>
            <strong>路线摘要</strong>
            <p class="helper-text">只记录当前有效时间线里的选项和条件结果，回退后放弃的路线不会混进来。</p>
          </div>
          ${
            routeSummary.pendingChoiceCount > 0
              ? `<span class="issue-tag warn-text">当前还有 ${routeSummary.pendingChoiceCount} 个分支口在等你选择</span>`
              : ""
          }
        </div>
        <div class="preview-route-metrics">
          <div class="preview-route-metric"><span>走过场景</span><strong>${routeSummary.visitedSceneCount}</strong></div>
          <div class="preview-route-metric"><span>已选选项</span><strong>${routeSummary.choiceCount}</strong></div>
          <div class="preview-route-metric"><span>命中条件</span><strong>${routeSummary.conditionCount}</strong></div>
        </div>
        ${
          recentItems.length === 0
            ? '<div class="preview-route-note">这轮试玩暂时还没有经过选项或条件判断。继续往后走，路线记录会自动出现。</div>'
            : `
              <div class="detail-stack preview-route-list">
                ${recentItems
                  .map(
                    (item) => `
                      <article class="preview-route-item ${item.isCurrent ? "is-current" : ""}">
                        <div class="preview-route-step">
                          <span>第 ${item.index + 1} 步</span>
                          <strong>${escapeHtml(item.blockType === "choice" ? "选项结果" : "条件结果")}</strong>
                        </div>
                        <div class="preview-route-copy">
                          <strong>${escapeHtml(item.title)}</strong>
                          <p>${escapeHtml(`${item.sceneName} · ${item.meta}`)}</p>
                        </div>
                        <div class="detail-actions">
                          <button type="button" class="toolbar-button toolbar-button-primary" data-action="jump-preview-history" data-preview-index="${item.index}">跳回这一步</button>
                          <button type="button" class="toolbar-button" data-action="open-character-line" data-scene-id="${escapeHtml(item.sceneId)}" data-block-id="${escapeHtml(item.blockId)}">打开卡片</button>
                        </div>
                      </article>
                    `
                  )
                  .join("")}
              </div>
            `
        }
      </article>
    `;
  }

  function renderPreviewCoveragePoint(point, tone = "pending") {
    const badgeClass = tone === "pending" ? "warn-text" : point.remainingCount > 1 ? "warn-text" : "good-text";
    const badgeText = tone === "pending" ? "还没走到" : point.remainingCount > 0 ? `还差 ${point.remainingCount} 条` : "这处已测完";
    return `
      <article class="preview-coverage-item ${point.isCurrent ? "is-current" : ""}">
        <div class="preview-coverage-item-head">
          <div class="preview-coverage-copy"><strong>${escapeHtml(point.title)}</strong><p>${escapeHtml(point.meta)}</p></div>
          <span class="issue-tag ${badgeClass}">${escapeHtml(badgeText)}</span>
        </div>
        <div class="preview-coverage-progress">
          <span>已试 ${point.coveredCount}/${point.outcomes.length} 条</span>
          <span>${point.blockType === "choice" ? "选项结果" : "判断结果"}</span>
        </div>
        <div class="preview-coverage-branch-list">
          ${toArray(point.outcomes)
            .map(
              (outcome) => `
                <span class="preview-coverage-branch ${outcome.covered ? "is-covered" : "is-missing"}" title="${escapeHtml(`${outcome.label} · ${outcome.meta}`)}">
                  ${escapeHtml(truncateText(outcome.label, 22))}
                </span>
              `
            )
            .join("")}
        </div>
        <div class="detail-actions">
          <button type="button" class="toolbar-button toolbar-button-primary" data-action="preview-story-location" data-scene-id="${escapeHtml(point.sceneId)}" data-block-id="${escapeHtml(point.blockId)}">试玩这里</button>
          <button type="button" class="toolbar-button" data-action="open-character-line" data-scene-id="${escapeHtml(point.sceneId)}" data-block-id="${escapeHtml(point.blockId)}">打开卡片</button>
        </div>
      </article>
    `;
  }

  function renderPreviewBranchCoveragePanel(coverage = {}) {
    if (!coverage.totalPoints) {
      return `
        <article class="detail-card preview-coverage-card">
          <strong>分支覆盖</strong>
          <p class="helper-text">这个项目目前还没有选项或条件判断，所以这里暂时不用查覆盖率。</p>
        </article>
      `;
    }

    const unvisitedMarkup = toArray(coverage.unvisitedPoints)
      .slice(0, 3)
      .map((point) => renderPreviewCoveragePoint(point, "pending"))
      .join("");
    const partialMarkup = toArray(coverage.partialPoints)
      .slice(0, 3)
      .map((point) => renderPreviewCoveragePoint(point, "partial"))
      .join("");
    const remainingUnvisitedCount = Math.max(toArray(coverage.unvisitedPoints).length - 3, 0);
    const remainingPartialCount = Math.max(toArray(coverage.partialPoints).length - 3, 0);

    return `
      <article class="detail-card preview-coverage-card">
        <div class="preview-coverage-head">
          <div>
            <strong>分支覆盖</strong>
            <p class="helper-text">覆盖率只按当前有效路线计算，回退后未继续采用的未来记录不会造成误报。</p>
          </div>
          <div class="route-badge-row">
            <span class="issue-tag ${coverage.remainingOutcomeCount > 0 ? "warn-text" : "good-text"}">
              ${coverage.remainingOutcomeCount > 0 ? `还差 ${coverage.remainingOutcomeCount} 条路线` : "这轮试玩已测完"}
            </span>
          </div>
        </div>
        <div class="preview-coverage-metrics">
          <div class="preview-coverage-metric"><span>已遇到分支口</span><strong>${coverage.visitedPointCount} / ${coverage.totalPoints}</strong></div>
          <div class="preview-coverage-metric"><span>已试路线结果</span><strong>${coverage.coveredOutcomeCount} / ${coverage.totalOutcomeCount}</strong></div>
          <div class="preview-coverage-metric"><span>整处测完</span><strong>${coverage.fullyCoveredPointCount} / ${coverage.totalPoints}</strong></div>
        </div>
        ${
          coverage.currentPendingChoice
            ? '<div class="preview-coverage-note">当前正停在一个选项口。选完以后，覆盖结果会立刻更新。</div>'
            : coverage.remainingOutcomeCount === 0
              ? '<div class="preview-coverage-note is-complete">当前有效路线已经把所有分支结果都测到了。</div>'
              : ""
        }
        <div class="preview-coverage-section">
          <div class="preview-coverage-section-head"><strong>还没走到的分支口</strong><span>${toArray(coverage.unvisitedPoints).length} 处</span></div>
          ${unvisitedMarkup || '<div class="preview-coverage-note is-complete">所有分支口这轮都已经走到过了。</div>'}
          ${remainingUnvisitedCount > 0 ? `<div class="preview-coverage-note">还有 ${remainingUnvisitedCount} 处分支口未展示。</div>` : ""}
        </div>
        <div class="preview-coverage-section">
          <div class="preview-coverage-section-head"><strong>已经走到但还没试全</strong><span>${toArray(coverage.partialPoints).length} 处</span></div>
          ${partialMarkup || '<div class="preview-coverage-note is-complete">目前没有“走到但没试全”的分支口。</div>'}
          ${remainingPartialCount > 0 ? `<div class="preview-coverage-note">还有 ${remainingPartialCount} 处未试全的分支口未展示。</div>` : ""}
        </div>
      </article>
    `;
  }

  function renderVariableChanges(changes = []) {
    if (!changes.length) {
      return "";
    }
    return `
      <div class="preview-flight-change-list" aria-label="变量变化">
        ${changes
          .map(
            (change) => `
              <span class="preview-flight-change">
                <strong>${escapeHtml(change.name)}</strong>
                <del>${escapeHtml(change.beforeLabel)}</del>
                <span aria-hidden="true">→</span>
                <ins>${escapeHtml(change.afterLabel)}</ins>
              </span>
            `
          )
          .join("")}
      </div>
    `;
  }

  function renderStageCues(cues = []) {
    if (!cues.length) {
      return "";
    }
    return `
      <div class="preview-flight-cue-list" aria-label="音画调度">
        ${cues
          .map(
            (cue) => `<span class="preview-flight-cue is-${escapeHtml(cue.kind)}"><strong>${escapeHtml(cue.label)}</strong>${escapeHtml(cue.detail)}</span>`
          )
          .join("")}
      </div>
    `;
  }

  function renderFlightEntry(entry) {
    const routeMarkup = entry.routeDecision
      ? `<div class="preview-flight-route ${entry.routeDecision.pending ? "is-pending" : "is-resolved"}"><strong>${escapeHtml(entry.routeDecision.title)}</strong><span>${escapeHtml(entry.routeDecision.meta)}</span></div>`
      : "";
    return `
      <article class="preview-flight-entry ${entry.isCurrent ? "is-current" : ""}">
        <div class="preview-flight-step"><span>${String(entry.index + 1).padStart(2, "0")}</span><small>${entry.isCurrent ? "当前" : "记录"}</small></div>
        <div class="preview-flight-entry-body">
          <div class="preview-flight-entry-head">
            <div>
              <strong>${escapeHtml(entry.sceneName)}</strong>
              <span>${escapeHtml(entry.blockLabel)}${entry.blockIndex >= 0 ? ` · 第 ${entry.blockIndex + 1} 张` : ""}</span>
            </div>
            <div class="detail-actions">
              <button type="button" class="toolbar-button toolbar-button-primary" data-action="jump-preview-history" data-preview-index="${entry.index}">回到这步</button>
              ${
                entry.blockId
                  ? `<button type="button" class="toolbar-button" data-action="open-character-line" data-scene-id="${escapeHtml(entry.sceneId)}" data-block-id="${escapeHtml(entry.blockId)}">打开卡片</button>`
                  : ""
              }
            </div>
          </div>
          <p>${escapeHtml(entry.title || entry.meta || "这一步没有附加文字。")}</p>
          ${routeMarkup}
          ${renderVariableChanges(toArray(entry.variableChanges))}
          ${renderStageCues(toArray(entry.stageCues))}
        </div>
      </article>
    `;
  }

  function renderPreviewFlightRecorderPanel(report = null) {
    if (!report || !report.summary?.stepCount) {
      return `
        <article class="detail-card preview-flight-card">
          <div class="preview-flight-head">
            <div><strong>试玩飞行记录器</strong><p class="helper-text">开始试玩后，会自动记录当前路线、变量变化和关键音画调度。</p></div>
            <span class="preview-flight-signal" aria-hidden="true"><i></i><i></i><i></i></span>
          </div>
        </article>
      `;
    }

    const summary = report.summary;
    const recentEntries = (toArray(report.significantEntries).length ? report.significantEntries : report.entries)
      .slice(-8)
      .reverse();
    return `
      <article class="detail-card preview-flight-card">
        <div class="preview-flight-head">
          <div>
            <strong>试玩飞行记录器</strong>
            <p class="helper-text">自动记录真正走过的路线、变量差异与关键音画调度，可直接回跳或打开源卡片。</p>
          </div>
          <span class="preview-flight-signal" title="正在记录当前有效时间线" aria-label="正在记录"><i></i><i></i><i></i></span>
        </div>
        <div class="preview-flight-current">
          <span>当前落点</span>
          <strong>${escapeHtml(summary.currentSceneName)}</strong>
          <small>${escapeHtml(summary.currentBlockLabel)} · ${summary.completed ? "路线已结束" : "记录中"}</small>
        </div>
        <div class="preview-flight-metrics">
          <div><span>有效步数</span><strong>${summary.stepCount}</strong></div>
          <div><span>变量变化</span><strong>${summary.variableChangeCount}</strong></div>
          <div><span>路线结果</span><strong>${summary.routeDecisionCount}</strong></div>
          <div><span>音画调度</span><strong>${summary.stageCueCount}</strong></div>
        </div>
        <div class="detail-actions preview-flight-export-actions">
          <button type="button" class="toolbar-button toolbar-button-primary" data-action="export-preview-flight-recorder-markdown">导出易读记录</button>
          <button type="button" class="toolbar-button" data-action="export-preview-flight-recorder-json">导出完整数据</button>
        </div>
        <div class="preview-flight-list">
          ${recentEntries.map(renderFlightEntry).join("") || '<div class="preview-route-note">继续试玩后，关键变化会出现在这里。</div>'}
        </div>
        ${
          report.significantEntries.length > recentEntries.length
            ? `<div class="preview-route-note">这里只展示最近 ${recentEntries.length} 条关键变化；导出的文件会保留全部 ${report.entries.length} 步。</div>`
            : ""
        }
      </article>
    `;
  }

  global.CanvasiaEditorPreviewStoryDebuggerPanel = Object.freeze({
    renderPreviewRouteSummaryPanel,
    renderPreviewCoveragePoint,
    renderPreviewBranchCoveragePanel,
    renderPreviewFlightRecorderPanel,
  });
})(typeof window !== "undefined" ? window : globalThis);
