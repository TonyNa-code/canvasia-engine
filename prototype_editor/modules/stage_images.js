(function attachStageImageTools(global) {
  "use strict";

  const STAGE_IMAGE_ASSET_TYPES = Object.freeze(["background", "sprite", "cg", "ui"]);

  const STAGE_IMAGE_ACTION_LABELS = Object.freeze({
    show: "显示或替换贴图",
    update: "调整已有贴图",
    hide: "隐藏贴图",
  });

  const STAGE_IMAGE_PLANE_LABELS = Object.freeze({
    back: "角色后方",
    front: "角色前方",
  });

  const STAGE_IMAGE_POSITION_LABELS = Object.freeze({
    left: "左侧",
    center: "中间",
    right: "右侧",
  });

  const STAGE_IMAGE_EASING_LABELS = Object.freeze({
    linear: "匀速",
    ease_in: "缓慢起步",
    ease_out: "自然收住",
    ease_in_out: "两端柔和",
    spring: "轻微弹性",
  });

  const DEFAULT_STAGE_IMAGE_TRANSFORM = Object.freeze({
    offsetX: 0,
    offsetY: 0,
    width: 34,
    opacity: 100,
    rotation: 0,
    layer: 0,
    flipX: false,
  });

  const STAGE_IMAGE_PRESETS = Object.freeze({
    prop_left: Object.freeze({
      label: "左侧道具",
      description: "角色前方的小型道具或手持物。",
      plane: "front",
      position: "left",
      transform: Object.freeze({ ...DEFAULT_STAGE_IMAGE_TRANSFORM, width: 28, offsetY: 16, layer: 2 }),
    }),
    prop_right: Object.freeze({
      label: "右侧道具",
      description: "右侧前景物件，可与左侧角色形成构图。",
      plane: "front",
      position: "right",
      transform: Object.freeze({ ...DEFAULT_STAGE_IMAGE_TRANSFORM, width: 28, offsetY: 16, layer: 2 }),
    }),
    cut_in: Object.freeze({
      label: "中央 Cut-in",
      description: "关键道具、手机画面、信件或事件插图。",
      plane: "front",
      position: "center",
      transform: Object.freeze({ ...DEFAULT_STAGE_IMAGE_TRANSFORM, width: 58, layer: 5 }),
    }),
    foreground: Object.freeze({
      label: "前景遮挡",
      description: "窗框、树叶、桌沿等增强空间感的前景。",
      plane: "front",
      position: "center",
      transform: Object.freeze({ ...DEFAULT_STAGE_IMAGE_TRANSFORM, width: 118, offsetY: 10, layer: -2 }),
    }),
    atmosphere: Object.freeze({
      label: "半透明光影",
      description: "柔光、阴影、玻璃反射等氛围叠层。",
      plane: "front",
      position: "center",
      transform: Object.freeze({ ...DEFAULT_STAGE_IMAGE_TRANSFORM, width: 118, opacity: 46, layer: 8 }),
    }),
    background_prop: Object.freeze({
      label: "角色后方布景",
      description: "公告牌、门窗或场景内固定装饰。",
      plane: "back",
      position: "center",
      transform: Object.freeze({ ...DEFAULT_STAGE_IMAGE_TRANSFORM, width: 48, layer: 0 }),
    }),
  });

  const STAGE_IMAGE_DURATION_DEFAULT_MS = 520;
  const STAGE_IMAGE_DURATION_MIN_MS = 0;
  const STAGE_IMAGE_DURATION_MAX_MS = 10000;

  function clamp(value, minimum, maximum) {
    return Math.min(Math.max(value, minimum), maximum);
  }

  function safeNumber(value, fallback) {
    const number = Number.parseFloat(value ?? "");
    return Number.isFinite(number) ? number : fallback;
  }

  function safeBoolean(value, fallback = false) {
    if (typeof value === "boolean") return value;
    const normalized = String(value ?? "").trim().toLowerCase();
    if (["true", "1", "yes", "on"].includes(normalized)) return true;
    if (["false", "0", "no", "off"].includes(normalized)) return false;
    return fallback;
  }

  function getSafeStageImageAction(value) {
    const action = String(value ?? "").trim();
    return Object.hasOwn(STAGE_IMAGE_ACTION_LABELS, action) ? action : "show";
  }

  function getStageImageActionLabel(value) {
    return STAGE_IMAGE_ACTION_LABELS[getSafeStageImageAction(value)];
  }

  function getSafeStageImagePlane(value) {
    const plane = String(value ?? "").trim();
    return Object.hasOwn(STAGE_IMAGE_PLANE_LABELS, plane) ? plane : "front";
  }

  function getStageImagePlaneLabel(value) {
    return STAGE_IMAGE_PLANE_LABELS[getSafeStageImagePlane(value)];
  }

  function getSafeStageImagePosition(value) {
    const position = String(value ?? "").trim();
    return Object.hasOwn(STAGE_IMAGE_POSITION_LABELS, position) ? position : "center";
  }

  function getStageImagePositionLabel(value) {
    return STAGE_IMAGE_POSITION_LABELS[getSafeStageImagePosition(value)];
  }

  function getSafeStageImageEasing(value) {
    const easing = String(value ?? "").trim();
    return Object.hasOwn(STAGE_IMAGE_EASING_LABELS, easing) ? easing : "ease_out";
  }

  function getStageImageEasingLabel(value) {
    return STAGE_IMAGE_EASING_LABELS[getSafeStageImageEasing(value)];
  }

  function getSafeStageImageLayerId(value, fallback = "layer_main") {
    const cleaned = String(value ?? "")
      .replace(/[\u0000-\u001f\u007f]/g, "")
      .trim()
      .replace(/\s+/g, "_")
      .slice(0, 48);
    return cleaned || String(fallback || "layer_main").slice(0, 48);
  }

  function getSafeStageImageTransform(source = {}) {
    const raw = source && typeof source === "object" ? source : {};
    return {
      offsetX: Math.round(clamp(safeNumber(raw.offsetX, DEFAULT_STAGE_IMAGE_TRANSFORM.offsetX), -80, 80)),
      offsetY: Math.round(clamp(safeNumber(raw.offsetY, DEFAULT_STAGE_IMAGE_TRANSFORM.offsetY), -70, 70)),
      width: Math.round(clamp(safeNumber(raw.width, DEFAULT_STAGE_IMAGE_TRANSFORM.width), 4, 180)),
      opacity: Math.round(clamp(safeNumber(raw.opacity, DEFAULT_STAGE_IMAGE_TRANSFORM.opacity), 0, 100)),
      rotation: Math.round(clamp(safeNumber(raw.rotation, DEFAULT_STAGE_IMAGE_TRANSFORM.rotation), -180, 180)),
      layer: Math.round(clamp(safeNumber(raw.layer, DEFAULT_STAGE_IMAGE_TRANSFORM.layer), -20, 20)),
      flipX: safeBoolean(raw.flipX, DEFAULT_STAGE_IMAGE_TRANSFORM.flipX),
    };
  }

  function getSafeStageImageDurationMs(value, fallback = STAGE_IMAGE_DURATION_DEFAULT_MS) {
    const safeFallback = clamp(
      safeNumber(fallback, STAGE_IMAGE_DURATION_DEFAULT_MS),
      STAGE_IMAGE_DURATION_MIN_MS,
      STAGE_IMAGE_DURATION_MAX_MS
    );
    return Math.round(
      clamp(safeNumber(value, safeFallback), STAGE_IMAGE_DURATION_MIN_MS, STAGE_IMAGE_DURATION_MAX_MS)
    );
  }

  function getStageImagePreset(presetId) {
    return STAGE_IMAGE_PRESETS[String(presetId ?? "").trim()] ?? null;
  }

  function applyStageImagePreset(source = {}, presetId = "") {
    const preset = getStageImagePreset(presetId);
    if (!preset) return normalizeStageImageState(source);
    return normalizeStageImageState({
      ...source,
      plane: preset.plane,
      position: preset.position,
      transform: preset.transform,
    });
  }

  function normalizeStageImageState(source = {}, fallback = {}) {
    const raw = source && typeof source === "object" ? source : {};
    const previous = fallback && typeof fallback === "object" ? fallback : {};
    const previousTransform = previous.transform ?? previous.stage ?? {};
    const explicitTransform = raw.transform ?? raw.stage;
    const transformSource = explicitTransform && typeof explicitTransform === "object"
      ? { ...previousTransform, ...explicitTransform }
      : previousTransform;
    return {
      layerId: getSafeStageImageLayerId(raw.layerId ?? previous.layerId),
      assetId: String(raw.assetId ?? previous.assetId ?? "").trim(),
      plane: getSafeStageImagePlane(raw.plane ?? previous.plane),
      position: getSafeStageImagePosition(raw.position ?? previous.position),
      transform: getSafeStageImageTransform(transformSource),
    };
  }

  function sortStageImages(images = []) {
    const planeOrder = { back: 0, front: 1 };
    return [...images].sort((left, right) => {
      const planeDifference = planeOrder[getSafeStageImagePlane(left?.plane)] - planeOrder[getSafeStageImagePlane(right?.plane)];
      if (planeDifference) return planeDifference;
      const layerDifference = getSafeStageImageTransform(left?.transform).layer - getSafeStageImageTransform(right?.transform).layer;
      if (layerDifference) return layerDifference;
      return getSafeStageImageLayerId(left?.layerId).localeCompare(getSafeStageImageLayerId(right?.layerId));
    });
  }

  function cloneStageImageState(source = {}) {
    const normalized = normalizeStageImageState(source);
    return { ...normalized, transform: { ...normalized.transform } };
  }

  function applyStageImageBlock(visibleImages = [], block = {}) {
    const action = getSafeStageImageAction(block.action);
    const layerId = getSafeStageImageLayerId(block.layerId);
    const imageMap = new Map(
      (Array.isArray(visibleImages) ? visibleImages : [])
        .map((item) => cloneStageImageState(item))
        .map((item) => [item.layerId, item])
    );
    const previousState = imageMap.get(layerId) ?? null;
    const durationMs = getSafeStageImageDurationMs(block.durationMs);
    const easing = getSafeStageImageEasing(block.easing);

    if (action === "hide") {
      imageMap.delete(layerId);
      return {
        visibleImages: sortStageImages(imageMap.values()),
        event: previousState
          ? { mode: "hide", layerId, previousState: cloneStageImageState(previousState), durationMs, easing }
          : null,
      };
    }

    const targetState = normalizeStageImageState({ ...block, layerId }, previousState ?? {});
    imageMap.set(layerId, targetState);
    return {
      visibleImages: sortStageImages(imageMap.values()),
      event: {
        mode: previousState ? "move" : "show",
        layerId,
        previousState: previousState ? cloneStageImageState(previousState) : null,
        targetState: cloneStageImageState(targetState),
        durationMs,
        easing,
      },
    };
  }

  function getStageImageSummary(block = {}, assetName = "") {
    const action = getSafeStageImageAction(block.action);
    const layerId = getSafeStageImageLayerId(block.layerId);
    if (action === "hide") return `隐藏“${layerId}”贴图`;
    const state = normalizeStageImageState(block);
    const name = String(assetName || state.assetId || "未选择素材").trim();
    return `${getStageImageActionLabel(action)}：${name} · ${getStageImagePlaneLabel(state.plane)} · ${getStageImagePositionLabel(state.position)}`;
  }

  function getStageImagePositionPercent(value) {
    return { left: 24, center: 50, right: 76 }[getSafeStageImagePosition(value)];
  }

  function getStageImageStyle(source = {}) {
    const state = normalizeStageImageState(source);
    const transform = state.transform;
    return [
      `--stage-image-position-x:${getStageImagePositionPercent(state.position)}%`,
      `--stage-image-offset-x:${transform.offsetX}%`,
      `--stage-image-offset-y:${transform.offsetY}%`,
      `--stage-image-width:${transform.width}%`,
      `--stage-image-opacity:${transform.opacity / 100}`,
      `--stage-image-rotation:${transform.rotation}deg`,
      `--stage-image-layer:${transform.layer}`,
      `--stage-image-flip:${transform.flipX ? -1 : 1}`,
    ].join(";") + ";";
  }

  function getStageImageMotionStyle(event = {}) {
    const previous = event.previousState ? normalizeStageImageState(event.previousState) : null;
    const easing = getSafeStageImageEasing(event.easing);
    const easingCss = {
      linear: "linear",
      ease_in: "cubic-bezier(0.42, 0, 1, 1)",
      ease_out: "cubic-bezier(0.16, 1, 0.3, 1)",
      ease_in_out: "cubic-bezier(0.65, 0, 0.35, 1)",
      spring: "cubic-bezier(0.34, 1.56, 0.64, 1)",
    }[easing];
    const values = [
      `--stage-image-motion-ms:${getSafeStageImageDurationMs(event.durationMs)}ms`,
      `--stage-image-motion-easing:${easingCss}`,
    ];
    if (previous) {
      values.push(
        `--stage-image-from-position-x:${getStageImagePositionPercent(previous.position)}%`,
        `--stage-image-from-offset-x:${previous.transform.offsetX}%`,
        `--stage-image-from-offset-y:${previous.transform.offsetY}%`,
        `--stage-image-from-width:${previous.transform.width}%`,
        `--stage-image-from-opacity:${previous.transform.opacity / 100}`,
        `--stage-image-from-rotation:${previous.transform.rotation}deg`,
        `--stage-image-from-flip:${previous.transform.flipX ? -1 : 1}`
      );
    }
    return values.join(";") + ";";
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function renderSelectOptions(labelMap, selectedValue, escape) {
    return Object.entries(labelMap)
      .map(([value, label]) => `<option value="${escape(value)}" ${value === selectedValue ? "selected" : ""}>${escape(label)}</option>`)
      .join("");
  }

  function renderStageImageEditor(block = {}, options = {}) {
    const escape = typeof options.escapeHtml === "function" ? options.escapeHtml : escapeHtml;
    const action = getSafeStageImageAction(block.action);
    const state = normalizeStageImageState(block);
    const durationMs = getSafeStageImageDurationMs(block.durationMs);
    const easing = getSafeStageImageEasing(block.easing);
    const assets = Array.isArray(options.assets) ? options.assets : [];
    const assetOptions = assets
      .map((asset) => `<option value="${escape(asset.id ?? "")}" ${asset.id === state.assetId ? "selected" : ""}>${escape(asset.name ?? asset.id ?? "未命名图片")} · ${escape(asset.type ?? "image")}</option>`)
      .join("");
    const presetOptions = Object.entries(STAGE_IMAGE_PRESETS)
      .map(([presetId, preset]) => `<option value="${escape(presetId)}">${escape(preset.label)} · ${escape(preset.description)}</option>`)
      .join("");

    return `
      <article class="editor-card">
        <h3>编辑舞台贴图</h3>
        <p>把道具、前景、Cut-in、窗框或光影作为独立图层摆进画面，不会占用角色位，也不需要把它们伪装成背景。</p>
      </article>
      <div class="field-grid">
        <div class="detail-row">
          <label for="editorStageImageAction">这张卡片要做什么</label>
          <select id="editorStageImageAction">${renderSelectOptions(STAGE_IMAGE_ACTION_LABELS, action, escape)}</select>
        </div>
        <div class="detail-row">
          <label for="editorStageImageLayerId">图层名称</label>
          <input id="editorStageImageLayerId" maxlength="48" value="${escape(state.layerId)}" placeholder="例如：letter、window、foreground" />
          <p class="helper-text">后续用同一个名称即可调整或隐藏这张贴图。建议用简短、好认的英文或中文名称。</p>
        </div>
        <div class="detail-row">
          <label for="editorStageImageAssetId">图片素材</label>
          <select id="editorStageImageAssetId">
            <option value="">先选择一张图片</option>
            ${assetOptions}
          </select>
          <p class="helper-text">隐藏动作不需要重新选择素材；显示和调整动作会沿用同名图层的已有素材。</p>
        </div>
        <div class="detail-row">
          <label for="editorStageImagePreset">新手构图预设</label>
          <div class="inline-control-row">
            <select id="editorStageImagePreset">${presetOptions}</select>
            <button class="toolbar-button" type="button" data-action="apply-stage-image-preset">套用预设</button>
          </div>
        </div>
        <div class="detail-row">
          <label for="editorStageImagePlane">位于角色哪一侧</label>
          <select id="editorStageImagePlane">${renderSelectOptions(STAGE_IMAGE_PLANE_LABELS, state.plane, escape)}</select>
        </div>
        <div class="detail-row">
          <label for="editorStageImagePosition">基础位置</label>
          <select id="editorStageImagePosition">${renderSelectOptions(STAGE_IMAGE_POSITION_LABELS, state.position, escape)}</select>
        </div>
        <div class="detail-row">
          <label>位置与外观</label>
          <div class="field-grid compact-grid">
            <label><span>横向偏移 %</span><input id="editorStageImageOffsetX" type="number" min="-80" max="80" step="1" value="${escape(state.transform.offsetX)}" /></label>
            <label><span>纵向偏移 %</span><input id="editorStageImageOffsetY" type="number" min="-70" max="70" step="1" value="${escape(state.transform.offsetY)}" /></label>
            <label><span>画面宽度 %</span><input id="editorStageImageWidth" type="number" min="4" max="180" step="1" value="${escape(state.transform.width)}" /></label>
            <label><span>不透明度 %</span><input id="editorStageImageOpacity" type="number" min="0" max="100" step="1" value="${escape(state.transform.opacity)}" /></label>
            <label><span>旋转角度</span><input id="editorStageImageRotation" type="number" min="-180" max="180" step="1" value="${escape(state.transform.rotation)}" /></label>
            <label><span>同侧图层</span><input id="editorStageImageLayer" type="number" min="-20" max="20" step="1" value="${escape(state.transform.layer)}" /></label>
          </div>
        </div>
        <label class="toggle-row">
          <input id="editorStageImageFlipX" type="checkbox" ${state.transform.flipX ? "checked" : ""} />
          <span>水平翻转图片</span>
        </label>
        <div class="detail-row">
          <label for="editorStageImageEasing">出现 / 移动手感</label>
          <select id="editorStageImageEasing">${renderSelectOptions(STAGE_IMAGE_EASING_LABELS, easing, escape)}</select>
        </div>
        <div class="detail-row">
          <label for="editorStageImageDurationMs">动作时长（毫秒）</label>
          <input id="editorStageImageDurationMs" type="number" min="0" max="10000" step="50" value="${escape(durationMs)}" />
          <p class="helper-text">0 表示立即变化；日常淡入建议 350-700，关键 Cut-in 建议 500-1000。</p>
        </div>
      </div>
      <div class="detail-actions">
        <button class="toolbar-button toolbar-button-primary" data-action="save-block">保存这张卡片</button>
      </div>
    `;
  }

  function getStageImageAssets(assets = []) {
    return (Array.isArray(assets) ? assets : []).filter((asset) => STAGE_IMAGE_ASSET_TYPES.includes(asset?.type));
  }

  function getSafeStageImageAssetId(assets = [], assetId = "", fallback = "") {
    const imageAssets = getStageImageAssets(assets);
    const selected = imageAssets.find((asset) => asset.id === String(assetId ?? ""));
    if (selected) return selected.id;
    const fallbackAsset = imageAssets.find((asset) => asset.id === String(fallback ?? ""));
    return fallbackAsset?.id ?? imageAssets[0]?.id ?? "";
  }

  function readStageImageEditorBlock(block = {}, options = {}) {
    const doc = options.document ?? global.document;
    const assets = options.assets ?? [];
    const read = (id, fallback) => doc?.getElementById?.(id)?.value ?? fallback;
    return {
      ...block,
      type: "stage_image",
      action: getSafeStageImageAction(read("editorStageImageAction", block.action)),
      layerId: getSafeStageImageLayerId(read("editorStageImageLayerId", block.layerId)),
      assetId: getSafeStageImageAssetId(assets, read("editorStageImageAssetId", ""), block.assetId),
      plane: getSafeStageImagePlane(read("editorStageImagePlane", block.plane)),
      position: getSafeStageImagePosition(read("editorStageImagePosition", block.position)),
      transform: getSafeStageImageTransform({
        offsetX: read("editorStageImageOffsetX", block.transform?.offsetX),
        offsetY: read("editorStageImageOffsetY", block.transform?.offsetY),
        width: read("editorStageImageWidth", block.transform?.width),
        opacity: read("editorStageImageOpacity", block.transform?.opacity),
        rotation: read("editorStageImageRotation", block.transform?.rotation),
        layer: read("editorStageImageLayer", block.transform?.layer),
        flipX: doc?.getElementById?.("editorStageImageFlipX")?.checked ?? block.transform?.flipX,
      }),
      durationMs: getSafeStageImageDurationMs(read("editorStageImageDurationMs", block.durationMs)),
      easing: getSafeStageImageEasing(read("editorStageImageEasing", block.easing)),
    };
  }

  function setStageImageEditorValue(doc, id, value) {
    const input = doc?.getElementById?.(id);
    if (!input) return false;
    if (input.type === "checkbox") input.checked = Boolean(value);
    else input.value = String(value ?? "");
    return true;
  }

  function applyStageImagePresetToEditor(block = {}, options = {}) {
    const doc = options.document ?? global.document;
    const presetId = options.presetId ?? doc?.getElementById?.("editorStageImagePreset")?.value ?? "";
    const next = applyStageImagePreset(readStageImageEditorBlock(block, options), presetId);
    setStageImageEditorValue(doc, "editorStageImagePlane", next.plane);
    setStageImageEditorValue(doc, "editorStageImagePosition", next.position);
    setStageImageEditorValue(doc, "editorStageImageOffsetX", next.transform.offsetX);
    setStageImageEditorValue(doc, "editorStageImageOffsetY", next.transform.offsetY);
    setStageImageEditorValue(doc, "editorStageImageWidth", next.transform.width);
    setStageImageEditorValue(doc, "editorStageImageOpacity", next.transform.opacity);
    setStageImageEditorValue(doc, "editorStageImageRotation", next.transform.rotation);
    setStageImageEditorValue(doc, "editorStageImageLayer", next.transform.layer);
    setStageImageEditorValue(doc, "editorStageImageFlipX", next.transform.flipX);
    return { presetId, preset: getStageImagePreset(presetId), state: next };
  }

  function renderStageImageLayer(visualState = {}, plane = "front", options = {}) {
    const escape = typeof options.escapeHtml === "function" ? options.escapeHtml : escapeHtml;
    const getAsset = typeof options.getAsset === "function" ? options.getAsset : () => null;
    const getAssetUrl = typeof options.getAssetUrl === "function" ? options.getAssetUrl : () => "";
    const safePlane = getSafeStageImagePlane(plane);
    const event = visualState.stageImageEvent;
    const images = (visualState.visibleStageImages ?? [])
      .filter((imageState) => getSafeStageImagePlane(imageState.plane) === safePlane)
      .map((imageState) => ({ ...imageState, __ghostMode: "" }));
    if (event?.mode === "hide" && event.previousState && getSafeStageImagePlane(event.previousState.plane) === safePlane) {
      images.push({ ...event.previousState, __ghostMode: "hide" });
    }
    if (!images.length) return "";

    const cards = images.map((imageState) => {
      const asset = getAsset(imageState.assetId);
      const assetUrl = asset ? getAssetUrl(asset) : "";
      const isActiveEvent = event?.layerId === imageState.layerId;
      const classes = ["stage-image-card"];
      if (isActiveEvent && event.mode === "show") classes.push("is-entering");
      if (isActiveEvent && event.mode === "move") classes.push("is-moving");
      if (imageState.__ghostMode === "hide") classes.push("is-leaving");
      const style = `${getStageImageStyle(imageState)}${isActiveEvent ? getStageImageMotionStyle(event) : ""}`;
      const content = assetUrl
        ? `<img src="${escape(assetUrl)}" alt="${escape(asset?.name ?? imageState.layerId)}" draggable="false" />`
        : `<div class="stage-image-placeholder"><strong>${escape(asset?.name ?? imageState.assetId ?? "未选择图片")}</strong><span>${escape(imageState.layerId)}</span></div>`;
      return `<div class="${classes.join(" ")}" data-layer-id="${escape(imageState.layerId)}" style="${style}">${content}</div>`;
    }).join("");
    return `<div class="stage-image-layer stage-image-layer-${safePlane}" aria-hidden="true">${cards}</div>`;
  }

  global.CanvasiaEditorStageImages = Object.freeze({
    STAGE_IMAGE_ASSET_TYPES,
    STAGE_IMAGE_ACTION_LABELS,
    STAGE_IMAGE_PLANE_LABELS,
    STAGE_IMAGE_POSITION_LABELS,
    STAGE_IMAGE_EASING_LABELS,
    DEFAULT_STAGE_IMAGE_TRANSFORM,
    STAGE_IMAGE_PRESETS,
    STAGE_IMAGE_DURATION_DEFAULT_MS,
    STAGE_IMAGE_DURATION_MIN_MS,
    STAGE_IMAGE_DURATION_MAX_MS,
    getSafeStageImageAction,
    getStageImageActionLabel,
    getSafeStageImagePlane,
    getStageImagePlaneLabel,
    getSafeStageImagePosition,
    getStageImagePositionLabel,
    getSafeStageImageEasing,
    getStageImageEasingLabel,
    getSafeStageImageLayerId,
    getSafeStageImageTransform,
    getSafeStageImageDurationMs,
    getStageImagePreset,
    applyStageImagePreset,
    normalizeStageImageState,
    sortStageImages,
    cloneStageImageState,
    applyStageImageBlock,
    getStageImageSummary,
    getStageImagePositionPercent,
    getStageImageStyle,
    getStageImageMotionStyle,
    renderStageImageEditor,
    getStageImageAssets,
    getSafeStageImageAssetId,
    readStageImageEditorBlock,
    applyStageImagePresetToEditor,
    renderStageImageLayer,
  });
})(typeof window !== "undefined" ? window : globalThis);
