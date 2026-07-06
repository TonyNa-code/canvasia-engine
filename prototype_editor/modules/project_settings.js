(function attachProjectSettingsTools(global) {
  const runtimeSettingsTools = global.CanvasiaEditorProjectRuntimeSettings;
  const DEFAULT_RESOLUTION = Object.freeze({ width: 1280, height: 720 });
  const SUPPORTED_RESOLUTIONS = Object.freeze([
    Object.freeze({ width: 1280, height: 720, label: "HD 1280 × 720" }),
    Object.freeze({ width: 1920, height: 1080, label: "Full HD 1920 × 1080" }),
  ]);
  const SCREEN_LABELS = Object.freeze({
    dashboard: "首页",
    story: "写剧情",
    assets: "管素材",
    characters: "管角色",
    script: "台词台本",
    preview: "预览导出",
  });
  const DEFAULT_SAVE_SLOT_COUNT_LIMITS =
    runtimeSettingsTools?.DEFAULT_SAVE_SLOT_COUNT_LIMITS ?? Object.freeze({ min: 3, max: 120 });
  const DEFAULT_RUNTIME_TEXT_SPEED_LABELS = Object.freeze({
    slow: "慢一点",
    normal: "正常",
    fast: "快一点",
    instant: "立刻显示",
  });
  const DEFAULT_RUNTIME_DIALOG_THEME_LABELS = Object.freeze({
    project: "项目样式",
    warm: "暖光标准",
    moonlight: "夜色月光",
    paper: "纸页回忆",
    transparent: "透明无框",
  });
  const DEFAULT_RUNTIME_UI_THEME_MODE_LABELS = Object.freeze({
    auto: "自动切换",
    light: "浅色模式",
    dark: "深色模式",
  });
  const DEFAULT_RUNTIME_PERFORMANCE_PROFILE_LABELS = Object.freeze({
    standard: "标准 PC / 网页",
    web: "网页轻量",
    mobile_low: "低配 / 移动端",
    high_quality_pc: "高画质 PC",
  });
  const DEFAULT_RUNTIME_SETTINGS =
    runtimeSettingsTools?.DEFAULT_RUNTIME_SETTINGS ??
    Object.freeze({
      formalSaveSlotCount: 24,
      performanceProfile: "standard",
      defaultTextSpeed: "normal",
      defaultDialogTheme: "project",
      defaultUiThemeMode: "auto",
      defaultBgmVolume: 72,
      defaultSfxVolume: 85,
      defaultVoiceVolume: 92,
      defaultVoiceDuckingRatio: 45,
      defaultVoiceEnabled: true,
      defaultVoiceDuckingEnabled: true,
    });
  const DEFAULT_VOICE_DUCKING_RATIO_LIMITS =
    runtimeSettingsTools?.DEFAULT_VOICE_DUCKING_RATIO_LIMITS ?? Object.freeze({ min: 15, max: 100 });
  const DEFAULT_FRAME_SLICE = Object.freeze({ top: 18, right: 18, bottom: 18, left: 18 });
  const PROJECT_DIALOG_BOX_PRESET_LABELS = Object.freeze({
    moonlight: "夜色玻璃",
    warm: "暖光标准",
    paper: "纸页回忆",
    transparent: "透明无框",
    custom: "自定义样式",
  });
  const PROJECT_DIALOG_BOX_SHAPE_LABELS = Object.freeze({
    rounded: "圆角框",
    square: "方角框",
    capsule: "胶囊框",
  });
  const PROJECT_DIALOG_BOX_ANCHOR_LABELS = Object.freeze({
    bottom: "底部对话框",
    center: "居中对话框",
    top: "顶部字幕框",
    free: "自由偏移",
  });
  const DEFAULT_PROJECT_DIALOG_BOX_CONFIG = Object.freeze({
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
  });
  const PROJECT_DIALOG_BOX_PRESETS = Object.freeze({
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
      shape: "rounded",
      widthPercent: 78,
      minHeight: 132,
      paddingX: 18,
      paddingY: 12,
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
  });
  const PROJECT_GAME_UI_PRESET_LABELS = Object.freeze({
    stellar: "神秘科技",
    warm: "暖色轻小说",
    paper: "纸页回忆",
    minimal: "极简透明",
    custom: "自定义皮肤",
  });
  const PROJECT_GAME_UI_LAYOUT_LABELS = Object.freeze({
    balanced: "标准工作台",
    cinematic: "电影标题页",
    compact: "紧凑信息栏",
    minimal: "沉浸无侧栏",
    custom: "自定义布局",
  });
  const PROJECT_GAME_UI_TITLE_LAYOUT_LABELS = Object.freeze({
    center: "居中标题",
    left: "左侧标题",
    poster: "海报标题",
  });
  const PROJECT_GAME_UI_FONT_LABELS = Object.freeze({
    modern: "现代无衬线",
    serif: "文学衬线",
    rounded: "圆润轻快",
  });
  const PROJECT_GAME_UI_SURFACE_LABELS = Object.freeze({
    glass: "玻璃面板",
    solid: "实色面板",
    minimal: "轻量线框",
  });
  const PROJECT_GAME_UI_BRAND_LABELS = Object.freeze({
    project: "显示项目名",
    engine: "显示引擎标识",
    hidden: "隐藏品牌露出",
  });
  const PROJECT_GAME_UI_SIDE_PANEL_LABELS = Object.freeze({
    full: "完整侧栏",
    compact: "紧凑侧栏",
    hidden: "隐藏侧栏",
  });
  const PROJECT_GAME_UI_SIDE_POSITION_LABELS = Object.freeze({
    right: "侧栏在右",
    left: "侧栏在左",
  });
  const PROJECT_GAME_UI_TOPBAR_POSITION_LABELS = Object.freeze({
    top: "顶部栏在上",
    bottom: "顶部栏在下",
    hidden: "隐藏顶部栏",
  });
  const PROJECT_GAME_UI_HUD_POSITION_LABELS = Object.freeze({
    top: "顶部两端",
    "top-left": "左上角",
    "top-right": "右上角",
    "bottom-left": "左下角",
    "bottom-right": "右下角",
    hidden: "隐藏 HUD",
  });
  const PROJECT_GAME_UI_TITLE_CARD_ANCHOR_LABELS = Object.freeze({
    center: "标题居中",
    left: "标题靠左",
    right: "标题靠右",
    top: "标题靠上",
    bottom: "标题靠下",
    free: "自由偏移",
  });
  const DEFAULT_PROJECT_GAME_UI_CONFIG = Object.freeze({
    preset: "stellar",
    layoutPreset: "balanced",
    titleLayout: "center",
    fontStyle: "modern",
    fontFamily: "",
    fontAssetId: "",
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
  });
  const PROJECT_GAME_UI_PRESETS = Object.freeze({
    stellar: {
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
      titleBackgroundOpacity: 42,
      titleBackgroundFit: "cover",
      panelFrameOpacity: 18,
      buttonFrameOpacity: 24,
      uiOverlayOpacity: 8,
    },
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
  });

  function hasOwn(source, key) {
    return Object.prototype.hasOwnProperty.call(source || {}, key);
  }

  function getSafeNumber(value, fallback = 0, options = {}) {
    if (typeof options.getSafeNumber === "function") {
      return options.getSafeNumber(value, fallback);
    }
    const parsed = Number.parseFloat(value ?? "");
    return Number.isFinite(parsed) ? parsed : fallback;
  }

  function clamp(value, min, max, options = {}) {
    if (typeof options.clamp === "function") {
      return options.clamp(value, min, max);
    }
    return Math.min(Math.max(value, min), max);
  }

  function getSafeColor(value, fallback = "#ffffff", options = {}) {
    if (typeof options.getSafeColor === "function") {
      return options.getSafeColor(value, fallback);
    }
    const text = String(value ?? "").trim();
    if (/^#[0-9a-fA-F]{6}$/.test(text)) {
      return text.toLowerCase();
    }
    return String(fallback ?? "#ffffff").trim().toLowerCase();
  }

  function getSafeLabelKey(labels, value, fallback) {
    return hasOwn(labels, value) ? value : fallback;
  }

  function getProjectResolution(project, options = {}) {
    const fallbackResolution = options.defaultResolution || DEFAULT_RESOLUTION;
    const width = Number.parseInt(project?.resolution?.width ?? fallbackResolution.width, 10);
    const height = Number.parseInt(project?.resolution?.height ?? fallbackResolution.height, 10);

    return {
      width: Number.isFinite(width) ? width : fallbackResolution.width,
      height: Number.isFinite(height) ? height : fallbackResolution.height,
    };
  }

  function getResolutionLabel(width, height, options = {}) {
    const supportedResolutions = options.supportedResolutions || SUPPORTED_RESOLUTIONS;
    return supportedResolutions.find((item) => item.width === width && item.height === height)?.label ?? `${width} × ${height}`;
  }

  function getScreenLabel(screenName, options = {}) {
    const labels = options.screenLabels || SCREEN_LABELS;
    return labels[screenName] ?? screenName ?? "页面";
  }

  function getStageContainerStyle(project, options = {}) {
    const resolution = getProjectResolution(project, options);
    return `--stage-ratio: ${resolution.width} / ${resolution.height};${options.large === true ? " max-width: 100%;" : ""}`;
  }

  function renderResolutionButtons(project, options = {}) {
    const escapeHtml =
      typeof options.escapeHtml === "function"
        ? options.escapeHtml
        : (value) =>
            String(value ?? "")
              .replace(/&/g, "&amp;")
              .replace(/</g, "&lt;")
              .replace(/>/g, "&gt;")
              .replace(/"/g, "&quot;")
              .replace(/'/g, "&#39;");
    const resolution = getProjectResolution(project, options);
    const supportedResolutions = options.supportedResolutions || SUPPORTED_RESOLUTIONS;

    return supportedResolutions
      .map(
        (item) => `
          <button
            class="toolbar-button ${item.width === resolution.width && item.height === resolution.height ? "toolbar-button-primary" : ""}"
            data-action="set-resolution"
            data-width="${item.width}"
            data-height="${item.height}"
          >
            ${escapeHtml(item.label)}
          </button>
        `
      )
      .join("");
  }

  function getSafeProjectFormalSaveSlotCount(value, options = {}) {
    if (runtimeSettingsTools?.getSafeProjectFormalSaveSlotCount) {
      return runtimeSettingsTools.getSafeProjectFormalSaveSlotCount(value, options);
    }
    const limits = options.saveSlotCountLimits || DEFAULT_SAVE_SLOT_COUNT_LIMITS;
    const defaults = options.defaultRuntimeSettings || DEFAULT_RUNTIME_SETTINGS;
    return clamp(Math.round(getSafeNumber(value, defaults.formalSaveSlotCount, options)), limits.min, limits.max, options);
  }

  function getSafeProjectRuntimeTextSpeed(value, options = {}) {
    if (runtimeSettingsTools?.getSafeProjectRuntimeTextSpeed) {
      return runtimeSettingsTools.getSafeProjectRuntimeTextSpeed(value, options);
    }
    const labels = options.runtimeTextSpeedLabels || DEFAULT_RUNTIME_TEXT_SPEED_LABELS;
    const defaults = options.defaultRuntimeSettings || DEFAULT_RUNTIME_SETTINGS;
    return getSafeLabelKey(labels, value, defaults.defaultTextSpeed);
  }

  function getSafeProjectRuntimeDialogTheme(value, options = {}) {
    if (runtimeSettingsTools?.getSafeProjectRuntimeDialogTheme) {
      return runtimeSettingsTools.getSafeProjectRuntimeDialogTheme(value, options);
    }
    const labels = options.runtimeDialogThemeLabels || DEFAULT_RUNTIME_DIALOG_THEME_LABELS;
    const defaults = options.defaultRuntimeSettings || DEFAULT_RUNTIME_SETTINGS;
    return getSafeLabelKey(labels, value, defaults.defaultDialogTheme);
  }

  function getSafeProjectRuntimeUiThemeMode(value, options = {}) {
    if (runtimeSettingsTools?.getSafeProjectRuntimeUiThemeMode) {
      return runtimeSettingsTools.getSafeProjectRuntimeUiThemeMode(value, options);
    }
    const labels = options.runtimeUiThemeModeLabels || DEFAULT_RUNTIME_UI_THEME_MODE_LABELS;
    const defaults = options.defaultRuntimeSettings || DEFAULT_RUNTIME_SETTINGS;
    return getSafeLabelKey(labels, value, defaults.defaultUiThemeMode);
  }

  function getSafeProjectRuntimePerformanceProfile(value, options = {}) {
    if (runtimeSettingsTools?.getSafeProjectRuntimePerformanceProfile) {
      return runtimeSettingsTools.getSafeProjectRuntimePerformanceProfile(value, options);
    }
    const labels = options.runtimePerformanceProfileLabels || DEFAULT_RUNTIME_PERFORMANCE_PROFILE_LABELS;
    const defaults = options.defaultRuntimeSettings || DEFAULT_RUNTIME_SETTINGS;
    return getSafeLabelKey(labels, value, defaults.performanceProfile ?? DEFAULT_RUNTIME_SETTINGS.performanceProfile);
  }

  function getSafeProjectRuntimeVolume(value, fallback = 100, options = {}) {
    if (runtimeSettingsTools?.getSafeProjectRuntimeVolume) {
      return runtimeSettingsTools.getSafeProjectRuntimeVolume(value, fallback, options);
    }
    return clamp(Math.round(getSafeNumber(value, fallback, options)), 0, 100, options);
  }

  function getSafeProjectRuntimeVoiceDuckingRatio(value, fallback = DEFAULT_RUNTIME_SETTINGS.defaultVoiceDuckingRatio, options = {}) {
    if (runtimeSettingsTools?.getSafeProjectRuntimeVoiceDuckingRatio) {
      return runtimeSettingsTools.getSafeProjectRuntimeVoiceDuckingRatio(value, fallback, options);
    }
    return clamp(
      Math.round(getSafeNumber(value, fallback, options)),
      DEFAULT_VOICE_DUCKING_RATIO_LIMITS.min,
      DEFAULT_VOICE_DUCKING_RATIO_LIMITS.max,
      options
    );
  }

  function getProjectRuntimeSettings(project, options = {}) {
    if (runtimeSettingsTools?.getProjectRuntimeSettings) {
      return runtimeSettingsTools.getProjectRuntimeSettings(project, options);
    }
    const runtimeSettings = project?.runtimeSettings ?? {};
    const defaults = options.defaultRuntimeSettings || DEFAULT_RUNTIME_SETTINGS;
    return {
      formalSaveSlotCount: getSafeProjectFormalSaveSlotCount(runtimeSettings.formalSaveSlotCount, options),
      performanceProfile: getSafeProjectRuntimePerformanceProfile(runtimeSettings.performanceProfile, options),
      defaultTextSpeed: getSafeProjectRuntimeTextSpeed(runtimeSettings.defaultTextSpeed, options),
      defaultDialogTheme: getSafeProjectRuntimeDialogTheme(runtimeSettings.defaultDialogTheme, options),
      defaultUiThemeMode: getSafeProjectRuntimeUiThemeMode(runtimeSettings.defaultUiThemeMode, options),
      defaultBgmVolume: getSafeProjectRuntimeVolume(runtimeSettings.defaultBgmVolume, defaults.defaultBgmVolume, options),
      defaultSfxVolume: getSafeProjectRuntimeVolume(runtimeSettings.defaultSfxVolume, defaults.defaultSfxVolume, options),
      defaultVoiceVolume: getSafeProjectRuntimeVolume(
        runtimeSettings.defaultVoiceVolume,
        defaults.defaultVoiceVolume,
        options
      ),
      defaultVoiceDuckingRatio: getSafeProjectRuntimeVoiceDuckingRatio(
        runtimeSettings.defaultVoiceDuckingRatio,
        defaults.defaultVoiceDuckingRatio,
        options
      ),
      defaultVoiceEnabled: runtimeSettings.defaultVoiceEnabled !== false,
      defaultVoiceDuckingEnabled: runtimeSettings.defaultVoiceDuckingEnabled !== false,
    };
  }

  function getProjectFormalSaveSlotCount(project, options = {}) {
    if (runtimeSettingsTools?.getProjectFormalSaveSlotCount) {
      return runtimeSettingsTools.getProjectFormalSaveSlotCount(project, options);
    }
    return getProjectRuntimeSettings(project, options).formalSaveSlotCount;
  }

  function getSafeProjectDialogBoxPreset(value, options = {}) {
    return getSafeLabelKey(
      options.dialogBoxPresetLabels || PROJECT_DIALOG_BOX_PRESET_LABELS,
      value,
      (options.defaultDialogBoxConfig || DEFAULT_PROJECT_DIALOG_BOX_CONFIG).preset
    );
  }

  function getSafeProjectDialogBoxShape(value, options = {}) {
    return getSafeLabelKey(
      options.dialogBoxShapeLabels || PROJECT_DIALOG_BOX_SHAPE_LABELS,
      value,
      (options.defaultDialogBoxConfig || DEFAULT_PROJECT_DIALOG_BOX_CONFIG).shape
    );
  }

  function getSafeProjectDialogBoxAnchor(value, options = {}) {
    return getSafeLabelKey(
      options.dialogBoxAnchorLabels || PROJECT_DIALOG_BOX_ANCHOR_LABELS,
      value,
      (options.defaultDialogBoxConfig || DEFAULT_PROJECT_DIALOG_BOX_CONFIG).anchor
    );
  }

  function getProjectDialogBoxPresetConfig(preset, options = {}) {
    const defaultConfig = options.defaultDialogBoxConfig || DEFAULT_PROJECT_DIALOG_BOX_CONFIG;
    const presets = options.dialogBoxPresets || PROJECT_DIALOG_BOX_PRESETS;
    const safePreset = getSafeProjectDialogBoxPreset(preset, options);
    return {
      ...defaultConfig,
      ...(presets[safePreset] ?? {}),
      preset: safePreset,
    };
  }

  function getProjectDialogBoxConfig(project, options = {}) {
    const source = project?.dialogBoxConfig ?? {};
    const base = getProjectDialogBoxPresetConfig(source.preset, options);
    return {
      ...base,
      preset: getSafeProjectDialogBoxPreset(source.preset ?? base.preset, options),
      shape: getSafeProjectDialogBoxShape(source.shape ?? base.shape, options),
      widthPercent: clamp(getSafeNumber(source.widthPercent, base.widthPercent, options), 55, 100, options),
      minHeight: clamp(getSafeNumber(source.minHeight, base.minHeight, options), 96, 320, options),
      paddingX: clamp(getSafeNumber(source.paddingX, base.paddingX, options), 8, 72, options),
      paddingY: clamp(getSafeNumber(source.paddingY, base.paddingY, options), 6, 48, options),
      backgroundColor: getSafeColor(source.backgroundColor, base.backgroundColor, options),
      backgroundOpacity: clamp(getSafeNumber(source.backgroundOpacity, base.backgroundOpacity, options), 0, 100, options),
      borderColor: getSafeColor(source.borderColor, base.borderColor, options),
      borderOpacity: clamp(getSafeNumber(source.borderOpacity, base.borderOpacity, options), 0, 100, options),
      textColor: getSafeColor(source.textColor, base.textColor, options),
      speakerColor: getSafeColor(source.speakerColor, base.speakerColor, options),
      hintColor: getSafeColor(source.hintColor, base.hintColor, options),
      blurStrength: clamp(getSafeNumber(source.blurStrength, base.blurStrength, options), 0, 24, options),
      borderWidth: clamp(getSafeNumber(source.borderWidth, base.borderWidth, options), 0, 4, options),
      shadowStrength: clamp(getSafeNumber(source.shadowStrength, base.shadowStrength, options), 0, 48, options),
      panelAssetId: String(source.panelAssetId ?? "").trim(),
      panelAssetOpacity: clamp(getSafeNumber(source.panelAssetOpacity, base.panelAssetOpacity, options), 0, 100, options),
      panelAssetFit: source.panelAssetFit === "contain" ? "contain" : "cover",
      anchor: getSafeProjectDialogBoxAnchor(source.anchor ?? base.anchor, options),
      offsetXPercent: clamp(getSafeNumber(source.offsetXPercent, base.offsetXPercent, options), -35, 35, options),
      offsetYPercent: clamp(getSafeNumber(source.offsetYPercent, base.offsetYPercent, options), -35, 35, options),
    };
  }

  function getSafeProjectGameUiPreset(value, options = {}) {
    return getSafeLabelKey(
      options.gameUiPresetLabels || PROJECT_GAME_UI_PRESET_LABELS,
      value,
      (options.defaultGameUiConfig || DEFAULT_PROJECT_GAME_UI_CONFIG).preset
    );
  }

  function getSafeProjectGameUiLayoutPreset(value, options = {}) {
    const defaults = options.defaultGameUiConfig || DEFAULT_PROJECT_GAME_UI_CONFIG;
    return getSafeLabelKey(
      options.gameUiLayoutLabels || PROJECT_GAME_UI_LAYOUT_LABELS,
      value,
      defaults.layoutPreset
    );
  }

  function getSafeProjectGameUiTitleLayout(value, options = {}) {
    return getSafeLabelKey(
      options.gameUiTitleLayoutLabels || PROJECT_GAME_UI_TITLE_LAYOUT_LABELS,
      value,
      (options.defaultGameUiConfig || DEFAULT_PROJECT_GAME_UI_CONFIG).titleLayout
    );
  }

  function getSafeProjectGameUiFontStyle(value, options = {}) {
    return getSafeLabelKey(
      options.gameUiFontLabels || PROJECT_GAME_UI_FONT_LABELS,
      value,
      (options.defaultGameUiConfig || DEFAULT_PROJECT_GAME_UI_CONFIG).fontStyle
    );
  }

  function getSafeProjectGameUiSurfaceStyle(value, options = {}) {
    return getSafeLabelKey(
      options.gameUiSurfaceLabels || PROJECT_GAME_UI_SURFACE_LABELS,
      value,
      (options.defaultGameUiConfig || DEFAULT_PROJECT_GAME_UI_CONFIG).surfaceStyle
    );
  }

  function getSafeProjectGameUiBrandMode(value, options = {}) {
    return getSafeLabelKey(
      options.gameUiBrandLabels || PROJECT_GAME_UI_BRAND_LABELS,
      value,
      (options.defaultGameUiConfig || DEFAULT_PROJECT_GAME_UI_CONFIG).brandMode
    );
  }

  function getSafeProjectGameUiSidePanelMode(value, options = {}) {
    const defaults = options.defaultGameUiConfig || DEFAULT_PROJECT_GAME_UI_CONFIG;
    return getSafeLabelKey(
      options.gameUiSidePanelLabels || PROJECT_GAME_UI_SIDE_PANEL_LABELS,
      value,
      defaults.sidePanelMode
    );
  }

  function getSafeProjectGameUiSidePanelPosition(value, options = {}) {
    const defaults = options.defaultGameUiConfig || DEFAULT_PROJECT_GAME_UI_CONFIG;
    return getSafeLabelKey(
      options.gameUiSidePositionLabels || PROJECT_GAME_UI_SIDE_POSITION_LABELS,
      value,
      defaults.sidePanelPosition
    );
  }

  function getSafeProjectGameUiTopbarPosition(value, options = {}) {
    const defaults = options.defaultGameUiConfig || DEFAULT_PROJECT_GAME_UI_CONFIG;
    return getSafeLabelKey(
      options.gameUiTopbarPositionLabels || PROJECT_GAME_UI_TOPBAR_POSITION_LABELS,
      value,
      defaults.topbarPosition
    );
  }

  function getSafeProjectGameUiHudPosition(value, options = {}) {
    return getSafeLabelKey(
      options.gameUiHudPositionLabels || PROJECT_GAME_UI_HUD_POSITION_LABELS,
      value,
      (options.defaultGameUiConfig || DEFAULT_PROJECT_GAME_UI_CONFIG).hudPosition
    );
  }

  function getSafeProjectGameUiTitleCardAnchor(value, options = {}) {
    const defaults = options.defaultGameUiConfig || DEFAULT_PROJECT_GAME_UI_CONFIG;
    return getSafeLabelKey(
      options.gameUiTitleCardAnchorLabels || PROJECT_GAME_UI_TITLE_CARD_ANCHOR_LABELS,
      value,
      defaults.titleCardAnchor
    );
  }

  function getSafeGameUiFrameSlice(value, fallback = DEFAULT_FRAME_SLICE, options = {}) {
    const source = value && typeof value === "object" ? value : {};
    return {
      top: clamp(getSafeNumber(source.top, fallback.top, options), 0, 96, options),
      right: clamp(getSafeNumber(source.right, fallback.right, options), 0, 96, options),
      bottom: clamp(getSafeNumber(source.bottom, fallback.bottom, options), 0, 96, options),
      left: clamp(getSafeNumber(source.left, fallback.left, options), 0, 96, options),
    };
  }

  function getProjectGameUiPresetConfig(preset, options = {}) {
    const defaultConfig = options.defaultGameUiConfig || DEFAULT_PROJECT_GAME_UI_CONFIG;
    const presets = options.gameUiPresets || PROJECT_GAME_UI_PRESETS;
    const safePreset = getSafeProjectGameUiPreset(preset, options);
    return {
      ...defaultConfig,
      ...(presets[safePreset] ?? {}),
      preset: safePreset,
    };
  }

  function getProjectGameUiConfig(project, options = {}) {
    const source = project?.gameUiConfig ?? {};
    const base = getProjectGameUiPresetConfig(source.preset, options);
    return {
      ...base,
      preset: getSafeProjectGameUiPreset(source.preset ?? base.preset, options),
      layoutPreset: getSafeProjectGameUiLayoutPreset(source.layoutPreset ?? base.layoutPreset, options),
      titleLayout: getSafeProjectGameUiTitleLayout(source.titleLayout ?? base.titleLayout, options),
      fontStyle: getSafeProjectGameUiFontStyle(source.fontStyle ?? base.fontStyle, options),
      fontFamily: String(source.fontFamily ?? base.fontFamily ?? "").trim().slice(0, 80),
      fontAssetId: String(source.fontAssetId ?? base.fontAssetId ?? "").trim(),
      surfaceStyle: getSafeProjectGameUiSurfaceStyle(source.surfaceStyle ?? base.surfaceStyle, options),
      brandMode: getSafeProjectGameUiBrandMode(source.brandMode ?? base.brandMode, options),
      sidePanelMode: getSafeProjectGameUiSidePanelMode(source.sidePanelMode ?? base.sidePanelMode, options),
      sidePanelPosition: getSafeProjectGameUiSidePanelPosition(source.sidePanelPosition ?? base.sidePanelPosition, options),
      topbarPosition: getSafeProjectGameUiTopbarPosition(source.topbarPosition ?? base.topbarPosition, options),
      hudPosition: getSafeProjectGameUiHudPosition(source.hudPosition ?? base.hudPosition, options),
      titleCardAnchor: getSafeProjectGameUiTitleCardAnchor(source.titleCardAnchor ?? base.titleCardAnchor, options),
      titleCardOffsetXPercent: clamp(
        getSafeNumber(source.titleCardOffsetXPercent, base.titleCardOffsetXPercent, options),
        -35,
        35,
        options
      ),
      titleCardOffsetYPercent: clamp(
        getSafeNumber(source.titleCardOffsetYPercent, base.titleCardOffsetYPercent, options),
        -35,
        35,
        options
      ),
      layoutGap: clamp(getSafeNumber(source.layoutGap, base.layoutGap, options), 8, 48, options),
      sidePanelWidth: clamp(getSafeNumber(source.sidePanelWidth, base.sidePanelWidth, options), 240, 460, options),
      backgroundColor: getSafeColor(source.backgroundColor, base.backgroundColor, options),
      backgroundAccentColor: getSafeColor(source.backgroundAccentColor, base.backgroundAccentColor, options),
      panelColor: getSafeColor(source.panelColor, base.panelColor, options),
      panelOpacity: clamp(getSafeNumber(source.panelOpacity, base.panelOpacity, options), 35, 100, options),
      textColor: getSafeColor(source.textColor, base.textColor, options),
      mutedTextColor: getSafeColor(source.mutedTextColor, base.mutedTextColor, options),
      accentColor: getSafeColor(source.accentColor, base.accentColor, options),
      accentAltColor: getSafeColor(source.accentAltColor, base.accentAltColor, options),
      buttonTextColor: getSafeColor(source.buttonTextColor, base.buttonTextColor, options),
      borderColor: getSafeColor(source.borderColor, base.borderColor, options),
      borderOpacity: clamp(getSafeNumber(source.borderOpacity, base.borderOpacity, options), 0, 100, options),
      cornerRadius: clamp(getSafeNumber(source.cornerRadius, base.cornerRadius, options), 4, 42, options),
      backdropBlur: clamp(getSafeNumber(source.backdropBlur, base.backdropBlur, options), 0, 28, options),
      stageVignette: clamp(getSafeNumber(source.stageVignette, base.stageVignette, options), 0, 80, options),
      motionIntensity: clamp(getSafeNumber(source.motionIntensity, base.motionIntensity, options), 0, 100, options),
      titleBackgroundAssetId: String(source.titleBackgroundAssetId ?? "").trim(),
      titleBackgroundFit: source.titleBackgroundFit === "contain" ? "contain" : "cover",
      titleBackgroundOpacity: clamp(
        getSafeNumber(source.titleBackgroundOpacity, base.titleBackgroundOpacity, options),
        0,
        100,
        options
      ),
      titleLogoAssetId: String(source.titleLogoAssetId ?? "").trim(),
      panelFrameAssetId: String(source.panelFrameAssetId ?? "").trim(),
      panelFrameOpacity: clamp(getSafeNumber(source.panelFrameOpacity, base.panelFrameOpacity, options), 0, 100, options),
      panelFrameSlice: getSafeGameUiFrameSlice(source.panelFrameSlice, base.panelFrameSlice, options),
      buttonFrameAssetId: String(source.buttonFrameAssetId ?? "").trim(),
      buttonHoverFrameAssetId: String(source.buttonHoverFrameAssetId ?? "").trim(),
      buttonPressedFrameAssetId: String(source.buttonPressedFrameAssetId ?? "").trim(),
      buttonDisabledFrameAssetId: String(source.buttonDisabledFrameAssetId ?? "").trim(),
      buttonFrameOpacity: clamp(getSafeNumber(source.buttonFrameOpacity, base.buttonFrameOpacity, options), 0, 100, options),
      buttonFrameSlice: getSafeGameUiFrameSlice(source.buttonFrameSlice, base.buttonFrameSlice, options),
      saveSlotFrameAssetId: String(source.saveSlotFrameAssetId ?? "").trim(),
      systemPanelFrameAssetId: String(source.systemPanelFrameAssetId ?? "").trim(),
      uiOverlayAssetId: String(source.uiOverlayAssetId ?? "").trim(),
      uiOverlayOpacity: clamp(getSafeNumber(source.uiOverlayOpacity, base.uiOverlayOpacity, options), 0, 100, options),
    };
  }

  function toRgbaString(hexColor, opacityPercent, options = {}) {
    const safeHex = getSafeColor(hexColor, "#ffffff", options).slice(1);
    const red = Number.parseInt(safeHex.slice(0, 2), 16);
    const green = Number.parseInt(safeHex.slice(2, 4), 16);
    const blue = Number.parseInt(safeHex.slice(4, 6), 16);
    const alpha = clamp(getSafeNumber(opacityPercent, 100, options), 0, 100, options) / 100;
    return `rgba(${red}, ${green}, ${blue}, ${alpha.toFixed(2)})`;
  }

  function getDialogShapeRadius(shape, fallbackRadius = 18, options = {}) {
    const safeShape = getSafeProjectDialogBoxShape(shape, options);
    if (safeShape === "square") {
      return 6;
    }
    if (safeShape === "capsule") {
      return 999;
    }
    return clamp(getSafeNumber(fallbackRadius, 18, options), 8, 42, options);
  }

  global.CanvasiaEditorProjectSettings = Object.freeze({
    DEFAULT_RESOLUTION,
    SUPPORTED_RESOLUTIONS,
    SCREEN_LABELS,
    PROJECT_DIALOG_BOX_PRESET_LABELS,
    PROJECT_DIALOG_BOX_SHAPE_LABELS,
    PROJECT_DIALOG_BOX_ANCHOR_LABELS,
    DEFAULT_PROJECT_DIALOG_BOX_CONFIG,
    PROJECT_DIALOG_BOX_PRESETS,
    PROJECT_GAME_UI_PRESET_LABELS,
    PROJECT_GAME_UI_LAYOUT_LABELS,
    PROJECT_GAME_UI_TITLE_LAYOUT_LABELS,
    PROJECT_GAME_UI_FONT_LABELS,
    PROJECT_GAME_UI_SURFACE_LABELS,
    PROJECT_GAME_UI_BRAND_LABELS,
    PROJECT_GAME_UI_SIDE_PANEL_LABELS,
    PROJECT_GAME_UI_SIDE_POSITION_LABELS,
    PROJECT_GAME_UI_TOPBAR_POSITION_LABELS,
    PROJECT_GAME_UI_HUD_POSITION_LABELS,
    PROJECT_GAME_UI_TITLE_CARD_ANCHOR_LABELS,
    DEFAULT_PROJECT_GAME_UI_CONFIG,
    PROJECT_GAME_UI_PRESETS,
    getProjectResolution,
    getResolutionLabel,
    getScreenLabel,
    getStageContainerStyle,
    renderResolutionButtons,
    getSafeProjectFormalSaveSlotCount,
    getSafeProjectRuntimeTextSpeed,
    getSafeProjectRuntimeDialogTheme,
    getSafeProjectRuntimeUiThemeMode,
    getSafeProjectRuntimePerformanceProfile,
    getSafeProjectRuntimeVolume,
    getSafeProjectRuntimeVoiceDuckingRatio,
    getProjectRuntimeSettings,
    getProjectFormalSaveSlotCount,
    getSafeProjectDialogBoxPreset,
    getSafeProjectDialogBoxShape,
    getSafeProjectDialogBoxAnchor,
    getProjectDialogBoxPresetConfig,
    getProjectDialogBoxConfig,
    getSafeProjectGameUiPreset,
    getSafeProjectGameUiLayoutPreset,
    getSafeProjectGameUiTitleLayout,
    getSafeProjectGameUiFontStyle,
    getSafeProjectGameUiSurfaceStyle,
    getSafeProjectGameUiBrandMode,
    getSafeProjectGameUiSidePanelMode,
    getSafeProjectGameUiSidePanelPosition,
    getSafeProjectGameUiTopbarPosition,
    getSafeProjectGameUiHudPosition,
    getSafeProjectGameUiTitleCardAnchor,
    getSafeGameUiFrameSlice,
    getProjectGameUiPresetConfig,
    getProjectGameUiConfig,
    toRgbaString,
    getDialogShapeRadius,
  });
})(typeof window !== "undefined" ? window : globalThis);
