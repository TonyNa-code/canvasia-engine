import { getSafeDialogTheme } from "./runtime_settings.js";
import { getSafeDialogBoxOpacityPercent } from "./runtime_reading_profiles.js";
import {
  DEFAULT_PROJECT_DIALOG_BOX_CONFIG,
  DEFAULT_PROJECT_GAME_UI_CONFIG,
  PROJECT_DIALOG_BOX_PRESETS,
  PROJECT_GAME_UI_PRESETS,
} from "./runtime_visual_constants.js";

const HEX_COLOR_PATTERN = /^#[0-9a-f]{6}$/i;
const DEFAULT_PROJECT_FONT_ALIAS = "CanvasiaProjectFont";
const documentFontRequests = new WeakMap();
const documentFontCache = new WeakMap();

function getSafeNumber(value, fallback = 0) {
  const numericValue = Number.parseFloat(value ?? "");
  return Number.isFinite(numericValue) ? numericValue : fallback;
}

function clamp(value, minimum, maximum) {
  return Math.min(Math.max(value, minimum), maximum);
}

export function getSafeUiColor(value, fallback = "#ffffff") {
  const normalized = String(value ?? "").trim();
  if (HEX_COLOR_PATTERN.test(normalized)) {
    return normalized.toLowerCase();
  }
  const safeFallback = String(fallback ?? "#ffffff").trim();
  return HEX_COLOR_PATTERN.test(safeFallback) ? safeFallback.toLowerCase() : "#ffffff";
}

export function getSafeProjectDialogBoxPreset(value) {
  return value === "custom" || Object.hasOwn(PROJECT_DIALOG_BOX_PRESETS, value)
    ? value
    : DEFAULT_PROJECT_DIALOG_BOX_CONFIG.preset;
}

export function getSafeProjectDialogBoxShape(value) {
  return ["square", "capsule", "rounded"].includes(value)
    ? value
    : DEFAULT_PROJECT_DIALOG_BOX_CONFIG.shape;
}

export function getSafeProjectDialogBoxAnchor(value) {
  return ["bottom", "center", "top", "free"].includes(value)
    ? value
    : DEFAULT_PROJECT_DIALOG_BOX_CONFIG.anchor;
}

export function getProjectDialogBoxPresetConfig(preset) {
  const safePreset = getSafeProjectDialogBoxPreset(preset);
  return {
    ...DEFAULT_PROJECT_DIALOG_BOX_CONFIG,
    ...(PROJECT_DIALOG_BOX_PRESETS[safePreset] ?? {}),
    preset: safePreset,
  };
}

