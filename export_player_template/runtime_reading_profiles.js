export const READING_PROFILE_IDS = Object.freeze(["standard", "comfortable", "large", "calm"]);

export const READING_PROFILE_LABELS = Object.freeze({
  standard: "原作演出",
  comfortable: "舒适阅读",
  large: "大字阅读",
  calm: "静态阅读",
  custom: "自定义组合",
});

export const READING_PROFILE_DESCRIPTIONS = Object.freeze({
  standard: "保留标准字号、文字速度和原始演出。",
  comfortable: "字号略大，并柔化闪屏、震动和转场。",
  large: "使用最大字号、较慢文字和柔和演出。",
  calm: "放大文字并停止短暂动态演出。",
  custom: "当前设置由玩家逐项调整。",
});

export const READING_PROFILES = Object.freeze({
  standard: Object.freeze({
    textSpeed: "normal",
    textScalePercent: 100,
    dialogBoxOpacityPercent: 100,
    visualComfort: "standard",
  }),
  comfortable: Object.freeze({
    textSpeed: "normal",
    textScalePercent: 110,
    dialogBoxOpacityPercent: 100,
    visualComfort: "gentle",
  }),
  large: Object.freeze({
    textSpeed: "slow",
    textScalePercent: 125,
    dialogBoxOpacityPercent: 100,
    visualComfort: "gentle",
  }),
  calm: Object.freeze({
    textSpeed: "normal",
    textScalePercent: 110,
    dialogBoxOpacityPercent: 100,
    visualComfort: "static",
  }),
});

function clampInteger(value, minimum, maximum, fallback) {
  const numeric = Number(value);
  const safeValue = Number.isFinite(numeric) ? Math.round(numeric) : fallback;
  return Math.min(maximum, Math.max(minimum, safeValue));
}

export function getSafeReadingProfileId(value, fallback = "standard") {
  const safeFallback = READING_PROFILE_IDS.includes(fallback) ? fallback : "standard";
  const profileId = String(value ?? safeFallback).trim().toLowerCase();
  return READING_PROFILE_IDS.includes(profileId) ? profileId : safeFallback;
}

export function getReadingProfileLabel(value) {
  const profileId = value === "custom" ? "custom" : getSafeReadingProfileId(value);
  return READING_PROFILE_LABELS[profileId];
}

export function getReadingProfileDescription(value) {
  const profileId = value === "custom" ? "custom" : getSafeReadingProfileId(value);
  return READING_PROFILE_DESCRIPTIONS[profileId];
}

export function getSafeReadingTextScalePercent(value, fallback = 100) {
  return clampInteger(value, 90, 125, clampInteger(fallback, 90, 125, 100));
}

export function getSafeDialogBoxOpacityPercent(value, fallback = 100) {
  return clampInteger(value, 0, 100, clampInteger(fallback, 0, 100, 100));
}

export function applyReadingProfile(settings = {}, profileId = "standard") {
  const safeProfileId = getSafeReadingProfileId(profileId);
  return {
    ...(settings && typeof settings === "object" ? settings : {}),
    ...READING_PROFILES[safeProfileId],
  };
}

export function detectReadingProfile(settings = {}) {
  const source = settings && typeof settings === "object" ? settings : {};
  const normalized = {
    textSpeed: String(source.textSpeed ?? "normal").trim().toLowerCase(),
    textScalePercent: getSafeReadingTextScalePercent(source.textScalePercent),
    dialogBoxOpacityPercent: getSafeDialogBoxOpacityPercent(source.dialogBoxOpacityPercent),
    visualComfort: String(source.visualComfort ?? "standard").trim().toLowerCase(),
  };
  return (
    READING_PROFILE_IDS.find((profileId) => {
      const profile = READING_PROFILES[profileId];
      return Object.entries(profile).every(([key, value]) => normalized[key] === value);
    }) ?? "custom"
  );
}

export function getReadingProfileSummary(settings = {}) {
  const profileId = detectReadingProfile(settings);
  return {
    profileId,
    label: getReadingProfileLabel(profileId),
    description: getReadingProfileDescription(profileId),
    textScalePercent: getSafeReadingTextScalePercent(settings.textScalePercent),
    dialogBoxOpacityPercent: getSafeDialogBoxOpacityPercent(settings.dialogBoxOpacityPercent),
  };
}

const runtimeReadingProfilesApi = Object.freeze({
  READING_PROFILE_IDS,
  READING_PROFILE_LABELS,
  READING_PROFILE_DESCRIPTIONS,
  READING_PROFILES,
  getSafeReadingProfileId,
  getReadingProfileLabel,
  getReadingProfileDescription,
  getSafeReadingTextScalePercent,
  getSafeDialogBoxOpacityPercent,
  applyReadingProfile,
  detectReadingProfile,
  getReadingProfileSummary,
});

globalThis.CanvasiaRuntimeReadingProfiles = runtimeReadingProfilesApi;
