(function attachRenpyExporterTools(global) {
  "use strict";

  const CHOICE_CONTINUE_TARGET = "__continue__";
  const BLOCK_TYPES_REQUIRING_COMMENT = Object.freeze([]);
  const POSITION_XALIGN = Object.freeze({ left: 0.25, center: 0.5, right: 0.75 });
  const DEFAULT_CHARACTER_STAGE = Object.freeze({
    offsetX: 0,
    offsetY: 0,
    scale: 100,
    opacity: 100,
    layer: 0,
    flipX: false,
  });
  const CHARACTER_SHOW_TRANSITIONS = Object.freeze({
    fade: "dissolve",
    dissolve: "dissolve",
    slide_left: "moveinleft",
    slide_right: "moveinright",
    rise: "moveinbottom",
  });
  const CHARACTER_HIDE_TRANSITIONS = Object.freeze({
    fade: "dissolve",
    dissolve: "dissolve",
    slide_left: "moveoutleft",
    slide_right: "moveoutright",
    rise: "moveoutbottom",
  });
  const TEXT_SPEED_CPS = Object.freeze({
    slow: 24,
    normal: 42,
    fast: 72,
    instant: 10000,
  });
  const BACKGROUND_TRANSITION_DEFAULT_MS = 360;
  const EFFECT_DURATION_SECONDS = Object.freeze({
    short: 0.42,
    medium: 0.78,
    long: 1.2,
  });
  const FLASH_COLOR_HEX = Object.freeze({
    white: "#ffffff",
    warm: "#ffeccc",
    red: "#ff7878",
    black: "#201816",
  });
  const FADE_COLOR_HEX = Object.freeze({
    black: "#120e0c",
    white: "#fffcf7",
  });
  const DEFAULT_PROJECT_RESOLUTION = Object.freeze({ width: 1280, height: 720 });
  const CAMERA_ZOOM_SCALE = Object.freeze({
    zoom_in: Object.freeze({ light: 1.08, medium: 1.16, heavy: 1.26 }),
    zoom_out: Object.freeze({ light: 0.96, medium: 0.92, heavy: 0.88 }),
  });
  const CAMERA_FOCUS_XALIGN = Object.freeze({ left: 0.28, center: 0.5, right: 0.72 });
  const CAMERA_PAN_PERCENT = Object.freeze({ light: 4, medium: 8, heavy: 12 });
  const CAMERA_EFFECT_STRENGTH = Object.freeze({ soft: 0.65, medium: 1, strong: 1.35 });
  const SCREEN_FILTER_PRESETS = Object.freeze({
    memory: Object.freeze({ tint: "#ffeec2", saturation: 0.82, brightness: 0.03 }),
    mono: Object.freeze({ tint: "#ffffff", saturation: 0 }),
    dream: Object.freeze({ tint: "#eee4ff", saturation: 0.92, brightness: 0.05 }),
    cold: Object.freeze({ tint: "#dcecff", saturation: 0.86, brightness: -0.01 }),
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
  const DEPTH_BLUR_PIXELS = Object.freeze({ soft: 2, medium: 4, strong: 6 });
  const PARTICLE_PRESET_DEFAULTS = Object.freeze({
    snow: Object.freeze({ symbol: "*", color: "#ffffff", density: 40, size: 12, yspeed: 70, spread: 100, distribution: "linear" }),
    rain: Object.freeze({ symbol: "|", color: "#b7dcff", density: 56, size: 18, yspeed: 190, spread: 100, distribution: "linear" }),
    petals: Object.freeze({ symbol: "*", color: "#ffd6ea", density: 28, size: 18, yspeed: 58, spread: 100, distribution: "gaussian" }),
    dust: Object.freeze({ symbol: ".", color: "#c4f6ff", density: 26, size: 8, yspeed: 24, spread: 100, distribution: "gaussian" }),
    embers: Object.freeze({ symbol: "*", color: "#ffb36b", density: 24, size: 7, yspeed: -46, spread: 100, distribution: "gaussian" }),
    sparkles: Object.freeze({ symbol: "*", color: "#dff8ff", density: 18, size: 9, yspeed: 16, spread: 100, distribution: "gaussian" }),
    bubbles: Object.freeze({ symbol: "o", color: "#b6f3ff", density: 20, size: 18, yspeed: -72, spread: 100, distribution: "gaussian" }),
    confetti: Object.freeze({ symbol: "*", color: "#7fe7ff", density: 34, size: 10, yspeed: 120, spread: 100, distribution: "linear" }),
    smoke: Object.freeze({ symbol: ".", color: "#aebed4", density: 22, size: 44, yspeed: -24, spread: 72, distribution: "gaussian" }),
    flame: Object.freeze({ symbol: "*", color: "#ff8b3d", density: 26, size: 24, yspeed: -82, spread: 40, distribution: "gaussian" }),
    stardust: Object.freeze({ symbol: "*", color: "#8edbff", density: 30, size: 7, yspeed: 8, spread: 100, distribution: "gaussian" }),
    glyphs: Object.freeze({ symbol: "*", color: "#85d4ff", density: 14, size: 26, yspeed: 0, spread: 34, distribution: "gaussian" }),
  });
  const PARTICLE_INTENSITY_MULTIPLIER = Object.freeze({ light: 0.62, medium: 1, heavy: 1.55 });
  const PARTICLE_SPEED_MULTIPLIER = Object.freeze({ slow: 0.72, medium: 1, fast: 1.35 });
  const PARTICLE_WIND_SPEED = Object.freeze({ left: -55, still: 0, right: 55 });

  function toArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function cleanText(value, fallback = "") {
    const text = String(value ?? "").replace(/\s+/g, " ").trim();
    return text || fallback;
  }

  function normalizeIdentifier(value, fallback = "item") {
    const raw = cleanText(value, fallback)
      .normalize("NFKD")
      .replace(/[^\w]+/g, "_")
      .replace(/^_+|_+$/g, "")
      .toLowerCase();
    const safe = raw || fallback;
    return /^[a-z_]/i.test(safe) ? safe : `id_${safe}`;
  }

  function quoteRenpy(value) {
    return `"${String(value ?? "").replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/\r?\n/g, "\\n")}"`;
  }

  function getProjectTitle(data = {}, options = {}) {
    return cleanText(options.projectTitle ?? data.project?.title ?? data.title, "Canvasia Project");
  }

  function getProjectResolution(data = {}) {
    const resolution = data.project?.resolution ?? data.resolution ?? {};
    const width = Number(resolution.width ?? DEFAULT_PROJECT_RESOLUTION.width);
    const height = Number(resolution.height ?? DEFAULT_PROJECT_RESOLUTION.height);
    return {
      width: Number.isFinite(width) && width > 0 ? Math.round(width) : DEFAULT_PROJECT_RESOLUTION.width,
      height: Number.isFinite(height) && height > 0 ? Math.round(height) : DEFAULT_PROJECT_RESOLUTION.height,
    };
  }

  function getAssetList(data = {}) {
    return Array.isArray(data.assetList)
      ? data.assetList
      : Array.isArray(data.assets?.assets)
        ? data.assets.assets
        : [];
  }

  function getCharacterList(data = {}) {
    return Array.isArray(data.characters)
      ? data.characters
      : Array.isArray(data.characters?.characters)
        ? data.characters.characters
        : [];
  }

  function getVariableList(data = {}) {
    return Array.isArray(data.variables)
      ? data.variables
      : Array.isArray(data.variables?.variables)
        ? data.variables.variables
        : [];
  }

  function buildCollectionMap(source, idField = "id") {
    const result = new Map();
    if (source instanceof Map) {
      source.forEach((value, id) => {
        if (id) {
          result.set(String(id), value);
        }
      });
      return result;
    }
    if (source && typeof source === "object" && !Array.isArray(source)) {
      Object.entries(source).forEach(([id, value]) => {
        if (id) {
          result.set(String(id), value);
        }
      });
      return result;
    }
    toArray(source).forEach((item) => {
      if (item?.[idField]) {
        result.set(String(item[idField]), item);
      }
    });
    return result;
  }

  function buildAssetMap(data = {}) {
    const assetMap = new Map();
    getAssetList(data).forEach((asset) => {
      if (asset?.id) {
        assetMap.set(String(asset.id), asset);
      }
    });
    buildCollectionMap(data.assetsById).forEach((asset, id) => assetMap.set(id, asset));
    return assetMap;
  }

  function buildCharacterMap(data = {}) {
    const characterMap = new Map();
    getCharacterList(data).forEach((character) => {
      if (character?.id) {
        characterMap.set(String(character.id), character);
      }
    });
    buildCollectionMap(data.charactersById).forEach((character, id) => characterMap.set(id, character));
    return characterMap;
  }

  function buildSceneMap(data = {}) {
    const sceneMap = new Map();
    toArray(data.scenes).forEach((scene) => {
      if (scene?.id) {
        sceneMap.set(String(scene.id), scene);
      }
    });
    buildCollectionMap(data.scenesById).forEach((scene, id) => sceneMap.set(id, scene));
    toArray(data.chapters).forEach((chapter) => {
      toArray(chapter.scenes).forEach((scene) => {
        if (scene?.id) {
          sceneMap.set(String(scene.id), scene);
        }
      });
    });
    return sceneMap;
  }

  function getSceneRecords(data = {}) {
    const sceneMap = buildSceneMap(data);
    const records = [];
    const seenSceneIds = new Set();
    toArray(data.chapters).forEach((chapter, chapterIndex) => {
      const directScenes = toArray(chapter?.scenes);
      const orderedIds = toArray(chapter?.sceneOrder).map((sceneId) => cleanText(sceneId)).filter(Boolean);
      const scenes = directScenes.length
        ? directScenes
        : orderedIds.map((sceneId) => sceneMap.get(sceneId)).filter(Boolean);
      scenes.forEach((scene, sceneIndex) => {
        const sceneId = cleanText(scene?.id);
        if (!sceneId || seenSceneIds.has(sceneId)) {
          return;
        }
        seenSceneIds.add(sceneId);
        records.push({
          scene,
          chapterName: cleanText(chapter?.name ?? chapter?.title, `Chapter ${chapterIndex + 1}`),
          chapterOrder: chapterIndex,
          sceneIndex,
        });
      });
    });
    toArray(data.scenes).forEach((scene, sceneIndex) => {
      const sceneId = cleanText(scene?.id);
      if (!sceneId || seenSceneIds.has(sceneId)) {
        return;
      }
      seenSceneIds.add(sceneId);
      records.push({
        scene,
        chapterName: "Unassigned",
        chapterOrder: 9999,
        sceneIndex,
      });
    });
    return records.sort((left, right) =>
      left.chapterOrder === right.chapterOrder ? left.sceneIndex - right.sceneIndex : left.chapterOrder - right.chapterOrder
    );
  }

  function getAssetPath(assetMap, assetId) {
    const asset = assetMap.get(cleanText(assetId));
    return cleanText(asset?.path ?? asset?.filePath ?? asset?.src ?? asset?.name ?? assetId);
  }

  function getCharacterName(characterMap, characterId) {
    const character = characterMap.get(cleanText(characterId));
    return cleanText(character?.displayName ?? character?.name ?? characterId, "Narrator");
  }

  function getSceneLabel(sceneId, sceneMap = new Map()) {
    const scene = sceneMap.get(cleanText(sceneId));
    return normalizeIdentifier(scene?.id ?? sceneId, "scene");
  }

  function getChoiceTarget(option = {}) {
    return cleanText(option.gotoSceneId ?? option.targetSceneId ?? option.target);
  }

  function secondsFromMs(ms) {
    const value = Number(ms ?? 0);
    return Number.isFinite(value) && value > 0 ? Number((value / 1000).toFixed(2)) : 0;
  }

  function getSafeVolumeRatio(value, fallback = 100) {
    const number = Number(value ?? fallback);
    const percent = clampNumber(Number.isFinite(number) ? number : fallback, 0, 100);
    return Number((percent / 100).toFixed(2));
  }

  function renderVolumeClause(value, fallback = 100) {
    const ratio = getSafeVolumeRatio(value, fallback);
    return ratio === 1 ? "" : ` volume ${ratio}`;
  }

  function renderMusicLoopClause(block = {}) {
    if (block.loop === true) {
      return " loop";
    }
    if (block.loop === false) {
      return " noloop";
    }
    return "";
  }

  function pushMusicScopeReview(block = {}, context = {}) {
    const endMode = cleanText(block.endMode, "until_next_music");
    if (!["scene_end", "after_block"].includes(endMode)) {
      return [];
    }
    const endBlockId = cleanText(block.endBlockId);
    pushWarning(context.warnings ?? [], "renpy_music_scope_review", "BGM 播放范围需要在 Ren'Py 中复核并按需要补 stop music。", getWarningContext(context));
    return [`    # Canvasia review music scope: endMode=${endMode}, endBlockId=${endBlockId || "auto"}, fadeOutMs=${block.fadeOutMs ?? "default"}`];
  }

  function clampNumber(value, min, max) {
    return Math.min(Math.max(value, min), max);
  }

  function formatRenpySeconds(value) {
    const seconds = Number(value);
    return Number.isFinite(seconds) ? Number(seconds.toFixed(2)).toString() : "0";
  }

  function getSafeStageNumber(value, fallback, min, max) {
    const number = Number(value ?? fallback);
    return clampNumber(Number.isFinite(number) ? number : fallback, min, max);
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

  function getSafePosition(position) {
    const safePosition = cleanText(position, "center");
    return Object.hasOwn(POSITION_XALIGN, safePosition) ? safePosition : "center";
  }

  function getSafeCharacterStage(stageSource = {}) {
    const raw = stageSource && typeof stageSource === "object" ? stageSource : {};
    return {
      offsetX: Math.round(getSafeStageNumber(raw.offsetX, DEFAULT_CHARACTER_STAGE.offsetX, -60, 60)),
      offsetY: Math.round(getSafeStageNumber(raw.offsetY, DEFAULT_CHARACTER_STAGE.offsetY, -45, 45)),
      scale: Math.round(getSafeStageNumber(raw.scale, DEFAULT_CHARACTER_STAGE.scale, 45, 220)),
      opacity: Math.round(getSafeStageNumber(raw.opacity, DEFAULT_CHARACTER_STAGE.opacity, 0, 100)),
      layer: Math.round(getSafeStageNumber(raw.layer, DEFAULT_CHARACTER_STAGE.layer, -10, 10)),
      flipX: getSafeStageBoolean(raw.flipX, DEFAULT_CHARACTER_STAGE.flipX),
    };
  }

  function hasCustomCharacterStage(stageSource = {}) {
    const stage = getSafeCharacterStage(stageSource);
    return Object.entries(DEFAULT_CHARACTER_STAGE).some(([key, value]) => stage[key] !== value);
  }

  function formatRenpyFloat(value, digits = 3) {
    return Number(value.toFixed(digits)).toString();
  }

  function getCharacterStageTransformName(sceneId, sceneMap, blockIndex) {
    return normalizeIdentifier(`canvasia_stage_${getSceneLabel(sceneId, sceneMap)}_${Number(blockIndex ?? 0) + 1}`, "canvasia_stage");
  }

  function getCharacterStageTransformDefinition(block = {}, context = {}) {
    const stage = getSafeCharacterStage(block.stage);
    const position = getSafePosition(block.position);
    const name = getCharacterStageTransformName(context.sceneId, context.sceneMap, context.blockIndex);
    const xalign = clampNumber((POSITION_XALIGN[position] ?? POSITION_XALIGN.center) + stage.offsetX / 100, -0.2, 1.2);
    const yalign = clampNumber(1 + stage.offsetY / 100, -0.2, 1.2);
    const zoom = stage.scale / 100;
    const xzoom = stage.flipX ? -zoom : zoom;
    return [
      `transform ${name}:`,
      `    xalign ${formatRenpyFloat(xalign)}`,
      `    yalign ${formatRenpyFloat(yalign)}`,
      `    xzoom ${formatRenpyFloat(xzoom)}`,
      `    yzoom ${formatRenpyFloat(zoom)}`,
      `    alpha ${formatRenpyFloat(stage.opacity / 100, 2)}`,
    ];
  }

  function buildCharacterStageTransformDefinitions(sceneRecords = [], sceneMap = new Map()) {
    const definitions = [];
    sceneRecords.forEach((record, sceneIndex) => {
      const scene = record.scene ?? {};
      const sceneId = cleanText(scene.id, `scene_${sceneIndex + 1}`);
      toArray(scene.blocks).forEach((block, blockIndex) => {
        if (cleanText(block?.type) !== "character_show" || !hasCustomCharacterStage(block?.stage)) {
          return;
        }
        definitions.push(...getCharacterStageTransformDefinition(block, { sceneId, sceneMap, blockIndex }), "");
      });
    });
    return definitions;
  }

  function getTransitionDurationSeconds(block = {}, fallbackMs = 600) {
    const value = Number(block.transitionDurationMs ?? fallbackMs);
    const ms = Number.isFinite(value) ? clampNumber(value, 0, 5000) : fallbackMs;
    return Number((ms / 1000).toFixed(2));
  }

  function getScreenEffectDurationSeconds(block = {}) {
    const duration = cleanText(block.duration, "medium");
    return EFFECT_DURATION_SECONDS[duration] ?? EFFECT_DURATION_SECONDS.medium;
  }

  function getEffectColorHex(table, value, fallback) {
    const key = cleanText(value, fallback);
    return table[key] ?? table[fallback];
  }

  function getBackgroundTransitionExpression(block = {}, context = {}) {
    const transition = cleanText(block.transition, "fade");
    const seconds = getTransitionDurationSeconds(block, BACKGROUND_TRANSITION_DEFAULT_MS);
    if (transition === "none" || seconds <= 0) {
      return "";
    }
    if (["fade", "dissolve", "crossfade"].includes(transition)) {
      return `Dissolve(${formatRenpySeconds(seconds)})`;
    }
    pushWarning(context.warnings ?? [], "renpy_background_transition_review", `背景转场 ${transition} 暂未精确映射，已按淡入淡出导出。`, getWarningContext(context));
    return `Dissolve(${formatRenpySeconds(seconds)})`;
  }

  function renderBackgroundBlock(block = {}, context = {}) {
    const assetId = cleanText(block.assetId, "missing_background");
    const transition = getBackgroundTransitionExpression(block, context);
    return [`    scene ${normalizeIdentifier(assetId, "background")}${transition ? ` with ${transition}` : ""}`];
  }

  function getSafeCameraZoomAction(action) {
    const safeAction = cleanText(action, "zoom_in");
    return ["zoom_in", "zoom_out", "reset"].includes(safeAction) ? safeAction : "zoom_in";
  }

  function getSafeCameraStrength(strength) {
    const safeStrength = cleanText(strength, "medium");
    return ["light", "medium", "heavy"].includes(safeStrength) ? safeStrength : "medium";
  }

  function getSafeCameraFocus(focus) {
    const safeFocus = cleanText(focus, "center");
    return Object.hasOwn(CAMERA_FOCUS_XALIGN, safeFocus) ? safeFocus : "center";
  }

  function getSafeCameraPanTarget(target) {
    const safeTarget = cleanText(target, "center");
    return ["left", "center", "right"].includes(safeTarget) ? safeTarget : "center";
  }

  function getSafeEffectStrength(strength) {
    const safeStrength = cleanText(strength, "medium");
    return Object.hasOwn(CAMERA_EFFECT_STRENGTH, safeStrength) ? safeStrength : "medium";
  }

  function getSafeScreenFilterAction(action) {
    const safeAction = cleanText(action, "apply");
    return ["apply", "clear"].includes(safeAction) ? safeAction : "apply";
  }

  function getSafeScreenFilterPreset(preset) {
    const safePreset = cleanText(preset, "memory");
    return Object.hasOwn(SCREEN_FILTER_PRESETS, safePreset) ? safePreset : "memory";
  }

  function getSafeDepthBlurAction(action) {
    const safeAction = cleanText(action, "apply");
    return ["apply", "clear"].includes(safeAction) ? safeAction : "apply";
  }

  function getSafeDepthBlurFocus(focus) {
    const safeFocus = cleanText(focus, "full");
    return ["left", "center", "right", "full"].includes(safeFocus) ? safeFocus : "full";
  }

  function getSafeParticleAction(action) {
    const safeAction = cleanText(action, "start");
    return ["start", "stop"].includes(safeAction) ? safeAction : "start";
  }

  function getSafeParticlePreset(preset) {
    const safePreset = cleanText(preset, "snow");
    return Object.hasOwn(PARTICLE_PRESET_DEFAULTS, safePreset) ? safePreset : "snow";
  }

  function getSafeParticleIntensity(intensity) {
    const safeIntensity = cleanText(intensity, "medium");
    return Object.hasOwn(PARTICLE_INTENSITY_MULTIPLIER, safeIntensity) ? safeIntensity : "medium";
  }

  function getSafeParticleSpeed(speed) {
    const safeSpeed = cleanText(speed, "medium");
    return Object.hasOwn(PARTICLE_SPEED_MULTIPLIER, safeSpeed) ? safeSpeed : "medium";
  }

  function getSafeParticleWind(wind) {
    const safeWind = cleanText(wind, "still");
    return Object.hasOwn(PARTICLE_WIND_SPEED, safeWind) ? safeWind : "still";
  }

  function getCameraPanOffset(target, strength, resolution = DEFAULT_PROJECT_RESOLUTION) {
    const safeTarget = getSafeCameraPanTarget(target);
    if (safeTarget === "center") {
      return 0;
    }
    const percent = CAMERA_PAN_PERCENT[getSafeCameraStrength(strength)] ?? CAMERA_PAN_PERCENT.medium;
    const offset = Math.round((resolution.width * percent) / 100);
    return safeTarget === "left" ? offset : -offset;
  }

  function getDefaultCameraState() {
    return {
      zoomScale: 1,
      focus: "center",
      panOffset: 0,
      matrixcolor: "",
      blur: 0,
    };
  }

  function getCameraState(context = {}) {
    if (!context.cameraState) {
      context.cameraState = getDefaultCameraState();
    }
    return context.cameraState;
  }

  function renderCameraStatement(state = getDefaultCameraState()) {
    const zoomScale = Number(state.zoomScale ?? 1);
    const panOffset = Number(state.panOffset ?? 0);
    const blur = Number(state.blur ?? 0);
    const focus = getSafeCameraFocus(state.focus);
    const matrixcolor = cleanText(state.matrixcolor);
    const neutral =
      Math.abs(zoomScale - 1) < 0.001 &&
      panOffset === 0 &&
      focus === "center" &&
      !matrixcolor &&
      (!Number.isFinite(blur) || blur <= 0);
    if (neutral) {
      return ["    camera"];
    }
    const lines = [
      "    camera:",
      "        subpixel True",
      `        xalign ${formatRenpyFloat(CAMERA_FOCUS_XALIGN[focus], 2)}`,
      "        yalign 0.52",
      `        zoom ${formatRenpyFloat(zoomScale, 2)}`,
      `        xoffset ${Math.round(panOffset)}`,
      "        yoffset 0",
    ];
    if (matrixcolor) {
      lines.push(`        matrixcolor ${matrixcolor}`);
    }
    if (Number.isFinite(blur) && blur > 0) {
      lines.push(`        blur ${formatRenpyFloat(blur, 2)}`);
    }
    return lines;
  }

  function renderCameraZoomBlock(block = {}, context = {}) {
    const state = getCameraState(context);
    const action = getSafeCameraZoomAction(block.action);
    if (action === "reset") {
      state.zoomScale = 1;
      state.focus = "center";
    } else {
      const strength = getSafeCameraStrength(block.strength);
      state.zoomScale = CAMERA_ZOOM_SCALE[action]?.[strength] ?? CAMERA_ZOOM_SCALE.zoom_in.medium;
      state.focus = getSafeCameraFocus(block.focus);
    }
    return renderCameraStatement(state);
  }

  function renderCameraPanBlock(block = {}, context = {}) {
    const state = getCameraState(context);
    state.panOffset = getCameraPanOffset(block.target, block.strength, context.projectResolution ?? DEFAULT_PROJECT_RESOLUTION);
    return renderCameraStatement(state);
  }

  function getSafeScreenColorGrade(source = {}) {
    const raw = source && typeof source === "object" ? source : {};
    return Object.fromEntries(
      Object.entries(SCREEN_COLOR_GRADE_DEFAULTS).map(([key, fallback]) => {
        const [minimum, maximum] = SCREEN_COLOR_GRADE_LIMITS[key];
        const value = Number(raw[key]);
        return [key, Math.round(clampNumber(Number.isFinite(value) ? value : fallback, minimum, maximum))];
      })
    );
  }

  function getStrengthAdjustedValue(base, neutral, strength) {
    const multiplier = CAMERA_EFFECT_STRENGTH[getSafeEffectStrength(strength)] ?? 1;
    return neutral + (base - neutral) * multiplier;
  }

  function formatMatrixNumber(value) {
    const number = Number(value);
    return Number.isFinite(number) ? Number(number.toFixed(3)).toString() : "0";
  }

  function getScreenFilterMatrixExpression(block = {}) {
    const preset = SCREEN_FILTER_PRESETS[getSafeScreenFilterPreset(block.preset)];
    const strength = getSafeEffectStrength(block.strength);
    const grade = getSafeScreenColorGrade(block.grade);
    const parts = [
      `TintMatrix("${preset.tint}")`,
      `SaturationMatrix(${formatMatrixNumber(clampNumber(getStrengthAdjustedValue(preset.saturation, 1, strength), 0, 2.2))})`,
    ];
    const presetBrightness = getStrengthAdjustedValue(preset.brightness ?? 0, 0, strength);
    if (Math.abs(presetBrightness) > 0.001) {
      parts.push(`BrightnessMatrix(${formatMatrixNumber(clampNumber(presetBrightness, -1, 1))})`);
    }
    if (grade.brightness !== SCREEN_COLOR_GRADE_DEFAULTS.brightness) {
      parts.push(`BrightnessMatrix(${formatMatrixNumber(clampNumber((grade.brightness - 100) / 100, -1, 1))})`);
    }
    if (grade.contrast !== SCREEN_COLOR_GRADE_DEFAULTS.contrast) {
      parts.push(`ContrastMatrix(${formatMatrixNumber(clampNumber(grade.contrast / 100, 0, 2.2))})`);
    }
    if (grade.saturation !== SCREEN_COLOR_GRADE_DEFAULTS.saturation) {
      parts.push(`SaturationMatrix(${formatMatrixNumber(clampNumber(grade.saturation / 100, 0, 2.2))})`);
    }
    const hue = grade.hue - grade.temperature * 0.08;
    if (Math.abs(hue) > 0.001) {
      parts.push(`HueMatrix(${formatMatrixNumber(hue)})`);
    }
    return parts.join(" * ");
  }

  function renderScreenFilterBlock(block = {}, context = {}) {
    const state = getCameraState(context);
    if (getSafeScreenFilterAction(block.action) === "clear") {
      state.matrixcolor = "";
    } else {
      state.matrixcolor = getScreenFilterMatrixExpression(block);
    }
    return renderCameraStatement(state);
  }

  function renderDepthBlurBlock(block = {}, context = {}) {
    const state = getCameraState(context);
    if (getSafeDepthBlurAction(block.action) === "clear") {
      state.blur = 0;
      return renderCameraStatement(state);
    }
    const focus = getSafeDepthBlurFocus(block.focus);
    const strength = getSafeEffectStrength(block.strength);
    if (focus !== "full") {
      pushWarning(context.warnings ?? [], "renpy_depth_blur_focus_review", "Ren'Py 草稿已导出全层 blur；指定角色侧清晰需要在 Ren'Py 中改成分层镜头。", getWarningContext(context));
    }
    state.blur = DEPTH_BLUR_PIXELS[strength] ?? DEPTH_BLUR_PIXELS.medium;
    return renderCameraStatement(state);
  }

  function getSafeParticleNumber(value, fallback, min, max) {
    const number = Number(value ?? fallback);
    return clampNumber(Number.isFinite(number) ? number : fallback, min, max);
  }

  function getParticleCount(block = {}, defaults = {}) {
    const baseDensity = getSafeParticleNumber(block.density, defaults.density ?? 32, 4, 180);
    const intensity = PARTICLE_INTENSITY_MULTIPLIER[getSafeParticleIntensity(block.intensity)] ?? 1;
    return Math.round(clampNumber(baseDensity * intensity, 4, 220));
  }

  function getParticleSize(block = {}, defaults = {}) {
    const sizeMin = getSafeParticleNumber(block.sizeMin, defaults.size ?? 10, 1, 160);
    const sizeMax = getSafeParticleNumber(block.sizeMax, defaults.size ?? 10, 1, 160);
    return Math.round(clampNumber((Math.min(sizeMin, sizeMax) + Math.max(sizeMin, sizeMax)) / 2, 1, 160));
  }

  function getSpeedTuple(baseValue, spreadRatio = 0.25) {
    const spread = Math.max(4, Math.abs(baseValue) * spreadRatio);
    const first = Number((baseValue - spread).toFixed(1));
    const second = Number((baseValue + spread).toFixed(1));
    return [Math.min(first, second), Math.max(first, second)];
  }

  function renderParticleSpeedTuple(values) {
    return `(${values.map((value) => formatRenpyFloat(value, 1)).join(", ")})`;
  }

  function renderParticleBlock(block = {}, context = {}) {
    if (getSafeParticleAction(block.action) === "stop") {
      return ["    hide canvasia_particles onlayer overlay"];
    }
    const preset = getSafeParticlePreset(block.preset);
    const defaults = PARTICLE_PRESET_DEFAULTS[preset];
    const speedMultiplier = PARTICLE_SPEED_MULTIPLIER[getSafeParticleSpeed(block.speed)] ?? 1;
    const windSpeed = PARTICLE_WIND_SPEED[getSafeParticleWind(block.wind)] ?? 0;
    const size = getParticleSize(block, defaults);
    const count = getParticleCount(block, defaults);
    const baseYSpeed = getSafeParticleNumber(block.gravityY, defaults.yspeed, -220, 320) * speedMultiplier;
    const spread = getSafeParticleNumber(block.spreadX, defaults.spread, 4, 100);
    const xSpeed = getSpeedTuple(windSpeed, Math.max(0.18, spread / 400));
    const ySpeed = getSpeedTuple(baseYSpeed, 0.22);
    const color = /^#[0-9a-f]{6}$/i.test(cleanText(block.color)) ? cleanText(block.color) : defaults.color;
    const advancedKeys = ["assetId", "customComboLayers", "comboPreset", "forceField", "follow", "emitterShape", "emissionMode"];
    const needsReview = advancedKeys.some((key) => {
      if (key === "customComboLayers") {
        return toArray(block[key]).length > 0;
      }
      return cleanText(block[key]) && !["none", "line", "continuous"].includes(cleanText(block[key]));
    });
    if (needsReview) {
      pushWarning(context.warnings ?? [], "renpy_particle_advanced_review", "粒子已按 SnowBlossom 基础层导出；自定义贴图、叠层、力场、跟随目标等高级参数需要在 Ren'Py 中复核。", getWarningContext(context));
    }
    return [
      `    show expression SnowBlossom(Text(${quoteRenpy(defaults.symbol)}, color=${quoteRenpy(color)}, size=${size}), count=${count}, border=80, xspeed=${renderParticleSpeedTuple(xSpeed)}, yspeed=${renderParticleSpeedTuple(ySpeed)}, start=0.04, fast=True, distribution=${quoteRenpy(defaults.distribution)}, animation=True) as canvasia_particles onlayer overlay`,
    ];
  }

  function getCharacterTransitionExpression(block = {}, context = {}, direction = "show") {
    const transition = cleanText(block.transition, "fade");
    if (transition === "none" || getTransitionDurationSeconds(block) <= 0) {
      return "";
    }
    const seconds = getTransitionDurationSeconds(block);
    if (["fade", "dissolve"].includes(transition)) {
      return `Dissolve(${seconds})`;
    }
    if (transition === "pop") {
      pushWarning(context.warnings ?? [], "renpy_character_transition_review", "轻微弹出转场已按淡入导出，请在 Ren'Py 中按需要替换为自定义 ATL。", getWarningContext(context));
      return `Dissolve(${seconds})`;
    }
    const table = direction === "hide" ? CHARACTER_HIDE_TRANSITIONS : CHARACTER_SHOW_TRANSITIONS;
    if (table[transition]) {
      if (seconds !== 0.6) {
        pushWarning(context.warnings ?? [], "renpy_character_transition_timing_review", `${transition} 转场时长需要在 Ren'Py 中复核。`, getWarningContext(context));
      }
      return table[transition];
    }
    pushWarning(context.warnings ?? [], "renpy_character_transition_review", `角色转场 ${transition} 暂未精确映射，已按淡入导出。`, getWarningContext(context));
    return `Dissolve(${seconds})`;
  }

  function renderCharacterShowBlock(block = {}, context = {}) {
    const characterId = cleanText(block.characterId, "character");
    const expression = cleanText(block.expressionId);
    const stage = getSafeCharacterStage(block.stage);
    const customStage = hasCustomCharacterStage(stage);
    const atTarget = customStage
      ? getCharacterStageTransformName(context.sceneId, context.sceneMap, context.blockIndex)
      : getSafePosition(block.position);
    const transition = getCharacterTransitionExpression(block, context, "show");
    const expressionSuffix = expression ? ` ${normalizeIdentifier(expression, "expr")}` : "";
    const zorderSuffix = customStage && stage.layer ? ` zorder ${20 + stage.layer}` : "";
    return [
      `    show ${normalizeIdentifier(characterId, "character")}${expressionSuffix} at ${atTarget}${zorderSuffix}${transition ? ` with ${transition}` : ""}`,
    ];
  }

  function renderCharacterHideBlock(block = {}, context = {}) {
    const transition = getCharacterTransitionExpression(block, context, "hide");
    return [`    hide ${normalizeIdentifier(block.characterId, "character")}${transition ? ` with ${transition}` : ""}`];
  }

  function renderScreenFlashBlock(block = {}) {
    const duration = getScreenEffectDurationSeconds(block);
    const outTime = clampNumber(duration * 0.2, 0.05, 0.28);
    const holdTime = clampNumber(duration * 0.12, 0.03, 0.16);
    const inTime = Math.max(0.05, duration - outTime - holdTime);
    const color = getEffectColorHex(FLASH_COLOR_HEX, block.color, "white");
    return [
      `    with Fade(${formatRenpySeconds(outTime)}, ${formatRenpySeconds(holdTime)}, ${formatRenpySeconds(inTime)}, color="${color}")`,
    ];
  }

  function renderScreenFadeBlock(block = {}, context = {}) {
    const action = cleanText(block.action, "fade_out");
    const duration = getScreenEffectDurationSeconds(block);
    const color = getEffectColorHex(FADE_COLOR_HEX, block.color, "black");
    if (action === "fade_in") {
      return [`    with Fade(0, 0, ${formatRenpySeconds(duration)}, color="${color}")`];
    }
    if (action !== "fade_out") {
      pushWarning(context.warnings ?? [], "renpy_screen_fade_action_review", `黑场动作 ${action} 暂未识别，已按淡出导出。`, getWarningContext(context));
    }
    return [`    with Fade(${formatRenpySeconds(duration)}, 0, 0, color="${color}")`];
  }

  function getBlockText(block = {}) {
    return cleanText(block.text ?? block.fields?.text);
  }

  function getSafeTextSpeed(speed) {
    const safeSpeed = cleanText(speed);
    return Object.hasOwn(TEXT_SPEED_CPS, safeSpeed) ? safeSpeed : "";
  }

  function renderRenpyText(block = {}) {
    const line = getBlockText(block) || " ";
    const textSpeed = getSafeTextSpeed(block.textSpeed);
    if (!textSpeed) {
      return line;
    }
    return `{cps=${TEXT_SPEED_CPS[textSpeed]}}${line}{/cps}`;
  }

  function getVoiceAssetId(block = {}) {
    return cleanText(block.voiceAssetId ?? block.voice?.assetId);
  }

  function renderRenpyLiteral(value) {
    if (typeof value === "boolean") {
      return value ? "True" : "False";
    }
    if (typeof value === "number" && Number.isFinite(value)) {
      return String(value);
    }
    if (value === null) {
      return "None";
    }

    const text = String(value ?? "").trim();
    if (/^(true|false)$/i.test(text)) {
      return text.toLowerCase() === "true" ? "True" : "False";
    }
    if (/^-?\d+(?:\.\d+)?$/.test(text)) {
      return text;
    }
    if (/^(none|null)$/i.test(text)) {
      return "None";
    }
    return quoteRenpy(text);
  }

  function getVariableIdentifier(value, fallback = "var") {
    return normalizeIdentifier(value, fallback);
  }

  function buildCharacterDefinitions(characterMap = new Map()) {
    return Array.from(characterMap.entries())
      .map(([characterId, character]) => {
        const variableName = normalizeIdentifier(characterId, "character");
        const displayName = cleanText(character?.displayName ?? character?.name, characterId);
        return `define ${variableName} = Character(${quoteRenpy(displayName)})`;
      })
      .sort();
  }

  function buildImageDefinitions(assetMap = new Map()) {
    return Array.from(assetMap.entries())
      .filter(([, asset]) => ["background", "cg", "sprite", "character", "image"].includes(cleanText(asset?.type).toLowerCase()))
      .map(([assetId, asset]) => {
        const imageName = normalizeIdentifier(assetId, "asset");
        const assetPath = cleanText(asset?.path ?? asset?.filePath ?? asset?.src ?? asset?.name, assetId);
        return `image ${imageName} = ${quoteRenpy(assetPath)}`;
      })
      .sort();
  }

  function buildVariableDefinitions(data = {}) {
    return getVariableList(data)
      .filter((variable) => cleanText(variable?.id))
      .map((variable) => `default ${getVariableIdentifier(variable.id)} = ${renderRenpyLiteral(variable.defaultValue)}`)
      .sort();
  }

  function pushWarning(warnings, code, message, context = {}) {
    warnings.push({ code, message, ...context });
  }

  function getWarningContext(context = {}) {
    return {
      sceneId: context.sceneId,
      blockIndex: context.blockIndex,
      optionIndex: context.optionIndex,
    };
  }

  function renderEffectComment(block = {}, warnings = [], context = {}) {
    const type = cleanText(block.type, "unknown");
    pushWarning(warnings, "renpy_comment_only_block", `${type} 已作为注释导出，需要在 Ren'Py 中手动还原。`, getWarningContext(context));
    return [`    # Canvasia review ${type}: ${quoteRenpy(getBlockText(block) || cleanText(block.preset ?? block.action ?? block.assetId, "manual port"))}`];
  }

  function renderVoicePrefix(block = {}, context = {}, indent = "    ") {
    const voiceAssetId = getVoiceAssetId(block);
    if (!voiceAssetId) {
      return [];
    }
    const path = getAssetPath(context.assetMap ?? new Map(), voiceAssetId);
    if (!path) {
      pushWarning(context.warnings ?? [], "renpy_missing_voice_asset", `语音 ${voiceAssetId} 没有找到素材路径。`, getWarningContext(context));
      return [`${indent}# Canvasia review missing voice asset: ${quoteRenpy(voiceAssetId)}`];
    }
    return [`${indent}voice ${quoteRenpy(path)}`];
  }

  function getEffectVariableId(effect = {}) {
    return cleanText(effect.variableId ?? effect.variableHint);
  }

  function renderVariableEffect(effect = {}, context = {}, indent = "    ") {
    const variableId = getEffectVariableId(effect);
    const warnings = context.warnings ?? [];
    if (!variableId) {
      pushWarning(warnings, "renpy_missing_variable_id", "变量卡缺少变量 ID，已导出 pass。", getWarningContext(context));
      return [`${indent}pass`];
    }

    if (effect.type === "variable_add") {
      const delta = Number(effect.value ?? 0);
      if (!Number.isFinite(delta)) {
        pushWarning(warnings, "renpy_variable_add_value_review", `变量 ${variableId} 的增减值不是数字，已按 0 导出。`, getWarningContext(context));
      }
      return [`${indent}$ ${getVariableIdentifier(variableId)} += ${Number.isFinite(delta) ? delta : 0}`];
    }

    return [`${indent}$ ${getVariableIdentifier(variableId)} = ${renderRenpyLiteral(effect.value)}`];
  }

  function normalizeConditionOperator(operator) {
    const safeOperator = cleanText(operator, "==");
    return safeOperator === "=" ? "==" : safeOperator;
  }

  function renderConditionRuleExpression(rule = {}, context = {}) {
    const variableId = cleanText(rule.variableId ?? rule.variableHint);
    if (!variableId) {
      pushWarning(context.warnings ?? [], "renpy_condition_missing_variable", "条件判断缺少变量 ID，已按 True 导出。", getWarningContext(context));
      return "True";
    }
    return `${getVariableIdentifier(variableId)} ${normalizeConditionOperator(rule.operator)} ${renderRenpyLiteral(rule.value)}`;
  }

  function renderConditionTargetLines(targetSceneId, context = {}, indent = "        ") {
    const target = cleanText(targetSceneId);
    if (!target) {
      pushWarning(context.warnings ?? [], "renpy_condition_missing_target", "条件分支缺少目标场景，已导出 pass。", getWarningContext(context));
      return [`${indent}pass`];
    }
    return [`${indent}jump ${getSceneLabel(target, context.sceneMap)}`];
  }

  function renderConditionBlock(block = {}, context = {}) {
    const branches = toArray(block.branches);
    if (!branches.length) {
      pushWarning(context.warnings ?? [], "renpy_empty_condition", "条件判断没有分支，已导出 pass。", getWarningContext(context));
      return ["    pass"];
    }

    const lines = [];
    branches.forEach((branch, index) => {
      const expression = toArray(branch.when)
        .map((rule) => renderConditionRuleExpression(rule, context))
        .filter(Boolean)
        .join(" and ") || "True";
      lines.push(`    ${index === 0 ? "if" : "elif"} ${expression}:`);
      renderConditionTargetLines(branch.gotoSceneId ?? branch.targetSceneId ?? branch.targetHint, context).forEach((line) => lines.push(line));
    });

    const elseTarget = block.elseGotoSceneId ?? block.elseTargetSceneId ?? block.elseTargetHint;
    if (elseTarget) {
      lines.push("    else:");
      renderConditionTargetLines(elseTarget, context).forEach((line) => lines.push(line));
    }

    return lines;
  }

  function renderVideoBlock(block = {}, context = {}) {
    const path = getAssetPath(context.assetMap ?? new Map(), block.assetId);
    if (!path) {
      pushWarning(context.warnings ?? [], "renpy_missing_video_asset", "视频卡没有找到可播放素材，已导出复核注释。", getWarningContext(context));
      return [`    # Canvasia review missing video: ${quoteRenpy(cleanText(block.assetId, "video"))}`];
    }

    const lines = [];
    const start = Number(block.startTimeSeconds ?? 0);
    const end = Number(block.endTimeSeconds ?? 0);
    if ((Number.isFinite(start) && start > 0) || (Number.isFinite(end) && end > 0) || block.volume) {
      pushWarning(context.warnings ?? [], "renpy_video_timing_review", "视频裁段或音量设置需要在 Ren'Py 中复核。", getWarningContext(context));
      lines.push(`    # Canvasia review video timing: start=${Number.isFinite(start) ? start : 0}, end=${Number.isFinite(end) ? end : 0}, volume=${block.volume ?? "default"}`);
    }
    lines.push(`    $ renpy.movie_cutscene(${quoteRenpy(path)})`);
    return lines;
  }

  function renderCreditsBlock(block = {}) {
    const title = cleanText(block.title, "STAFF");
    const subtitle = cleanText(block.subtitle);
    const lines = toArray(block.lines).map((line) => cleanText(line)).filter(Boolean);
    const duration = Number(block.durationSeconds ?? 12);
    const text = [title, subtitle, ...lines].filter(Boolean).join("\n");
    return [
      "    window hide",
      "    scene black with fade",
      `    show text ${quoteRenpy(text)} at truecenter with dissolve`,
      `    $ renpy.pause(${Number.isFinite(duration) && duration > 0 ? duration : 12})`,
      "    hide text with dissolve",
      "    window show",
    ];
  }

  function renderChoiceBlock(block = {}, context = {}) {
    const lines = ["    menu:"];
    const options = toArray(block.options);
    const warnings = context.warnings ?? [];
    if (!options.length) {
      pushWarning(warnings, "renpy_empty_choice", "选项卡没有选项，已导出 pass。", getWarningContext(context));
      lines.push("        pass");
      return lines;
    }
    options.forEach((option, optionIndex) => {
      const optionText = cleanText(option?.text ?? option?.label, `Option ${optionIndex + 1}`);
      const targetSceneId = getChoiceTarget(option);
      const effectCount = toArray(option.effects).length;
      lines.push(`        ${quoteRenpy(optionText)}:`);
      if (effectCount > 0) {
        toArray(option.effects).forEach((effect) => {
          renderVariableEffect(effect, { ...context, optionIndex }, "            ").forEach((line) => lines.push(line));
        });
      }
      if (targetSceneId && targetSceneId !== CHOICE_CONTINUE_TARGET) {
        lines.push(`            jump ${getSceneLabel(targetSceneId, context.sceneMap)}`);
      } else {
        lines.push("            pass");
      }
    });
    return lines;
  }

  function renderBlock(block = {}, context = {}) {
    const type = cleanText(block.type, "unknown");
    const assetMap = context.assetMap ?? new Map();
    const characterMap = context.characterMap ?? new Map();
    const warnings = context.warnings ?? [];
    if (type === "background") {
      return renderBackgroundBlock(block, context);
    }
    if (type === "character_show") {
      return renderCharacterShowBlock(block, context);
    }
    if (type === "character_hide") {
      return renderCharacterHideBlock(block, context);
    }
    if (type === "music_play") {
      const path = getAssetPath(assetMap, block.assetId);
      const fadeIn = secondsFromMs(block.fadeInMs);
      return [
        `    play music ${quoteRenpy(path || "audio/bgm.ogg")}${fadeIn ? ` fadein ${fadeIn}` : ""}${renderMusicLoopClause(block)}${renderVolumeClause(block.volume)}`,
        ...pushMusicScopeReview(block, context),
      ];
    }
    if (type === "music_stop") {
      const fadeOut = secondsFromMs(block.fadeOutMs);
      return [`    stop music${fadeOut ? ` fadeout ${fadeOut}` : ""}`];
    }
    if (type === "sfx_play") {
      return [`    play sound ${quoteRenpy(getAssetPath(assetMap, block.assetId) || "audio/sfx.ogg")}${renderVolumeClause(block.volume)}`];
    }
    if (type === "video_play") {
      return renderVideoBlock(block, context);
    }
    if (type === "credits_roll") {
      return renderCreditsBlock(block);
    }
    if (type === "variable_set" || type === "variable_add") {
      return renderVariableEffect(block, context);
    }
    if (type === "condition") {
      return renderConditionBlock(block, context);
    }
    if (type === "screen_shake") {
      return ["    with hpunch"];
    }
    if (type === "screen_flash") {
      return renderScreenFlashBlock(block);
    }
    if (type === "screen_fade") {
      return renderScreenFadeBlock(block, context);
    }
    if (type === "camera_zoom") {
      return renderCameraZoomBlock(block, context);
    }
    if (type === "camera_pan") {
      return renderCameraPanBlock(block, context);
    }
    if (type === "screen_filter") {
      return renderScreenFilterBlock(block, context);
    }
    if (type === "depth_blur") {
      return renderDepthBlurBlock(block, context);
    }
    if (type === "particle_effect") {
      return renderParticleBlock(block, context);
    }
    if (type === "dialogue") {
      const characterId = cleanText(block.speakerId);
      const line = renderRenpyText(block);
      const voiceLines = renderVoicePrefix(block, context);
      if (!characterId) {
        pushWarning(warnings, "renpy_missing_speaker", "台词缺少说话人，已作为旁白导出。", getWarningContext(context));
        return [...voiceLines, `    ${quoteRenpy(line)}`];
      }
      return [...voiceLines, `    ${normalizeIdentifier(characterId, "character")} ${quoteRenpy(line)}`];
    }
    if (type === "narration") {
      return [...renderVoicePrefix(block, context), `    ${quoteRenpy(renderRenpyText(block))}`];
    }
    if (type === "choice") {
      return renderChoiceBlock(block, context);
    }
    if (type === "jump") {
      const targetSceneId = cleanText(block.targetSceneId ?? block.target);
      if (!targetSceneId) {
        pushWarning(warnings, "renpy_missing_jump_target", "跳转卡没有目标，已导出 pass。", getWarningContext(context));
        return ["    pass"];
      }
      return [`    jump ${getSceneLabel(targetSceneId, context.sceneMap)}`];
    }
    if (type === "wait") {
      const seconds = Number(block.durationSeconds ?? 0) || secondsFromMs(block.durationMs);
      return [`    $ renpy.pause(${seconds || 0.5})`];
    }
    if (BLOCK_TYPES_REQUIRING_COMMENT.includes(type)) {
      return renderEffectComment(block, warnings, context);
    }
    pushWarning(warnings, "renpy_unknown_block", `${type} 暂未映射，已作为注释导出。`, getWarningContext(context));
    return renderEffectComment(block, warnings, context);
  }

  function buildRenpyDraftExport(data = {}, options = {}) {
    const assetMap = buildAssetMap(data);
    const characterMap = buildCharacterMap(data);
    const sceneMap = buildSceneMap(data);
    const sceneRecords = getSceneRecords(data);
    const projectResolution = getProjectResolution(data);
    const warnings = [];
    const characterStageTransforms = buildCharacterStageTransformDefinitions(sceneRecords, sceneMap);
    const lines = [
      `# ${getProjectTitle(data, options)} - Canvasia Ren'Py draft`,
      "# Generated as a migration-friendly draft. Review labels, assets, and custom effects before shipping.",
      "",
      ...buildImageDefinitions(assetMap),
      "",
      ...characterStageTransforms,
      ...(characterStageTransforms.length ? [""] : []),
      ...buildCharacterDefinitions(characterMap),
      "",
      ...buildVariableDefinitions(data),
      "",
    ];

    sceneRecords.forEach((record, sceneIndex) => {
      const scene = record.scene ?? {};
      const sceneId = cleanText(scene.id, `scene_${sceneIndex + 1}`);
      const cameraState = getDefaultCameraState();
      lines.push(`# ${record.chapterName} / ${cleanText(scene.name ?? scene.title, sceneId)}`);
      lines.push(`label ${getSceneLabel(sceneId, sceneMap)}:`);
      const blocks = toArray(scene.blocks);
      if (!blocks.length) {
        pushWarning(warnings, "renpy_empty_scene", "空场景已导出 pass。", { sceneId });
        lines.push("    pass");
      } else {
        blocks.forEach((block, blockIndex) => {
          renderBlock(block, { assetMap, characterMap, sceneMap, warnings, sceneId, blockIndex, cameraState, projectResolution }).forEach((line) => lines.push(line));
        });
      }
      const lastBlock = blocks[blocks.length - 1];
      if (!lastBlock || !["jump", "choice", "return", "credits_roll"].includes(cleanText(lastBlock.type))) {
        lines.push("    return");
      }
      lines.push("");
    });

    return {
      formatVersion: 1,
      projectTitle: getProjectTitle(data, options),
      sceneCount: sceneRecords.length,
      characterCount: characterMap.size,
      assetDefinitionCount: buildImageDefinitions(assetMap).length,
      variableDefinitionCount: buildVariableDefinitions(data).length,
      warningCount: warnings.length,
      warnings,
      script: `${lines.join("\n").replace(/\n{3,}/g, "\n\n").trim()}\n`,
    };
  }

  function getRenpyDraftStatusDigest(exportResult = {}) {
    if (!exportResult.sceneCount) {
      return {
        status: "empty",
        title: "还没有可导出的 Ren'Py 草稿",
        detail: "添加章节和场景后，可以生成一份便于迁移或协作的 .rpy 草稿。",
      };
    }
    if ((exportResult.warningCount ?? 0) > 0) {
      return {
        status: "review",
        title: "Ren'Py 草稿可导出，需人工复核",
        detail: `已转换 ${exportResult.sceneCount} 个场景，其中 ${exportResult.warningCount} 处自定义演出或缺口会以复核注释保留。`,
      };
    }
    return {
      status: "ready",
      title: "Ren'Py 草稿已就绪",
      detail: `已转换 ${exportResult.sceneCount} 个场景、${exportResult.characterCount} 个角色定义和 ${exportResult.assetDefinitionCount} 个图片定义。`,
    };
  }

  function buildRenpyDraftManifest(exportResult = {}) {
    const warnings = toArray(exportResult.warnings).map((warning, index) => [
      index + 1,
      warning.code,
      warning.sceneId ?? "",
      warning.blockIndex ?? "",
      warning.message,
    ]);
    return [
      `# ${cleanText(exportResult.projectTitle, "Canvasia Project")} Ren'Py 草稿迁移备注`,
      "",
      `场景数：${exportResult.sceneCount ?? 0}`,
      `角色定义：${exportResult.characterCount ?? 0}`,
      `变量默认值：${exportResult.variableDefinitionCount ?? 0}`,
      `图片定义：${exportResult.assetDefinitionCount ?? 0}`,
      `需要复核：${exportResult.warningCount ?? 0}`,
      "",
      warnings.length ? "| # | Code | Scene | Block | Message |\n| --- | --- | --- | --- | --- |" : "暂无需要人工复核的迁移提示。",
      ...warnings.map((row) => `| ${row.map((cell) => String(cell ?? "").replace(/\|/g, "\\|")).join(" | ")} |`),
      "",
    ].join("\n");
  }

  global.CanvasiaEditorRenpyExporter = Object.freeze({
    CHOICE_CONTINUE_TARGET,
    normalizeIdentifier,
    quoteRenpy,
    buildRenpyDraftExport,
    getRenpyDraftStatusDigest,
    buildRenpyDraftManifest,
    renderBlock,
  });
})(typeof window !== "undefined" ? window : globalThis);
