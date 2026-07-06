(function attachExportFileNameTools(global) {
  "use strict";

  function fallbackSanitizeFileName(value) {
    return String(value ?? "")
      .trim()
      .replace(/[\\/:*?"<>|]/g, "_")
      .replace(/\s+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_+|_+$/g, "");
  }

  function getSanitizer(options = {}) {
    return (
      (typeof options.sanitizeFileName === "function" && options.sanitizeFileName) ||
      global.CanvasiaEditorCommon?.sanitizeFileName ||
      fallbackSanitizeFileName
    );
  }

  function buildFileNameDateStamp(dateValue = new Date()) {
    const date = dateValue instanceof Date ? dateValue : new Date(dateValue);
    const safeDate = Number.isNaN(date.getTime()) ? new Date() : date;
    return [
      safeDate.getFullYear(),
      String(safeDate.getMonth() + 1).padStart(2, "0"),
      String(safeDate.getDate()).padStart(2, "0"),
    ].join("");
  }

  function getProjectFileNameBase(options = {}) {
    const fallback = String(options.fallback || "canvasia-engine").trim() || "canvasia-engine";
    const sanitizeFileName = getSanitizer(options);
    return sanitizeFileName(options.projectTitle || fallback) || fallback;
  }

  function normalizeExtension(extension = "md") {
    return String(extension ?? "md").replace(/^\.+/, "").trim() || "md";
  }

  function buildDatedProjectFileName(slug, extension = "md", options = {}) {
    const sanitizeFileName = getSanitizer(options);
    const safeSlug = sanitizeFileName(slug) || "export";
    const projectTitle = getProjectFileNameBase(options);
    const dateStamp = buildFileNameDateStamp(options.dateValue);
    return `${projectTitle}_${safeSlug}_${dateStamp}.${normalizeExtension(extension)}`;
  }

  global.CanvasiaEditorExportFileNames = Object.freeze({
    buildDatedProjectFileName,
    buildFileNameDateStamp,
    getProjectFileNameBase,
    normalizeExtension,
  });
})(typeof window !== "undefined" ? window : globalThis);