export function getProjectDialogBoxConfig(project = {}) {
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
    backgroundColor: getSafeUiColor(source.backgroundColor, base.backgroundColor),
    backgroundOpacity: clamp(getSafeNumber(source.backgroundOpacity, base.backgroundOpacity), 0, 100),
    borderColor: getSafeUiColor(source.borderColor, base.borderColor),
    borderOpacity: clamp(getSafeNumber(source.borderOpacity, base.borderOpacity), 0, 100),
    textColor: getSafeUiColor(source.textColor, base.textColor),
    speakerColor: getSafeUiColor(source.speakerColor, base.speakerColor),
    hintColor: getSafeUiColor(source.hintColor, base.hintColor),
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

export function getSafeProjectGameUiPreset(value) {
  return value === "custom" || Object.hasOwn(PROJECT_GAME_UI_PRESETS, value)
    ? value
    : DEFAULT_PROJECT_GAME_UI_CONFIG.preset;
}

export function getSafeProjectGameUiLayoutPreset(value) {
  return ["balanced", "cinematic", "compact", "minimal", "custom"].includes(value)
    ? value
    : DEFAULT_PROJECT_GAME_UI_CONFIG.layoutPreset;
}

export function getSafeProjectGameUiTitleLayout(value) {
  return ["center", "left", "poster"].includes(value)
    ? value
    : DEFAULT_PROJECT_GAME_UI_CONFIG.titleLayout;
}

export function getSafeProjectGameUiFontStyle(value) {
  return ["modern", "serif", "rounded"].includes(value)
    ? value
    : DEFAULT_PROJECT_GAME_UI_CONFIG.fontStyle;
}

export function getSafeProjectGameUiSurfaceStyle(value) {
  return ["glass", "solid", "minimal"].includes(value)
    ? value
    : DEFAULT_PROJECT_GAME_UI_CONFIG.surfaceStyle;
}

export function getSafeProjectGameUiBrandMode(value) {
  return ["project", "engine", "hidden"].includes(value)
    ? value
    : DEFAULT_PROJECT_GAME_UI_CONFIG.brandMode;
}

export function getSafeProjectGameUiSidePanelMode(value) {
  return ["full", "compact", "hidden"].includes(value)
    ? value
    : DEFAULT_PROJECT_GAME_UI_CONFIG.sidePanelMode;
}

export function getSafeProjectGameUiSidePanelPosition(value) {
  return ["right", "left"].includes(value)
    ? value
    : DEFAULT_PROJECT_GAME_UI_CONFIG.sidePanelPosition;
}

export function getSafeProjectGameUiTopbarPosition(value) {
  return ["top", "bottom", "hidden"].includes(value)
    ? value
    : DEFAULT_PROJECT_GAME_UI_CONFIG.topbarPosition;
}

export function getSafeProjectGameUiHudPosition(value) {
  return ["top", "top-left", "top-right", "bottom-left", "bottom-right", "hidden"].includes(value)
    ? value
    : DEFAULT_PROJECT_GAME_UI_CONFIG.hudPosition;
}

export function getSafeProjectGameUiTitleCardAnchor(value) {
  return ["center", "left", "right", "top", "bottom", "free"].includes(value)
    ? value
    : DEFAULT_PROJECT_GAME_UI_CONFIG.titleCardAnchor;
}

export function getSafeGameUiFrameSlice(
  value,
  fallback = { top: 18, right: 18, bottom: 18, left: 18 }
) {
  const source = value && typeof value === "object" ? value : {};
  return {
    top: clamp(getSafeNumber(source.top, fallback.top), 0, 96),
    right: clamp(getSafeNumber(source.right, fallback.right), 0, 96),
    bottom: clamp(getSafeNumber(source.bottom, fallback.bottom), 0, 96),
    left: clamp(getSafeNumber(source.left, fallback.left), 0, 96),
  };
}

export function getProjectGameUiPresetConfig(preset) {
  const safePreset = getSafeProjectGameUiPreset(preset);
  return {
    ...DEFAULT_PROJECT_GAME_UI_CONFIG,
    ...(PROJECT_GAME_UI_PRESETS[safePreset] ?? {}),
    preset: safePreset,
  };
}

export function getSafeProjectFontFamily(value) {
  return String(value ?? "")
    .replace(/[^\p{L}\p{N}\s,_'"-]/gu, "")
    .trim()
    .slice(0, 80);
}

export function getProjectGameUiConfig(project = {}) {
  const source = project?.gameUiConfig ?? {};
  const base = getProjectGameUiPresetConfig(source.preset);
  return {
    ...base,
    preset: getSafeProjectGameUiPreset(source.preset ?? base.preset),
    layoutPreset: getSafeProjectGameUiLayoutPreset(source.layoutPreset ?? base.layoutPreset),
    titleLayout: getSafeProjectGameUiTitleLayout(source.titleLayout ?? base.titleLayout),
    fontStyle: getSafeProjectGameUiFontStyle(source.fontStyle ?? base.fontStyle),
    fontFamily: getSafeProjectFontFamily(source.fontFamily ?? base.fontFamily),
    fontAssetId: String(source.fontAssetId ?? base.fontAssetId ?? "").trim(),
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
    backgroundColor: getSafeUiColor(source.backgroundColor, base.backgroundColor),
    backgroundAccentColor: getSafeUiColor(source.backgroundAccentColor, base.backgroundAccentColor),
    panelColor: getSafeUiColor(source.panelColor, base.panelColor),
    panelOpacity: clamp(getSafeNumber(source.panelOpacity, base.panelOpacity), 35, 100),
    textColor: getSafeUiColor(source.textColor, base.textColor),
    mutedTextColor: getSafeUiColor(source.mutedTextColor, base.mutedTextColor),
    accentColor: getSafeUiColor(source.accentColor, base.accentColor),
    accentAltColor: getSafeUiColor(source.accentAltColor, base.accentAltColor),
    buttonTextColor: getSafeUiColor(source.buttonTextColor, base.buttonTextColor),
    borderColor: getSafeUiColor(source.borderColor, base.borderColor),
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

export function toRgbaString(hexColor, opacityPercent) {
  const safeHex = getSafeUiColor(hexColor).slice(1);
  const red = Number.parseInt(safeHex.slice(0, 2), 16);
  const green = Number.parseInt(safeHex.slice(2, 4), 16);
  const blue = Number.parseInt(safeHex.slice(4, 6), 16);
  const alpha = clamp(getSafeNumber(opacityPercent, 100), 0, 100) / 100;
  return `rgba(${red}, ${green}, ${blue}, ${alpha.toFixed(2)})`;
}

export function getDialogShapeRadius(shape, fallbackRadius = 18) {
  const safeShape = getSafeProjectDialogBoxShape(shape);
  if (safeShape === "square") {
    return 6;
  }
  if (safeShape === "capsule") {
    return 999;
  }
  return clamp(getSafeNumber(fallbackRadius, 18), 8, 42);
}

export function getDialogThemeBaseColors(theme) {
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

function resolveAssetUrl(assetId, getAssetUrl) {
  const safeId = String(assetId ?? "").trim();
  if (!safeId || typeof getAssetUrl !== "function") {
    return "";
  }
  const assetUrl = getAssetUrl(safeId);
  return typeof assetUrl === "string" ? assetUrl : "";
}

function escapeCssUrl(value) {
  return String(value ?? "")
    .replace(/[\n\r\f]/g, "")
    .replace(/\\/g, "\\\\")
    .replace(/"/g, "%22");
}

function cssUrlFromAssetId(assetId, getAssetUrl) {
  const assetUrl = resolveAssetUrl(assetId, getAssetUrl);
  return assetUrl ? `url("${escapeCssUrl(assetUrl)}")` : "none";
}

function cssImageWithFallback(assetId, fallbackImage, getAssetUrl) {
  const image = cssUrlFromAssetId(assetId, getAssetUrl);
  return image === "none" ? fallbackImage : image;
}

function cssFrameSliceValue(slice) {
  return `${slice.top} ${slice.right} ${slice.bottom} ${slice.left} fill`;
}

function cssFrameWidthValue(slice) {
  return `${slice.top}px ${slice.right}px ${slice.bottom}px ${slice.left}px`;
}

function buildProjectFontAlias(assetUrl) {
  let hash = 0;
  for (const character of String(assetUrl)) {
    hash = (hash * 31 + character.codePointAt(0)) >>> 0;
  }
  return `${DEFAULT_PROJECT_FONT_ALIAS}${hash.toString(36)}`;
}

function setProjectFontCss(root, familyValue) {
  if (!root?.style) {
    return;
  }
  if (familyValue) {
    root.style.setProperty("--game-ui-font-family", familyValue);
    root.style.setProperty("--game-ui-heading-font-family", familyValue);
  } else {
    root.style.removeProperty?.("--game-ui-font-family");
    root.style.removeProperty?.("--game-ui-heading-font-family");
  }
}

export async function applyProjectGameUiFont(config, options = {}) {
  const documentRef = options.documentRef ?? globalThis.document;
  const root = documentRef?.documentElement;
  if (!root) {
    return { status: "unavailable", family: "", assetUrl: "" };
  }

  const requestToken = Symbol("project-font-request");
  documentFontRequests.set(documentRef, requestToken);
  const fallbackFamily = getSafeProjectFontFamily(config?.fontFamily);
  const fallbackCss = fallbackFamily || "";
  const assetUrl = resolveAssetUrl(config?.fontAssetId, options.getAssetUrl);
  if (!assetUrl) {
    setProjectFontCss(root, fallbackCss);
    root.dataset.gameUiCustomFont = fallbackFamily ? "system" : "preset";
    return { status: fallbackFamily ? "system" : "preset", family: fallbackFamily, assetUrl: "" };
  }

  const FontFaceCtor = options.FontFaceCtor ?? globalThis.FontFace;
  if (typeof FontFaceCtor !== "function" || typeof documentRef.fonts?.add !== "function") {
    setProjectFontCss(root, fallbackCss);
    root.dataset.gameUiCustomFont = "unsupported";
    return { status: "unsupported", family: fallbackFamily, assetUrl };
  }

  const alias = buildProjectFontAlias(assetUrl);
  const familyCss = `"${alias}"${fallbackFamily ? `, ${fallbackFamily}` : ", sans-serif"}`;
  let cache = documentFontCache.get(documentRef);
  if (!cache) {
    cache = new Map();
    documentFontCache.set(documentRef, cache);
  }

  try {
    let loadedFontPromise = cache.get(assetUrl);
    if (!loadedFontPromise) {
      const fontFace = new FontFaceCtor(alias, `url("${escapeCssUrl(assetUrl)}")`);
      loadedFontPromise = Promise.resolve(fontFace.load());
      cache.set(assetUrl, loadedFontPromise);
    }
    const loadedFont = await loadedFontPromise;
    if (documentFontRequests.get(documentRef) !== requestToken) {
      return { status: "stale", family: alias, assetUrl };
    }
    documentRef.fonts.add(loadedFont);
    setProjectFontCss(root, familyCss);
    root.dataset.gameUiCustomFont = "loaded";
    return { status: "loaded", family: alias, assetUrl };
  } catch (error) {
    cache.delete(assetUrl);
    if (documentFontRequests.get(documentRef) === requestToken) {
      setProjectFontCss(root, fallbackCss);
      root.dataset.gameUiCustomFont = "fallback";
    }
    return {
      status: "fallback",
      family: fallbackFamily,
      assetUrl,
      error: error instanceof Error ? error.message : String(error),
    };
  }
}

export function applyProjectGameUiSkin(project = {}, options = {}) {
  const documentRef = options.documentRef ?? globalThis.document;
  const root = documentRef?.documentElement;
  const config = getProjectGameUiConfig(project);
  if (!root?.style) {
    return { applied: false, config, fontPromise: Promise.resolve({ status: "unavailable" }) };
  }

  const panel = toRgbaString(config.panelColor, config.panelOpacity);
  const panelStrong = toRgbaString(config.panelColor, Math.min(100, config.panelOpacity + 8));
  const border = toRgbaString(config.borderColor, config.borderOpacity);
  const lowMotion = config.motionIntensity <= 15 ? "0" : "1";
  const panelFrameImage = cssUrlFromAssetId(config.panelFrameAssetId, options.getAssetUrl);
  const buttonFrameImage = cssUrlFromAssetId(config.buttonFrameAssetId, options.getAssetUrl);

  Object.assign(root.dataset, {
    gameUiPreset: config.preset,
    gameUiLayout: config.layoutPreset,
    gameUiTitleLayout: config.titleLayout,
    gameUiFont: config.fontStyle,
    gameUiSurface: config.surfaceStyle,
    gameUiBrand: config.brandMode,
    gameUiSidePanel: config.sidePanelMode,
    gameUiSidePosition: config.sidePanelPosition,
    gameUiTopbarPosition: config.topbarPosition,
    gameUiHudPosition: config.hudPosition,
    gameUiTitleAnchor: config.titleCardAnchor,
    gameUiMotion: lowMotion === "0" ? "low" : "normal",
  });

  const styleValues = {
    "--bg": config.backgroundColor,
    "--panel": panel,
    "--panel-strong": panelStrong,
    "--line": border,
    "--ink": config.textColor,
    "--muted": config.mutedTextColor,
    "--brand": config.accentColor,
    "--brand-deep": config.accentAltColor,
    "--accent": toRgbaString(config.accentColor, 18),
    "--game-ui-bg": config.backgroundColor,
    "--game-ui-bg-accent": config.backgroundAccentColor,
    "--game-ui-panel": panel,
    "--game-ui-panel-strong": panelStrong,
    "--game-ui-line": border,
    "--game-ui-text": config.textColor,
    "--game-ui-muted": config.mutedTextColor,
    "--game-ui-accent": config.accentColor,
    "--game-ui-accent-alt": config.accentAltColor,
    "--game-ui-button-text": config.buttonTextColor,
    "--game-ui-radius": `${config.cornerRadius}px`,
    "--game-ui-radius-large": `${Math.min(42, config.cornerRadius + 10)}px`,
    "--game-ui-blur": `${config.backdropBlur}px`,
    "--game-ui-stage-vignette": (config.stageVignette / 100).toFixed(2),
    "--game-ui-motion-enabled": lowMotion,
    "--game-ui-layout-gap": `${config.layoutGap}px`,
    "--game-ui-side-panel-width": `${config.sidePanelWidth}px`,
    "--game-ui-title-card-offset-x": `${config.titleCardOffsetXPercent}%`,
    "--game-ui-title-card-offset-y": `${config.titleCardOffsetYPercent}%`,
    "--game-ui-title-bg-image": cssUrlFromAssetId(config.titleBackgroundAssetId, options.getAssetUrl),
    "--game-ui-title-bg-fit": config.titleBackgroundFit,
    "--game-ui-title-bg-opacity": (config.titleBackgroundOpacity / 100).toFixed(2),
    "--game-ui-panel-frame-image": panelFrameImage,
    "--game-ui-panel-frame-opacity": (config.panelFrameOpacity / 100).toFixed(2),
    "--game-ui-panel-frame-slice": cssFrameSliceValue(config.panelFrameSlice),
    "--game-ui-panel-frame-width": cssFrameWidthValue(config.panelFrameSlice),
    "--game-ui-button-frame-image": buttonFrameImage,
    "--game-ui-button-hover-frame-image": cssImageWithFallback(config.buttonHoverFrameAssetId, buttonFrameImage, options.getAssetUrl),
    "--game-ui-button-pressed-frame-image": cssImageWithFallback(config.buttonPressedFrameAssetId, buttonFrameImage, options.getAssetUrl),
    "--game-ui-button-disabled-frame-image": cssImageWithFallback(config.buttonDisabledFrameAssetId, buttonFrameImage, options.getAssetUrl),
    "--game-ui-button-frame-opacity": (config.buttonFrameOpacity / 100).toFixed(2),
    "--game-ui-button-frame-slice": cssFrameSliceValue(config.buttonFrameSlice),
    "--game-ui-button-frame-width": cssFrameWidthValue(config.buttonFrameSlice),
    "--game-ui-save-slot-frame-image": cssImageWithFallback(config.saveSlotFrameAssetId, panelFrameImage, options.getAssetUrl),
    "--game-ui-system-panel-frame-image": cssImageWithFallback(config.systemPanelFrameAssetId, panelFrameImage, options.getAssetUrl),
    "--game-ui-overlay-image": cssUrlFromAssetId(config.uiOverlayAssetId, options.getAssetUrl),
    "--game-ui-overlay-opacity": (config.uiOverlayOpacity / 100).toFixed(2),
  };
  Object.entries(styleValues).forEach(([name, value]) => root.style.setProperty(name, value));

  const projectTitle = String(project?.title ?? options.fallbackTitle ?? "Canvasia Engine").trim() || "Canvasia Engine";
  const topEyebrow = documentRef.querySelector?.(".player-brand-copy .eyebrow");
  const startEyebrow = documentRef.querySelector?.(".start-card > .eyebrow");
  const startBrandTitle = documentRef.querySelector?.(".start-brand-copy strong");
  const startBrandSubtitle = documentRef.querySelector?.(".start-brand-copy span");
  const logoUrl = resolveAssetUrl(config.titleLogoAssetId, options.getAssetUrl);
  documentRef.querySelectorAll?.(".player-brand-logo, .start-brand-logo-image").forEach((image) => {
    if (logoUrl) {
      image.src = logoUrl;
    }
  });

  if (config.brandMode === "project") {
    if (topEyebrow) topEyebrow.textContent = `${projectTitle} · Runtime`;
    if (startEyebrow) startEyebrow.textContent = `${projectTitle} 导出试玩包`;
    if (startBrandTitle) startBrandTitle.textContent = projectTitle;
    if (startBrandSubtitle) startBrandSubtitle.textContent = "Visual Novel Runtime";
  }

  return {
    applied: true,
    config,
    fontPromise: applyProjectGameUiFont(config, { ...options, documentRef }),
  };
}

export function buildDialogBoxPresentation(theme, project = {}, options = {}) {
  const safeTheme = getSafeDialogTheme(theme);
  const opacityScale = getSafeDialogBoxOpacityPercent(options.dialogBoxOpacityPercent, 100) / 100;
  const scaleOpacity = (value) => clamp(getSafeNumber(value, 0) * opacityScale, 0, 100);
  if (safeTheme !== "project") {
    const base = getDialogThemeBaseColors(safeTheme);
    const blurStrength = safeTheme === "paper" ? 4 : safeTheme === "transparent" ? 0 : 10;
    const borderWidth = safeTheme === "transparent" ? 0 : 1;
    const shadowStrength = safeTheme === "transparent" ? 0 : safeTheme === "moonlight" ? 32 : 18;
    return {
      theme: safeTheme,
      assetUrl: "",
      style: [
        "--dialog-box-width: 76%;",
        "--dialog-box-min-height: 148px;",
        "--dialog-box-padding-x: 18px;",
        "--dialog-box-padding-y: 14px;",
        `--dialog-box-radius: ${getDialogShapeRadius("rounded", 18)}px;`,
        `--dialog-box-bg: ${toRgbaString(base.backgroundColor, scaleOpacity(base.backgroundOpacity))};`,
        `--dialog-box-border: ${toRgbaString(base.borderColor, scaleOpacity(base.borderOpacity))};`,
        `--dialog-box-border-width: ${borderWidth}px;`,
        `--dialog-box-text: ${base.textColor};`,
        `--dialog-box-speaker: ${base.speakerColor};`,
        `--dialog-box-hint: ${base.hintColor};`,
        `--dialog-box-blur: ${blurStrength}px;`,
        `--dialog-box-shadow-strength: ${shadowStrength};`,
        "--dialog-box-art-opacity: 0;",
        "--dialog-box-art-fit: cover;",
        "--dialog-box-art-image: none;",
        "--dialog-box-offset-x: 0%;",
        "--dialog-box-offset-y: 0%;",
      ].join(" "),
    };
  }

  const config = getProjectDialogBoxConfig(project);
  const assetUrl = resolveAssetUrl(config.panelAssetId, options.getAssetUrl);
  return {
    theme: "project",
    assetUrl,
    style: [
      `--dialog-box-width: ${config.widthPercent}%;`,
      `--dialog-box-min-height: ${config.minHeight}px;`,
      `--dialog-box-padding-x: ${config.paddingX}px;`,
      `--dialog-box-padding-y: ${config.paddingY}px;`,
      `--dialog-box-radius: ${getDialogShapeRadius(config.shape, config.shape === "rounded" ? 22 : 18)}px;`,
      `--dialog-box-bg: ${toRgbaString(config.backgroundColor, scaleOpacity(config.backgroundOpacity))};`,
      `--dialog-box-border: ${toRgbaString(config.borderColor, scaleOpacity(config.borderOpacity))};`,
      `--dialog-box-border-width: ${config.borderWidth}px;`,
      `--dialog-box-text: ${config.textColor};`,
      `--dialog-box-speaker: ${config.speakerColor};`,
      `--dialog-box-hint: ${config.hintColor};`,
      `--dialog-box-blur: ${config.blurStrength}px;`,
      `--dialog-box-shadow-strength: ${config.shadowStrength};`,
      `--dialog-box-art-opacity: ${(scaleOpacity(config.panelAssetOpacity) / 100).toFixed(2)};`,
      `--dialog-box-art-fit: ${config.panelAssetFit};`,
      `--dialog-box-offset-x: ${config.offsetXPercent}%;`,
      `--dialog-box-offset-y: ${config.offsetYPercent}%;`,
      assetUrl ? `--dialog-box-art-image: url("${escapeCssUrl(assetUrl)}");` : "--dialog-box-art-image: none;",
    ].join(" "),
  };
}
