(function attachDashboardSearchPanelTools(global) {
  function fallbackEscapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function fallbackTruncateText(value, maxLength = 96) {
    const text = String(value ?? "");
    return text.length > maxLength ? `${text.slice(0, Math.max(0, maxLength - 1))}…` : text;
  }

  function fallbackRenderEmpty(message) {
    return `<div class="empty-state">${fallbackEscapeHtml(message)}</div>`;
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

  function getSearchCount(overview, key) {
    const value = Number(overview?.counts?.[key] ?? 0);
    return Number.isFinite(value) ? value : 0;
  }

  function renderDashboardSearchFilterBar(overview = {}, helpers = {}) {
    const escapeHtml = getHelper(helpers, "escapeHtml", fallbackEscapeHtml);
    const modes = [
      ["all", "全部", getSearchCount(overview, "scenes") + getSearchCount(overview, "characters") + getSearchCount(overview, "lines")],
      ["scenes", "场景", getSearchCount(overview, "scenes")],
      ["characters", "角色", getSearchCount(overview, "characters")],
      ["lines", "台词", getSearchCount(overview, "lines")],
    ];

    return modes
      .map(
        ([mode, label, count]) => `
        <button
          type="button"
          class="asset-tag-chip ${overview.mode === mode ? "is-active" : ""}"
          data-action="set-dashboard-search-mode"
          data-search-mode="${escapeHtml(mode)}"
        >
          <span>${escapeHtml(label)}</span>
          <strong>${escapeHtml(count)}</strong>
        </button>
      `
      )
      .join("");
  }

  function renderDashboardSearchSummary(overview = {}, stats = {}, helpers = {}) {
    const renderRouteMetricCard = getHelper(helpers, "renderRouteMetricCard", fallbackMetricCard);

    if (!overview.normalizedQuery) {
      return `
      ${renderRouteMetricCard("搜索状态", "等待输入", "输一个词，下面就会立刻给你结果")}
      ${renderRouteMetricCard("场景总数", stats.sceneCount ?? 0, "支持按场景名和章节名查")}
      ${renderRouteMetricCard("角色总数", stats.characterCount ?? 0, "支持按角色名和简介查")}
      ${renderRouteMetricCard("正文卡片", stats.storyBlockCount ?? 0, "台词、旁白、选项都能查")}
    `;
    }

    const totalCount = getSearchCount(overview, "scenes") + getSearchCount(overview, "characters") + getSearchCount(overview, "lines");
    return `
    ${renderRouteMetricCard("当前关键词", overview.query ?? "", "输入即检索")}
    ${renderRouteMetricCard("命中总数", totalCount, "所有分类加起来的结果")}
    ${renderRouteMetricCard("场景命中", getSearchCount(overview, "scenes"), "能直接打开场景或试玩")}
    ${renderRouteMetricCard("角色命中", getSearchCount(overview, "characters"), "能直接跳到角色页")}
    ${renderRouteMetricCard("台词命中", getSearchCount(overview, "lines"), "能直接定位到具体卡片")}
  `;
  }

  function renderDashboardSearchResults(overview = {}, helpers = {}) {
    const renderEmpty = getHelper(helpers, "renderEmpty", fallbackRenderEmpty);

    if (!overview.normalizedQuery) {
      return renderDashboardSearchSuggestions(overview.suggestions ?? [], helpers);
    }

    const totalCount = getSearchCount(overview, "scenes") + getSearchCount(overview, "characters") + getSearchCount(overview, "lines");
    if (totalCount === 0) {
      return renderEmpty(`没有找到和“${overview.query ?? ""}”有关的场景、角色或台词。可以试试搜章节名、角色名或更短的关键字。`);
    }

    const sections = [];
    const limitByMode = overview.mode === "all" ? 6 : 18;

    if (overview.mode === "all" || overview.mode === "scenes") {
      sections.push(renderDashboardSearchSection("场景结果", overview.scenes ?? [], limitByMode, helpers));
    }

    if (overview.mode === "all" || overview.mode === "characters") {
      sections.push(renderDashboardSearchSection("角色结果", overview.characters ?? [], limitByMode, helpers));
    }

    if (overview.mode === "all" || overview.mode === "lines") {
      sections.push(renderDashboardSearchSection("台词和选项", overview.lines ?? [], limitByMode, helpers));
    }

    return sections.filter(Boolean).join("") || renderEmpty("这个筛选下暂时没有结果。");
  }

  function renderDashboardSearchSuggestions(suggestions = [], helpers = {}) {
    const escapeHtml = getHelper(helpers, "escapeHtml", fallbackEscapeHtml);
    return `
    <article class="detail-card">
      <strong>可以直接试试这些词</strong>
      <p class="helper-text">点击后会自动填入搜索框。项目内容变多时，可用来快速定位剧情。</p>
      <div class="asset-tag-chip-row">
        ${suggestions
          .map(
            (item) => `
              <button
                type="button"
                class="asset-tag-chip asset-preset-tag-chip"
                data-action="apply-dashboard-search-sample"
                data-query="${escapeHtml(item)}"
              >
                ${escapeHtml(item)}
              </button>
            `
          )
          .join("")}
      </div>
    </article>
  `;
  }

  function renderDashboardSearchSection(title, items = [], limit = 6, helpers = {}) {
    const escapeHtml = getHelper(helpers, "escapeHtml", fallbackEscapeHtml);
    if (!items.length) {
      return "";
    }

    const visibleItems = items.slice(0, limit);
    const hiddenCount = Math.max(items.length - visibleItems.length, 0);

    return `
    <div class="search-result-section">
      <div class="chapter-divider">${escapeHtml(title)} · ${items.length} 条</div>
      <div class="list-stack compact-list">
        ${visibleItems.map((item) => renderDashboardSearchResultCard(item, helpers)).join("")}
      </div>
      ${hiddenCount > 0 ? `<div class="helper-text">还有 ${hiddenCount} 条结果没有展开。把筛选切到这个分类，会看得更全。</div>` : ""}
    </div>
  `;
  }

  function renderDashboardSearchResultCard(item = {}, helpers = {}) {
    const escapeHtml = getHelper(helpers, "escapeHtml", fallbackEscapeHtml);
    const truncateText = getHelper(helpers, "truncateText", fallbackTruncateText);

    if (item.resultType === "scene") {
      return `
      <article class="search-result-card">
        <div class="search-result-top">
          <span class="issue-tag good-text">场景</span>
          <span class="search-result-meta">${escapeHtml(item.meta)}</span>
        </div>
        <strong>${escapeHtml(item.title)}</strong>
        <p>${escapeHtml(item.snippet)}</p>
        <div class="search-result-actions">
          <button type="button" class="toolbar-button toolbar-button-primary" data-action="open-scene-from-map" data-scene-id="${escapeHtml(item.sceneId)}">
            打开场景
          </button>
          <button type="button" class="toolbar-button" data-action="preview-scene-from-map" data-scene-id="${escapeHtml(item.sceneId)}">
            直接试玩
          </button>
        </div>
      </article>
    `;
    }

    if (item.resultType === "character") {
      return `
      <article class="search-result-card">
        <div class="search-result-top">
          <span class="issue-tag">角色</span>
          <span class="search-result-meta">${escapeHtml(item.meta)}</span>
        </div>
        <strong>${escapeHtml(item.title)}</strong>
        <p>${escapeHtml(item.snippet)}</p>
        <div class="search-result-actions">
          <button type="button" class="toolbar-button toolbar-button-primary" data-action="open-dashboard-character" data-character-id="${escapeHtml(item.characterId)}">
            打开角色页
          </button>
        </div>
      </article>
    `;
    }

    const lineTag = item.lineType === "dialogue" ? "台词" : item.lineType === "narration" ? "旁白" : "选项";
    const toneClass = item.lineType === "dialogue" ? "good-text" : item.lineType === "choice" ? "warn-text" : "";

    return `
    <article class="search-result-card">
      <div class="search-result-top">
        <span class="issue-tag ${toneClass}">${lineTag}</span>
        <span class="search-result-meta">${escapeHtml(item.meta)}</span>
      </div>
      <strong>${escapeHtml(item.title)}</strong>
      <p>${escapeHtml(truncateText(item.snippet, 96))}</p>
      <div class="search-result-actions">
        <button
          type="button"
          class="toolbar-button toolbar-button-primary"
          data-action="open-character-line"
          data-scene-id="${escapeHtml(item.sceneId)}"
          data-block-id="${escapeHtml(item.blockId)}"
        >
          定位到卡片
        </button>
      </div>
    </article>
  `;
  }

  global.CanvasiaEditorDashboardSearchPanel = Object.freeze({
    renderDashboardSearchFilterBar,
    renderDashboardSearchSummary,
    renderDashboardSearchResults,
    renderDashboardSearchSuggestions,
    renderDashboardSearchSection,
    renderDashboardSearchResultCard,
  });
})(typeof window !== "undefined" ? window : globalThis);
