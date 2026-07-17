import { sanitizeVoiceMixProfiles } from "./runtime_voice_mixer.js";
import {
  DEFAULT_RUNTIME_KEY_BINDINGS,
  sanitizeRuntimeKeyBindings,
} from "./runtime_controls.js";

export const TEXT_SPEED_LABELS = Object.freeze({
  slow: "慢一点",
  normal: "正常",
  fast: "快一点",
  instant: "立刻显示",
});

export const DIALOG_THEME_LABELS = Object.freeze({
  project: "项目样式",
  warm: "暖光标准",
  moonlight: "夜色月光",
  paper: "纸页回忆",
  transparent: "透明无框",
});

export const UI_THEME_MODE_LABELS = Object.freeze({
  auto: "自动切换",
  light: "浅色模式",
  dark: "深色模式",
});

export const PLAYBACK_DEFAULTS = Object.freeze({
  textSpeed: "normal",
  language: "",
  dialogTheme: "project",
  uiThemeMode: "auto",
  autoPlay: false,
  skipRead: false,
  voiceEnabled: true,
  voiceDuckingEnabled: true,
  bgmVolume: 72,
  sfxVolume: 85,
  voiceVolume: 92,
  voiceDuckingRatio: 45,
  voiceMix: Object.freeze({}),
  keyBindings: DEFAULT_RUNTIME_KEY_BINDINGS,
});

const DEFAULT_PROJECT_RUNTIME_SETTINGS = Object.freeze({
  formalSaveSlotCount: 24,
  performanceProfile: "standard",
});
const VOICE_DUCKING_RATIO_LIMITS = Object.freeze({ min: 15, max: 100 });

export const RUNTIME_PERFORMANCE_PROFILE_LABELS = Object.freeze({
  standard: "标准 PC / 网页",
  web: "网页轻量",
  mobile_low: "低配 / 移动端",
  high_quality_pc: "高画质 PC",
});

function clamp(value, min, max) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return min;
  }
  return Math.min(max, Math.max(min, numeric));
}

function getSafeNumber(value, fallback = 0) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : fallback;
}

function normalizePlaybackLanguage(value, fallback = "", options = {}) {
  if (typeof options.getSafeLanguage === "function") {
    return options.getSafeLanguage(value ?? fallback);
  }
  return String(value ?? fallback ?? "").trim();
}

export function getSafeTextSpeed(speed) {
  return Object.hasOwn(TEXT_SPEED_LABELS, speed) ? speed : "normal";
}

export function getTextSpeedLabel(speed) {
  return TEXT_SPEED_LABELS[getSafeTextSpeed(speed)];
}

export function getSafeDialogTheme(theme) {
  return Object.hasOwn(DIALOG_THEME_LABELS, theme) ? theme : "project";
}

export function getDialogThemeLabel(theme) {
  return DIALOG_THEME_LABELS[getSafeDialogTheme(theme)];
}

export function getSafeUiThemeMode(mode) {
  return Object.hasOwn(UI_THEME_MODE_LABELS, mode) ? mode : "auto";
}

export function getUiThemeModeLabel(mode) {
  return UI_THEME_MODE_LABELS[getSafeUiThemeMode(mode)];
}

export function getSafeVolumePercent(value, fallback = 100) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return fallback;
  }
  return Math.min(100, Math.max(0, Math.round(numeric)));
}

export function getVolumeRatio(value, fallback = 100) {
  return getSafeVolumePercent(value, fallback) / 100;
}

export function getSafeVoiceDuckingRatioPercent(value, fallback = PLAYBACK_DEFAULTS.voiceDuckingRatio) {
  const numeric = Number(value);
  const fallbackValue = getSafeVolumePercent(fallback, PLAYBACK_DEFAULTS.voiceDuckingRatio);
  if (!Number.isFinite(numeric)) {
    return Math.min(VOICE_DUCKING_RATIO_LIMITS.max, Math.max(VOICE_DUCKING_RATIO_LIMITS.min, fallbackValue));
  }
  return Math.min(VOICE_DUCKING_RATIO_LIMITS.max, Math.max(VOICE_DUCKING_RATIO_LIMITS.min, Math.round(numeric)));
}

export function formatVolumePercent(value, fallback = 100) {
  return `${getSafeVolumePercent(value, fallback)}%`;
}

export function getSafeProjectFormalSaveSlotCount(value) {
  return clamp(
    Math.round(getSafeNumber(value, DEFAULT_PROJECT_RUNTIME_SETTINGS.formalSaveSlotCount)),
    3,
    120
  );
}

export function getSafeProjectRuntimePerformanceProfile(value) {
  const key = String(value ?? DEFAULT_PROJECT_RUNTIME_SETTINGS.performanceProfile).trim().toLowerCase();
  return Object.hasOwn(RUNTIME_PERFORMANCE_PROFILE_LABELS, key) ? key : DEFAULT_PROJECT_RUNTIME_SETTINGS.performanceProfile;
}

