(function attachUiThemeTools(global) {
  const UI_THEME_MODE_LABELS = Object.freeze({
    auto: "自动切换",
    light: "浅色模式",
    dark: "深色模式",
  });

  const EDITOR_UI_THEME_STORAGE_KEY = "canvasia-engine:editor-ui-theme-mode";

  function hasOwn(source, key) {
    return Object.prototype.hasOwnProperty.call(source, key);
  }

  function getSafeUiThemeMode(mode) {
    const safeMode = String(mode ?? "").trim();
    return hasOwn(UI_THEME_MODE_LABELS, safeMode) ? safeMode : "auto";
  }

  function getUiThemeModeLabel(mode) {
    return UI_THEME_MODE_LABELS[getSafeUiThemeMode(mode)];
  }

  function getSafeDateHour(now) {
    const timestamp = typeof now?.getTime === "function" ? now.getTime() : Number.NaN;
    return Number.isNaN(timestamp) ? new Date().getHours() : now.getHours();
  }

  function resolveUiTheme(mode = "auto", now = new Date()) {
    const safeMode = getSafeUiThemeMode(mode);
    if (safeMode === "light" || safeMode === "dark") {
      return safeMode;
    }
    const hour = getSafeDateHour(now);
    return hour >= 7 && hour < 19 ? "light" : "dark";
  }

  function loadStoredEditorUiThemeMode(storage, fallbackMode = "auto") {
    if (!storage) {
      return getSafeUiThemeMode(fallbackMode);
    }
    try {
      return getSafeUiThemeMode(storage.getItem(EDITOR_UI_THEME_STORAGE_KEY));
    } catch (error) {
      return getSafeUiThemeMode(fallbackMode);
    }
  }

  function persistStoredEditorUiThemeMode(storage, mode) {
    if (!storage) {
      return false;
    }
    try {
      storage.setItem(EDITOR_UI_THEME_STORAGE_KEY, getSafeUiThemeMode(mode));
      return true;
    } catch (error) {
      return false;
    }
  }

  global.CanvasiaEditorUiTheme = Object.freeze({
    UI_THEME_MODE_LABELS,
    EDITOR_UI_THEME_STORAGE_KEY,
    getSafeUiThemeMode,
    getUiThemeModeLabel,
    resolveUiTheme,
    loadStoredEditorUiThemeMode,
    persistStoredEditorUiThemeMode,
  });
})(typeof window !== "undefined" ? window : globalThis);
