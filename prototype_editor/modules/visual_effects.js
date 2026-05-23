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

  const POSITION_LABELS = Object.freeze({
    left: "左侧",
    center: "中间",
    right: "右侧",
  });

  const CHARACTER_TRANSITION_LABELS = Object.freeze({
    fade: "淡入淡出",
    slide_left: "从左侧滑入 / 滑出",
    slide_right: "从右侧滑入 / 滑出",
    rise: "向上浮现",
    pop: "轻微弹出",
    none: "直接切换",
  });

  const BASIC_TRANSITION_LABELS = Object.freeze({
    fade: "淡入淡出",
    none: "直接切换",
  });

  const TRANSITION_DURATION_DEFAULT_MS = 360;
  const TRANSITION_DURATION_MIN_MS = 0;
  const TRANSITION_DURATION_MAX_MS = 5000;

  const DEFAULT_CHARACTER_STAGE = Object.freeze({
    offsetX: 0,
    offsetY: 0,
    scale: 100,
    opacity: 100,
    layer: 0,
    flipX: false,
  });

  const TEXT_SPEED_LABELS = Object.freeze({
    slow: "慢一点",
    normal: "正常",
    fast: "快一点",
    instant: "立刻显示",
  });

  const DIALOG_THEME_LABELS = Object.freeze({
    project: "项目样式",
    warm: "暖光标准",
    moonlight: "夜色月光",
    paper: "纸页回忆",
    transparent: "透明无框",
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

  function getScreenColorGradeSummary(source) {
    const grade = getSafeScreenColorGrade(source);
    const parts = [];
    if (grade.brightness !== SCREEN_COLOR_GRADE_DEFAULTS.brightness) {
      parts.push(`亮度 ${grade.brightness}`);
    }
    if (grade.contrast !== SCREEN_COLOR_GRADE_DEFAULTS.contrast) {
      parts.push(`对比 ${grade.contrast}`);
    }
    if (grade.saturation !== SCREEN_COLOR_GRADE_DEFAULTS.saturation) {
      parts.push(`饱和 ${grade.saturation}`);
    }
    if (grade.hue !== SCREEN_COLOR_GRADE_DEFAULTS.hue) {
      parts.push(`色相 ${grade.hue}`);
    }
    if (grade.temperature !== SCREEN_COLOR_GRADE_DEFAULTS.temperature) {
      parts.push(`冷暖 ${grade.temperature}`);
    }
    if (grade.vignette !== SCREEN_COLOR_GRADE_DEFAULTS.vignette) {
      parts.push(`暗角 ${grade.vignette}`);
    }
    return parts.length ? parts.join(" / ") : "默认色彩";
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

    return [recipes[preset][strength], getScreenColorGradeCss(screenFilter.grade)].filter(Boolean).join(" ");
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
      background:
        temperatureOpacity > 0.001 ? `${temperatureWash}, ${backgrounds[preset]}` : backgrounds[preset],
      opacity: Number(clamp(baseOpacity + temperatureOpacity, 0, 0.46).toFixed(3)),
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

  function getSafePosition(position) {
    return getSafeLabelKey(POSITION_LABELS, position, "center");
  }

  function getPositionLabel(position) {
    return POSITION_LABELS[getSafePosition(position)];
  }

  function getSafeTransition(transition) {
    return getSafeLabelKey(CHARACTER_TRANSITION_LABELS, transition, "fade");
  }

  function getTransitionLabel(transition) {
    return CHARACTER_TRANSITION_LABELS[getSafeTransition(transition)];
  }

  function getSafeTransitionDurationMs(value, fallback = TRANSITION_DURATION_DEFAULT_MS) {
    const number = Number.parseFloat(value ?? "");
    const safeFallback = Number.isFinite(Number(fallback))
      ? clamp(Number(fallback), TRANSITION_DURATION_MIN_MS, TRANSITION_DURATION_MAX_MS)
      : TRANSITION_DURATION_DEFAULT_MS;
    return Math.round(clamp(Number.isFinite(number) ? number : safeFallback, TRANSITION_DURATION_MIN_MS, TRANSITION_DURATION_MAX_MS));
  }

  function getSafeStageNumber(value, fallback, min, max) {
    const number = Number.parseFloat(value ?? "");
    return Number.isFinite(number) ? clamp(number, min, max) : fallback;
  }

  function getSafeStageBoolean(value, fallback = false) {
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

  function getSafeCharacterStage(source = {}) {
    const raw = source && typeof source === "object" ? source : {};
    return {
      offsetX: Math.round(getSafeStageNumber(raw.offsetX, DEFAULT_CHARACTER_STAGE.offsetX, -60, 60)),
      offsetY: Math.round(getSafeStageNumber(raw.offsetY, DEFAULT_CHARACTER_STAGE.offsetY, -45, 45)),
      scale: Math.round(getSafeStageNumber(raw.scale, DEFAULT_CHARACTER_STAGE.scale, 45, 220)),
      opacity: Math.round(getSafeStageNumber(raw.opacity, DEFAULT_CHARACTER_STAGE.opacity, 0, 100)),
      layer: Math.round(getSafeStageNumber(raw.layer, DEFAULT_CHARACTER_STAGE.layer, -10, 10)),
      flipX: getSafeStageBoolean(raw.flipX, DEFAULT_CHARACTER_STAGE.flipX),
    };
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

  function getCharacterStageSummary(stageSource = {}) {
    const stage = getSafeCharacterStage(stageSource);
    return `X ${stage.offsetX}% / Y ${stage.offsetY}% / ${stage.scale}% / 透明 ${stage.opacity}% / 层级 ${stage.layer}${
      stage.flipX ? " / 镜像" : ""
    }`;
  }

  function getSafeTextSpeed(speed) {
    return getSafeLabelKey(TEXT_SPEED_LABELS, speed, "normal");
  }

  function getTextSpeedLabel(speed) {
    return TEXT_SPEED_LABELS[getSafeTextSpeed(speed)];
  }

  function getSafeDialogTheme(theme) {
    return getSafeLabelKey(DIALOG_THEME_LABELS, theme, "project");
  }

  function getDialogThemeLabel(theme) {
    return DIALOG_THEME_LABELS[getSafeDialogTheme(theme)];
  }

  global.CanvasiaEditorVisualEffects = Object.freeze({
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
    SCREEN_COLOR_GRADE_DEFAULTS,
    SCREEN_COLOR_GRADE_LIMITS,
    CAMERA_PAN_TARGET_LABELS,
    CAMERA_PAN_STRENGTH_LABELS,
    DEPTH_BLUR_ACTION_LABELS,
    DEPTH_BLUR_FOCUS_LABELS,
    DEPTH_BLUR_STRENGTH_LABELS,
    VIDEO_FIT_LABELS,
    VIDEO_VOLUME_LABELS,
    CREDITS_BACKGROUND_LABELS,
    POSITION_LABELS,
    CHARACTER_TRANSITION_LABELS,
    BASIC_TRANSITION_LABELS,
    TRANSITION_DURATION_DEFAULT_MS,
    TRANSITION_DURATION_MIN_MS,
    TRANSITION_DURATION_MAX_MS,
    DEFAULT_CHARACTER_STAGE,
    TEXT_SPEED_LABELS,
    DIALOG_THEME_LABELS,
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
    getSafeScreenColorGrade,
    getScreenColorGradeCss,
    getScreenColorGradeSummary,
    getScreenFilterCss,
    getScreenFilterWash,
    getScreenFilterVignette,
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
    getSafePosition,
    getPositionLabel,
    getSafeTransition,
    getTransitionLabel,
    getSafeTransitionDurationMs,
    getSafeCharacterStage,
    getCharacterStageStyle,
    getCharacterStageSummary,
    getSafeTextSpeed,
    getTextSpeedLabel,
    getSafeDialogTheme,
    getDialogThemeLabel,
  });
})(typeof window !== "undefined" ? window : globalThis);
