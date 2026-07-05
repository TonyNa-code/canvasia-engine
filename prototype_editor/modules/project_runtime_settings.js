(function attachProjectRuntimeSettingsTools(global) {
  "use strict";

  const DEFAULT_SAVE_SLOT_COUNT_LIMITS = Object.freeze({ min: 3, max: 120 });
  const DEFAULT_RUNTIME_SETTINGS = Object.freeze({
    formalSaveSlotCount: 24,
    defaultTextSpeed: "normal",
    defaultDialogTheme: "project",
    defaultUiThemeMode: "auto",
    defaultBgmVolume: 72,
    defaultSfxVolume: 85,
    defaultVoiceVolume: 92,
    defaultVoiceEnabled: true,
    defaultVoiceDuckingEnabled: true,
  });
  const TEXT_SPEED_CPS = Object.freeze({
    slow: 24,
    normal: 42,
    fast: 72,
    instant: 10000,
  });
  const RUNTIME_DIALOG_THEMES = Object.freeze(["project", "warm", "moonlight", "paper", "transparent"]);
  const RUNTIME_UI_THEME_MODES = Object.freeze(["auto", "light", "dark"]);

  function hasOwn(source, key) {
    return Object.prototype.hasOwnProperty.call(source ?? {}, key);
  }

  function cleanKey(value, fallback = "") {
    const text = String(value ?? "").trim().toLowerCase();
    return text || fallback;
  }

  function clamp(value, min, max) {
    return Math.min(Math.max(value, min), max);
  }

  function getSafeNumber(value, fallback = 0) {
    const number = Number(value);
    return Number.isFinite(number) ? number : fallback;
  }

  function getSafeKey(allowedKeys, value, fallback) {
    const key = cleanKey(value, fallback);
    if (Array.isArray(allowedKeys)) {
      return allowedKeys.includes(key) ? key : fallback;
    }
    return hasOwn(allowedKeys, key) ? key : fallback;
  }

  function getRuntimeDefaults(options = {}) {
    return { ...DEFAULT_RUNTIME_SETTINGS, ...(options.defaultRuntimeSettings ?? {}) };
  }

  function getSaveSlotLimits(options = {}) {
    return { ...DEFAULT_SAVE_SLOT_COUNT_LIMITS, ...(options.saveSlotCountLimits ?? {}) };
  }

  function getSafeProjectFormalSaveSlotCount(value, options = {}) {
    const limits = getSaveSlotLimits(options);
    const defaults = getRuntimeDefaults(options);
    return clamp(Math.round(getSafeNumber(value, defaults.formalSaveSlotCount)), limits.min, limits.max);
  }

  function getSafeProjectRuntimeTextSpeed(value, options = {}) {
    const defaults = getRuntimeDefaults(options);
    return getSafeKey(options.runtimeTextSpeedLabels || TEXT_SPEED_CPS, value, defaults.defaultTextSpeed);
  }

  function getSafeProjectRuntimeDialogTheme(value, options = {}) {
    const defaults = getRuntimeDefaults(options);
    return getSafeKey(options.runtimeDialogThemeLabels || RUNTIME_DIALOG_THEMES, value, defaults.defaultDialogTheme);
  }

  function getSafeProjectRuntimeUiThemeMode(value, options = {}) {
    const defaults = getRuntimeDefaults(options);
    return getSafeKey(options.runtimeUiThemeModeLabels || RUNTIME_UI_THEME_MODES, value, defaults.defaultUiThemeMode);
  }

  function getSafeProjectRuntimeVolume(value, fallback = 100) {
    return clamp(Math.round(getSafeNumber(value, fallback)), 0, 100);
  }

  function getProjectRuntimeSettings(project = {}, options = {}) {
    const runtimeSettings = project?.runtimeSettings ?? {};
    const defaults = getRuntimeDefaults(options);
    return {
      formalSaveSlotCount: getSafeProjectFormalSaveSlotCount(runtimeSettings.formalSaveSlotCount, options),
      defaultTextSpeed: getSafeProjectRuntimeTextSpeed(runtimeSettings.defaultTextSpeed, options),
      defaultDialogTheme: getSafeProjectRuntimeDialogTheme(runtimeSettings.defaultDialogTheme, options),
      defaultUiThemeMode: getSafeProjectRuntimeUiThemeMode(runtimeSettings.defaultUiThemeMode, options),
      defaultBgmVolume: getSafeProjectRuntimeVolume(runtimeSettings.defaultBgmVolume, defaults.defaultBgmVolume),
      defaultSfxVolume: getSafeProjectRuntimeVolume(runtimeSettings.defaultSfxVolume, defaults.defaultSfxVolume),
      defaultVoiceVolume: getSafeProjectRuntimeVolume(runtimeSettings.defaultVoiceVolume, defaults.defaultVoiceVolume),
      defaultVoiceEnabled: runtimeSettings.defaultVoiceEnabled !== false,
      defaultVoiceDuckingEnabled: runtimeSettings.defaultVoiceDuckingEnabled !== false,
    };
  }

  function getProjectFormalSaveSlotCount(project = {}, options = {}) {
    return getProjectRuntimeSettings(project, options).formalSaveSlotCount;
  }

  function getEffectiveTextSpeed(block = {}, runtimeSettings = {}, options = {}) {
    const explicitSpeed = getSafeProjectRuntimeTextSpeed(block?.textSpeed, {
      ...options,
      defaultRuntimeSettings: { ...getRuntimeDefaults(options), defaultTextSpeed: "" },
    });
    if (explicitSpeed) {
      return explicitSpeed;
    }
    const defaultSpeed = getProjectRuntimeSettings({ runtimeSettings }, options).defaultTextSpeed;
    return defaultSpeed === "normal" ? "" : defaultSpeed;
  }

  function getEffectiveTextCps(block = {}, runtimeSettings = {}, options = {}) {
    const speed = getEffectiveTextSpeed(block, runtimeSettings, options);
    return speed ? TEXT_SPEED_CPS[speed] : null;
  }

  function getRuntimeVolumeRatio(runtimeSettings = {}, key, options = {}) {
    const settings = getProjectRuntimeSettings({ runtimeSettings }, options);
    return Number(((settings[key] ?? 100) / 100).toFixed(2));
  }

  function getRenpyPreferenceTextCps(defaultSpeed) {
    return defaultSpeed === "instant" ? 0 : TEXT_SPEED_CPS[defaultSpeed];
  }

  function getRenpyRuntimeSummary(runtimeSettings = {}, options = {}) {
    const settings = getProjectRuntimeSettings({ runtimeSettings }, options);
    const voiceVolume = settings.defaultVoiceEnabled ? getRuntimeVolumeRatio(settings, "defaultVoiceVolume", options) : 0;
    return {
      defaultTextSpeed: settings.defaultTextSpeed,
      defaultTextCps: TEXT_SPEED_CPS[settings.defaultTextSpeed],
      renpyPreferenceTextCps: getRenpyPreferenceTextCps(settings.defaultTextSpeed),
      defaultBgmVolume: getRuntimeVolumeRatio(settings, "defaultBgmVolume", options),
      defaultSfxVolume: getRuntimeVolumeRatio(settings, "defaultSfxVolume", options),
      defaultVoiceVolume: getRuntimeVolumeRatio(settings, "defaultVoiceVolume", options),
      effectiveVoiceVolume: voiceVolume,
      defaultVoiceEnabled: settings.defaultVoiceEnabled,
      defaultVoiceDuckingEnabled: settings.defaultVoiceDuckingEnabled,
      formalSaveSlotCount: settings.formalSaveSlotCount,
    };
  }

  global.CanvasiaEditorProjectRuntimeSettings = Object.freeze({
    DEFAULT_SAVE_SLOT_COUNT_LIMITS,
    DEFAULT_RUNTIME_SETTINGS,
    TEXT_SPEED_CPS,
    RUNTIME_DIALOG_THEMES,
    RUNTIME_UI_THEME_MODES,
    getSafeProjectFormalSaveSlotCount,
    getSafeProjectRuntimeTextSpeed,
    getSafeProjectRuntimeDialogTheme,
    getSafeProjectRuntimeUiThemeMode,
    getSafeProjectRuntimeVolume,
    getProjectRuntimeSettings,
    getProjectFormalSaveSlotCount,
    getEffectiveTextSpeed,
    getEffectiveTextCps,
    getRuntimeVolumeRatio,
    getRenpyPreferenceTextCps,
    getRenpyRuntimeSummary,
  });
})(typeof window !== "undefined" ? window : globalThis);
