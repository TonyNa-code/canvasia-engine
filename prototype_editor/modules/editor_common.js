(function attachEditorCommonTools(global) {
  function sanitizeFileName(value) {
    return String(value ?? "")
      .trim()
      .replace(/[\\/:*?"<>|]/g, "_")
      .replace(/\s+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_+|_+$/g, "");
  }

  function formatCsvCell(value) {
    const text = String(value ?? "");
    return `"${text.replaceAll('"', '""')}"`;
  }

  function truncateText(value, maxLength = 32) {
    const text = String(value ?? "").trim();
    const safeMaxLength = Number.isFinite(Number(maxLength)) ? Number(maxLength) : 32;

    if (text.length <= safeMaxLength) {
      return text;
    }

    return `${text.slice(0, Math.max(safeMaxLength - 1, 1))}…`;
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

  function getSafeNonNegativeNumber(value, fallback = 0) {
    const parsed = Number.parseInt(value ?? "", 10);
    return Number.isFinite(parsed) ? Math.max(parsed, 0) : fallback;
  }

  function getSafeNumber(value, fallback = 0) {
    const parsed = Number.parseFloat(value ?? "");
    return Number.isFinite(parsed) ? parsed : fallback;
  }

  function buildTemplateAssetUrl(relativePath, publicRoot = "") {
    const normalized = String(relativePath ?? "")
      .replaceAll("\\", "/")
      .replace(/^\/+/, "")
      .split("/")
      .filter(Boolean)
      .map((part) => encodeURIComponent(part))
      .join("/");
    const safePublicRoot = String(publicRoot ?? "").replace(/\/+$/, "");
    return normalized && safePublicRoot ? `${safePublicRoot}/${normalized}` : "";
  }

  function formatFileSize(bytes) {
    const size = Number(bytes);
    if (!Number.isFinite(size) || size < 0) {
      return "未知";
    }
    if (size < 1024) {
      return `${size} B`;
    }
    if (size < 1024 * 1024) {
      return `${(size / 1024).toFixed(size < 10 * 1024 ? 1 : 0)} KB`;
    }
    return `${(size / (1024 * 1024)).toFixed(size < 10 * 1024 * 1024 ? 1 : 0)} MB`;
  }

  function clamp(value, min, max) {
    return Math.min(Math.max(value, min), max);
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function renderDetailRows(rows) {
    return (Array.isArray(rows) ? rows : [])
      .map(
        ([label, value]) => `
        <div class="detail-row">
          <label>${escapeHtml(label)}</label>
          <div class="value">${escapeHtml(String(value))}</div>
        </div>
      `
      )
      .join("");
  }

  function renderStatCard(label, value) {
    return `
    <article class="stat-card">
      <h3>${escapeHtml(label)}</h3>
      <strong>${value}</strong>
    </article>
  `;
  }

  function renderEmpty(text) {
    return `<div class="empty-note">${escapeHtml(text)}</div>`;
  }

  function renderQuickActionButton(action, emphasized = false) {
    const className = `toolbar-button${emphasized ? " toolbar-button-primary" : ""}`;
    const label = escapeHtml(action.label ?? "去处理");
    const disabledMarkup = action.disabled ? ' disabled aria-disabled="true"' : "";
    const titleMarkup = action.title ? ` title="${escapeHtml(action.title)}"` : "";
    const datasetMarkup = Object.entries(action.dataset ?? {})
      .map(([key, value]) => ` data-${key}="${escapeHtml(String(value ?? ""))}"`)
      .join("");

    if (action.href) {
      return `
      <a
        class="${className}"
        href="${escapeHtml(action.href)}"
        target="_blank"
        rel="noreferrer"
      >
        ${label}
      </a>
    `;
    }

    if (action.action === "open-scene-from-map" || action.action === "preview-scene-from-map") {
      return `
      <button
        type="button"
        class="${className}"
        data-action="${action.action}"
        data-scene-id="${escapeHtml(action.sceneId ?? "")}"
      >
        ${label}
      </button>
    `;
    }

    if (action.action === "open-character-line") {
      return `
      <button
        type="button"
        class="${className}"
        data-action="open-character-line"
        data-scene-id="${escapeHtml(action.sceneId ?? "")}"
        data-block-id="${escapeHtml(action.blockId ?? "")}"
      >
        ${label}
      </button>
    `;
    }

    if (action.action === "preview-story-location") {
      return `
      <button
        type="button"
        class="${className}"
        data-action="preview-story-location"
        data-scene-id="${escapeHtml(action.sceneId ?? "")}"
        data-block-id="${escapeHtml(action.blockId ?? "")}"
      >
        ${label}
      </button>
    `;
    }

    if (action.action === "open-dashboard-character") {
      return `
      <button
        type="button"
        class="${className}"
        data-action="open-dashboard-character"
        data-character-id="${escapeHtml(action.characterId ?? "")}"
      >
        ${label}
      </button>
    `;
    }

    if (action.action === "open-script-chapter-scene") {
      return `
      <button
        type="button"
        class="${className}"
        data-action="open-script-chapter-scene"
        data-chapter-id="${escapeHtml(action.chapterId ?? "")}"
      >
        ${label}
      </button>
    `;
    }

    if (action.action === "open-asset-from-issue") {
      return `
      <button
        type="button"
        class="${className}"
        data-action="open-asset-from-issue"
        data-asset-id="${escapeHtml(action.assetId ?? "")}"
      >
        ${label}
      </button>
    `;
    }

    if (action.action === "switch-screen") {
      const screen = action.screen ?? action.dataset?.screen ?? "dashboard";
      return `
      <button
        type="button"
        class="${className}"
        data-action="switch-screen"
        data-screen="${escapeHtml(screen)}"
      >
        ${label}
      </button>
    `;
    }

    return `
    <button
      type="button"
      class="${className}"
      data-action="${escapeHtml(action.action ?? "")}"
      ${titleMarkup}
      ${disabledMarkup}
      ${datasetMarkup}
    >
      ${label}
    </button>
  `;
  }

  function renderDashboardTaskActions(actions = []) {
    return actions
      .slice(0, 2)
      .map((action, index) => renderQuickActionButton(action, index === 0))
      .join("");
  }

  function renderRouteMetricCard(label, value, hint) {
    return `
    <article class="route-metric-card">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(String(value))}</strong>
      <small>${escapeHtml(hint)}</small>
    </article>
  `;
  }

  global.CanvasiaEditorCommon = Object.freeze({
    sanitizeFileName,
    formatCsvCell,
    truncateText,
    formatDate,
    getSafeNonNegativeNumber,
    getSafeNumber,
    buildTemplateAssetUrl,
    formatFileSize,
    clamp,
    escapeHtml,
    renderDetailRows,
    renderStatCard,
    renderEmpty,
    renderQuickActionButton,
    renderDashboardTaskActions,
    renderRouteMetricCard,
  });
})(typeof window !== "undefined" ? window : globalThis);
