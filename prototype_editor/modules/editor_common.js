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
  });
})(typeof window !== "undefined" ? window : globalThis);
