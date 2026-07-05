import { renderOperationGuideGroups } from "./runtime_controls.js";
import {
  cancelAudioFade,
  disposeAudio,
  fadeAudioVolume,
  getRuntimeMusicTargetVolume as getRuntimeMusicTargetVolumeBase,
  getRuntimeSfxTargetVolume as getRuntimeSfxTargetVolumeBase,
  getRuntimeVoiceTargetVolume as getRuntimeVoiceTargetVolumeBase,
  getSafeAudioFadeMs,
  stopTrackedAudios,
} from "./runtime_audio.js";
import {
  getRuntimePreloadSummary,
  startRuntimePreload,
} from "./runtime_preload.js";
import {
  DIALOG_THEME_LABELS,
  PLAYBACK_DEFAULTS,
  TEXT_SPEED_LABELS,
  UI_THEME_MODE_LABELS,
  buildProjectPlaybackDefaults,
  formatVolumePercent,
  getDialogThemeLabel,
  getProjectFormalSaveSlotCount as getProjectFormalSaveSlotCountBase,
  getSafeDialogTheme,
  getSafeTextSpeed,
  getSafeUiThemeMode,
  getSafeVolumePercent,
  getTextSpeedLabel,
  getUiThemeModeLabel,
  getVolumeRatio,
  sanitizePlaybackSettings as sanitizePlaybackSettingsBase,
} from "./runtime_settings.js";

const DEFAULT_RUNTIME_LANGUAGE = "zh-CN";
const CHOICE_CONTINUE_TARGET = "__continue__";
const RUNTIME_LANGUAGE_LABELS = {
  "zh-CN": "简体中文",
  "ja-JP": "日本語",
  "en-US": "English",
};

function normalizeLanguageCode(value, fallback = DEFAULT_RUNTIME_LANGUAGE) {
  const rawValue = String(value ?? "").trim();
  if (!rawValue || !/^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8}){0,2}$/.test(rawValue)) {
    return fallback;
  }
  const parts = rawValue.split("-");
  return [
    parts[0].toLowerCase(),
    ...parts.slice(1).map((part, index) => (index === 0 && [2, 3].includes(part.length) ? part.toUpperCase() : part)),
  ].join("-");
}

function normalizeSupportedLanguages(rawLanguages, defaultLanguage = DEFAULT_RUNTIME_LANGUAGE) {
  const languages = [];
  (Array.isArray(rawLanguages) ? rawLanguages : []).forEach((rawLanguage) => {
    const language = normalizeLanguageCode(rawLanguage, "");
    if (language && !languages.includes(language)) {
      languages.push(language);
    }
  });
  if (!languages.includes(defaultLanguage)) {
    languages.unshift(defaultLanguage);
  }
  return languages.length ? languages : [DEFAULT_RUNTIME_LANGUAGE];
}

const rawData = window.LIGHTWHISPER_GAME_DATA ?? {};
const data = normalizeGameData(rawData);

function isChoiceContinueTarget(value) {
  return String(value ?? "").trim() === CHOICE_CONTINUE_TARGET;
}

const refs = {
  stageFrame: document.getElementById("stageFrame"),
  dialogPanel: document.querySelector(".dialog-panel"),
  gameTitle: document.getElementById("gameTitle"),
  gameMeta: document.getElementById("gameMeta"),
  backgroundLayer: document.getElementById("backgroundLayer"),
  particleLayer: document.getElementById("particleLayer"),
  filterLayer: document.getElementById("filterLayer"),
  fadeLayer: document.getElementById("fadeLayer"),
  flashLayer: document.getElementById("flashLayer"),
  spriteLayer: document.getElementById("spriteLayer"),
  videoOverlay: document.getElementById("videoOverlay"),
  runtimeVideo: document.getElementById("runtimeVideo"),
  videoOverlayTitle: document.getElementById("videoOverlayTitle"),
  videoSkipButton: document.getElementById("videoSkipButton"),
  creditsOverlay: document.getElementById("creditsOverlay"),
  creditsRoll: document.getElementById("creditsRoll"),
  creditsSkipButton: document.getElementById("creditsSkipButton"),
  sceneChip: document.getElementById("sceneChip"),
  musicChip: document.getElementById("musicChip"),
  backgroundLabel: document.getElementById("backgroundLabel"),
  dialogHiddenHint: document.getElementById("dialogHiddenHint"),
  speakerName: document.getElementById("speakerName"),
  lineTypeTag: document.getElementById("lineTypeTag"),
  messageText: document.getElementById("messageText"),
  choiceList: document.getElementById("choiceList"),
  hintText: document.getElementById("hintText"),
  continueButton: document.getElementById("continueButton"),
  restartButton: document.getElementById("restartButton"),
  startOverlay: document.getElementById("startOverlay"),
  startArtworkWrap: document.getElementById("startArtworkWrap"),
  startArtwork: document.getElementById("startArtwork"),
  startButton: document.getElementById("startButton"),
  startContinueButton: document.getElementById("startContinueButton"),
  startLoadButton: document.getElementById("startLoadButton"),
  startOperationGuideButton: document.getElementById("startOperationGuideButton"),
  startProfileButton: document.getElementById("startProfileButton"),
  startVoiceReplayButton: document.getElementById("startVoiceReplayButton"),
  startAchievementButton: document.getElementById("startAchievementButton"),
  startChapterButton: document.getElementById("startChapterButton"),
  startLocationButton: document.getElementById("startLocationButton"),
  startNarrationButton: document.getElementById("startNarrationButton"),
  startRelationButton: document.getElementById("startRelationButton"),
  startCharacterButton: document.getElementById("startCharacterButton"),
  startEndingButton: document.getElementById("startEndingButton"),
  startGalleryButton: document.getElementById("startGalleryButton"),
  startMusicRoomButton: document.getElementById("startMusicRoomButton"),
  runtimeThemeButtons: Array.from(document.querySelectorAll(".player-theme-button")),
  startSummary: document.getElementById("startSummary"),
  startResumeSummary: document.getElementById("startResumeSummary"),
  textSpeedSelect: document.getElementById("textSpeedSelect"),
  languageSelect: document.getElementById("languageSelect"),
  dialogThemeSelect: document.getElementById("dialogThemeSelect"),
  uiThemeSelect: document.getElementById("uiThemeSelect"),
  bgmVolumeRange: document.getElementById("bgmVolumeRange"),
  bgmVolumeValue: document.getElementById("bgmVolumeValue"),
  sfxVolumeRange: document.getElementById("sfxVolumeRange"),
  sfxVolumeValue: document.getElementById("sfxVolumeValue"),
  voiceVolumeRange: document.getElementById("voiceVolumeRange"),
  voiceVolumeValue: document.getElementById("voiceVolumeValue"),
  previousHistoryButton: document.getElementById("previousHistoryButton"),
  nextHistoryButton: document.getElementById("nextHistoryButton"),
  autoPlayToggleButton: document.getElementById("autoPlayToggleButton"),
  voiceToggleButton: document.getElementById("voiceToggleButton"),
  voiceDuckingToggleButton: document.getElementById("voiceDuckingToggleButton"),
  skipReadToggleButton: document.getElementById("skipReadToggleButton"),
  dialogToggleButton: document.getElementById("dialogToggleButton"),
  replayVoiceButton: document.getElementById("replayVoiceButton"),
  resetPlaybackButton: document.getElementById("resetPlaybackButton"),
  systemMenuButton: document.getElementById("systemMenuButton"),
  operationGuideButton: document.getElementById("operationGuideButton"),
  buildInfoPanel: document.getElementById("buildInfoPanel"),
  variablesPanel: document.getElementById("variablesPanel"),
  missingAssetsPanel: document.getElementById("missingAssetsPanel"),
  historyPanel: document.getElementById("historyPanel"),
  saveSlotPanel: document.getElementById("saveSlotPanel"),
  saveDialog: document.getElementById("saveDialog"),
  saveDialogTitle: document.getElementById("saveDialogTitle"),
  saveDialogSummary: document.getElementById("saveDialogSummary"),
  closeSaveDialogButton: document.getElementById("closeSaveDialogButton"),
  saveDialogSaveModeButton: document.getElementById("saveDialogSaveModeButton"),
  saveDialogLoadModeButton: document.getElementById("saveDialogLoadModeButton"),
  saveDialogSlotList: document.getElementById("saveDialogSlotList"),
  profileDialog: document.getElementById("profileDialog"),
  profileDialogSummary: document.getElementById("profileDialogSummary"),
  profileDialogHero: document.getElementById("profileDialogHero"),
  profileDialogList: document.getElementById("profileDialogList"),
  closeProfileDialogButton: document.getElementById("closeProfileDialogButton"),
  voiceReplayDialog: document.getElementById("voiceReplayDialog"),
  voiceReplayDialogSummary: document.getElementById("voiceReplayDialogSummary"),
  voiceReplayDialogHero: document.getElementById("voiceReplayDialogHero"),
  voiceReplayDialogList: document.getElementById("voiceReplayDialogList"),
  closeVoiceReplayDialogButton: document.getElementById("closeVoiceReplayDialogButton"),
  systemMenu: document.getElementById("systemMenu"),
  systemMenuSummary: document.getElementById("systemMenuSummary"),
  closeSystemMenuButton: document.getElementById("closeSystemMenuButton"),
  systemMenuOpenSaveButton: document.getElementById("systemMenuOpenSaveButton"),
  systemMenuOpenLoadButton: document.getElementById("systemMenuOpenLoadButton"),
  systemMenuQuickSaveButton: document.getElementById("systemMenuQuickSaveButton"),
  systemMenuQuickLoadButton: document.getElementById("systemMenuQuickLoadButton"),
  systemMenuOperationGuideButton: document.getElementById("systemMenuOperationGuideButton"),
  systemMenuReturnTitleButton: document.getElementById("systemMenuReturnTitleButton"),
  menuTextSpeedSelect: document.getElementById("menuTextSpeedSelect"),
  menuLanguageSelect: document.getElementById("menuLanguageSelect"),
  menuDialogThemeSelect: document.getElementById("menuDialogThemeSelect"),
  menuUiThemeSelect: document.getElementById("menuUiThemeSelect"),
  menuBgmVolumeRange: document.getElementById("menuBgmVolumeRange"),
  menuBgmVolumeValue: document.getElementById("menuBgmVolumeValue"),
  menuSfxVolumeRange: document.getElementById("menuSfxVolumeRange"),
  menuSfxVolumeValue: document.getElementById("menuSfxVolumeValue"),
  menuVoiceVolumeRange: document.getElementById("menuVoiceVolumeRange"),
  menuVoiceVolumeValue: document.getElementById("menuVoiceVolumeValue"),
  menuVoiceDuckingToggleButton: document.getElementById("menuVoiceDuckingToggleButton"),
  achievementDialog: document.getElementById("achievementDialog"),
  achievementDialogSummary: document.getElementById("achievementDialogSummary"),
  achievementDialogHero: document.getElementById("achievementDialogHero"),
  achievementDialogList: document.getElementById("achievementDialogList"),
  closeAchievementDialogButton: document.getElementById("closeAchievementDialogButton"),
  locationDialog: document.getElementById("locationDialog"),
  locationDialogSummary: document.getElementById("locationDialogSummary"),
  locationDialogHero: document.getElementById("locationDialogHero"),
  locationDialogList: document.getElementById("locationDialogList"),
  closeLocationDialogButton: document.getElementById("closeLocationDialogButton"),
  narrationDialog: document.getElementById("narrationDialog"),
  narrationDialogSummary: document.getElementById("narrationDialogSummary"),
  narrationDialogHero: document.getElementById("narrationDialogHero"),
  narrationDialogList: document.getElementById("narrationDialogList"),
  closeNarrationDialogButton: document.getElementById("closeNarrationDialogButton"),
  relationDialog: document.getElementById("relationDialog"),
  relationDialogSummary: document.getElementById("relationDialogSummary"),
  relationDialogHero: document.getElementById("relationDialogHero"),
  relationDialogList: document.getElementById("relationDialogList"),
  closeRelationDialogButton: document.getElementById("closeRelationDialogButton"),
  chapterDialog: document.getElementById("chapterDialog"),
  chapterDialogSummary: document.getElementById("chapterDialogSummary"),
  chapterDialogHero: document.getElementById("chapterDialogHero"),
  chapterDialogList: document.getElementById("chapterDialogList"),
  closeChapterDialogButton: document.getElementById("closeChapterDialogButton"),
  galleryDialog: document.getElementById("galleryDialog"),
  galleryDialogSummary: document.getElementById("galleryDialogSummary"),
  galleryDialogHero: document.getElementById("galleryDialogHero"),
  galleryDialogList: document.getElementById("galleryDialogList"),
  closeGalleryDialogButton: document.getElementById("closeGalleryDialogButton"),
  characterDialog: document.getElementById("characterDialog"),
  characterDialogSummary: document.getElementById("characterDialogSummary"),
  characterDialogHero: document.getElementById("characterDialogHero"),
  characterDialogList: document.getElementById("characterDialogList"),
  closeCharacterDialogButton: document.getElementById("closeCharacterDialogButton"),
  endingDialog: document.getElementById("endingDialog"),
  endingDialogSummary: document.getElementById("endingDialogSummary"),
  endingDialogHero: document.getElementById("endingDialogHero"),
  endingDialogList: document.getElementById("endingDialogList"),
  closeEndingDialogButton: document.getElementById("closeEndingDialogButton"),
  musicRoomDialog: document.getElementById("musicRoomDialog"),
  musicRoomDialogSummary: document.getElementById("musicRoomDialogSummary"),
  musicRoomNowPlaying: document.getElementById("musicRoomNowPlaying"),
  musicRoomList: document.getElementById("musicRoomList"),
  closeMusicRoomDialogButton: document.getElementById("closeMusicRoomDialogButton"),
  operationGuideDialog: document.getElementById("operationGuideDialog"),
  operationGuideDialogSummary: document.getElementById("operationGuideDialogSummary"),
  operationGuideList: document.getElementById("operationGuideList"),
  closeOperationGuideButton: document.getElementById("closeOperationGuideButton"),
  returnTitleDialog: document.getElementById("returnTitleDialog"),
  cancelReturnTitleButton: document.getElementById("cancelReturnTitleButton"),
  confirmReturnTitleButton: document.getElementById("confirmReturnTitleButton"),
  saveConfirmDialog: document.getElementById("saveConfirmDialog"),
  saveConfirmDialogTitle: document.getElementById("saveConfirmDialogTitle"),
  saveConfirmDialogSummary: document.getElementById("saveConfirmDialogSummary"),
  cancelSaveConfirmButton: document.getElementById("cancelSaveConfirmButton"),
  confirmSaveConfirmButton: document.getElementById("confirmSaveConfirmButton"),
};

function resolveUiTheme(mode = state.playback?.uiThemeMode ?? PLAYBACK_DEFAULTS.uiThemeMode, now = new Date()) {
  const safeMode = getSafeUiThemeMode(mode);

  if (safeMode === "light" || safeMode === "dark") {
    return safeMode;
  }

  const hour = now.getHours();
  return hour >= 7 && hour < 19 ? "light" : "dark";
}

function applyRuntimeUiTheme(mode = state.playback?.uiThemeMode ?? PLAYBACK_DEFAULTS.uiThemeMode) {
  const safeMode = getSafeUiThemeMode(mode);
  document.documentElement.dataset.uiThemeMode = safeMode;
  document.documentElement.dataset.uiTheme = resolveUiTheme(safeMode);
}

function renderRuntimeUiThemeButtons() {
  const activeMode = getSafeUiThemeMode(state.playback?.uiThemeMode);
  refs.runtimeThemeButtons?.forEach((button) => {
    const isActive = button.dataset.uiThemeMode === activeMode;
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-pressed", isActive ? "true" : "false");
  });
}

function scheduleRuntimeUiThemeAutoRefresh() {
  if (runtimeUiThemeAutoRefreshTimer) {
    window.clearInterval(runtimeUiThemeAutoRefreshTimer);
  }

  runtimeUiThemeAutoRefreshTimer = window.setInterval(() => {
    if (getSafeUiThemeMode(state.playback?.uiThemeMode) === "auto") {
      applyRuntimeUiTheme("auto");
    }
  }, 60 * 1000);
}

const state = {
  started: false,
  session: null,
  bgmAudio: null,
  currentMusicAssetId: null,
  lastRenderedStepKey: null,
  typingTimer: null,
  typingSnapshotKey: null,
  typingFullText: "",
  typingVisibleText: "",
  typingActive: false,
  voiceAudio: null,
  currentVoiceStepKey: null,
  videoPlaybackStepKey: null,
  videoPlaybackCleanup: null,
  creditsPlaybackStepKey: null,
  creditsPlaybackTimer: null,
  autoAdvanceTimer: null,
  autoAdvanceStepKey: null,
  dialogHidden: false,
  playback: {},
  autoResume: null,
  readHistory: new Set(),
  saveSlots: [],
  quickSave: null,
  playerProfile: null,
  voiceReplayProgress: new Map(),
  achievementProgress: new Map(),
  chapterReplayProgress: new Map(),
  locationArchiveProgress: new Map(),
  narrationArchiveProgress: new Map(),
  relationArchiveProgress: new Map(),
  characterArchive: new Set(),
  endingProgress: {
    unlocked: new Map(),
    completionCount: 0,
    lastCompletedAt: null,
  },
  extraUnlocks: {
    cg: new Set(),
    bgm: new Set(),
  },
  profileDialogOpen: false,
  voiceReplayDialogOpen: false,
  selectedVoiceReplayId: null,
  currentVoiceReplayPreviewId: null,
  achievementDialogOpen: false,
  selectedAchievementId: null,
  chapterDialogOpen: false,
  selectedChapterReplayId: null,
  locationDialogOpen: false,
  selectedLocationArchiveId: null,
  narrationDialogOpen: false,
  selectedNarrationArchiveId: null,
  relationDialogOpen: false,
  selectedRelationArchiveId: null,
  characterDialogOpen: false,
  selectedCharacterArchiveId: null,
  endingDialogOpen: false,
  selectedEndingSceneId: null,
  galleryDialogOpen: false,
  selectedGalleryAssetId: null,
  musicRoomDialogOpen: false,
  currentMusicRoomAssetId: null,
  operationGuideOpen: false,
  saveDialogOpen: false,
  saveDialogMode: "save",
  saveDialogPage: 0,
  systemMenuOpen: false,
  returnTitleConfirmOpen: false,
  saveConfirmOpen: false,
  saveConfirmIntent: null,
  profileSessionStartedAt: null,
  lastLocationArchiveStepKey: null,
  lastNarrationArchiveStepKey: null,
  lastVoiceReplayStepKey: null,
  runtimePreload: null,
  runtimePreloadStatus: null,
};

const activeSfxAudios = new Set();

const PARTICLE_PRESET_LABELS = {
  snow: "雪花",
  rain: "雨丝",
  petals: "樱花",
  dust: "光尘",
  embers: "火星",
  sparkles: "闪光",
  bubbles: "气泡",
  confetti: "纸片",
  smoke: "烟雾",
  flame: "火焰",
  stardust: "星尘",
  glyphs: "法阵符纹",
};

const PARTICLE_INTENSITY_LABELS = {
  light: "轻一点",
  medium: "中等",
  heavy: "浓一点",
};

const PARTICLE_SPEED_LABELS = {
  slow: "慢一点",
  medium: "正常",
  fast: "快一点",
};

const PARTICLE_WIND_LABELS = {
  left: "向左吹",
  still: "几乎无风",
  right: "向右吹",
};

const PARTICLE_AREA_LABELS = {
  full: "铺满全屏",
  left: "左半边",
  center: "中间区域",
  right: "右半边",
};

const PARTICLE_BLEND_LABELS = {
  screen: "滤色发光",
  add: "线性发光",
  normal: "正常叠加",
};

const PARTICLE_EMISSION_MODE_LABELS = {
  continuous: "持续发射",
  burst: "爆发式发射",
};

const PARTICLE_EMITTER_SHAPE_LABELS = {
  line: "线形发射器",
  point: "点发射器",
  box: "盒形发射器",
  circle: "圆形发射器",
};

const PARTICLE_FOLLOW_LABELS = {
  none: "固定在画面上",
  character: "跟随当前说话角色",
  camera: "跟随镜头中心",
};

const PARTICLE_FOLLOW_ANCHOR_LABELS = {
  head: "头部附近",
  torso: "身体中段",
  feet: "脚边 / 地面",
};

const PARTICLE_SIZE_CURVE_LABELS = {
  steady: "尺寸保持稳定",
  bloom: "先小后大",
  shrink: "慢慢缩小",
  pulse: "中段放大",
};

const PARTICLE_OPACITY_CURVE_LABELS = {
  fade: "正常淡出",
  linger: "停留更久",
  blink: "中段更亮",
  pop: "先亮后淡",
};

const PARTICLE_COLOR_CURVE_LABELS = {
  steady: "颜色保持稳定",
  cool_shift: "慢慢偏冷",
  warm_shift: "越烧越暖",
  spectral: "光谱漂移",
  pulse_glow: "中段爆亮",
};

const PARTICLE_FORCE_FIELD_LABELS = {
  none: "无中心力场",
  attract: "吸附中心",
  repel: "排斥中心",
  orbit: "环绕中心",
};

const PARTICLE_CUSTOM_COMBO_LAYER_LIMIT = 6;

const PARTICLE_COMBO_PRESET_LABELS = {
  none: "单层粒子",
  blizzard_stack: "暴风雪叠层",
  inferno_stack: "火焰仪式叠层",
  arcane_stack: "魔法阵叠层",
  celestial_stack: "星海梦境叠层",
  celebration_stack: "礼花舞台叠层",
};

const PARTICLE_PRESET_DEFAULTS = {
  snow: {
    density: 40,
    sizeMin: 6,
    sizeMax: 18,
    lifeMin: 6,
    lifeMax: 11,
    gravityX: 0,
    gravityY: 70,
    gravityZ: 16,
    spreadX: 100,
    spreadY: 22,
    spreadZ: 36,
    opacityMin: 0.38,
    opacityMax: 0.95,
    rotationMin: 0,
    rotationMax: 180,
    spin: 55,
    turbulence: 22,
    color: "#ffffff",
    colorAccent: "#dff4ff",
    blend: "screen",
  },
  rain: {
    density: 56,
    sizeMin: 2,
    sizeMax: 4,
    lifeMin: 1.2,
    lifeMax: 2.5,
    gravityX: 18,
    gravityY: 190,
    gravityZ: -8,
    spreadX: 100,
    spreadY: 14,
    spreadZ: 20,
    opacityMin: 0.26,
    opacityMax: 0.82,
    rotationMin: 8,
    rotationMax: 14,
    spin: 0,
    turbulence: 10,
    color: "#b7dcff",
    colorAccent: "#f0fbff",
    blend: "screen",
  },
  petals: {
    density: 28,
    sizeMin: 12,
    sizeMax: 22,
    lifeMin: 4.5,
    lifeMax: 8.2,
    gravityX: 0,
    gravityY: 58,
    gravityZ: 6,
    spreadX: 100,
    spreadY: 24,
    spreadZ: 42,
    opacityMin: 0.48,
    opacityMax: 0.96,
    rotationMin: -20,
    rotationMax: 40,
    spin: 120,
    turbulence: 36,
    color: "#ffd6ea",
    colorAccent: "#fff3f8",
    blend: "screen",
  },
  dust: {
    density: 26,
    sizeMin: 4,
    sizeMax: 12,
    lifeMin: 5.5,
    lifeMax: 11,
    gravityX: 0,
    gravityY: 24,
    gravityZ: 24,
    spreadX: 100,
    spreadY: 40,
    spreadZ: 70,
    opacityMin: 0.18,
    opacityMax: 0.72,
    rotationMin: 0,
    rotationMax: 360,
    spin: 40,
    turbulence: 24,
    color: "#c4f6ff",
    colorAccent: "#f8fdff",
    blend: "screen",
  },
  embers: {
    density: 24,
    sizeMin: 3,
    sizeMax: 9,
    lifeMin: 2.6,
    lifeMax: 6.4,
    gravityX: 6,
    gravityY: -46,
    gravityZ: 30,
    spreadX: 100,
    spreadY: 36,
    spreadZ: 54,
    opacityMin: 0.3,
    opacityMax: 0.92,
    rotationMin: 0,
    rotationMax: 180,
    spin: 80,
    turbulence: 34,
    color: "#ffb36b",
    colorAccent: "#fff1b5",
    blend: "add",
  },
  sparkles: {
    density: 18,
    sizeMin: 5,
    sizeMax: 12,
    lifeMin: 1.8,
    lifeMax: 4.2,
    gravityX: 0,
    gravityY: 16,
    gravityZ: 36,
    spreadX: 100,
    spreadY: 50,
    spreadZ: 58,
    opacityMin: 0.28,
    opacityMax: 1,
    rotationMin: 0,
    rotationMax: 180,
    spin: 180,
    turbulence: 26,
    color: "#dff8ff",
    colorAccent: "#8fe8ff",
    blend: "add",
  },
  bubbles: {
    density: 20,
    sizeMin: 10,
    sizeMax: 26,
    lifeMin: 3.8,
    lifeMax: 8.6,
    gravityX: 0,
    gravityY: -72,
    gravityZ: 28,
    spreadX: 100,
    spreadY: 44,
    spreadZ: 64,
    opacityMin: 0.18,
    opacityMax: 0.62,
    rotationMin: -16,
    rotationMax: 16,
    spin: 36,
    turbulence: 18,
    color: "#b6f3ff",
    colorAccent: "#effcff",
    blend: "normal",
  },
  confetti: {
    density: 34,
    sizeMin: 6,
    sizeMax: 14,
    lifeMin: 3.2,
    lifeMax: 6.4,
    gravityX: 0,
    gravityY: 120,
    gravityZ: 18,
    spreadX: 100,
    spreadY: 26,
    spreadZ: 48,
    opacityMin: 0.52,
    opacityMax: 0.98,
    rotationMin: 0,
    rotationMax: 360,
    spin: 240,
    turbulence: 42,
    color: "#7fe7ff",
    colorAccent: "#ff8ee3",
    blend: "normal",
  },
  smoke: {
    density: 22,
    sizeMin: 24,
    sizeMax: 64,
    lifeMin: 4.6,
    lifeMax: 10.8,
    gravityX: 0,
    gravityY: -24,
    gravityZ: 42,
    spreadX: 72,
    spreadY: 44,
    spreadZ: 80,
    opacityMin: 0.14,
    opacityMax: 0.46,
    rotationMin: -26,
    rotationMax: 26,
    spin: 18,
    turbulence: 32,
    color: "#aebed4",
    colorAccent: "#f1f7ff",
    blend: "normal",
  },
  flame: {
    density: 26,
    sizeMin: 14,
    sizeMax: 34,
    lifeMin: 1.4,
    lifeMax: 3.8,
    gravityX: 0,
    gravityY: -82,
    gravityZ: 24,
    spreadX: 40,
    spreadY: 36,
    spreadZ: 44,
    opacityMin: 0.34,
    opacityMax: 0.92,
    rotationMin: -18,
    rotationMax: 18,
    spin: 58,
    turbulence: 44,
    color: "#ff8b3d",
    colorAccent: "#fff4a6",
    blend: "add",
  },
  stardust: {
    density: 30,
    sizeMin: 3,
    sizeMax: 10,
    lifeMin: 5.4,
    lifeMax: 12.6,
    gravityX: 0,
    gravityY: 8,
    gravityZ: 54,
    spreadX: 100,
    spreadY: 60,
    spreadZ: 90,
    opacityMin: 0.18,
    opacityMax: 0.86,
    rotationMin: 0,
    rotationMax: 240,
    spin: 140,
    turbulence: 28,
    color: "#8edbff",
    colorAccent: "#fff1ff",
    blend: "screen",
  },
  glyphs: {
    density: 14,
    sizeMin: 18,
    sizeMax: 36,
    lifeMin: 2.6,
    lifeMax: 5.8,
    gravityX: 0,
    gravityY: 0,
    gravityZ: 18,
    spreadX: 34,
    spreadY: 18,
    spreadZ: 26,
    opacityMin: 0.34,
    opacityMax: 0.92,
    rotationMin: -12,
    rotationMax: 12,
    spin: 120,
    turbulence: 14,
    color: "#85d4ff",
    colorAccent: "#f7dcff",
    blend: "add",
  },
};

const PARTICLE_PRESET_ADVANCED_DEFAULTS = {
  snow: {
    emissionMode: "continuous",
    emitterShape: "line",
    emitterX: 50,
    emitterY: -6,
    emitterZ: 0,
    attractionX: 0,
    attractionY: 0,
    vortex: 12,
    follow: "none",
    sizeCurve: "steady",
    opacityCurve: "linger",
    forceField: "none",
    fieldX: 50,
    fieldY: 52,
  },
  rain: {
    emissionMode: "continuous",
    emitterShape: "line",
    emitterX: 50,
    emitterY: -8,
    emitterZ: -8,
    attractionX: 10,
    attractionY: 0,
    vortex: 6,
    follow: "none",
    sizeCurve: "steady",
    opacityCurve: "fade",
    forceField: "none",
    fieldX: 50,
    fieldY: 58,
  },
  petals: {
    emissionMode: "continuous",
    emitterShape: "line",
    emitterX: 50,
    emitterY: -4,
    emitterZ: 10,
    attractionX: 0,
    attractionY: 4,
    vortex: 48,
    follow: "none",
    sizeCurve: "pulse",
    opacityCurve: "linger",
    forceField: "orbit",
    fieldX: 50,
    fieldY: 56,
  },
  dust: {
    emissionMode: "continuous",
    emitterShape: "box",
    emitterX: 50,
    emitterY: 52,
    emitterZ: 20,
    attractionX: 0,
    attractionY: -4,
    vortex: 18,
    follow: "none",
    sizeCurve: "bloom",
    opacityCurve: "linger",
    forceField: "attract",
    fieldX: 50,
    fieldY: 54,
  },
  embers: {
    emissionMode: "continuous",
    emitterShape: "circle",
    emitterX: 50,
    emitterY: 104,
    emitterZ: 24,
    attractionX: 0,
    attractionY: -14,
    vortex: 65,
    follow: "none",
    sizeCurve: "shrink",
    opacityCurve: "pop",
    forceField: "orbit",
    fieldX: 50,
    fieldY: 84,
  },
  sparkles: {
    emissionMode: "burst",
    emitterShape: "point",
    emitterX: 50,
    emitterY: 48,
    emitterZ: 0,
    attractionX: 0,
    attractionY: 0,
    vortex: 95,
    follow: "none",
    sizeCurve: "pulse",
    opacityCurve: "blink",
    forceField: "orbit",
    fieldX: 50,
    fieldY: 50,
  },
  bubbles: {
    emissionMode: "continuous",
    emitterShape: "circle",
    emitterX: 50,
    emitterY: 106,
    emitterZ: 26,
    attractionX: 0,
    attractionY: -18,
    vortex: 24,
    follow: "none",
    sizeCurve: "bloom",
    opacityCurve: "linger",
    forceField: "attract",
    fieldX: 50,
    fieldY: 36,
  },
  confetti: {
    emissionMode: "burst",
    emitterShape: "line",
    emitterX: 50,
    emitterY: -6,
    emitterZ: 6,
    attractionX: 0,
    attractionY: 16,
    vortex: 110,
    follow: "none",
    sizeCurve: "pulse",
    opacityCurve: "pop",
    forceField: "repel",
    fieldX: 50,
    fieldY: 46,
  },
  smoke: {
    emissionMode: "continuous",
    emitterShape: "circle",
    emitterX: 50,
    emitterY: 94,
    emitterZ: 22,
    attractionX: 0,
    attractionY: -10,
    vortex: 36,
    follow: "none",
    sizeCurve: "bloom",
    opacityCurve: "linger",
    forceField: "attract",
    fieldX: 50,
    fieldY: 58,
  },
  flame: {
    emissionMode: "continuous",
    emitterShape: "point",
    emitterX: 50,
    emitterY: 94,
    emitterZ: 12,
    attractionX: 0,
    attractionY: -22,
    vortex: 84,
    follow: "none",
    sizeCurve: "shrink",
    opacityCurve: "pop",
    forceField: "orbit",
    fieldX: 50,
    fieldY: 76,
  },
  stardust: {
    emissionMode: "continuous",
    emitterShape: "box",
    emitterX: 50,
    emitterY: 48,
    emitterZ: 36,
    attractionX: 0,
    attractionY: 0,
    vortex: 72,
    follow: "camera",
    sizeCurve: "pulse",
    opacityCurve: "blink",
    forceField: "orbit",
    fieldX: 50,
    fieldY: 50,
  },
  glyphs: {
    emissionMode: "burst",
    emitterShape: "circle",
    emitterX: 50,
    emitterY: 56,
    emitterZ: 10,
    attractionX: 0,
    attractionY: 0,
    vortex: 150,
    follow: "character",
    sizeCurve: "pulse",
    opacityCurve: "blink",
    forceField: "orbit",
    fieldX: 50,
    fieldY: 56,
  },
};

const PARTICLE_COMBO_PRESET_CONFIGS = {
  none: [],
  blizzard_stack: [
    {
      preset: "snow",
      densityMultiplier: 0.84,
      layerCount: 2,
      sizeScale: 1.08,
      lifeScale: 1.12,
      spreadYMultiplier: 1.18,
      spreadZAdd: 18,
      turbulenceAdd: 10,
      opacityScale: 0.92,
      follow: "camera",
      followAnchor: "torso",
      blend: "screen",
      colorMix: 0.28,
    },
    {
      preset: "dust",
      densityMultiplier: 0.42,
      sizeScale: 1.52,
      lifeScale: 1.34,
      spreadYMultiplier: 1.46,
      spreadZAdd: 24,
      gravityYAdd: -10,
      turbulenceAdd: 18,
      opacityScale: 0.46,
      follow: "camera",
      followAnchor: "torso",
      forceField: "attract",
      blend: "screen",
      color: "#d9efff",
      colorAccent: "#ffffff",
      colorEnd: "#b8d8ff",
    },
  ],
  inferno_stack: [
    {
      preset: "flame",
      densityMultiplier: 0.88,
      layerCount: 2,
      sizeScale: 1.04,
      opacityScale: 0.96,
      follow: "character",
      followAnchor: "feet",
      emitterYOffset: 10,
      blend: "add",
      colorMix: 0.36,
    },
    {
      preset: "smoke",
      densityMultiplier: 0.44,
      sizeScale: 1.62,
      lifeScale: 1.26,
      spreadYMultiplier: 1.38,
      spreadZAdd: 28,
      gravityYAdd: -14,
      turbulenceAdd: 14,
      opacityScale: 0.56,
      follow: "character",
      followAnchor: "torso",
      emitterYOffset: 4,
      blend: "normal",
      color: "#9e95a6",
      colorAccent: "#ddd8e8",
      colorEnd: "#706978",
    },
    {
      preset: "embers",
      densityMultiplier: 0.48,
      sizeScale: 0.92,
      lifeScale: 0.92,
      opacityScale: 0.78,
      follow: "character",
      followAnchor: "torso",
      emitterYOffset: 8,
      blend: "add",
      colorMix: 0.22,
    },
  ],
  arcane_stack: [
    {
      preset: "glyphs",
      densityMultiplier: 0.9,
      layerCount: 2,
      sizeScale: 1.06,
      opacityScale: 0.92,
      follow: "character",
      followAnchor: "feet",
      forceField: "orbit",
      blend: "add",
      colorMix: 0.48,
    },
    {
      preset: "stardust",
      densityMultiplier: 0.54,
      sizeScale: 0.92,
      lifeScale: 1.12,
      spreadZAdd: 34,
      turbulenceAdd: 18,
      opacityScale: 0.72,
      follow: "camera",
      followAnchor: "torso",
      area: "center",
      blend: "screen",
      colorMix: 0.52,
    },
    {
      preset: "sparkles",
      densityMultiplier: 0.34,
      sizeScale: 0.82,
      opacityScale: 0.78,
      emissionMode: "burst",
      follow: "character",
      followAnchor: "torso",
      emitterShape: "circle",
      blend: "add",
      colorMix: 0.48,
    },
  ],
  celestial_stack: [
    {
      preset: "stardust",
      densityMultiplier: 0.88,
      layerCount: 2,
      opacityScale: 0.92,
      follow: "camera",
      followAnchor: "torso",
      blend: "screen",
      colorMix: 0.46,
    },
    {
      preset: "dust",
      densityMultiplier: 0.4,
      sizeScale: 1.44,
      lifeScale: 1.28,
      spreadZAdd: 30,
      opacityScale: 0.42,
      turbulenceAdd: 18,
      follow: "camera",
      followAnchor: "torso",
      blend: "screen",
      colorMix: 0.44,
    },
    {
      preset: "bubbles",
      densityMultiplier: 0.24,
      sizeScale: 0.74,
      lifeScale: 1.12,
      gravityYAdd: -22,
      opacityScale: 0.36,
      follow: "camera",
      followAnchor: "torso",
      area: "center",
      blend: "normal",
      colorMix: 0.34,
    },
  ],
  celebration_stack: [
    {
      preset: "confetti",
      densityMultiplier: 0.78,
      layerCount: 2,
      emissionMode: "burst",
      opacityScale: 0.96,
      blend: "normal",
      colorMix: 0.3,
    },
    {
      preset: "sparkles",
      densityMultiplier: 0.4,
      sizeScale: 0.82,
      opacityScale: 0.82,
      emissionMode: "burst",
      blend: "add",
      colorMix: 0.44,
    },
    {
      preset: "stardust",
      densityMultiplier: 0.26,
      lifeScale: 0.92,
      opacityScale: 0.46,
      follow: "camera",
      followAnchor: "torso",
      blend: "screen",
      colorMix: 0.38,
    },
  ],
};

const PARTICLE_IMAGE_ASSET_TYPES = ["background", "sprite", "cg", "ui"];

const SHAKE_INTENSITY_LABELS = {
  light: "轻微",
  medium: "明显",
  heavy: "很强",
};

const EFFECT_DURATION_LABELS = {
  short: "短一下",
  medium: "正常",
  long: "久一点",
};

const TRANSITION_DURATION_DEFAULT_MS = 360;
const TRANSITION_DURATION_MIN_MS = 0;
const TRANSITION_DURATION_MAX_MS = 5000;

const FLASH_COLOR_LABELS = {
  white: "白闪",
  warm: "暖光",
  red: "红闪",
  black: "黑闪",
};

const FLASH_INTENSITY_LABELS = {
  soft: "柔和",
  medium: "明显",
  strong: "很亮",
};

const FADE_ACTION_LABELS = {
  fade_out: "慢慢淡出",
  fade_in: "慢慢亮起",
};

const FADE_COLOR_LABELS = {
  black: "黑场",
  white: "白场",
};

const MUSIC_END_MODE_LABELS = {
  until_next_music: "播到下一首或停止卡",
  scene_end: "播完整个场景",
  after_block: "播到指定卡片后",
};

const CAMERA_ZOOM_ACTION_LABELS = {
  zoom_in: "推近镜头",
  zoom_out: "拉远镜头",
  reset: "恢复正常",
};

const CAMERA_ZOOM_STRENGTH_LABELS = {
  light: "轻一点",
  medium: "明显",
  heavy: "更强",
};

const CAMERA_ZOOM_FOCUS_LABELS = {
  left: "看左侧",
  center: "看中间",
  right: "看右侧",
};

const SCREEN_FILTER_ACTION_LABELS = {
  apply: "开启滤镜",
  clear: "关闭滤镜",
};

const SCREEN_FILTER_PRESET_LABELS = {
  memory: "暖色回忆",
  mono: "黑白回忆",
  dream: "梦境柔光",
  cold: "冷色回放",
};

const SCREEN_FILTER_STRENGTH_LABELS = {
  soft: "轻一点",
  medium: "正常",
  strong: "更明显",
};

const SCREEN_COLOR_GRADE_DEFAULTS = Object.freeze({
  brightness: 100,
  contrast: 100,
  saturation: 100,
  hue: 0,
  temperature: 0,
  vignette: 0,
});

const SCREEN_COLOR_GRADE_LIMITS = Object.freeze({
  brightness: Object.freeze([40, 180]),
  contrast: Object.freeze([40, 180]),
  saturation: Object.freeze([0, 220]),
  hue: Object.freeze([-180, 180]),
  temperature: Object.freeze([-100, 100]),
  vignette: Object.freeze([0, 100]),
});

const CAMERA_PAN_TARGET_LABELS = {
  left: "向左看",
  center: "回到中间",
  right: "向右看",
};

const CAMERA_PAN_STRENGTH_LABELS = {
  light: "轻一点",
  medium: "明显",
  heavy: "更远",
};

const DEPTH_BLUR_ACTION_LABELS = {
  apply: "开启景深",
  clear: "关闭景深",
};

const DEPTH_BLUR_FOCUS_LABELS = {
  left: "左侧角色更清楚",
  center: "中间角色更清楚",
  right: "右侧角色更清楚",
  full: "只虚化背景",
};

const DEPTH_BLUR_STRENGTH_LABELS = {
  soft: "轻一点",
  medium: "正常",
  strong: "更明显",
};

const VIDEO_FIT_LABELS = {
  contain: "完整显示",
  cover: "铺满裁切",
  fill: "拉伸填满",
};

const CREDITS_BACKGROUND_LABELS = {
  dark: "深色电影片尾",
  light: "浅色清爽片尾",
  transparent: "叠在当前画面上",
};

const typewriterGraphemeSegmenter =
  typeof Intl !== "undefined" && typeof Intl.Segmenter === "function"
    ? new Intl.Segmenter(undefined, { granularity: "grapheme" })
    : null;
const TYPEWRITER_LEADING_OPENERS = "“‘\"'（([{【〔〈《「『";
const TYPEWRITER_TRAILING_CLOSERS = "”’\"'）)]}】〕〉》」』";
const TYPEWRITER_PERIOD_ABBREVIATIONS = new Set([
  "mr",
  "mrs",
  "ms",
  "dr",
  "prof",
  "sr",
  "jr",
  "st",
  "vs",
  "etc",
  "e.g",
  "i.e",
  "u.s",
  "u.k",
  "no",
  "fig",
  "vol",
  "ch",
  "dept",
  "inc",
  "ltd",
  "co",
]);

const SAVE_SHORTCUT_COUNT = 3;
const SAVE_DIALOG_PAGE_SIZE = 6;
const DEFAULT_PROJECT_DIALOG_BOX_CONFIG = {
  preset: "moonlight",
  shape: "rounded",
  widthPercent: 76,
  minHeight: 148,
  paddingX: 18,
  paddingY: 14,
  backgroundColor: "#0c1422",
  backgroundOpacity: 92,
  borderColor: "#79dcff",
  borderOpacity: 18,
  textColor: "#f3f6ff",
  speakerColor: "#ffffff",
  hintColor: "#c8d6ea",
  blurStrength: 10,
  borderWidth: 1,
  shadowStrength: 30,
  panelAssetId: "",
  panelAssetOpacity: 0,
  panelAssetFit: "cover",
  anchor: "bottom",
  offsetXPercent: 0,
  offsetYPercent: 0,
};
const DEFAULT_PROJECT_GAME_UI_CONFIG = {
  preset: "stellar",
  layoutPreset: "balanced",
  titleLayout: "center",
  fontStyle: "modern",
  surfaceStyle: "glass",
  brandMode: "project",
  sidePanelMode: "full",
  sidePanelPosition: "right",
  topbarPosition: "top",
  hudPosition: "top",
  titleCardAnchor: "center",
  titleCardOffsetXPercent: 0,
  titleCardOffsetYPercent: 0,
  layoutGap: 20,
  sidePanelWidth: 320,
  backgroundColor: "#071120",
  backgroundAccentColor: "#6bd5ff",
  panelColor: "#0c1422",
  panelOpacity: 88,
  textColor: "#f3f7ff",
  mutedTextColor: "#bacce4",
  accentColor: "#79dcff",
  accentAltColor: "#7b7cff",
  buttonTextColor: "#f8fcff",
  borderColor: "#79dcff",
  borderOpacity: 18,
  cornerRadius: 22,
  backdropBlur: 14,
  stageVignette: 42,
  motionIntensity: 70,
  titleBackgroundAssetId: "",
  titleBackgroundFit: "cover",
  titleBackgroundOpacity: 42,
  titleLogoAssetId: "",
  panelFrameAssetId: "",
  panelFrameOpacity: 18,
  panelFrameSlice: { top: 24, right: 24, bottom: 24, left: 24 },
  buttonFrameAssetId: "",
  buttonHoverFrameAssetId: "",
  buttonPressedFrameAssetId: "",
  buttonDisabledFrameAssetId: "",
  buttonFrameOpacity: 24,
  buttonFrameSlice: { top: 18, right: 18, bottom: 18, left: 18 },
  saveSlotFrameAssetId: "",
  systemPanelFrameAssetId: "",
  uiOverlayAssetId: "",
  uiOverlayOpacity: 8,
};
const PROJECT_GAME_UI_PRESETS = {
  stellar: DEFAULT_PROJECT_GAME_UI_CONFIG,
  warm: {
    preset: "warm",
    layoutPreset: "balanced",
    titleLayout: "center",
    fontStyle: "rounded",
    surfaceStyle: "glass",
    brandMode: "project",
    sidePanelMode: "full",
    sidePanelPosition: "right",
    topbarPosition: "top",
    hudPosition: "top",
    titleCardAnchor: "center",
    titleCardOffsetXPercent: 0,
    titleCardOffsetYPercent: 0,
    layoutGap: 20,
    sidePanelWidth: 320,
    backgroundColor: "#fff4e8",
    backgroundAccentColor: "#f0a35f",
    panelColor: "#fff8ef",
    panelOpacity: 92,
    textColor: "#3d2a1f",
    mutedTextColor: "#7a6252",
    accentColor: "#d67245",
    accentAltColor: "#f0b35d",
    buttonTextColor: "#fffaf4",
    borderColor: "#d67245",
    borderOpacity: 20,
    cornerRadius: 24,
    backdropBlur: 10,
    stageVignette: 28,
    motionIntensity: 45,
    titleBackgroundOpacity: 36,
    titleBackgroundFit: "cover",
    panelFrameOpacity: 14,
    buttonFrameOpacity: 18,
    uiOverlayOpacity: 5,
  },
  paper: {
    preset: "paper",
    layoutPreset: "compact",
    titleLayout: "left",
    fontStyle: "serif",
    surfaceStyle: "solid",
    brandMode: "project",
    sidePanelMode: "compact",
    sidePanelPosition: "left",
    topbarPosition: "top",
    hudPosition: "bottom-left",
    titleCardAnchor: "left",
    titleCardOffsetXPercent: 0,
    titleCardOffsetYPercent: 0,
    layoutGap: 16,
    sidePanelWidth: 280,
    backgroundColor: "#f7efe0",
    backgroundAccentColor: "#b98a5d",
    panelColor: "#fff9ed",
    panelOpacity: 96,
    textColor: "#3d2a1d",
    mutedTextColor: "#806b57",
    accentColor: "#9a683d",
    accentAltColor: "#c09a64",
    buttonTextColor: "#fffaf1",
    borderColor: "#a5794e",
    borderOpacity: 28,
    cornerRadius: 12,
    backdropBlur: 4,
    stageVignette: 35,
    motionIntensity: 25,
    titleBackgroundOpacity: 28,
    titleBackgroundFit: "cover",
    panelFrameOpacity: 22,
    buttonFrameOpacity: 12,
    uiOverlayOpacity: 10,
  },
  minimal: {
    preset: "minimal",
    layoutPreset: "minimal",
    titleLayout: "poster",
    fontStyle: "modern",
    surfaceStyle: "minimal",
    brandMode: "hidden",
    sidePanelMode: "hidden",
    sidePanelPosition: "right",
    topbarPosition: "hidden",
    hudPosition: "hidden",
    titleCardAnchor: "bottom",
    titleCardOffsetXPercent: 0,
    titleCardOffsetYPercent: -6,
    layoutGap: 14,
    sidePanelWidth: 260,
    backgroundColor: "#05070c",
    backgroundAccentColor: "#ffffff",
    panelColor: "#05070c",
    panelOpacity: 48,
    textColor: "#f7f7f7",
    mutedTextColor: "#c6c8cf",
    accentColor: "#ffffff",
    accentAltColor: "#aeb5c6",
    buttonTextColor: "#101216",
    borderColor: "#ffffff",
    borderOpacity: 16,
    cornerRadius: 10,
    backdropBlur: 2,
    stageVignette: 20,
    motionIntensity: 10,
    titleBackgroundOpacity: 24,
    titleBackgroundFit: "cover",
    panelFrameOpacity: 0,
    buttonFrameOpacity: 0,
    uiOverlayOpacity: 0,
  },
};
const PROJECT_DIALOG_BOX_PRESETS = {
  moonlight: {
    preset: "moonlight",
    shape: "rounded",
    widthPercent: 76,
    minHeight: 148,
    paddingX: 18,
    paddingY: 14,
    backgroundColor: "#0c1422",
    backgroundOpacity: 92,
    borderColor: "#79dcff",
    borderOpacity: 18,
    textColor: "#f3f6ff",
    speakerColor: "#ffffff",
    hintColor: "#c8d6ea",
    blurStrength: 10,
    borderWidth: 1,
    shadowStrength: 30,
    panelAssetOpacity: 0,
    panelAssetFit: "cover",
    anchor: "bottom",
    offsetXPercent: 0,
    offsetYPercent: 0,
  },
  warm: {
    preset: "warm",
    shape: "rounded",
    widthPercent: 76,
    minHeight: 148,
    paddingX: 16,
    paddingY: 14,
    backgroundColor: "#fffaf5",
    backgroundOpacity: 92,
    borderColor: "#8f6548",
    borderOpacity: 18,
    textColor: "#332117",
    speakerColor: "#7f5438",
    hintColor: "#6d5b4f",
    blurStrength: 8,
    borderWidth: 1,
    shadowStrength: 18,
    panelAssetOpacity: 0,
    panelAssetFit: "cover",
    anchor: "bottom",
    offsetXPercent: 0,
    offsetYPercent: 0,
  },
  paper: {
    preset: "paper",
    shape: "square",
    widthPercent: 76,
    minHeight: 156,
    paddingX: 18,
    paddingY: 16,
    backgroundColor: "#fff7e8",
    backgroundOpacity: 95,
    borderColor: "#b08659",
    borderOpacity: 28,
    textColor: "#4a2f1d",
    speakerColor: "#7f5438",
    hintColor: "#7f6a54",
    blurStrength: 4,
    borderWidth: 1,
    shadowStrength: 16,
    panelAssetOpacity: 0,
    panelAssetFit: "cover",
    anchor: "bottom",
    offsetXPercent: 0,
    offsetYPercent: 0,
  },
  transparent: {
    preset: "transparent",
    shape: "capsule",
    widthPercent: 88,
    minHeight: 132,
    paddingX: 14,
    paddingY: 10,
    backgroundColor: "#08111b",
    backgroundOpacity: 0,
    borderColor: "#7fe6ff",
    borderOpacity: 0,
    textColor: "#f4f8ff",
    speakerColor: "#ffffff",
    hintColor: "#d0daf0",
    blurStrength: 0,
    borderWidth: 0,
    shadowStrength: 0,
    panelAssetOpacity: 0,
    panelAssetFit: "cover",
    anchor: "bottom",
    offsetXPercent: 0,
    offsetYPercent: 0,
  },
};
let musicRoomAudio = null;
let voiceReplayAudio = null;
let runtimeUiThemeAutoRefreshTimer = null;

init();

function init() {
  applyProjectResolutionStyles();
  state.playback = loadStoredPlaybackSettings();
  applyRuntimeUiTheme(state.playback.uiThemeMode);
  applyProjectGameUiSkin();
  state.autoResume = loadStoredAutoResume();
  state.readHistory = loadStoredReadHistory();
  state.saveSlots = loadStoredSaveSlots();
  state.quickSave = loadStoredQuickSave();
  state.playerProfile = loadStoredPlayerProfile();
  state.voiceReplayProgress = loadStoredVoiceReplayProgress();
  state.achievementProgress = loadStoredAchievementProgress();
  state.chapterReplayProgress = loadStoredChapterReplayProgress();
  state.locationArchiveProgress = loadStoredLocationArchiveProgress();
  state.narrationArchiveProgress = loadStoredNarrationArchiveProgress();
  state.relationArchiveProgress = loadStoredRelationArchiveProgress();
  state.characterArchive = loadStoredCharacterArchive();
  state.endingProgress = loadStoredEndingProgress();
  state.extraUnlocks = loadStoredExtraUnlocks();
  syncAchievementProgressFromState();
  document.title = `${data.project.title ?? "Canvasia Engine"} · 网页试玩包`;
  refs.gameTitle.textContent = data.project.title ?? "未命名项目";
  refs.gameMeta.textContent = buildMetaSummary();
  renderStartArtwork();
  refs.continueButton.addEventListener("click", handleContinue);
  refs.videoSkipButton?.addEventListener("click", () => finishVideoPlayback({ skipped: true }));
  refs.creditsSkipButton?.addEventListener("click", () => finishCreditsPlayback({ skipped: true }));
  refs.restartButton.addEventListener("click", startGame);
  refs.startButton.addEventListener("click", startGame);
  refs.startContinueButton?.addEventListener("click", continueLastSession);
  refs.startLoadButton?.addEventListener("click", () => openSaveDialog("load"));
  refs.startOperationGuideButton?.addEventListener("click", openOperationGuideDialog);
  refs.startProfileButton?.addEventListener("click", openProfileDialog);
  refs.startVoiceReplayButton?.addEventListener("click", openVoiceReplayDialog);
  refs.startAchievementButton?.addEventListener("click", openAchievementDialog);
  refs.startChapterButton?.addEventListener("click", openChapterDialog);
  refs.startLocationButton?.addEventListener("click", openLocationDialog);
  refs.startNarrationButton?.addEventListener("click", openNarrationDialog);
  refs.startRelationButton?.addEventListener("click", openRelationDialog);
  refs.startCharacterButton?.addEventListener("click", openCharacterDialog);
  refs.startEndingButton?.addEventListener("click", openEndingDialog);
  refs.startGalleryButton?.addEventListener("click", openGalleryDialog);
  refs.startMusicRoomButton?.addEventListener("click", openMusicRoomDialog);
  refs.runtimeThemeButtons?.forEach((button) => {
    button.addEventListener("click", () => {
      setRuntimeUiThemeMode(button.dataset.uiThemeMode);
    });
  });
  refs.textSpeedSelect?.addEventListener("change", handleTextSpeedChange);
  refs.languageSelect?.addEventListener("change", handleLanguageChange);
  refs.dialogThemeSelect?.addEventListener("change", handleDialogThemeChange);
  refs.uiThemeSelect?.addEventListener("change", handleUiThemeModeChange);
  refs.bgmVolumeRange?.addEventListener("input", handleBgmVolumeChange);
  refs.sfxVolumeRange?.addEventListener("input", handleSfxVolumeChange);
  refs.voiceVolumeRange?.addEventListener("input", handleVoiceVolumeChange);
  refs.previousHistoryButton?.addEventListener("click", () => stepRuntimeHistory(-1));
  refs.nextHistoryButton?.addEventListener("click", () => stepRuntimeHistory(1));
  refs.autoPlayToggleButton?.addEventListener("click", toggleAutoPlay);
  refs.voiceToggleButton?.addEventListener("click", toggleVoiceEnabled);
  refs.voiceDuckingToggleButton?.addEventListener("click", toggleVoiceDuckingEnabled);
  refs.skipReadToggleButton?.addEventListener("click", toggleSkipRead);
  refs.dialogToggleButton?.addEventListener("click", toggleDialogVisibility);
  refs.replayVoiceButton?.addEventListener("click", replayCurrentVoice);
  refs.resetPlaybackButton?.addEventListener("click", resetPlaybackSettings);
  refs.systemMenuButton?.addEventListener("click", openSystemMenu);
  refs.operationGuideButton?.addEventListener("click", openOperationGuideDialog);
  refs.stageFrame?.addEventListener("click", handleStageFrameClick);
  refs.stageFrame?.addEventListener("contextmenu", handleStageFrameContextMenu);
  refs.historyPanel?.addEventListener("click", handleHistoryPanelClick);
  refs.saveSlotPanel?.addEventListener("click", handleSaveSlotPanelClick);
  refs.saveDialogSlotList?.addEventListener("click", handleSaveSlotPanelClick);
  refs.closeSaveDialogButton?.addEventListener("click", closeSaveDialog);
  refs.saveDialogSaveModeButton?.addEventListener("click", () => setSaveDialogMode("save"));
  refs.saveDialogLoadModeButton?.addEventListener("click", () => setSaveDialogMode("load"));
  refs.closeSystemMenuButton?.addEventListener("click", closeSystemMenu);
  refs.systemMenuOpenSaveButton?.addEventListener("click", () => {
    closeSystemMenu();
    openSaveDialog("save");
  });
  refs.systemMenuOpenLoadButton?.addEventListener("click", () => {
    closeSystemMenu();
    openSaveDialog("load");
  });
  refs.systemMenuQuickSaveButton?.addEventListener("click", quickSaveCurrent);
  refs.systemMenuQuickLoadButton?.addEventListener("click", quickLoadCurrent);
  refs.systemMenuOperationGuideButton?.addEventListener("click", openOperationGuideDialog);
  refs.systemMenuReturnTitleButton?.addEventListener("click", openReturnTitleDialog);
  refs.closeProfileDialogButton?.addEventListener("click", closeProfileDialog);
  refs.closeVoiceReplayDialogButton?.addEventListener("click", closeVoiceReplayDialog);
  refs.closeAchievementDialogButton?.addEventListener("click", closeAchievementDialog);
  refs.closeLocationDialogButton?.addEventListener("click", closeLocationDialog);
  refs.closeNarrationDialogButton?.addEventListener("click", closeNarrationDialog);
  refs.closeRelationDialogButton?.addEventListener("click", closeRelationDialog);
  refs.closeChapterDialogButton?.addEventListener("click", closeChapterDialog);
  refs.closeCharacterDialogButton?.addEventListener("click", closeCharacterDialog);
  refs.closeEndingDialogButton?.addEventListener("click", closeEndingDialog);
  refs.closeGalleryDialogButton?.addEventListener("click", closeGalleryDialog);
  refs.closeMusicRoomDialogButton?.addEventListener("click", closeMusicRoomDialog);
  refs.closeOperationGuideButton?.addEventListener("click", closeOperationGuideDialog);
  refs.achievementDialogList?.addEventListener("click", handleAchievementDialogClick);
  refs.narrationDialogList?.addEventListener("click", handleNarrationDialogClick);
  refs.relationDialogList?.addEventListener("click", handleRelationDialogClick);
  refs.characterDialogList?.addEventListener("click", handleCharacterDialogClick);
  refs.endingDialogList?.addEventListener("click", handleEndingDialogClick);
  refs.galleryDialogList?.addEventListener("click", handleGalleryDialogClick);
  refs.musicRoomList?.addEventListener("click", handleMusicRoomClick);
  refs.chapterDialogList?.addEventListener("click", handleChapterDialogClick);
  refs.voiceReplayDialogList?.addEventListener("click", handleVoiceReplayDialogClick);
  refs.locationDialogList?.addEventListener("click", handleLocationDialogClick);
  refs.cancelReturnTitleButton?.addEventListener("click", closeReturnTitleDialog);
  refs.confirmReturnTitleButton?.addEventListener("click", confirmReturnToTitle);
  refs.cancelSaveConfirmButton?.addEventListener("click", closeSaveConfirmDialog);
  refs.confirmSaveConfirmButton?.addEventListener("click", confirmSaveIntent);
  refs.menuTextSpeedSelect?.addEventListener("change", handleTextSpeedChange);
  refs.menuLanguageSelect?.addEventListener("change", handleLanguageChange);
  refs.menuDialogThemeSelect?.addEventListener("change", handleDialogThemeChange);
  refs.menuUiThemeSelect?.addEventListener("change", handleUiThemeModeChange);
  refs.menuBgmVolumeRange?.addEventListener("input", handleBgmVolumeChange);
  refs.menuSfxVolumeRange?.addEventListener("input", handleSfxVolumeChange);
  refs.menuVoiceVolumeRange?.addEventListener("input", handleVoiceVolumeChange);
  refs.menuVoiceDuckingToggleButton?.addEventListener("click", toggleVoiceDuckingEnabled);
  document.addEventListener("keydown", handleGlobalKeydown);
  window.addEventListener("beforeunload", finalizePlayerSession);
  window.addEventListener("beforeunload", stopMusic);
  window.addEventListener("beforeunload", stopMusicRoomPreview);
  window.addEventListener("beforeunload", stopVoiceReplayPreview);
  window.addEventListener("beforeunload", stopOneShotAudio);
  window.addEventListener("beforeunload", stopVoicePlayback);
  startRuntimeAssetPreload();
  renderPlaybackControls();
  scheduleRuntimeUiThemeAutoRefresh();
  renderStartSummary();
  renderBuildInfo();
  renderMissingAssets();
  renderBeforeStart();
}

function startRuntimeAssetPreload() {
  state.runtimePreload?.stop?.();
  state.runtimePreloadStatus = null;
  state.runtimePreload = startRuntimePreload(data.buildInfo.runtimePreloadManifest, {
    onProgress: (status) => {
      state.runtimePreloadStatus = status;
      renderStartSummary();
      renderBuildInfo();
    },
  });
  state.runtimePreloadStatus = state.runtimePreload?.getStatus?.() ?? null;
}

function normalizeGameData(source) {
  const project = source.project ?? {};
  const defaultLanguage = normalizeLanguageCode(
    source.i18n?.defaultLanguage ?? project.language,
    DEFAULT_RUNTIME_LANGUAGE
  );
  const supportedLanguages = normalizeSupportedLanguages(
    source.i18n?.supportedLanguages ?? project.supportedLanguages,
    defaultLanguage
  );
  const i18n = {
    defaultLanguage,
    fallbackLanguage: normalizeLanguageCode(source.i18n?.fallbackLanguage, defaultLanguage),
    supportedLanguages,
    languageLabels: {
      ...RUNTIME_LANGUAGE_LABELS,
      ...(source.i18n?.languageLabels && typeof source.i18n.languageLabels === "object" ? source.i18n.languageLabels : {}),
    },
  };
  const assets = source.assets?.assets ?? [];
  const characters = source.characters?.characters ?? [];
  const variables = source.variables?.variables ?? [];
  const orderedChapters = orderChapters(source.chapters ?? [], project.chapterOrder ?? []);
  const assetsById = new Map(assets.map((asset) => [asset.id, asset]));
  const charactersById = new Map(characters.map((character) => [character.id, character]));
  const variablesById = new Map(variables.map((variable) => [variable.id, variable]));
  const scenesById = new Map();
  const scenes = [];

  orderedChapters.forEach((chapter) => {
    (chapter.scenes ?? []).forEach((scene) => {
      const fullScene = {
        ...scene,
        chapterId: chapter.chapterId,
        chapterName: chapter.name,
      };
      scenes.push(fullScene);
      scenesById.set(scene.id, fullScene);
    });
  });

  const endingScenes = scenes.filter((scene) => collectSceneOutgoingTargets(scene).length === 0);

  return {
    project,
    assets,
    assetsById,
    characters,
    charactersById,
    variables,
    variablesById,
    chapters: orderedChapters,
    scenes,
    scenesById,
    endingScenes,
    i18n,
    buildInfo: source.buildInfo ?? { copiedAssets: 0, missingAssets: [] },
  };
}

function collectSceneOutgoingTargets(scene) {
  const targets = [];

  (scene?.blocks ?? []).forEach((block) => {
    if (block.type === "jump" && block.targetSceneId) {
      targets.push(block.targetSceneId);
      return;
    }

    if (block.type === "choice") {
      (block.options ?? []).forEach((option) => {
        if (option.gotoSceneId && !isChoiceContinueTarget(option.gotoSceneId)) {
          targets.push(option.gotoSceneId);
        }
      });
      return;
    }

    if (block.type === "condition") {
      (block.branches ?? []).forEach((branch) => {
        if (branch.gotoSceneId) {
          targets.push(branch.gotoSceneId);
        }
      });
      if (block.elseGotoSceneId) {
        targets.push(block.elseGotoSceneId);
      }
    }
  });

  return Array.from(new Set(targets.filter((target) => typeof target === "string" && target.trim())));
}

function getRuntimePreloadStatusText() {
  const summary = getRuntimePreloadSummary(data.buildInfo.runtimePreloadManifest);
  if (!summary.totalCount) {
    return "没有需要预热的素材";
  }

  const status = state.runtimePreloadStatus ?? state.runtimePreload?.getStatus?.() ?? null;
  const loadedCount = status?.loadedCount ?? 0;
  const failedCount = status?.failedCount ?? 0;
  const failureText = failedCount > 0 ? ` · ${failedCount} 个稍后重试` : "";
  const sizeText = formatRuntimePreloadSize(summary);
  return [
    `首屏 ${summary.criticalCount} 个`,
    `全局 ${summary.totalCount} 个`,
    sizeText,
    `图片 ${summary.imageCount}`,
    `音频 ${summary.audioCount}`,
    `视频 ${summary.videoCount}`,
    `已预热 ${loadedCount}/${summary.totalCount}${failureText}`,
  ].filter(Boolean).join(" · ");
}

function getRuntimePreloadMetaText() {
  const summary = getRuntimePreloadSummary(data.buildInfo.runtimePreloadManifest);
  if (!summary.totalCount) {
    return "";
  }
  const sizeText = formatRuntimePreloadSize(summary);
  return ` · 预热 ${summary.criticalCount}/${summary.totalCount} 个素材${sizeText ? ` · ${sizeText}` : ""}`;
}

function formatRuntimePreloadSize(summary) {
  const criticalSizeBytes = Number(summary?.criticalSizeBytes ?? 0);
  const totalSizeBytes = Number(summary?.totalSizeBytes ?? 0);
  if (!Number.isFinite(totalSizeBytes) || totalSizeBytes <= 0) {
    return "";
  }
  const criticalLabel = formatRuntimePreloadBytes(Math.max(0, criticalSizeBytes));
  const totalLabel = formatRuntimePreloadBytes(totalSizeBytes);
  return `首屏体积 ${criticalLabel} / 预热合计 ${totalLabel}`;
}

function formatRuntimePreloadBytes(bytes) {
  const units = ["B", "KB", "MB", "GB"];
  let value = Number(bytes);
  if (!Number.isFinite(value) || value <= 0) {
    return "0 B";
  }
  let unitIndex = 0;
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }
  if (unitIndex === 0) {
    return `${Math.round(value)} B`;
  }
  return `${value.toFixed(1)} ${units[unitIndex]}`;
}

function buildEndingScenePreview(scene) {
  const visualState = createInitialPreviewVisualState();
  const variables = createInitialVariableState();
  let lastStoryText = "";
  let lastStorySpeaker = "";

  (scene?.blocks ?? []).forEach((block) => {
    applyBlockToPreviewState(block, visualState, variables);
    if (block.type === "dialogue" || block.type === "narration") {
      lastStoryText = getBlockText(block).trim();
      lastStorySpeaker = visualState.speakerName ?? "";
    }
  });

  if (lastStoryText) {
    visualState.dialogueText = lastStoryText;
  }

  if (lastStorySpeaker) {
    visualState.speakerName = lastStorySpeaker;
  }

  return {
    backgroundAssetId: visualState.backgroundAssetId,
    backgroundName: visualState.backgroundName,
    backgroundUrl: getAssetUrl(visualState.backgroundAssetId),
    speakerName: visualState.speakerName,
    dialogueText: visualState.dialogueText,
    musicName: visualState.musicName,
  };
}

function orderChapters(chapters, chapterOrder) {
  if (!chapterOrder?.length) {
    return chapters;
  }

  const chapterMap = new Map(chapters.map((chapter) => [chapter.chapterId, chapter]));
  return [
    ...chapterOrder.map((chapterId) => chapterMap.get(chapterId)).filter(Boolean),
    ...chapters.filter((chapter) => !chapterOrder.includes(chapter.chapterId)),
  ];
}

function buildMetaSummary() {
  const builtAt = formatDate(data.buildInfo.builtAt);
  const copiedAssets = data.buildInfo.copiedAssets ?? 0;
  const missingAssets = data.buildInfo.missingAssets?.length ?? 0;
  const resolution = getProjectResolution();
  const targetLabel = data.buildInfo.exportTargetLabel ?? "导出试玩包";
  const releaseVersion = data.buildInfo.releaseVersion ? ` · 版本 ${data.buildInfo.releaseVersion}` : "";
  const profileSummary =
    state.playerProfile?.sessionCount > 0
      ? ` · 游玩 ${state.playerProfile.sessionCount} 次 · ${formatPlayDuration(state.playerProfile.totalPlayMs)}`
      : "";
  const achievementDefinitions = getAchievementDefinitions();
  const achievementSummary =
    achievementDefinitions.length > 0
      ? ` · 成就 ${state.achievementProgress.size}/${achievementDefinitions.length} 已达成`
      : "";
  const chapterEntries = getChapterReplayEntries();
  const chapterSummary =
    chapterEntries.length > 0
      ? ` · 章节 ${state.chapterReplayProgress.size}/${chapterEntries.length} 已开放`
      : "";
  const locationEntries = getLocationArchiveEntries();
  const locationSummary =
    locationEntries.length > 0
      ? ` · 地点 ${state.locationArchiveProgress.size}/${locationEntries.length} 已收录`
      : "";
  const narrationEntries = getNarrationArchiveEntries();
  const narrationSummary =
    narrationEntries.length > 0
      ? ` · 摘录 ${state.narrationArchiveProgress.size}/${narrationEntries.length} 已收录`
      : "";
  const relationEntries = getRelationshipArchiveEntries();
  const relationSummary =
    relationEntries.length > 0
      ? ` · 关系 ${state.relationArchiveProgress.size}/${relationEntries.length} 已收录`
      : "";
  const voiceReplayEntries = getVoiceReplayEntries();
  const voiceReplaySummary =
    voiceReplayEntries.length > 0
      ? ` · 回听 ${state.voiceReplayProgress.size}/${voiceReplayEntries.length} 已收录`
      : "";
  const preloadSummary = getRuntimePreloadMetaText();
  const characterEntries = getCharacterArchiveEntries();
  const characterSummary =
    characterEntries.length > 0
      ? ` · 图鉴 ${state.characterArchive.size}/${characterEntries.length} 已收录`
      : "";
  const endingScenes = getEndingScenes();
  const endingSummary =
    endingScenes.length > 0
      ? ` · 结局 ${state.endingProgress.unlocked.size}/${endingScenes.length} 已回收`
      : "";
  return `${targetLabel}${releaseVersion} · 输出 ${resolution.width} × ${resolution.height}${profileSummary}${achievementSummary}${chapterSummary}${locationSummary}${narrationSummary}${relationSummary}${voiceReplaySummary}${preloadSummary}${characterSummary}${endingSummary} · 构建时间 ${builtAt} · 已复制 ${copiedAssets} 个素材 · 缺失 ${missingAssets} 个素材`;
}

function renderStartSummary() {
  const resolution = getProjectResolution();
  const profile = state.playerProfile ?? sanitizePlayerProfile(null);
  const achievementDefinitions = getAchievementDefinitions();
  const chapterEntries = getChapterReplayEntries();
  const locationEntries = getLocationArchiveEntries();
  const narrationEntries = getNarrationArchiveEntries();
  const relationEntries = getRelationshipArchiveEntries();
  const voiceReplayEntries = getVoiceReplayEntries();
  const characterEntries = getCharacterArchiveEntries();
  const endingScenes = getEndingScenes();
  const galleryAssets = getGalleryAssets();
  const musicAssets = getMusicRoomAssets();
  refs.startSummary.innerHTML = [
    ["导出类型", data.buildInfo.exportTargetLabel ?? "网页试玩包"],
    ["发布版本", data.buildInfo.releaseVersion ?? "1.0.0-preview"],
    ["入口场景", getSceneName(data.scenesById.get(getEntrySceneId()), "未找到")],
    ["输出分辨率", `${resolution.width} × ${resolution.height}`],
    ["章节数量", `${data.chapters.length} 个`],
    ["场景数量", `${data.scenes.length} 个`],
    ["玩家档案", profile.sessionCount > 0 ? `游玩 ${profile.sessionCount} 次 · ${formatPlayDuration(profile.totalPlayMs)}` : "还没有游玩记录"],
    [
      "章节选集",
      chapterEntries.length > 0
        ? `已开放 ${state.chapterReplayProgress.size} / ${chapterEntries.length}`
        : "当前没有章节条目",
    ],
    [
      "地点图鉴",
      locationEntries.length > 0
        ? `已收录 ${state.locationArchiveProgress.size} / ${locationEntries.length}`
        : "当前没有地点条目",
    ],
    [
      "旁白摘录",
      narrationEntries.length > 0
        ? `已收录 ${state.narrationArchiveProgress.size} / ${narrationEntries.length}`
        : "当前没有旁白摘录条目",
    ],
    [
      "关系图鉴",
      relationEntries.length > 0
        ? `已收录 ${state.relationArchiveProgress.size} / ${relationEntries.length}`
        : "当前没有关系条目",
    ],
    [
      "语音回听",
      voiceReplayEntries.length > 0
        ? `已收录 ${state.voiceReplayProgress.size} / ${voiceReplayEntries.length}`
        : "当前没有带真实语音的台词",
    ],
    [
      "成就馆",
      achievementDefinitions.length > 0
        ? `已达成 ${state.achievementProgress.size} / ${achievementDefinitions.length}`
        : "当前没有可收录成就",
    ],
    [
      "角色图鉴",
      characterEntries.length > 0
        ? `已收录 ${state.characterArchive.size} / ${characterEntries.length}`
        : "当前没有角色条目",
    ],
    [
      "结局回收",
      endingScenes.length > 0
        ? `已回收 ${state.endingProgress.unlocked.size} / ${endingScenes.length} · 通关 ${state.endingProgress.completionCount} 次`
        : "当前没有可回收结局",
    ],
    ["CG 回想", galleryAssets.length > 0 ? `已解锁 ${state.extraUnlocks.cg.size} / ${galleryAssets.length}` : "当前没有 CG 条目"],
    ["音乐鉴赏", musicAssets.length > 0 ? `已解锁 ${state.extraUnlocks.bgm.size} / ${musicAssets.length}` : "当前没有 BGM 条目"],
    ["资源预热", getRuntimePreloadStatusText()],
    ["素材状态", `已复制 ${data.buildInfo.copiedAssets ?? 0} 个 / 缺失 ${data.buildInfo.missingAssets?.length ?? 0} 个`],
  ]
    .map(
      ([label, value]) => `
        <div class="summary-row">
          <label>${escapeHtml(label)}</label>
          <div class="value">${escapeHtml(value)}</div>
        </div>
      `
    )
    .join("");
  renderStartResumeSummary();
}

function renderStartResumeSummary() {
  if (!refs.startResumeSummary || !refs.startContinueButton || !refs.startLoadButton) {
    return;
  }

  const slot = state.autoResume;
  const snapshot = getSaveSlotSnapshot(slot);
  const hasResume = Boolean(slot && snapshot);
  const hasLoadSource = Boolean(hasResume || state.saveSlots.some(Boolean) || state.quickSave);

  refs.startContinueButton.hidden = !hasResume;
  refs.startLoadButton.hidden = !hasLoadSource;
  refs.startLoadButton.disabled = !hasLoadSource;
  refs.startResumeSummary.hidden = !hasResume;

  if (!hasResume) {
    refs.startResumeSummary.innerHTML = "";
    return;
  }

  refs.startResumeSummary.innerHTML = `
    <strong>上次试玩停在这里</strong>
    <div>${escapeHtml(getSaveSlotSummary(slot))}</div>
    <div>${escapeHtml(`变量：${getVariableSummary(snapshot.variables)}`)}</div>
    <div>${escapeHtml(`记录时间：${formatDate(slot.savedAt)}`)}</div>
  `;
}

function renderBuildInfo() {
  const resolution = getProjectResolution();
  const profile = state.playerProfile ?? sanitizePlayerProfile(null);
  const achievementDefinitions = getAchievementDefinitions();
  const chapterEntries = getChapterReplayEntries();
  const locationEntries = getLocationArchiveEntries();
  const narrationEntries = getNarrationArchiveEntries();
  const relationEntries = getRelationshipArchiveEntries();
  const voiceReplayEntries = getVoiceReplayEntries();
  const characterEntries = getCharacterArchiveEntries();
  const endingScenes = getEndingScenes();
  const galleryAssets = getGalleryAssets();
  const musicAssets = getMusicRoomAssets();
  refs.buildInfoPanel.innerHTML = [
    ["项目标题", data.project.title ?? "未命名项目"],
    ["导出类型", data.buildInfo.exportTargetLabel ?? "网页试玩包"],
    ["发布版本", data.buildInfo.releaseVersion ?? "1.0.0-preview"],
    ["输出分辨率", `${resolution.width} × ${resolution.height}`],
    ["入口场景", getSceneName(data.scenesById.get(getEntrySceneId()), getEntrySceneId())],
    ["玩家档案", profile.sessionCount > 0 ? `${profile.sessionCount} 次 · ${formatPlayDuration(profile.totalPlayMs)}` : "未记录"],
    [
      "章节选集",
      chapterEntries.length > 0
        ? `${state.chapterReplayProgress.size} / ${chapterEntries.length} 已开放`
        : "未设置",
    ],
    [
      "地点图鉴",
      locationEntries.length > 0
        ? `${state.locationArchiveProgress.size} / ${locationEntries.length} 已收录`
        : "未设置",
    ],
    [
      "旁白摘录",
      narrationEntries.length > 0
        ? `${state.narrationArchiveProgress.size} / ${narrationEntries.length} 已收录`
        : "未设置",
    ],
    [
      "关系图鉴",
      relationEntries.length > 0
        ? `${state.relationArchiveProgress.size} / ${relationEntries.length} 已收录`
        : "未设置",
    ],
    [
      "语音回听",
      voiceReplayEntries.length > 0
        ? `${state.voiceReplayProgress.size} / ${voiceReplayEntries.length} 已收录`
        : "未设置",
    ],
    [
      "成就馆",
      achievementDefinitions.length > 0
        ? `${state.achievementProgress.size} / ${achievementDefinitions.length} 已达成`
        : "未设置",
    ],
    [
      "角色图鉴",
      characterEntries.length > 0
        ? `${state.characterArchive.size} / ${characterEntries.length} 已收录`
        : "未设置",
    ],
    [
      "结局回收",
      endingScenes.length > 0
        ? `${state.endingProgress.unlocked.size} / ${endingScenes.length} 已回收 · 通关 ${state.endingProgress.completionCount} 次`
        : "未设置",
    ],
    ["CG 回想", galleryAssets.length > 0 ? `${state.extraUnlocks.cg.size} / ${galleryAssets.length} 已解锁` : "未设置"],
    ["音乐鉴赏", musicAssets.length > 0 ? `${state.extraUnlocks.bgm.size} / ${musicAssets.length} 已解锁` : "未设置"],
    ["资源预热", getRuntimePreloadStatusText()],
    ["导出时间", formatDate(data.buildInfo.builtAt)],
    ["已复制素材", `${data.buildInfo.copiedAssets ?? 0} 个`],
  ]
    .map(
      ([label, value]) => `
        <div class="info-row">
          <label>${escapeHtml(label)}</label>
          <div class="value">${escapeHtml(value)}</div>
        </div>
      `
    )
    .join("");
}

function renderStartArtwork() {
  if (!refs.startArtworkWrap || !refs.startArtwork) {
    return;
  }

  const splashImageUrl = String(data.buildInfo.splashImageUrl ?? "").trim();
  const hasSplash = splashImageUrl.length > 0;

  refs.startArtworkWrap.hidden = !hasSplash;
  if (!hasSplash) {
    refs.startArtwork.removeAttribute("src");
    return;
  }

  refs.startArtwork.src = splashImageUrl;
}

function renderMissingAssets() {
  const missingAssets = data.buildInfo.missingAssets ?? [];
  refs.missingAssetsPanel.innerHTML =
    missingAssets.length === 0
      ? renderEmpty("导出时没有发现缺失素材。")
      : missingAssets
          .slice(0, 8)
          .map(
            (asset) => `
              <div class="info-row">
                <label>${escapeHtml(getAssetTypeLabel(asset.type))}</label>
                <div class="value">${escapeHtml(asset.name ?? asset.id)}</div>
              </div>
            `
          )
          .join("") +
        (missingAssets.length > 8
          ? `
            <div class="empty-note">还有 ${missingAssets.length - 8} 个缺失素材未展示。</div>
          `
          : "");
}

function renderBeforeStart() {
  stopRuntimeTypewriter();
  stopRuntimeAutoAdvance();
  stopOneShotAudio();
  stopVoicePlayback();
  stopMusicRoomPreview();
  stopVoiceReplayPreview({ rerender: false });
  stopVideoPlayback();
  stopCreditsPlayback();
  state.dialogHidden = false;
  state.saveDialogPage = 0;
  state.systemMenuOpen = false;
  state.profileDialogOpen = false;
  state.voiceReplayDialogOpen = false;
  state.achievementDialogOpen = false;
  state.chapterDialogOpen = false;
  state.locationDialogOpen = false;
  state.relationDialogOpen = false;
  state.characterDialogOpen = false;
  state.endingDialogOpen = false;
  state.galleryDialogOpen = false;
  state.musicRoomDialogOpen = false;
  state.operationGuideOpen = false;
  state.returnTitleConfirmOpen = false;
  state.saveConfirmOpen = false;
  state.saveConfirmIntent = null;
  state.lastLocationArchiveStepKey = null;
  state.lastVoiceReplayStepKey = null;
  refs.startOverlay.hidden = false;
  refs.restartButton.disabled = true;
  refs.sceneChip.textContent = "等待开始";
  refs.musicChip.textContent = "BGM：未播放";
  refs.backgroundLabel.textContent = "导出试玩包已就绪";
  refs.speakerName.textContent = "Canvasia Engine";
  refs.speakerName.style.color = "";
  refs.lineTypeTag.textContent = "准备";
  refs.messageText.textContent = "点击“开始试玩”后，运行时会按当前项目的分支、变量和跳转继续推进。";
  refs.messageText.classList.remove("is-typing");
  refs.choiceList.innerHTML = "";
  refs.hintText.textContent = "可直接打开当前 HTML 文件进行试玩。";
  refs.continueButton.textContent = "开始试玩";
  refs.continueButton.disabled = false;
  refs.variablesPanel.innerHTML = renderVariables(createInitialVariableState());
  refs.historyPanel.innerHTML = renderEmpty("开始后，这里会显示已经走过的剧情步骤。");
  state.saveDialogOpen = false;
  renderStartResumeSummary();
  renderPlaybackControls();
  renderExtraButtons();
  renderProfileDialog();
  renderVoiceReplayDialog();
  renderAchievementDialog();
  renderChapterDialog();
  renderLocationDialog();
  renderRelationDialog();
  renderCharacterDialog();
  renderEndingDialog();
  renderGalleryDialog();
  renderMusicRoomDialog();
  renderOperationGuideDialog();
  renderSaveDialog();
  renderSystemMenu();
  renderReturnTitleDialog();
  renderSaveConfirmDialog();
  applyDialogTheme();
  renderStageVisual({
    block: null,
    visualState: createInitialPreviewVisualState(),
  });
}

function startGameFromScene(sceneId = getEntrySceneId()) {
  stopMusic();
  stopRuntimeTypewriter();
  stopRuntimeAutoAdvance();
  stopOneShotAudio();
  stopVoicePlayback();
  stopMusicRoomPreview();
  stopVoiceReplayPreview({ rerender: false });
  stopVideoPlayback();
  stopCreditsPlayback();
  state.dialogHidden = false;
  state.saveDialogOpen = false;
  state.saveDialogPage = 0;
  state.systemMenuOpen = false;
  state.profileDialogOpen = false;
  state.voiceReplayDialogOpen = false;
  state.achievementDialogOpen = false;
  state.chapterDialogOpen = false;
  state.locationDialogOpen = false;
  state.relationDialogOpen = false;
  state.characterDialogOpen = false;
  state.endingDialogOpen = false;
  state.galleryDialogOpen = false;
  state.musicRoomDialogOpen = false;
  state.operationGuideOpen = false;
  state.returnTitleConfirmOpen = false;
  state.saveConfirmOpen = false;
  state.saveConfirmIntent = null;
  state.started = true;
  state.session = createPreviewSession(sceneId);
  state.lastRenderedStepKey = null;
  state.lastLocationArchiveStepKey = null;
  state.lastVoiceReplayStepKey = null;
  recordPlayerSessionStart("start");
  unlockAchievement("first_start");
  persistAutoResume();
  refs.startOverlay.hidden = true;
  refs.restartButton.disabled = false;
  renderProfileDialog();
  renderVoiceReplayDialog();
  renderAchievementDialog();
  renderChapterDialog();
  renderLocationDialog();
  renderRelationDialog();
  renderCharacterDialog();
  renderEndingDialog();
  renderGalleryDialog();
  renderMusicRoomDialog();
  renderRuntime();
}

function startGame() {
  startGameFromScene(getEntrySceneId());
}

function continueLastSession() {
  const session = sanitizeStoredSession(state.autoResume?.session);

  if (!session) {
    startGame();
    return false;
  }

  stopMusic();
  stopRuntimeTypewriter();
  stopRuntimeAutoAdvance();
  stopOneShotAudio();
  stopVoicePlayback();
  stopMusicRoomPreview();
  stopVoiceReplayPreview({ rerender: false });
  stopVideoPlayback();
  stopCreditsPlayback();
  state.dialogHidden = false;
  state.saveDialogOpen = false;
  state.saveDialogPage = 0;
  state.systemMenuOpen = false;
  state.profileDialogOpen = false;
  state.voiceReplayDialogOpen = false;
  state.achievementDialogOpen = false;
  state.chapterDialogOpen = false;
  state.locationDialogOpen = false;
  state.relationDialogOpen = false;
  state.characterDialogOpen = false;
  state.endingDialogOpen = false;
  state.galleryDialogOpen = false;
  state.musicRoomDialogOpen = false;
  state.operationGuideOpen = false;
  state.returnTitleConfirmOpen = false;
  state.saveConfirmOpen = false;
  state.saveConfirmIntent = null;
  state.started = true;
  state.session = session;
  state.lastRenderedStepKey = null;
  state.lastLocationArchiveStepKey = null;
  state.lastVoiceReplayStepKey = null;
  recordPlayerSessionStart("resume");
  unlockAchievement("first_start");
  persistAutoResume();
  refs.startOverlay.hidden = true;
  refs.restartButton.disabled = false;
  renderProfileDialog();
  renderVoiceReplayDialog();
  renderAchievementDialog();
  renderChapterDialog();
  renderLocationDialog();
  renderRelationDialog();
  renderCharacterDialog();
  renderEndingDialog();
  renderGalleryDialog();
  renderMusicRoomDialog();
  renderRuntime();
  return true;
}

function handleContinue() {
  if (!state.started || !state.session) {
    startGame();
    return;
  }

  const snapshot = getCurrentSnapshot();
  if (!snapshot) {
    startGame();
    return;
  }

  if (snapshot.completed) {
    startGame();
    return;
  }

  if (snapshot.blockType === "video_play") {
    if (isMediaSnapshotSkippable(snapshot)) {
      finishVideoPlayback({ skipped: true });
    }
    return;
  }

  if (snapshot.blockType === "credits_roll") {
    if (isMediaSnapshotSkippable(snapshot)) {
      finishCreditsPlayback({ skipped: true });
    }
    return;
  }

  if (completeRuntimeTypewriter()) {
    stopRuntimeAutoAdvance();
    renderRuntime();
    return;
  }

  if (snapshot.choiceOptions.length > 0) {
    return;
  }

  stopRuntimeAutoAdvance();
  movePreviewForward();
  renderRuntime();
}

function getSafeEndingSceneId(sceneId = null) {
  const endings = getEndingScenes();
  if (endings.some((scene) => scene.id === sceneId)) {
    return sceneId;
  }

  const unlockedId = endings.find((scene) => state.endingProgress.unlocked.has(scene.id))?.id ?? "";
  return unlockedId || endings[0]?.id || "";
}

function getSafeAchievementId(achievementId = null) {
  const achievements = getAchievementDefinitions();
  if (achievements.some((achievement) => achievement.id === achievementId)) {
    return achievementId;
  }

  const unlockedId = achievements.find((achievement) => state.achievementProgress.has(achievement.id))?.id ?? "";
  return unlockedId || achievements[0]?.id || "";
}

function getSafeChapterReplayId(chapterId = null) {
  const chapters = getChapterReplayEntries();
  if (chapters.some((chapter) => chapter.chapterId === chapterId)) {
    return chapterId;
  }

  const unlockedId = chapters.find((chapter) => state.chapterReplayProgress.has(chapter.chapterId))?.chapterId ?? "";
  return unlockedId || chapters[0]?.chapterId || "";
}

function getSafeLocationArchiveId(locationId = null) {
  const locations = getLocationArchiveEntries();
  if (locations.some((location) => location.id === locationId)) {
    return locationId;
  }

  const unlockedId = locations.find((location) => state.locationArchiveProgress.has(location.id))?.id ?? "";
  return unlockedId || locations[0]?.id || "";
}

function getSafeNarrationArchiveId(narrationId = null) {
  const narrations = getNarrationArchiveEntries();
  if (narrations.some((entry) => entry.id === narrationId)) {
    return narrationId;
  }

  const unlockedId = narrations.find((entry) => state.narrationArchiveProgress.has(entry.id))?.id ?? "";
  return unlockedId || narrations[0]?.id || "";
}

function getSafeRelationArchiveId(relationId = null) {
  const relations = getRelationshipArchiveEntries();
  if (relations.some((relation) => relation.id === relationId)) {
    return relationId;
  }

  const unlockedId = relations.find((relation) => state.relationArchiveProgress.has(relation.id))?.id ?? "";
  return unlockedId || relations[0]?.id || "";
}

function getSafeCharacterArchiveId(characterId = null) {
  const characters = getCharacterArchiveEntries();
  if (characters.some((character) => character.id === characterId)) {
    return characterId;
  }

  const unlockedId = characters.find((character) => state.characterArchive.has(character.id))?.id ?? "";
  return unlockedId || characters[0]?.id || "";
}

function openAchievementDialog() {
  if (!getAchievementDefinitions().length) {
    return false;
  }

  state.profileDialogOpen = false;
  state.voiceReplayDialogOpen = false;
  state.achievementDialogOpen = true;
  state.chapterDialogOpen = false;
  state.locationDialogOpen = false;
  state.characterDialogOpen = false;
  state.endingDialogOpen = false;
  state.galleryDialogOpen = false;
  state.musicRoomDialogOpen = false;
  stopMusicRoomPreview();
  stopVoiceReplayPreview({ rerender: false });
  state.selectedAchievementId = getSafeAchievementId(state.selectedAchievementId);
  renderProfileDialog();
  renderVoiceReplayDialog();
  renderAchievementDialog();
  renderChapterDialog();
  renderLocationDialog();
  renderCharacterDialog();
  renderEndingDialog();
  renderGalleryDialog();
  renderMusicRoomDialog();
  return true;
}

function closeAchievementDialog() {
  if (!state.achievementDialogOpen) {
    return false;
  }

  state.achievementDialogOpen = false;
  renderAchievementDialog();
  return true;
}

function buildPlayerProfileStats() {
  const profile = state.playerProfile ?? sanitizePlayerProfile(null);
  const formalSaveCount = state.saveSlots.filter(Boolean).length;
  const hasQuickSave = Boolean(state.quickSave);
  const hasAutoResume = Boolean(state.autoResume);
  const chapterEntries = getChapterReplayEntries();
  const locationEntries = getLocationArchiveEntries();
  const narrationEntries = getNarrationArchiveEntries();
  const relationEntries = getRelationshipArchiveEntries();
  const voiceReplayEntries = getVoiceReplayEntries();
  const achievementEntries = getAchievementDefinitions();
  const characterEntries = getCharacterArchiveEntries();
  const endingScenes = getEndingScenes();
  const galleryAssets = getGalleryAssets();
  const musicAssets = getMusicRoomAssets();

  return {
    profile,
    formalSaveCount,
    hasQuickSave,
    hasAutoResume,
    chapterEntries,
    locationEntries,
    narrationEntries,
    relationEntries,
    voiceReplayEntries,
    achievementEntries,
    characterEntries,
    endingScenes,
    galleryAssets,
    musicAssets,
  };
}

function openProfileDialog() {
  if (data.scenes.length === 0) {
    return false;
  }

  state.profileDialogOpen = true;
  state.voiceReplayDialogOpen = false;
  state.achievementDialogOpen = false;
  state.chapterDialogOpen = false;
  state.locationDialogOpen = false;
  state.characterDialogOpen = false;
  state.endingDialogOpen = false;
  state.galleryDialogOpen = false;
  state.musicRoomDialogOpen = false;
  stopMusicRoomPreview();
  stopVoiceReplayPreview({ rerender: false });
  renderProfileDialog();
  renderVoiceReplayDialog();
  renderAchievementDialog();
  renderChapterDialog();
  renderLocationDialog();
  renderCharacterDialog();
  renderEndingDialog();
  renderGalleryDialog();
  renderMusicRoomDialog();
  return true;
}

function closeProfileDialog() {
  if (!state.profileDialogOpen) {
    return false;
  }

  state.profileDialogOpen = false;
  renderProfileDialog();
  return true;
}

function openChapterDialog() {
  if (!getChapterReplayEntries().length) {
    return false;
  }

  state.profileDialogOpen = false;
  state.voiceReplayDialogOpen = false;
  state.achievementDialogOpen = false;
  state.chapterDialogOpen = true;
  state.locationDialogOpen = false;
  state.relationDialogOpen = false;
  state.characterDialogOpen = false;
  state.endingDialogOpen = false;
  state.galleryDialogOpen = false;
  state.musicRoomDialogOpen = false;
  stopMusicRoomPreview();
  stopVoiceReplayPreview({ rerender: false });
  state.selectedChapterReplayId = getSafeChapterReplayId(state.selectedChapterReplayId);
  renderProfileDialog();
  renderVoiceReplayDialog();
  renderAchievementDialog();
  renderChapterDialog();
  renderLocationDialog();
  renderRelationDialog();
  renderCharacterDialog();
  renderEndingDialog();
  renderGalleryDialog();
  renderMusicRoomDialog();
  return true;
}

function closeChapterDialog() {
  if (!state.chapterDialogOpen) {
    return false;
  }

  state.chapterDialogOpen = false;
  renderChapterDialog();
  return true;
}

function renderExtraButtons() {
  const shouldShowProfileButton = data.scenes.length > 0;
  const voiceReplayEntries = getVoiceReplayEntries();
  const achievementDefinitions = getAchievementDefinitions();
  const chapterEntries = getChapterReplayEntries();
  const locationEntries = getLocationArchiveEntries();
  const narrationEntries = getNarrationArchiveEntries();
  const relationEntries = getRelationshipArchiveEntries();
  const characterEntries = getCharacterArchiveEntries();
  const endingScenes = getEndingScenes();
  const galleryAssets = getGalleryAssets();
  const musicAssets = getMusicRoomAssets();

  if (refs.startProfileButton) {
    refs.startProfileButton.hidden = !shouldShowProfileButton;
    refs.startProfileButton.textContent =
      shouldShowProfileButton
        ? state.playerProfile?.sessionCount > 0
          ? `玩家档案 ${state.playerProfile.sessionCount}次`
          : "玩家档案"
        : "玩家档案";
  }

  if (refs.startVoiceReplayButton) {
    refs.startVoiceReplayButton.hidden = voiceReplayEntries.length === 0;
    refs.startVoiceReplayButton.textContent =
      voiceReplayEntries.length > 0
        ? `语音回听 ${state.voiceReplayProgress.size}/${voiceReplayEntries.length}`
        : "语音回听";
  }

  if (refs.startAchievementButton) {
    refs.startAchievementButton.hidden = achievementDefinitions.length === 0;
    refs.startAchievementButton.textContent =
      achievementDefinitions.length > 0
        ? `成就馆 ${state.achievementProgress.size}/${achievementDefinitions.length}`
        : "成就馆";
  }

  if (refs.startChapterButton) {
    refs.startChapterButton.hidden = chapterEntries.length === 0;
    refs.startChapterButton.textContent =
      chapterEntries.length > 0
        ? `章节选集 ${state.chapterReplayProgress.size}/${chapterEntries.length}`
        : "章节选集";
  }

  if (refs.startLocationButton) {
    refs.startLocationButton.hidden = locationEntries.length === 0;
    refs.startLocationButton.textContent =
      locationEntries.length > 0
        ? `地点图鉴 ${state.locationArchiveProgress.size}/${locationEntries.length}`
        : "地点图鉴";
  }

  if (refs.startNarrationButton) {
    refs.startNarrationButton.hidden = narrationEntries.length === 0;
    refs.startNarrationButton.textContent =
      narrationEntries.length > 0
        ? `旁白摘录 ${state.narrationArchiveProgress.size}/${narrationEntries.length}`
        : "旁白摘录";
  }

  if (refs.startRelationButton) {
    refs.startRelationButton.hidden = relationEntries.length === 0;
    refs.startRelationButton.textContent =
      relationEntries.length > 0
        ? `关系图鉴 ${state.relationArchiveProgress.size}/${relationEntries.length}`
        : "关系图鉴";
  }

  if (refs.startCharacterButton) {
    refs.startCharacterButton.hidden = characterEntries.length === 0;
    refs.startCharacterButton.textContent =
      characterEntries.length > 0
        ? `角色图鉴 ${state.characterArchive.size}/${characterEntries.length}`
        : "角色图鉴";
  }

  if (refs.startEndingButton) {
    refs.startEndingButton.hidden = endingScenes.length === 0;
    refs.startEndingButton.textContent =
      endingScenes.length > 0
        ? `结局回收 ${state.endingProgress.unlocked.size}/${endingScenes.length}`
        : "结局回收";
  }

  if (refs.startGalleryButton) {
    refs.startGalleryButton.hidden = galleryAssets.length === 0;
    refs.startGalleryButton.textContent =
      galleryAssets.length > 0
        ? `CG 回想 ${state.extraUnlocks.cg.size}/${galleryAssets.length}`
        : "CG 回想";
  }

  if (refs.startMusicRoomButton) {
    refs.startMusicRoomButton.hidden = musicAssets.length === 0;
    refs.startMusicRoomButton.textContent =
      musicAssets.length > 0
        ? `音乐鉴赏 ${state.extraUnlocks.bgm.size}/${musicAssets.length}`
        : "音乐鉴赏";
  }
}

function handleAchievementDialogClick(event) {
  const button = event.target.closest("[data-achievement-id]");
  if (!(button instanceof HTMLElement)) {
    return;
  }

  state.selectedAchievementId = getSafeAchievementId(button.dataset.achievementId);
  renderAchievementDialog();
}

function handleChapterDialogClick(event) {
  const replayButton = event.target.closest("[data-chapter-replay]");
  if (replayButton instanceof HTMLElement) {
    const chapterId = getSafeChapterReplayId(replayButton.dataset.chapterReplay);
    const entry = getChapterReplayEntries().find((chapter) => chapter.chapterId === chapterId);
    if (entry?.firstSceneId && state.chapterReplayProgress.has(chapterId)) {
      closeChapterDialog();
      startGameFromScene(entry.firstSceneId);
    }
    return;
  }

  const button = event.target.closest("[data-chapter-id]");
  if (!(button instanceof HTMLElement)) {
    return;
  }

  state.selectedChapterReplayId = getSafeChapterReplayId(button.dataset.chapterId);
  renderChapterDialog();
}

function openLocationDialog() {
  if (!getLocationArchiveEntries().length) {
    return false;
  }

  state.profileDialogOpen = false;
  state.voiceReplayDialogOpen = false;
  state.achievementDialogOpen = false;
  state.chapterDialogOpen = false;
  state.locationDialogOpen = true;
  state.characterDialogOpen = false;
  state.endingDialogOpen = false;
  state.galleryDialogOpen = false;
  state.musicRoomDialogOpen = false;
  stopMusicRoomPreview();
  stopVoiceReplayPreview({ rerender: false });
  state.selectedLocationArchiveId = getSafeLocationArchiveId(state.selectedLocationArchiveId);
  renderProfileDialog();
  renderVoiceReplayDialog();
  renderAchievementDialog();
  renderChapterDialog();
  renderLocationDialog();
  renderCharacterDialog();
  renderEndingDialog();
  renderGalleryDialog();
  renderMusicRoomDialog();
  return true;
}

function closeLocationDialog() {
  if (!state.locationDialogOpen) {
    return false;
  }

  state.locationDialogOpen = false;
  renderLocationDialog();
  return true;
}

function handleLocationDialogClick(event) {
  const button = event.target.closest("[data-location-archive-id]");
  if (!(button instanceof HTMLElement)) {
    return;
  }

  state.selectedLocationArchiveId = getSafeLocationArchiveId(button.dataset.locationArchiveId);
  renderLocationDialog();
}

function openRelationDialog() {
  if (!getRelationshipArchiveEntries().length) {
    return false;
  }

  state.profileDialogOpen = false;
  state.voiceReplayDialogOpen = false;
  state.achievementDialogOpen = false;
  state.chapterDialogOpen = false;
  state.locationDialogOpen = false;
  state.relationDialogOpen = true;
  state.characterDialogOpen = false;
  state.endingDialogOpen = false;
  state.galleryDialogOpen = false;
  state.musicRoomDialogOpen = false;
  stopMusicRoomPreview();
  stopVoiceReplayPreview({ rerender: false });
  state.selectedRelationArchiveId = getSafeRelationArchiveId(state.selectedRelationArchiveId);
  renderProfileDialog();
  renderVoiceReplayDialog();
  renderAchievementDialog();
  renderChapterDialog();
  renderLocationDialog();
  renderRelationDialog();
  renderCharacterDialog();
  renderEndingDialog();
  renderGalleryDialog();
  renderMusicRoomDialog();
  return true;
}

function closeRelationDialog() {
  if (!state.relationDialogOpen) {
    return false;
  }

  state.relationDialogOpen = false;
  renderRelationDialog();
  return true;
}

function handleRelationDialogClick(event) {
  const button = event.target.closest("[data-relation-archive-id]");
  if (!(button instanceof HTMLElement)) {
    return;
  }

  state.selectedRelationArchiveId = getSafeRelationArchiveId(button.dataset.relationArchiveId);
  renderRelationDialog();
}

function openNarrationDialog() {
  if (!getNarrationArchiveEntries().length) {
    return false;
  }

  state.profileDialogOpen = false;
  state.voiceReplayDialogOpen = false;
  state.achievementDialogOpen = false;
  state.chapterDialogOpen = false;
  state.locationDialogOpen = false;
  state.narrationDialogOpen = true;
  state.relationDialogOpen = false;
  state.characterDialogOpen = false;
  state.endingDialogOpen = false;
  state.galleryDialogOpen = false;
  state.musicRoomDialogOpen = false;
  stopMusicRoomPreview();
  stopVoiceReplayPreview({ rerender: false });
  state.selectedNarrationArchiveId = getSafeNarrationArchiveId(state.selectedNarrationArchiveId);
  renderProfileDialog();
  renderVoiceReplayDialog();
  renderAchievementDialog();
  renderChapterDialog();
  renderLocationDialog();
  renderNarrationDialog();
  renderRelationDialog();
  renderCharacterDialog();
  renderEndingDialog();
  renderGalleryDialog();
  renderMusicRoomDialog();
  return true;
}

function closeNarrationDialog() {
  if (!state.narrationDialogOpen) {
    return false;
  }

  state.narrationDialogOpen = false;
  renderNarrationDialog();
  return true;
}

function handleNarrationDialogClick(event) {
  const button = event.target.closest("[data-narration-archive-id]");
  if (!(button instanceof HTMLElement)) {
    return;
  }

  state.selectedNarrationArchiveId = getSafeNarrationArchiveId(button.dataset.narrationArchiveId);
  renderNarrationDialog();
}

function getSafeGalleryAssetId(assetId = null) {
  const galleryAssets = getGalleryAssets();
  if (galleryAssets.some((asset) => asset.id === assetId)) {
    return assetId;
  }

  const unlocked = galleryAssets.find((asset) => state.extraUnlocks.cg.has(asset.id));
  return unlocked?.id ?? galleryAssets[0]?.id ?? "";
}

function getSafeMusicRoomAssetId(assetId = null) {
  const musicAssets = getMusicRoomAssets();
  if (musicAssets.some((asset) => asset.id === assetId)) {
    return assetId;
  }

  const unlocked = musicAssets.find((asset) => state.extraUnlocks.bgm.has(asset.id));
  return unlocked?.id ?? musicAssets[0]?.id ?? "";
}

function openCharacterDialog() {
  if (!getCharacterArchiveEntries().length) {
    return false;
  }

  state.profileDialogOpen = false;
  state.voiceReplayDialogOpen = false;
  state.achievementDialogOpen = false;
  state.chapterDialogOpen = false;
  state.locationDialogOpen = false;
  state.relationDialogOpen = false;
  state.characterDialogOpen = true;
  state.endingDialogOpen = false;
  state.galleryDialogOpen = false;
  state.musicRoomDialogOpen = false;
  stopMusicRoomPreview();
  stopVoiceReplayPreview({ rerender: false });
  state.selectedCharacterArchiveId = getSafeCharacterArchiveId(state.selectedCharacterArchiveId);
  renderProfileDialog();
  renderVoiceReplayDialog();
  renderAchievementDialog();
  renderChapterDialog();
  renderLocationDialog();
  renderRelationDialog();
  renderCharacterDialog();
  renderEndingDialog();
  renderGalleryDialog();
  renderMusicRoomDialog();
  return true;
}

function closeCharacterDialog() {
  if (!state.characterDialogOpen) {
    return false;
  }

  state.characterDialogOpen = false;
  renderCharacterDialog();
  return true;
}

function openEndingDialog() {
  if (!getEndingScenes().length) {
    return false;
  }

  state.profileDialogOpen = false;
  state.voiceReplayDialogOpen = false;
  state.achievementDialogOpen = false;
  state.chapterDialogOpen = false;
  state.locationDialogOpen = false;
  state.relationDialogOpen = false;
  state.characterDialogOpen = false;
  state.endingDialogOpen = true;
  state.galleryDialogOpen = false;
  state.musicRoomDialogOpen = false;
  stopMusicRoomPreview();
  stopVoiceReplayPreview({ rerender: false });
  state.selectedEndingSceneId = getSafeEndingSceneId(state.selectedEndingSceneId);
  renderProfileDialog();
  renderVoiceReplayDialog();
  renderAchievementDialog();
  renderChapterDialog();
  renderLocationDialog();
  renderRelationDialog();
  renderCharacterDialog();
  renderEndingDialog();
  renderGalleryDialog();
  renderMusicRoomDialog();
  return true;
}

function closeEndingDialog() {
  if (!state.endingDialogOpen) {
    return false;
  }

  state.endingDialogOpen = false;
  renderEndingDialog();
  return true;
}

function openGalleryDialog() {
  if (!getGalleryAssets().length) {
    return false;
  }

  state.profileDialogOpen = false;
  state.voiceReplayDialogOpen = false;
  state.achievementDialogOpen = false;
  state.chapterDialogOpen = false;
  state.locationDialogOpen = false;
  state.relationDialogOpen = false;
  state.characterDialogOpen = false;
  state.endingDialogOpen = false;
  state.galleryDialogOpen = true;
  state.musicRoomDialogOpen = false;
  stopMusicRoomPreview();
  stopVoiceReplayPreview({ rerender: false });
  renderProfileDialog();
  renderVoiceReplayDialog();
  renderAchievementDialog();
  renderChapterDialog();
  renderLocationDialog();
  renderRelationDialog();
  renderCharacterDialog();
  renderEndingDialog();
  state.selectedGalleryAssetId = getSafeGalleryAssetId(state.selectedGalleryAssetId);
  renderGalleryDialog();
  renderMusicRoomDialog();
  return true;
}

function closeGalleryDialog() {
  if (!state.galleryDialogOpen) {
    return false;
  }

  state.galleryDialogOpen = false;
  renderGalleryDialog();
  return true;
}

function openMusicRoomDialog() {
  if (!getMusicRoomAssets().length) {
    return false;
  }

  state.profileDialogOpen = false;
  state.voiceReplayDialogOpen = false;
  state.achievementDialogOpen = false;
  state.chapterDialogOpen = false;
  state.locationDialogOpen = false;
  state.relationDialogOpen = false;
  state.characterDialogOpen = false;
  state.endingDialogOpen = false;
  state.musicRoomDialogOpen = true;
  state.galleryDialogOpen = false;
  stopVoiceReplayPreview({ rerender: false });
  state.currentMusicRoomAssetId = getSafeMusicRoomAssetId(state.currentMusicRoomAssetId);
  renderProfileDialog();
  renderVoiceReplayDialog();
  renderAchievementDialog();
  renderChapterDialog();
  renderLocationDialog();
  renderRelationDialog();
  renderCharacterDialog();
  renderEndingDialog();
  renderGalleryDialog();
  renderMusicRoomDialog();
  return true;
}

function closeMusicRoomDialog() {
  if (!state.musicRoomDialogOpen) {
    return false;
  }

  state.musicRoomDialogOpen = false;
  stopMusicRoomPreview();
  renderMusicRoomDialog();
  return true;
}

function openOperationGuideDialog() {
  state.operationGuideOpen = true;
  stopRuntimeAutoAdvance();
  renderOperationGuideDialog();
  window.requestAnimationFrame(() => refs.closeOperationGuideButton?.focus());
  return true;
}

function closeOperationGuideDialog() {
  if (!state.operationGuideOpen) {
    return false;
  }

  state.operationGuideOpen = false;
  renderOperationGuideDialog();
  return true;
}

function renderOperationGuideDialog() {
  if (!refs.operationGuideDialog || !refs.operationGuideDialogSummary || !refs.operationGuideList) {
    return;
  }

  refs.operationGuideDialog.hidden = !state.operationGuideOpen;
  refs.operationGuideDialog.classList.toggle("is-visible", state.operationGuideOpen);
  refs.operationGuideDialogSummary.textContent = state.started
    ? "这些操作会直接作用于当前试玩进度；打开本页时自动播放会先暂停，避免错过剧情。"
    : "开始试玩前可以先看一眼操作方式。导出包可以直接用鼠标，也支持常见视觉小说快捷键。";
  refs.operationGuideList.innerHTML = renderOperationGuideGroups();
}

function handleCharacterDialogClick(event) {
  const button = event.target.closest("[data-character-archive-id]");
  if (!(button instanceof HTMLElement)) {
    return;
  }

  state.selectedCharacterArchiveId = getSafeCharacterArchiveId(button.dataset.characterArchiveId);
  renderCharacterDialog();
}

function handleEndingDialogClick(event) {
  const replayButton = event.target.closest("[data-ending-replay]");
  if (replayButton instanceof HTMLElement) {
    const sceneId = getSafeEndingSceneId(replayButton.dataset.endingReplay);
    if (state.endingProgress.unlocked.has(sceneId)) {
      closeEndingDialog();
      startGameFromScene(sceneId);
    }
    return;
  }

  const button = event.target.closest("[data-ending-scene-id]");
  if (!(button instanceof HTMLElement)) {
    return;
  }

  state.selectedEndingSceneId = getSafeEndingSceneId(button.dataset.endingSceneId);
  renderEndingDialog();
}

function handleGalleryDialogClick(event) {
  const button = event.target.closest("[data-gallery-asset-id]");
  if (!(button instanceof HTMLElement)) {
    return;
  }

  state.selectedGalleryAssetId = getSafeGalleryAssetId(button.dataset.galleryAssetId);
  renderGalleryDialog();
}

function handleMusicRoomClick(event) {
  const playButton = event.target.closest("[data-music-room-play]");
  if (playButton instanceof HTMLElement) {
    void toggleMusicRoomTrack(playButton.dataset.musicRoomPlay);
    return;
  }

  const stopButton = event.target.closest("[data-music-room-stop]");
  if (stopButton instanceof HTMLElement) {
    stopMusicRoomPreview();
    renderMusicRoomDialog();
  }
}

function unlockChapterReplayEntry(chapterId) {
  if (!chapterId || state.chapterReplayProgress.has(chapterId)) {
    return false;
  }

  if (!getChapterReplayEntries().some((chapter) => chapter.chapterId === chapterId)) {
    return false;
  }

  state.chapterReplayProgress.set(chapterId, new Date().toISOString());
  persistChapterReplayProgress();
  refs.gameMeta.textContent = buildMetaSummary();
  renderStartSummary();
  renderBuildInfo();
  renderExtraButtons();
  renderProfileDialog();
  renderChapterDialog();
  return true;
}

function buildChapterReplayDialogEntries() {
  return getChapterReplayEntries().map((chapter) => ({
    ...chapter,
    unlocked: state.chapterReplayProgress.has(chapter.chapterId),
    unlockedAt: state.chapterReplayProgress.get(chapter.chapterId) ?? null,
    previewBackgroundUrl: chapter.previewBackgroundAssetId ? getAssetUrl(chapter.previewBackgroundAssetId) : "",
    previewSpeakerName: chapter.previewSpeakerId ? getCharacterName(chapter.previewSpeakerId) : "",
  }));
}

function buildLocationArchiveDialogEntries() {
  return getLocationArchiveEntries().map((entry) => ({
    ...entry,
    unlocked: state.locationArchiveProgress.has(entry.id),
    unlockedAt: state.locationArchiveProgress.get(entry.id) ?? null,
  }));
}

function buildNarrationArchiveDialogEntries() {
  return getNarrationArchiveEntries().map((entry) => ({
    ...entry,
    unlocked: state.narrationArchiveProgress.has(entry.id),
    unlockedAt: state.narrationArchiveProgress.get(entry.id) ?? null,
  }));
}

function buildRelationArchiveDialogEntries() {
  return getRelationshipArchiveEntries().map((entry) => ({
    ...entry,
    unlocked: state.relationArchiveProgress.has(entry.id),
    unlockedAt: state.relationArchiveProgress.get(entry.id) ?? null,
  }));
}

function renderLocationDialog() {
  if (!refs.locationDialog || !refs.locationDialogSummary || !refs.locationDialogHero || !refs.locationDialogList) {
    return;
  }

  const entries = buildLocationArchiveDialogEntries();
  const selectedLocationId = getSafeLocationArchiveId(state.selectedLocationArchiveId);
  const selectedEntry = entries.find((entry) => entry.id === selectedLocationId) ?? entries[0] ?? null;
  const unlockedCount = entries.filter((entry) => entry.unlocked).length;
  state.selectedLocationArchiveId = selectedEntry?.id ?? null;

  refs.locationDialog.hidden = !state.locationDialogOpen;
  refs.locationDialog.classList.toggle("is-visible", state.locationDialogOpen);
  refs.locationDialogSummary.textContent =
    entries.length > 0
      ? `当前已收录 ${unlockedCount} / ${entries.length} 个地点。第一次真正走到某张背景出现的位置后，这个地点就会在标题页地点图鉴里亮起。`
      : "这个项目当前还没有可收录的地点条目。";

  if (!selectedEntry) {
    refs.locationDialogHero.innerHTML = renderEmpty("这个项目当前还没有可收录的地点条目。");
    refs.locationDialogList.innerHTML = "";
    return;
  }

  refs.locationDialogHero.innerHTML = selectedEntry.unlocked
    ? `
        <div class="extra-hero-image-wrap">
          ${
            selectedEntry.imageUrl
              ? `<img class="extra-hero-image" src="${escapeHtml(selectedEntry.imageUrl)}" alt="${escapeHtml(selectedEntry.name)}" />`
              : `<div class="extra-hero-locked">这个地点当前没有可显示的背景预览。</div>`
          }
        </div>
        <div class="extra-hero-copy">
          <strong>${escapeHtml(selectedEntry.name)}</strong>
          <span>${escapeHtml(`${selectedEntry.chapterName} · ${selectedEntry.sceneName}`)}</span>
          <span>${escapeHtml(
            selectedEntry.tags.length > 0
              ? `标签：${selectedEntry.tags.join(" / ")}`
              : "这个地点来自剧情里第一次切到这张背景的位置。"
          )}</span>
          <span>${escapeHtml(`收录时间：${selectedEntry.unlockedAt ? formatDate(selectedEntry.unlockedAt) : "未记录"}`)}</span>
        </div>
      `
    : `
        <div class="extra-hero-locked">这个地点还没有收录。</div>
        <div class="extra-hero-copy">
          <strong>？？？</strong>
          <span>${escapeHtml("推进到这张背景第一次出现的位置后即可解锁。")}</span>
          <span>${escapeHtml(`${selectedEntry.chapterName} · ${selectedEntry.sceneName}`)}</span>
        </div>
      `;

  refs.locationDialogList.innerHTML = entries.length
    ? entries
        .map(
          (entry) => `
            <article class="ending-room-card ${entry.id === selectedEntry.id ? "is-active" : ""} ${entry.unlocked ? "" : "is-locked"}">
              <button
                class="history-main-button"
                type="button"
                data-location-archive-id="${escapeHtml(entry.id)}"
              >
                <strong>${escapeHtml(entry.unlocked ? entry.name : "？？？ · 未收录地点")}</strong>
                <div class="ending-room-meta">
                  ${escapeHtml(
                    entry.unlocked
                      ? `${entry.chapterName} · ${entry.sceneName} · ${entry.unlockedAt ? `收录于 ${formatDate(entry.unlockedAt)}` : "已收录"}`
                      : `${entry.chapterName} · ${entry.sceneName} · 未收录`
                  )}
                </div>
                <p>${escapeHtml(
                  entry.unlocked
                    ? entry.tags.length > 0
                      ? `标签：${entry.tags.join(" / ")}`
                      : "这张背景已经在剧情里被玩家真正见过。"
                    : "推进到对应剧情后，这个地点会在标题页自动解锁。"
                )}</p>
              </button>
            </article>
          `
        )
        .join("")
    : renderEmpty("这个项目当前还没有可收录的地点条目。");
}

function renderNarrationDialog() {
  if (!refs.narrationDialog || !refs.narrationDialogSummary || !refs.narrationDialogHero || !refs.narrationDialogList) {
    return;
  }

  const entries = buildNarrationArchiveDialogEntries();
  const selectedNarrationId = getSafeNarrationArchiveId(state.selectedNarrationArchiveId);
  const selectedEntry = entries.find((entry) => entry.id === selectedNarrationId) ?? entries[0] ?? null;
  const unlockedCount = entries.filter((entry) => entry.unlocked).length;
  state.selectedNarrationArchiveId = selectedEntry?.id ?? null;

  refs.narrationDialog.hidden = !state.narrationDialogOpen;
  refs.narrationDialog.classList.toggle("is-visible", state.narrationDialogOpen);
  refs.narrationDialogSummary.textContent =
    entries.length > 0
      ? `当前已收录 ${unlockedCount} / ${entries.length} 段旁白。推进到对应段落后，会在标题页摘录馆解锁。`
      : "这个项目当前还没有可收录的旁白摘录条目。";

  if (!selectedEntry) {
    refs.narrationDialogHero.innerHTML = renderEmpty("这个项目当前还没有可收录的旁白摘录条目。");
    refs.narrationDialogList.innerHTML = "";
    return;
  }

  refs.narrationDialogHero.innerHTML = selectedEntry.unlocked
    ? `
        <div class="extra-hero-image-wrap">
          ${
            selectedEntry.previewBackgroundUrl
              ? `<img class="extra-hero-image" src="${escapeHtml(selectedEntry.previewBackgroundUrl)}" alt="${escapeHtml(selectedEntry.chapterName)}" />`
              : `<div class="extra-hero-locked">这段旁白当前没有可显示的背景预览。</div>`
          }
        </div>
        <div class="extra-hero-copy">
          <strong>${escapeHtml(`${selectedEntry.chapterName} · ${selectedEntry.sceneName}`)}</strong>
          <span>${escapeHtml(truncateText(selectedEntry.text, 110))}</span>
          <span>${escapeHtml(`收录时间：${selectedEntry.unlockedAt ? formatDate(selectedEntry.unlockedAt) : "未记录"}`)}</span>
        </div>
      `
    : `
        <div class="extra-hero-locked">这段旁白还没有收录。</div>
        <div class="extra-hero-copy">
          <strong>？？？ · 未收录旁白</strong>
          <span>${escapeHtml("推进到这段旁白后即可解锁。")}</span>
          <span>${escapeHtml(`${selectedEntry.chapterName} · ${selectedEntry.sceneName}`)}</span>
        </div>
      `;

  refs.narrationDialogList.innerHTML = entries.length
    ? entries
        .map(
          (entry) => `
            <article class="ending-room-card ${entry.id === selectedEntry.id ? "is-active" : ""} ${entry.unlocked ? "" : "is-locked"}">
              <button
                class="history-main-button"
                type="button"
                data-narration-archive-id="${escapeHtml(entry.id)}"
              >
                <strong>${escapeHtml(entry.unlocked ? `${entry.chapterName} · ${entry.sceneName}` : "？？？ · 未收录旁白")}</strong>
                <div class="ending-room-meta">
                  ${escapeHtml(
                    entry.unlocked
                      ? `${entry.chapterName} · ${entry.sceneName} · ${entry.unlockedAt ? `收录于 ${formatDate(entry.unlockedAt)}` : "已收录"}`
                      : `${entry.chapterName} · ${entry.sceneName} · 未收录`
                  )}
                </div>
                <p>${escapeHtml(entry.unlocked ? truncateText(entry.text, 96) : "推进到对应剧情后，这段旁白会收录到标题页摘录馆。")}</p>
              </button>
            </article>
          `
        )
        .join("")
    : renderEmpty("这个项目当前还没有可收录的旁白摘录条目。");
}

function renderRelationDialog() {
  if (!refs.relationDialog || !refs.relationDialogSummary || !refs.relationDialogHero || !refs.relationDialogList) {
    return;
  }

  const entries = buildRelationArchiveDialogEntries();
  const selectedRelationId = getSafeRelationArchiveId(state.selectedRelationArchiveId);
  const selectedEntry = entries.find((entry) => entry.id === selectedRelationId) ?? entries[0] ?? null;
  const unlockedCount = entries.filter((entry) => entry.unlocked).length;
  state.selectedRelationArchiveId = selectedEntry?.id ?? null;

  refs.relationDialog.hidden = !state.relationDialogOpen;
  refs.relationDialog.classList.toggle("is-visible", state.relationDialogOpen);
  refs.relationDialogSummary.textContent =
    entries.length > 0
      ? `当前已收录 ${unlockedCount} / ${entries.length} 组关系。两位角色首次同场后，这组共演关系会在标题页解锁。`
      : "这个项目当前还没有可收录的双人关系条目。";

  if (!selectedEntry) {
    refs.relationDialogHero.innerHTML = renderEmpty("这个项目当前还没有可收录的双人关系条目。");
    refs.relationDialogList.innerHTML = "";
    return;
  }

  refs.relationDialogHero.innerHTML = selectedEntry.unlocked
    ? `
        <div class="extra-hero-image-wrap">
          ${
            selectedEntry.previewBackgroundUrl
              ? `<img class="extra-hero-image" src="${escapeHtml(selectedEntry.previewBackgroundUrl)}" alt="${escapeHtml(`${selectedEntry.leftCharacterName} 与 ${selectedEntry.rightCharacterName}`)}" />`
              : `<div class="extra-hero-locked">这组关系当前没有可显示的场景背景预览。</div>`
          }
        </div>
        <div class="extra-hero-copy">
          <strong>${escapeHtml(`${selectedEntry.leftCharacterName} × ${selectedEntry.rightCharacterName}`)}</strong>
          <span>${escapeHtml(`${selectedEntry.chapterName} · ${selectedEntry.sceneName}`)}</span>
          <div class="achievement-badge-strip">
            <span class="achievement-badge">${escapeHtml(selectedEntry.leftCharacterName)}</span>
            <span class="achievement-badge">${escapeHtml(selectedEntry.rightCharacterName)}</span>
          </div>
          <span>${escapeHtml(truncateText(selectedEntry.previewText || "这组角色已经在剧情里真正同场出现过。", 72))}</span>
          <span>${escapeHtml(`收录时间：${selectedEntry.unlockedAt ? formatDate(selectedEntry.unlockedAt) : "未记录"}`)}</span>
        </div>
      `
    : `
        <div class="extra-hero-locked">这组关系还没有收录。</div>
        <div class="extra-hero-copy">
          <strong>？？？ × ？？？</strong>
          <span>${escapeHtml("推进到两位角色首次同场的位置后即可解锁。")}</span>
          <span>${escapeHtml(`${selectedEntry.chapterName} · ${selectedEntry.sceneName}`)}</span>
        </div>
      `;

  refs.relationDialogList.innerHTML = entries.length
    ? entries
        .map(
          (entry) => `
            <article class="ending-room-card ${entry.id === selectedEntry.id ? "is-active" : ""} ${entry.unlocked ? "" : "is-locked"}">
              <button
                class="history-main-button"
                type="button"
                data-relation-archive-id="${escapeHtml(entry.id)}"
              >
                <strong>${escapeHtml(entry.unlocked ? `${entry.leftCharacterName} × ${entry.rightCharacterName}` : "？？？ × ？？？")}</strong>
                <div class="ending-room-meta">
                  ${escapeHtml(
                    entry.unlocked
                      ? `${entry.chapterName} · ${entry.sceneName} · ${entry.unlockedAt ? `收录于 ${formatDate(entry.unlockedAt)}` : "已收录"}`
                      : `${entry.chapterName} · ${entry.sceneName} · 未收录`
                  )}
                </div>
                <p>${escapeHtml(
                  entry.unlocked
                    ? truncateText(entry.previewText || "这组角色已经在剧情里真正同场出现过。", 72)
                    : "推进到两位角色同场后，这组关系会收录。"
                )}</p>
              </button>
            </article>
          `
        )
        .join("")
    : renderEmpty("这个项目当前还没有可收录的双人关系条目。");
}

function renderChapterDialog() {
  if (!refs.chapterDialog || !refs.chapterDialogSummary || !refs.chapterDialogHero || !refs.chapterDialogList) {
    return;
  }

  const entries = buildChapterReplayDialogEntries();
  const selectedChapterId = getSafeChapterReplayId(state.selectedChapterReplayId);
  const selectedEntry = entries.find((entry) => entry.chapterId === selectedChapterId) ?? entries[0] ?? null;
  const unlockedCount = entries.filter((entry) => entry.unlocked).length;
  state.selectedChapterReplayId = selectedEntry?.chapterId ?? null;

  refs.chapterDialog.hidden = !state.chapterDialogOpen;
  refs.chapterDialog.classList.toggle("is-visible", state.chapterDialogOpen);
  refs.chapterDialogSummary.textContent =
    entries.length > 0
      ? `当前已开放 ${unlockedCount} / ${entries.length} 章。第一次真正走到某一章里的场景后，这一章就会在标题页章节选集里亮起。`
      : "这个项目当前还没有章节条目。";

  if (!selectedEntry) {
    refs.chapterDialogHero.innerHTML = renderEmpty("这个项目当前还没有章节条目。");
    refs.chapterDialogList.innerHTML = "";
    return;
  }

  refs.chapterDialogHero.innerHTML = selectedEntry.unlocked
    ? `
        <div class="extra-hero-image-wrap">
          ${
            selectedEntry.previewBackgroundUrl
              ? `<img class="extra-hero-image" src="${escapeHtml(selectedEntry.previewBackgroundUrl)}" alt="${escapeHtml(selectedEntry.name)}" />`
              : `<div class="extra-hero-locked">这一章当前没有可显示的背景预览。</div>`
          }
        </div>
        <div class="extra-hero-copy">
          <strong>${escapeHtml(selectedEntry.name)}</strong>
          <span>${escapeHtml(`这一章共有 ${selectedEntry.sceneCount} 个场景，章节开头是：${selectedEntry.firstSceneName}`)}</span>
          <span>${escapeHtml(
            `${selectedEntry.previewSpeakerName || "章节导语"} · ${truncateText(selectedEntry.previewText || selectedEntry.notes || "这里会显示这一章开头的回放摘要。", 72)}`
          )}</span>
          <span>${escapeHtml(
            `开放时间：${selectedEntry.unlockedAt ? formatDate(selectedEntry.unlockedAt) : "未记录"}`
          )}</span>
          <div class="detail-actions">
            <button class="pill-button" type="button" data-chapter-replay="${escapeHtml(selectedEntry.chapterId)}">从这一章开头重放</button>
          </div>
        </div>
      `
    : `
        <div class="extra-hero-locked">这一章还没有开放。</div>
        <div class="extra-hero-copy">
          <strong>？？？</strong>
          <span>${escapeHtml(`推进到这一章后即可解锁。`)}</span>
          <span>${escapeHtml(`这一章共有 ${selectedEntry.sceneCount} 个场景。`)}</span>
        </div>
      `;

  refs.chapterDialogList.innerHTML = entries.length
    ? entries
        .map(
          (entry) => `
            <article class="ending-room-card ${entry.chapterId === selectedEntry.chapterId ? "is-active" : ""} ${entry.unlocked ? "" : "is-locked"}">
              <button
                class="history-main-button"
                type="button"
                data-chapter-id="${escapeHtml(entry.chapterId)}"
              >
                <strong>${escapeHtml(entry.unlocked ? entry.name : `？？？ · 第 ${entry.order} 章`)}</strong>
                <div class="ending-room-meta">
                  ${escapeHtml(
                    entry.unlocked
                      ? `${entry.sceneCount} 个场景 · ${entry.unlockedAt ? `开放于 ${formatDate(entry.unlockedAt)}` : "已开放"}`
                      : `${entry.sceneCount} 个场景 · 未开放`
                  )}
                </div>
                <p>${escapeHtml(entry.unlocked ? truncateText(entry.notes || `章节开头：${entry.firstSceneName}`, 72) : "推进主流程后开放")}</p>
              </button>
              <div class="music-room-actions">
                <button
                  class="pill-button ${entry.unlocked ? "" : "is-secondary"}"
                  type="button"
                  data-chapter-replay="${escapeHtml(entry.chapterId)}"
                  ${entry.unlocked && entry.firstSceneId ? "" : "disabled"}
                >
                  ${entry.unlocked ? "重放这一章" : "未开放"}
                </button>
              </div>
            </article>
          `
        )
        .join("")
    : renderEmpty("这个项目当前还没有章节条目。");
}

function renderProfileDialog() {
  if (!refs.profileDialog || !refs.profileDialogSummary || !refs.profileDialogHero || !refs.profileDialogList) {
    return;
  }

  const stats = buildPlayerProfileStats();
  const profile = stats.profile;
  const sections = [
    {
      title: "游玩记录",
      meta: profile.sessionCount > 0 ? `累计 ${profile.sessionCount} 次 · 继续试玩 ${profile.resumedCount} 次` : "当前还没有正式游玩记录",
      body:
        profile.sessionCount > 0
          ? `累计游玩 ${formatPlayDuration(profile.totalPlayMs)} · 最近开始 ${profile.lastPlayedAt ? formatDate(profile.lastPlayedAt) : "未记录"}`
          : "开始试玩后，这里会开始记录本机游玩档案。",
    },
    {
      title: "存档状态",
      meta: `${stats.formalSaveCount} 个正式存档 · 快速存档 ${stats.hasQuickSave ? "已存在" : "未创建"}`,
      body: `自动续玩 ${stats.hasAutoResume ? "已记录" : "暂未记录"} · 标题页和系统菜单都会沿用这批本机存档。`,
    },
    {
      title: "章节选集",
      meta:
        stats.chapterEntries.length > 0
          ? `${state.chapterReplayProgress.size} / ${stats.chapterEntries.length} 已开放`
          : "当前没有章节条目",
      body:
        stats.chapterEntries.length > 0
          ? "推进到哪一章，就开放哪一章；之后可直接从该章的第一个场景开头重放。"
          : "项目具备第一章后，这里才会开始累计章节回放进度。",
    },
    {
      title: "地点图鉴",
      meta:
        stats.locationEntries.length > 0
          ? `${state.locationArchiveProgress.size} / ${stats.locationEntries.length} 已收录`
          : "当前没有地点条目",
      body:
        stats.locationEntries.length > 0
          ? "推进到这张背景第一次出现的位置后，这个地点会收录到标题页地点图鉴。"
          : "剧情中出现背景切换后，这里才会开始累计地点图鉴进度。",
    },
    {
      title: "旁白摘录",
      meta:
        stats.narrationEntries.length > 0
          ? `${state.narrationArchiveProgress.size} / ${stats.narrationEntries.length} 已收录`
          : "当前没有旁白摘录条目",
      body:
        stats.narrationEntries.length > 0
          ? "推进到这段旁白后，它会收录到标题页摘录馆，之后可在标题页回看。"
          : "剧情中出现旁白段落后，这里才会开始累计摘录收藏进度。",
    },
    {
      title: "关系图鉴",
      meta:
        stats.relationEntries.length > 0
          ? `${state.relationArchiveProgress.size} / ${stats.relationEntries.length} 已收录`
          : "当前没有关系条目",
      body:
        stats.relationEntries.length > 0
          ? "两位角色首次同场后，这组共演关系会收录到标题页关系图鉴。"
          : "剧情中出现双人互动场景后，这里才会开始累计关系图鉴进度。",
    },
    {
      title: "语音回听",
      meta:
        stats.voiceReplayEntries.length > 0
          ? `${state.voiceReplayProgress.size} / ${stats.voiceReplayEntries.length} 已收录`
          : "当前没有可回听的语音台词",
      body:
        stats.voiceReplayEntries.length > 0
          ? "推进到这句带真实语音的台词后，这里会收录，之后可直接在标题页回放。"
          : "项目中有可播放的语音台词后，这里才会开始累计。",
    },
    {
      title: "成就馆",
      meta:
        stats.achievementEntries.length > 0
          ? `${state.achievementProgress.size} / ${stats.achievementEntries.length} 已达成`
          : "当前没有自动成就",
      body:
        stats.achievementEntries.length > 0
          ? "会根据开始试玩、首次选项、图鉴收录、结局回收和 EXTRA 全收集自动点亮。"
          : "项目内容达到对应条件后，标题页成就馆会开始累计。",
    },
    {
      title: "角色图鉴 / 结局回收",
      meta: `${state.characterArchive.size} / ${stats.characterEntries.length || 0} 角色 · ${state.endingProgress.unlocked.size} / ${stats.endingScenes.length || 0} 结局`,
      body: `角色图鉴记录已见过和说过话的角色，结局回收记录已真正通关的路线。`,
    },
    {
      title: "EXTRA 收藏",
      meta: `${state.extraUnlocks.cg.size} / ${stats.galleryAssets.length || 0} CG · ${state.extraUnlocks.bgm.size} / ${stats.musicAssets.length || 0} BGM`,
      body: `首次看到某张 CG、首次听到某首 BGM 后，这里会同步累计对应收藏进度。`,
    },
  ];

  refs.profileDialog.hidden = !state.profileDialogOpen;
  refs.profileDialog.classList.toggle("is-visible", state.profileDialogOpen);
  refs.profileDialogSummary.textContent =
    profile.sessionCount > 0
      ? `这份玩家档案会把游玩记录、存档、章节、成就、图鉴、结局和 EXTRA 收藏一起记在本机里。当前已游玩 ${profile.sessionCount} 次，累计 ${formatPlayDuration(profile.totalPlayMs)}。`
      : "这份玩家档案会把游玩记录、存档、章节、成就、图鉴、结局和 EXTRA 收藏一起记录在本机里。开始试玩后会逐步累积。";

  refs.profileDialogHero.innerHTML = `
    <div class="extra-hero-copy">
      <strong>${escapeHtml(data.project.title ?? "Canvasia Engine")} · 玩家档案</strong>
      <span>${escapeHtml(
        profile.firstPlayedAt
          ? `第一次开始：${formatDate(profile.firstPlayedAt)} · 最近一次开始：${profile.lastPlayedAt ? formatDate(profile.lastPlayedAt) : "未记录"}`
          : "还没有正式开始试玩记录。"
      )}</span>
      <div class="achievement-badge-strip">
        <span class="achievement-badge">${escapeHtml(`累计游玩：${formatPlayDuration(profile.totalPlayMs)}`)}</span>
        <span class="achievement-badge">${escapeHtml(`开始次数：${profile.sessionCount} 次`)}</span>
        <span class="achievement-badge">${escapeHtml(`继续次数：${profile.resumedCount} 次`)}</span>
        <span class="achievement-badge">${escapeHtml(`返回标题：${profile.returnToTitleCount} 次`)}</span>
      </div>
      <span>${escapeHtml("这份档案只会保存在玩家自己的浏览器里，不会写回项目文件。")}</span>
    </div>
  `;

  refs.profileDialogList.innerHTML = sections
    .map(
      (section) => `
        <article class="ending-room-card">
          <div class="history-main-button">
            <strong>${escapeHtml(section.title)}</strong>
            <div class="ending-room-meta">${escapeHtml(section.meta)}</div>
            <p>${escapeHtml(section.body)}</p>
          </div>
        </article>
      `
    )
    .join("");
}

function getVoiceReplayProgressEntry(entryId) {
  return (
    state.voiceReplayProgress.get(entryId) ?? {
      unlockedAt: null,
      lastHeardAt: null,
      heardCount: 0,
    }
  );
}

function buildVoiceReplayEntries() {
  return getVoiceReplayEntries().map((entry) => {
    const progress = getVoiceReplayProgressEntry(entry.id);
    return {
      ...entry,
      unlocked: Boolean(progress.unlockedAt),
      unlockedAt: progress.unlockedAt,
      lastHeardAt: progress.lastHeardAt,
      heardCount: progress.heardCount,
      isCurrent: state.currentVoiceReplayPreviewId === entry.id && Boolean(voiceReplayAudio),
    };
  });
}

function openVoiceReplayDialog() {
  if (!getVoiceReplayEntries().length) {
    return false;
  }

  state.profileDialogOpen = false;
  state.voiceReplayDialogOpen = true;
  state.achievementDialogOpen = false;
  state.chapterDialogOpen = false;
  state.locationDialogOpen = false;
  state.characterDialogOpen = false;
  state.endingDialogOpen = false;
  state.galleryDialogOpen = false;
  state.musicRoomDialogOpen = false;
  stopMusicRoomPreview();
  stopVoiceReplayPreview({ rerender: false });
  state.selectedVoiceReplayId = getSafeVoiceReplayId(state.selectedVoiceReplayId);
  renderProfileDialog();
  renderVoiceReplayDialog();
  renderAchievementDialog();
  renderChapterDialog();
  renderLocationDialog();
  renderCharacterDialog();
  renderEndingDialog();
  renderGalleryDialog();
  renderMusicRoomDialog();
  return true;
}

function closeVoiceReplayDialog() {
  if (!state.voiceReplayDialogOpen) {
    return false;
  }

  state.voiceReplayDialogOpen = false;
  stopVoiceReplayPreview();
  renderVoiceReplayDialog();
  return true;
}

function handleVoiceReplayDialogClick(event) {
  const itemButton = event.target.closest("[data-voice-replay-id]");
  if (itemButton) {
    state.selectedVoiceReplayId = getSafeVoiceReplayId(itemButton.dataset.voiceReplayId);
    renderVoiceReplayDialog();
    return;
  }

  const playButton = event.target.closest("[data-voice-replay-play]");
  if (playButton) {
    void playVoiceReplayPreview(playButton.dataset.voiceReplayPlay);
    return;
  }

  const stopButton = event.target.closest("[data-voice-replay-stop]");
  if (stopButton) {
    stopVoiceReplayPreview();
  }
}

function renderVoiceReplayDialog() {
  if (!refs.voiceReplayDialog || !refs.voiceReplayDialogSummary || !refs.voiceReplayDialogHero || !refs.voiceReplayDialogList) {
    return;
  }

  const entries = buildVoiceReplayEntries();
  const selectedEntryId = getSafeVoiceReplayId(state.selectedVoiceReplayId);
  const selectedEntry = entries.find((entry) => entry.id === selectedEntryId) ?? entries[0] ?? null;
  const unlockedCount = entries.filter((entry) => entry.unlocked).length;
  state.selectedVoiceReplayId = selectedEntry?.id ?? null;

  refs.voiceReplayDialog.hidden = !state.voiceReplayDialogOpen;
  refs.voiceReplayDialog.classList.toggle("is-visible", state.voiceReplayDialogOpen);
  refs.voiceReplayDialogSummary.textContent =
    entries.length > 0
      ? `当前已收录 ${unlockedCount} / ${entries.length} 句。推进到带真实语音的台词后即可解锁。`
      : "这个项目当前还没有可回听的语音台词。";

  if (!selectedEntry) {
    refs.voiceReplayDialogHero.innerHTML = renderEmpty("这个项目当前还没有可回听的语音条目。");
    refs.voiceReplayDialogList.innerHTML = "";
    return;
  }

  refs.voiceReplayDialogHero.innerHTML = selectedEntry.unlocked
    ? `
        <div class="extra-hero-copy">
          <strong>${escapeHtml(selectedEntry.speakerName)} · ${escapeHtml(selectedEntry.voiceName)}</strong>
          <span>${escapeHtml(`${selectedEntry.chapterName} · ${selectedEntry.sceneName}`)}</span>
          <span>${escapeHtml(truncateText(selectedEntry.text || "这句台词暂时没有正文。", 120))}</span>
          <div class="achievement-badge-strip">
            <span class="achievement-badge">${escapeHtml(`已回听 ${selectedEntry.heardCount} 次`)}</span>
            <span class="achievement-badge">${escapeHtml(`首次收录：${formatDate(selectedEntry.unlockedAt)}`)}</span>
            <span class="achievement-badge">${escapeHtml(`最近一次：${selectedEntry.lastHeardAt ? formatDate(selectedEntry.lastHeardAt) : "未记录"}`)}</span>
          </div>
          <div class="detail-actions">
            <button class="pill-button" type="button" data-voice-replay-play="${escapeHtml(selectedEntry.id)}">
              ${selectedEntry.isCurrent ? "重新播放这句" : "播放这句语音"}
            </button>
            ${
              selectedEntry.isCurrent
                ? '<button class="pill-button is-secondary" type="button" data-voice-replay-stop>停止回听</button>'
                : ""
            }
          </div>
        </div>
      `
    : `
        <div class="extra-hero-locked">这句语音还没有解锁。</div>
        <div class="extra-hero-copy">
          <strong>？？？ · 名台词回放馆</strong>
          <span>推进到这句带真实语音的台词后会收录到这里。</span>
        </div>
      `;

  refs.voiceReplayDialogList.innerHTML = entries.length
    ? entries
        .map(
          (entry) => `
            <article class="ending-room-card ${entry.id === selectedEntry.id ? "is-active" : ""} ${entry.unlocked ? "" : "is-locked"}">
              <button class="history-main-button" type="button" data-voice-replay-id="${escapeHtml(entry.id)}">
                <strong>${escapeHtml(entry.unlocked ? `${entry.speakerName} · ${entry.sceneName}` : "？？？ · 未解锁")}</strong>
                <div class="ending-room-meta">
                  ${escapeHtml(
                    entry.unlocked
                      ? `${entry.chapterName} · 已回听 ${entry.heardCount} 次`
                      : `${entry.chapterName} · 推进剧情后解锁`
                  )}
                </div>
                <p>${escapeHtml(entry.unlocked ? truncateText(entry.text || "这句台词暂时没有正文。", 80) : "推进到对应剧情后，这句带语音的台词会收录到这里。")}</p>
              </button>
              <div class="music-room-actions">
                <button
                  class="pill-button ${entry.unlocked ? "" : "is-secondary"}"
                  type="button"
                  data-voice-replay-play="${escapeHtml(entry.id)}"
                  ${entry.unlocked ? "" : "disabled"}
                >
                  ${entry.isCurrent ? "正在回听" : entry.unlocked ? "回听这句" : "未解锁"}
                </button>
              </div>
            </article>
          `
        )
        .join("")
    : renderEmpty("这个项目当前还没有可回听的语音条目。");
}

async function playVoiceReplayPreview(entryId) {
  const safeEntryId = getSafeVoiceReplayId(entryId);
  const entry = safeEntryId ? getVoiceReplayEntryMap().get(safeEntryId) : null;
  const progress = safeEntryId ? getVoiceReplayProgressEntry(safeEntryId) : null;

  if (!entry || !progress?.unlocked || !entry.voiceUrl) {
    return false;
  }

  stopVoicePlayback();
  stopMusicRoomPreview();

  if (state.currentVoiceReplayPreviewId === safeEntryId && voiceReplayAudio && !voiceReplayAudio.paused) {
    stopVoiceReplayPreview();
    return true;
  }

  stopVoiceReplayPreview({ rerender: false });

  const audio = new Audio(entry.voiceUrl);
  audio.volume = getVolumeRatio(state.playback.voiceVolume, 92) * getVolumeRatio(entry.voiceVolume, 100);
  audio.addEventListener("ended", () => {
    stopVoiceReplayPreview();
  });
  audio.addEventListener("error", () => {
    stopVoiceReplayPreview();
  });

  voiceReplayAudio = audio;
  state.currentVoiceReplayPreviewId = safeEntryId;
  renderVoiceReplayDialog();

  try {
    await audio.play();
  } catch (error) {
    stopVoiceReplayPreview();
    return false;
  }

  return true;
}

function stopVoiceReplayPreview({ rerender = true } = {}) {
  if (voiceReplayAudio) {
    voiceReplayAudio.pause();
    voiceReplayAudio.src = "";
    voiceReplayAudio = null;
  }

  state.currentVoiceReplayPreviewId = null;
  if (rerender) {
    renderVoiceReplayDialog();
  }
}

function unlockVoiceReplayEntry(snapshot) {
  if (!snapshot || (snapshot.blockType !== "dialogue" && snapshot.blockType !== "narration")) {
    return false;
  }

  const voiceAssetId = getVoiceAssetId(snapshot);
  const voiceAsset = data.assetsById.get(voiceAssetId);
  if (!voiceAssetId || !voiceAsset || voiceAsset.type !== "voice" || !getAssetUrl(voiceAssetId)) {
    return false;
  }

  const stepKey = `${snapshot.sceneId ?? "none"}:${snapshot.blockId ?? "block"}:${snapshot.blockIndex}`;
  if (state.lastVoiceReplayStepKey === stepKey) {
    return false;
  }

  state.lastVoiceReplayStepKey = stepKey;
  const entryId = buildVoiceReplayEntryId(snapshot.sceneId, snapshot.blockId, snapshot.blockIndex);
  const now = new Date().toISOString();
  const existing = state.voiceReplayProgress.get(entryId);

  state.voiceReplayProgress.set(entryId, {
    unlockedAt: existing?.unlockedAt ?? now,
    lastHeardAt: now,
    heardCount: Math.max(1, (existing?.heardCount ?? 0) + 1),
  });
  persistVoiceReplayProgress();
  refs.gameMeta.textContent = buildMetaSummary();
  renderStartSummary();
  renderBuildInfo();
  renderExtraButtons();
  renderProfileDialog();
  renderVoiceReplayDialog();
  return true;
}

function unlockLocationArchiveEntry(snapshot) {
  const backgroundAssetId = snapshot?.visualState?.backgroundAssetId;
  const backgroundAsset = data.assetsById.get(backgroundAssetId);
  if (!backgroundAssetId || !backgroundAsset || backgroundAsset.type !== "background") {
    return false;
  }

  const stepKey = `${snapshot.sceneId ?? "none"}:${backgroundAssetId}:${snapshot.blockIndex}`;
  if (state.lastLocationArchiveStepKey === stepKey) {
    return false;
  }

  state.lastLocationArchiveStepKey = stepKey;
  if (state.locationArchiveProgress.has(backgroundAssetId)) {
    return false;
  }

  if (!getLocationArchiveEntries().some((entry) => entry.id === backgroundAssetId)) {
    return false;
  }

  state.locationArchiveProgress.set(backgroundAssetId, new Date().toISOString());
  persistLocationArchiveProgress();
  refs.gameMeta.textContent = buildMetaSummary();
  renderStartSummary();
  renderBuildInfo();
  renderExtraButtons();
  renderProfileDialog();
  renderLocationDialog();
  return true;
}

function unlockNarrationArchiveEntry(snapshot) {
  if (!snapshot || snapshot.blockType !== "narration") {
    return false;
  }

  const entryId = buildNarrationArchiveEntryId(snapshot.sceneId, snapshot.blockId, snapshot.blockIndex);
  const stepKey = `${entryId}:${snapshot.blockIndex}`;
  if (state.lastNarrationArchiveStepKey === stepKey) {
    return false;
  }

  state.lastNarrationArchiveStepKey = stepKey;
  if (state.narrationArchiveProgress.has(entryId)) {
    return false;
  }

  if (!getNarrationArchiveEntries().some((entry) => entry.id === entryId)) {
    return false;
  }

  state.narrationArchiveProgress.set(entryId, new Date().toISOString());
  persistNarrationArchiveProgress();
  refs.gameMeta.textContent = buildMetaSummary();
  renderStartSummary();
  renderBuildInfo();
  renderExtraButtons();
  renderProfileDialog();
  renderNarrationDialog();
  return true;
}

function unlockRelationArchiveEntries(snapshot) {
  if (!snapshot?.sceneId) {
    return false;
  }

  const scene = data.scenesById.get(snapshot.sceneId);
  if (!scene) {
    return false;
  }

  const encounteredCharacterIds = collectSceneEncounterCharacterIds(scene, snapshot.blockIndex);
  if (encounteredCharacterIds.length < 2) {
    return false;
  }

  let changed = false;
  const unlockedAt = new Date().toISOString();

  for (let index = 0; index < encounteredCharacterIds.length; index += 1) {
    for (let nextIndex = index + 1; nextIndex < encounteredCharacterIds.length; nextIndex += 1) {
      const relationId = buildRelationshipArchiveId(
        encounteredCharacterIds[index],
        encounteredCharacterIds[nextIndex]
      );
      if (state.relationArchiveProgress.has(relationId)) {
        continue;
      }
      if (!getRelationshipArchiveEntries().some((entry) => entry.id === relationId)) {
        continue;
      }

      state.relationArchiveProgress.set(relationId, unlockedAt);
      changed = true;
    }
  }

  if (!changed) {
    return false;
  }

  persistRelationArchiveProgress();
  refs.gameMeta.textContent = buildMetaSummary();
  renderStartSummary();
  renderBuildInfo();
  renderExtraButtons();
  renderProfileDialog();
  renderRelationDialog();
  return true;
}

function unlockCharacterArchiveEntry(characterId) {
  if (!characterId || state.characterArchive.has(characterId)) {
    return false;
  }

  if (!data.charactersById.has(characterId)) {
    return false;
  }

  state.characterArchive.add(characterId);
  persistCharacterArchive();
  syncAchievementProgressFromState();
  refs.gameMeta.textContent = buildMetaSummary();
  renderStartSummary();
  renderBuildInfo();
  renderExtraButtons();
  renderProfileDialog();
  renderAchievementDialog();
  renderCharacterDialog();
  return true;
}

function buildCharacterArchiveEntries() {
  return getCharacterArchiveEntries().map((character) => {
    const defaultExpression = character.expressions?.[0] ?? null;
    const defaultSpriteAssetId = defaultExpression?.spriteAssetId ?? character.defaultSpriteId ?? null;
    return {
      ...character,
      unlocked: state.characterArchive.has(character.id),
      defaultSpriteAssetId,
      defaultSpriteUrl: defaultSpriteAssetId ? getAssetUrl(defaultSpriteAssetId) : "",
      expressions:
        (character.expressions ?? []).map((expression) => ({
          ...expression,
          imageUrl: expression.spriteAssetId ? getAssetUrl(expression.spriteAssetId) : "",
        })) ?? [],
    };
  });
}

function renderCharacterDialog() {
  if (!refs.characterDialog || !refs.characterDialogSummary || !refs.characterDialogHero || !refs.characterDialogList) {
    return;
  }

  const entries = buildCharacterArchiveEntries();
  const selectedCharacterId = getSafeCharacterArchiveId(state.selectedCharacterArchiveId);
  const selectedEntry = entries.find((entry) => entry.id === selectedCharacterId) ?? entries[0] ?? null;
  const unlockedCount = entries.filter((entry) => entry.unlocked).length;
  state.selectedCharacterArchiveId = selectedEntry?.id ?? null;

  refs.characterDialog.hidden = !state.characterDialogOpen;
  refs.characterDialog.classList.toggle("is-visible", state.characterDialogOpen);
  refs.characterDialogSummary.textContent =
    entries.length > 0
      ? `当前已收录 ${unlockedCount} / ${entries.length} 位角色。首次见到角色或角色首次开口后即可解锁。`
      : "这个项目当前还没有可收录的角色。";

  if (!selectedEntry) {
    refs.characterDialogHero.innerHTML = renderEmpty("这个项目当前还没有角色条目。");
    refs.characterDialogList.innerHTML = "";
    return;
  }

  const selectedDisplayName = getCharacterName(selectedEntry.id);
  refs.characterDialogHero.innerHTML = selectedEntry.unlocked
    ? `
        <div class="extra-hero-image-wrap">
          ${
            selectedEntry.defaultSpriteUrl
              ? `<img class="extra-hero-image" src="${escapeHtml(selectedEntry.defaultSpriteUrl)}" alt="${escapeHtml(selectedDisplayName)}" />`
              : `<div class="extra-hero-locked">这个角色当前没有可显示的立绘文件。</div>`
          }
        </div>
        <div class="extra-hero-copy">
          <strong>${escapeHtml(selectedDisplayName)}</strong>
          <span>${escapeHtml(selectedEntry.bio || "这个角色暂时还没有简介。")}</span>
          <span>${escapeHtml(`默认站位：${getPositionLabel(selectedEntry.defaultPosition ?? "center")} · 表情 ${selectedEntry.expressions.length} 种`)}</span>
          <div class="character-expression-strip">
            ${
              selectedEntry.expressions.length > 0
                ? selectedEntry.expressions
                    .map(
                      (expression) => `
                        <div class="character-expression-chip">
                          <div class="character-expression-thumb">
                            ${
                              expression.imageUrl
                                ? `<img src="${escapeHtml(expression.imageUrl)}" alt="${escapeHtml(expression.name)}" />`
                                : `<span>${escapeHtml(expression.name.slice(0, 1) || "?")}</span>`
                            }
                          </div>
                          <span>${escapeHtml(expression.name)}</span>
                        </div>
                      `
                    )
                    .join("")
                : `<div class="empty-note">这个角色目前还没有配置表情。</div>`
            }
          </div>
        </div>
      `
    : `
        <div class="extra-hero-locked">这个角色还没有解锁。</div>
        <div class="extra-hero-copy">
          <strong>？？？</strong>
          <span>推进剧情后，这里会收录已经见过的角色。</span>
        </div>
      `;

  refs.characterDialogList.innerHTML = entries.length
    ? entries
        .map((entry) => {
          const displayName = getCharacterName(entry.id);
          return `
            <button
              class="extra-gallery-card ${entry.id === selectedEntry.id ? "is-active" : ""} ${entry.unlocked ? "" : "is-locked"}"
              type="button"
              data-character-archive-id="${escapeHtml(entry.id)}"
            >
              <div class="extra-gallery-thumb">
                ${
                  entry.unlocked && entry.defaultSpriteUrl
                    ? `<img src="${escapeHtml(entry.defaultSpriteUrl)}" alt="${escapeHtml(displayName)}" />`
                    : `<span>${entry.unlocked ? "待载入" : "未解锁"}</span>`
                }
              </div>
              <strong>${escapeHtml(entry.unlocked ? displayName : "？？？")}</strong>
              <span>${escapeHtml(entry.unlocked ? (entry.bio || "已收录角色资料") : "推进剧情后解锁")}</span>
            </button>
          `;
        })
        .join("")
    : renderEmpty("这个项目当前还没有角色条目。");
}

function buildAchievementEntries() {
  return getAchievementDefinitions().map((achievement) => {
    const unlockedAt = state.achievementProgress.get(achievement.id) ?? null;
    const progressCurrent = Math.max(0, Math.min(achievement.progressCurrent ?? 0, achievement.progressTarget ?? 1));
    const progressTarget = Math.max(achievement.progressTarget ?? 1, 1);

    return {
      ...achievement,
      unlocked: Boolean(unlockedAt),
      unlockedAt,
      progressCurrent,
      progressTarget,
      progressLabel:
        progressTarget > 1 ? `${progressCurrent} / ${progressTarget}` : progressCurrent >= progressTarget ? "已达成" : "未达成",
    };
  });
}

function renderAchievementDialog() {
  if (!refs.achievementDialog || !refs.achievementDialogSummary || !refs.achievementDialogHero || !refs.achievementDialogList) {
    return;
  }

  const entries = buildAchievementEntries();
  const selectedAchievementId = getSafeAchievementId(state.selectedAchievementId);
  const selectedEntry = entries.find((entry) => entry.id === selectedAchievementId) ?? entries[0] ?? null;
  const unlockedCount = entries.filter((entry) => entry.unlocked).length;
  state.selectedAchievementId = selectedEntry?.id ?? null;

  refs.achievementDialog.hidden = !state.achievementDialogOpen;
  refs.achievementDialog.classList.toggle("is-visible", state.achievementDialogOpen);
  refs.achievementDialogSummary.textContent =
    entries.length > 0
      ? `当前已达成 ${unlockedCount} / ${entries.length} 个自动成就。它们会根据试玩推进、图鉴收录、结局回收和 EXTRA 解锁自动点亮。`
      : "这个项目当前还没有可收录的成就。";

  if (!selectedEntry) {
    refs.achievementDialogHero.innerHTML = renderEmpty("这个项目当前还没有可收录的成就。");
    refs.achievementDialogList.innerHTML = "";
    return;
  }

  refs.achievementDialogHero.innerHTML = `
    <div class="extra-hero-copy">
      <strong>${escapeHtml(selectedEntry.unlocked ? selectedEntry.name : `？？？ · ${selectedEntry.name}`)}</strong>
      <span>${escapeHtml(selectedEntry.description)}</span>
      <div class="achievement-badge-strip">
        <span class="achievement-badge">${escapeHtml(selectedEntry.category)}</span>
        <span class="achievement-badge">${escapeHtml(`进度：${selectedEntry.progressLabel}`)}</span>
        <span class="achievement-badge">${escapeHtml(selectedEntry.unlocked ? `达成于 ${formatDate(selectedEntry.unlockedAt)}` : "推进剧情后自动达成")}</span>
      </div>
      <span>${escapeHtml(`目标：${selectedEntry.requirement}`)}</span>
    </div>
  `;

  refs.achievementDialogList.innerHTML = entries.length
    ? entries
        .map(
          (entry) => `
            <article class="ending-room-card ${entry.id === selectedEntry.id ? "is-active" : ""} ${entry.unlocked ? "" : "is-locked"}">
              <button
                class="history-main-button"
                type="button"
                data-achievement-id="${escapeHtml(entry.id)}"
              >
                <strong>${escapeHtml(entry.unlocked ? entry.name : `？？？ · ${entry.name}`)}</strong>
                <div class="ending-room-meta">
                  ${escapeHtml(entry.category)} · ${escapeHtml(entry.progressLabel)}
                </div>
                <p>${escapeHtml(entry.unlocked ? entry.description : `目标：${entry.requirement}`)}</p>
              </button>
            </article>
          `
        )
        .join("")
    : renderEmpty("这个项目当前还没有可收录的成就。");
}

function recordEndingCompletion(sceneId) {
  const safeSceneId = getSafeEndingSceneId(sceneId);
  if (!safeSceneId || !getEndingScenes().some((scene) => scene.id === safeSceneId)) {
    return false;
  }

  const now = new Date().toISOString();
  if (!state.endingProgress.unlocked.has(safeSceneId)) {
    state.endingProgress.unlocked.set(safeSceneId, now);
  }
  state.endingProgress.completionCount += 1;
  state.endingProgress.lastCompletedAt = now;
  persistEndingProgress();
  syncAchievementProgressFromState();
  refs.gameMeta.textContent = buildMetaSummary();
  renderStartSummary();
  renderBuildInfo();
  renderExtraButtons();
  renderProfileDialog();
  renderAchievementDialog();
  renderEndingDialog();
  return true;
}

function buildEndingEntries() {
  return getEndingScenes().map((scene) => {
    const unlockedAt = state.endingProgress.unlocked.get(scene.id) ?? null;
    return {
      ...scene,
      unlocked: Boolean(unlockedAt),
      unlockedAt,
      preview: buildEndingScenePreview(scene),
    };
  });
}

function renderEndingDialog() {
  if (!refs.endingDialog || !refs.endingDialogSummary || !refs.endingDialogHero || !refs.endingDialogList) {
    return;
  }

  const entries = buildEndingEntries();
  const selectedSceneId = getSafeEndingSceneId(state.selectedEndingSceneId);
  const selectedEntry = entries.find((entry) => entry.id === selectedSceneId) ?? entries[0] ?? null;
  const unlockedCount = entries.filter((entry) => entry.unlocked).length;
  state.selectedEndingSceneId = selectedEntry?.id ?? null;

  refs.endingDialog.hidden = !state.endingDialogOpen;
  refs.endingDialog.classList.toggle("is-visible", state.endingDialogOpen);
  refs.endingDialogSummary.textContent =
    entries.length > 0
      ? `当前已回收 ${unlockedCount} / ${entries.length} 个结局 · 累计通关 ${state.endingProgress.completionCount} 次${
          state.endingProgress.lastCompletedAt ? ` · 最近一次 ${formatDate(state.endingProgress.lastCompletedAt)}` : ""
        }`
      : "这个项目当前还没有可回收的结局场景。";

  if (!selectedEntry) {
    refs.endingDialogHero.innerHTML = renderEmpty("这个项目当前还没有可回收的结局场景。");
    refs.endingDialogList.innerHTML = "";
    return;
  }

  const preview = selectedEntry.preview ?? {};
  refs.endingDialogHero.innerHTML = selectedEntry.unlocked
    ? `
        <div class="extra-hero-image-wrap">
          ${
            preview.backgroundUrl
              ? `<img class="extra-hero-image" src="${escapeHtml(preview.backgroundUrl)}" alt="${escapeHtml(selectedEntry.name)}" />`
              : `<div class="extra-hero-locked">这个结局当前没有可显示的背景预览。</div>`
          }
        </div>
        <div class="extra-hero-copy">
          <strong>${escapeHtml(selectedEntry.name)}</strong>
          <span>${escapeHtml(
            `${selectedEntry.chapterName} · ${selectedEntry.notes || "这个场景会在路线收束时自动记进回收馆。"}`
          )}</span>
          <span>${escapeHtml(
            `预览：${preview.speakerName || "结局"} · ${truncateText(preview.dialogueText || "这条路线已经走到了收束位置。", 68)}`
          )}</span>
          <span>${escapeHtml(
            `收录时间：${selectedEntry.unlockedAt ? formatDate(selectedEntry.unlockedAt) : "未记录"}`
          )}</span>
          <div class="detail-actions">
            <button class="pill-button" type="button" data-ending-replay="${escapeHtml(selectedEntry.id)}">回放这个结局</button>
          </div>
        </div>
      `
    : `
        <div class="extra-hero-locked">这个结局还没有解锁。</div>
        <div class="extra-hero-copy">
          <strong>？？？</strong>
          <span>${escapeHtml(`${selectedEntry.chapterName} · 推进不同选项和条件分支后会收录到这里。`)}</span>
          <span>${escapeHtml(selectedEntry.notes || "你打到对应路线收尾以后，这一格就会亮起来。")}</span>
        </div>
      `;

  refs.endingDialogList.innerHTML = entries.length
    ? entries
        .map(
          (entry) => `
            <article class="ending-room-card ${entry.id === selectedEntry.id ? "is-active" : ""} ${entry.unlocked ? "" : "is-locked"}">
              <button
                class="history-main-button"
                type="button"
                data-ending-scene-id="${escapeHtml(entry.id)}"
              >
                <strong>${escapeHtml(entry.unlocked ? entry.name : "？？？")}</strong>
                <div class="ending-room-meta">
                  ${escapeHtml(entry.chapterName)} · ${escapeHtml(
                    entry.unlocked ? (entry.unlockedAt ? `收录于 ${formatDate(entry.unlockedAt)}` : "已回收") : "未解锁"
                  )}
                </div>
                <p>${escapeHtml(entry.unlocked ? truncateText(entry.notes || "这条结局已经可以从标题页直接回放。", 72) : "推进不同路线后解锁")}</p>
              </button>
              <div class="music-room-actions">
                <button
                  class="pill-button ${entry.unlocked ? "" : "is-secondary"}"
                  type="button"
                  data-ending-replay="${escapeHtml(entry.id)}"
                  ${entry.unlocked ? "" : "disabled"}
                >
                  ${entry.unlocked ? "回放结局" : "未解锁"}
                </button>
              </div>
            </article>
          `
        )
        .join("")
    : renderEmpty("这个项目当前还没有可回收的结局场景。");
}

function createPreviewSession(startSceneId) {
  const safeStartSceneId = getSafeSceneId(startSceneId);
  const initialVisualState = createInitialPreviewVisualState();
  const initialVariables = createInitialVariableState();
  const firstSnapshot = buildPreviewSnapshot(safeStartSceneId, 0, initialVisualState, initialVariables);

  return {
    startSceneId: safeStartSceneId,
    timeline: [firstSnapshot],
    position: 0,
  };
}

function buildGalleryEntries() {
  return getGalleryAssets().map((asset) => ({
    ...asset,
    unlocked: state.extraUnlocks.cg.has(asset.id),
    imageUrl: getAssetUrl(asset.id),
  }));
}

function buildMusicRoomEntries() {
  return getMusicRoomAssets().map((asset) => ({
    ...asset,
    unlocked: state.extraUnlocks.bgm.has(asset.id),
    audioUrl: getAssetUrl(asset.id),
    isCurrent: state.currentMusicRoomAssetId === asset.id && Boolean(musicRoomAudio),
  }));
}

function renderGalleryDialog() {
  if (!refs.galleryDialog || !refs.galleryDialogSummary || !refs.galleryDialogHero || !refs.galleryDialogList) {
    return;
  }

  const entries = buildGalleryEntries();
  const unlockedCount = entries.filter((entry) => entry.unlocked).length;
  const selectedAssetId = getSafeGalleryAssetId(state.selectedGalleryAssetId);
  const selectedEntry = entries.find((entry) => entry.id === selectedAssetId) ?? entries[0] ?? null;
  state.selectedGalleryAssetId = selectedEntry?.id ?? null;

  refs.galleryDialog.hidden = !state.galleryDialogOpen;
  refs.galleryDialog.classList.toggle("is-visible", state.galleryDialogOpen);
  refs.galleryDialogSummary.textContent =
    entries.length > 0
      ? `当前已解锁 ${unlockedCount} / ${entries.length} 张。首次在剧情里看到某张 CG 后会收录到这里。`
      : "这个项目当前还没有可收录的 CG 资源。";

  if (!selectedEntry) {
    refs.galleryDialogHero.innerHTML = renderEmpty("这个项目当前还没有 CG 条目。");
    refs.galleryDialogList.innerHTML = "";
    return;
  }

  refs.galleryDialogHero.innerHTML = selectedEntry.unlocked
    ? `
        <div class="extra-hero-image-wrap">
          ${
            selectedEntry.imageUrl
              ? `<img class="extra-hero-image" src="${escapeHtml(selectedEntry.imageUrl)}" alt="${escapeHtml(selectedEntry.name)}" />`
              : `<div class="extra-hero-locked">这张 CG 的图片文件暂时没有导出成功。</div>`
          }
        </div>
        <div class="extra-hero-copy">
          <strong>${escapeHtml(selectedEntry.name)}</strong>
          <span>${escapeHtml(getAssetTypeLabel(selectedEntry.type))} · ${
            selectedEntry.tags?.length ? escapeHtml(selectedEntry.tags.join(" / ")) : "已解锁"
          }</span>
        </div>
      `
    : `
        <div class="extra-hero-locked">这张 CG 还没有解锁。</div>
        <div class="extra-hero-copy">
          <strong>？？？</strong>
          <span>推进剧情后，这里会收录已经见过的 CG。</span>
        </div>
      `;

  refs.galleryDialogList.innerHTML = entries.length
    ? entries
        .map(
          (entry) => `
            <button
              class="extra-gallery-card ${entry.id === selectedEntry.id ? "is-active" : ""} ${entry.unlocked ? "" : "is-locked"}"
              type="button"
              data-gallery-asset-id="${escapeHtml(entry.id)}"
            >
              <div class="extra-gallery-thumb">
                ${
                  entry.unlocked && entry.imageUrl
                    ? `<img src="${escapeHtml(entry.imageUrl)}" alt="${escapeHtml(entry.name)}" />`
                    : `<span>${entry.unlocked ? "待载入" : "未解锁"}</span>`
                }
              </div>
              <strong>${escapeHtml(entry.unlocked ? entry.name : "？？？")}</strong>
              <span>${escapeHtml(entry.unlocked ? (entry.tags?.join(" / ") || "已解锁") : "推进剧情后解锁")}</span>
            </button>
          `
        )
        .join("")
    : renderEmpty("这个项目当前还没有 CG 条目。");
}

function renderMusicRoomDialog() {
  if (!refs.musicRoomDialog || !refs.musicRoomDialogSummary || !refs.musicRoomNowPlaying || !refs.musicRoomList) {
    return;
  }

  const entries = buildMusicRoomEntries();
  const unlockedCount = entries.filter((entry) => entry.unlocked).length;
  const currentEntry = entries.find((entry) => entry.id === state.currentMusicRoomAssetId) ?? null;

  refs.musicRoomDialog.hidden = !state.musicRoomDialogOpen;
  refs.musicRoomDialog.classList.toggle("is-visible", state.musicRoomDialogOpen);
  refs.musicRoomDialogSummary.textContent =
    entries.length > 0
      ? `当前已解锁 ${unlockedCount} / ${entries.length} 首。首次在剧情里听到某首 BGM 后会收录到这里。`
      : "这个项目当前还没有可收录的 BGM。";

  refs.musicRoomNowPlaying.innerHTML = currentEntry
    ? `
        <div class="extra-hero-copy">
          <strong>当前试听：${escapeHtml(currentEntry.name)}</strong>
          <span>${escapeHtml(currentEntry.tags?.join(" / ") || "已解锁曲目")}</span>
        </div>
        <div class="detail-actions">
          <button class="pill-button is-secondary" type="button" data-music-room-stop>停止播放</button>
        </div>
      `
    : `<div class="extra-hero-copy"><strong>当前没有正在试听的曲目</strong><span>点下面任意一首已解锁 BGM，即可在这里试听。</span></div>`;

  refs.musicRoomList.innerHTML = entries.length
    ? entries
        .map(
          (entry) => `
            <article class="music-room-card ${entry.unlocked ? "" : "is-locked"}">
              <div class="music-room-copy">
                <strong>${escapeHtml(entry.unlocked ? entry.name : "？？？")}</strong>
                <span>${escapeHtml(entry.unlocked ? (entry.tags?.join(" / ") || "已解锁曲目") : "推进剧情后解锁")}</span>
              </div>
              <div class="music-room-actions">
                <button
                  class="pill-button ${entry.isCurrent ? "" : "is-secondary"}"
                  type="button"
                  data-music-room-play="${escapeHtml(entry.id)}"
                  ${entry.unlocked && entry.audioUrl ? "" : "disabled"}
                >
                  ${entry.isCurrent ? "正在播放" : "试听这首"}
                </button>
              </div>
            </article>
          `
        )
        .join("")
    : renderEmpty("这个项目当前还没有 BGM 条目。");
}

async function toggleMusicRoomTrack(assetId) {
  const safeAssetId = getSafeMusicRoomAssetId(assetId);
  const asset = data.assetsById.get(safeAssetId);

  if (!asset || asset.type !== "bgm" || !state.extraUnlocks.bgm.has(safeAssetId)) {
    return false;
  }

  if (state.currentMusicRoomAssetId === safeAssetId && musicRoomAudio && !musicRoomAudio.paused) {
    stopMusicRoomPreview();
    renderMusicRoomDialog();
    return true;
  }

  const audioUrl = getAssetUrl(safeAssetId);
  if (!audioUrl) {
    return false;
  }

  stopMusicRoomPreview();
  const audio = new Audio(encodeURI(audioUrl));
  audio.loop = true;
  audio.volume = getVolumeRatio(state.playback.bgmVolume, 72);
  audio.addEventListener("ended", () => {
    stopMusicRoomPreview();
    renderMusicRoomDialog();
  });
  audio.addEventListener("error", () => {
    stopMusicRoomPreview();
    renderMusicRoomDialog();
  });
  await audio.play().catch(() => {});
  musicRoomAudio = audio;
  state.currentMusicRoomAssetId = safeAssetId;
  renderMusicRoomDialog();
  return true;
}

function stopMusicRoomPreview() {
  if (musicRoomAudio) {
    musicRoomAudio.pause();
    musicRoomAudio.src = "";
    musicRoomAudio = null;
  }
  state.currentMusicRoomAssetId = null;
}

function movePreviewForward() {
  const session = state.session;
  const current = getCurrentSnapshot();

  if (!session || !current || current.choiceOptions.length > 0 || current.completed) {
    return;
  }

  if (session.position < session.timeline.length - 1) {
    session.position += 1;
    persistAutoResume();
    return;
  }

  const nextSnapshot = createNextPreviewSnapshot(current);
  session.timeline.push(nextSnapshot);
  session.position = session.timeline.length - 1;
  if (nextSnapshot.completed) {
    recordEndingCompletion(nextSnapshot.sceneId);
  }
  persistAutoResume();
}

function buildChoiceOptionNextSnapshot(current, option, nextVariables) {
  const targetSceneId = option?.gotoSceneId ?? option?.targetSceneId ?? "";
  if (isChoiceContinueTarget(targetSceneId)) {
    return buildPreviewSnapshot(current.sceneId, current.blockIndex + 1, current.visualState, nextVariables);
  }
  return buildPreviewSnapshot(targetSceneId, 0, current.visualState, nextVariables);
}

function choosePreviewOption(optionId) {
  const session = state.session;
  const current = getCurrentSnapshot();

  if (!session || !current || current.choiceOptions.length === 0 || isRuntimeTypewriterActive()) {
    return;
  }

  const option = current.choiceOptions.find((item) => item.id === optionId);
  if (!option) {
    return;
  }

  unlockAchievement("first_choice");
  const nextVariables = clonePreviewVariables(current.variables);
  applyChoiceEffectsToPreviewVariables(nextVariables, option.effects ?? []);
  const nextSnapshot = buildChoiceOptionNextSnapshot(current, option, nextVariables);
  stopRuntimeAutoAdvance();
  session.timeline = session.timeline.slice(0, session.position + 1);
  session.timeline.push(nextSnapshot);
  session.position = session.timeline.length - 1;
  persistAutoResume();
  renderRuntime();
}

function getCurrentSnapshot() {
  return state.session?.timeline?.[state.session.position] ?? null;
}

function getRuntimeSnapshotKey(snapshot) {
  if (!snapshot) {
    return "";
  }

  return `${snapshot.sceneId ?? "none"}:${snapshot.blockId ?? "complete"}:${snapshot.blockIndex}:${
    state.session?.position ?? 0
  }`;
}

function shouldUseRuntimeTypewriter(snapshot) {
  if (!snapshot || snapshot.completed) {
    return false;
  }

  if (getSnapshotTextSpeed(snapshot) === "instant") {
    return false;
  }

  if (snapshot.blockType !== "dialogue" && snapshot.blockType !== "narration") {
    return false;
  }

  return (snapshot.visualState?.dialogueText ?? "").trim().length > 0;
}

function getSnapshotTextSpeed(snapshot) {
  return getSafeTextSpeed(snapshot?.block?.textSpeed ?? state.playback.textSpeed);
}

function isRuntimeTypewriterActive() {
  return Boolean(state.typingActive);
}

function stopRuntimeTypewriter() {
  if (state.typingTimer) {
    window.clearTimeout(state.typingTimer);
  }

  state.typingTimer = null;
  state.typingSnapshotKey = null;
  state.typingFullText = "";
  state.typingVisibleText = "";
  state.typingActive = false;
}

function completeRuntimeTypewriter() {
  if (!state.typingActive) {
    return false;
  }

  if (state.typingTimer) {
    window.clearTimeout(state.typingTimer);
  }

  state.typingTimer = null;
  state.typingVisibleText = state.typingFullText;
  state.typingActive = false;
  markSnapshotAsRead(getCurrentSnapshot());
  return true;
}

function syncRuntimeDialoguePresentation(snapshot) {
  if (!snapshot || !shouldUseRuntimeTypewriter(snapshot)) {
    stopRuntimeTypewriter();
    markSnapshotAsRead(snapshot);
    refs.messageText.textContent = snapshot?.visualState?.dialogueText ?? "";
    refs.messageText.classList.remove("is-typing");
    refs.choiceList.innerHTML = snapshot ? renderChoiceButtons(snapshot) : "";
    return;
  }

  if (state.playback.skipRead && isSnapshotRead(snapshot)) {
    stopRuntimeTypewriter();
    markSnapshotAsRead(snapshot);
    refs.messageText.textContent = snapshot.visualState?.dialogueText ?? "";
    refs.messageText.classList.remove("is-typing");
    refs.choiceList.innerHTML = renderChoiceButtons(snapshot);
    return;
  }

  const snapshotKey = getRuntimeSnapshotKey(snapshot);
  const fullText = snapshot.visualState?.dialogueText ?? "";

  if (state.typingSnapshotKey !== snapshotKey) {
    stopRuntimeTypewriter();
    state.typingSnapshotKey = snapshotKey;
    state.typingFullText = fullText;
    state.typingVisibleText = fullText.slice(0, getNextTypewriterIndex(fullText, 0));
    state.typingActive = state.typingVisibleText.length < fullText.length;

    if (state.typingActive) {
      scheduleRuntimeTypewriterTick(snapshotKey);
    }
  }

  refs.messageText.textContent = state.typingActive ? state.typingVisibleText : fullText;
  refs.messageText.classList.toggle("is-typing", state.typingActive);
  refs.choiceList.innerHTML = state.typingActive ? "" : renderChoiceButtons(snapshot);

  if (!state.typingActive) {
    markSnapshotAsRead(snapshot);
  }
}

function scheduleRuntimeTypewriterTick(expectedKey) {
  if (state.typingTimer) {
    window.clearTimeout(state.typingTimer);
  }

  state.typingTimer = window.setTimeout(() => {
    if (!state.typingActive || state.typingSnapshotKey !== expectedKey) {
      return;
    }

    const nextIndex = getNextTypewriterIndex(state.typingFullText, state.typingVisibleText.length);
    state.typingVisibleText = state.typingFullText.slice(0, nextIndex);
    refs.messageText.textContent = state.typingVisibleText;
    refs.messageText.classList.toggle("is-typing", nextIndex < state.typingFullText.length);

    if (nextIndex >= state.typingFullText.length) {
      state.typingTimer = null;
      state.typingActive = false;
      renderRuntime();
      return;
    }

    scheduleRuntimeTypewriterTick(expectedKey);
  }, getTypewriterStepDelay(
    getSnapshotTextSpeed(getCurrentSnapshot()),
    state.typingVisibleText,
    state.typingFullText
  ));
}

function getNextTypewriterIndex(text, currentIndex) {
  const safeText = String(text ?? "");
  const safeIndex = Math.max(0, Math.min(Number(currentIndex) || 0, safeText.length));

  if (safeIndex >= safeText.length) {
    return safeText.length;
  }

  let nextIndex = getNextCodePointIndex(safeText, safeIndex);
  const currentChar = getCodePointAtIndex(safeText, safeIndex);
  nextIndex = includeTypewriterLeadingFollower(safeText, safeIndex, nextIndex);

  if (/[A-Za-z0-9]/.test(currentChar)) {
    let grouped = 1;
    while (nextIndex < safeText.length && grouped < 3) {
      const nextChar = getCodePointAtIndex(safeText, nextIndex);
      if (!/[A-Za-z0-9]/.test(nextChar)) {
        break;
      }
      nextIndex = getNextCodePointIndex(safeText, nextIndex);
      grouped += 1;
    }
  }

  nextIndex = includeTypewriterTrailingClosers(safeText, nextIndex);

  while (nextIndex < safeText.length && /\s/.test(getCodePointAtIndex(safeText, nextIndex))) {
    nextIndex = getNextCodePointIndex(safeText, nextIndex);
  }

  return nextIndex;
}

function includeTypewriterLeadingFollower(text, currentIndex, index) {
  const safeText = String(text ?? "");
  const currentChar = getCodePointAtIndex(safeText, currentIndex);
  let nextIndex = Math.max(0, Math.min(Number(index) || 0, safeText.length));

  if (!TYPEWRITER_LEADING_OPENERS.includes(currentChar)) {
    return nextIndex;
  }

  while (nextIndex < safeText.length && TYPEWRITER_LEADING_OPENERS.includes(getCodePointAtIndex(safeText, nextIndex))) {
    nextIndex = getNextCodePointIndex(safeText, nextIndex);
  }

  return nextIndex < safeText.length ? getNextCodePointIndex(safeText, nextIndex) : nextIndex;
}

function includeTypewriterTrailingClosers(text, index) {
  const safeText = String(text ?? "");
  let nextIndex = Math.max(0, Math.min(Number(index) || 0, safeText.length));
  while (nextIndex < safeText.length && TYPEWRITER_TRAILING_CLOSERS.includes(getCodePointAtIndex(safeText, nextIndex))) {
    nextIndex = getNextUnicodeScalarIndex(safeText, nextIndex);
  }
  return nextIndex;
}

function getNextCodePointIndex(text, index) {
  const safeText = String(text ?? "");
  const safeIndex = Math.max(0, Math.min(Number(index) || 0, safeText.length));
  if (safeIndex >= safeText.length) {
    return safeText.length;
  }
  if (typewriterGraphemeSegmenter) {
    for (const segment of typewriterGraphemeSegmenter.segment(safeText)) {
      const segmentEnd = segment.index + segment.segment.length;
      if (safeIndex >= segment.index && safeIndex < segmentEnd) {
        return segmentEnd;
      }
    }
  }
  return getNextTypewriterClusterIndex(safeText, safeIndex);
}

function getNextUnicodeScalarIndex(text, index) {
  const safeText = String(text ?? "");
  const safeIndex = Math.max(0, Math.min(Number(index) || 0, safeText.length));
  if (safeIndex >= safeText.length) {
    return safeText.length;
  }
  const codePoint = safeText.codePointAt(safeIndex);
  return safeIndex + (codePoint && codePoint > 0xffff ? 2 : 1);
}

function getCodePointAtIndex(text, index) {
  const safeText = String(text ?? "");
  const safeIndex = Math.max(0, Math.min(Number(index) || 0, safeText.length));
  return safeText.slice(safeIndex, getNextUnicodeScalarIndex(safeText, safeIndex));
}

function getTypewriterCodePointAtIndex(text, index) {
  return String(text ?? "").codePointAt(index) ?? 0;
}

function isRegionalIndicatorSymbol(text, index) {
  const codePoint = getTypewriterCodePointAtIndex(text, index);
  return codePoint >= 0x1f1e6 && codePoint <= 0x1f1ff;
}

function isTypewriterGraphemeExtension(text, index) {
  const codePoint = getTypewriterCodePointAtIndex(text, index);
  return (
    (codePoint >= 0x0300 && codePoint <= 0x036f) ||
    (codePoint >= 0x1ab0 && codePoint <= 0x1aff) ||
    (codePoint >= 0x1dc0 && codePoint <= 0x1dff) ||
    (codePoint >= 0x20d0 && codePoint <= 0x20ff) ||
    (codePoint >= 0xfe00 && codePoint <= 0xfe0f) ||
    (codePoint >= 0xe0100 && codePoint <= 0xe01ef) ||
    (codePoint >= 0x1f3fb && codePoint <= 0x1f3ff)
  );
}

function getNextTypewriterClusterIndex(text, index) {
  const safeText = String(text ?? "");
  const safeIndex = Math.max(0, Math.min(Number(index) || 0, safeText.length));
  if (safeIndex >= safeText.length) {
    return safeText.length;
  }

  let nextIndex = getNextUnicodeScalarIndex(safeText, safeIndex);

  if (isRegionalIndicatorSymbol(safeText, safeIndex) && isRegionalIndicatorSymbol(safeText, nextIndex)) {
    return getNextUnicodeScalarIndex(safeText, nextIndex);
  }

  while (nextIndex < safeText.length) {
    const previousChar = getCodePointAtIndex(safeText, Math.max(0, nextIndex - 1));
    const currentChar = getCodePointAtIndex(safeText, nextIndex);

    if (isTypewriterGraphemeExtension(safeText, nextIndex) || previousChar === "\u200d") {
      nextIndex = getNextUnicodeScalarIndex(safeText, nextIndex);
      continue;
    }

    if (currentChar === "\u200d") {
      nextIndex = getNextUnicodeScalarIndex(safeText, getNextUnicodeScalarIndex(safeText, nextIndex));
      continue;
    }

    break;
  }

  return nextIndex;
}

function getTypewriterPunctuationPause(text, fullText = "") {
  const anchorText = getTypewriterPauseAnchorText(text);
  const anchorChar = Array.from(anchorText).at(-1) ?? "";
  if (/(\.{3,}|…+)$/.test(anchorText)) {
    return 220;
  }
  if (anchorChar === "." && isTypewriterInlinePeriod(anchorText, fullText)) {
    return 0;
  }
  if (anchorChar === "." && isTypewriterAbbreviationPeriod(anchorText, fullText)) {
    return 0;
  }
  if (/[。！？!?.]/.test(anchorChar)) {
    return 260;
  }
  if (/[………。—-]/.test(anchorChar)) {
    return 220;
  }
  if (/[，、；;：:,]/.test(anchorChar)) {
    return 140;
  }
  return 0;
}

function getTypewriterPauseAnchorText(text) {
  const chars = Array.from(String(text ?? "").trimEnd());
  while (chars.length > 1 && TYPEWRITER_TRAILING_CLOSERS.includes(chars.at(-1))) {
    chars.pop();
  }
  return chars.join("");
}

function getTypewriterPauseAnchorChar(text) {
  return Array.from(getTypewriterPauseAnchorText(text)).at(-1) ?? "";
}

function isTypewriterInlinePeriod(anchorText, fullText = "") {
  const safeAnchorText = String(anchorText ?? "");
  const safeFullText = String(fullText ?? "");
  const previousChar = Array.from(safeAnchorText).at(-2) ?? "";
  const nextChar = safeFullText.slice(safeAnchorText.length, safeAnchorText.length + 1);
  return /[A-Za-z0-9]/.test(previousChar) && /[A-Za-z0-9]/.test(nextChar);
}

function isTypewriterAbbreviationPeriod(anchorText, fullText = "") {
  const safeAnchorText = String(anchorText ?? "");
  const safeFullText = String(fullText ?? "");
  const token = (safeAnchorText.match(/([A-Za-z](?:[A-Za-z]|\.)*)\.$/)?.[1] ?? "").toLowerCase();
  const nextChar = safeFullText.slice(safeAnchorText.length, safeAnchorText.length + 1);
  return TYPEWRITER_PERIOD_ABBREVIATIONS.has(token) && /\s/.test(nextChar);
}

function getProjectPlaybackDefaults(project = data.project) {
  return buildProjectPlaybackDefaults(project, getDefaultRuntimeLanguage(), {
    getSafeLanguage: getSafeRuntimeLanguage,
  });
}

function getProjectFormalSaveSlotCount(project = data.project) {
  return getProjectFormalSaveSlotCountBase(project);
}

function getSafeProjectDialogBoxPreset(value) {
  return value === "custom" || Object.hasOwn(PROJECT_DIALOG_BOX_PRESETS, value)
    ? value
    : DEFAULT_PROJECT_DIALOG_BOX_CONFIG.preset;
}

function getSafeProjectDialogBoxShape(value) {
  return value === "square" || value === "capsule" || value === "rounded"
    ? value
    : DEFAULT_PROJECT_DIALOG_BOX_CONFIG.shape;
}

function getSafeProjectDialogBoxAnchor(value) {
  return ["bottom", "center", "top", "free"].includes(value) ? value : DEFAULT_PROJECT_DIALOG_BOX_CONFIG.anchor;
}

function getProjectDialogBoxPresetConfig(preset) {
  const safePreset = getSafeProjectDialogBoxPreset(preset);
  return {
    ...DEFAULT_PROJECT_DIALOG_BOX_CONFIG,
    ...(PROJECT_DIALOG_BOX_PRESETS[safePreset] ?? {}),
    preset: safePreset,
  };
}

function getProjectDialogBoxConfig(project = data.project) {
  const source = project?.dialogBoxConfig ?? {};
  const base = getProjectDialogBoxPresetConfig(source.preset);
  return {
    ...base,
    preset: getSafeProjectDialogBoxPreset(source.preset ?? base.preset),
    shape: getSafeProjectDialogBoxShape(source.shape ?? base.shape),
    widthPercent: clamp(getSafeNumber(source.widthPercent, base.widthPercent), 55, 100),
    minHeight: clamp(getSafeNumber(source.minHeight, base.minHeight), 96, 320),
    paddingX: clamp(getSafeNumber(source.paddingX, base.paddingX), 8, 72),
    paddingY: clamp(getSafeNumber(source.paddingY, base.paddingY), 6, 48),
    backgroundColor: getSafeParticleColor(source.backgroundColor, base.backgroundColor),
    backgroundOpacity: clamp(getSafeNumber(source.backgroundOpacity, base.backgroundOpacity), 0, 100),
    borderColor: getSafeParticleColor(source.borderColor, base.borderColor),
    borderOpacity: clamp(getSafeNumber(source.borderOpacity, base.borderOpacity), 0, 100),
    textColor: getSafeParticleColor(source.textColor, base.textColor),
    speakerColor: getSafeParticleColor(source.speakerColor, base.speakerColor),
    hintColor: getSafeParticleColor(source.hintColor, base.hintColor),
    blurStrength: clamp(getSafeNumber(source.blurStrength, base.blurStrength), 0, 24),
    borderWidth: clamp(getSafeNumber(source.borderWidth, base.borderWidth), 0, 4),
    shadowStrength: clamp(getSafeNumber(source.shadowStrength, base.shadowStrength), 0, 48),
    panelAssetId: String(source.panelAssetId ?? "").trim(),
    panelAssetOpacity: clamp(getSafeNumber(source.panelAssetOpacity, base.panelAssetOpacity), 0, 100),
    panelAssetFit: source.panelAssetFit === "contain" ? "contain" : "cover",
    anchor: getSafeProjectDialogBoxAnchor(source.anchor ?? base.anchor),
    offsetXPercent: clamp(getSafeNumber(source.offsetXPercent, base.offsetXPercent), -35, 35),
    offsetYPercent: clamp(getSafeNumber(source.offsetYPercent, base.offsetYPercent), -35, 35),
  };
}

function getSafeProjectGameUiPreset(value) {
  return value === "custom" || Object.hasOwn(PROJECT_GAME_UI_PRESETS, value)
    ? value
    : DEFAULT_PROJECT_GAME_UI_CONFIG.preset;
}

function getSafeProjectGameUiLayoutPreset(value) {
  return ["balanced", "cinematic", "compact", "minimal", "custom"].includes(value)
    ? value
    : DEFAULT_PROJECT_GAME_UI_CONFIG.layoutPreset;
}

function getSafeProjectGameUiTitleLayout(value) {
  return ["center", "left", "poster"].includes(value) ? value : DEFAULT_PROJECT_GAME_UI_CONFIG.titleLayout;
}

function getSafeProjectGameUiFontStyle(value) {
  return ["modern", "serif", "rounded"].includes(value) ? value : DEFAULT_PROJECT_GAME_UI_CONFIG.fontStyle;
}

function getSafeProjectGameUiSurfaceStyle(value) {
  return ["glass", "solid", "minimal"].includes(value) ? value : DEFAULT_PROJECT_GAME_UI_CONFIG.surfaceStyle;
}

function getSafeProjectGameUiBrandMode(value) {
  return ["project", "engine", "hidden"].includes(value) ? value : DEFAULT_PROJECT_GAME_UI_CONFIG.brandMode;
}

function getSafeProjectGameUiSidePanelMode(value) {
  return ["full", "compact", "hidden"].includes(value) ? value : DEFAULT_PROJECT_GAME_UI_CONFIG.sidePanelMode;
}

function getSafeProjectGameUiSidePanelPosition(value) {
  return ["right", "left"].includes(value) ? value : DEFAULT_PROJECT_GAME_UI_CONFIG.sidePanelPosition;
}

function getSafeProjectGameUiTopbarPosition(value) {
  return ["top", "bottom", "hidden"].includes(value) ? value : DEFAULT_PROJECT_GAME_UI_CONFIG.topbarPosition;
}

function getSafeProjectGameUiHudPosition(value) {
  return ["top", "top-left", "top-right", "bottom-left", "bottom-right", "hidden"].includes(value)
    ? value
    : DEFAULT_PROJECT_GAME_UI_CONFIG.hudPosition;
}

function getSafeProjectGameUiTitleCardAnchor(value) {
  return ["center", "left", "right", "top", "bottom", "free"].includes(value)
    ? value
    : DEFAULT_PROJECT_GAME_UI_CONFIG.titleCardAnchor;
}

function getSafeGameUiFrameSlice(value, fallback = { top: 18, right: 18, bottom: 18, left: 18 }) {
  const source = value && typeof value === "object" ? value : {};
  return {
    top: clamp(getSafeNumber(source.top, fallback.top), 0, 96),
    right: clamp(getSafeNumber(source.right, fallback.right), 0, 96),
    bottom: clamp(getSafeNumber(source.bottom, fallback.bottom), 0, 96),
    left: clamp(getSafeNumber(source.left, fallback.left), 0, 96),
  };
}

function getProjectGameUiPresetConfig(preset) {
  const safePreset = getSafeProjectGameUiPreset(preset);
  return {
    ...DEFAULT_PROJECT_GAME_UI_CONFIG,
    ...(PROJECT_GAME_UI_PRESETS[safePreset] ?? {}),
    preset: safePreset,
  };
}

function getProjectGameUiConfig(project = data.project) {
  const source = project?.gameUiConfig ?? {};
  const base = getProjectGameUiPresetConfig(source.preset);
  return {
    ...base,
    preset: getSafeProjectGameUiPreset(source.preset ?? base.preset),
    layoutPreset: getSafeProjectGameUiLayoutPreset(source.layoutPreset ?? base.layoutPreset),
    titleLayout: getSafeProjectGameUiTitleLayout(source.titleLayout ?? base.titleLayout),
    fontStyle: getSafeProjectGameUiFontStyle(source.fontStyle ?? base.fontStyle),
    surfaceStyle: getSafeProjectGameUiSurfaceStyle(source.surfaceStyle ?? base.surfaceStyle),
    brandMode: getSafeProjectGameUiBrandMode(source.brandMode ?? base.brandMode),
    sidePanelMode: getSafeProjectGameUiSidePanelMode(source.sidePanelMode ?? base.sidePanelMode),
    sidePanelPosition: getSafeProjectGameUiSidePanelPosition(source.sidePanelPosition ?? base.sidePanelPosition),
    topbarPosition: getSafeProjectGameUiTopbarPosition(source.topbarPosition ?? base.topbarPosition),
    hudPosition: getSafeProjectGameUiHudPosition(source.hudPosition ?? base.hudPosition),
    titleCardAnchor: getSafeProjectGameUiTitleCardAnchor(source.titleCardAnchor ?? base.titleCardAnchor),
    titleCardOffsetXPercent: clamp(getSafeNumber(source.titleCardOffsetXPercent, base.titleCardOffsetXPercent), -35, 35),
    titleCardOffsetYPercent: clamp(getSafeNumber(source.titleCardOffsetYPercent, base.titleCardOffsetYPercent), -35, 35),
    layoutGap: clamp(getSafeNumber(source.layoutGap, base.layoutGap), 8, 48),
    sidePanelWidth: clamp(getSafeNumber(source.sidePanelWidth, base.sidePanelWidth), 240, 460),
    backgroundColor: getSafeParticleColor(source.backgroundColor, base.backgroundColor),
    backgroundAccentColor: getSafeParticleColor(source.backgroundAccentColor, base.backgroundAccentColor),
    panelColor: getSafeParticleColor(source.panelColor, base.panelColor),
    panelOpacity: clamp(getSafeNumber(source.panelOpacity, base.panelOpacity), 35, 100),
    textColor: getSafeParticleColor(source.textColor, base.textColor),
    mutedTextColor: getSafeParticleColor(source.mutedTextColor, base.mutedTextColor),
    accentColor: getSafeParticleColor(source.accentColor, base.accentColor),
    accentAltColor: getSafeParticleColor(source.accentAltColor, base.accentAltColor),
    buttonTextColor: getSafeParticleColor(source.buttonTextColor, base.buttonTextColor),
    borderColor: getSafeParticleColor(source.borderColor, base.borderColor),
    borderOpacity: clamp(getSafeNumber(source.borderOpacity, base.borderOpacity), 0, 100),
    cornerRadius: clamp(getSafeNumber(source.cornerRadius, base.cornerRadius), 4, 42),
    backdropBlur: clamp(getSafeNumber(source.backdropBlur, base.backdropBlur), 0, 28),
    stageVignette: clamp(getSafeNumber(source.stageVignette, base.stageVignette), 0, 80),
    motionIntensity: clamp(getSafeNumber(source.motionIntensity, base.motionIntensity), 0, 100),
    titleBackgroundAssetId: String(source.titleBackgroundAssetId ?? "").trim(),
    titleBackgroundFit: source.titleBackgroundFit === "contain" ? "contain" : "cover",
    titleBackgroundOpacity: clamp(getSafeNumber(source.titleBackgroundOpacity, base.titleBackgroundOpacity), 0, 100),
    titleLogoAssetId: String(source.titleLogoAssetId ?? "").trim(),
    panelFrameAssetId: String(source.panelFrameAssetId ?? "").trim(),
    panelFrameOpacity: clamp(getSafeNumber(source.panelFrameOpacity, base.panelFrameOpacity), 0, 100),
    panelFrameSlice: getSafeGameUiFrameSlice(source.panelFrameSlice, base.panelFrameSlice),
    buttonFrameAssetId: String(source.buttonFrameAssetId ?? "").trim(),
    buttonHoverFrameAssetId: String(source.buttonHoverFrameAssetId ?? "").trim(),
    buttonPressedFrameAssetId: String(source.buttonPressedFrameAssetId ?? "").trim(),
    buttonDisabledFrameAssetId: String(source.buttonDisabledFrameAssetId ?? "").trim(),
    buttonFrameOpacity: clamp(getSafeNumber(source.buttonFrameOpacity, base.buttonFrameOpacity), 0, 100),
    buttonFrameSlice: getSafeGameUiFrameSlice(source.buttonFrameSlice, base.buttonFrameSlice),
    saveSlotFrameAssetId: String(source.saveSlotFrameAssetId ?? "").trim(),
    systemPanelFrameAssetId: String(source.systemPanelFrameAssetId ?? "").trim(),
    uiOverlayAssetId: String(source.uiOverlayAssetId ?? "").trim(),
    uiOverlayOpacity: clamp(getSafeNumber(source.uiOverlayOpacity, base.uiOverlayOpacity), 0, 100),
  };
}

function cssUrlFromAssetId(assetId) {
  const assetUrl = getAssetUrl(assetId);
  return assetUrl ? `url("${assetUrl.replace(/"/g, "%22")}")` : "none";
}

function cssImageWithFallback(assetId, fallbackImage = "none") {
  const image = cssUrlFromAssetId(assetId);
  return image === "none" ? fallbackImage : image;
}

function cssFrameSliceValue(slice) {
  return `${slice.top} ${slice.right} ${slice.bottom} ${slice.left} fill`;
}

function cssFrameWidthValue(slice) {
  return `${slice.top}px ${slice.right}px ${slice.bottom}px ${slice.left}px`;
}

function applyProjectGameUiSkin(project = data.project) {
  const config = getProjectGameUiConfig(project);
  const root = document.documentElement;
  const panel = toRgbaString(config.panelColor, config.panelOpacity);
  const panelStrong = toRgbaString(config.panelColor, Math.min(100, config.panelOpacity + 8));
  const border = toRgbaString(config.borderColor, config.borderOpacity);
  const lowMotion = config.motionIntensity <= 15 ? "0" : "1";
  const panelFrameImage = cssUrlFromAssetId(config.panelFrameAssetId);
  const buttonFrameImage = cssUrlFromAssetId(config.buttonFrameAssetId);

  root.dataset.gameUiPreset = config.preset;
  root.dataset.gameUiLayout = config.layoutPreset;
  root.dataset.gameUiTitleLayout = config.titleLayout;
  root.dataset.gameUiFont = config.fontStyle;
  root.dataset.gameUiSurface = config.surfaceStyle;
  root.dataset.gameUiBrand = config.brandMode;
  root.dataset.gameUiSidePanel = config.sidePanelMode;
  root.dataset.gameUiSidePosition = config.sidePanelPosition;
  root.dataset.gameUiTopbarPosition = config.topbarPosition;
  root.dataset.gameUiHudPosition = config.hudPosition;
  root.dataset.gameUiTitleAnchor = config.titleCardAnchor;
  root.dataset.gameUiMotion = lowMotion === "0" ? "low" : "normal";
  root.style.setProperty("--bg", config.backgroundColor);
  root.style.setProperty("--panel", panel);
  root.style.setProperty("--panel-strong", panelStrong);
  root.style.setProperty("--line", border);
  root.style.setProperty("--ink", config.textColor);
  root.style.setProperty("--muted", config.mutedTextColor);
  root.style.setProperty("--brand", config.accentColor);
  root.style.setProperty("--brand-deep", config.accentAltColor);
  root.style.setProperty("--accent", toRgbaString(config.accentColor, 18));
  root.style.setProperty("--game-ui-bg", config.backgroundColor);
  root.style.setProperty("--game-ui-bg-accent", config.backgroundAccentColor);
  root.style.setProperty("--game-ui-panel", panel);
  root.style.setProperty("--game-ui-panel-strong", panelStrong);
  root.style.setProperty("--game-ui-line", border);
  root.style.setProperty("--game-ui-text", config.textColor);
  root.style.setProperty("--game-ui-muted", config.mutedTextColor);
  root.style.setProperty("--game-ui-accent", config.accentColor);
  root.style.setProperty("--game-ui-accent-alt", config.accentAltColor);
  root.style.setProperty("--game-ui-button-text", config.buttonTextColor);
  root.style.setProperty("--game-ui-radius", `${config.cornerRadius}px`);
  root.style.setProperty("--game-ui-radius-large", `${Math.min(42, config.cornerRadius + 10)}px`);
  root.style.setProperty("--game-ui-blur", `${config.backdropBlur}px`);
  root.style.setProperty("--game-ui-stage-vignette", (config.stageVignette / 100).toFixed(2));
  root.style.setProperty("--game-ui-motion-enabled", lowMotion);
  root.style.setProperty("--game-ui-layout-gap", `${config.layoutGap}px`);
  root.style.setProperty("--game-ui-side-panel-width", `${config.sidePanelWidth}px`);
  root.style.setProperty("--game-ui-title-card-offset-x", `${config.titleCardOffsetXPercent}%`);
  root.style.setProperty("--game-ui-title-card-offset-y", `${config.titleCardOffsetYPercent}%`);
  root.style.setProperty("--game-ui-title-bg-image", cssUrlFromAssetId(config.titleBackgroundAssetId));
  root.style.setProperty("--game-ui-title-bg-fit", config.titleBackgroundFit);
  root.style.setProperty("--game-ui-title-bg-opacity", (config.titleBackgroundOpacity / 100).toFixed(2));
  root.style.setProperty("--game-ui-panel-frame-image", panelFrameImage);
  root.style.setProperty("--game-ui-panel-frame-opacity", (config.panelFrameOpacity / 100).toFixed(2));
  root.style.setProperty("--game-ui-panel-frame-slice", cssFrameSliceValue(config.panelFrameSlice));
  root.style.setProperty("--game-ui-panel-frame-width", cssFrameWidthValue(config.panelFrameSlice));
  root.style.setProperty("--game-ui-button-frame-image", buttonFrameImage);
  root.style.setProperty("--game-ui-button-hover-frame-image", cssImageWithFallback(config.buttonHoverFrameAssetId, buttonFrameImage));
  root.style.setProperty("--game-ui-button-pressed-frame-image", cssImageWithFallback(config.buttonPressedFrameAssetId, buttonFrameImage));
  root.style.setProperty("--game-ui-button-disabled-frame-image", cssImageWithFallback(config.buttonDisabledFrameAssetId, buttonFrameImage));
  root.style.setProperty("--game-ui-button-frame-opacity", (config.buttonFrameOpacity / 100).toFixed(2));
  root.style.setProperty("--game-ui-button-frame-slice", cssFrameSliceValue(config.buttonFrameSlice));
  root.style.setProperty("--game-ui-button-frame-width", cssFrameWidthValue(config.buttonFrameSlice));
  root.style.setProperty("--game-ui-save-slot-frame-image", cssImageWithFallback(config.saveSlotFrameAssetId, panelFrameImage));
  root.style.setProperty("--game-ui-system-panel-frame-image", cssImageWithFallback(config.systemPanelFrameAssetId, panelFrameImage));
  root.style.setProperty("--game-ui-overlay-image", cssUrlFromAssetId(config.uiOverlayAssetId));
  root.style.setProperty("--game-ui-overlay-opacity", (config.uiOverlayOpacity / 100).toFixed(2));

  const projectTitle = data.project?.title ?? "Canvasia Engine";
  const topEyebrow = document.querySelector(".player-brand-copy .eyebrow");
  const startEyebrow = document.querySelector(".start-card > .eyebrow");
  const startBrandTitle = document.querySelector(".start-brand-copy strong");
  const startBrandSubtitle = document.querySelector(".start-brand-copy span");
  const logoUrl = getAssetUrl(config.titleLogoAssetId);
  document.querySelectorAll(".player-brand-logo, .start-brand-logo-image").forEach((image) => {
    if (logoUrl) {
      image.src = logoUrl;
    }
  });

  if (config.brandMode === "project") {
    if (topEyebrow) {
      topEyebrow.textContent = `${projectTitle} · Runtime`;
    }
    if (startEyebrow) {
      startEyebrow.textContent = `${projectTitle} 导出试玩包`;
    }
    if (startBrandTitle) {
      startBrandTitle.textContent = projectTitle;
    }
    if (startBrandSubtitle) {
      startBrandSubtitle.textContent = "Visual Novel Runtime";
    }
  }
}

function getDialogThemeBaseColors(theme) {
  if (theme === "moonlight") {
    return {
      backgroundColor: "#17233a",
      backgroundOpacity: 92,
      borderColor: "#a2c1ff",
      borderOpacity: 24,
      textColor: "#f4f7ff",
      speakerColor: "#ffffff",
      hintColor: "#d7e3ff",
    };
  }
  if (theme === "paper") {
    return {
      backgroundColor: "#fff7e8",
      backgroundOpacity: 95,
      borderColor: "#b08659",
      borderOpacity: 28,
      textColor: "#4a2f1d",
      speakerColor: "#7f5438",
      hintColor: "#7f6a54",
    };
  }
  if (theme === "transparent") {
    return {
      backgroundColor: "#08111b",
      backgroundOpacity: 0,
      borderColor: "#7fe6ff",
      borderOpacity: 0,
      textColor: "#f4f8ff",
      speakerColor: "#ffffff",
      hintColor: "#d0daf0",
    };
  }
  return {
    backgroundColor: "#fffaf5",
    backgroundOpacity: 92,
    borderColor: "#8f6548",
    borderOpacity: 18,
    textColor: "#332117",
    speakerColor: "#7f5438",
    hintColor: "#6d5b4f",
  };
}

function toRgbaString(hexColor, opacityPercent) {
  const safeHex = getSafeParticleColor(hexColor, "#ffffff").slice(1);
  const red = Number.parseInt(safeHex.slice(0, 2), 16);
  const green = Number.parseInt(safeHex.slice(2, 4), 16);
  const blue = Number.parseInt(safeHex.slice(4, 6), 16);
  const alpha = clamp(getSafeNumber(opacityPercent, 100), 0, 100) / 100;
  return `rgba(${red}, ${green}, ${blue}, ${alpha.toFixed(2)})`;
}

function getDialogShapeRadius(shape, fallbackRadius = 18) {
  const safeShape = getSafeProjectDialogBoxShape(shape);
  if (safeShape === "square") {
    return 6;
  }
  if (safeShape === "capsule") {
    return 999;
  }
  return clamp(getSafeNumber(fallbackRadius, 18), 8, 42);
}

function getDialogPanelAssetUrl(assetId) {
  const safeId = String(assetId ?? "").trim();
  if (!safeId) {
    return "";
  }
  const assetUrl = getAssetUrl(safeId);
  return typeof assetUrl === "string" ? assetUrl : "";
}

function buildDialogBoxPresentation(theme, project = data.project) {
  const safeTheme = getSafeDialogTheme(theme);
  if (safeTheme !== "project") {
    const base = getDialogThemeBaseColors(safeTheme);
    const blurStrength = safeTheme === "paper" ? 4 : safeTheme === "transparent" ? 0 : 10;
    const borderWidth = safeTheme === "transparent" ? 0 : 1;
    const shadowStrength = safeTheme === "transparent" ? 0 : safeTheme === "moonlight" ? 32 : 18;
    return {
      theme: safeTheme,
      assetUrl: "",
      style: [
        `--dialog-box-width: 76%;`,
        `--dialog-box-min-height: 148px;`,
        `--dialog-box-padding-x: 18px;`,
        `--dialog-box-padding-y: 14px;`,
        `--dialog-box-radius: ${getDialogShapeRadius("rounded", 18)}px;`,
        `--dialog-box-bg: ${toRgbaString(base.backgroundColor, base.backgroundOpacity)};`,
        `--dialog-box-border: ${toRgbaString(base.borderColor, base.borderOpacity)};`,
        `--dialog-box-border-width: ${borderWidth}px;`,
        `--dialog-box-text: ${base.textColor};`,
        `--dialog-box-speaker: ${base.speakerColor};`,
        `--dialog-box-hint: ${base.hintColor};`,
        `--dialog-box-blur: ${blurStrength}px;`,
        `--dialog-box-shadow-strength: ${shadowStrength};`,
        `--dialog-box-art-opacity: 0;`,
        `--dialog-box-art-fit: cover;`,
        `--dialog-box-art-image: none;`,
        `--dialog-box-offset-x: 0%;`,
        `--dialog-box-offset-y: 0%;`,
      ].join(" "),
    };
  }

  const config = getProjectDialogBoxConfig(project);
  const assetUrl = getDialogPanelAssetUrl(config.panelAssetId);
  return {
    theme: "project",
    assetUrl,
    style: [
      `--dialog-box-width: ${config.widthPercent}%;`,
      `--dialog-box-min-height: ${config.minHeight}px;`,
      `--dialog-box-padding-x: ${config.paddingX}px;`,
      `--dialog-box-padding-y: ${config.paddingY}px;`,
      `--dialog-box-radius: ${getDialogShapeRadius(config.shape, config.shape === "rounded" ? 22 : 18)}px;`,
      `--dialog-box-bg: ${toRgbaString(config.backgroundColor, config.backgroundOpacity)};`,
      `--dialog-box-border: ${toRgbaString(config.borderColor, config.borderOpacity)};`,
      `--dialog-box-border-width: ${config.borderWidth}px;`,
      `--dialog-box-text: ${config.textColor};`,
      `--dialog-box-speaker: ${config.speakerColor};`,
      `--dialog-box-hint: ${config.hintColor};`,
      `--dialog-box-blur: ${config.blurStrength}px;`,
      `--dialog-box-shadow-strength: ${config.shadowStrength};`,
      `--dialog-box-art-opacity: ${(config.panelAssetOpacity / 100).toFixed(2)};`,
      `--dialog-box-art-fit: ${config.panelAssetFit};`,
      `--dialog-box-offset-x: ${config.offsetXPercent}%;`,
      `--dialog-box-offset-y: ${config.offsetYPercent}%;`,
      assetUrl ? `--dialog-box-art-image: url("${assetUrl.replace(/"/g, "%22")}");` : `--dialog-box-art-image: none;`,
    ].join(" "),
  };
}

function getBrowserStorage() {
  try {
    return window.localStorage;
  } catch (error) {
    return null;
  }
}

function getProjectStorageScope() {
  const title = String(data.project.title ?? "canvasia-project")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9\u4e00-\u9fa5_-]+/g, "-")
    .replace(/-+/g, "-")
    .slice(0, 72);

  return title || "project";
}

function getPlaybackStorageKey() {
  return `canvasia-engine:player-preview:${getProjectStorageScope()}`;
}

function sanitizePlaybackSettings(source = {}) {
  return sanitizePlaybackSettingsBase(source, {
    getSafeLanguage: getSafeRuntimeLanguage,
  });
}

function getSupportedRuntimeLanguages() {
  return data.i18n?.supportedLanguages?.length ? data.i18n.supportedLanguages : [DEFAULT_RUNTIME_LANGUAGE];
}

function getDefaultRuntimeLanguage() {
  return getSafeRuntimeLanguage(data.i18n?.defaultLanguage ?? DEFAULT_RUNTIME_LANGUAGE);
}

function getSafeRuntimeLanguage(language) {
  const supportedLanguages = getSupportedRuntimeLanguages();
  const normalized = normalizeLanguageCode(language, "");
  if (normalized && supportedLanguages.includes(normalized)) {
    return normalized;
  }
  return supportedLanguages.includes(data.i18n?.defaultLanguage)
    ? data.i18n.defaultLanguage
    : supportedLanguages[0] ?? DEFAULT_RUNTIME_LANGUAGE;
}

function getRuntimeLanguageLabel(language) {
  const safeLanguage = getSafeRuntimeLanguage(language);
  return data.i18n?.languageLabels?.[safeLanguage] ?? RUNTIME_LANGUAGE_LABELS[safeLanguage] ?? safeLanguage;
}

function getCurrentRuntimeLanguage() {
  return getSafeRuntimeLanguage(state.playback?.language || getDefaultRuntimeLanguage());
}

function getLocalizedValue(source, key, fallback = "") {
  const safeSource = source && typeof source === "object" ? source : {};
  const translations = safeSource[`${key}Translations`];
  const language = getCurrentRuntimeLanguage();
  if (translations && typeof translations === "object") {
    for (const candidate of [language, data.i18n?.fallbackLanguage, data.i18n?.defaultLanguage, DEFAULT_RUNTIME_LANGUAGE]) {
      const text = String(translations[candidate] ?? "").trim();
      if (text) {
        return text;
      }
    }
  }
  return String(safeSource[key] ?? fallback ?? "");
}

function getBlockText(block) {
  return getLocalizedValue(block, "text");
}

function getChoiceText(option) {
  return getLocalizedValue(option, "text", "未命名选项");
}

function getSceneName(scene, fallback = "") {
  return getLocalizedValue(scene, "name", fallback || scene?.id || "未知场景");
}

function getChapterName(chapterId, fallback = "") {
  const chapter = data.chapters.find((item) => item.chapterId === chapterId);
  return getLocalizedValue(chapter, "name", fallback || chapterId || "未命名章节");
}

function getSceneChapterName(scene) {
  return getChapterName(scene?.chapterId, scene?.chapterName || scene?.chapterId);
}

function loadStoredPlaybackSettings() {
  const storage = getBrowserStorage();
  const projectDefaults = getProjectPlaybackDefaults();

  if (!storage) {
    return projectDefaults;
  }

  try {
    const raw = storage.getItem(getPlaybackStorageKey());

    if (!raw) {
      return projectDefaults;
    }

    return sanitizePlaybackSettings({
      ...projectDefaults,
      ...JSON.parse(raw),
    });
  } catch (error) {
    return projectDefaults;
  }
}

function persistPlaybackSettings() {
  const storage = getBrowserStorage();

  if (!storage) {
    return;
  }

  try {
    storage.setItem(getPlaybackStorageKey(), JSON.stringify(sanitizePlaybackSettings(state.playback)));
  } catch (error) {
    // Ignore storage write failures so the exported player still works in stricter browsers.
  }
}

function getAutoResumeStorageKey() {
  return `canvasia-engine:player-autoresume:${getProjectStorageScope()}`;
}

function getReadHistoryStorageKey() {
  return `canvasia-engine:player-read:${getProjectStorageScope()}`;
}

function getSaveSlotStorageKey() {
  return `canvasia-engine:player-saves:${getProjectStorageScope()}`;
}

function getQuickSaveStorageKey() {
  return `canvasia-engine:player-quicksave:${getProjectStorageScope()}`;
}

function getPlayerProfileStorageKey() {
  return `canvasia-engine:player-profile:${getProjectStorageScope()}`;
}

function getAchievementProgressStorageKey() {
  return `canvasia-engine:player-achievements:${getProjectStorageScope()}`;
}

function getChapterReplayStorageKey() {
  return `canvasia-engine:player-chapters:${getProjectStorageScope()}`;
}

function getLocationArchiveStorageKey() {
  return `canvasia-engine:player-locations:${getProjectStorageScope()}`;
}

function getNarrationArchiveStorageKey() {
  return `canvasia-engine:player-narrations:${getProjectStorageScope()}`;
}

function getRelationArchiveStorageKey() {
  return `canvasia-engine:player-relations:${getProjectStorageScope()}`;
}

function getVoiceReplayStorageKey() {
  return `canvasia-engine:player-voice-replay:${getProjectStorageScope()}`;
}

function buildVoiceReplayEntryId(sceneId, blockId, blockIndex) {
  const safeSceneId = typeof sceneId === "string" ? sceneId : "scene";
  const safeBlockId = blockId == null ? "block" : String(blockId);
  const safeBlockIndex = Number.isFinite(blockIndex) ? blockIndex : 0;
  return `${safeSceneId}:${safeBlockId}:${safeBlockIndex}`;
}

function getVoiceReplayEntries() {
  const entries = [];

  data.scenes.forEach((scene) => {
    (scene.blocks ?? []).forEach((block, blockIndex) => {
      if ((block.type !== "dialogue" && block.type !== "narration") || !block.voiceAssetId) {
        return;
      }

      const voiceAsset = data.assetsById.get(block.voiceAssetId);
      const voiceUrl = getAssetUrl(block.voiceAssetId);
      if (!voiceAsset || voiceAsset.type !== "voice" || !voiceUrl) {
        return;
      }

      entries.push({
        id: buildVoiceReplayEntryId(scene.id, block.id, blockIndex),
        sceneId: scene.id,
        sceneName: getSceneName(scene),
        chapterId: scene.chapterId,
        chapterName: getSceneChapterName(scene),
        blockId: block.id ?? null,
        blockIndex,
        blockType: block.type,
        text: getBlockText(block).trim(),
        speakerName: block.type === "dialogue" ? getCharacterName(block.speakerId) : "旁白",
        voiceAssetId: block.voiceAssetId,
        voiceVolume: getSafeVolumePercent(block.voiceVolume, 100),
        voiceName: voiceAsset.name || block.voiceAssetId,
        voiceUrl,
      });
    });
  });

  return entries;
}

function getVoiceReplayEntryMap() {
  return new Map(getVoiceReplayEntries().map((entry) => [entry.id, entry]));
}

function getSafeVoiceReplayId(entryId = null) {
  const entries = getVoiceReplayEntries();
  if (entries.length === 0) {
    return null;
  }

  if (entryId && entries.some((entry) => entry.id === entryId)) {
    return entryId;
  }

  const unlockedEntry = entries.find((entry) => state.voiceReplayProgress.has(entry.id));
  return unlockedEntry?.id ?? entries[0]?.id ?? null;
}

function sanitizeVoiceReplayProgressMap(source) {
  const validIds = new Set(getVoiceReplayEntries().map((entry) => entry.id));
  const entries = source && typeof source === "object" ? Object.entries(source) : [];

  return new Map(
    entries
      .filter(([entryId]) => validIds.has(entryId))
      .map(([entryId, payload]) => {
        if (typeof payload === "string") {
          return [
            entryId,
            {
              unlockedAt: payload,
              lastHeardAt: payload,
              heardCount: 1,
            },
          ];
        }

        const item = payload && typeof payload === "object" ? payload : {};
        return [
          entryId,
          {
            unlockedAt: typeof item.unlockedAt === "string" && item.unlockedAt.trim() ? item.unlockedAt : null,
            lastHeardAt: typeof item.lastHeardAt === "string" && item.lastHeardAt.trim() ? item.lastHeardAt : null,
            heardCount: Math.max(1, Math.round(Number(item.heardCount) || 1)),
          },
        ];
      })
      .filter(([, item]) => Boolean(item.unlockedAt))
  );
}

function getAchievementDefinitions() {
  const achievements = [];
  const choiceBlockCount = data.scenes.reduce(
    (count, scene) => count + ((scene.blocks ?? []).filter((block) => block.type === "choice").length || 0),
    0
  );
  const characters = getCharacterArchiveEntries();
  const galleryAssets = getGalleryAssets();
  const musicAssets = getMusicRoomAssets();
  const endingScenes = getEndingScenes();

  if (data.scenes.length > 0) {
    achievements.push({
      id: "first_start",
      name: "初次启程",
      category: "剧情里程碑",
      description: "第一次正式开始试玩这个项目。",
      requirement: "点击开始试玩 1 次",
      progressCurrent: state.achievementProgress.has("first_start") ? 1 : 0,
      progressTarget: 1,
    });
  }

  if (choiceBlockCount > 0) {
    achievements.push({
      id: "first_choice",
      name: "分岔路口",
      category: "剧情里程碑",
      description: "第一次在剧情里做出一个选项分支。",
      requirement: "做出 1 次选项选择",
      progressCurrent: state.achievementProgress.has("first_choice") ? 1 : 0,
      progressTarget: 1,
    });
  }

  if (characters.length > 0) {
    achievements.push(
      {
        id: "first_character",
        name: "初次相遇",
        category: "人物收集",
        description: "第一次在剧情里见到角色，人物档案馆开始亮起。",
        requirement: "解锁 1 位角色",
        progressCurrent: Math.min(state.characterArchive.size, 1),
        progressTarget: 1,
      },
      {
        id: "all_characters",
        name: "全员到齐",
        category: "人物收集",
        description: "把这个项目里的所有角色都收录进图鉴里。",
        requirement: `收录全部 ${characters.length} 位角色`,
        progressCurrent: Math.min(state.characterArchive.size, characters.length),
        progressTarget: characters.length,
      }
    );
  }

  if (galleryAssets.length > 0) {
    achievements.push(
      {
        id: "first_cg",
        name: "回想开幕",
        category: "EXTRA 收集",
        description: "第一次在剧情里解锁一张 CG。",
        requirement: "解锁 1 张 CG",
        progressCurrent: Math.min(state.extraUnlocks.cg.size, 1),
        progressTarget: 1,
      },
      {
        id: "all_cg",
        name: "回想收藏家",
        category: "EXTRA 收集",
        description: "把这个项目里的所有 CG 都解锁进回想馆。",
        requirement: `解锁全部 ${galleryAssets.length} 张 CG`,
        progressCurrent: Math.min(state.extraUnlocks.cg.size, galleryAssets.length),
        progressTarget: galleryAssets.length,
      }
    );
  }

  if (musicAssets.length > 0) {
    achievements.push(
      {
        id: "first_bgm",
        name: "旋律初响",
        category: "EXTRA 收集",
        description: "第一次在剧情里听到并解锁一首 BGM。",
        requirement: "解锁 1 首 BGM",
        progressCurrent: Math.min(state.extraUnlocks.bgm.size, 1),
        progressTarget: 1,
      },
      {
        id: "all_bgm",
        name: "全曲收藏",
        category: "EXTRA 收集",
        description: "把这个项目里的所有 BGM 都收录进音乐鉴赏。",
        requirement: `解锁全部 ${musicAssets.length} 首 BGM`,
        progressCurrent: Math.min(state.extraUnlocks.bgm.size, musicAssets.length),
        progressTarget: musicAssets.length,
      }
    );
  }

  if (endingScenes.length > 0) {
    achievements.push(
      {
        id: "first_ending",
        name: "终幕初见",
        category: "路线回收",
        description: "第一次真正抵达某条路线的结局。",
        requirement: "回收 1 个结局",
        progressCurrent: Math.min(state.endingProgress.unlocked.size, 1),
        progressTarget: 1,
      },
      {
        id: "all_endings",
        name: "全结局制霸",
        category: "路线回收",
        description: "把所有可回收结局都点亮进结局回收馆。",
        requirement: `回收全部 ${endingScenes.length} 个结局`,
        progressCurrent: Math.min(state.endingProgress.unlocked.size, endingScenes.length),
        progressTarget: endingScenes.length,
      }
    );
  }

  return achievements;
}

function getChapterReplayEntries() {
  return (data.chapters ?? []).map((chapter, index) => {
    const firstScene = (chapter.scenes ?? [])[0] ?? null;
    return {
      chapterId: chapter.chapterId,
      name: getLocalizedValue(chapter, "name", chapter.name || `章节 ${index + 1}`),
      order: index + 1,
      firstSceneId: firstScene?.id ?? "",
      firstSceneName: firstScene ? getSceneName(firstScene, "未设置开场场景") : "未设置开场场景",
      notes: firstScene?.notes ?? "",
      sceneCount: (chapter.scenes ?? []).length,
      previewBackgroundAssetId:
        (firstScene?.blocks ?? []).find((block) => block.type === "background" && block.assetId)?.assetId ?? "",
      previewSpeakerId:
        (firstScene?.blocks ?? []).find((block) => block.type === "dialogue" && block.speakerId)?.speakerId ?? "",
      previewText: getBlockText(
        (firstScene?.blocks ?? []).find((block) => block.type === "dialogue" || block.type === "narration")
      ),
    };
  });
}

function buildRelationshipArchiveId(leftCharacterId, rightCharacterId) {
  return [leftCharacterId, rightCharacterId].sort().join("__");
}

function buildNarrationArchiveEntryId(sceneId, blockId, blockIndex) {
  const safeSceneId = typeof sceneId === "string" ? sceneId : "scene";
  const safeBlockId = blockId == null ? "block" : String(blockId);
  const safeBlockIndex = Number.isFinite(blockIndex) ? blockIndex : 0;
  return `${safeSceneId}:${safeBlockId}:${safeBlockIndex}`;
}

function collectSceneEncounterCharacterIds(scene, maxBlockIndex = Number.POSITIVE_INFINITY) {
  const characterIds = [];
  const seenIds = new Set();

  (scene?.blocks ?? []).forEach((block, blockIndex) => {
    if (blockIndex > maxBlockIndex) {
      return;
    }

    const candidates = [];
    if (typeof block?.speakerId === "string" && block.speakerId.trim()) {
      candidates.push(block.speakerId);
    }
    if (typeof block?.characterId === "string" && block.characterId.trim()) {
      candidates.push(block.characterId);
    }

    candidates.forEach((characterId) => {
      if (!data.charactersById.has(characterId) || seenIds.has(characterId)) {
        return;
      }

      seenIds.add(characterId);
      characterIds.push(characterId);
    });
  });

  return characterIds;
}

function getRelationshipArchiveEntries() {
  const entries = [];
  const seenPairIds = new Set();

  data.scenes.forEach((scene) => {
    const sceneCharacterIds = collectSceneEncounterCharacterIds(scene);
    if (sceneCharacterIds.length < 2) {
      return;
    }

    for (let index = 0; index < sceneCharacterIds.length; index += 1) {
      for (let nextIndex = index + 1; nextIndex < sceneCharacterIds.length; nextIndex += 1) {
        const leftCharacterId = sceneCharacterIds[index];
        const rightCharacterId = sceneCharacterIds[nextIndex];
        const pairId = buildRelationshipArchiveId(leftCharacterId, rightCharacterId);
        if (seenPairIds.has(pairId)) {
          continue;
        }

        seenPairIds.add(pairId);
        const previewBackgroundAssetId =
          (scene.blocks ?? []).find((block) => block.type === "background" && block.assetId)?.assetId ?? "";

        entries.push({
          id: pairId,
          leftCharacterId,
          rightCharacterId,
          leftCharacterName: getCharacterName(leftCharacterId),
          rightCharacterName: getCharacterName(rightCharacterId),
          chapterId: scene.chapterId,
          chapterName: getSceneChapterName(scene),
          sceneId: scene.id,
          sceneName: getSceneName(scene),
          previewBackgroundAssetId,
          previewBackgroundUrl: getAssetUrl(previewBackgroundAssetId),
          previewText: getBlockText(
            (scene.blocks ?? []).find((block) => block.type === "dialogue" || block.type === "narration")
          ),
        });
      }
    }
  });

  return entries;
}

function getNarrationArchiveEntries() {
  const entries = [];

  data.scenes.forEach((scene) => {
    let currentBackgroundAssetId = null;

    (scene.blocks ?? []).forEach((block, blockIndex) => {
      if (block.type === "background" && block.assetId) {
        currentBackgroundAssetId = block.assetId;
      }

      if (block.type !== "narration") {
        return;
      }

      const text = getBlockText(block).trim();
      if (!text) {
        return;
      }

      entries.push({
        id: buildNarrationArchiveEntryId(scene.id, block.id, blockIndex),
        sceneId: scene.id,
        sceneName: getSceneName(scene),
        chapterId: scene.chapterId,
        chapterName: getSceneChapterName(scene),
        blockId: block.id ?? null,
        blockIndex,
        text,
        previewBackgroundAssetId: currentBackgroundAssetId,
        previewBackgroundUrl: getAssetUrl(currentBackgroundAssetId),
      });
    });
  });

  return entries;
}

function getLocationArchiveEntries() {
  const entries = [];
  const seenAssetIds = new Set();

  data.scenes.forEach((scene) => {
    (scene.blocks ?? []).forEach((block, blockIndex) => {
      if (block.type !== "background" || !block.assetId || seenAssetIds.has(block.assetId)) {
        return;
      }

      const asset = data.assetsById.get(block.assetId);
      if (!asset || asset.type !== "background") {
        return;
      }

      seenAssetIds.add(block.assetId);
      entries.push({
        id: asset.id,
        name: asset.name || asset.id,
        chapterId: scene.chapterId,
        chapterName: getSceneChapterName(scene),
        sceneId: scene.id,
        sceneName: getSceneName(scene),
        firstBlockIndex: blockIndex,
        tags: Array.isArray(asset.tags) ? asset.tags : [],
        imageUrl: getAssetUrl(asset.id),
      });
    });
  });

  return entries;
}

function sanitizeLocationArchiveProgressMap(source) {
  const validIds = new Set(getLocationArchiveEntries().map((entry) => entry.id));
  const entries = source && typeof source === "object" ? Object.entries(source) : [];

  return new Map(
    entries
      .filter(([entryId, unlockedAt]) => validIds.has(entryId) && typeof unlockedAt === "string" && unlockedAt.trim())
      .map(([entryId, unlockedAt]) => [entryId, unlockedAt])
  );
}

function sanitizeNarrationArchiveProgressMap(source) {
  const validIds = new Set(getNarrationArchiveEntries().map((entry) => entry.id));
  const entries = source && typeof source === "object" ? Object.entries(source) : [];

  return new Map(
    entries
      .filter(([entryId, unlockedAt]) => validIds.has(entryId) && typeof unlockedAt === "string" && unlockedAt.trim())
      .map(([entryId, unlockedAt]) => [entryId, unlockedAt])
  );
}

function sanitizeRelationArchiveProgressMap(source) {
  const validIds = new Set(getRelationshipArchiveEntries().map((entry) => entry.id));
  const entries = source && typeof source === "object" ? Object.entries(source) : [];

  return new Map(
    entries
      .filter(([entryId, unlockedAt]) => validIds.has(entryId) && typeof unlockedAt === "string" && unlockedAt.trim())
      .map(([entryId, unlockedAt]) => [entryId, unlockedAt])
  );
}

function sanitizePlayerProfile(source) {
  const profile = source && typeof source === "object" ? source : {};

  return {
    firstPlayedAt: typeof profile.firstPlayedAt === "string" ? profile.firstPlayedAt : null,
    lastPlayedAt: typeof profile.lastPlayedAt === "string" ? profile.lastPlayedAt : null,
    lastEndedAt: typeof profile.lastEndedAt === "string" ? profile.lastEndedAt : null,
    totalPlayMs: Math.max(0, Math.round(Number(profile.totalPlayMs) || 0)),
    sessionCount: Math.max(0, Math.round(Number(profile.sessionCount) || 0)),
    resumedCount: Math.max(0, Math.round(Number(profile.resumedCount) || 0)),
    returnToTitleCount: Math.max(0, Math.round(Number(profile.returnToTitleCount) || 0)),
  };
}

function sanitizeAchievementProgressMap(source) {
  const validIds = new Set(getAchievementDefinitions().map((achievement) => achievement.id));
  const entries = source && typeof source === "object" ? Object.entries(source) : [];

  return new Map(
    entries
      .filter(([achievementId, unlockedAt]) => validIds.has(achievementId) && typeof unlockedAt === "string" && unlockedAt.trim())
      .map(([achievementId, unlockedAt]) => [achievementId, unlockedAt])
  );
}

function sanitizeChapterReplayProgressMap(source) {
  const validIds = new Set(getChapterReplayEntries().map((chapter) => chapter.chapterId));
  const entries = source && typeof source === "object" ? Object.entries(source) : [];

  return new Map(
    entries
      .filter(([chapterId, unlockedAt]) => validIds.has(chapterId) && typeof unlockedAt === "string" && unlockedAt.trim())
      .map(([chapterId, unlockedAt]) => [chapterId, unlockedAt])
  );
}

function loadStoredAchievementProgress() {
  const storage = getBrowserStorage();

  if (!storage) {
    return new Map();
  }

  try {
    const raw = storage.getItem(getAchievementProgressStorageKey());

    if (!raw) {
      return new Map();
    }

    return sanitizeAchievementProgressMap(JSON.parse(raw));
  } catch (error) {
    return new Map();
  }
}

function loadStoredChapterReplayProgress() {
  const storage = getBrowserStorage();

  if (!storage) {
    return new Map();
  }

  try {
    const raw = storage.getItem(getChapterReplayStorageKey());

    if (!raw) {
      return new Map();
    }

    return sanitizeChapterReplayProgressMap(JSON.parse(raw));
  } catch (error) {
    return new Map();
  }
}

function persistAchievementProgress() {
  const storage = getBrowserStorage();

  if (!storage) {
    return;
  }

  try {
    storage.setItem(
      getAchievementProgressStorageKey(),
      JSON.stringify(Object.fromEntries(state.achievementProgress))
    );
  } catch (error) {
    // Ignore storage write failures so achievement collection remains optional.
  }
}

function persistChapterReplayProgress() {
  const storage = getBrowserStorage();

  if (!storage) {
    return;
  }

  try {
    storage.setItem(
      getChapterReplayStorageKey(),
      JSON.stringify(Object.fromEntries(state.chapterReplayProgress))
    );
  } catch (error) {
    // Ignore storage write failures so chapter replay remains optional.
  }
}

function loadStoredLocationArchiveProgress() {
  const storage = getBrowserStorage();

  if (!storage) {
    return new Map();
  }

  try {
    const raw = storage.getItem(getLocationArchiveStorageKey());

    if (!raw) {
      return new Map();
    }

    return sanitizeLocationArchiveProgressMap(JSON.parse(raw));
  } catch (error) {
    return new Map();
  }
}

function persistLocationArchiveProgress() {
  const storage = getBrowserStorage();

  if (!storage) {
    return;
  }

  try {
    storage.setItem(
      getLocationArchiveStorageKey(),
      JSON.stringify(Object.fromEntries(state.locationArchiveProgress))
    );
  } catch (error) {
    // Ignore storage write failures so location archive remains optional.
  }
}

function loadStoredNarrationArchiveProgress() {
  const storage = getBrowserStorage();

  if (!storage) {
    return new Map();
  }

  try {
    const raw = storage.getItem(getNarrationArchiveStorageKey());

    if (!raw) {
      return new Map();
    }

    return sanitizeNarrationArchiveProgressMap(JSON.parse(raw));
  } catch (error) {
    return new Map();
  }
}

function persistNarrationArchiveProgress() {
  const storage = getBrowserStorage();

  if (!storage) {
    return;
  }

  try {
    storage.setItem(
      getNarrationArchiveStorageKey(),
      JSON.stringify(Object.fromEntries(state.narrationArchiveProgress))
    );
  } catch (error) {
    // Ignore storage write failures so narration archive remains optional.
  }
}

function loadStoredRelationArchiveProgress() {
  const storage = getBrowserStorage();

  if (!storage) {
    return new Map();
  }

  try {
    const raw = storage.getItem(getRelationArchiveStorageKey());

    if (!raw) {
      return new Map();
    }

    return sanitizeRelationArchiveProgressMap(JSON.parse(raw));
  } catch (error) {
    return new Map();
  }
}

function persistRelationArchiveProgress() {
  const storage = getBrowserStorage();

  if (!storage) {
    return;
  }

  try {
    storage.setItem(
      getRelationArchiveStorageKey(),
      JSON.stringify(Object.fromEntries(state.relationArchiveProgress))
    );
  } catch (error) {
    // Ignore storage write failures so relation archive remains optional.
  }
}

function loadStoredVoiceReplayProgress() {
  const storage = getBrowserStorage();

  if (!storage) {
    return new Map();
  }

  try {
    const raw = storage.getItem(getVoiceReplayStorageKey());

    if (!raw) {
      return new Map();
    }

    return sanitizeVoiceReplayProgressMap(JSON.parse(raw));
  } catch (error) {
    return new Map();
  }
}

function persistVoiceReplayProgress() {
  const storage = getBrowserStorage();

  if (!storage) {
    return;
  }

  try {
    storage.setItem(
      getVoiceReplayStorageKey(),
      JSON.stringify(Object.fromEntries(state.voiceReplayProgress))
    );
  } catch (error) {
    // Ignore storage write failures so voice replay collection remains optional.
  }
}

function unlockAchievement(achievementId, { silent = false } = {}) {
  if (!achievementId) {
    return false;
  }

  const definition = getAchievementDefinitions().find((achievement) => achievement.id === achievementId);
  if (!definition || state.achievementProgress.has(achievementId)) {
    return false;
  }

  state.achievementProgress.set(achievementId, new Date().toISOString());
  persistAchievementProgress();

  if (!silent) {
    refs.gameMeta.textContent = buildMetaSummary();
    renderStartSummary();
    renderBuildInfo();
    renderExtraButtons();
    renderAchievementDialog();
  }

  return true;
}

function syncAchievementProgressFromState() {
  let changed = false;

  if (data.scenes.length > 0 && state.started) {
    changed = unlockAchievement("first_start", { silent: true }) || changed;
  }

  if (state.characterArchive.size > 0) {
    changed = unlockAchievement("first_character", { silent: true }) || changed;
  }

  const characters = getCharacterArchiveEntries();
  if (characters.length > 0 && state.characterArchive.size >= characters.length) {
    changed = unlockAchievement("all_characters", { silent: true }) || changed;
  }

  if (state.extraUnlocks.cg.size > 0) {
    changed = unlockAchievement("first_cg", { silent: true }) || changed;
  }

  const galleryAssets = getGalleryAssets();
  if (galleryAssets.length > 0 && state.extraUnlocks.cg.size >= galleryAssets.length) {
    changed = unlockAchievement("all_cg", { silent: true }) || changed;
  }

  if (state.extraUnlocks.bgm.size > 0) {
    changed = unlockAchievement("first_bgm", { silent: true }) || changed;
  }

  const musicAssets = getMusicRoomAssets();
  if (musicAssets.length > 0 && state.extraUnlocks.bgm.size >= musicAssets.length) {
    changed = unlockAchievement("all_bgm", { silent: true }) || changed;
  }

  if (state.endingProgress.unlocked.size > 0) {
    changed = unlockAchievement("first_ending", { silent: true }) || changed;
  }

  const endingScenes = getEndingScenes();
  if (endingScenes.length > 0 && state.endingProgress.unlocked.size >= endingScenes.length) {
    changed = unlockAchievement("all_endings", { silent: true }) || changed;
  }

  return changed;
}

function getCharacterArchiveStorageKey() {
  return `canvasia-engine:player-characters:${getProjectStorageScope()}`;
}

function getExtraUnlockStorageKey() {
  return `canvasia-engine:player-extra:${getProjectStorageScope()}`;
}

function getEndingProgressStorageKey() {
  return `canvasia-engine:player-endings:${getProjectStorageScope()}`;
}

function getEndingScenes() {
  return data.endingScenes ?? [];
}

function getEndingSceneIds() {
  return getEndingScenes().map((scene) => scene.id);
}

function sanitizeEndingUnlockMap(source) {
  const validSceneIds = new Set(getEndingSceneIds());
  const entries = source && typeof source === "object" ? Object.entries(source) : [];

  return new Map(
    entries
      .filter(([sceneId, unlockedAt]) => validSceneIds.has(sceneId) && typeof unlockedAt === "string" && unlockedAt.trim())
      .map(([sceneId, unlockedAt]) => [sceneId, unlockedAt])
  );
}

function loadStoredEndingProgress() {
  const storage = getBrowserStorage();

  if (!storage) {
    return { unlocked: new Map(), completionCount: 0, lastCompletedAt: null };
  }

  try {
    const raw = storage.getItem(getEndingProgressStorageKey());

    if (!raw) {
      return { unlocked: new Map(), completionCount: 0, lastCompletedAt: null };
    }

    const parsed = JSON.parse(raw);
    return {
      unlocked: sanitizeEndingUnlockMap(parsed?.unlocked),
      completionCount: Math.max(0, Math.round(Number(parsed?.completionCount) || 0)),
      lastCompletedAt: typeof parsed?.lastCompletedAt === "string" ? parsed.lastCompletedAt : null,
    };
  } catch (error) {
    return { unlocked: new Map(), completionCount: 0, lastCompletedAt: null };
  }
}

function persistEndingProgress() {
  const storage = getBrowserStorage();

  if (!storage) {
    return;
  }

  try {
    storage.setItem(
      getEndingProgressStorageKey(),
      JSON.stringify({
        unlocked: Object.fromEntries(state.endingProgress.unlocked),
        completionCount: state.endingProgress.completionCount,
        lastCompletedAt: state.endingProgress.lastCompletedAt,
      })
    );
  } catch (error) {
    // Ignore storage write failures so ending collection remains optional.
  }
}

function getGalleryAssets() {
  return data.assets.filter((asset) => asset.type === "cg");
}

function getMusicRoomAssets() {
  return data.assets.filter((asset) => asset.type === "bgm");
}

function getCharacterArchiveEntries() {
  return data.characters ?? [];
}

function sanitizeCharacterArchiveSet(source) {
  const validIds = new Set(getCharacterArchiveEntries().map((character) => character.id));

  return new Set(
    Array.isArray(source)
      ? source.filter((characterId) => typeof characterId === "string" && validIds.has(characterId))
      : []
  );
}

function loadStoredCharacterArchive() {
  const storage = getBrowserStorage();

  if (!storage) {
    return new Set();
  }

  try {
    const raw = storage.getItem(getCharacterArchiveStorageKey());

    if (!raw) {
      return new Set();
    }

    return sanitizeCharacterArchiveSet(JSON.parse(raw));
  } catch (error) {
    return new Set();
  }
}

function persistCharacterArchive() {
  const storage = getBrowserStorage();

  if (!storage) {
    return;
  }

  try {
    storage.setItem(getCharacterArchiveStorageKey(), JSON.stringify(Array.from(state.characterArchive)));
  } catch (error) {
    // Ignore storage write failures so archive mode remains optional.
  }
}

function sanitizeExtraUnlockSet(source, assetType) {
  const validIds = new Set(
    data.assets
      .filter((asset) => asset.type === assetType)
      .map((asset) => asset.id)
  );

  return new Set(
    Array.isArray(source)
      ? source.filter((assetId) => typeof assetId === "string" && validIds.has(assetId))
      : []
  );
}

function loadStoredExtraUnlocks() {
  const storage = getBrowserStorage();

  if (!storage) {
    return { cg: new Set(), bgm: new Set() };
  }

  try {
    const raw = storage.getItem(getExtraUnlockStorageKey());

    if (!raw) {
      return { cg: new Set(), bgm: new Set() };
    }

    const parsed = JSON.parse(raw);
    return {
      cg: sanitizeExtraUnlockSet(parsed?.cg, "cg"),
      bgm: sanitizeExtraUnlockSet(parsed?.bgm, "bgm"),
    };
  } catch (error) {
    return { cg: new Set(), bgm: new Set() };
  }
}

function persistExtraUnlocks() {
  const storage = getBrowserStorage();

  if (!storage) {
    return;
  }

  try {
    storage.setItem(
      getExtraUnlockStorageKey(),
      JSON.stringify({
        cg: Array.from(state.extraUnlocks.cg),
        bgm: Array.from(state.extraUnlocks.bgm),
      })
    );
  } catch (error) {
    // Ignore storage write failures so extra mode remains optional.
  }
}

function unlockExtraAsset(type, assetId) {
  if (!assetId || !state.extraUnlocks[type]?.has) {
    return false;
  }

  const asset = data.assetsById.get(assetId);
  if (!asset || asset.type !== type || state.extraUnlocks[type].has(assetId)) {
    return false;
  }

  state.extraUnlocks[type].add(assetId);
  persistExtraUnlocks();
  syncAchievementProgressFromState();
  refs.gameMeta.textContent = buildMetaSummary();
  renderStartSummary();
  renderBuildInfo();
  renderExtraButtons();
  renderProfileDialog();
  renderAchievementDialog();
  renderGalleryDialog();
  renderMusicRoomDialog();
  return true;
}
function createEmptySaveSlots() {
  return Array.from({ length: getProjectFormalSaveSlotCount() }, () => null);
}

function deepCloneRuntimeData(value) {
  try {
    return JSON.parse(JSON.stringify(value ?? null));
  } catch (error) {
    return null;
  }
}

function sanitizeStoredSnapshot(source) {
  if (!source || typeof source !== "object") {
    return null;
  }

  const sceneId = typeof source.sceneId === "string" ? source.sceneId : null;
  const scene = sceneId ? data.scenesById.get(sceneId) : null;
  const choiceOptions = Array.isArray(source.choiceOptions)
    ? source.choiceOptions
        .map((option) => deepCloneRuntimeData(option))
        .filter(Boolean)
    : [];

  return {
    sceneId,
    sceneName: String(source.sceneName ?? scene?.name ?? sceneId ?? "试玩记录"),
    blockIndex: Number.isFinite(Number(source.blockIndex)) ? Number(source.blockIndex) : -1,
    blockId: source.blockId == null ? null : String(source.blockId),
    blockType: source.completed ? "complete" : String(source.blockType ?? "dialogue"),
    block: source.block && typeof source.block === "object" ? deepCloneRuntimeData(source.block) : null,
    visualState: clonePreviewVisualState(source.visualState),
    variables: clonePreviewVariables(source.variables),
    choiceOptions,
    transitionTargetSceneId:
      source.transitionTargetSceneId == null ? null : String(source.transitionTargetSceneId),
    completed: Boolean(source.completed),
  };
}

function relocalizeRuntimeSnapshot(snapshot) {
  if (!snapshot || !snapshot.block) {
    return snapshot;
  }
  const scene = data.scenesById.get(snapshot.sceneId);
  snapshot.sceneName = getSceneName(scene, snapshot.sceneName);
  if (snapshot.blockType === "dialogue") {
    snapshot.visualState.speakerName = getCharacterName(snapshot.block.speakerId);
    snapshot.visualState.dialogueText = getBlockText(snapshot.block);
  } else if (snapshot.blockType === "narration") {
    snapshot.visualState.speakerName = "旁白";
    snapshot.visualState.dialogueText = getBlockText(snapshot.block);
  } else if (snapshot.blockType === "choice") {
    snapshot.visualState.speakerName = "选择分支";
    snapshot.visualState.dialogueText = "请选择一个选项继续试玩。";
  }
  return snapshot;
}

function relocalizeRuntimeSession() {
  if (!state.session?.timeline?.length) {
    return;
  }
  state.session.timeline.forEach((snapshot) => relocalizeRuntimeSnapshot(snapshot));
}

function sanitizeStoredSession(source) {
  if (!source || typeof source !== "object") {
    return null;
  }

  const fallbackSceneId = getSafeSceneId(source.startSceneId ?? getEntrySceneId());
  const timeline = Array.isArray(source.timeline)
    ? source.timeline
        .map((snapshot) => sanitizeStoredSnapshot(snapshot))
        .filter(Boolean)
    : [];

  if (timeline.length === 0) {
    return null;
  }

  return {
    startSceneId: getSafeSceneId(source.startSceneId ?? timeline[0]?.sceneId ?? fallbackSceneId),
    timeline,
    position: Math.min(Math.max(Math.round(Number(source.position) || 0), 0), timeline.length - 1),
  };
}

function sanitizeStoredSaveSlot(source) {
  if (!source || typeof source !== "object") {
    return null;
  }

  const session = sanitizeStoredSession(source.session);

  if (!session) {
    return null;
  }

  return {
    savedAt: source.savedAt ? String(source.savedAt) : new Date().toISOString(),
    session,
    thumbnailDataUrl: typeof source.thumbnailDataUrl === "string" ? source.thumbnailDataUrl : "",
  };
}

function loadStoredAutoResume() {
  const storage = getBrowserStorage();

  if (!storage) {
    return null;
  }

  try {
    const raw = storage.getItem(getAutoResumeStorageKey());

    if (!raw) {
      return null;
    }

    return sanitizeStoredSaveSlot(JSON.parse(raw));
  } catch (error) {
    return null;
  }
}

function loadStoredSaveSlots() {
  const storage = getBrowserStorage();
  const slotCount = getProjectFormalSaveSlotCount();

  if (!storage) {
    return createEmptySaveSlots();
  }

  try {
    const raw = storage.getItem(getSaveSlotStorageKey());

    if (!raw) {
      return createEmptySaveSlots();
    }

    const parsed = JSON.parse(raw);
    const sourceSlots = Array.isArray(parsed) ? parsed : Array.isArray(parsed?.slots) ? parsed.slots : [];

    return Array.from({ length: slotCount }, (_, index) => sanitizeStoredSaveSlot(sourceSlots[index]));
  } catch (error) {
    return createEmptySaveSlots();
  }
}

function loadStoredQuickSave() {
  const storage = getBrowserStorage();

  if (!storage) {
    return null;
  }

  try {
    const raw = storage.getItem(getQuickSaveStorageKey());

    if (!raw) {
      return null;
    }

    return sanitizeStoredSaveSlot(JSON.parse(raw));
  } catch (error) {
    return null;
  }
}

function loadStoredPlayerProfile() {
  const storage = getBrowserStorage();

  if (!storage) {
    return sanitizePlayerProfile(null);
  }

  try {
    const raw = storage.getItem(getPlayerProfileStorageKey());

    if (!raw) {
      return sanitizePlayerProfile(null);
    }

    return sanitizePlayerProfile(JSON.parse(raw));
  } catch (error) {
    return sanitizePlayerProfile(null);
  }
}

function persistAutoResume() {
  const storage = getBrowserStorage();

  if (!storage) {
    return;
  }

  const session = sanitizeStoredSession(state.session);

  if (!session) {
    return;
  }

  state.autoResume = {
    savedAt: new Date().toISOString(),
    session: deepCloneRuntimeData(session),
    thumbnailDataUrl: buildSaveThumbnailDataUrl(getCurrentSnapshot()),
  };

  try {
    storage.setItem(getAutoResumeStorageKey(), JSON.stringify(state.autoResume));
  } catch (error) {
    // Ignore storage write failures so auto resume remains optional.
  }
}

function persistPlayerProfile() {
  const storage = getBrowserStorage();

  if (!storage || !state.playerProfile) {
    return;
  }

  try {
    storage.setItem(getPlayerProfileStorageKey(), JSON.stringify(state.playerProfile));
  } catch (error) {
    // Ignore storage write failures so player profile remains optional.
  }
}

function refreshPlayerProfileUi() {
  refs.gameMeta.textContent = buildMetaSummary();
  renderStartSummary();
  renderBuildInfo();
  renderExtraButtons();
  renderProfileDialog();
}

function formatPlayDuration(totalMs) {
  const minutes = Math.max(0, Math.round((Number(totalMs) || 0) / 60000));

  if (minutes < 60) {
    return `${minutes} 分钟`;
  }

  const hours = Math.floor(minutes / 60);
  const restMinutes = minutes % 60;

  return restMinutes > 0 ? `${hours} 小时 ${restMinutes} 分钟` : `${hours} 小时`;
}

function recordPlayerSessionStart(mode = "start") {
  finalizePlayerSession({ silent: true });

  const now = new Date().toISOString();
  const profile = state.playerProfile ?? sanitizePlayerProfile(null);
  if (!profile.firstPlayedAt) {
    profile.firstPlayedAt = now;
  }
  profile.lastPlayedAt = now;
  profile.sessionCount += 1;
  if (mode === "resume") {
    profile.resumedCount += 1;
  }
  state.playerProfile = profile;
  state.profileSessionStartedAt = Date.now();
  persistPlayerProfile();
  refreshPlayerProfileUi();
}

function finalizePlayerSession({ silent = false } = {}) {
  if (!state.profileSessionStartedAt || !state.playerProfile) {
    return false;
  }

  const elapsedMs = Math.max(0, Date.now() - state.profileSessionStartedAt);
  state.playerProfile.totalPlayMs += elapsedMs;
  state.playerProfile.lastEndedAt = new Date().toISOString();
  state.profileSessionStartedAt = null;
  persistPlayerProfile();

  if (!silent) {
    refreshPlayerProfileUi();
  }

  return true;
}

function persistSaveSlots() {
  const storage = getBrowserStorage();

  if (!storage) {
    return;
  }

  try {
    const payload = state.saveSlots.map((slot) =>
      slot
        ? {
            savedAt: slot.savedAt,
            session: deepCloneRuntimeData(slot.session),
            thumbnailDataUrl: slot.thumbnailDataUrl ?? "",
          }
        : null
    );

    storage.setItem(getSaveSlotStorageKey(), JSON.stringify(payload));
  } catch (error) {
    // Ignore storage write failures so local save slots stay optional.
  }
}

function persistQuickSave() {
  const storage = getBrowserStorage();

  if (!storage) {
    return;
  }

  try {
    storage.setItem(
      getQuickSaveStorageKey(),
      JSON.stringify(
        state.quickSave
          ? {
              savedAt: state.quickSave.savedAt,
              session: deepCloneRuntimeData(state.quickSave.session),
              thumbnailDataUrl: state.quickSave.thumbnailDataUrl ?? "",
            }
          : null
      )
    );
  } catch (error) {
    // Ignore storage write failures so quick save stays optional.
  }
}

function clearStoredAutoResume() {
  const storage = getBrowserStorage();
  state.autoResume = null;

  if (!storage) {
    return;
  }

  try {
    storage.removeItem(getAutoResumeStorageKey());
  } catch (error) {
    // Ignore storage cleanup failures.
  }
}

function clearStoredQuickSave() {
  const storage = getBrowserStorage();
  state.quickSave = null;

  if (!storage) {
    return;
  }

  try {
    storage.removeItem(getQuickSaveStorageKey());
  } catch (error) {
    // Ignore storage cleanup failures.
  }
}

function clearStoredCharacterArchive() {
  const storage = getBrowserStorage();
  state.characterArchive = new Set();

  if (!storage) {
    return;
  }

  try {
    storage.removeItem(getCharacterArchiveStorageKey());
  } catch (error) {
    // Ignore storage cleanup failures.
  }
}

function loadStoredReadHistory() {
  const storage = getBrowserStorage();

  if (!storage) {
    return new Set();
  }

  try {
    const raw = storage.getItem(getReadHistoryStorageKey());

    if (!raw) {
      return new Set();
    }

    const parsed = JSON.parse(raw);
    const values = Array.isArray(parsed) ? parsed : [];
    return new Set(values.filter((value) => typeof value === "string" && value.trim()));
  } catch (error) {
    return new Set();
  }
}

function persistReadHistory() {
  const storage = getBrowserStorage();

  if (!storage) {
    return;
  }

  try {
    storage.setItem(getReadHistoryStorageKey(), JSON.stringify(Array.from(state.readHistory)));
  } catch (error) {
    // Ignore storage write failures so read history remains optional.
  }
}

function getTypewriterStepDelay(speed, visibleText = "", fullText = "") {
  const safeSpeed = getSafeTextSpeed(speed);
  if (safeSpeed === "instant") {
    return 0;
  }
  return {
    slow: 42,
    normal: 28,
    fast: 18,
    instant: 0,
  }[safeSpeed] + getTypewriterPunctuationPause(visibleText, fullText);
}

function getCurrentStepKey(snapshot) {
  if (!snapshot) {
    return "";
  }

  return `${snapshot.sceneId ?? "none"}:${snapshot.blockId ?? "complete"}:${snapshot.blockIndex}`;
}

function getReadStepKey(snapshot) {
  if (!snapshot) {
    return "";
  }

  return `${snapshot.sceneId ?? "none"}:${snapshot.blockId ?? "complete"}:${snapshot.blockIndex}`;
}

function isSnapshotRead(snapshot) {
  const stepKey = getReadStepKey(snapshot);
  return Boolean(stepKey) && state.readHistory.has(stepKey);
}

function markSnapshotAsRead(snapshot) {
  const stepKey = getReadStepKey(snapshot);

  if (!stepKey || state.readHistory.has(stepKey)) {
    return false;
  }

  state.readHistory.add(stepKey);
  persistReadHistory();
  return true;
}

function getVoiceAssetId(snapshot) {
  if (!snapshot || (snapshot.blockType !== "dialogue" && snapshot.blockType !== "narration")) {
    return "";
  }

  return snapshot.block?.voiceAssetId ?? "";
}

function getAutoAdvanceDelay(snapshot) {
  if (!snapshot) {
    return 0;
  }

  if (snapshot.blockType === "dialogue" || snapshot.blockType === "narration") {
    const text = snapshot.visualState?.dialogueText ?? "";
    const multiplier = {
      slow: 92,
      normal: 72,
      fast: 58,
      instant: 42,
    }[getSnapshotTextSpeed(snapshot)];
    return Math.min(6800, Math.max(1100, 520 + text.length * multiplier));
  }

  if (snapshot.blockType === "jump" || snapshot.blockType === "condition") {
    return 520;
  }

  if (snapshot.blockType === "wait") {
    return getSafeWaitDurationMs(snapshot.block?.durationSeconds);
  }

  return 820;
}

function stopRuntimeAutoAdvance() {
  if (state.autoAdvanceTimer) {
    window.clearTimeout(state.autoAdvanceTimer);
    state.autoAdvanceTimer = null;
  }

  state.autoAdvanceStepKey = null;
}

function stopOneShotAudio() {
  stopTrackedAudios(activeSfxAudios);
}

function stopVoicePlayback({ resetStepKey = true } = {}) {
  if (state.voiceAudio) {
    disposeAudio(state.voiceAudio);
    state.voiceAudio = null;
  }

  if (resetStepKey) {
    state.currentVoiceStepKey = null;
  }

  updateRuntimeAudioVolumes();
}

function updateRuntimeAudioVolumes() {
  if (state.bgmAudio) {
    cancelAudioFade(state.bgmAudio);
    state.bgmAudio.volume = getRuntimeMusicTargetVolume(getCurrentSnapshot());
  }

  if (musicRoomAudio) {
    musicRoomAudio.volume = getVolumeRatio(state.playback.bgmVolume, 72);
  }

  if (state.voiceAudio) {
    state.voiceAudio.volume = getRuntimeVoiceTargetVolume(getCurrentSnapshot());
  }

  activeSfxAudios.forEach((audio) => {
    audio.volume = getRuntimeSfxTargetVolume(audio._canvasiaSfxVolumePercent);
  });
}

function isRuntimeVoiceDuckingActive() {
  return (
    state.playback?.voiceDuckingEnabled !== false &&
    state.playback?.voiceEnabled !== false &&
    Boolean(state.voiceAudio) &&
    !state.voiceAudio.paused &&
    !state.voiceAudio.ended
  );
}

function applyDialogTheme() {
  const presentation = buildDialogBoxPresentation(state.playback.dialogTheme, data.project);

  if (refs.dialogPanel) {
    refs.dialogPanel.dataset.dialogTheme = presentation.theme;
    refs.dialogPanel.setAttribute("style", presentation.style);
    const artNode = refs.dialogPanel.querySelector(".dialog-panel-art");
    if (artNode) {
      artNode.classList.toggle("has-image", Boolean(presentation.assetUrl));
    }
  }

  if (refs.stageFrame) {
    refs.stageFrame.dataset.dialogTheme = presentation.theme;
    refs.stageFrame.dataset.dialogAnchor = presentation.theme === "project" ? getProjectDialogBoxConfig(data.project).anchor : "bottom";
  }
}

function renderDialogVisibility() {
  if (refs.dialogPanel) {
    refs.dialogPanel.classList.toggle("is-hidden", state.dialogHidden);
  }

  if (refs.dialogHiddenHint) {
    refs.dialogHiddenHint.hidden = !state.dialogHidden;
  }
}

function scheduleRuntimeAutoAdvance(snapshot, options = {}) {
  stopRuntimeAutoAdvance();

  const skipActive = state.playback.skipRead;
  const autoPlayActive = state.playback.autoPlay;
  const timedWaitActive = snapshot?.blockType === "wait";

  if (
    (!autoPlayActive && !skipActive && !timedWaitActive) ||
    !snapshot ||
    snapshot.completed ||
    isBlockingMediaSnapshot(snapshot) ||
    snapshot.choiceOptions.length > 0
  ) {
    return;
  }

  if (skipActive && !timedWaitActive && !isSnapshotRead(snapshot)) {
    state.playback.skipRead = false;
    persistPlaybackSettings();
    renderPlaybackControls(snapshot);
    return;
  }

  if (isRuntimeTypewriterActive()) {
    return;
  }

  const stepKey = getCurrentStepKey(snapshot);
  const voiceAssetId = getVoiceAssetId(snapshot);
  const shouldWaitVoice =
    !skipActive &&
    options.preferVoiceEnding !== true &&
    Boolean(voiceAssetId) &&
    state.playback.voiceEnabled &&
    state.currentVoiceStepKey === stepKey &&
    state.voiceAudio &&
    !state.voiceAudio.paused;

  if (shouldWaitVoice) {
    state.autoAdvanceStepKey = stepKey;
    return;
  }

  state.autoAdvanceStepKey = stepKey;
  state.autoAdvanceTimer = window.setTimeout(() => {
    const current = getCurrentSnapshot();
    if (
      (!state.playback.autoPlay && !state.playback.skipRead && current?.blockType !== "wait") ||
      state.autoAdvanceStepKey !== stepKey
    ) {
      return;
    }

    if (!current || getCurrentStepKey(current) !== stepKey) {
      return;
    }

    movePreviewForward();
    renderRuntime();
  }, skipActive ? 70 : options.preferVoiceEnding ? 180 : getAutoAdvanceDelay(snapshot));
}

function handleVoiceEnded() {
  const snapshot = getCurrentSnapshot();
  const stepKey = getCurrentStepKey(snapshot);

  updateRuntimeAudioVolumes();

  if (stepKey && stepKey === state.currentVoiceStepKey) {
    scheduleRuntimeAutoAdvance(snapshot, { preferVoiceEnding: true });
  }
}

function handleVoiceError() {
  const snapshot = getCurrentSnapshot();
  updateRuntimeAudioVolumes();
  scheduleRuntimeAutoAdvance(snapshot);
}

function syncVoice(snapshot) {
  const voiceAssetId = getVoiceAssetId(snapshot);
  const stepKey = getCurrentStepKey(snapshot);
  const targetVolume = getRuntimeVoiceTargetVolume(snapshot);

  if (!state.playback.voiceEnabled || !voiceAssetId) {
    stopVoicePlayback();
    return;
  }

  if (state.currentVoiceStepKey === stepKey && state.voiceAudio) {
    state.voiceAudio.volume = targetVolume;
    updateRuntimeAudioVolumes();
    return;
  }

  const voiceUrl = getAssetUrl(voiceAssetId);
  stopVoicePlayback({ resetStepKey: false });
  state.currentVoiceStepKey = stepKey;

  if (!voiceUrl) {
    return;
  }

  const audio = new Audio(encodeURI(voiceUrl));
  audio.volume = targetVolume;
  audio.addEventListener("play", updateRuntimeAudioVolumes);
  audio.addEventListener("playing", updateRuntimeAudioVolumes);
  audio.addEventListener("pause", updateRuntimeAudioVolumes);
  audio.addEventListener("ended", handleVoiceEnded);
  audio.addEventListener("error", handleVoiceError);
  audio.play().catch(() => {
    scheduleRuntimeAutoAdvance(snapshot);
    updateRuntimeAudioVolumes();
  });
  state.voiceAudio = audio;
  updateRuntimeAudioVolumes();
}

function getRuntimeVoiceTargetVolume(snapshot) {
  return getRuntimeVoiceTargetVolumeBase(state.playback, snapshot);
}

function renderPlaybackControls(snapshot = getCurrentSnapshot()) {
  if (refs.textSpeedSelect) {
    refs.textSpeedSelect.value = getSafeTextSpeed(state.playback.textSpeed);
  }

  renderRuntimeLanguageSelect(refs.languageSelect);

  if (refs.dialogThemeSelect) {
    refs.dialogThemeSelect.value = getSafeDialogTheme(state.playback.dialogTheme);
  }

  if (refs.uiThemeSelect) {
    refs.uiThemeSelect.value = getSafeUiThemeMode(state.playback.uiThemeMode);
  }

  if (refs.menuTextSpeedSelect) {
    refs.menuTextSpeedSelect.value = getSafeTextSpeed(state.playback.textSpeed);
  }

  renderRuntimeLanguageSelect(refs.menuLanguageSelect);

  if (refs.menuDialogThemeSelect) {
    refs.menuDialogThemeSelect.value = getSafeDialogTheme(state.playback.dialogTheme);
  }

  if (refs.menuUiThemeSelect) {
    refs.menuUiThemeSelect.value = getSafeUiThemeMode(state.playback.uiThemeMode);
  }

  if (refs.bgmVolumeRange) {
    refs.bgmVolumeRange.value = String(getSafeVolumePercent(state.playback.bgmVolume, 72));
  }

  if (refs.bgmVolumeValue) {
    refs.bgmVolumeValue.textContent = formatVolumePercent(state.playback.bgmVolume, 72);
  }

  if (refs.menuBgmVolumeRange) {
    refs.menuBgmVolumeRange.value = String(getSafeVolumePercent(state.playback.bgmVolume, 72));
  }

  if (refs.menuBgmVolumeValue) {
    refs.menuBgmVolumeValue.textContent = formatVolumePercent(state.playback.bgmVolume, 72);
  }

  if (refs.sfxVolumeRange) {
    refs.sfxVolumeRange.value = String(getSafeVolumePercent(state.playback.sfxVolume, 85));
  }

  if (refs.sfxVolumeValue) {
    refs.sfxVolumeValue.textContent = formatVolumePercent(state.playback.sfxVolume, 85);
  }

  if (refs.menuSfxVolumeRange) {
    refs.menuSfxVolumeRange.value = String(getSafeVolumePercent(state.playback.sfxVolume, 85));
  }

  if (refs.menuSfxVolumeValue) {
    refs.menuSfxVolumeValue.textContent = formatVolumePercent(state.playback.sfxVolume, 85);
  }

  if (refs.voiceVolumeRange) {
    refs.voiceVolumeRange.value = String(getSafeVolumePercent(state.playback.voiceVolume, 92));
  }

  if (refs.voiceVolumeValue) {
    refs.voiceVolumeValue.textContent = formatVolumePercent(state.playback.voiceVolume, 92);
  }

  if (refs.menuVoiceVolumeRange) {
    refs.menuVoiceVolumeRange.value = String(getSafeVolumePercent(state.playback.voiceVolume, 92));
  }

  if (refs.menuVoiceVolumeValue) {
    refs.menuVoiceVolumeValue.textContent = formatVolumePercent(state.playback.voiceVolume, 92);
  }

  if (refs.previousHistoryButton) {
    refs.previousHistoryButton.disabled = !canStepRuntimeHistory(-1);
    refs.previousHistoryButton.textContent = "上一句";
  }

  if (refs.nextHistoryButton) {
    refs.nextHistoryButton.disabled = !canStepRuntimeHistory(1);
    refs.nextHistoryButton.textContent = "下一句";
  }

  if (refs.autoPlayToggleButton) {
    refs.autoPlayToggleButton.textContent = `自动播放：${state.playback.autoPlay ? "开" : "关"}`;
  }

  if (refs.voiceToggleButton) {
    refs.voiceToggleButton.textContent = `语音：${state.playback.voiceEnabled ? "开" : "关"}`;
  }

  if (refs.voiceDuckingToggleButton) {
    refs.voiceDuckingToggleButton.textContent = `语音焦点：${state.playback.voiceDuckingEnabled !== false ? "开" : "关"}`;
  }

  if (refs.menuVoiceDuckingToggleButton) {
    refs.menuVoiceDuckingToggleButton.textContent = `语音焦点：${state.playback.voiceDuckingEnabled !== false ? "开" : "关"}`;
  }

  if (refs.skipReadToggleButton) {
    refs.skipReadToggleButton.textContent = `跳过已读：${state.playback.skipRead ? "开" : "关"}`;
  }

  if (refs.dialogToggleButton) {
    refs.dialogToggleButton.textContent = state.dialogHidden ? "显示对话框" : "隐藏对话框";
  }

  if (refs.replayVoiceButton) {
    refs.replayVoiceButton.disabled = !getVoiceAssetId(snapshot);
  }

  applyRuntimeUiTheme(state.playback.uiThemeMode);
  renderRuntimeUiThemeButtons();

  if (refs.systemMenuButton) {
    refs.systemMenuButton.disabled = false;
  }

  applyDialogTheme();
  renderDialogVisibility();
  renderSaveSlots();
  renderSystemMenu();
  renderReturnTitleDialog();
  renderSaveConfirmDialog();
  renderSaveDialog();
  renderOperationGuideDialog();
}

function renderRuntimeLanguageSelect(select) {
  if (!select) {
    return;
  }
  const currentLanguage = getCurrentRuntimeLanguage();
  const options = getSupportedRuntimeLanguages()
    .map(
      (language) =>
        `<option value="${escapeHtml(language)}" ${language === currentLanguage ? "selected" : ""}>${escapeHtml(
          getRuntimeLanguageLabel(language)
        )}</option>`
    )
    .join("");
  if (select.innerHTML !== options) {
    select.innerHTML = options;
  }
  select.value = currentLanguage;
  select.disabled = getSupportedRuntimeLanguages().length <= 1;
}

function setRuntimeUiThemeMode(mode) {
  state.playback.uiThemeMode = getSafeUiThemeMode(mode);
  persistPlaybackSettings();
  applyRuntimeUiTheme(state.playback.uiThemeMode);
  renderPlaybackControls();
}

function handleTextSpeedChange(event) {
  state.playback.textSpeed = getSafeTextSpeed(event.target.value);
  persistPlaybackSettings();
  stopRuntimeTypewriter();
  stopRuntimeAutoAdvance();
  renderRuntime();
}

function handleLanguageChange(event) {
  state.playback.language = getSafeRuntimeLanguage(event.target.value);
  persistPlaybackSettings();
  stopRuntimeTypewriter();
  stopRuntimeAutoAdvance();
  relocalizeRuntimeSession();
  renderStartSummary();
  renderBuildInfo();
  if (state.started && state.session) {
    renderRuntime();
  } else {
    renderBeforeStart();
  }
}

function handleDialogThemeChange(event) {
  state.playback.dialogTheme = getSafeDialogTheme(event.target.value);
  persistPlaybackSettings();
  renderPlaybackControls();
}

function handleUiThemeModeChange(event) {
  state.playback.uiThemeMode = getSafeUiThemeMode(event.target.value);
  persistPlaybackSettings();
  applyRuntimeUiTheme(state.playback.uiThemeMode);
  renderPlaybackControls();
}

function handleBgmVolumeChange(event) {
  state.playback.bgmVolume = getSafeVolumePercent(event.target.value, 72);
  persistPlaybackSettings();
  updateRuntimeAudioVolumes();
  renderPlaybackControls();
}

function handleSfxVolumeChange(event) {
  state.playback.sfxVolume = getSafeVolumePercent(event.target.value, 85);
  persistPlaybackSettings();
  updateRuntimeAudioVolumes();
  renderPlaybackControls();
}

function handleVoiceVolumeChange(event) {
  state.playback.voiceVolume = getSafeVolumePercent(event.target.value, 92);
  persistPlaybackSettings();
  updateRuntimeAudioVolumes();
  renderPlaybackControls();
}

function toggleAutoPlay() {
  state.playback.autoPlay = !state.playback.autoPlay;

  if (state.playback.autoPlay) {
    state.playback.skipRead = false;
  }

  persistPlaybackSettings();
  stopRuntimeAutoAdvance();
  renderRuntime();
}

function toggleSkipRead() {
  state.playback.skipRead = !state.playback.skipRead;

  if (state.playback.skipRead) {
    state.playback.autoPlay = false;
  }

  persistPlaybackSettings();
  stopRuntimeAutoAdvance();
  renderRuntime();
}

function showDialogPanel() {
  if (!state.dialogHidden) {
    return false;
  }

  state.dialogHidden = false;
  renderDialogVisibility();
  return true;
}

function toggleDialogVisibility() {
  if (!state.started || !state.session) {
    return false;
  }

  state.dialogHidden = !state.dialogHidden;
  renderDialogVisibility();
  return true;
}

function toggleVoiceEnabled() {
  state.playback.voiceEnabled = !state.playback.voiceEnabled;
  persistPlaybackSettings();

  if (!state.playback.voiceEnabled) {
    stopVoicePlayback();
  }

  renderRuntime();
}

function toggleVoiceDuckingEnabled() {
  state.playback.voiceDuckingEnabled = state.playback.voiceDuckingEnabled === false;
  persistPlaybackSettings();
  updateRuntimeAudioVolumes();
  renderPlaybackControls();
}

function replayCurrentVoice() {
  const snapshot = getCurrentSnapshot();
  const voiceAssetId = getVoiceAssetId(snapshot);

  if (!voiceAssetId) {
    return;
  }

  if (!state.playback.voiceEnabled) {
    state.playback.voiceEnabled = true;
    persistPlaybackSettings();
  }

  stopRuntimeAutoAdvance();
  state.currentVoiceStepKey = null;
  syncVoice(snapshot);
  renderPlaybackControls(snapshot);
}

function resetPlaybackSettings() {
  state.playback = getProjectPlaybackDefaults();
  persistPlaybackSettings();
  applyRuntimeUiTheme(state.playback.uiThemeMode);
  stopRuntimeAutoAdvance();
  stopRuntimeTypewriter();
  relocalizeRuntimeSession();
  updateRuntimeAudioVolumes();

  if (state.started && state.session) {
    renderRuntime();
  } else {
    renderBeforeStart();
  }
}

function handleGlobalKeydown(event) {
  if (event.defaultPrevented || event.altKey || event.ctrlKey || event.metaKey) {
    return;
  }

  if (state.operationGuideOpen && event.code === "Escape") {
    event.preventDefault();
    closeOperationGuideDialog();
    return;
  }

  if (state.operationGuideOpen) {
    if (isKeyboardTypingTarget(event.target)) {
      return;
    }
    event.preventDefault();
    return;
  }

  if (state.profileDialogOpen && event.code === "Escape") {
    event.preventDefault();
    closeProfileDialog();
    return;
  }

  if (state.profileDialogOpen) {
    if (isKeyboardTypingTarget(event.target)) {
      return;
    }
    event.preventDefault();
    return;
  }

  if (state.voiceReplayDialogOpen && event.code === "Escape") {
    event.preventDefault();
    closeVoiceReplayDialog();
    return;
  }

  if (state.voiceReplayDialogOpen) {
    if (isKeyboardTypingTarget(event.target)) {
      return;
    }
    event.preventDefault();
    return;
  }

  if (state.achievementDialogOpen && event.code === "Escape") {
    event.preventDefault();
    closeAchievementDialog();
    return;
  }

  if (state.achievementDialogOpen) {
    if (isKeyboardTypingTarget(event.target)) {
      return;
    }
    event.preventDefault();
    return;
  }

  if (state.chapterDialogOpen && event.code === "Escape") {
    event.preventDefault();
    closeChapterDialog();
    return;
  }

  if (state.chapterDialogOpen) {
    if (isKeyboardTypingTarget(event.target)) {
      return;
    }
    event.preventDefault();
    return;
  }

  if (state.locationDialogOpen && event.code === "Escape") {
    event.preventDefault();
    closeLocationDialog();
    return;
  }

  if (state.locationDialogOpen) {
    if (isKeyboardTypingTarget(event.target)) {
      return;
    }
    event.preventDefault();
    return;
  }

  if (state.narrationDialogOpen && event.code === "Escape") {
    event.preventDefault();
    closeNarrationDialog();
    return;
  }

  if (state.narrationDialogOpen) {
    if (isKeyboardTypingTarget(event.target)) {
      return;
    }
    event.preventDefault();
    return;
  }

  if (state.relationDialogOpen && event.code === "Escape") {
    event.preventDefault();
    closeRelationDialog();
    return;
  }

  if (state.relationDialogOpen) {
    if (isKeyboardTypingTarget(event.target)) {
      return;
    }
    event.preventDefault();
    return;
  }

  if (state.characterDialogOpen && event.code === "Escape") {
    event.preventDefault();
    closeCharacterDialog();
    return;
  }

  if (state.characterDialogOpen) {
    if (isKeyboardTypingTarget(event.target)) {
      return;
    }
    event.preventDefault();
    return;
  }

  if (state.galleryDialogOpen && event.code === "Escape") {
    event.preventDefault();
    closeGalleryDialog();
    return;
  }

  if (state.galleryDialogOpen) {
    if (isKeyboardTypingTarget(event.target)) {
      return;
    }
    event.preventDefault();
    return;
  }

  if (state.musicRoomDialogOpen && event.code === "Escape") {
    event.preventDefault();
    closeMusicRoomDialog();
    return;
  }

  if (state.musicRoomDialogOpen) {
    if (isKeyboardTypingTarget(event.target)) {
      return;
    }
    event.preventDefault();
    return;
  }

  if (state.endingDialogOpen && event.code === "Escape") {
    event.preventDefault();
    closeEndingDialog();
    return;
  }

  if (state.endingDialogOpen) {
    if (isKeyboardTypingTarget(event.target)) {
      return;
    }
    event.preventDefault();
    return;
  }

  if (state.saveConfirmOpen && event.code === "Escape") {
    event.preventDefault();
    closeSaveConfirmDialog();
    return;
  }

  if (state.saveConfirmOpen) {
    if (isKeyboardTypingTarget(event.target)) {
      return;
    }
    event.preventDefault();
    return;
  }

  if (state.returnTitleConfirmOpen && event.code === "Escape") {
    event.preventDefault();
    closeReturnTitleDialog();
    return;
  }

  if (state.returnTitleConfirmOpen) {
    if (isKeyboardTypingTarget(event.target)) {
      return;
    }
    event.preventDefault();
    return;
  }

  if (state.systemMenuOpen && event.code === "Escape") {
    event.preventDefault();
    closeSystemMenu();
    return;
  }

  if (state.systemMenuOpen) {
    if (isKeyboardTypingTarget(event.target)) {
      return;
    }
    event.preventDefault();
    return;
  }

  if (state.saveDialogOpen && event.code === "Escape") {
    event.preventDefault();
    closeSaveDialog();
    return;
  }

  if (state.saveDialogOpen) {
    if (isKeyboardTypingTarget(event.target)) {
      return;
    }
    event.preventDefault();
    return;
  }

  if (isKeyboardTypingTarget(event.target)) {
    return;
  }

  if (event.code === "F1" || (event.shiftKey && event.code === "Slash")) {
    event.preventDefault();
    openOperationGuideDialog();
    return;
  }

  if (event.code === "KeyR") {
    event.preventDefault();
    startGame();
    return;
  }

  if (event.code === "KeyS") {
    event.preventDefault();
    toggleSkipRead();
    return;
  }

  if (event.code === "KeyQ") {
    event.preventDefault();
    quickSaveCurrent();
    return;
  }

  if (event.code === "KeyL") {
    event.preventDefault();
    quickLoadCurrent();
    return;
  }

  if (event.code === "KeyH") {
    event.preventDefault();
    toggleDialogVisibility();
    return;
  }

  if (event.code === "PageUp" && canStepRuntimeHistory(-1)) {
    event.preventDefault();
    stepRuntimeHistory(-1);
    return;
  }

  if (event.code === "PageDown" && canStepRuntimeHistory(1)) {
    event.preventDefault();
    stepRuntimeHistory(1);
    return;
  }

  if (event.code === "Space" || event.code === "Enter" || event.code === "ArrowRight") {
    event.preventDefault();
    handleContinue();
  }
}

function isKeyboardTypingTarget(target) {
  if (!(target instanceof HTMLElement)) {
    return false;
  }

  return Boolean(target.closest("input, textarea, select, button, [contenteditable='true']"));
}

function handleStageFrameClick(event) {
  if (!(event.target instanceof HTMLElement)) {
    return;
  }

  if (event.target.closest("button, input, select, textarea, label, a")) {
    return;
  }

  if (state.dialogHidden) {
    showDialogPanel();
    return;
  }

  handleContinue();
}

function handleStageFrameContextMenu(event) {
  if (!(event.target instanceof HTMLElement)) {
    return;
  }

  if (event.target.closest("button, input, select, textarea, label, a")) {
    return;
  }

  if (!state.started || !state.session) {
    return;
  }

  event.preventDefault();
  toggleDialogVisibility();
}

function handleHistoryPanelClick(event) {
  if (!(event.target instanceof HTMLElement)) {
    return;
  }

  const jumpButton = event.target.closest("[data-history-index]");

  if (jumpButton) {
    jumpToHistory(jumpButton.dataset.historyIndex);
    return;
  }

  const voiceButton = event.target.closest("[data-history-voice-index]");

  if (voiceButton) {
    void replayHistoryVoice(voiceButton.dataset.historyVoiceIndex);
  }
}

function handleSaveSlotPanelClick(event) {
  if (!(event.target instanceof HTMLElement)) {
    return;
  }

  const loadAutoResumeButton = event.target.closest("[data-load-auto-resume]");

  if (loadAutoResumeButton) {
    continueLastSession();
    closeSaveDialog();
    return;
  }

  const clearAutoResumeButton = event.target.closest("[data-clear-auto-resume]");

  if (clearAutoResumeButton) {
    requestAutoResumeClear();
    return;
  }

  const quickSaveButton = event.target.closest("[data-quick-save]");

  if (quickSaveButton) {
    quickSaveCurrent();
    return;
  }

  const quickLoadButton = event.target.closest("[data-quick-load]");

  if (quickLoadButton) {
    quickLoadCurrent();
    return;
  }

  const clearQuickSaveButton = event.target.closest("[data-clear-quick-save]");

  if (clearQuickSaveButton) {
    requestQuickSaveClear();
    return;
  }

  const pageButton = event.target.closest("[data-save-page]");

  if (pageButton) {
    setSaveDialogPage(pageButton.dataset.savePage);
    return;
  }

  const saveButton = event.target.closest("[data-save-slot]");

  if (saveButton) {
    requestSaveSlot(saveButton.dataset.saveSlot);
    return;
  }

  const loadButton = event.target.closest("[data-load-slot]");

  if (loadButton) {
    loadSaveSlot(loadButton.dataset.loadSlot);
    return;
  }

  const clearButton = event.target.closest("[data-clear-slot]");

  if (clearButton) {
    requestSaveSlotClear(clearButton.dataset.clearSlot);
  }
}

function getRuntimeHistoryStepIndex(delta) {
  const session = state.session;
  const offset = Math.trunc(Number(delta) || 0);

  if (!session || !Number.isInteger(session.position) || !offset) {
    return null;
  }

  const nextIndex = session.position + offset;
  if (nextIndex < 0 || nextIndex >= session.timeline.length) {
    return null;
  }
  return nextIndex;
}

function canStepRuntimeHistory(delta) {
  return getRuntimeHistoryStepIndex(delta) !== null;
}

function stepRuntimeHistory(delta) {
  const nextIndex = getRuntimeHistoryStepIndex(delta);
  return nextIndex === null ? false : jumpToHistory(nextIndex);
}

function jumpToHistory(rawIndex) {
  const session = state.session;
  const nextIndex = Number(rawIndex);

  if (!session || !Number.isInteger(nextIndex) || nextIndex < 0 || nextIndex >= session.timeline.length) {
    return false;
  }

  stopRuntimeTypewriter();
  stopRuntimeAutoAdvance();
  stopOneShotAudio();
  stopVoicePlayback();
  session.position = nextIndex;
  persistAutoResume();
  renderRuntime();
  return true;
}

async function replayHistoryVoice(rawIndex) {
  const session = state.session;
  const nextIndex = Number(rawIndex);

  if (!session || !Number.isInteger(nextIndex) || nextIndex < 0 || nextIndex >= session.timeline.length) {
    return;
  }

  const snapshot = session.timeline[nextIndex];
  const voiceAssetId = getVoiceAssetId(snapshot);

  if (!voiceAssetId) {
    return;
  }

  if (!state.playback.voiceEnabled) {
    state.playback.voiceEnabled = true;
    persistPlaybackSettings();
  }

  stopRuntimeAutoAdvance();
  state.currentVoiceStepKey = null;
  syncVoice(snapshot);
  renderPlaybackControls(getCurrentSnapshot());
}

function getSafeSaveSlotIndex(rawIndex) {
  const numeric = Number(rawIndex);

  if (!Number.isInteger(numeric)) {
    return null;
  }

  const nextIndex = numeric - 1;
  return nextIndex >= 0 && nextIndex < getProjectFormalSaveSlotCount() ? nextIndex : null;
}

function getSaveDialogPageCount() {
  return Math.max(1, Math.ceil(getProjectFormalSaveSlotCount() / SAVE_DIALOG_PAGE_SIZE));
}

function getSafeSaveDialogPage(rawPage) {
  const numeric = Number(rawPage);
  const maxPageIndex = getSaveDialogPageCount() - 1;
  if (!Number.isInteger(numeric)) {
    return Math.min(Math.max(Math.round(Number(state.saveDialogPage) || 0), 0), maxPageIndex);
  }
  return Math.min(Math.max(numeric, 0), maxPageIndex);
}

function getSaveSlotSnapshot(slot) {
  const session = slot?.session;

  if (!session || !Array.isArray(session.timeline) || session.timeline.length === 0) {
    return null;
  }

  const safePosition = Math.min(Math.max(Math.round(Number(session.position) || 0), 0), session.timeline.length - 1);
  return session.timeline[safePosition] ?? session.timeline[0] ?? null;
}

function getSaveSlotSummary(slot) {
  const snapshot = getSaveSlotSnapshot(slot);

  if (!snapshot) {
    return "还没有保存关键节点。";
  }

  const sceneName = snapshot.sceneName ?? snapshot.sceneId ?? "未知场景";
  const stepLabel = snapshot.completed ? "路线已结束" : `第 ${Math.max(snapshot.blockIndex + 1, 0)} 步`;
  const speakerName = snapshot.visualState?.speakerName ? `${snapshot.visualState.speakerName}：` : "";
  const dialogueText = truncateText(snapshot.visualState?.dialogueText ?? "这个节点没有正文。", 34);
  return `${sceneName} · ${stepLabel} · ${speakerName}${dialogueText}`;
}

function getVariableSummary(variables) {
  const changedVariables = (data.variables ?? []).filter((variable) => {
    const currentValue = Object.hasOwn(variables ?? {}, variable.id)
      ? normalizeVariableValue(variable.id, variables?.[variable.id])
      : getVariableDefaultValue(variable.id);
    const defaultValue = getVariableDefaultValue(variable.id);
    return JSON.stringify(currentValue) !== JSON.stringify(defaultValue);
  });

  if (changedVariables.length === 0) {
    return "变量还是初始状态。";
  }

  const summary = changedVariables
    .slice(0, 3)
    .map(
      (variable) =>
        `${variable.name} ${formatVariableValue(
          variable.id,
          Object.hasOwn(variables ?? {}, variable.id) ? variables?.[variable.id] : getVariableDefaultValue(variable.id)
        )}`
    )
    .join(" · ");

  return changedVariables.length > 3 ? `${summary} 等 ${changedVariables.length} 项` : summary;
}

function toAbsoluteThumbnailUrl(url) {
  if (!url) {
    return "";
  }

  try {
    return new URL(url, window.location.href).href;
  } catch (error) {
    return url;
  }
}

function buildSaveThumbnailDataUrl(snapshot) {
  if (!snapshot) {
    return "";
  }

  const width = 320;
  const height = 180;
  const backgroundUrl = toAbsoluteThumbnailUrl(getAssetUrl(snapshot.visualState?.backgroundAssetId ?? ""));
  const visibleCharacters = [...(snapshot.visualState?.visibleCharacters ?? [])]
    .sort((left, right) => getPositionOrder(left.position) - getPositionOrder(right.position))
    .slice(0, 3);
  const positionMap = {
    left: 56,
    center: 160,
    right: 264,
  };
  const spriteMarkup = visibleCharacters
    .map((characterState) => {
      const spriteUrl = toAbsoluteThumbnailUrl(
        getAssetUrl(getSpriteAssetId(characterState.characterId, characterState.expressionId))
      );
      const centerX = positionMap[characterState.position] ?? positionMap.center;
      const x = centerX - 34;
      const y = 46;
      const labelY = 146;
      const localizedName = getCharacterName(characterState.characterId);
      const name = escapeHtml(localizedName);
      const isActive = snapshot.visualState?.activeCharacterId === characterState.characterId;

      if (spriteUrl) {
        return `
          <g opacity="${isActive ? "1" : "0.9"}">
            <image href="${escapeHtml(spriteUrl)}" x="${x}" y="${y}" width="68" height="94" preserveAspectRatio="xMidYMid slice" />
            <rect x="${centerX - 28}" y="${labelY}" rx="8" ry="8" width="56" height="16" fill="rgba(26,18,14,0.52)" />
            <text x="${centerX}" y="${labelY + 11}" text-anchor="middle" font-size="10" fill="rgba(255,251,247,0.96)">${name}</text>
          </g>
        `;
      }

      const fallback = escapeHtml((localizedName || "?").slice(0, 1));
      return `
        <g opacity="${isActive ? "1" : "0.88"}">
          <rect x="${x}" y="${y}" rx="14" ry="14" width="68" height="94" fill="rgba(255,248,242,0.24)" stroke="rgba(255,255,255,0.22)" />
          <text x="${centerX}" y="${y + 56}" text-anchor="middle" font-size="28" font-weight="700" fill="rgba(255,251,247,0.95)">${fallback}</text>
          <rect x="${centerX - 28}" y="${labelY}" rx="8" ry="8" width="56" height="16" fill="rgba(26,18,14,0.52)" />
          <text x="${centerX}" y="${labelY + 11}" text-anchor="middle" font-size="10" fill="rgba(255,251,247,0.96)">${name}</text>
        </g>
      `;
    })
    .join("");

  const speaker = escapeHtml(snapshot.visualState?.speakerName ?? snapshot.sceneName ?? "Canvasia Engine");
  const dialogue = escapeHtml(truncateText(snapshot.visualState?.dialogueText ?? "这个节点没有正文。", 34));
  const scene = escapeHtml(snapshot.visualState?.backgroundName ?? snapshot.sceneName ?? "未设置背景");
  const block = escapeHtml(snapshot.completed ? "路线结束" : getBlockLabel(snapshot.blockType));
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
      <defs>
        <linearGradient id="thumbOverlay" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stop-color="rgba(26,18,14,0.10)" />
          <stop offset="100%" stop-color="rgba(26,18,14,0.64)" />
        </linearGradient>
      </defs>
      <rect width="${width}" height="${height}" fill="#6d4b3b" />
      ${
        backgroundUrl
          ? `<image href="${escapeHtml(backgroundUrl)}" width="${width}" height="${height}" preserveAspectRatio="xMidYMid slice" />`
          : `<rect width="${width}" height="${height}" fill="#775444" />`
      }
      <rect width="${width}" height="${height}" fill="url(#thumbOverlay)" />
      <rect x="12" y="12" rx="12" ry="12" width="116" height="20" fill="rgba(255,248,242,0.18)" />
      <text x="22" y="26" font-size="10" fill="rgba(255,251,247,0.96)">${scene}</text>
      <rect x="${width - 92}" y="12" rx="12" ry="12" width="80" height="20" fill="rgba(255,248,242,0.18)" />
      <text x="${width - 52}" y="26" text-anchor="middle" font-size="10" fill="rgba(255,251,247,0.96)">${block}</text>
      ${spriteMarkup}
      <rect x="12" y="${height - 56}" rx="14" ry="14" width="${width - 24}" height="44" fill="rgba(24,16,12,0.42)" />
      <text x="24" y="${height - 32}" font-size="13" font-weight="700" fill="rgba(255,251,247,0.98)">${speaker}</text>
      <text x="24" y="${height - 16}" font-size="11" fill="rgba(255,251,247,0.9)">${dialogue}</text>
    </svg>
  `;

  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`;
}

function getSaveBackdropStyle(snapshot) {
  const backgroundAssetId = snapshot?.visualState?.backgroundAssetId ?? null;
  const backgroundUrl = getAssetUrl(backgroundAssetId);

  if (backgroundUrl) {
    return `background: linear-gradient(180deg, rgba(28, 18, 14, 0.12), rgba(28, 18, 14, 0.34)), url("${escapeHtml(
      encodeURI(backgroundUrl)
    )}") center / cover no-repeat;`;
  }

  return `background: ${getBackdropStyle(backgroundAssetId)};`;
}

function renderSaveCast(snapshot) {
  const visibleCharacters = [...(snapshot?.visualState?.visibleCharacters ?? [])]
    .sort((left, right) => getPositionOrder(left.position) - getPositionOrder(right.position))
    .slice(0, 3);

  if (!visibleCharacters.length) {
    return `<div class="save-slot-cast-empty">当前没有角色出场</div>`;
  }

  return visibleCharacters
    .map((characterState) => {
      const spriteAssetId = getSpriteAssetId(characterState.characterId, characterState.expressionId);
      const spriteUrl = getAssetUrl(spriteAssetId);
      const isActive = snapshot?.visualState?.activeCharacterId === characterState.characterId;
      const localizedName = getCharacterName(characterState.characterId);
      const artMarkup = spriteUrl
        ? `<div class="save-slot-character-art has-image" style="background-image:url('${escapeHtml(
            encodeURI(spriteUrl)
          )}')"></div>`
        : `<div class="save-slot-character-art">${escapeHtml(
            (localizedName || "?").slice(0, 1)
          )}</div>`;

      return `
        <div class="save-slot-character ${isActive ? "is-active" : ""}" data-position="${escapeHtml(
          characterState.position ?? "center"
        )}">
          ${artMarkup}
          <span>${escapeHtml(localizedName)}</span>
        </div>
      `;
    })
    .join("");
}

function renderSaveVisualSummary(slot) {
  const snapshot = getSaveSlotSnapshot(slot);

  if (!snapshot) {
    return `
      <div class="save-slot-preview is-empty">
        <strong>还没有保存画面</strong>
        <span>到达关键节点后，这里会显示这一格的大致舞台状态。</span>
      </div>
    `;
  }

  const blockLabel = snapshot.completed ? "路线结束" : getBlockLabel(snapshot.blockType);
  const stageTitle = snapshot.visualState?.speakerName || snapshot.sceneName || "Canvasia Engine";
  const stageText = truncateText(snapshot.visualState?.dialogueText ?? "这个节点没有正文。", 38);
  const thumbnailUrl = slot?.thumbnailDataUrl || buildSaveThumbnailDataUrl(snapshot);

  return `
    <div class="save-slot-preview">
      <div
        class="save-slot-stage ${thumbnailUrl ? "has-thumbnail" : ""}"
        style="${
          thumbnailUrl
            ? `background-image:url('${escapeHtml(thumbnailUrl)}'); background-size:cover; background-position:center;`
            : getSaveBackdropStyle(snapshot)
        }"
      >
        <div class="save-slot-stage-head">
          <span class="save-slot-scene">${escapeHtml(
            snapshot.visualState?.backgroundName ?? snapshot.sceneName ?? "未设置背景"
          )}</span>
          <span class="save-slot-block">${escapeHtml(blockLabel)}</span>
        </div>
        <div class="save-slot-cast">${renderSaveCast(snapshot)}</div>
        <div class="save-slot-stage-caption">
          <strong>${escapeHtml(stageTitle)}</strong>
          <span>${escapeHtml(stageText)}</span>
        </div>
      </div>
    </div>
  `;
}

function quickSaveCurrent() {
  if (!state.started || !state.session) {
    return false;
  }

  state.quickSave = {
    savedAt: new Date().toISOString(),
    session: deepCloneRuntimeData(state.session),
    thumbnailDataUrl: buildSaveThumbnailDataUrl(getCurrentSnapshot()),
  };
  persistQuickSave();
  renderStartResumeSummary();
  renderPlaybackControls(getCurrentSnapshot());
  return true;
}

function quickLoadCurrent() {
  const session = sanitizeStoredSession(state.quickSave?.session);

  if (!session) {
    return false;
  }

  stopMusic();
  stopRuntimeTypewriter();
  stopRuntimeAutoAdvance();
  stopOneShotAudio();
  stopVoicePlayback();
  state.started = true;
  state.session = session;
  state.lastRenderedStepKey = null;
  state.systemMenuOpen = false;
  state.returnTitleConfirmOpen = false;
  state.locationDialogOpen = false;
  state.relationDialogOpen = false;
  persistAutoResume();
  refs.startOverlay.hidden = true;
  refs.restartButton.disabled = false;
  state.saveDialogOpen = false;
  renderLocationDialog();
  renderRelationDialog();
  renderRuntime();
  return true;
}

function requestSaveSlot(rawIndex) {
  const slotIndex = getSafeSaveSlotIndex(rawIndex);

  if (slotIndex == null || !state.started || !state.session) {
    return false;
  }

  if (!state.saveSlots[slotIndex]) {
    return saveCurrentSlot(rawIndex);
  }

  return openSaveConfirmDialog({
    type: "overwrite-slot",
    slotIndex,
  });
}

function requestSaveSlotClear(rawIndex) {
  const slotIndex = getSafeSaveSlotIndex(rawIndex);

  if (slotIndex == null || !state.saveSlots[slotIndex]) {
    return false;
  }

  return openSaveConfirmDialog({
    type: "clear-slot",
    slotIndex,
  });
}

function requestQuickSaveClear() {
  if (!state.quickSave) {
    return false;
  }

  return openSaveConfirmDialog({
    type: "clear-quick-save",
  });
}

function requestAutoResumeClear() {
  if (!state.autoResume) {
    return false;
  }

  return openSaveConfirmDialog({
    type: "clear-auto-resume",
  });
}

function getSaveConfirmContent(intent = state.saveConfirmIntent) {
  if (!intent) {
    return {
      title: "确认执行这个操作",
      summary: "这个操作会直接改动当前正式存档记录。",
    };
  }

  if (intent.type === "overwrite-slot") {
    const slotNumber = intent.slotIndex + 1;
    return {
      title: `确认覆盖正式存档 ${slotNumber}`,
      summary: `这一格现在是：${getSaveSlotSummary(
        state.saveSlots[intent.slotIndex]
      )}。确认后，会改成当前节点：${getSaveSlotSummary({
        session: state.session,
      })}。`,
    };
  }

  if (intent.type === "clear-slot") {
    const slotNumber = intent.slotIndex + 1;
    return {
      title: `确认清空正式存档 ${slotNumber}`,
      summary: `这一格现在是：${getSaveSlotSummary(
        state.saveSlots[intent.slotIndex]
      )}。确认后，这一格会被清空。`,
    };
  }

  if (intent.type === "clear-quick-save") {
    return {
      title: "确认清空快速存档",
      summary: `当前快速存档是：${getSaveSlotSummary(
        state.quickSave
      )}。确认后，这个临时打点会被删除。`,
    };
  }

  if (intent.type === "clear-auto-resume") {
    return {
      title: "确认清空自动续玩记录",
      summary: `当前自动续玩会回到：${getSaveSlotSummary(
        state.autoResume
      )}。确认后，下次就不能直接从这里继续试玩了。`,
    };
  }

  return {
    title: "确认执行这个操作",
    summary: "这个操作会直接改动当前正式存档记录。",
  };
}

function openSaveConfirmDialog(intent) {
  if (!intent) {
    return false;
  }

  state.returnTitleConfirmOpen = false;
  state.saveConfirmIntent = intent;
  state.saveConfirmOpen = true;
  renderReturnTitleDialog();
  renderSaveConfirmDialog();
  return true;
}

function closeSaveConfirmDialog() {
  if (!state.saveConfirmOpen && !state.saveConfirmIntent) {
    return false;
  }

  state.saveConfirmOpen = false;
  state.saveConfirmIntent = null;
  renderSaveConfirmDialog();
  return true;
}

function confirmSaveIntent() {
  const intent = state.saveConfirmIntent;

  if (!intent) {
    return false;
  }

  state.saveConfirmOpen = false;
  state.saveConfirmIntent = null;
  renderSaveConfirmDialog();

  if (intent.type === "overwrite-slot") {
    return saveCurrentSlot(intent.slotIndex + 1);
  }

  if (intent.type === "clear-slot") {
    return clearSaveSlot(intent.slotIndex + 1);
  }

  if (intent.type === "clear-quick-save") {
    return clearQuickSave();
  }

  if (intent.type === "clear-auto-resume") {
    clearStoredAutoResume();
    renderStartResumeSummary();
    renderPlaybackControls(getCurrentSnapshot());
    return true;
  }

  return false;
}

function clearQuickSave() {
  if (!state.quickSave) {
    return false;
  }

  clearStoredQuickSave();
  renderStartResumeSummary();
  renderPlaybackControls(getCurrentSnapshot());
  return true;
}

function getSystemMenuSummary() {
  const snapshot = getCurrentSnapshot();

  if (snapshot) {
    return `当前停在：${getSaveSlotSummary({ session: state.session })}`;
  }

  if (state.autoResume) {
    return `当前还没进入试玩，上次停留位置：${getSaveSlotSummary(state.autoResume)}`;
  }

  return "这里统一管理正式存档、快速存档、设置，以及返回标题页。";
}

function openSystemMenu() {
  state.saveDialogOpen = false;
  state.returnTitleConfirmOpen = false;
  state.saveConfirmOpen = false;
  state.saveConfirmIntent = null;
  state.profileDialogOpen = false;
  state.voiceReplayDialogOpen = false;
  state.achievementDialogOpen = false;
  state.chapterDialogOpen = false;
  state.locationDialogOpen = false;
  state.relationDialogOpen = false;
  state.characterDialogOpen = false;
  state.endingDialogOpen = false;
  state.galleryDialogOpen = false;
  state.musicRoomDialogOpen = false;
  stopMusicRoomPreview();
  stopVoiceReplayPreview({ rerender: false });
  state.systemMenuOpen = true;
  stopRuntimeAutoAdvance();
  renderProfileDialog();
  renderVoiceReplayDialog();
  renderAchievementDialog();
  renderChapterDialog();
  renderLocationDialog();
  renderRelationDialog();
  renderCharacterDialog();
  renderEndingDialog();
  renderGalleryDialog();
  renderMusicRoomDialog();
  renderSaveDialog();
  renderReturnTitleDialog();
  renderSaveConfirmDialog();
  renderSystemMenu();
  return true;
}

function closeSystemMenu() {
  if (!state.systemMenuOpen) {
    return false;
  }

  state.systemMenuOpen = false;
  renderSystemMenu();
  return true;
}

function openReturnTitleDialog() {
  state.saveDialogOpen = false;
  state.saveConfirmOpen = false;
  state.saveConfirmIntent = null;
  state.returnTitleConfirmOpen = true;
  renderSaveDialog();
  renderReturnTitleDialog();
  renderSaveConfirmDialog();
  return true;
}

function closeReturnTitleDialog() {
  if (!state.returnTitleConfirmOpen) {
    return false;
  }

  state.returnTitleConfirmOpen = false;
  renderReturnTitleDialog();
  return true;
}

function confirmReturnToTitle() {
  finalizePlayerSession({ silent: true });
  const profile = state.playerProfile ?? sanitizePlayerProfile(null);
  profile.returnToTitleCount += 1;
  state.playerProfile = profile;
  persistPlayerProfile();
  stopMusicRoomPreview();
  stopVoiceReplayPreview({ rerender: false });
  state.saveDialogOpen = false;
  state.systemMenuOpen = false;
  state.profileDialogOpen = false;
  state.voiceReplayDialogOpen = false;
  state.achievementDialogOpen = false;
  state.chapterDialogOpen = false;
  state.locationDialogOpen = false;
  state.relationDialogOpen = false;
  state.characterDialogOpen = false;
  state.endingDialogOpen = false;
  state.galleryDialogOpen = false;
  state.musicRoomDialogOpen = false;
  state.returnTitleConfirmOpen = false;
  state.saveConfirmOpen = false;
  state.saveConfirmIntent = null;
  state.started = false;
  state.session = null;
  state.lastRenderedStepKey = null;
  state.currentVoiceStepKey = null;
  renderSaveDialog();
  renderSystemMenu();
  renderProfileDialog();
  renderVoiceReplayDialog();
  renderAchievementDialog();
  renderChapterDialog();
  renderLocationDialog();
  renderRelationDialog();
  renderCharacterDialog();
  renderEndingDialog();
  renderGalleryDialog();
  renderMusicRoomDialog();
  renderOperationGuideDialog();
  renderReturnTitleDialog();
  renderSaveConfirmDialog();
  renderBeforeStart();
  refreshPlayerProfileUi();
  return true;
}

function getSafeSaveDialogMode(rawMode) {
  return rawMode === "load" ? "load" : "save";
}

function openSaveDialog(rawMode = "save") {
  state.systemMenuOpen = false;
  state.returnTitleConfirmOpen = false;
  state.saveConfirmOpen = false;
  state.saveConfirmIntent = null;
  state.profileDialogOpen = false;
  state.voiceReplayDialogOpen = false;
  state.achievementDialogOpen = false;
  state.chapterDialogOpen = false;
  state.locationDialogOpen = false;
  state.relationDialogOpen = false;
  state.characterDialogOpen = false;
  state.endingDialogOpen = false;
  state.galleryDialogOpen = false;
  state.musicRoomDialogOpen = false;
  stopMusicRoomPreview();
  stopVoiceReplayPreview({ rerender: false });
  state.saveDialogMode = getSafeSaveDialogMode(rawMode);
  state.saveDialogPage = getSafeSaveDialogPage(state.saveDialogPage);
  state.saveDialogOpen = true;
  stopRuntimeAutoAdvance();
  renderProfileDialog();
  renderVoiceReplayDialog();
  renderAchievementDialog();
  renderChapterDialog();
  renderLocationDialog();
  renderRelationDialog();
  renderCharacterDialog();
  renderEndingDialog();
  renderGalleryDialog();
  renderMusicRoomDialog();
  renderSystemMenu();
  renderReturnTitleDialog();
  renderSaveConfirmDialog();
  renderSaveDialog();
  return true;
}

function closeSaveDialog() {
  if (!state.saveDialogOpen) {
    return false;
  }

  state.saveDialogOpen = false;
  renderSaveDialog();
  return true;
}

function setSaveDialogMode(rawMode) {
  const nextMode = getSafeSaveDialogMode(rawMode);

  if (!state.saveDialogOpen) {
    state.saveDialogOpen = true;
  }

  state.saveDialogMode = nextMode;
  stopRuntimeAutoAdvance();
  renderSaveDialog();
  return true;
}

function setSaveDialogPage(rawPage) {
  const nextPage = getSafeSaveDialogPage(rawPage);

  if (!state.saveDialogOpen) {
    state.saveDialogOpen = true;
  }

  if (state.saveDialogPage === nextPage) {
    renderSaveDialog();
    return false;
  }

  state.saveDialogPage = nextPage;
  renderSaveDialog();
  return true;
}

function getSaveDialogSummary() {
  const mode = getSafeSaveDialogMode(state.saveDialogMode);
  const snapshot = getCurrentSnapshot();

  if (mode === "save") {
    if (!state.started || !snapshot) {
      return "当前还没有开始试玩，进入剧情后即可保存关键节点。";
    }

    return `当前节点：${getSaveSlotSummary({
      session: state.session,
    })} · 第 ${getSafeSaveDialogPage(state.saveDialogPage) + 1} / ${getSaveDialogPageCount()} 页`;
  }

  const hasManualSlots = state.saveSlots.some(Boolean);
  if (state.autoResume && hasManualSlots) {
    return `可继续上次试玩，也可从多页正式存档中选择一个读回。当前在第 ${
      getSafeSaveDialogPage(state.saveDialogPage) + 1
    } 页。`;
  }

  if (state.autoResume) {
    return "当前只有自动续玩记录，可先继续上次试玩，或稍后再保存正式节点。";
  }

  if (hasManualSlots) {
    return `从多页正式存档里选一个读回去，适合回头重试关键分支。当前在第 ${
      getSafeSaveDialogPage(state.saveDialogPage) + 1
    } 页。`;
  }

  return "当前还没有正式存档，可在关键剧情点保存节点。";
}

function renderFormalSaveSlotCard(slotNumber, slot, mode, options = {}) {
  const hasSave = Boolean(slot);
  const canSave = Boolean(options.canSave);
  const actionLabel = mode === "save" ? (hasSave ? "覆盖这个存档" : "存到这里") : "读这个点";
  const actionName = mode === "save" ? "save" : "load";
  const actionDisabled = mode === "save" ? !canSave : !hasSave;

  return `
    <article class="save-slot-card save-dialog-slot-card ${hasSave ? "" : "is-empty"}">
      ${renderSaveVisualSummary(slot)}
      <div class="save-slot-meta">
        <strong>存档 ${slotNumber}</strong>
        <span class="save-slot-time">${hasSave ? `保存时间：${escapeHtml(formatDate(slot.savedAt))}` : "还没有存档"}</span>
        <p>${escapeHtml(getSaveSlotSummary(slot))}</p>
        <p>${escapeHtml(hasSave ? `变量：${getVariableSummary(getSaveSlotSnapshot(slot)?.variables)}` : "变量还是初始状态。")}</p>
      </div>
      <div class="save-slot-actions">
        <button
          class="pill-button"
          type="button"
          data-${actionName}-slot="${slotNumber}"
          ${actionDisabled ? "disabled" : ""}
        >
          ${actionLabel}
        </button>
        <button
          class="pill-button"
          type="button"
          data-clear-slot="${slotNumber}"
          ${hasSave ? "" : "disabled"}
        >
          清空
        </button>
      </div>
    </article>
  `;
}

function renderSaveDialogPager() {
  const pageCount = getSaveDialogPageCount();
  const currentPage = getSafeSaveDialogPage(state.saveDialogPage);

  if (pageCount <= 1) {
    return "";
  }

  return `
    <div class="save-dialog-pager">
      <button
        class="pill-button"
        type="button"
        data-save-page="${currentPage - 1}"
        ${currentPage <= 0 ? "disabled" : ""}
      >
        上一页
      </button>
      <div class="save-dialog-page-list">
        ${Array.from({ length: pageCount }, (_, index) => {
          const start = index * SAVE_DIALOG_PAGE_SIZE + 1;
          const end = Math.min(getProjectFormalSaveSlotCount(), start + SAVE_DIALOG_PAGE_SIZE - 1);
          return `
            <button
              class="pill-button ${index === currentPage ? "" : "is-secondary"}"
              type="button"
              data-save-page="${index}"
            >
              ${start}-${end}
            </button>
          `;
        }).join("")}
      </div>
      <button
        class="pill-button"
        type="button"
        data-save-page="${currentPage + 1}"
        ${currentPage >= pageCount - 1 ? "disabled" : ""}
      >
        下一页
      </button>
    </div>
  `;
}

function renderSaveDialog() {
  if (!refs.saveDialog || !refs.saveDialogSlotList || !refs.saveDialogSummary) {
    return;
  }

  const mode = getSafeSaveDialogMode(state.saveDialogMode);
  const canSave = Boolean(state.started && state.session && getCurrentSnapshot());
  const currentPage = getSafeSaveDialogPage(state.saveDialogPage);
  const pageStartIndex = currentPage * SAVE_DIALOG_PAGE_SIZE;
  const pageSlots = state.saveSlots.slice(pageStartIndex, pageStartIndex + SAVE_DIALOG_PAGE_SIZE);

  refs.saveDialog.hidden = !state.saveDialogOpen;
  refs.saveDialog.classList.toggle("is-visible", state.saveDialogOpen);
  refs.saveDialogTitle.textContent = mode === "save" ? "正式存档" : "正式读档";
  refs.saveDialogSummary.textContent = getSaveDialogSummary();
  refs.saveDialogSaveModeButton?.classList.toggle("is-secondary", mode !== "save");
  refs.saveDialogLoadModeButton?.classList.toggle("is-secondary", mode !== "load");

  const quickSaveCard = `
    <article class="save-slot-card save-dialog-slot-card save-dialog-feature ${state.quickSave ? "" : "is-empty"}">
      ${renderSaveVisualSummary(state.quickSave)}
      <div class="save-slot-meta">
        <strong>快速存档</strong>
        <span class="save-slot-time">${
          state.quickSave ? `记录时间：${escapeHtml(formatDate(state.quickSave.savedAt))}` : "还没有快速存档"
        }</span>
        <p>${escapeHtml(getSaveSlotSummary(state.quickSave))}</p>
        <p>${escapeHtml(
          state.quickSave
            ? `变量：${getVariableSummary(getSaveSlotSnapshot(state.quickSave)?.variables)}`
            : "适合临时打点，后续可快速重试当前分支。"
        )}</p>
      </div>
      <div class="save-slot-actions">
        <button
          class="pill-button"
          type="button"
          data-${mode === "save" ? "quick-save" : "quick-load"}
          ${mode === "save" ? (canSave ? "" : "disabled") : state.quickSave ? "" : "disabled"}
        >
          ${mode === "save" ? "覆盖快速存档" : "快速读档"}
        </button>
        <button
          class="pill-button"
          type="button"
          data-clear-quick-save
          ${state.quickSave ? "" : "disabled"}
        >
          清空快速存档
        </button>
      </div>
    </article>
  `;

  const autoResumeCard =
    mode === "load"
      ? `
        <article class="save-slot-card save-dialog-slot-card save-dialog-feature ${state.autoResume ? "" : "is-empty"}">
          <div class="save-slot-meta">
            <strong>自动续玩</strong>
            <span class="save-slot-time">${
              state.autoResume ? `上次记录：${escapeHtml(formatDate(state.autoResume.savedAt))}` : "还没有自动续玩记录"
            }</span>
            <p>${escapeHtml(getSaveSlotSummary(state.autoResume))}</p>
            <p>${escapeHtml(
              state.autoResume
                ? `变量：${getVariableSummary(getSaveSlotSnapshot(state.autoResume)?.variables)}`
                : "关闭页面后，这里会记录上次看到的位置。"
            )}</p>
          </div>
          <div class="save-slot-actions">
            <button class="pill-button" type="button" data-load-auto-resume ${state.autoResume ? "" : "disabled"}>
              继续上次试玩
            </button>
            <button class="pill-button" type="button" data-clear-auto-resume ${state.autoResume ? "" : "disabled"}>
              清空记录
            </button>
          </div>
        </article>
      `
      : "";

  refs.saveDialogSlotList.innerHTML = `
    ${quickSaveCard}
    ${autoResumeCard}
    ${renderSaveDialogPager()}
    ${pageSlots.map((slot, index) =>
      renderFormalSaveSlotCard(pageStartIndex + index + 1, slot ?? null, mode, { canSave })
    ).join("")}
  `;
}

function renderSaveSlots() {
  if (!refs.saveSlotPanel) {
    return;
  }

  const canSave = Boolean(state.started && state.session);
  refs.saveSlotPanel.innerHTML = Array.from({ length: SAVE_SHORTCUT_COUNT }, (_, index) => {
    const slotNumber = index + 1;
    const slot = state.saveSlots[index] ?? null;
    const hasSave = Boolean(slot);

    return `
      <article class="save-slot-card">
        ${renderSaveVisualSummary(slot)}
        <div class="save-slot-meta">
          <strong>存档 ${slotNumber}</strong>
          <span class="save-slot-time">${hasSave ? `保存时间：${escapeHtml(formatDate(slot.savedAt))}` : "还没有存档"}</span>
          <p>${escapeHtml(getSaveSlotSummary(slot))}</p>
          <p>${escapeHtml(hasSave ? `变量：${getVariableSummary(getSaveSlotSnapshot(slot)?.variables)}` : "变量还是初始状态。")}</p>
        </div>
        <div class="save-slot-actions">
          <button class="pill-button" type="button" data-save-slot="${slotNumber}" ${canSave ? "" : "disabled"}>
            存到这里
          </button>
          <button class="pill-button" type="button" data-load-slot="${slotNumber}" ${hasSave ? "" : "disabled"}>
            读这个点
          </button>
          <button class="pill-button" type="button" data-clear-slot="${slotNumber}" ${hasSave ? "" : "disabled"}>
            清空
          </button>
        </div>
      </article>
    `;
  }).join("");
}

function saveCurrentSlot(rawIndex) {
  const slotIndex = getSafeSaveSlotIndex(rawIndex);

  if (slotIndex == null || !state.started || !state.session) {
    return false;
  }

  state.saveSlots[slotIndex] = {
    savedAt: new Date().toISOString(),
    session: deepCloneRuntimeData(state.session),
    thumbnailDataUrl: buildSaveThumbnailDataUrl(getCurrentSnapshot()),
  };
  persistSaveSlots();
  renderStartResumeSummary();
  renderPlaybackControls(getCurrentSnapshot());
  return true;
}

function loadSaveSlot(rawIndex) {
  const slotIndex = getSafeSaveSlotIndex(rawIndex);
  const savedSlot = slotIndex == null ? null : state.saveSlots[slotIndex];
  const session = sanitizeStoredSession(savedSlot?.session);

  if (slotIndex == null || !session) {
    return false;
  }

  stopMusic();
  stopRuntimeTypewriter();
  stopRuntimeAutoAdvance();
  stopOneShotAudio();
  stopVoicePlayback();
  stopMusicRoomPreview();
  stopVoiceReplayPreview({ rerender: false });
  state.started = true;
  state.session = session;
  state.lastRenderedStepKey = null;
  state.lastLocationArchiveStepKey = null;
  state.lastVoiceReplayStepKey = null;
  state.systemMenuOpen = false;
  state.profileDialogOpen = false;
  state.voiceReplayDialogOpen = false;
  state.locationDialogOpen = false;
  state.relationDialogOpen = false;
  state.returnTitleConfirmOpen = false;
  persistAutoResume();
  refs.startOverlay.hidden = true;
  refs.restartButton.disabled = false;
  state.saveDialogOpen = false;
  renderLocationDialog();
  renderRelationDialog();
  renderRuntime();
  return true;
}

function renderSystemMenu() {
  if (!refs.systemMenu || !refs.systemMenuSummary) {
    return;
  }

  const snapshot = getCurrentSnapshot();
  const hasLoadSource = Boolean(state.autoResume || state.saveSlots.some(Boolean) || state.quickSave);
  refs.systemMenu.hidden = !state.systemMenuOpen;
  refs.systemMenu.classList.toggle("is-visible", state.systemMenuOpen);
  refs.systemMenuSummary.textContent = getSystemMenuSummary();

  if (refs.systemMenuOpenSaveButton) {
    refs.systemMenuOpenSaveButton.disabled = !state.started || !snapshot;
  }

  if (refs.systemMenuOpenLoadButton) {
    refs.systemMenuOpenLoadButton.disabled = !hasLoadSource;
  }

  if (refs.systemMenuQuickSaveButton) {
    refs.systemMenuQuickSaveButton.disabled = !state.started || !snapshot;
  }

  if (refs.systemMenuQuickLoadButton) {
    refs.systemMenuQuickLoadButton.disabled = !state.quickSave;
  }

  if (refs.systemMenuReturnTitleButton) {
    refs.systemMenuReturnTitleButton.disabled = !state.started;
  }
}

function trackExtraUnlocks(snapshot) {
  if (!snapshot) {
    return;
  }

  const backgroundAsset = data.assetsById.get(snapshot.visualState?.backgroundAssetId ?? "");
  if (backgroundAsset?.type === "cg") {
    unlockExtraAsset("cg", backgroundAsset.id);
  }

  const musicAsset = data.assetsById.get(snapshot.visualState?.musicAssetId ?? "");
  if (musicAsset?.type === "bgm") {
    unlockExtraAsset("bgm", musicAsset.id);
  }
}

function trackChapterReplayUnlocks(snapshot) {
  if (!snapshot?.chapterId) {
    return;
  }

  unlockChapterReplayEntry(snapshot.chapterId);
}

function trackCharacterArchiveUnlocks(snapshot) {
  if (!snapshot) {
    return;
  }

  if (snapshot.blockType === "dialogue" && snapshot.block?.speakerId) {
    unlockCharacterArchiveEntry(snapshot.block.speakerId);
  }

  (snapshot.visualState?.visibleCharacters ?? []).forEach((characterState) => {
    unlockCharacterArchiveEntry(characterState.characterId);
  });
}

function renderReturnTitleDialog() {
  if (!refs.returnTitleDialog) {
    return;
  }

  refs.returnTitleDialog.hidden = !state.returnTitleConfirmOpen;
  refs.returnTitleDialog.classList.toggle("is-visible", state.returnTitleConfirmOpen);
}

function renderSaveConfirmDialog() {
  if (!refs.saveConfirmDialog || !refs.saveConfirmDialogTitle || !refs.saveConfirmDialogSummary) {
    return;
  }

  const content = getSaveConfirmContent();
  refs.saveConfirmDialogTitle.textContent = content.title;
  refs.saveConfirmDialogSummary.textContent = content.summary;
  refs.saveConfirmDialog.hidden = !state.saveConfirmOpen;
  refs.saveConfirmDialog.classList.toggle("is-visible", state.saveConfirmOpen);
}

function clearSaveSlot(rawIndex) {
  const slotIndex = getSafeSaveSlotIndex(rawIndex);

  if (slotIndex == null || !state.saveSlots[slotIndex]) {
    return false;
  }

  state.saveSlots[slotIndex] = null;
  persistSaveSlots();
  renderStartResumeSummary();
  renderPlaybackControls(getCurrentSnapshot());
  return true;
}

function createInitialPreviewVisualState() {
  return {
    backgroundAssetId: null,
    backgroundName: "未设置背景",
    backgroundTransitionEvent: null,
    musicName: "未播放",
    musicAssetId: null,
    musicVolume: 100,
    musicScope: null,
    musicFadeOutMs: 0,
    musicPreviousFadeOutMs: 0,
    particleEffect: null,
    screenShake: null,
    screenFlash: null,
    screenFade: null,
    cameraZoom: null,
    cameraPan: null,
    screenFilter: null,
    depthBlur: null,
    activeCharacterId: null,
    characterTransitionEvent: null,
    characterEmphasisEvent: null,
    visibleCharacters: [],
    speakerName: "Canvasia Engine",
    dialogueText: "点击“继续”后，这里会按导出时的剧情顺序推进。",
  };
}

function clonePreviewVisualState(visualState) {
  return {
    ...createInitialPreviewVisualState(),
    ...(visualState ?? {}),
    particleEffect: visualState?.particleEffect
      ? normalizeParticleEffectConfig(visualState.particleEffect)
      : null,
    musicScope: visualState?.musicScope
      ? {
          sceneId: String(visualState.musicScope.sceneId ?? ""),
          endMode: getSafeMusicEndMode(visualState.musicScope.endMode),
          endBlockId: String(visualState.musicScope.endBlockId ?? ""),
          fadeOutMs: getSafeAudioFadeMs(visualState.musicScope.fadeOutMs, 600),
        }
      : null,
    musicVolume: getSafeVolumePercent(visualState?.musicVolume, 100),
    musicFadeOutMs: getSafeAudioFadeMs(visualState?.musicFadeOutMs, 0),
    musicPreviousFadeOutMs: getSafeAudioFadeMs(visualState?.musicPreviousFadeOutMs, 0),
    backgroundTransitionEvent: visualState?.backgroundTransitionEvent
      ? {
          transition: getSafeTransition(visualState.backgroundTransitionEvent.transition),
          durationMs: getSafeTransitionDurationMs(visualState.backgroundTransitionEvent.durationMs),
        }
      : null,
    screenShake: visualState?.screenShake
      ? {
          intensity: getSafeShakeIntensity(visualState.screenShake.intensity),
          duration: getSafeEffectDuration(visualState.screenShake.duration),
        }
      : null,
    screenFlash: visualState?.screenFlash
      ? {
          color: getSafeFlashColor(visualState.screenFlash.color),
          intensity: getSafeFlashIntensity(visualState.screenFlash.intensity),
          duration: getSafeEffectDuration(visualState.screenFlash.duration),
        }
      : null,
    screenFade: visualState?.screenFade
      ? {
          color: getSafeFadeColor(visualState.screenFade.color),
          duration: getSafeEffectDuration(visualState.screenFade.duration),
        }
      : null,
    cameraZoom: visualState?.cameraZoom
      ? {
          action: getSafeCameraZoomAction(visualState.cameraZoom.action),
          strength: getSafeCameraZoomStrength(visualState.cameraZoom.strength),
          focus: getSafeCameraZoomFocus(visualState.cameraZoom.focus),
        }
      : null,
    cameraPan: visualState?.cameraPan
      ? {
          target: getSafeCameraPanTarget(visualState.cameraPan.target),
          strength: getSafeCameraPanStrength(visualState.cameraPan.strength),
        }
      : null,
    screenFilter: visualState?.screenFilter
      ? {
          preset: getSafeScreenFilterPreset(visualState.screenFilter.preset),
          strength: getSafeScreenFilterStrength(visualState.screenFilter.strength),
          grade: getSafeScreenColorGrade(visualState.screenFilter.grade),
        }
      : null,
    depthBlur: visualState?.depthBlur
      ? {
          focus: getSafeDepthBlurFocus(visualState.depthBlur.focus),
          strength: getSafeDepthBlurStrength(visualState.depthBlur.strength),
        }
      : null,
    activeCharacterId: visualState?.activeCharacterId ?? null,
    characterTransitionEvent: visualState?.characterTransitionEvent
      ? JSON.parse(JSON.stringify(visualState.characterTransitionEvent))
      : null,
    characterEmphasisEvent: visualState?.characterEmphasisEvent
      ? JSON.parse(JSON.stringify(visualState.characterEmphasisEvent))
      : null,
    visibleCharacters: (visualState?.visibleCharacters ?? []).map((characterState) => ({
      ...characterState,
    })),
  };
}

function clearTransientStageEffects(visualState) {
  if (!visualState) {
    return;
  }

  visualState.screenShake = null;
  visualState.screenFlash = null;
  visualState.backgroundTransitionEvent = null;
  visualState.activeCharacterId = null;
  visualState.characterTransitionEvent = null;
  visualState.characterEmphasisEvent = null;
  visualState.musicFadeOutMs = 0;
  visualState.musicPreviousFadeOutMs = 0;
}

function getSafeMusicEndMode(mode) {
  return Object.hasOwn(MUSIC_END_MODE_LABELS, mode) ? mode : "until_next_music";
}

function getMusicScopeFromBlock(block = {}, sceneId = "") {
  const endMode = getSafeMusicEndMode(block.endMode);
  const endBlockId = endMode === "after_block" ? String(block.endBlockId ?? "").trim() : "";
  return {
    sceneId: String(sceneId ?? ""),
    endMode: endBlockId ? endMode : endMode === "after_block" ? "until_next_music" : endMode,
    endBlockId,
    fadeOutMs: getSafeAudioFadeMs(block.fadeOutMs, 600),
  };
}

function clearPreviewMusicForScopeEnd(visualState, fadeOutMs = 0) {
  visualState.musicAssetId = null;
  visualState.musicName = "未播放";
  visualState.musicVolume = 100;
  visualState.musicScope = null;
  visualState.musicFadeOutMs = getSafeAudioFadeMs(fadeOutMs, 0);
}

function applyMusicScopeBeforeBlock(visualState, scene, blockIndex) {
  const scope = visualState?.musicScope;
  if (!scope || getSafeMusicEndMode(scope.endMode) === "until_next_music") {
    return;
  }

  const sceneId = String(scene?.id ?? "");
  const scopeSceneId = String(scope.sceneId ?? "");
  if (scopeSceneId && sceneId && scopeSceneId !== sceneId) {
    clearPreviewMusicForScopeEnd(visualState, scope.fadeOutMs);
    return;
  }

  if (getSafeMusicEndMode(scope.endMode) !== "after_block") {
    return;
  }

  const endBlockId = String(scope.endBlockId ?? "");
  const endIndex = (scene?.blocks ?? []).findIndex((item) => item.id === endBlockId);
  if (endIndex >= 0 && blockIndex > endIndex) {
    clearPreviewMusicForScopeEnd(visualState, scope.fadeOutMs);
  }
}

function applyMusicScopeForTerminal(visualState) {
  const scope = visualState?.musicScope;
  if (!scope || getSafeMusicEndMode(scope.endMode) === "until_next_music") {
    return;
  }
  clearPreviewMusicForScopeEnd(visualState, scope.fadeOutMs);
}

function createInitialVariableState() {
  return data.variables.reduce((result, variable) => {
    result[variable.id] = getVariableDefaultValue(variable.id);
    return result;
  }, {});
}

function clonePreviewVariables(variables) {
  return JSON.parse(JSON.stringify(variables ?? {}));
}

function buildPreviewSnapshot(sceneId, blockIndex, previousVisualState, previousVariables) {
  const scene = data.scenesById.get(getSafeSceneId(sceneId));
  const baseVisualState = clonePreviewVisualState(previousVisualState);
  const baseVariables = clonePreviewVariables(previousVariables);

  if (!scene) {
    return createPreviewTerminalSnapshot(
      {
        sceneId,
        sceneName: sceneId || "未知场景",
      },
      baseVisualState,
      baseVariables,
      "目标场景不存在，试玩在这里停下来了。"
    );
  }

  const block = scene.blocks?.[blockIndex];
  if (!block) {
    return createPreviewTerminalSnapshot(
      {
        sceneId: scene.id,
        sceneName: getSceneName(scene),
      },
      baseVisualState,
      baseVariables,
      "这段剧情已经结束了。"
    );
  }

  const nextVisualState = clonePreviewVisualState(baseVisualState);
  clearTransientStageEffects(nextVisualState);
  applyMusicScopeBeforeBlock(nextVisualState, scene, blockIndex);
  const nextVariables = clonePreviewVariables(baseVariables);
  const transitionTargetSceneId = applyBlockToPreviewState(block, nextVisualState, nextVariables, scene.id);

  return {
    sceneId: scene.id,
    sceneName: getSceneName(scene),
    blockIndex,
    blockId: block.id,
    blockType: block.type,
    block,
    visualState: nextVisualState,
    variables: nextVariables,
    choiceOptions: block.type === "choice" ? (block.options ?? []).map((option) => ({ ...option })) : [],
    transitionTargetSceneId,
    completed: false,
  };
}

function createPreviewTerminalSnapshot(scene, visualState, variables, message) {
  const nextVisualState = clonePreviewVisualState(visualState);
  clearTransientStageEffects(nextVisualState);
  applyMusicScopeForTerminal(nextVisualState);
  nextVisualState.speakerName = "试玩结束";
  nextVisualState.dialogueText = message;

  return {
    sceneId: scene.sceneId ?? null,
    sceneName: scene.sceneName ?? "试玩结束",
    blockIndex: -1,
    blockId: null,
    blockType: "complete",
    block: null,
    visualState: nextVisualState,
    variables: clonePreviewVariables(variables),
    choiceOptions: [],
    transitionTargetSceneId: null,
    completed: true,
  };
}

function createNextPreviewSnapshot(currentSnapshot) {
  if (currentSnapshot.transitionTargetSceneId) {
    return buildPreviewSnapshot(
      currentSnapshot.transitionTargetSceneId,
      0,
      currentSnapshot.visualState,
      currentSnapshot.variables
    );
  }

  const scene = data.scenesById.get(currentSnapshot.sceneId);
  const nextBlockIndex = currentSnapshot.blockIndex + 1;

  if (scene?.blocks?.[nextBlockIndex]) {
    return buildPreviewSnapshot(
      currentSnapshot.sceneId,
      nextBlockIndex,
      currentSnapshot.visualState,
      currentSnapshot.variables
    );
  }

  return createPreviewTerminalSnapshot(
    currentSnapshot,
    currentSnapshot.visualState,
    currentSnapshot.variables,
    "这条试玩路线已经结束了。"
  );
}

function applyBlockToPreviewState(block, visualState, variables, sceneId = "") {
  switch (block.type) {
    case "background": {
      const asset = data.assetsById.get(block.assetId);
      visualState.backgroundAssetId = block.assetId;
      visualState.backgroundName = asset?.name ?? block.assetId;
      visualState.backgroundTransitionEvent =
        getSafeTransition(block.transition) === "none"
          ? null
          : {
              transition: getSafeTransition(block.transition),
              durationMs: getSafeTransitionDurationMs(block.transitionDurationMs),
            };
      visualState.speakerName = "画面";
      visualState.dialogueText = `背景切换到：${asset?.name ?? block.assetId}`;
      return null;
    }
    case "music_play": {
      const asset = data.assetsById.get(block.assetId);
      if (visualState.musicAssetId && visualState.musicAssetId !== block.assetId) {
        visualState.musicPreviousFadeOutMs = getSafeAudioFadeMs(
          visualState.musicScope?.fadeOutMs,
          getSafeAudioFadeMs(block.fadeInMs, 0)
        );
      }
      visualState.musicAssetId = block.assetId;
      visualState.musicName = asset?.name ?? block.assetId;
      visualState.musicVolume = getSafeVolumePercent(block.volume, 100);
      visualState.musicScope = getMusicScopeFromBlock(block, sceneId);
      visualState.musicFadeOutMs = 0;
      visualState.speakerName = "音乐";
      visualState.dialogueText = `开始播放：${asset?.name ?? block.assetId}`;
      return null;
    }
    case "music_stop":
      visualState.musicFadeOutMs = getSafeAudioFadeMs(block.fadeOutMs, 600);
      visualState.musicAssetId = null;
      visualState.musicName = "未播放";
      visualState.musicVolume = 100;
      visualState.musicScope = null;
      visualState.speakerName = "音乐";
      visualState.dialogueText = "背景音乐停止了。";
      return null;
    case "video_play": {
      const asset = data.assetsById.get(block.assetId);
      visualState.speakerName = "视频播放";
      visualState.dialogueText = `${block.title || asset?.name || block.assetId || "未选择视频"} 会以 ${getVideoFitLabel(
        block.fit
      )} 方式播放。`;
      return null;
    }
    case "credits_roll":
      visualState.speakerName = "片尾字幕";
      visualState.dialogueText = `${block.title || "STAFF"} / ${getCreditsLines(block.lines).length} 行 / ${getSafeCreditsDuration(
        block.durationSeconds
      )} 秒。`;
      return null;
    case "wait":
      visualState.speakerName = "节奏停顿";
      visualState.dialogueText = `等待 ${getSafeWaitDurationSeconds(block.durationSeconds)} 秒。`;
      return null;
    case "particle_effect": {
      const action = getSafeParticleAction(block.action);
      if (action === "stop") {
        visualState.particleEffect = null;
        visualState.speakerName = "粒子特效";
        visualState.dialogueText = "当前场景里的粒子特效已经关闭。";
        return null;
      }
      visualState.particleEffect = normalizeParticleEffectConfig(block);
      visualState.speakerName = "粒子特效";
      visualState.dialogueText = `${getParticlePresetLabel(block.preset)}开始出现，${getParticleEmissionModeLabel(
        visualState.particleEffect.emissionMode
      )} / ${getParticleEmitterShapeLabel(visualState.particleEffect.emitterShape)} / ${getParticleSizeCurveLabel(
        visualState.particleEffect.sizeCurve
      )} / ${visualState.particleEffect.density} 颗。`;
      return null;
    }
    case "screen_shake":
      visualState.screenShake = {
        intensity: getSafeShakeIntensity(block.intensity),
        duration: getSafeEffectDuration(block.duration),
      };
      visualState.speakerName = "屏幕演出";
      visualState.dialogueText = `画面会${getShakeIntensityLabel(block.intensity)}地震动一下，持续 ${getEffectDurationLabel(
        block.duration
      )}。`;
      return null;
    case "screen_flash":
      visualState.screenFlash = {
        color: getSafeFlashColor(block.color),
        intensity: getSafeFlashIntensity(block.intensity),
        duration: getSafeEffectDuration(block.duration),
      };
      visualState.speakerName = "屏幕演出";
      visualState.dialogueText = `画面会出现一次${getFlashColorLabel(block.color)}，强度 ${getFlashIntensityLabel(
        block.intensity
      )}。`;
      return null;
    case "screen_fade": {
      const fadeAction = getSafeFadeAction(block.action);
      visualState.screenFade =
        fadeAction === "fade_out"
          ? {
              color: getSafeFadeColor(block.color),
              duration: getSafeEffectDuration(block.duration),
            }
          : null;
      visualState.speakerName = "画面过场";
      visualState.dialogueText =
        fadeAction === "fade_out"
          ? `画面会慢慢淡到${getFadeColorLabel(block.color)}，持续 ${getEffectDurationLabel(block.duration)}。`
          : `画面会从${getFadeColorLabel(block.color)}慢慢亮起，持续 ${getEffectDurationLabel(block.duration)}。`;
      return null;
    }
    case "camera_zoom": {
      const zoomAction = getSafeCameraZoomAction(block.action);
      visualState.cameraZoom =
        zoomAction === "reset"
          ? null
          : {
              action: zoomAction,
              strength: getSafeCameraZoomStrength(block.strength),
              focus: getSafeCameraZoomFocus(block.focus),
            };
      visualState.speakerName = "镜头演出";
      visualState.dialogueText =
        zoomAction === "reset"
          ? "镜头会恢复到正常大小。"
          : `镜头会${getCameraZoomActionLabel(block.action)}，强度 ${getCameraZoomStrengthLabel(
              block.strength
            )}，重点看${getCameraZoomFocusLabel(block.focus)}。`;
      return null;
    }
    case "camera_pan": {
      const target = getSafeCameraPanTarget(block.target);
      visualState.cameraPan =
        target === "center"
          ? null
          : {
              target,
              strength: getSafeCameraPanStrength(block.strength),
            };
      visualState.speakerName = "镜头演出";
      visualState.dialogueText =
        target === "center"
          ? "镜头会慢慢回到中间。"
          : `镜头会${getCameraPanTargetLabel(block.target)}，幅度 ${getCameraPanStrengthLabel(block.strength)}。`;
      return null;
    }
    case "screen_filter": {
      const filterAction = getSafeScreenFilterAction(block.action);
      visualState.screenFilter =
        filterAction === "clear"
          ? null
          : {
              preset: getSafeScreenFilterPreset(block.preset),
              strength: getSafeScreenFilterStrength(block.strength),
              grade: getSafeScreenColorGrade(block.grade),
            };
      visualState.speakerName = "画面滤镜";
      visualState.dialogueText =
        filterAction === "clear"
          ? "当前画面的回忆滤镜会在这里关闭。"
          : `画面会套上${getScreenFilterPresetLabel(block.preset)}，强度 ${getScreenFilterStrengthLabel(
              block.strength
            )}。`;
      return null;
    }
    case "depth_blur": {
      const blurAction = getSafeDepthBlurAction(block.action);
      visualState.depthBlur =
        blurAction === "clear"
          ? null
          : {
              focus: getSafeDepthBlurFocus(block.focus),
              strength: getSafeDepthBlurStrength(block.strength),
            };
      visualState.speakerName = "镜头景深";
      visualState.dialogueText =
        blurAction === "clear"
          ? "当前画面的景深模糊会在这里关闭。"
          : `画面会加上景深模糊，重点突出${getDepthBlurFocusLabel(block.focus)}，强度 ${getDepthBlurStrengthLabel(
              block.strength
            )}。`;
      return null;
    }
    case "character_show":
      upsertPreviewCharacter(visualState, {
        characterId: block.characterId,
        position: block.position ?? getDefaultCharacterPosition(block.characterId),
        expressionId: block.expressionId,
        expressionName: getExpressionName(block.characterId, block.expressionId),
        stage: getCharacterStageFromBlock(block),
      });
      if (getSafeTransition(block.transition) !== "none") {
        visualState.characterTransitionEvent = {
          mode: "show",
          characterId: block.characterId,
          transition: getSafeTransition(block.transition),
          durationMs: getSafeTransitionDurationMs(block.transitionDurationMs),
        };
      }
      visualState.speakerName = "角色演出";
      visualState.dialogueText = `${getCharacterName(block.characterId)} 出现在画面里。`;
      return null;
    case "character_hide": {
      const previousState =
        getPreviewCharacterState(visualState, block.characterId) ??
        createFallbackPreviewCharacterState(block.characterId);
      removePreviewCharacter(visualState, block.characterId);
      if (getSafeTransition(block.transition) !== "none") {
        visualState.characterTransitionEvent = {
          mode: "hide",
          characterState: previousState,
          transition: getSafeTransition(block.transition),
          durationMs: getSafeTransitionDurationMs(block.transitionDurationMs),
        };
      }
      visualState.speakerName = "角色演出";
      visualState.dialogueText = `${getCharacterName(block.characterId)} 离开了画面。`;
      return null;
    }
    case "dialogue":
      visualState.activeCharacterId = block.speakerId;
      visualState.characterEmphasisEvent = {
        mode: "dialogue",
        characterId: block.speakerId,
      };
      visualState.speakerName = getCharacterName(block.speakerId);
      visualState.dialogueText = getBlockText(block);
      upsertPreviewCharacter(visualState, {
        characterId: block.speakerId,
        position:
          getPreviewCharacterState(visualState, block.speakerId)?.position ??
          getDefaultCharacterPosition(block.speakerId),
        expressionId: block.expressionId,
        expressionName: getExpressionName(block.speakerId, block.expressionId),
        stage:
          getPreviewCharacterState(visualState, block.speakerId)?.stage ??
          getSafeCharacterStage(),
      });
      return null;
    case "narration":
      visualState.speakerName = "旁白";
      visualState.dialogueText = getBlockText(block);
      return null;
    case "choice":
      visualState.speakerName = "选择分支";
      visualState.dialogueText = "请选择一个选项继续试玩。";
      return null;
    case "variable_set": {
      const value = setPreviewVariableValue(variables, block.variableId, block.value);
      visualState.speakerName = "系统变量";
      visualState.dialogueText = `${getVariableName(block.variableId)} 设为 ${formatVariableValue(
        block.variableId,
        value
      )}`;
      return null;
    }
    case "variable_add": {
      const value = addPreviewVariableValue(variables, block.variableId, block.value);
      visualState.speakerName = "系统变量";
      visualState.dialogueText = `${getVariableName(block.variableId)} 现在是 ${formatVariableValue(
        block.variableId,
        value
      )}`;
      return null;
    }
    case "condition": {
      const targetSceneId = resolveConditionTargetSceneId(block, variables);
      visualState.speakerName = "系统判断";
      visualState.dialogueText = `判断完成，下一步会去：${getSceneName(
        data.scenesById.get(targetSceneId),
        targetSceneId
      )}`;
      return targetSceneId;
    }
    case "jump":
      visualState.speakerName = "场景跳转";
      visualState.dialogueText = `下一步会跳到：${getSceneName(
        data.scenesById.get(block.targetSceneId),
        block.targetSceneId
      )}`;
      return getSafeSceneId(block.targetSceneId, block.targetSceneId);
    case "sfx_play":
      visualState.speakerName = "音效";
      visualState.dialogueText = `播放音效：${data.assetsById.get(block.assetId)?.name ?? block.assetId}`;
      return null;
    default:
      visualState.speakerName = getBlockLabel(block.type);
      visualState.dialogueText = "这张卡片会参与试玩流程。";
      return null;
  }
}

function getPreviewCharacterState(visualState, characterId) {
  return (visualState.visibleCharacters ?? []).find((item) => item.characterId === characterId);
}

function upsertPreviewCharacter(visualState, characterState) {
  const visibleMap = new Map(
    (visualState.visibleCharacters ?? []).map((item) => [item.characterId, { ...item }])
  );
  visibleMap.set(characterState.characterId, { ...characterState });
  visualState.visibleCharacters = Array.from(visibleMap.values()).sort(
    (left, right) => getPositionOrder(left.position) - getPositionOrder(right.position)
  );
}

function removePreviewCharacter(visualState, characterId) {
  visualState.visibleCharacters = (visualState.visibleCharacters ?? []).filter(
    (characterState) => characterState.characterId !== characterId
  );
}

function createFallbackPreviewCharacterState(characterId) {
  const character = data.charactersById.get(characterId);
  const expressionId = character?.expressions?.[0]?.id ?? "";
  return {
    characterId,
    position: getDefaultCharacterPosition(characterId),
    expressionId,
    expressionName: getExpressionName(characterId, expressionId),
    stage: getSafeCharacterStage(),
  };
}

function getPreviewVariableValue(variables, variableId) {
  if (Object.hasOwn(variables, variableId)) {
    return normalizeVariableValue(variableId, variables[variableId]);
  }

  return getVariableDefaultValue(variableId);
}

function clampPreviewVariableNumber(variableId, value) {
  const [minValue, maxValue] = getVariableNumberBounds(variableId);
  let nextValue = value;

  if (minValue !== null) {
    nextValue = Math.max(nextValue, minValue);
  }

  if (maxValue !== null) {
    nextValue = Math.min(nextValue, maxValue);
  }

  return nextValue;
}

function setPreviewVariableValue(variables, variableId, value) {
  const nextValue = normalizeVariableValue(variableId, value);
  variables[variableId] =
    typeof nextValue === "number" ? clampPreviewVariableNumber(variableId, nextValue) : nextValue;
  return variables[variableId];
}

function addPreviewVariableValue(variables, variableId, delta) {
  const currentValue = getSafeNumber(getPreviewVariableValue(variables, variableId), 0);
  return setPreviewVariableValue(variables, variableId, currentValue + getSafeNumber(delta, 0));
}

function applyChoiceEffectsToPreviewVariables(variables, effects) {
  (effects ?? []).forEach((effect) => {
    if (effect.type === "variable_add") {
      addPreviewVariableValue(variables, effect.variableId, effect.value);
      return;
    }

    if (effect.type === "variable_set") {
      setPreviewVariableValue(variables, effect.variableId, effect.value);
    }
  });
}

function resolveConditionTargetSceneId(block, variables) {
  const matchedBranch = (block.branches ?? []).find((branch) =>
    (branch.when ?? []).every((rule) => evaluateConditionRule(rule, variables))
  );

  return getSafeSceneId(matchedBranch?.gotoSceneId ?? block.elseGotoSceneId, block.elseGotoSceneId);
}

function evaluateConditionRule(rule, variables) {
  const left = getPreviewVariableValue(variables, rule.variableId);
  const right = normalizeVariableValue(rule.variableId, rule.value);

  switch (rule.operator) {
    case ">":
      return left > right;
    case ">=":
      return left >= right;
    case "<":
      return left < right;
    case "<=":
      return left <= right;
    case "!=":
      return left !== right;
    case "==":
    default:
      return left === right;
  }
}

function renderRuntime() {
  const snapshot = getCurrentSnapshot();
  const session = state.session;

  if (!snapshot || !session) {
    renderBeforeStart();
    return;
  }

  trackExtraUnlocks(snapshot);
  trackChapterReplayUnlocks(snapshot);
  trackCharacterArchiveUnlocks(snapshot);
  unlockLocationArchiveEntry(snapshot);
  unlockNarrationArchiveEntry(snapshot);
  unlockRelationArchiveEntries(snapshot);
  unlockVoiceReplayEntry(snapshot);
  syncAchievementProgressFromState();
  refs.sceneChip.textContent = `${snapshot.sceneName} · 第 ${Math.max(snapshot.blockIndex + 1, 0)} 步`;
  refs.musicChip.textContent = `BGM：${snapshot.visualState.musicName ?? "未播放"}`;
  refs.backgroundLabel.textContent = snapshot.visualState.backgroundName ?? "未设置背景";
  refs.speakerName.textContent = snapshot.visualState.speakerName ?? "";
  refs.speakerName.style.color = getSpeakerColor(snapshot);
  refs.lineTypeTag.textContent = snapshot.completed ? "结束" : getBlockLabel(snapshot.blockType);
  refs.variablesPanel.innerHTML = renderVariables(snapshot.variables);
  refs.historyPanel.innerHTML = renderHistory(session);
  syncRuntimeDialoguePresentation(snapshot);
  refs.hintText.textContent = getPreviewHint(snapshot);
  const isBlockingMedia = isBlockingMediaSnapshot(snapshot);
  refs.continueButton.textContent = snapshot.completed
    ? "重新开始"
    : isBlockingMedia
      ? isMediaSnapshotSkippable(snapshot)
        ? snapshot.blockType === "credits_roll"
          ? "跳过片尾"
          : "跳过视频"
        : "播放中"
    : isRuntimeTypewriterActive()
      ? "显示整句"
      : "继续";
  refs.continueButton.disabled =
    (isBlockingMedia && !isMediaSnapshotSkippable(snapshot)) ||
    (!isRuntimeTypewriterActive() && snapshot.choiceOptions.length > 0);
  renderPlaybackControls(snapshot);
  renderStageVisual(snapshot);
  syncAudio(snapshot);
  syncVoice(snapshot);
  syncOneShotAudio(snapshot);
  syncVideoPlayback(snapshot);
  syncCreditsPlayback(snapshot);
  scheduleRuntimeAutoAdvance(snapshot);
}

function applyProjectResolutionStyles() {
  const resolution = getProjectResolution();
  document.documentElement.style.setProperty("--stage-width", String(resolution.width));
  document.documentElement.style.setProperty("--stage-height", String(resolution.height));
}

function renderVariables(variables) {
  return data.variables.length === 0
    ? renderEmpty("这个项目还没有变量。")
    : data.variables
        .map(
          (variable) => `
            <div class="info-row">
              <label>${escapeHtml(variable.name)}</label>
              <div class="value">${escapeHtml(
                formatVariableValue(
                  variable.id,
                  Object.hasOwn(variables ?? {}, variable.id) ? variables?.[variable.id] : getVariableDefaultValue(variable.id)
                )
              )}</div>
            </div>
          `
        )
        .join("");
}

function renderHistory(session) {
  const startIndex = Math.max(session.timeline.length - 12, 0);
  const rows = session.timeline
    .slice(startIndex)
    .map((snapshot, index) => {
      const absoluteIndex = startIndex + index;
      const number = absoluteIndex + 1;
      const title = snapshot.completed
        ? "试玩结束"
        : `${getBlockLabel(snapshot.blockType)} · ${snapshot.sceneName}`;
      const hasVoice = Boolean(getVoiceAssetId(snapshot));

      return `
        <article class="history-row ${absoluteIndex === session.position ? "is-selected" : ""}">
          <button class="history-main-button" type="button" data-history-index="${absoluteIndex}">
            <strong>${number}. ${escapeHtml(title)}</strong>
            <p>${escapeHtml(snapshot.visualState.dialogueText ?? "")}</p>
            <div class="meta">${escapeHtml(snapshot.visualState.speakerName ?? "系统")}</div>
          </button>
          <div class="history-actions">
            <button
              class="history-voice-button"
              type="button"
              data-history-voice-index="${absoluteIndex}"
              ${hasVoice ? "" : "disabled"}
            >
              重播语音
            </button>
          </div>
        </article>
      `;
    })
    .join("");

  return rows || renderEmpty("还没有历史记录。");
}

function renderChoiceButtons(snapshot) {
  if (!snapshot.choiceOptions.length) {
    return "";
  }

  return snapshot.choiceOptions
    .map(
      (option) => `
        <button class="choice-button" type="button" data-option-id="${escapeHtml(option.id)}">
          <strong>${escapeHtml(getChoiceText(option))}</strong>
          <span>${escapeHtml(isChoiceContinueTarget(option.gotoSceneId) ? "继续下一张卡" : `进入 ${getSceneName(data.scenesById.get(option.gotoSceneId), option.gotoSceneId)}`)}</span>
        </button>
      `
    )
    .join("");
}

function renderStageVisual(snapshot) {
  const visualState = snapshot.visualState;
  const backgroundAsset = data.assetsById.get(visualState.backgroundAssetId);
  const backgroundUrl = getAssetUrl(backgroundAsset?.id);

  refs.backgroundLayer.style.backgroundImage = backgroundUrl
    ? `linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.18)), url("${encodeURI(backgroundUrl)}")`
    : getBackdropStyle(visualState.backgroundAssetId);
  const backgroundTransition = visualState.backgroundTransitionEvent;
  refs.backgroundLayer.style.setProperty(
    "--background-transition-ms",
    `${getSafeTransitionDurationMs(backgroundTransition?.durationMs)}ms`
  );
  refs.backgroundLayer.dataset.transition = getSafeTransition(backgroundTransition?.transition ?? "none");
  refs.backgroundLayer.classList.remove("is-transitioning", "transition-fade");
  void refs.backgroundLayer.offsetWidth;
  if (backgroundTransition && getSafeTransition(backgroundTransition.transition) !== "none") {
    refs.backgroundLayer.classList.add("is-transitioning", `transition-${getSafeTransition(backgroundTransition.transition)}`);
  }
  refs.particleLayer.innerHTML = renderParticleEffectLayer(visualState.particleEffect, visualState);
  applyStageWorldPresentation(visualState);
  applyStageScreenEffects(visualState, snapshot.block);

  refs.spriteLayer.innerHTML = renderSpriteCards(visualState);

  refs.choiceList.querySelectorAll("[data-option-id]").forEach((button) => {
    button.addEventListener("click", () => choosePreviewOption(button.dataset.optionId));
  });
}

function renderSpriteCards(visualState) {
  const cards = [...(visualState.visibleCharacters ?? [])];

  if (visualState.characterTransitionEvent?.mode === "hide" && visualState.characterTransitionEvent.characterState) {
    cards.push({
      ...visualState.characterTransitionEvent.characterState,
      __ghostMode: "hide",
    });
  }

  return cards
    .sort((left, right) => getPositionOrder(left.position) - getPositionOrder(right.position))
    .map((characterState) =>
      renderSpriteCard(
        characterState,
        visualState.depthBlur,
        visualState.characterTransitionEvent,
        visualState.activeCharacterId,
        visualState.characterEmphasisEvent
      )
    )
    .join("");
}

function renderSpriteCard(
  characterState,
  depthBlur = null,
  characterTransitionEvent = null,
  activeCharacterId = null,
  characterEmphasisEvent = null
) {
  const spriteAssetId = getSpriteAssetId(characterState.characterId, characterState.expressionId);
  const spriteUrl = getAssetUrl(spriteAssetId);
  const localizedName = getCharacterName(characterState.characterId);
  const classes = ["sprite-card"];
  const isGhostHide = characterState.__ghostMode === "hide";
  const transition = characterTransitionEvent ? getSafeTransition(characterTransitionEvent.transition) : "none";
  const transitionDurationMs = characterTransitionEvent
    ? getSafeTransitionDurationMs(characterTransitionEvent.durationMs)
    : getSafeTransitionDurationMs();
  const stageStyle = `${getCharacterStageStyle(characterState.stage)}--sprite-transition-ms:${transitionDurationMs}ms;`;

  if (shouldBlurPlayerCharacter(characterState.position, depthBlur)) {
    classes.push("is-depth-muted");
    classes.push(`depth-strength-${getSafeDepthBlurStrength(depthBlur?.strength)}`);
  } else if (depthBlur) {
    classes.push("is-depth-focus");
  }

  if (characterTransitionEvent?.mode === "show" && characterTransitionEvent.characterId === characterState.characterId) {
    classes.push("is-entering");
  }

  if (isGhostHide) {
    classes.push("is-leaving");
  }

  classes.push("is-breathing");

  if (activeCharacterId === characterState.characterId) {
    classes.push("is-speaking");
  }

  if (characterEmphasisEvent?.characterId === characterState.characterId) {
    classes.push("is-emphasis");
  }

  const visual = spriteUrl
    ? `<img class="sprite-image" src="${escapeHtml(encodeURI(spriteUrl))}" alt="${escapeHtml(localizedName)}" />`
    : `<div class="sprite-fallback">${escapeHtml((localizedName || "?").slice(0, 1))}</div>`;

  return `
    <article class="${classes.join(" ")}" data-position="${escapeHtml(characterState.position)}" data-transition="${escapeHtml(transition)}" style="${stageStyle}">
      <div class="sprite-card-inner">
        <div class="sprite-visual-frame">${visual}</div>
        <div class="sprite-name">${escapeHtml(localizedName)}</div>
        <div class="sprite-expression">${escapeHtml(characterState.expressionName ?? "默认")}</div>
      </div>
    </article>
  `;
}

function syncAudio(snapshot) {
  const nextMusicAssetId = snapshot.visualState.musicAssetId ?? null;
  const targetVolume = getRuntimeMusicTargetVolume(snapshot);

  if (!nextMusicAssetId) {
    stopMusic({
      fadeOutMs: getSafeAudioFadeMs(snapshot.visualState?.musicFadeOutMs ?? snapshot.block?.fadeOutMs),
    });
    return;
  }

  if (state.currentMusicAssetId === nextMusicAssetId && state.bgmAudio) {
    state.bgmAudio.volume = targetVolume;
    return;
  }

  const fadeInMs = getSafeAudioFadeMs(snapshot.block?.fadeInMs);
  const previousFadeOutMs = getSafeAudioFadeMs(snapshot.visualState?.musicPreviousFadeOutMs, fadeInMs);
  fadeOutPreviousMusic(previousFadeOutMs);
  const musicUrl = getAssetUrl(nextMusicAssetId);

  if (!musicUrl) {
    state.currentMusicAssetId = nextMusicAssetId;
    return;
  }

  const audio = new Audio(encodeURI(musicUrl));
  audio.loop = true;
  audio.volume = fadeInMs > 0 ? 0 : targetVolume;
  audio.play().catch(() => {});
  state.bgmAudio = audio;
  state.currentMusicAssetId = nextMusicAssetId;

  if (fadeInMs > 0) {
    fadeAudioVolume(audio, {
      from: 0,
      to: targetVolume,
      durationMs: fadeInMs,
    });
  }
}

function getRuntimeMusicTargetVolume(snapshot) {
  return getRuntimeMusicTargetVolumeBase(state.playback, snapshot, {
    voiceActive: isRuntimeVoiceDuckingActive(),
  });
}

function getRuntimeSfxTargetVolume(volumePercent = 100) {
  return getRuntimeSfxTargetVolumeBase(state.playback, volumePercent);
}

function syncOneShotAudio(snapshot) {
  const stepKey = `${snapshot.sceneId}:${snapshot.blockId ?? "complete"}:${snapshot.blockIndex}`;

  if (state.lastRenderedStepKey === stepKey) {
    return;
  }

  state.lastRenderedStepKey = stepKey;

  if (snapshot.blockType !== "sfx_play") {
    return;
  }

  const soundUrl = getAssetUrl(snapshot.block?.assetId);
  if (!soundUrl) {
    return;
  }

  const audio = new Audio(encodeURI(soundUrl));
  audio._canvasiaSfxVolumePercent = getSafeVolumePercent(snapshot.block?.volume, 100);
  audio.volume = getRuntimeSfxTargetVolume(audio._canvasiaSfxVolumePercent);
  activeSfxAudios.add(audio);
  const cleanup = () => {
    activeSfxAudios.delete(audio);
  };
  audio.addEventListener("ended", cleanup, { once: true });
  audio.addEventListener("error", cleanup, { once: true });
  audio.play().catch(cleanup);
}

function syncVideoPlayback(snapshot) {
  if (snapshot?.blockType !== "video_play") {
    stopVideoPlayback();
    return;
  }

  const stepKey = getCurrentStepKey(snapshot);
  if (state.videoPlaybackStepKey === stepKey) {
    return;
  }

  stopVideoPlayback();
  stopCreditsPlayback();

  const block = snapshot.block ?? {};
  const asset = data.assetsById.get(block.assetId);
  const videoUrl = getAssetUrl(block.assetId);
  const title = block.title || asset?.name || "视频播放";
  const startTimeSeconds = getSafeVideoTime(block.startTimeSeconds, 0);
  const endTimeSeconds = getSafeVideoTime(block.endTimeSeconds, 0);

  state.videoPlaybackStepKey = stepKey;
  refs.videoOverlay.hidden = false;
  refs.videoOverlay.dataset.fit = getSafeVideoFit(block.fit);
  refs.videoOverlayTitle.textContent = title;
  refs.videoSkipButton.hidden = block.skippable === false;
  refs.runtimeVideo.controls = true;
  refs.runtimeVideo.volume = getSafeVideoVolume(block.volume) / 100;

  const finish = () => {
    if (state.videoPlaybackStepKey === stepKey) {
      finishVideoPlayback();
    }
  };
  const handleTimeUpdate = () => {
    if (endTimeSeconds > 0 && refs.runtimeVideo.currentTime >= endTimeSeconds) {
      finish();
    }
  };
  const handleLoadedMetadata = () => {
    if (startTimeSeconds > 0 && Number.isFinite(refs.runtimeVideo.duration)) {
      refs.runtimeVideo.currentTime = Math.min(startTimeSeconds, Math.max(refs.runtimeVideo.duration - 0.08, 0));
    }
  };

  refs.runtimeVideo.addEventListener("ended", finish);
  refs.runtimeVideo.addEventListener("error", finish);
  refs.runtimeVideo.addEventListener("loadedmetadata", handleLoadedMetadata);
  refs.runtimeVideo.addEventListener("timeupdate", handleTimeUpdate);
  state.videoPlaybackCleanup = () => {
    refs.runtimeVideo.removeEventListener("ended", finish);
    refs.runtimeVideo.removeEventListener("error", finish);
    refs.runtimeVideo.removeEventListener("loadedmetadata", handleLoadedMetadata);
    refs.runtimeVideo.removeEventListener("timeupdate", handleTimeUpdate);
  };

  if (!videoUrl) {
    refs.videoOverlayTitle.textContent = `${title}（视频文件缺失）`;
    refs.videoSkipButton.hidden = false;
    refs.runtimeVideo.removeAttribute("src");
    refs.runtimeVideo.load();
    const missingVideoTimer = window.setTimeout(finish, 1600);
    const cleanup = state.videoPlaybackCleanup;
    state.videoPlaybackCleanup = () => {
      if (typeof cleanup === "function") {
        cleanup();
      }
      window.clearTimeout(missingVideoTimer);
    };
    return;
  }

  refs.runtimeVideo.src = encodeURI(videoUrl);
  refs.runtimeVideo.load();
  refs.runtimeVideo.play().catch(() => {
    refs.videoOverlayTitle.textContent = `${title} · 点击视频画面播放`;
  });
}

function stopVideoPlayback() {
  if (typeof state.videoPlaybackCleanup === "function") {
    state.videoPlaybackCleanup();
  }

  state.videoPlaybackCleanup = null;
  state.videoPlaybackStepKey = null;

  if (refs.runtimeVideo) {
    refs.runtimeVideo.pause();
    refs.runtimeVideo.removeAttribute("src");
    refs.runtimeVideo.load();
  }

  if (refs.videoOverlay) {
    refs.videoOverlay.hidden = true;
  }
}

function finishVideoPlayback({ skipped = false } = {}) {
  const snapshot = getCurrentSnapshot();
  if (snapshot?.blockType !== "video_play") {
    stopVideoPlayback();
    return;
  }

  if (skipped && !isMediaSnapshotSkippable(snapshot)) {
    return;
  }

  stopVideoPlayback();
  movePreviewForward();
  renderRuntime();
}

function syncCreditsPlayback(snapshot) {
  if (snapshot?.blockType !== "credits_roll") {
    stopCreditsPlayback();
    return;
  }

  const stepKey = getCurrentStepKey(snapshot);
  if (state.creditsPlaybackStepKey === stepKey) {
    return;
  }

  stopCreditsPlayback();
  stopVideoPlayback();

  const block = snapshot.block ?? {};
  const durationSeconds = getSafeCreditsDuration(block.durationSeconds);
  const lines = getCreditsLines(block.lines);
  state.creditsPlaybackStepKey = stepKey;
  refs.creditsOverlay.hidden = false;
  refs.creditsOverlay.dataset.background = getSafeCreditsBackground(block.background);
  refs.creditsOverlay.style.setProperty("--credits-duration", `${durationSeconds}s`);
  refs.creditsSkipButton.hidden = block.skippable === false;
  refs.creditsRoll.innerHTML = `
    <div class="credits-roll-inner">
      <div class="credits-roll-kicker">Canvasia Engine</div>
      <h2>${escapeHtml(block.title || "STAFF")}</h2>
      ${block.subtitle ? `<p class="credits-roll-subtitle">${escapeHtml(block.subtitle)}</p>` : ""}
      <div class="credits-roll-lines">
        ${
          lines.length > 0
            ? lines.map((line) => `<p>${escapeHtml(line)}</p>`).join("")
            : "<p>感谢游玩。</p>"
        }
      </div>
    </div>
  `;
  state.creditsPlaybackTimer = window.setTimeout(() => {
    if (state.creditsPlaybackStepKey === stepKey) {
      finishCreditsPlayback();
    }
  }, durationSeconds * 1000);
}

function stopCreditsPlayback() {
  if (state.creditsPlaybackTimer) {
    window.clearTimeout(state.creditsPlaybackTimer);
  }

  state.creditsPlaybackTimer = null;
  state.creditsPlaybackStepKey = null;

  if (refs.creditsOverlay) {
    refs.creditsOverlay.hidden = true;
  }

  if (refs.creditsRoll) {
    refs.creditsRoll.innerHTML = "";
  }
}

function finishCreditsPlayback({ skipped = false } = {}) {
  const snapshot = getCurrentSnapshot();
  if (snapshot?.blockType !== "credits_roll") {
    stopCreditsPlayback();
    return;
  }

  if (skipped && !isMediaSnapshotSkippable(snapshot)) {
    return;
  }

  stopCreditsPlayback();
  movePreviewForward();
  renderRuntime();
}

function fadeOutPreviousMusic(fadeOutMs = 0) {
  const previousAudio = state.bgmAudio;
  state.bgmAudio = null;
  state.currentMusicAssetId = null;

  if (!previousAudio) {
    return;
  }

  const safeFadeOutMs = getSafeAudioFadeMs(fadeOutMs);
  if (safeFadeOutMs <= 0) {
    disposeAudio(previousAudio);
    return;
  }

  fadeAudioVolume(previousAudio, {
    from: previousAudio.volume,
    to: 0,
    durationMs: safeFadeOutMs,
    onComplete: () => disposeAudio(previousAudio),
  });
}

function stopMusic({ fadeOutMs = 0 } = {}) {
  fadeOutPreviousMusic(fadeOutMs);
  state.currentMusicAssetId = null;
}

function getPreviewHint(snapshot) {
  if (state.dialogHidden) {
    return "对话框现在是隐藏状态，点画面、按 H 或右键可以恢复。";
  }

  if (isRuntimeTypewriterActive()) {
    return "可点画面、按空格或回车，先显示整句台词。";
  }

  if (state.playback.autoPlay && snapshot.choiceOptions.length === 0 && !snapshot.completed) {
    return "自动播放已开启，当前段落会自动继续推进。";
  }

  if (state.playback.skipRead && snapshot.choiceOptions.length === 0 && !snapshot.completed) {
    return "跳过已读已开启，已经看过的内容会快速略过，遇到新句子会停下。";
  }

  if (snapshot.choiceOptions.length > 0) {
    return "需要先选择一个选项，剧情才会继续。";
  }

  if (snapshot.blockType === "video_play") {
    return snapshot.block?.skippable === false ? "视频播放完后会自动继续。" : "视频播放完会自动继续，也可以跳过视频。";
  }

  if (snapshot.blockType === "credits_roll") {
    return snapshot.block?.skippable === false ? "片尾字幕滚完后会自动继续。" : "片尾字幕滚完会自动继续，也可以跳过片尾。";
  }

  if (snapshot.blockType === "wait") {
    return `这里会停顿 ${getSafeWaitDurationSeconds(snapshot.block?.durationSeconds)} 秒；也可以点击或按空格提前继续。`;
  }

  if (snapshot.completed) {
    return "这条试玩路线已经结束了。";
  }

  if (snapshot.blockType === "condition") {
    return "下一步会按当前变量结果跳到对应场景。";
  }

  if (snapshot.blockType === "jump") {
    return "下一步会进入目标场景。";
  }

  return "可点画面或按空格 / 回车继续，按 R 重新开始，按 S 切换跳过已读，按 H 隐藏对话框。";
}

function getEntrySceneId() {
  return getSafeSceneId(data.project.entrySceneId);
}

function getProjectResolution() {
  const width = Number.parseInt(data.project?.resolution?.width ?? 1280, 10);
  const height = Number.parseInt(data.project?.resolution?.height ?? 720, 10);

  return {
    width: Number.isFinite(width) ? width : 1280,
    height: Number.isFinite(height) ? height : 720,
  };
}

function getSafeSceneId(sceneId, fallbackSceneId = null) {
  if (data.scenesById.has(sceneId)) {
    return sceneId;
  }

  if (fallbackSceneId && data.scenesById.has(fallbackSceneId)) {
    return fallbackSceneId;
  }

  return data.scenes[0]?.id ?? "";
}

function getCharacterName(characterId) {
  const character = data.charactersById.get(characterId);
  return getLocalizedValue(character, "displayName", characterId ?? "未命名角色");
}

function getPositionLabel(position) {
  return {
    left: "左侧",
    center: "中间",
    right: "右侧",
  }[position] ?? "中间";
}

function getVariableName(variableId) {
  return data.variablesById.get(variableId)?.name ?? variableId ?? "未命名变量";
}

function getSpeakerColor(snapshot) {
  if (snapshot.blockType === "dialogue") {
    return data.charactersById.get(snapshot.block?.speakerId)?.nameColor ?? "";
  }

  return "";
}

function getExpressionName(characterId, expressionId) {
  const character = data.charactersById.get(characterId);
  const expression = character?.expressions?.find((item) => item.id === expressionId);
  return expression?.name ?? expressionId ?? "默认";
}

function getSpriteAssetId(characterId, expressionId) {
  const character = data.charactersById.get(characterId);
  const expression = character?.expressions?.find((item) => item.id === expressionId);
  return expression?.spriteAssetId ?? character?.defaultSpriteId ?? null;
}

function getDefaultCharacterPosition(characterId) {
  return data.charactersById.get(characterId)?.defaultPosition ?? "center";
}

function getSafeTransition(transition) {
  return ["fade", "slide_left", "slide_right", "rise", "pop", "none"].includes(transition)
    ? transition
    : "fade";
}

function getSafeTransitionDurationMs(value, fallback = TRANSITION_DURATION_DEFAULT_MS) {
  const number = Number.parseFloat(value ?? "");
  const safeFallback = Number.isFinite(Number(fallback))
    ? clamp(Number(fallback), TRANSITION_DURATION_MIN_MS, TRANSITION_DURATION_MAX_MS)
    : TRANSITION_DURATION_DEFAULT_MS;
  return Math.round(
    clamp(Number.isFinite(number) ? number : safeFallback, TRANSITION_DURATION_MIN_MS, TRANSITION_DURATION_MAX_MS)
  );
}

function getSafeCharacterStage(source = {}) {
  const raw = source && typeof source === "object" ? source : {};
  return {
    offsetX: Math.round(clamp(getSafeNumber(raw.offsetX, 0), -60, 60)),
    offsetY: Math.round(clamp(getSafeNumber(raw.offsetY, 0), -45, 45)),
    scale: Math.round(clamp(getSafeNumber(raw.scale, 100), 45, 220)),
    opacity: Math.round(clamp(getSafeNumber(raw.opacity, 100), 0, 100)),
    layer: Math.round(clamp(getSafeNumber(raw.layer, 0), -10, 10)),
    flipX: getSafeBoolean(raw.flipX, false),
  };
}

function getCharacterStageFromBlock(block = {}) {
  return getSafeCharacterStage(block.stage ?? block.characterStage ?? {});
}

function getCharacterStageStyle(stageSource = {}) {
  const stage = getSafeCharacterStage(stageSource);
  return [
    `--sprite-offset-x:${stage.offsetX}%;`,
    `--sprite-offset-y:${stage.offsetY}%;`,
    `--sprite-scale:${(stage.scale / 100).toFixed(3)};`,
    `--sprite-opacity:${(stage.opacity / 100).toFixed(2)};`,
    `--sprite-layer:${stage.layer};`,
    `--sprite-flip-x:${stage.flipX ? -1 : 1};`,
    `z-index:${20 + stage.layer};`,
  ].join("");
}

function getPositionOrder(position) {
  if (position === "left") return 0;
  if (position === "center") return 1;
  if (position === "right") return 2;
  return 3;
}

function getAssetUrl(assetId) {
  const asset = data.assetsById.get(assetId);
  return asset?.isMissing ? null : asset?.exportUrl ?? null;
}

function getAssetTypeLabel(type) {
  const labels = {
    background: "背景",
    sprite: "立绘",
    cg: "CG",
    bgm: "音乐",
    sfx: "音效",
    voice: "语音",
    video: "视频",
    ui: "界面素材",
  };

  return labels[type] ?? type ?? "素材";
}

function getBlockLabel(type) {
  const labels = {
    background: "切换背景",
    dialogue: "台词",
    narration: "旁白",
    character_show: "显示角色",
    character_hide: "隐藏角色",
    music_play: "播放音乐",
    music_stop: "停止音乐",
    sfx_play: "播放音效",
    video_play: "播放视频",
    credits_roll: "片尾字幕",
    wait: "等待停顿",
    particle_effect: "粒子特效",
    screen_shake: "屏幕震动",
    screen_flash: "闪屏",
    screen_fade: "黑场淡入淡出",
    camera_zoom: "镜头推近拉远",
    camera_pan: "镜头平移",
    screen_filter: "回忆滤镜",
    depth_blur: "景深模糊",
    jump: "跳转",
    variable_set: "设置变量",
    variable_add: "修改变量",
    choice: "选项",
    condition: "条件判断",
    complete: "结束",
  };

  return labels[type] ?? type ?? "步骤";
}

function getSafeVideoFit(value) {
  return Object.hasOwn(VIDEO_FIT_LABELS, value) ? value : "contain";
}

function getVideoFitLabel(value) {
  return VIDEO_FIT_LABELS[getSafeVideoFit(value)] ?? VIDEO_FIT_LABELS.contain;
}

function getSafeVideoVolume(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return 100;
  }
  return Math.round(clamp(number, 0, 100));
}

function getSafeVideoTime(value, fallback = 0) {
  const number = Number(value);
  if (!Number.isFinite(number) || number < 0) {
    return fallback;
  }
  return number;
}

function getSafeCreditsDuration(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return 18;
  }
  return Math.round(clamp(number, 4, 180));
}

function getSafeWaitDurationSeconds(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return 1;
  }
  return Math.round(clamp(number, 0.1, 30) * 10) / 10;
}

function getSafeWaitDurationMs(value) {
  return Math.round(getSafeWaitDurationSeconds(value) * 1000);
}

function getSafeCreditsBackground(value) {
  return Object.hasOwn(CREDITS_BACKGROUND_LABELS, value) ? value : "dark";
}

function getCreditsBackgroundLabel(value) {
  return CREDITS_BACKGROUND_LABELS[getSafeCreditsBackground(value)] ?? CREDITS_BACKGROUND_LABELS.dark;
}

function getCreditsLines(lines) {
  if (Array.isArray(lines)) {
    return lines.map((line) => String(line ?? "").trim()).filter(Boolean);
  }
  return String(lines ?? "")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
}

function isBlockingMediaSnapshot(snapshot) {
  return snapshot?.blockType === "video_play" || snapshot?.blockType === "credits_roll";
}

function isMediaSnapshotSkippable(snapshot) {
  return snapshot?.block?.skippable !== false;
}

function getSafeParticleAction(action) {
  return action === "stop" ? "stop" : "start";
}

function getSafeParticlePreset(preset) {
  return Object.hasOwn(PARTICLE_PRESET_LABELS, preset) ? preset : "snow";
}

function getParticlePresetLabel(preset) {
  return PARTICLE_PRESET_LABELS[getSafeParticlePreset(preset)];
}

function getParticlePresetDefaults(preset) {
  return PARTICLE_PRESET_DEFAULTS[getSafeParticlePreset(preset)] ?? PARTICLE_PRESET_DEFAULTS.snow;
}

function getParticleAdvancedDefaults(preset) {
  return (
    PARTICLE_PRESET_ADVANCED_DEFAULTS[getSafeParticlePreset(preset)] ?? PARTICLE_PRESET_ADVANCED_DEFAULTS.snow
  );
}

function getSafeParticleIntensity(intensity) {
  return Object.hasOwn(PARTICLE_INTENSITY_LABELS, intensity) ? intensity : "medium";
}

function getParticleIntensityLabel(intensity) {
  return PARTICLE_INTENSITY_LABELS[getSafeParticleIntensity(intensity)];
}

function getSafeParticleBlendMode(blend) {
  return Object.hasOwn(PARTICLE_BLEND_LABELS, blend) ? blend : "screen";
}

function getParticleBlendModeLabel(blend) {
  return PARTICLE_BLEND_LABELS[getSafeParticleBlendMode(blend)];
}

function getParticleBlendCssValue(blend) {
  return getSafeParticleBlendMode(blend) === "add" ? "plus-lighter" : getSafeParticleBlendMode(blend);
}

function getSafeParticleEmissionMode(mode) {
  return Object.hasOwn(PARTICLE_EMISSION_MODE_LABELS, mode) ? mode : "continuous";
}

function getParticleEmissionModeLabel(mode) {
  return PARTICLE_EMISSION_MODE_LABELS[getSafeParticleEmissionMode(mode)];
}

function getSafeParticleEmitterShape(shape) {
  return Object.hasOwn(PARTICLE_EMITTER_SHAPE_LABELS, shape) ? shape : "line";
}

function getParticleEmitterShapeLabel(shape) {
  return PARTICLE_EMITTER_SHAPE_LABELS[getSafeParticleEmitterShape(shape)];
}

function getSafeParticleFollowTarget(follow) {
  return Object.hasOwn(PARTICLE_FOLLOW_LABELS, follow) ? follow : "none";
}

function getParticleFollowTargetLabel(follow) {
  return PARTICLE_FOLLOW_LABELS[getSafeParticleFollowTarget(follow)];
}

function getSafeParticleFollowAnchor(anchor) {
  return Object.hasOwn(PARTICLE_FOLLOW_ANCHOR_LABELS, anchor) ? anchor : "torso";
}

function getParticleFollowAnchorLabel(anchor) {
  return PARTICLE_FOLLOW_ANCHOR_LABELS[getSafeParticleFollowAnchor(anchor)];
}

function getSafeParticleSizeCurve(curve) {
  return Object.hasOwn(PARTICLE_SIZE_CURVE_LABELS, curve) ? curve : "steady";
}

function getParticleSizeCurveLabel(curve) {
  return PARTICLE_SIZE_CURVE_LABELS[getSafeParticleSizeCurve(curve)];
}

function getSafeParticleOpacityCurve(curve) {
  return Object.hasOwn(PARTICLE_OPACITY_CURVE_LABELS, curve) ? curve : "fade";
}

function getParticleOpacityCurveLabel(curve) {
  return PARTICLE_OPACITY_CURVE_LABELS[getSafeParticleOpacityCurve(curve)];
}

function getSafeParticleForceField(mode) {
  return Object.hasOwn(PARTICLE_FORCE_FIELD_LABELS, mode) ? mode : "none";
}

function getParticleForceFieldLabel(mode) {
  return PARTICLE_FORCE_FIELD_LABELS[getSafeParticleForceField(mode)];
}

function buildDefaultParticleCustomComboLayer(preset = "stardust") {
  const safePreset = getSafeParticlePreset(preset);
  const defaults = getParticlePresetDefaults(safePreset);
  const advancedDefaults = getParticleAdvancedDefaults(safePreset);
  return {
    enabled: false,
    preset: safePreset,
    emissionMode: advancedDefaults.emissionMode,
    follow: advancedDefaults.follow,
    followAnchor: "torso",
    densityMultiplier: 1,
    sizeScale: 1,
    lifeScale: 1,
    opacityScale: 1,
    colorMix: 0.42,
    blend: defaults.blend,
  };
}

function normalizeParticleCustomComboLayer(layer, fallbackPreset = "stardust") {
  const base = buildDefaultParticleCustomComboLayer(layer?.preset ?? fallbackPreset);
  return {
    enabled: Boolean(layer?.enabled),
    preset: getSafeParticlePreset(layer?.preset ?? base.preset),
    emissionMode: getSafeParticleEmissionMode(layer?.emissionMode ?? base.emissionMode),
    follow: getSafeParticleFollowTarget(layer?.follow ?? base.follow),
    followAnchor: getSafeParticleFollowAnchor(layer?.followAnchor ?? base.followAnchor),
    densityMultiplier: getSafeParticleClampedNumber(layer?.densityMultiplier, 1, 0.2, 4),
    sizeScale: getSafeParticleClampedNumber(layer?.sizeScale, 1, 0.2, 4),
    lifeScale: getSafeParticleClampedNumber(layer?.lifeScale, 1, 0.2, 4),
    opacityScale: getSafeParticleClampedNumber(layer?.opacityScale, 1, 0.1, 2),
    colorMix: getSafeParticleClampedNumber(layer?.colorMix, 0.42, 0, 1),
    blend: getSafeParticleBlendMode(layer?.blend ?? base.blend),
  };
}

function normalizeParticleCustomComboLayers(layers) {
  const source = Array.isArray(layers) ? layers.slice(0, PARTICLE_CUSTOM_COMBO_LAYER_LIMIT) : [];
  return source.map((layer, index) =>
    normalizeParticleCustomComboLayer(layer, index === 0 ? "stardust" : "smoke")
  );
}

function getEnabledParticleCustomComboLayers(layers) {
  return normalizeParticleCustomComboLayers(layers).filter((layer) => layer.enabled);
}

function getSafeParticleLayerCount(layerCount) {
  return clamp(Math.round(getSafeNumber(layerCount, 1)), 1, 3);
}

function getSafeParticleComboPreset(comboPreset) {
  return Object.hasOwn(PARTICLE_COMBO_PRESET_LABELS, comboPreset) ? comboPreset : "none";
}

function getParticleDefaultColorCurve(preset) {
  return {
    snow: "cool_shift",
    rain: "cool_shift",
    petals: "steady",
    dust: "steady",
    embers: "warm_shift",
    sparkles: "pulse_glow",
    bubbles: "cool_shift",
    confetti: "steady",
    smoke: "cool_shift",
    flame: "warm_shift",
    stardust: "spectral",
    glyphs: "spectral",
  }[getSafeParticlePreset(preset)] ?? "steady";
}

function getSafeParticleColorCurve(curve) {
  return Object.hasOwn(PARTICLE_COLOR_CURVE_LABELS, curve) ? curve : "steady";
}

function isValidParticleColor(color) {
  return /^#[0-9a-fA-F]{6}$/.test(String(color ?? "").trim());
}

function getSafeParticleColor(color, fallback = "#ffffff") {
  if (isValidParticleColor(color)) {
    return String(color).trim().toLowerCase();
  }
  return String(fallback).trim().toLowerCase();
}

function getSafeParticleClampedNumber(value, fallback, min, max) {
  return clamp(getSafeNumber(value, fallback), min, max);
}

function normalizeParticleRange(minValue, maxValue, fallbackMin, fallbackMax, clampMin, clampMax) {
  const safeMin = getSafeParticleClampedNumber(minValue, fallbackMin, clampMin, clampMax);
  const safeMax = getSafeParticleClampedNumber(maxValue, fallbackMax, clampMin, clampMax);
  return [Math.min(safeMin, safeMax), Math.max(safeMin, safeMax)];
}

function buildDefaultParticleEffectConfig(preset = "snow") {
  const safePreset = getSafeParticlePreset(preset);
  const defaults = getParticlePresetDefaults(safePreset);
  const advancedDefaults = getParticleAdvancedDefaults(safePreset);
  return {
    action: "start",
    preset: safePreset,
    assetId: "",
    intensity: "medium",
    speed: "medium",
    wind: "still",
    area: "full",
    emissionMode: advancedDefaults.emissionMode,
    emitterShape: advancedDefaults.emitterShape,
    emitterX: advancedDefaults.emitterX,
    emitterY: advancedDefaults.emitterY,
    emitterZ: advancedDefaults.emitterZ,
    attractionX: advancedDefaults.attractionX,
    attractionY: advancedDefaults.attractionY,
    vortex: advancedDefaults.vortex,
    follow: advancedDefaults.follow,
    followAnchor: "torso",
    comboPreset: "none",
    customComboLayers: [],
    layerCount: 1,
    sizeCurve: advancedDefaults.sizeCurve,
    opacityCurve: advancedDefaults.opacityCurve,
    colorCurve: getParticleDefaultColorCurve(safePreset),
    forceField: advancedDefaults.forceField,
    fieldX: advancedDefaults.fieldX,
    fieldY: advancedDefaults.fieldY,
    density: defaults.density,
    sizeMin: defaults.sizeMin,
    sizeMax: defaults.sizeMax,
    lifeMin: defaults.lifeMin,
    lifeMax: defaults.lifeMax,
    gravityX: defaults.gravityX,
    gravityY: defaults.gravityY,
    gravityZ: defaults.gravityZ,
    spreadX: defaults.spreadX,
    spreadY: defaults.spreadY,
    spreadZ: defaults.spreadZ,
    opacityMin: defaults.opacityMin,
    opacityMax: defaults.opacityMax,
    rotationMin: defaults.rotationMin,
    rotationMax: defaults.rotationMax,
    spin: defaults.spin,
    turbulence: defaults.turbulence,
    color: defaults.color,
    colorAccent: defaults.colorAccent,
    colorEnd: defaults.colorAccent,
    blend: defaults.blend,
  };
}

function normalizeParticleEffectConfig(particleEffect) {
  const safePreset = getSafeParticlePreset(particleEffect?.preset);
  const defaults = getParticlePresetDefaults(safePreset);
  const advancedDefaults = getParticleAdvancedDefaults(safePreset);
  const [sizeMin, sizeMax] = normalizeParticleRange(
    particleEffect?.sizeMin,
    particleEffect?.sizeMax,
    defaults.sizeMin,
    defaults.sizeMax,
    1,
    160
  );
  const [lifeMin, lifeMax] = normalizeParticleRange(
    particleEffect?.lifeMin,
    particleEffect?.lifeMax,
    defaults.lifeMin,
    defaults.lifeMax,
    0.4,
    20
  );
  const [opacityMin, opacityMax] = normalizeParticleRange(
    particleEffect?.opacityMin,
    particleEffect?.opacityMax,
    defaults.opacityMin,
    defaults.opacityMax,
    0.04,
    1
  );
  const [rotationMin, rotationMax] = normalizeParticleRange(
    particleEffect?.rotationMin,
    particleEffect?.rotationMax,
    defaults.rotationMin,
    defaults.rotationMax,
    -360,
    360
  );

  return {
    action: getSafeParticleAction(particleEffect?.action),
    preset: safePreset,
    assetId: getSafeParticleImageAssetId(particleEffect?.assetId),
    intensity: getSafeParticleIntensity(particleEffect?.intensity),
    speed: getSafeParticleSpeed(particleEffect?.speed),
    wind: getSafeParticleWind(particleEffect?.wind),
    area: getSafeParticleArea(particleEffect?.area),
    emissionMode: getSafeParticleEmissionMode(particleEffect?.emissionMode ?? advancedDefaults.emissionMode),
    emitterShape: getSafeParticleEmitterShape(particleEffect?.emitterShape ?? advancedDefaults.emitterShape),
    emitterX: getSafeParticleClampedNumber(particleEffect?.emitterX, advancedDefaults.emitterX, 0, 100),
    emitterY: getSafeParticleClampedNumber(particleEffect?.emitterY, advancedDefaults.emitterY, -20, 120),
    emitterZ: getSafeParticleClampedNumber(particleEffect?.emitterZ, advancedDefaults.emitterZ, -100, 100),
    attractionX: getSafeParticleClampedNumber(
      particleEffect?.attractionX,
      advancedDefaults.attractionX,
      -160,
      160
    ),
    attractionY: getSafeParticleClampedNumber(
      particleEffect?.attractionY,
      advancedDefaults.attractionY,
      -160,
      160
    ),
    vortex: getSafeParticleClampedNumber(particleEffect?.vortex, advancedDefaults.vortex, -240, 240),
    follow: getSafeParticleFollowTarget(particleEffect?.follow ?? advancedDefaults.follow),
    followAnchor: getSafeParticleFollowAnchor(particleEffect?.followAnchor ?? "torso"),
    comboPreset: getSafeParticleComboPreset(particleEffect?.comboPreset ?? "none"),
    customComboLayers: normalizeParticleCustomComboLayers(particleEffect?.customComboLayers),
    layerCount: getSafeParticleLayerCount(particleEffect?.layerCount ?? 1),
    sizeCurve: getSafeParticleSizeCurve(particleEffect?.sizeCurve ?? advancedDefaults.sizeCurve),
    opacityCurve: getSafeParticleOpacityCurve(particleEffect?.opacityCurve ?? advancedDefaults.opacityCurve),
    colorCurve: getSafeParticleColorCurve(
      particleEffect?.colorCurve ?? getParticleDefaultColorCurve(safePreset)
    ),
    forceField: getSafeParticleForceField(particleEffect?.forceField ?? advancedDefaults.forceField),
    fieldX: getSafeParticleClampedNumber(particleEffect?.fieldX, advancedDefaults.fieldX, 0, 100),
    fieldY: getSafeParticleClampedNumber(particleEffect?.fieldY, advancedDefaults.fieldY, -20, 120),
    density: Math.round(getSafeParticleClampedNumber(particleEffect?.density, defaults.density, 4, 240)),
    sizeMin,
    sizeMax,
    lifeMin,
    lifeMax,
    gravityX: getSafeParticleClampedNumber(particleEffect?.gravityX, defaults.gravityX, -180, 180),
    gravityY: getSafeParticleClampedNumber(particleEffect?.gravityY, defaults.gravityY, -160, 280),
    gravityZ: getSafeParticleClampedNumber(particleEffect?.gravityZ, defaults.gravityZ, -120, 120),
    spreadX: getSafeParticleClampedNumber(particleEffect?.spreadX, defaults.spreadX, 4, 100),
    spreadY: getSafeParticleClampedNumber(particleEffect?.spreadY, defaults.spreadY, 0, 100),
    spreadZ: getSafeParticleClampedNumber(particleEffect?.spreadZ, defaults.spreadZ, 0, 100),
    opacityMin,
    opacityMax,
    rotationMin,
    rotationMax,
    spin: getSafeParticleClampedNumber(particleEffect?.spin, defaults.spin, -1080, 1080),
    turbulence: getSafeParticleClampedNumber(particleEffect?.turbulence, defaults.turbulence, 0, 120),
    color: getSafeParticleColor(particleEffect?.color, defaults.color),
    colorAccent: getSafeParticleColor(particleEffect?.colorAccent, defaults.colorAccent),
    colorEnd: getSafeParticleColor(particleEffect?.colorEnd, particleEffect?.colorAccent ?? defaults.colorAccent),
    blend: getSafeParticleBlendMode(particleEffect?.blend ?? defaults.blend),
  };
}

function getSafeParticleSpeed(speed) {
  return Object.hasOwn(PARTICLE_SPEED_LABELS, speed) ? speed : "medium";
}

function getSafeParticleWind(wind) {
  return Object.hasOwn(PARTICLE_WIND_LABELS, wind) ? wind : "still";
}

function getSafeParticleArea(area) {
  return Object.hasOwn(PARTICLE_AREA_LABELS, area) ? area : "full";
}

function getSafeParticleImageAssetId(assetId) {
  if (!assetId) {
    return "";
  }

  const asset = data.assetsById.get(assetId);
  return asset && PARTICLE_IMAGE_ASSET_TYPES.includes(asset.type) ? assetId : "";
}

function getParticleSpeedMultiplier(speed) {
  return {
    slow: 1.28,
    medium: 1,
    fast: 0.78,
  }[getSafeParticleSpeed(speed)];
}

function getParticleWindBias(wind, preset) {
  const base = {
    left: -26,
    still: 0,
    right: 26,
  }[getSafeParticleWind(wind)];

  if (preset === "rain") {
    return base * 0.85;
  }

  if (preset === "dust" || preset === "bubbles") {
    return base * 0.5;
  }

  return base;
}

function getParticleAreaLayout(area, spreadX = 100) {
  const base = {
    full: { start: 0, width: 100 },
    left: { start: 0, width: 54 },
    center: { start: 23, width: 54 },
    right: { start: 46, width: 54 },
  }[getSafeParticleArea(area)];
  const normalizedWidth = Math.max(8, base.width * (clamp(spreadX, 4, 100) / 100));
  return {
    start: base.start + (base.width - normalizedWidth) * 0.5,
    width: normalizedWidth,
  };
}

function getParticlePresetDensityMultiplier(preset) {
  return {
    snow: 1,
    rain: 1.15,
    petals: 0.72,
    dust: 0.56,
    embers: 0.58,
    sparkles: 0.42,
    bubbles: 0.45,
    confetti: 0.8,
  }[getSafeParticlePreset(preset)];
}

function getParticleMotionProfile(preset) {
  return {
    snow: { startBase: -18, endBase: 126, aspect: "round" },
    rain: { startBase: -20, endBase: 136, aspect: "rain" },
    petals: { startBase: -14, endBase: 126, aspect: "petal" },
    dust: { startBase: -8, endBase: 112, aspect: "dust" },
    embers: { startBase: 108, endBase: -18, aspect: "ember" },
    sparkles: { startBase: -6, endBase: 118, aspect: "sparkle" },
    bubbles: { startBase: 112, endBase: -22, aspect: "bubble" },
    confetti: { startBase: -12, endBase: 126, aspect: "confetti" },
  }[getSafeParticlePreset(preset)];
}

function getParticleRandom(index, salt = 1) {
  const value = Math.sin((index + 1) * 12.9898 + salt * 78.233) * 43758.5453123;
  return value - Math.floor(value);
}

function hexToRgb(color) {
  const safeColor = getSafeParticleColor(color, "#ffffff");
  return {
    red: Number.parseInt(safeColor.slice(1, 3), 16),
    green: Number.parseInt(safeColor.slice(3, 5), 16),
    blue: Number.parseInt(safeColor.slice(5, 7), 16),
  };
}

function mixParticleColors(colorA, colorB, ratio) {
  const first = hexToRgb(colorA);
  const second = hexToRgb(colorB);
  const mixChannel = (channel) =>
    clamp(Math.round(first[channel] + (second[channel] - first[channel]) * ratio), 0, 255)
      .toString(16)
      .padStart(2, "0");

  return `#${mixChannel("red")}${mixChannel("green")}${mixChannel("blue")}`;
}

function formatParticleNumber(value, fractionDigits = 0) {
  return Number(value).toFixed(fractionDigits).replace(/\.0+$/, "").replace(/(\.\d*[1-9])0+$/, "$1");
}

function getParticleAnchorPercent(position) {
  return {
    left: 24,
    center: 50,
    right: 76,
  }[position] ?? 50;
}

function getParticleCameraAnchorPercent(stageContext = null) {
  const focus =
    stageContext?.cameraPan?.target && stageContext.cameraPan.target !== "center"
      ? stageContext.cameraPan.target
      : stageContext?.cameraZoom?.focus ?? "center";
  return getParticleAnchorPercent(focus);
}

function getParticleEmitterAnchor(particleEffect, stageContext = null) {
  const config = normalizeParticleEffectConfig(particleEffect);
  const areaLayout = getParticleAreaLayout(config.area, 100);
  let anchorX = config.emitterX;
  let anchorY = config.emitterY;
  let anchorZ = config.emitterZ;
  const follow = getSafeParticleFollowTarget(config.follow);

  if (follow === "character" && stageContext?.activeCharacterId) {
    const activeCharacter = (stageContext.visibleCharacters ?? []).find(
      (item) => item.characterId === stageContext.activeCharacterId
    );
    if (activeCharacter) {
      anchorX = getParticleAnchorPercent(activeCharacter.position);
      const followAnchor = getSafeParticleFollowAnchor(config.followAnchor);
      anchorY =
        followAnchor === "head" ? 34 : followAnchor === "feet" ? 82 : 56;
      anchorZ += 8;
    }
  } else if (follow === "camera") {
    anchorX = getParticleCameraAnchorPercent(stageContext);
    const followAnchor = getSafeParticleFollowAnchor(config.followAnchor);
    anchorY =
      followAnchor === "head" ? 30 : followAnchor === "feet" ? 72 : 48;
  }

  return {
    x: clamp(anchorX, areaLayout.start, areaLayout.start + areaLayout.width),
    y: clamp(anchorY, -20, 120),
    z: clamp(anchorZ, -100, 100),
  };
}

function getParticleCurveProfile(particleEffect) {
  const config = normalizeParticleEffectConfig(particleEffect);
  const sizeCurve = getSafeParticleSizeCurve(config.sizeCurve);
  const opacityCurve = getSafeParticleOpacityCurve(config.opacityCurve);
  const forceField = getSafeParticleForceField(config.forceField);

  const sizeProfiles = {
    steady: { start: 1, mid: 1.02, end: 1.04 },
    bloom: { start: 0.48, mid: 0.92, end: 1.18 },
    shrink: { start: 1.16, mid: 0.94, end: 0.66 },
    pulse: { start: 0.68, mid: 1.28, end: 0.82 },
  };

  const opacityProfiles = {
    fade: { start: 1, mid: 0.74, end: 0.12 },
    linger: { start: 0.82, mid: 0.86, end: 0.26 },
    blink: { start: 0.44, mid: 1, end: 0.14 },
    pop: { start: 1, mid: 0.54, end: 0.08 },
  };

  const forceProfiles = {
    none: { x: 0, y: 0, orbit: 0 },
    attract: { x: 0.62, y: 0.62, orbit: 0.08 },
    repel: { x: -0.68, y: -0.68, orbit: 0.06 },
    orbit: { x: 0.22, y: 0.22, orbit: 0.78 },
  };

  return {
    size: sizeProfiles[sizeCurve],
    opacity: opacityProfiles[opacityCurve],
    force: forceProfiles[forceField],
  };
}

function getParticleColorCurveProfile(particleEffect) {
  const config = normalizeParticleEffectConfig(particleEffect);
  const colorCurve = getSafeParticleColorCurve(config.colorCurve);

  return {
    steady: {
      hue: { start: 0, mid: 0, end: 0 },
      saturation: { start: 1, mid: 1, end: 1 },
      brightness: { start: 1, mid: 1, end: 1 },
    },
    cool_shift: {
      hue: { start: 0, mid: 10, end: 22 },
      saturation: { start: 0.98, mid: 1.08, end: 1.14 },
      brightness: { start: 0.98, mid: 1.04, end: 0.94 },
    },
    warm_shift: {
      hue: { start: 0, mid: -10, end: -24 },
      saturation: { start: 1, mid: 1.12, end: 1.18 },
      brightness: { start: 0.96, mid: 1.08, end: 0.9 },
    },
    spectral: {
      hue: { start: -10, mid: 18, end: 54 },
      saturation: { start: 1.04, mid: 1.22, end: 1.12 },
      brightness: { start: 0.94, mid: 1.12, end: 0.96 },
    },
    pulse_glow: {
      hue: { start: 0, mid: 4, end: 0 },
      saturation: { start: 1, mid: 1.28, end: 1.04 },
      brightness: { start: 0.94, mid: 1.26, end: 0.9 },
    },
  }[colorCurve];
}

function buildParticleLayerVariants(particleEffect) {
  const config = normalizeParticleEffectConfig(particleEffect);
  const layerCount = getSafeParticleLayerCount(config.layerCount);
  return Array.from({ length: layerCount }, (_, layerIndex) => {
    const depthFactor = layerCount === 1 ? 0 : layerIndex / (layerCount - 1);
    const sizeFactor = layerCount === 1 ? 1 : 0.78 + depthFactor * 0.46;
    const opacityFactor = layerCount === 1 ? 1 : 0.72 + depthFactor * 0.32;
    const densityFactor = layerCount === 1 ? 1 : 0.74 + (1 - Math.abs(depthFactor - 0.5) * 2) * 0.42;
    return {
      ...config,
      density: Math.max(6, Math.round((config.density / layerCount) * densityFactor)),
      sizeMin: clamp(config.sizeMin * sizeFactor, 1, 160),
      sizeMax: clamp(config.sizeMax * sizeFactor, 1, 160),
      opacityMin: clamp(config.opacityMin * opacityFactor, 0.04, 1),
      opacityMax: clamp(config.opacityMax * opacityFactor, 0.04, 1),
      spreadZ: clamp(config.spreadZ + layerIndex * 12, 0, 100),
      gravityZ: clamp(config.gravityZ + (depthFactor - 0.5) * 24, -120, 120),
      emitterZ: clamp(config.emitterZ + (depthFactor - 0.5) * 22, -100, 100),
      color: mixParticleColors(config.color, config.colorAccent, depthFactor * 0.35),
      colorAccent: mixParticleColors(config.colorAccent, config.colorEnd, depthFactor * 0.35),
      colorEnd: mixParticleColors(config.colorEnd, config.color, depthFactor * 0.18),
      __layerIndex: layerIndex,
    };
  });
}

function buildParticleComboVariants(particleEffect) {
  const baseConfig = normalizeParticleEffectConfig(particleEffect);
  const comboPreset = getSafeParticleComboPreset(baseConfig.comboPreset);
  const presetOverlays = PARTICLE_COMBO_PRESET_CONFIGS[comboPreset] ?? [];
  const customOverlays = getEnabledParticleCustomComboLayers(baseConfig.customComboLayers).map((layer) => ({
    preset: layer.preset,
    emissionMode: layer.emissionMode,
    follow: layer.follow,
    followAnchor: layer.followAnchor,
    densityMultiplier: layer.densityMultiplier,
    sizeScale: layer.sizeScale,
    lifeScale: layer.lifeScale,
    opacityScale: layer.opacityScale,
    colorMix: layer.colorMix,
    blend: layer.blend,
  }));
  const overlays = [...presetOverlays, ...customOverlays];

  if (!overlays.length) {
    return [{ ...baseConfig, __comboIndex: 0 }];
  }

  return [
    { ...baseConfig, __comboIndex: 0 },
    ...overlays.map((overlay, comboIndex) => {
      const overlayDefaults = normalizeParticleEffectConfig(buildDefaultParticleEffectConfig(overlay.preset));
      const colorMix = clamp(getSafeNumber(overlay.colorMix, 0.42), 0, 1);
      const follow = overlay.follow ?? overlayDefaults.follow;
      const followAnchor =
        overlay.followAnchor ?? (follow === "none" ? overlayDefaults.followAnchor : baseConfig.followAnchor);

      return normalizeParticleEffectConfig({
        ...overlayDefaults,
        action: "start",
        intensity: overlay.intensity ?? baseConfig.intensity,
        speed: overlay.speed ?? baseConfig.speed,
        wind: overlay.wind ?? baseConfig.wind,
        area: overlay.area ?? baseConfig.area,
        emissionMode: overlay.emissionMode ?? overlayDefaults.emissionMode,
        emitterShape: overlay.emitterShape ?? overlayDefaults.emitterShape,
        emitterX: (overlay.emitterX ?? baseConfig.emitterX) + getSafeNumber(overlay.emitterXOffset, 0),
        emitterY: (overlay.emitterY ?? baseConfig.emitterY) + getSafeNumber(overlay.emitterYOffset, 0),
        emitterZ: (overlay.emitterZ ?? baseConfig.emitterZ) + getSafeNumber(overlay.emitterZOffset, 0),
        attractionX: overlay.attractionX ?? overlayDefaults.attractionX,
        attractionY: overlay.attractionY ?? overlayDefaults.attractionY,
        vortex: overlay.vortex ?? overlayDefaults.vortex,
        follow,
        followAnchor,
        comboPreset: "none",
        layerCount: overlay.layerCount ?? overlayDefaults.layerCount,
        sizeCurve: overlay.sizeCurve ?? overlayDefaults.sizeCurve,
        opacityCurve: overlay.opacityCurve ?? overlayDefaults.opacityCurve,
        forceField: overlay.forceField ?? overlayDefaults.forceField,
        fieldX: (overlay.fieldX ?? baseConfig.fieldX) + getSafeNumber(overlay.fieldXOffset, 0),
        fieldY: (overlay.fieldY ?? baseConfig.fieldY) + getSafeNumber(overlay.fieldYOffset, 0),
        density: Math.round(overlayDefaults.density * getSafeNumber(overlay.densityMultiplier, 1)),
        sizeMin: overlayDefaults.sizeMin * getSafeNumber(overlay.sizeScale, 1),
        sizeMax: overlayDefaults.sizeMax * getSafeNumber(overlay.sizeScale, 1),
        lifeMin: overlayDefaults.lifeMin * getSafeNumber(overlay.lifeScale, 1),
        lifeMax: overlayDefaults.lifeMax * getSafeNumber(overlay.lifeScale, 1),
        gravityX: overlayDefaults.gravityX + getSafeNumber(overlay.gravityXAdd, 0),
        gravityY: overlayDefaults.gravityY + getSafeNumber(overlay.gravityYAdd, 0),
        gravityZ: overlayDefaults.gravityZ + getSafeNumber(overlay.gravityZAdd, 0),
        spreadX: overlayDefaults.spreadX * getSafeNumber(overlay.spreadXMultiplier, 1),
        spreadY: overlayDefaults.spreadY * getSafeNumber(overlay.spreadYMultiplier, 1),
        spreadZ: overlayDefaults.spreadZ + getSafeNumber(overlay.spreadZAdd, 0),
        opacityMin: overlayDefaults.opacityMin * getSafeNumber(overlay.opacityScale, 1),
        opacityMax: overlayDefaults.opacityMax * getSafeNumber(overlay.opacityScale, 1),
        rotationMin: overlayDefaults.rotationMin,
        rotationMax: overlayDefaults.rotationMax,
        spin: overlayDefaults.spin + getSafeNumber(overlay.spinAdd, 0),
        turbulence: overlayDefaults.turbulence + getSafeNumber(overlay.turbulenceAdd, 0),
        color: overlay.color ?? mixParticleColors(overlayDefaults.color, baseConfig.color, colorMix),
        colorAccent:
          overlay.colorAccent ??
          mixParticleColors(overlayDefaults.colorAccent, baseConfig.colorAccent, Math.min(colorMix + 0.08, 1)),
        colorEnd:
          overlay.colorEnd ??
          mixParticleColors(overlayDefaults.colorAccent, baseConfig.colorEnd, Math.min(colorMix + 0.04, 1)),
        blend: overlay.blend ?? overlayDefaults.blend,
        assetId: "",
        __comboIndex: comboIndex + 1,
      });
    }),
  ];
}

function getSafeShakeIntensity(intensity) {
  return Object.hasOwn(SHAKE_INTENSITY_LABELS, intensity) ? intensity : "medium";
}

function getShakeIntensityLabel(intensity) {
  return SHAKE_INTENSITY_LABELS[getSafeShakeIntensity(intensity)];
}

function getSafeEffectDuration(duration) {
  return Object.hasOwn(EFFECT_DURATION_LABELS, duration) ? duration : "medium";
}

function getEffectDurationLabel(duration) {
  return EFFECT_DURATION_LABELS[getSafeEffectDuration(duration)];
}

function getShakeDistance(intensity) {
  return {
    light: 5,
    medium: 10,
    heavy: 16,
  }[getSafeShakeIntensity(intensity)];
}

function getEffectDurationSeconds(duration) {
  return {
    short: 0.42,
    medium: 0.78,
    long: 1.2,
  }[getSafeEffectDuration(duration)];
}

function getSafeFlashColor(color) {
  return Object.hasOwn(FLASH_COLOR_LABELS, color) ? color : "white";
}

function getFlashColorLabel(color) {
  return FLASH_COLOR_LABELS[getSafeFlashColor(color)];
}

function getSafeFlashIntensity(intensity) {
  return Object.hasOwn(FLASH_INTENSITY_LABELS, intensity) ? intensity : "medium";
}

function getFlashIntensityLabel(intensity) {
  return FLASH_INTENSITY_LABELS[getSafeFlashIntensity(intensity)];
}

function getFlashOpacity(intensity) {
  return {
    soft: 0.36,
    medium: 0.54,
    strong: 0.72,
  }[getSafeFlashIntensity(intensity)];
}

function getFlashColorRgb(color) {
  return {
    white: "255, 255, 255",
    warm: "255, 236, 204",
    red: "255, 120, 120",
    black: "32, 24, 22",
  }[getSafeFlashColor(color)];
}

function getSafeFadeAction(action) {
  return Object.hasOwn(FADE_ACTION_LABELS, action) ? action : "fade_out";
}

function getFadeColorLabel(color) {
  return FADE_COLOR_LABELS[getSafeFadeColor(color)];
}

function getSafeFadeColor(color) {
  return Object.hasOwn(FADE_COLOR_LABELS, color) ? color : "black";
}

function getFadeColorRgb(color) {
  return {
    black: "18, 14, 12",
    white: "255, 252, 247",
  }[getSafeFadeColor(color)];
}

function getSafeCameraZoomAction(action) {
  return Object.hasOwn(CAMERA_ZOOM_ACTION_LABELS, action) ? action : "zoom_in";
}

function getCameraZoomActionLabel(action) {
  return CAMERA_ZOOM_ACTION_LABELS[getSafeCameraZoomAction(action)];
}

function getSafeCameraZoomStrength(strength) {
  return Object.hasOwn(CAMERA_ZOOM_STRENGTH_LABELS, strength) ? strength : "medium";
}

function getCameraZoomStrengthLabel(strength) {
  return CAMERA_ZOOM_STRENGTH_LABELS[getSafeCameraZoomStrength(strength)];
}

function getSafeCameraZoomFocus(focus) {
  return Object.hasOwn(CAMERA_ZOOM_FOCUS_LABELS, focus) ? focus : "center";
}

function getCameraZoomFocusLabel(focus) {
  return CAMERA_ZOOM_FOCUS_LABELS[getSafeCameraZoomFocus(focus)];
}

function getCameraZoomScale(action, strength) {
  const safeAction = getSafeCameraZoomAction(action);
  const safeStrength = getSafeCameraZoomStrength(strength);

  if (safeAction === "reset") {
    return 1;
  }

  const zoomInScale = {
    light: 1.08,
    medium: 1.16,
    heavy: 1.26,
  };

  const zoomOutScale = {
    light: 0.96,
    medium: 0.92,
    heavy: 0.88,
  };

  return safeAction === "zoom_out" ? zoomOutScale[safeStrength] : zoomInScale[safeStrength];
}

function getCameraZoomOrigin(focus) {
  return {
    left: "28% 52%",
    center: "50% 52%",
    right: "72% 52%",
  }[getSafeCameraZoomFocus(focus)];
}

function getSafeCameraPanTarget(target) {
  return Object.hasOwn(CAMERA_PAN_TARGET_LABELS, target) ? target : "center";
}

function getCameraPanTargetLabel(target) {
  return CAMERA_PAN_TARGET_LABELS[getSafeCameraPanTarget(target)];
}

function getSafeCameraPanStrength(strength) {
  return Object.hasOwn(CAMERA_PAN_STRENGTH_LABELS, strength) ? strength : "medium";
}

function getCameraPanStrengthLabel(strength) {
  return CAMERA_PAN_STRENGTH_LABELS[getSafeCameraPanStrength(strength)];
}

function getCameraPanOffset(target, strength) {
  const safeTarget = getSafeCameraPanTarget(target);
  if (safeTarget === "center") {
    return 0;
  }

  const amount = {
    light: 4,
    medium: 8,
    heavy: 12,
  }[getSafeCameraPanStrength(strength)];

  return safeTarget === "left" ? amount : -amount;
}

function getSafeScreenFilterAction(action) {
  return Object.hasOwn(SCREEN_FILTER_ACTION_LABELS, action) ? action : "apply";
}

function getSafeScreenFilterPreset(preset) {
  return Object.hasOwn(SCREEN_FILTER_PRESET_LABELS, preset) ? preset : "memory";
}

function getScreenFilterPresetLabel(preset) {
  return SCREEN_FILTER_PRESET_LABELS[getSafeScreenFilterPreset(preset)];
}

function getSafeScreenFilterStrength(strength) {
  return Object.hasOwn(SCREEN_FILTER_STRENGTH_LABELS, strength) ? strength : "medium";
}

function getScreenFilterStrengthLabel(strength) {
  return SCREEN_FILTER_STRENGTH_LABELS[getSafeScreenFilterStrength(strength)];
}

function getSafeScreenColorGrade(source) {
  const grade = source && typeof source === "object" ? source : {};
  return Object.fromEntries(
    Object.entries(SCREEN_COLOR_GRADE_DEFAULTS).map(([key, fallback]) => {
      const [minimum, maximum] = SCREEN_COLOR_GRADE_LIMITS[key];
      const value = Number(grade[key]);
      const safeValue = Number.isFinite(value) ? value : fallback;
      return [key, Math.round(clamp(safeValue, minimum, maximum))];
    })
  );
}

function getScreenColorGradeCss(source) {
  const grade = getSafeScreenColorGrade(source);
  const hue = grade.hue - grade.temperature * 0.08;
  return [
    `brightness(${(grade.brightness / 100).toFixed(3)})`,
    `contrast(${(grade.contrast / 100).toFixed(3)})`,
    `saturate(${(grade.saturation / 100).toFixed(3)})`,
    `hue-rotate(${hue.toFixed(2)}deg)`,
  ].join(" ");
}

function getScreenFilterVignette(screenFilter) {
  if (!screenFilter) {
    return 0;
  }
  const grade = getSafeScreenColorGrade(screenFilter.grade);
  return Number((grade.vignette / 100 * 0.68).toFixed(3));
}

function getScreenFilterCss(screenFilter) {
  if (!screenFilter) {
    return "";
  }

  const preset = getSafeScreenFilterPreset(screenFilter.preset);
  const strength = getSafeScreenFilterStrength(screenFilter.strength);

  const recipes = {
    memory: {
      soft: "sepia(0.18) saturate(1.02) brightness(1.03) contrast(0.96)",
      medium: "sepia(0.34) saturate(1.05) brightness(1.05) contrast(0.93)",
      strong: "sepia(0.5) saturate(1.08) brightness(1.07) contrast(0.9)",
    },
    mono: {
      soft: "grayscale(0.45) brightness(1.03) contrast(0.98)",
      medium: "grayscale(0.72) brightness(1.04) contrast(1)",
      strong: "grayscale(1) brightness(1.06) contrast(1.03)",
    },
    dream: {
      soft: "saturate(0.94) brightness(1.06) contrast(0.94)",
      medium: "saturate(0.88) brightness(1.1) contrast(0.9)",
      strong: "saturate(0.8) brightness(1.14) contrast(0.86)",
    },
    cold: {
      soft: "saturate(0.88) hue-rotate(168deg) brightness(1.01) contrast(0.97)",
      medium: "saturate(0.8) hue-rotate(180deg) brightness(1.02) contrast(0.95)",
      strong: "saturate(0.72) hue-rotate(192deg) brightness(1.03) contrast(0.93)",
    },
  };

  return combineFilterCss(recipes[preset][strength], getScreenColorGradeCss(screenFilter.grade));
}

function getScreenFilterWash(screenFilter) {
  if (!screenFilter) {
    return {
      background: "transparent",
      opacity: 0,
    };
  }

  const preset = getSafeScreenFilterPreset(screenFilter.preset);
  const strength = getSafeScreenFilterStrength(screenFilter.strength);
  const grade = getSafeScreenColorGrade(screenFilter.grade);
  const baseOpacity = {
    soft: 0.12,
    medium: 0.2,
    strong: 0.28,
  }[strength];

  const backgrounds = {
    memory: "linear-gradient(180deg, rgba(255, 233, 204, 0.85), rgba(255, 208, 154, 0.62))",
    mono: "linear-gradient(180deg, rgba(255, 255, 255, 0.72), rgba(90, 90, 90, 0.34))",
    dream: "linear-gradient(180deg, rgba(255, 241, 250, 0.82), rgba(214, 230, 255, 0.48))",
    cold: "linear-gradient(180deg, rgba(204, 232, 255, 0.72), rgba(136, 176, 222, 0.44))",
  };
  const temperatureWash =
    grade.temperature > 0
      ? "linear-gradient(180deg, rgba(255, 220, 166, 0.76), rgba(255, 150, 92, 0.34))"
      : "linear-gradient(180deg, rgba(178, 221, 255, 0.72), rgba(86, 126, 255, 0.3))";
  const temperatureOpacity = Math.abs(grade.temperature) / 100 * 0.16;

  return {
    background: temperatureOpacity > 0.001 ? `${temperatureWash}, ${backgrounds[preset]}` : backgrounds[preset],
    opacity: Number(clamp(baseOpacity + temperatureOpacity, 0, 0.46).toFixed(3)),
  };
}

function getSafeDepthBlurAction(action) {
  return Object.hasOwn(DEPTH_BLUR_ACTION_LABELS, action) ? action : "apply";
}

function getSafeDepthBlurFocus(focus) {
  return Object.hasOwn(DEPTH_BLUR_FOCUS_LABELS, focus) ? focus : "center";
}

function getDepthBlurFocusLabel(focus) {
  return DEPTH_BLUR_FOCUS_LABELS[getSafeDepthBlurFocus(focus)];
}

function getSafeDepthBlurStrength(strength) {
  return Object.hasOwn(DEPTH_BLUR_STRENGTH_LABELS, strength) ? strength : "medium";
}

function getDepthBlurStrengthLabel(strength) {
  return DEPTH_BLUR_STRENGTH_LABELS[getSafeDepthBlurStrength(strength)];
}

function getDepthBlurBackdropPx(strength) {
  return {
    soft: 4,
    medium: 7,
    strong: 10,
  }[getSafeDepthBlurStrength(strength)];
}

function getDepthBlurParticlePx(strength) {
  return {
    soft: 1.5,
    medium: 2.4,
    strong: 3.2,
  }[getSafeDepthBlurStrength(strength)];
}

function getDepthBlurSpritePx(strength) {
  return {
    soft: 1.8,
    medium: 2.8,
    strong: 3.8,
  }[getSafeDepthBlurStrength(strength)];
}

function getDepthBlurSpriteOpacity(strength) {
  return {
    soft: 0.72,
    medium: 0.58,
    strong: 0.46,
  }[getSafeDepthBlurStrength(strength)];
}

function shouldBlurPlayerCharacter(position, depthBlur) {
  if (!depthBlur) {
    return false;
  }

  const focus = getSafeDepthBlurFocus(depthBlur.focus);
  return focus !== "full" && position !== focus;
}

function renderParticleEffectLayer(particleEffect, stageContext = null) {
  if (!particleEffect) {
    return "";
  }

  const config = normalizeParticleEffectConfig(particleEffect);
  const combos = buildParticleComboVariants(config);

  return `
    <div
      class="particle-layer"
      data-particle-preset="${config.preset}"
      data-particle-intensity="${config.intensity}"
      data-particle-speed="${config.speed}"
      data-particle-wind="${config.wind}"
      data-particle-area="${config.area}"
      data-particle-combo="${config.comboPreset}"
      data-particle-emission="${config.emissionMode}"
      data-particle-emitter-shape="${config.emitterShape}"
      data-particle-follow="${config.follow}"
      data-particle-blend="${config.blend}"
      data-particle-layers="${config.layerCount}"
      data-has-custom-image="${config.assetId ? "true" : "false"}"
      aria-hidden="true"
    >
      ${combos
        .map((comboConfig) => {
          const layers = buildParticleLayerVariants(comboConfig);
          return layers
            .map((layerConfig) => {
              const particleCount = getParticleItemCount(layerConfig);
              return Array.from({ length: particleCount }, (_, index) =>
                renderParticleItem(
                  layerConfig,
                  comboConfig.__comboIndex * 10000 + layerConfig.__layerIndex * 1000 + index,
                  stageContext
                )
              ).join("");
            })
            .join("");
        })
        .join("")}
    </div>
  `;
}

function renderParticleItem(particleEffect, index, stageContext = null) {
  const config = normalizeParticleEffectConfig(particleEffect);
  const motion = getParticleMotionProfile(config.preset);
  const areaLayout = getParticleAreaLayout(config.area, 100);
  const anchor = getParticleEmitterAnchor(config, stageContext);
  const emitterShape = getSafeParticleEmitterShape(config.emitterShape);
  const curves = getParticleCurveProfile(config);
  const colorCurve = getParticleColorCurveProfile(config);
  const speedMultiplier = getParticleSpeedMultiplier(config.speed);
  const duration = (config.lifeMin + (config.lifeMax - config.lifeMin) * getParticleRandom(index, 2)) * speedMultiplier;
  const baseSize = config.sizeMin + (config.sizeMax - config.sizeMin) * getParticleRandom(index, 3);
  const depthShift = (getParticleRandom(index, 4) - 0.5) * 2 * (config.spreadZ / 100) + anchor.z / 100;
  const profileAspect = motion.aspect;
  const width =
    profileAspect === "rain"
      ? Math.max(1.5, baseSize * 0.28)
      : profileAspect === "petal"
        ? baseSize * 1.08
        : profileAspect === "confetti"
          ? baseSize * 0.76
          : baseSize;
  const height =
    profileAspect === "rain"
      ? Math.max(18, baseSize * 8.6)
      : profileAspect === "petal"
        ? Math.max(6, baseSize * 0.82)
        : profileAspect === "confetti"
          ? Math.max(6, baseSize * 1.34)
          : width;
  const seedX = getParticleRandom(index, 5);
  const seedY = getParticleRandom(index, 6);
  const seedAngle = getParticleRandom(index, 13) * Math.PI * 2;
  const seedRadius = Math.sqrt(getParticleRandom(index, 14));
  let left = anchor.x;
  let startY = anchor.y;

  if (emitterShape === "point") {
    left += (seedX - 0.5) * Math.max(4, config.spreadX * 0.12);
    startY += (seedY - 0.5) * Math.max(4, config.spreadY * 0.12);
  } else if (emitterShape === "line") {
    left += (seedX - 0.5) * config.spreadX;
    startY += (seedY - 0.5) * Math.max(4, config.spreadY * 0.12);
  } else if (emitterShape === "box") {
    left += (seedX - 0.5) * config.spreadX;
    startY += (seedY - 0.5) * config.spreadY;
  } else if (emitterShape === "circle") {
    left += Math.cos(seedAngle) * (config.spreadX * 0.5) * seedRadius;
    startY += Math.sin(seedAngle) * (config.spreadY * 0.5) * seedRadius;
  }

  left = clamp(left, areaLayout.start, areaLayout.start + areaLayout.width);
  startY = clamp(startY, -24, 124);

  const travelY = motion.endBase - motion.startBase;
  const fieldX = clamp(config.fieldX, 0, 100);
  const fieldY = clamp(config.fieldY, -20, 120);
  const fieldDeltaX = fieldX - left;
  const fieldDeltaY = fieldY - startY;
  const endY =
    startY +
    travelY +
    config.gravityY * 0.18 +
    config.attractionY * 0.34 +
    fieldDeltaY * curves.force.y * 0.22 +
    (getParticleRandom(index, 15) - 0.5) * config.spreadY * 0.35;
  const windBias = getParticleWindBias(config.wind, config.preset);
  const driftX =
    windBias +
    config.gravityX * 0.88 +
    config.attractionX * 0.58 +
    fieldDeltaX * curves.force.x * 0.24 +
    (getParticleRandom(index, 7) - 0.5) * config.turbulence * 1.9 +
    (getParticleRandom(index, 16) - 0.5) * config.vortex * (0.42 + curves.force.orbit) +
    fieldDeltaY * curves.force.orbit * 0.18 +
    depthShift * config.spreadZ * 0.35;
  const opacityStart =
    config.opacityMin + (config.opacityMax - config.opacityMin) * getParticleRandom(index, 8);
  const opacityMid = clamp(opacityStart * curves.opacity.mid, 0, 1);
  const opacityEnd = clamp(
    opacityStart * curves.opacity.end * (config.preset === "bubbles" ? 1.16 : config.preset === "embers" ? 0.92 : 1),
    0,
    1
  );
  const rotationStart =
    config.rotationMin + (config.rotationMax - config.rotationMin) * getParticleRandom(index, 9);
  const rotationEnd =
    rotationStart +
    config.spin * (0.45 + getParticleRandom(index, 10) * 0.75) +
    config.vortex * (0.4 + getParticleRandom(index, 17) * 0.35);
  const midY = startY + (endY - startY) * (0.5 + getParticleRandom(index, 19) * 0.12);
  const rotationMid = rotationStart + (rotationEnd - rotationStart) * (0.48 + getParticleRandom(index, 20) * 0.14);
  const blur = Math.max(
    0,
    Math.abs(depthShift) * (config.spreadZ / 100) * 4.2 +
      (config.preset === "dust" ? 1.1 : 0) +
      (config.preset === "bubbles" ? 0.8 : 0)
  );
  const scaleBase = 0.68 + depthShift * 0.28 + config.gravityZ * 0.002 + anchor.z * 0.002;
  const scaleStart = clamp(scaleBase * curves.size.start, 0.22, 2.8);
  const scaleMid = clamp(scaleBase * curves.size.mid, 0.18, 3.2);
  const scaleEnd = clamp(
    scaleBase * curves.size.end + config.gravityZ * 0.004 + (motion.endBase < motion.startBase ? 0.16 : 0.05),
    0.16,
    3.4
  );
  const particleColor = mixParticleColors(config.color, config.colorAccent, getParticleRandom(index, 11));
  const particleAccent = mixParticleColors(
    config.colorAccent,
    config.colorEnd,
    getParticleRandom(index, 12) * 0.32
  );
  const particleEnd = mixParticleColors(config.colorEnd, config.colorAccent, getParticleRandom(index, 21) * 0.24);
  const filterStart = `blur(calc(var(--particle-blur, 0px) + var(--particle-blur-extra, 0px))) hue-rotate(${colorCurve.hue.start}deg) saturate(${colorCurve.saturation.start.toFixed(
    3
  )}) brightness(${colorCurve.brightness.start.toFixed(3)})`;
  const filterMid = `blur(calc(var(--particle-blur, 0px) + var(--particle-blur-extra, 0px))) hue-rotate(${colorCurve.hue.mid}deg) saturate(${colorCurve.saturation.mid.toFixed(
    3
  )}) brightness(${colorCurve.brightness.mid.toFixed(3)})`;
  const filterEnd = `blur(calc(var(--particle-blur, 0px) + var(--particle-blur-extra, 0px))) hue-rotate(${colorCurve.hue.end}deg) saturate(${colorCurve.saturation.end.toFixed(
    3
  )}) brightness(${colorCurve.brightness.end.toFixed(3)})`;
  const imageStyle = getParticleImageStyle(config.assetId);
  const emissionDelay =
    config.emissionMode === "burst"
      ? -(getParticleRandom(index, 18) * Math.min(0.9, Math.max(0.18, duration * 0.18)))
      : -((index * 0.35) % Math.max(duration * 0.72, 1.2));

  return `
    <span
      class="particle-item ${imageStyle ? "has-custom-image" : ""}"
      style="
        --particle-left:${left.toFixed(2)}%;
        --particle-start-y:${startY.toFixed(2)}%;
        --particle-mid-y:${midY.toFixed(2)}%;
        --particle-end-y:${endY.toFixed(2)}%;
        --particle-duration:${duration.toFixed(2)}s;
        --particle-delay:${emissionDelay.toFixed(2)}s;
        --particle-width:${width.toFixed(2)}px;
        --particle-height:${height.toFixed(2)}px;
        --particle-drift-x:${driftX.toFixed(2)}px;
        --particle-opacity-start:${opacityStart.toFixed(3)};
        --particle-opacity-mid:${opacityMid.toFixed(3)};
        --particle-opacity-end:${opacityEnd.toFixed(3)};
        --particle-scale-start:${scaleStart.toFixed(3)};
        --particle-scale-mid:${scaleMid.toFixed(3)};
        --particle-scale-end:${scaleEnd.toFixed(3)};
        --particle-rotate-start:${rotationStart.toFixed(2)}deg;
        --particle-rotate-mid:${rotationMid.toFixed(2)}deg;
        --particle-rotate-end:${rotationEnd.toFixed(2)}deg;
        --particle-blur:${blur.toFixed(2)}px;
        --particle-color:${particleColor};
        --particle-color-accent:${particleAccent};
        --particle-color-end:${particleEnd};
        --particle-filter-start:${filterStart};
        --particle-filter-mid:${filterMid};
        --particle-filter-end:${filterEnd};
        --particle-blend:${getParticleBlendCssValue(config.blend)};
        ${imageStyle}
      "
    ></span>
  `;
}

function getParticleItemCount(particleEffect) {
  const config = normalizeParticleEffectConfig(particleEffect);
  const intensityMultiplier = {
    light: 0.72,
    medium: 1,
    heavy: 1.28,
  }[config.intensity];
  const areaMultiplier = config.area === "full" ? 1 : 0.64;
  const presetMultiplier = getParticlePresetDensityMultiplier(config.preset);
  const count = Math.round(config.density * intensityMultiplier * areaMultiplier * presetMultiplier);
  return clamp(Math.max(count, 6), 6, 180);
}

function getParticleImageStyle(assetId) {
  const imageUrl = getParticleImageUrl(assetId);
  return imageUrl ? `--particle-image:url("${escapeHtml(encodeURI(imageUrl))}");` : "";
}

function getParticleImageUrl(assetId) {
  const safeAssetId = getSafeParticleImageAssetId(assetId);
  return safeAssetId ? getAssetUrl(safeAssetId) : null;
}

function applyStageWorldPresentation(visualState) {
  const zoomScale = visualState.cameraZoom
    ? getCameraZoomScale(visualState.cameraZoom.action, visualState.cameraZoom.strength)
    : 1;
  const panOffset = visualState.cameraPan
    ? getCameraPanOffset(visualState.cameraPan.target, visualState.cameraPan.strength)
    : 0;
  const zoomOrigin = getCameraZoomOrigin(visualState.cameraZoom?.focus);
  const filterCss = getScreenFilterCss(visualState.screenFilter);
  const wash = getScreenFilterWash(visualState.screenFilter);
  const depthBackdropFilter = visualState.depthBlur
    ? `blur(${getDepthBlurBackdropPx(visualState.depthBlur.strength)}px) brightness(0.96)`
    : "";
  const depthParticleFilter = visualState.depthBlur
    ? `blur(${getDepthBlurParticlePx(visualState.depthBlur.strength)}px)`
    : "";

  refs.backgroundLayer.style.transform = `translate3d(${panOffset.toFixed(2)}%, 0, 0) scale(${(zoomScale * 1.02).toFixed(3)})`;
  refs.particleLayer.style.transform = `translate3d(${panOffset.toFixed(2)}%, 0, 0) scale(${zoomScale.toFixed(3)})`;
  refs.spriteLayer.style.transform = `translate3d(${panOffset.toFixed(2)}%, 0, 0) scale(${zoomScale.toFixed(3)})`;

  refs.backgroundLayer.style.transformOrigin = zoomOrigin;
  refs.particleLayer.style.transformOrigin = zoomOrigin;
  refs.spriteLayer.style.transformOrigin = zoomOrigin;

  refs.backgroundLayer.style.filter = combineFilterCss(depthBackdropFilter, filterCss) || "none";
  refs.particleLayer.style.filter = combineFilterCss(depthParticleFilter, filterCss) || "none";
  refs.spriteLayer.style.filter = filterCss || "none";
  refs.particleLayer.style.opacity = visualState.depthBlur
    ? String(getDepthBlurSpriteOpacity(visualState.depthBlur.strength))
    : "1";

  refs.filterLayer.style.setProperty("--filter-wash", wash.background);
  refs.filterLayer.style.setProperty("--filter-opacity", String(wash.opacity));
  refs.filterLayer.style.setProperty("--filter-vignette-opacity", String(getScreenFilterVignette(visualState.screenFilter)));
}

function combineFilterCss(...parts) {
  return parts.filter(Boolean).join(" ");
}

function applyStageScreenEffects(visualState, currentBlock = null) {
  refs.stageFrame.classList.toggle("is-shaking", Boolean(visualState.screenShake));

  if (visualState.screenShake) {
    refs.stageFrame.style.setProperty("--shake-distance", `${getShakeDistance(visualState.screenShake.intensity)}px`);
    refs.stageFrame.style.setProperty(
      "--shake-duration",
      `${getEffectDurationSeconds(visualState.screenShake.duration)}s`
    );
  } else {
    refs.stageFrame.style.removeProperty("--shake-distance");
    refs.stageFrame.style.removeProperty("--shake-duration");
  }

  if (visualState.screenFlash) {
    refs.flashLayer.hidden = false;
    refs.flashLayer.classList.add("is-active");
    refs.flashLayer.style.setProperty("--flash-rgb", getFlashColorRgb(visualState.screenFlash.color));
    refs.flashLayer.style.setProperty("--flash-opacity", String(getFlashOpacity(visualState.screenFlash.intensity)));
    refs.flashLayer.style.setProperty(
      "--flash-duration",
      `${getEffectDurationSeconds(visualState.screenFlash.duration)}s`
    );
  } else {
    refs.flashLayer.hidden = true;
    refs.flashLayer.classList.remove("is-active");
    refs.flashLayer.style.removeProperty("--flash-rgb");
    refs.flashLayer.style.removeProperty("--flash-opacity");
    refs.flashLayer.style.removeProperty("--flash-duration");
  }

  const fadeBlock = currentBlock?.type === "screen_fade" ? currentBlock : null;
  const fadeColor = fadeBlock ? getSafeFadeColor(fadeBlock.color) : visualState.screenFade?.color;
  const fadeDuration = fadeBlock ? getSafeEffectDuration(fadeBlock.duration) : visualState.screenFade?.duration;

  refs.fadeLayer.style.setProperty("--fade-rgb", getFadeColorRgb(fadeColor ?? "black"));
  refs.fadeLayer.style.setProperty("--fade-duration", `${getEffectDurationSeconds(fadeDuration ?? "medium")}s`);
  refs.fadeLayer.classList.toggle("is-visible", Boolean(visualState.screenFade));
}

function getBackdropStyle(backgroundAssetId) {
  const gradients = {
    bg_classroom_sunset:
      "linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.28)), linear-gradient(180deg, #f1ca93 0%, #f0b27c 36%, #b86d55 100%)",
    bg_hallway_after_school:
      "linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.28)), linear-gradient(180deg, #f6d9ac 0%, #eaa572 45%, #905742 100%)",
    bg_rooftop_evening:
      "linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0.18)), linear-gradient(180deg, #f7d7b0 0%, #d39a7a 40%, #70516f 100%)",
  };

  return gradients[backgroundAssetId] ?? gradients.bg_classroom_sunset;
}

function getVariableType(variableId) {
  return data.variablesById.get(variableId)?.type ?? "string";
}

function parseVariableNumberBound(value) {
  if (value === null || value === undefined || typeof value === "boolean") {
    return null;
  }

  const parsed = Number.parseFloat(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function getVariableNumberBounds(variableId) {
  const variable = data.variablesById.get(variableId);
  if (!variable) {
    return [null, null];
  }

  return [
    parseVariableNumberBound(variable.min ?? variable.minValue),
    parseVariableNumberBound(variable.max ?? variable.maxValue),
  ];
}

function normalizeVariableValue(variableId, value) {
  const type = getVariableType(variableId);

  if (type === "number") {
    return getSafeNumber(value, 0);
  }

  if (type === "boolean") {
    if (typeof value === "boolean") {
      return value;
    }

    if (typeof value === "string") {
      return value === "true";
    }

    return Boolean(value);
  }

  return value == null ? "" : String(value);
}

function getVariableDefaultValue(variableId) {
  const value = normalizeVariableValue(variableId, data.variablesById.get(variableId)?.defaultValue);
  return typeof value === "number" ? clampPreviewVariableNumber(variableId, value) : value;
}

function formatVariableValue(variableId, value) {
  const safeValue = normalizeVariableValue(variableId, value);
  if (typeof safeValue === "boolean") {
    return safeValue ? "开" : "关";
  }
  return String(safeValue);
}

function getSafeNumber(value, fallback = 0) {
  const parsed = Number.parseFloat(value ?? "");
  return Number.isFinite(parsed) ? parsed : fallback;
}

function getSafeBoolean(value, fallback = false) {
  if (typeof value === "boolean") {
    return value;
  }

  if (typeof value === "string") {
    const normalized = value.trim().toLowerCase();
    if (["true", "1", "yes", "on"].includes(normalized)) {
      return true;
    }
    if (["false", "0", "no", "off", ""].includes(normalized)) {
      return false;
    }
  }

  return fallback;
}

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function formatDate(value) {
  if (!value) {
    return "未知";
  }

  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString("zh-CN");
}

function truncateText(value, maxLength = 32) {
  const text = String(value ?? "").trim();

  if (text.length <= maxLength) {
    return text;
  }

  return `${text.slice(0, Math.max(maxLength - 1, 1))}…`;
}

function renderEmpty(text) {
  return `<div class="empty-note">${escapeHtml(text)}</div>`;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
