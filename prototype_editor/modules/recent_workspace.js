(function attachRecentWorkspaceTools(global) {
  const RECENT_WORKSPACE_LIMIT = 8;

  const RECENT_WORKSPACE_TYPE_LABELS = Object.freeze({
    scene: "剧情场景",
    script: "台本入口",
    asset: "素材资料",
    character: "角色资料",
  });

  function hasOwn(source, key) {
    return Object.prototype.hasOwnProperty.call(source, key);
  }

  function getSafeRecentWorkspaceType(type) {
    return hasOwn(RECENT_WORKSPACE_TYPE_LABELS, type) ? type : "scene";
  }

  function getRecentWorkspaceTypeLabel(type) {
    return RECENT_WORKSPACE_TYPE_LABELS[getSafeRecentWorkspaceType(type)] ?? RECENT_WORKSPACE_TYPE_LABELS.scene;
  }

  function sanitizeRecentWorkspaceText(value, maxLength = 140) {
    const text = String(value ?? "").trim();
    const safeMaxLength = Number.isInteger(Number(maxLength)) && Number(maxLength) >= 0 ? Number(maxLength) : 140;
    return text ? text.slice(0, safeMaxLength) : "";
  }

  function getRecentWorkspaceStorageKey(scope = "default") {
    const safeScope = sanitizeRecentWorkspaceText(scope, 180) || "default";
    return `canvasia-engine:editor-recent-work:${safeScope}`;
  }

  function getRecentWorkspaceItemKey(entry) {
    if (!entry) {
      return "";
    }

    if (entry.type === "script") {
      return `script:${entry.sceneId ?? ""}:${entry.blockId ?? ""}`;
    }

    if (entry.type === "asset") {
      return `asset:${entry.assetId ?? ""}`;
    }

    if (entry.type === "character") {
      return `character:${entry.characterId ?? ""}`;
    }

    return `scene:${entry.sceneId ?? ""}`;
  }

  function getSafeRecentWorkspaceUpdatedAt(value, nowIso = () => new Date().toISOString()) {
    const updatedAt = new Date(value ?? nowIso());
    return Number.isNaN(updatedAt.getTime()) ? nowIso() : updatedAt.toISOString();
  }

  function sanitizeRecentWorkspaceEntry(source = {}, options = {}) {
    if (!source || typeof source !== "object") {
      return null;
    }

    const nowIso = typeof options.nowIso === "function" ? options.nowIso : () => new Date().toISOString();
    const type = getSafeRecentWorkspaceType(source.type);
    const base = {
      type,
      updatedAt: getSafeRecentWorkspaceUpdatedAt(source.updatedAt, nowIso),
      title: sanitizeRecentWorkspaceText(source.title, 160),
      subtitle: sanitizeRecentWorkspaceText(source.subtitle, 180),
      summary: sanitizeRecentWorkspaceText(source.summary, 240),
    };

    if (type === "script") {
      const sceneId = sanitizeRecentWorkspaceText(source.sceneId, 120);
      const blockId = sanitizeRecentWorkspaceText(source.blockId, 120);
      return sceneId && blockId ? { ...base, sceneId, blockId } : null;
    }

    if (type === "asset") {
      const assetId = sanitizeRecentWorkspaceText(source.assetId, 120);
      return assetId ? { ...base, assetId } : null;
    }

    if (type === "character") {
      const characterId = sanitizeRecentWorkspaceText(source.characterId, 120);
      return characterId ? { ...base, characterId } : null;
    }

    const sceneId = sanitizeRecentWorkspaceText(source.sceneId, 120);
    return sceneId ? { ...base, sceneId } : null;
  }

  function capRecentWorkspaceItems(entries, limit = RECENT_WORKSPACE_LIMIT) {
    const safeLimit = Number.isInteger(Number(limit)) && Number(limit) >= 0
      ? Number(limit)
      : RECENT_WORKSPACE_LIMIT;
    return (Array.isArray(entries) ? entries : [])
      .map((entry) => sanitizeRecentWorkspaceEntry(entry))
      .filter(Boolean)
      .slice(0, safeLimit);
  }

  function mergeRecentWorkspaceItem(entries, source, options = {}) {
    const limit = options.limit ?? RECENT_WORKSPACE_LIMIT;
    const entry = sanitizeRecentWorkspaceEntry(source, options);
    if (!entry) {
      return capRecentWorkspaceItems(entries, limit);
    }

    const nextKey = getRecentWorkspaceItemKey(entry);
    return [
      entry,
      ...capRecentWorkspaceItems(entries, limit).filter((item) => getRecentWorkspaceItemKey(item) !== nextKey),
    ].slice(0, Number.isInteger(Number(limit)) && Number(limit) >= 0 ? Number(limit) : RECENT_WORKSPACE_LIMIT);
  }

  function loadStoredRecentWorkspaceItems(storage, key, options = {}) {
    if (!storage || !key) {
      return [];
    }

    try {
      const raw = storage.getItem(key);
      if (!raw) {
        return [];
      }

      const parsed = JSON.parse(raw);
      const entries = Array.isArray(parsed) ? parsed : Array.isArray(parsed?.items) ? parsed.items : [];
      return capRecentWorkspaceItems(entries, options.limit ?? RECENT_WORKSPACE_LIMIT);
    } catch (error) {
      return [];
    }
  }

  function persistRecentWorkspaceItems(storage, key, entries, options = {}) {
    if (!storage || !key) {
      return false;
    }

    try {
      storage.setItem(
        key,
        JSON.stringify(capRecentWorkspaceItems(entries, options.limit ?? RECENT_WORKSPACE_LIMIT))
      );
      return true;
    } catch (error) {
      return false;
    }
  }

  function clearStoredRecentWorkspaceItems(storage, key) {
    if (!storage || !key) {
      return false;
    }

    try {
      storage.removeItem(key);
      return true;
    } catch (error) {
      return false;
    }
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function formatDate(value, options = {}) {
    if (!value) {
      return "未知";
    }

    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return String(value);
    }

    return date.toLocaleString(options.locale || "zh-CN", options.formatOptions);
  }

  function getDashboardTaskToneClass(tone) {
    if (tone === "danger") {
      return "danger-text";
    }
    if (tone === "warn") {
      return "warn-text";
    }
    if (tone === "good") {
      return "good-text";
    }
    return "";
  }

  function renderEmpty(text, options = {}) {
    const escape = typeof options.escapeHtml === "function" ? options.escapeHtml : escapeHtml;
    return `<div class="empty-note">${escape(text)}</div>`;
  }

  function renderRouteMetricCard(label, value, hint, options = {}) {
    if (typeof options.renderRouteMetricCard === "function") {
      return options.renderRouteMetricCard(label, value, hint);
    }

    const escape = typeof options.escapeHtml === "function" ? options.escapeHtml : escapeHtml;
    return `
    <article class="route-metric-card">
      <span>${escape(label)}</span>
      <strong>${escape(String(value))}</strong>
      <small>${escape(hint)}</small>
    </article>
  `;
  }

  function renderDashboardRecentWorkspaceCard(item, options = {}) {
    const escape = typeof options.escapeHtml === "function" ? options.escapeHtml : escapeHtml;
    const format = typeof options.formatDate === "function" ? options.formatDate : formatDate;
    const getToneClass =
      typeof options.getDashboardTaskToneClass === "function"
        ? options.getDashboardTaskToneClass
        : getDashboardTaskToneClass;
    const renderActions =
      typeof options.renderDashboardTaskActions === "function"
        ? options.renderDashboardTaskActions
        : () => "";

    return `
    <article class="detail-card recent-work-card is-${item.tone}">
      <div class="recent-work-top">
        <span class="issue-tag ${getToneClass(item.tone)}">${escape(
          getRecentWorkspaceTypeLabel(item.type)
        )}</span>
        <span class="recent-work-time">${escape(format(item.updatedAt))}</span>
      </div>
      <strong>${escape(item.title)}</strong>
      <p class="recent-work-summary">${escape(item.summary)}</p>
      <div class="detail-meta">${escape(item.subtitle)}</div>
      <div class="script-entry-actions">
        ${renderActions(item.actions)}
      </div>
    </article>
  `;
  }

  function renderDashboardRecentWorkspacePanel(items = [], options = {}) {
    const safeItems = Array.isArray(items) ? items : [];
    const sceneCount = safeItems.filter((item) => item.type === "scene").length;
    const scriptCount = safeItems.filter((item) => item.type === "script").length;
    const assetCount = safeItems.filter((item) => item.type === "asset").length;
    const characterCount = safeItems.filter((item) => item.type === "character").length;
    const renderBlank =
      typeof options.renderEmpty === "function" ? options.renderEmpty : (text) => renderEmpty(text, options);

    return `
    <section class="panel recent-work-panel">
      <div class="panel-heading recent-work-heading">
        <div>
          <h2>最近工作区</h2>
          <span class="panel-note">最近使用过的场景、台本、素材和角色会记录在这里</span>
        </div>
        <button
          class="toolbar-button"
          type="button"
          data-action="clear-recent-workspace"
          ${safeItems.length > 0 ? "" : "disabled"}
        >
          清空记录
        </button>
      </div>
      <div class="route-summary-strip">
        ${renderRouteMetricCard("场景", sceneCount, "最近切过或回去继续写的场景", options)}
        ${renderRouteMetricCard("台本", scriptCount, "最近直接定位过的正文入口", options)}
        ${renderRouteMetricCard("素材", assetCount, "最近查看或处理过的素材", options)}
        ${renderRouteMetricCard("角色", characterCount, "最近回头确认过的角色资料", options)}
      </div>
      ${
        safeItems.length > 0
          ? `<div class="recent-work-grid">${safeItems
              .map((item) => renderDashboardRecentWorkspaceCard(item, options))
              .join("")}</div>`
          : renderBlank("开始写剧情、补素材、查看角色或定位台本后，这里会记录最近的工作位置。")
      }
    </section>
  `;
  }

  global.CanvasiaEditorRecentWorkspace = Object.freeze({
    RECENT_WORKSPACE_LIMIT,
    RECENT_WORKSPACE_TYPE_LABELS,
    getSafeRecentWorkspaceType,
    getRecentWorkspaceTypeLabel,
    sanitizeRecentWorkspaceText,
    getRecentWorkspaceStorageKey,
    getRecentWorkspaceItemKey,
    sanitizeRecentWorkspaceEntry,
    capRecentWorkspaceItems,
    mergeRecentWorkspaceItem,
    loadStoredRecentWorkspaceItems,
    persistRecentWorkspaceItems,
    clearStoredRecentWorkspaceItems,
    renderDashboardRecentWorkspaceCard,
    renderDashboardRecentWorkspacePanel,
  });
})(typeof window !== "undefined" ? window : globalThis);
