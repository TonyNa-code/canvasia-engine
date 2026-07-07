(function attachProjectHistoryPanelTools(global) {
  function fallbackEscapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function fallbackFormatDate(value) {
    if (!value) {
      return "未知";
    }

    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return String(value);
    }
    return date.toLocaleString("zh-CN");
  }

  function fallbackMetricCard(label, value, hint) {
    return `
      <article class="route-metric-card">
        <strong>${fallbackEscapeHtml(value)}</strong>
        <span>${fallbackEscapeHtml(label)}</span>
        <small>${fallbackEscapeHtml(hint)}</small>
      </article>
    `;
  }

  function getHelper(helpers, key, fallback) {
    return typeof helpers?.[key] === "function" ? helpers[key] : fallback;
  }

  function renderProjectHistoryPanel(model = {}, helpers = {}) {
    const history = model.history ?? {};
    const sessionRecovery = model.sessionRecovery ?? {};
    const filteredSnapshots = Array.isArray(model.filteredSnapshots) ? model.filteredSnapshots : [];
    const historySearchQuery = model.historySearchQuery ?? "";
    const historyFilterMode = model.historyFilterMode ?? "all";
    const escapeHtml = getHelper(helpers, "escapeHtml", fallbackEscapeHtml);
    const formatDate = getHelper(helpers, "formatDate", fallbackFormatDate);
    const renderRouteMetricCard = getHelper(helpers, "renderRouteMetricCard", fallbackMetricCard);
    const renderHistoryTimeline = getHelper(helpers, "renderHistoryTimeline", () => "");
    const getSafeHistoryFilterMode = getHelper(helpers, "getSafeHistoryFilterMode", (value) => value || "all");
    const getHistoryFilterLabel = getHelper(helpers, "getHistoryFilterLabel", (value) => value || "全部版本");
    const currentLabel = history.currentSnapshot?.label ?? "当前版本";
    const previousLabel = history.previousSnapshot?.label ?? "还没有更早版本";
    const nextLabel = history.nextSnapshot?.label ?? "还没有更晚版本";

    return `
    <section class="panel history-panel">
      <div class="panel-heading">
        <div>
          <h2>项目安全网</h2>
          <span class="panel-note">自动快照、手动检查点和指定版本恢复都集中放在这里</span>
        </div>
        <div class="detail-actions">
          <button class="toolbar-button toolbar-button-primary" data-action="create-history-checkpoint">
            立即存一个检查点
          </button>
          <button class="toolbar-button" data-action="restore-previous-version" ${history.canUndo ? "" : "disabled"}>
            回到上个版本
          </button>
        </div>
      </div>
      <div class="history-summary-strip">
        ${renderRouteMetricCard("总快照数", history.totalSnapshots, "这个项目目前已经记住了多少份版本")}
        ${renderRouteMetricCard("当前筛到", filteredSnapshots.length, "搜索和筛选后现在能看到多少份版本")}
        ${renderRouteMetricCard("当前版本", currentLabel, "当前停留在哪一份快照")}
        ${renderRouteMetricCard("可回退到", previousLabel, "点一下就能先回到这里")}
        ${renderRouteMetricCard("较新版本", nextLabel, "如果已经撤销过，这里会提示能重做到哪")}
      </div>
      ${
        sessionRecovery.noticeActive
          ? `<article class="detail-card history-recovery-alert">
              <strong>检测到上次可能异常退出</strong>
              <p>${escapeHtml(
                sessionRecovery.message || "上次打开这个项目时，编辑器可能没有正常关闭。"
              )}</p>
              <div class="detail-meta">
                上次异常会话开始：${escapeHtml(
                  sessionRecovery.lastUnexpectedExitStartedAt
                    ? formatDate(sessionRecovery.lastUnexpectedExitStartedAt)
                    : "未知"
                )}
              </div>
              <div class="history-card-actions">
                <button class="toolbar-button toolbar-button-primary" data-action="create-history-checkpoint">
                  先存一个检查点
                </button>
                <button class="toolbar-button" data-action="acknowledge-project-recovery-notice">
                  我知道了
                </button>
              </div>
            </article>`
          : ""
      }
      <article class="detail-card">
        <strong>恢复说明</strong>
        <p>选中任意一份快照后，都可以把整个项目恢复到那个时刻。手动检查点最适合在“大改剧情前”“导入大批素材前”先存一下。</p>
      </article>
      <div class="asset-search-row dashboard-search-row">
        <label class="asset-search-field">
          <span class="sr-only">搜索快照时间线</span>
          <input
            id="historySearchInput"
            type="search"
            value="${escapeHtml(historySearchQuery)}"
            placeholder="搜备注、时间或快照类型，比如：检查点 / 自动快照 / 开工前"
          />
        </label>
        <button class="toolbar-button" data-action="clear-history-filters">清空筛选</button>
      </div>
      <div class="asset-tag-chip-row">
        ${["all", "manual", "auto", "baseline", "current"]
          .map(
            (filterMode) => `
              <button
                class="tag-chip ${getSafeHistoryFilterMode(historyFilterMode) === filterMode ? "is-active" : ""}"
                data-action="set-history-filter"
                data-history-filter="${filterMode}"
              >
                ${escapeHtml(getHistoryFilterLabel(filterMode))}
              </button>
            `
          )
          .join("")}
      </div>
      <div class="history-timeline">
        ${renderHistoryTimeline(history, { filteredSnapshots })}
      </div>
    </section>
  `;
  }

  global.CanvasiaEditorProjectHistoryPanel = Object.freeze({
    renderProjectHistoryPanel,
  });
})(typeof window !== "undefined" ? window : globalThis);
