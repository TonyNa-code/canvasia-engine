(function attachVisualEffectTools(global) {
  const SHAKE_INTENSITY_LABELS = Object.freeze({
    light: "轻微",
    medium: "明显",
    heavy: "很强",
  });

  const EFFECT_DURATION_LABELS = Object.freeze({
    short: "短一下",
    medium: "正常",
    long: "久一点",
  });

  const FLASH_COLOR_LABELS = Object.freeze({
    white: "白闪",
    warm: "暖光",
    red: "红闪",
    black: "黑闪",
  });

  const FLASH_INTENSITY_LABELS = Object.freeze({
    soft: "柔和",
    medium: "明显",
    strong: "很亮",
  });

  const FADE_ACTION_LABELS = Object.freeze({
    fade_out: "慢慢淡出",
    fade_in: "慢慢亮起",
  });

  const FADE_COLOR_LABELS = Object.freeze({
    black: "黑场",
    white: "白场",
  });

  const CAMERA_ZOOM_ACTION_LABELS = Object.freeze({
    zoom_in: "推近镜头",
    zoom_out: "拉远镜头",
    reset: "恢复正常",
  });

  const CAMERA_ZOOM_STRENGTH_LABELS = Object.freeze({
    light: "轻一点",
    medium: "明显",
    heavy: "更强",
  });

  const CAMERA_ZOOM_FOCUS_LABELS = Object.freeze({
    left: "看左侧",
    center: "看中间",
    right: "看右侧",
  });

  const SCREEN_FILTER_ACTION_LABELS = Object.freeze({
    apply: "开启滤镜",
    clear: "关闭滤镜",
  });

  const SCREEN_FILTER_PRESET_LABELS = Object.freeze({
    memory: "暖色回忆",
    mono: "黑白回忆",
    dream: "梦境柔光",
    cold: "冷色回放",
  });

  const SCREEN_FILTER_STRENGTH_LABELS = Object.freeze({
    soft: "轻一点",
    medium: "正常",
    strong: "更明显",
  });

  const CAMERA_PAN_TARGET_LABELS = Object.freeze({
    left: "向左看",
    center: "回到中间",
    right: "向右看",
  });

  const CAMERA_PAN_STRENGTH_LABELS = Object.freeze({
    light: "轻一点",
    medium: "明显",
    heavy: "更远",
  });

  const DEPTH_BLUR_ACTION_LABELS = Object.freeze({
    apply: "开启景深",
    clear: "关闭景深",
  });

  const DEPTH_BLUR_FOCUS_LABELS = Object.freeze({
    left: "左侧角色更清楚",
    center: "中间角色更清楚",
    right: "右侧角色更清楚",
    full: "只虚化背景",
  });

  const DEPTH_BLUR_STRENGTH_LABELS = Object.freeze({
    soft: "轻一点",
    medium: "正常",
    strong: "更明显",
  });

  const VIDEO_FIT_LABELS = Object.freeze({
    contain: "完整显示",
    cover: "铺满裁切",
    fill: "拉伸填满",
  });

  const VIDEO_VOLUME_LABELS = Object.freeze({
    0: "静音",
    25: "25%",
    50: "50%",
    75: "75%",
    100: "100%",
  });

  const CREDITS_BACKGROUND_LABELS = Object.freeze({
    dark: "深色电影片尾",
    light: "浅色清爽片尾",
    transparent: "叠在当前画面上",
  });

  function hasOwn(source, key) {
    return Object.prototype.hasOwnProperty.call(source, key);
  }

  function getSafeLabelKey(source, value, fallback) {
    const safeValue = String(value ?? "").trim();
    return hasOwn(source, safeValue) ? safeValue : fallback;
  }

  function clamp(value, min, max) {
    return Math.min(Math.max(value, min), max);
  }

  function getSafeShakeIntensity(intensity) {
    return getSafeLabelKey(SHAKE_INTENSITY_LABELS, intensity, "medium");
  }

  function getShakeIntensityLabel(intensity) {
    return SHAKE_INTENSITY_LABELS[getSafeShakeIntensity(intensity)];
  }

  function getSafeEffectDuration(duration) {
    return getSafeLabelKey(EFFECT_DURATION_LABELS, duration, "medium");
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
    return getSafeLabelKey(FLASH_COLOR_LABELS, color, "white");
  }

  function getFlashColorLabel(color) {
    return FLASH_COLOR_LABELS[getSafeFlashColor(color)];
  }

  function getSafeFlashIntensity(intensity) {
    return getSafeLabelKey(FLASH_INTENSITY_LABELS, intensity, "medium");
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
    return getSafeLabelKey(FADE_ACTION_LABELS, action, "fade_out");
  }

  function getFadeActionLabel(action) {
    return FADE_ACTION_LABELS[getSafeFadeAction(action)];
  }

  function getSafeFadeColor(color) {
    return getSafeLabelKey(FADE_COLOR_LABELS, color, "black");
  }

  function getFadeColorLabel(color) {
    return FADE_COLOR_LABELS[getSafeFadeColor(color)];
  }

  function getFadeColorRgb(color) {
    return {
      black: "18, 14, 12",
      white: "255, 252, 247",
    }[getSafeFadeColor(color)];
  }

  function getSafeCameraZoomAction(action) {
    return getSafeLabelKey(CAMERA_ZOOM_ACTION_LABELS, action, "zoom_in");
  }

  function getCameraZoomActionLabel(action) {
    return CAMERA_ZOOM_ACTION_LABELS[getSafeCameraZoomAction(action)];
  }

  function getSafeCameraZoomStrength(strength) {
    return getSafeLabelKey(CAMERA_ZOOM_STRENGTH_LABELS, strength, "medium");
  }

  function getCameraZoomStrengthLabel(strength) {
    return CAMERA_ZOOM_STRENGTH_LABELS[getSafeCameraZoomStrength(strength)];
  }

  function getSafeCameraZoomFocus(focus) {
    return getSafeLabelKey(CAMERA_ZOOM_FOCUS_LABELS, focus, "center");
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
    return getSafeLabelKey(CAMERA_PAN_TARGET_LABELS, target, "center");
  }

  function getCameraPanTargetLabel(target) {
    return CAMERA_PAN_TARGET_LABELS[getSafeCameraPanTarget(target)];
  }

  function getSafeCameraPanStrength(strength) {
    return getSafeLabelKey(CAMERA_PAN_STRENGTH_LABELS, strength, "medium");
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
    return getSafeLabelKey(SCREEN_FILTER_ACTION_LABELS, action, "apply");
  }

  function getScreenFilterActionLabel(action) {
    return SCREEN_FILTER_ACTION_LABELS[getSafeScreenFilterAction(action)];
  }

  function getSafeScreenFilterPreset(preset) {
    return getSafeLabelKey(SCREEN_FILTER_PRESET_LABELS, preset, "memory");
  }

  function getScreenFilterPresetLabel(preset) {
    return SCREEN_FILTER_PRESET_LABELS[getSafeScreenFilterPreset(preset)];
  }

  function getSafeScreenFilterStrength(strength) {
    return getSafeLabelKey(SCREEN_FILTER_STRENGTH_LABELS, strength, "medium");
  }

  function getScreenFilterStrengthLabel(strength) {
    return SCREEN_FILTER_STRENGTH_LABELS[getSafeScreenFilterStrength(strength)];
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

    return recipes[preset][strength];
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
    const opacity = {
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

    return {
      background: backgrounds[preset],
      opacity,
    };
  }

  function getSafeDepthBlurAction(action) {
    return getSafeLabelKey(DEPTH_BLUR_ACTION_LABELS, action, "apply");
  }

  function getDepthBlurActionLabel(action) {
    return DEPTH_BLUR_ACTION_LABELS[getSafeDepthBlurAction(action)];
  }

  function getSafeDepthBlurFocus(focus) {
    return getSafeLabelKey(DEPTH_BLUR_FOCUS_LABELS, focus, "center");
  }

  function getDepthBlurFocusLabel(focus) {
    return DEPTH_BLUR_FOCUS_LABELS[getSafeDepthBlurFocus(focus)];
  }

  function getSafeDepthBlurStrength(strength) {
    return getSafeLabelKey(DEPTH_BLUR_STRENGTH_LABELS, strength, "medium");
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

  function getSafeVideoFit(value) {
    return getSafeLabelKey(VIDEO_FIT_LABELS, value, "contain");
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

  function getSafeCreditsDuration(value) {
    const number = Number(value);
    if (!Number.isFinite(number)) {
      return 18;
    }
    return Math.round(clamp(number, 4, 180));
  }

  function getSafeCreditsBackground(value) {
    return getSafeLabelKey(CREDITS_BACKGROUND_LABELS, value, "dark");
  }

  function getCreditsBackgroundLabel(value) {
    return CREDITS_BACKGROUND_LABELS[getSafeCreditsBackground(value)] ?? CREDITS_BACKGROUND_LABELS.dark;
  }

  function parseCreditsLines(value) {
    return String(value ?? "")
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean);
  }

  function getCreditsLines(blockLines) {
    if (Array.isArray(blockLines)) {
      return blockLines.map((line) => String(line ?? "").trim()).filter(Boolean);
    }
    return parseCreditsLines(blockLines);
  }

  function getCreditsLinesText(blockLines) {
    return getCreditsLines(blockLines).join("\n");
  }

  global.TonyNaEditorVisualEffects = Object.freeze({
    SHAKE_INTENSITY_LABELS,
    EFFECT_DURATION_LABELS,
    FLASH_COLOR_LABELS,
    FLASH_INTENSITY_LABELS,
    FADE_ACTION_LABELS,
    FADE_COLOR_LABELS,
    CAMERA_ZOOM_ACTION_LABELS,
    CAMERA_ZOOM_STRENGTH_LABELS,
    CAMERA_ZOOM_FOCUS_LABELS,
    SCREEN_FILTER_ACTION_LABELS,
    SCREEN_FILTER_PRESET_LABELS,
    SCREEN_FILTER_STRENGTH_LABELS,
    CAMERA_PAN_TARGET_LABELS,
    CAMERA_PAN_STRENGTH_LABELS,
    DEPTH_BLUR_ACTION_LABELS,
    DEPTH_BLUR_FOCUS_LABELS,
    DEPTH_BLUR_STRENGTH_LABELS,
    VIDEO_FIT_LABELS,
    VIDEO_VOLUME_LABELS,
    CREDITS_BACKGROUND_LABELS,
    getSafeShakeIntensity,
    getShakeIntensityLabel,
    getSafeEffectDuration,
    getEffectDurationLabel,
    getShakeDistance,
    getEffectDurationSeconds,
    getSafeFlashColor,
    getFlashColorLabel,
    getSafeFlashIntensity,
    getFlashIntensityLabel,
    getFlashOpacity,
    getFlashColorRgb,
    getSafeFadeAction,
    getFadeActionLabel,
    getSafeFadeColor,
    getFadeColorLabel,
    getFadeColorRgb,
    getSafeCameraZoomAction,
    getCameraZoomActionLabel,
    getSafeCameraZoomStrength,
    getCameraZoomStrengthLabel,
    getSafeCameraZoomFocus,
    getCameraZoomFocusLabel,
    getCameraZoomScale,
    getCameraZoomOrigin,
    getSafeCameraPanTarget,
    getCameraPanTargetLabel,
    getSafeCameraPanStrength,
    getCameraPanStrengthLabel,
    getCameraPanOffset,
    getSafeScreenFilterAction,
    getScreenFilterActionLabel,
    getSafeScreenFilterPreset,
    getScreenFilterPresetLabel,
    getSafeScreenFilterStrength,
    getScreenFilterStrengthLabel,
    getScreenFilterCss,
    getScreenFilterWash,
    getSafeDepthBlurAction,
    getDepthBlurActionLabel,
    getSafeDepthBlurFocus,
    getDepthBlurFocusLabel,
    getSafeDepthBlurStrength,
    getDepthBlurStrengthLabel,
    getDepthBlurBackdropPx,
    getDepthBlurParticlePx,
    getDepthBlurSpritePx,
    getDepthBlurSpriteOpacity,
    getSafeVideoFit,
    getVideoFitLabel,
    getSafeVideoVolume,
    getSafeCreditsDuration,
    getSafeCreditsBackground,
    getCreditsBackgroundLabel,
    parseCreditsLines,
    getCreditsLines,
    getCreditsLinesText,
  });
})(typeof window !== "undefined" ? window : globalThis);
