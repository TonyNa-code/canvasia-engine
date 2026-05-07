(function attachProjectSettingsTools(global) {
  const DEFAULT_RESOLUTION = Object.freeze({ width: 1280, height: 720 });
  const DEFAULT_SAVE_SLOT_COUNT_LIMITS = Object.freeze({ min: 3, max: 120 });
  const DEFAULT_RUNTIME_SETTINGS = Object.freeze({ formalSaveSlotCount: 24 });
  const DEFAULT_FRAME_SLICE = Object.freeze({ top: 18, right: 18, bottom: 18, left: 18 });

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

  function getSafeProjectFormalSaveSlotCount(value, options = {}) {
    const limits = options.saveSlotCountLimits || DEFAULT_SAVE_SLOT_COUNT_LIMITS;
    const defaults = options.defaultRuntimeSettings || DEFAULT_RUNTIME_SETTINGS;
    return clamp(
      Math.round(getSafeNumber(value, defaults.formalSaveSlotCount, options)),
      limits.min,
      limits.max,
      options
    );
  }

  function getProjectRuntimeSettings(project, options = {}) {
    const runtimeSettings = project?.runtimeSettings ?? {};
    return {
      formalSaveSlotCount: getSafeProjectFormalSaveSlotCount(runtimeSettings.formalSaveSlotCount, options),
    };
  }

  function getProjectFormalSaveSlotCount(project, options = {}) {
    return getProjectRuntimeSettings(project, options).formalSaveSlotCount;
  }

  function getSafeProjectDialogBoxPreset(value, options = {}) {
    return getSafeLabelKey(
      options.dialogBoxPresetLabels,
      value,
      options.defaultDialogBoxConfig?.preset ?? "moonlight"
    );
  }

  function getSafeProjectDialogBoxShape(value, options = {}) {
    return getSafeLabelKey(
      options.dialogBoxShapeLabels,
      value,
      options.defaultDialogBoxConfig?.shape ?? "rounded"
    );
  }

  function getSafeProjectDialogBoxAnchor(value, options = {}) {
    return getSafeLabelKey(
      options.dialogBoxAnchorLabels,
      value,
      options.defaultDialogBoxConfig?.anchor ?? "bottom"
    );
  }

  function getProjectDialogBoxPresetConfig(preset, options = {}) {
    const defaultConfig = options.defaultDialogBoxConfig || {};
    const safePreset = getSafeProjectDialogBoxPreset(preset, options);
    return {
      ...defaultConfig,
      ...(options.dialogBoxPresets?.[safePreset] ?? {}),
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
    return getSafeLabelKey(options.gameUiPresetLabels, value, options.defaultGameUiConfig?.preset ?? "stellar");
  }

  function getSafeProjectGameUiLayoutPreset(value, options = {}) {
    return getSafeLabelKey(
      options.gameUiLayoutLabels,
      value,
      options.defaultGameUiConfig?.layoutPreset ?? "balanced"
    );
  }

  function getSafeProjectGameUiTitleLayout(value, options = {}) {
    return getSafeLabelKey(options.gameUiTitleLayoutLabels, value, options.defaultGameUiConfig?.titleLayout ?? "center");
  }

  function getSafeProjectGameUiFontStyle(value, options = {}) {
    return getSafeLabelKey(options.gameUiFontLabels, value, options.defaultGameUiConfig?.fontStyle ?? "modern");
  }

  function getSafeProjectGameUiSurfaceStyle(value, options = {}) {
    return getSafeLabelKey(options.gameUiSurfaceLabels, value, options.defaultGameUiConfig?.surfaceStyle ?? "glass");
  }

  function getSafeProjectGameUiBrandMode(value, options = {}) {
    return getSafeLabelKey(options.gameUiBrandLabels, value, options.defaultGameUiConfig?.brandMode ?? "project");
  }

  function getSafeProjectGameUiSidePanelMode(value, options = {}) {
    return getSafeLabelKey(
      options.gameUiSidePanelLabels,
      value,
      options.defaultGameUiConfig?.sidePanelMode ?? "full"
    );
  }

  function getSafeProjectGameUiSidePanelPosition(value, options = {}) {
    return getSafeLabelKey(
      options.gameUiSidePositionLabels,
      value,
      options.defaultGameUiConfig?.sidePanelPosition ?? "right"
    );
  }

  function getSafeProjectGameUiTopbarPosition(value, options = {}) {
    return getSafeLabelKey(
      options.gameUiTopbarPositionLabels,
      value,
      options.defaultGameUiConfig?.topbarPosition ?? "top"
    );
  }

  function getSafeProjectGameUiHudPosition(value, options = {}) {
    return getSafeLabelKey(options.gameUiHudPositionLabels, value, options.defaultGameUiConfig?.hudPosition ?? "top");
  }

  function getSafeProjectGameUiTitleCardAnchor(value, options = {}) {
    return getSafeLabelKey(
      options.gameUiTitleCardAnchorLabels,
      value,
      options.defaultGameUiConfig?.titleCardAnchor ?? "center"
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
    const defaultConfig = options.defaultGameUiConfig || {};
    const safePreset = getSafeProjectGameUiPreset(preset, options);
    return {
      ...defaultConfig,
      ...(options.gameUiPresets?.[safePreset] ?? {}),
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

  global.TonyNaEditorProjectSettings = Object.freeze({
    getProjectResolution,
    getSafeProjectFormalSaveSlotCount,
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