export function getProjectRuntimeSettings(project = {}) {
  const runtimeSettings = project?.runtimeSettings ?? {};
  return {
    formalSaveSlotCount: getSafeProjectFormalSaveSlotCount(runtimeSettings.formalSaveSlotCount),
    performanceProfile: getSafeProjectRuntimePerformanceProfile(runtimeSettings.performanceProfile),
    defaultTextSpeed: getSafeTextSpeed(runtimeSettings.defaultTextSpeed ?? PLAYBACK_DEFAULTS.textSpeed),
    defaultDialogTheme: getSafeDialogTheme(runtimeSettings.defaultDialogTheme ?? PLAYBACK_DEFAULTS.dialogTheme),
    defaultUiThemeMode: getSafeUiThemeMode(runtimeSettings.defaultUiThemeMode ?? PLAYBACK_DEFAULTS.uiThemeMode),
    defaultBgmVolume: getSafeVolumePercent(runtimeSettings.defaultBgmVolume, PLAYBACK_DEFAULTS.bgmVolume),
    defaultSfxVolume: getSafeVolumePercent(runtimeSettings.defaultSfxVolume, PLAYBACK_DEFAULTS.sfxVolume),
    defaultVoiceVolume: getSafeVolumePercent(runtimeSettings.defaultVoiceVolume, PLAYBACK_DEFAULTS.voiceVolume),
    defaultVoiceDuckingRatio: getSafeVoiceDuckingRatioPercent(
      runtimeSettings.defaultVoiceDuckingRatio,
      PLAYBACK_DEFAULTS.voiceDuckingRatio
    ),
    defaultVoiceEnabled: runtimeSettings.defaultVoiceEnabled !== false,
    defaultVoiceDuckingEnabled: runtimeSettings.defaultVoiceDuckingEnabled !== false,
  };
}

export function getProjectFormalSaveSlotCount(project = {}) {
  return getProjectRuntimeSettings(project).formalSaveSlotCount;
}

export function sanitizePlaybackSettings(source = {}, options = {}) {
  return {
    textSpeed: getSafeTextSpeed(source.textSpeed ?? PLAYBACK_DEFAULTS.textSpeed),
    language: normalizePlaybackLanguage(source.language, PLAYBACK_DEFAULTS.language, options),
    dialogTheme: getSafeDialogTheme(source.dialogTheme ?? PLAYBACK_DEFAULTS.dialogTheme),
    uiThemeMode: getSafeUiThemeMode(source.uiThemeMode ?? PLAYBACK_DEFAULTS.uiThemeMode),
    autoPlay: Boolean(source.autoPlay ?? PLAYBACK_DEFAULTS.autoPlay),
    skipRead: Boolean(source.skipRead ?? PLAYBACK_DEFAULTS.skipRead),
    voiceEnabled: source.voiceEnabled !== false,
    voiceDuckingEnabled: source.voiceDuckingEnabled !== false,
    bgmVolume: getSafeVolumePercent(source.bgmVolume, PLAYBACK_DEFAULTS.bgmVolume),
    sfxVolume: getSafeVolumePercent(source.sfxVolume, PLAYBACK_DEFAULTS.sfxVolume),
    voiceVolume: getSafeVolumePercent(source.voiceVolume, PLAYBACK_DEFAULTS.voiceVolume),
    voiceDuckingRatio: getSafeVoiceDuckingRatioPercent(source.voiceDuckingRatio, PLAYBACK_DEFAULTS.voiceDuckingRatio),
    voiceMix: sanitizeVoiceMixProfiles(source.voiceMix ?? PLAYBACK_DEFAULTS.voiceMix),
    keyBindings: sanitizeRuntimeKeyBindings(source.keyBindings ?? PLAYBACK_DEFAULTS.keyBindings),
  };
}

export function buildProjectPlaybackDefaults(project = {}, defaultLanguage = "", options = {}) {
  const runtimeSettings = getProjectRuntimeSettings(project);
  return sanitizePlaybackSettings(
    {
      ...PLAYBACK_DEFAULTS,
      textSpeed: runtimeSettings.defaultTextSpeed,
      language: defaultLanguage,
      dialogTheme: runtimeSettings.defaultDialogTheme,
      uiThemeMode: runtimeSettings.defaultUiThemeMode,
      voiceEnabled: runtimeSettings.defaultVoiceEnabled,
      voiceDuckingEnabled: runtimeSettings.defaultVoiceDuckingEnabled,
      bgmVolume: runtimeSettings.defaultBgmVolume,
      sfxVolume: runtimeSettings.defaultSfxVolume,
      voiceVolume: runtimeSettings.defaultVoiceVolume,
      voiceDuckingRatio: runtimeSettings.defaultVoiceDuckingRatio,
    },
    options
  );
}
