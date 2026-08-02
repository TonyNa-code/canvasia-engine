(function attachCharacterStageComposerTools(global) {
  const commonTools = global.CanvasiaEditorCommon || {};

  const CUSTOM_CHARACTER_STAGE_PRESET_LIMIT = 24;
  const CUSTOM_CHARACTER_STAGE_PRESET_NAME_MAX_LENGTH = 36;
  const CHARACTER_STAGE_FIELD_IDS = Object.freeze({
    offsetX: "editorCharacterOffsetX",
    offsetY: "editorCharacterOffsetY",
    scale: "editorCharacterScale",
    opacity: "editorCharacterOpacity",
    layer: "editorCharacterLayer",
    flipX: "editorCharacterFlipX",
    position: "editorCharacterPosition",
  });

  function fallbackEscapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  const escapeHtml = commonTools.escapeHtml || fallbackEscapeHtml;

  function toArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function cleanText(value, fallback = "") {
    const text = String(value ?? "").replace(/\s+/g, " ").trim();
    return text || fallback;
  }

  function clampNumber(value, minimum, maximum, fallback = minimum) {
    const number = Number(value);
    if (!Number.isFinite(number)) {
      return fallback;
    }
    return Math.min(Math.max(number, minimum), maximum);
  }

  function makeCharacterStagePresetBaseId(value) {
    const slug = cleanText(value)
      .normalize("NFKC")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/^_+|_+$/g, "")
      .slice(0, 42);
    return slug ? `stage_${slug}` : "stage_composition";
  }

  function makeUniqueCharacterStagePresetId(name, existingIds = []) {
    const used = new Set(toArray(existingIds).map((item) => cleanText(item)).filter(Boolean));
    const baseId = makeCharacterStagePresetBaseId(name);
    let candidate = baseId;
    let suffix = 2;
    while (used.has(candidate)) {
      candidate = `${baseId}_${String(suffix).padStart(2, "0")}`;
      suffix += 1;
    }
    return candidate;
  }

  function normalizeCharacterStagePresetId(value, fallbackName = "") {
    const cleanId = cleanText(value)
      .normalize("NFKC")
      .toLowerCase()
      .replace(/[^a-z0-9_]+/g, "_")
      .replace(/^_+|_+$/g, "")
      .slice(0, 64);
    return cleanId || makeCharacterStagePresetBaseId(fallbackName);
  }

  function makeUniqueNormalizedCharacterStagePresetId(value, fallbackName, existingIds = []) {
    const used = new Set(toArray(existingIds).map((item) => cleanText(item)).filter(Boolean));
    const baseId = normalizeCharacterStagePresetId(value, fallbackName);
    let candidate = baseId;
    let suffix = 2;
    while (used.has(candidate)) {
      candidate = `${baseId.slice(0, 61)}_${String(suffix).padStart(2, "0")}`;
      suffix += 1;
    }
    return candidate;
  }

  function normalizeCharacterStagePreset(rawPreset = {}, index = 0, options = {}) {
    const getSafeCharacterStage = options.getSafeCharacterStage || ((value) => ({ ...(value || {}) }));
    const getSafePosition = options.getSafePosition || ((value) => cleanText(value, "center"));
    const source = rawPreset && typeof rawPreset === "object" ? rawPreset : {};
    const name = cleanText(source.name, `构图 ${index + 1}`).slice(0, CUSTOM_CHARACTER_STAGE_PRESET_NAME_MAX_LENGTH);
    const id = normalizeCharacterStagePresetId(source.id, name);
    return {
      id,
      name,
      position: getSafePosition(source.position),
      stage: getSafeCharacterStage(source.stage),
    };
  }

  function normalizeCharacterStagePresets(value, options = {}) {
    const normalized = [];
    const usedIds = new Set();
    toArray(value)
      .slice(0, CUSTOM_CHARACTER_STAGE_PRESET_LIMIT)
      .forEach((rawPreset, index) => {
        if (!rawPreset || typeof rawPreset !== "object" || !cleanText(rawPreset.name)) {
          return;
        }
        const preset = normalizeCharacterStagePreset(rawPreset, index, options);
        const uniqueId = makeUniqueNormalizedCharacterStagePresetId(preset.id, preset.name, [...usedIds]);
        usedIds.add(uniqueId);
        normalized.push({ ...preset, id: uniqueId });
      });
    return normalized;
  }

  function getCharacterStagePresetById(presets = [], presetId = "", options = {}) {
    const cleanId = cleanText(presetId);
    if (!cleanId) {
      return null;
    }
    return normalizeCharacterStagePresets(presets, options).find((preset) => preset.id === cleanId) ?? null;
  }

  function isSameCharacterStage(leftSource = {}, rightSource = {}, options = {}) {
    const getSafeCharacterStage = options.getSafeCharacterStage || ((value) => ({ ...(value || {}) }));
    const left = getSafeCharacterStage(leftSource);
    const right = getSafeCharacterStage(rightSource);
    return (
      left.offsetX === right.offsetX &&
      left.offsetY === right.offsetY &&
      left.scale === right.scale &&
      left.opacity === right.opacity &&
      left.layer === right.layer &&
      left.flipX === right.flipX
    );
  }

  function getMatchingCustomCharacterStagePresetId(presets = [], stageSource = {}, positionSource = "center", options = {}) {
    const getSafePosition = options.getSafePosition || ((value) => cleanText(value, "center"));
    const position = getSafePosition(positionSource);
    const match = normalizeCharacterStagePresets(presets, options).find(
      (preset) => preset.position === position && isSameCharacterStage(preset.stage, stageSource, options)
    );
    return match?.id ?? "";
  }

  function buildCharacterStagePresetSavePlan(input = {}, options = {}) {
    const currentPresets = normalizeCharacterStagePresets(input.currentPresets, options);
    const name = cleanText(input.name).slice(0, CUSTOM_CHARACTER_STAGE_PRESET_NAME_MAX_LENGTH);
    if (!name) {
      return { ok: false, reason: "name_required", nextPresets: currentPresets };
    }

    const getSafeCharacterStage = options.getSafeCharacterStage || ((value) => ({ ...(value || {}) }));
    const getSafePosition = options.getSafePosition || ((value) => cleanText(value, "center"));
    const selectedPresetId = cleanText(input.selectedPresetId);
    const selectedIndex = currentPresets.findIndex((preset) => preset.id === selectedPresetId);
    const sameNameIndex = currentPresets.findIndex(
      (preset) => preset.name.localeCompare(name, undefined, { sensitivity: "accent" }) === 0
    );
    const updateIndex = selectedIndex >= 0 ? selectedIndex : sameNameIndex;
    const isUpdate = updateIndex >= 0;
    if (!isUpdate && currentPresets.length >= CUSTOM_CHARACTER_STAGE_PRESET_LIMIT) {
      return { ok: false, reason: "limit_reached", nextPresets: currentPresets };
    }

    const targetId = isUpdate
      ? currentPresets[updateIndex].id
      : makeUniqueCharacterStagePresetId(name, currentPresets.map((preset) => preset.id));
    const nextPreset = normalizeCharacterStagePreset(
      {
        id: targetId,
        name,
        position: getSafePosition(input.position),
        stage: getSafeCharacterStage(input.stage),
      },
      Math.max(updateIndex, currentPresets.length),
      options
    );
    const nextPresets = isUpdate
      ? currentPresets.map((preset, index) => (index === updateIndex ? nextPreset : preset))
      : [...currentPresets, nextPreset];
    return {
      ok: true,
      reason: "",
      isUpdate,
      targetId,
      name,
      preset: nextPreset,
      nextPresets,
    };
  }

  function buildCharacterStagePresetDeletePlan(presets = [], presetId = "", options = {}) {
    const currentPresets = normalizeCharacterStagePresets(presets, options);
    const preset = currentPresets.find((entry) => entry.id === cleanText(presetId)) ?? null;
    if (!preset) {
      return { ok: false, reason: "not_found", preset: null, nextPresets: currentPresets };
    }
    return {
      ok: true,
      reason: "",
      preset,
      nextPresets: currentPresets.filter((entry) => entry.id !== preset.id),
    };
  }

  function buildDraggedCharacterStage(startStage = {}, drag = {}, options = {}) {
    const getSafeCharacterStage = options.getSafeCharacterStage || ((value) => ({ ...(value || {}) }));
    const start = getSafeCharacterStage(startStage);
    const referenceWidth = Math.max(24, Number(drag.referenceWidth) || 72);
    const referenceHeight = Math.max(24, Number(drag.referenceHeight) || 108);
    const precision = drag.precise ? 0.35 : 1;
    const nextOffsetX = start.offsetX + ((Number(drag.deltaX) || 0) / referenceWidth) * 100 * precision;
    const nextOffsetY = start.offsetY + ((Number(drag.deltaY) || 0) / referenceHeight) * 100 * precision;
    return getSafeCharacterStage({
      ...start,
      offsetX: Math.round(nextOffsetX),
      offsetY: Math.round(nextOffsetY),
    });
  }

  function getCharacterStageKeyboardDelta(event = {}) {
    const moveStep = event.shiftKey ? 10 : 2;
    const scaleStep = event.shiftKey ? 12 : 3;
    const layerStep = event.shiftKey ? 2 : 1;
    if (event.code === "ArrowLeft") return { offsetX: -moveStep };
    if (event.code === "ArrowRight") return { offsetX: moveStep };
    if (event.code === "ArrowUp") return { offsetY: -moveStep };
    if (event.code === "ArrowDown") return { offsetY: moveStep };
    if (["Equal", "NumpadAdd"].includes(event.code)) return { scale: scaleStep };
    if (["Minus", "NumpadSubtract"].includes(event.code)) return { scale: -scaleStep };
    if (event.code === "BracketRight") return { layer: layerStep };
    if (event.code === "BracketLeft") return { layer: -layerStep };
    return null;
  }

  function getCharacterStageWheelDelta(event = {}) {
    const direction = Number(event.deltaY) > 0 ? -1 : 1;
    return { scale: direction * (event.shiftKey ? 12 : 4) };
  }

  function readCharacterStageControls(doc, options = {}) {
    const getSafeCharacterStage = options.getSafeCharacterStage || ((value) => ({ ...(value || {}) }));
    return getSafeCharacterStage({
      offsetX: doc?.getElementById?.(CHARACTER_STAGE_FIELD_IDS.offsetX)?.value,
      offsetY: doc?.getElementById?.(CHARACTER_STAGE_FIELD_IDS.offsetY)?.value,
      scale: doc?.getElementById?.(CHARACTER_STAGE_FIELD_IDS.scale)?.value,
      opacity: doc?.getElementById?.(CHARACTER_STAGE_FIELD_IDS.opacity)?.value,
      layer: doc?.getElementById?.(CHARACTER_STAGE_FIELD_IDS.layer)?.value,
      flipX: doc?.getElementById?.(CHARACTER_STAGE_FIELD_IDS.flipX)?.checked,
    });
  }

  function setCharacterStageControlValues(doc, stageSource = {}, options = {}) {
    const getSafeCharacterStage = options.getSafeCharacterStage || ((value) => ({ ...(value || {}) }));
    const stage = getSafeCharacterStage(stageSource);
    ["offsetX", "offsetY", "scale", "opacity", "layer"].forEach((field) => {
      const input = doc?.getElementById?.(CHARACTER_STAGE_FIELD_IDS[field]);
      if (input) input.value = String(stage[field]);
    });
    const flipInput = doc?.getElementById?.(CHARACTER_STAGE_FIELD_IDS.flipX);
    if (flipInput) flipInput.checked = Boolean(stage.flipX);
    return stage;
  }

  function getCharacterStageControlPosition(doc, options = {}) {
    const getSafePosition = options.getSafePosition || ((value) => cleanText(value, "center"));
    return getSafePosition(doc?.getElementById?.(CHARACTER_STAGE_FIELD_IDS.position)?.value);
  }

  function setCharacterStageControlPosition(doc, positionSource, options = {}) {
    const getSafePosition = options.getSafePosition || ((value) => cleanText(value, "center"));
    const position = getSafePosition(positionSource);
    const select = doc?.getElementById?.(CHARACTER_STAGE_FIELD_IDS.position);
    if (select) select.value = position;
    return position;
  }

  function buildCharacterStagePreviewSummary(stageSource = {}, positionSource = "center", options = {}) {
    const getPositionLabel = options.getPositionLabel || ((value) => cleanText(value, "中央"));
    const getCharacterStageSummary = options.getCharacterStageSummary || (() => "默认大小");
    return `${getPositionLabel(positionSource)} · ${getCharacterStageSummary(stageSource)}`;
  }

  function renderPresetCard(preset = {}, options = {}) {
    const custom = Boolean(options.custom);
    const active = Boolean(options.active);
    const action = custom ? "apply-custom-character-stage-preset" : "apply-character-stage-preset";
    const dataAttribute = custom ? "data-custom-character-stage-preset" : "data-character-stage-preset";
    const label = custom ? preset.name : preset.label;
    const description = custom ? options.summary : preset.description;
    return `
      <button
        type="button"
        class="stage-preset-chip${custom ? " is-custom" : ""}${active ? " is-active" : ""}"
        data-action="${action}"
        ${dataAttribute}="${escapeHtml(preset.id)}"
        aria-pressed="${active ? "true" : "false"}"
        title="${escapeHtml(description)}"
      >
        <strong>${escapeHtml(label)}<em class="stage-preset-current">当前</em></strong>
        <span>${escapeHtml(description)}</span>
      </button>
    `;
  }

  function renderCharacterStageLivePreview(stageSource = {}, positionSource = "center", options = {}) {
    const getSafeCharacterStage = options.getSafeCharacterStage || ((value) => ({ ...(value || {}) }));
    const getSafePosition = options.getSafePosition || ((value) => cleanText(value, "center"));
    const getCharacterStageStyle = options.getCharacterStageStyle || (() => "");
    const stage = getSafeCharacterStage(stageSource);
    const position = getSafePosition(positionSource);
    const summary = buildCharacterStagePreviewSummary(stage, position, options);
    const spriteUrl = cleanText(options.spriteUrl);
    const spriteLabel = cleanText(options.spriteLabel, "当前立绘");
    const backdropStyle = cleanText(options.backdropStyle);
    const spriteMarkup = spriteUrl
      ? `<img src="${escapeHtml(spriteUrl)}" alt="" draggable="false" />`
      : `
          <span class="stage-control-preview-head"></span>
          <span class="stage-control-preview-body"></span>
        `;
    return `
      <div
        class="stage-control-preview stage-composer-monitor${spriteUrl ? " has-real-sprite" : " is-fallback-sprite"}"
        data-character-stage-preview
        tabindex="0"
        aria-label="舞台构图预览。可直接拖动立绘；滚轮缩放；方向键微调，Shift 加速。"
        style="${escapeHtml(backdropStyle)}"
      >
        <div class="stage-control-preview-grid" aria-hidden="true"></div>
        <div class="stage-composer-safe-frame" aria-hidden="true"><span>SAFE FRAME</span></div>
        <div class="stage-composer-axis is-left" aria-hidden="true">L</div>
        <div class="stage-composer-axis is-center" aria-hidden="true">C</div>
        <div class="stage-composer-axis is-right" aria-hidden="true">R</div>
        <div class="stage-control-preview-floor" aria-hidden="true"></div>
        ${options.ensembleMarkup ?? ""}
        <div
          class="stage-control-preview-sprite${spriteUrl ? " has-image" : ""}"
          data-character-stage-preview-sprite
          data-position="${escapeHtml(position)}"
          style="${escapeHtml(getCharacterStageStyle(stage))}"
          role="img"
          aria-label="${escapeHtml(`${spriteLabel}，拖动可改变位置`)}"
          aria-grabbed="false"
        >
          ${spriteMarkup}
          <span class="stage-composer-drag-handle" aria-hidden="true">DRAG</span>
        </div>
        <div class="stage-control-preview-summary">
          <strong>STAGE COMPOSER</strong>
          <span data-character-stage-preview-summary>${escapeHtml(summary)}</span>
        </div>
      </div>
    `;
  }

  function renderCharacterStageControls(stageSource = {}, options = {}) {
    const getSafeCharacterStage = options.getSafeCharacterStage || ((value) => ({ ...(value || {}) }));
    const getSafePosition = options.getSafePosition || ((value) => cleanText(value, "center"));
    const getPositionLabel = options.getPositionLabel || ((value) => cleanText(value, "中央"));
    const getCharacterStageSummary = options.getCharacterStageSummary || (() => "默认大小");
    const stage = getSafeCharacterStage(stageSource);
    const position = getSafePosition(options.position);
    const builtInPresets = toArray(options.builtInPresets);
    const customPresets = normalizeCharacterStagePresets(options.customPresets, options);
    const matchingBuiltInId = typeof options.getMatchingBuiltInPresetId === "function"
      ? options.getMatchingBuiltInPresetId(stage, position)
      : "";
    const matchingCustomId = getMatchingCustomCharacterStagePresetId(customPresets, stage, position, options);
    const presetCards = builtInPresets
      .map((preset) => {
        const summary = preset.position
          ? `${getPositionLabel(preset.position)} · ${getCharacterStageSummary(preset.stage)}`
          : getCharacterStageSummary(preset.stage);
        return renderPresetCard(preset, {
          active: preset.id === matchingBuiltInId && !matchingCustomId,
          summary,
        });
      })
      .join("");
    const customCards = customPresets
      .map((preset) =>
        renderPresetCard(preset, {
          custom: true,
          active: preset.id === matchingCustomId,
          summary: `${getPositionLabel(preset.position)} · ${getCharacterStageSummary(preset.stage)}`,
        })
      )
      .join("");
    const adjustmentButtons = toArray(options.adjustments)
      .map(
        (adjustment) => `
          <button
            type="button"
            class="stage-adjust-button"
            data-action="adjust-character-stage"
            data-character-stage-adjustment="${escapeHtml(adjustment.id)}"
            title="${escapeHtml(adjustment.description)}"
          >
            <strong>${escapeHtml(adjustment.label)}</strong>
            <span>${escapeHtml(adjustment.description)}</span>
          </button>
        `
      )
      .join("");
    const selectedCustomPreset = customPresets.find((preset) => preset.id === matchingCustomId) ?? null;

    return `
      <div class="detail-row character-stage-controls" data-character-stage-composer>
        <div class="stage-composer-heading">
          <div>
            <span>DIRECTING TOOL</span>
            <strong>舞台构图器</strong>
          </div>
          <p>拖动立绘定位置，滚轮调大小；满意后可存成这个项目自己的构图。</p>
        </div>
        ${renderCharacterStageLivePreview(stage, position, options)}
        ${options.blockingWorkspaceMarkup ?? ""}
        <div class="stage-preset-section">
          <div class="stage-preset-section-head">
            <strong>基础构图</strong>
            <span>先选一个能用的，再微调</span>
          </div>
          <div class="stage-preset-grid" aria-label="内置立绘舞台预设">${presetCards}</div>
        </div>
        <div
          class="stage-custom-preset-library"
          data-character-stage-preset-library
          data-selected-character-stage-preset-id="${escapeHtml(matchingCustomId)}"
        >
          <div class="stage-preset-section-head">
            <strong>我的构图</strong>
            <span>${customPresets.length}/${CUSTOM_CHARACTER_STAGE_PRESET_LIMIT} · 全项目可复用</span>
          </div>
          ${
            customCards
              ? `<div class="stage-preset-grid is-custom" aria-label="项目自定义构图预设">${customCards}</div>`
              : `<div class="stage-custom-preset-empty">还没有自己的构图。把当前立绘摆好后，在下面起名保存即可。</div>`
          }
          <div class="stage-custom-preset-actions">
            <label>
              <span>构图名称</span>
              <input
                id="editorCharacterStagePresetName"
                type="text"
                maxlength="${CUSTOM_CHARACTER_STAGE_PRESET_NAME_MAX_LENGTH}"
                value="${escapeHtml(selectedCustomPreset?.name ?? "")}"
                placeholder="例如：双人对话右侧近景"
              />
            </label>
            <button type="button" class="toolbar-button toolbar-button-primary" data-action="save-character-stage-preset">
              保存当前构图
            </button>
            <button type="button" class="toolbar-button" data-action="delete-character-stage-preset" ${selectedCustomPreset ? "" : "disabled"}>
              删除当前预设
            </button>
          </div>
        </div>
        <div class="stage-adjust-panel" tabindex="0" aria-label="立绘微调。方向键移动，加减缩放，中括号调整层级。">
          <div class="stage-adjust-head">
            <strong>精细调整</strong>
            <span>方向键移动 · 滚轮或 +/- 缩放 · [ ] 层级</span>
          </div>
          <div class="stage-adjust-grid">${adjustmentButtons}</div>
        </div>
        <div class="field-grid compact-grid stage-composer-number-grid">
          <label><span>X 偏移 %</span><input id="${CHARACTER_STAGE_FIELD_IDS.offsetX}" type="number" min="-60" max="60" step="1" value="${stage.offsetX}" /></label>
          <label><span>Y 偏移 %</span><input id="${CHARACTER_STAGE_FIELD_IDS.offsetY}" type="number" min="-45" max="45" step="1" value="${stage.offsetY}" /></label>
          <label><span>缩放 %</span><input id="${CHARACTER_STAGE_FIELD_IDS.scale}" type="number" min="45" max="220" step="1" value="${stage.scale}" /></label>
          <label><span>透明度 %</span><input id="${CHARACTER_STAGE_FIELD_IDS.opacity}" type="number" min="0" max="100" step="1" value="${stage.opacity}" /></label>
          <label><span>层级</span><input id="${CHARACTER_STAGE_FIELD_IDS.layer}" type="number" min="-10" max="10" step="1" value="${stage.layer}" /></label>
        </div>
        <label class="toggle-row compact-toggle">
          <input id="${CHARACTER_STAGE_FIELD_IDS.flipX}" type="checkbox" ${stage.flipX ? "checked" : ""} />
          <span>水平镜像立绘，让角色朝向画面另一侧</span>
        </label>
      </div>
    `;
  }

  function createCharacterStageComposerController(options = {}) {
    const doc = options.document ?? global.document;
    let dragState = null;

    const getToolOptions = () => ({
      getSafeCharacterStage: options.getSafeCharacterStage,
      getSafePosition: options.getSafePosition,
      getPositionLabel: options.getPositionLabel,
      getCharacterStageSummary: options.getCharacterStageSummary,
    });
    const getCurrentPresets = () => normalizeCharacterStagePresets(options.getCustomPresets?.() ?? [], getToolOptions());

    function readStage() {
      return readCharacterStageControls(doc, getToolOptions());
    }

    function readPosition() {
      return getCharacterStageControlPosition(doc, getToolOptions());
    }

    function setStage(stageSource) {
      return setCharacterStageControlValues(doc, stageSource, getToolOptions());
    }

    function setPosition(positionSource) {
      return setCharacterStageControlPosition(doc, positionSource, getToolOptions());
    }

    function update(stageSource = readStage(), positionSource = readPosition()) {
      const stage = options.getSafeCharacterStage(stageSource);
      const position = options.getSafePosition(positionSource);
      const previewSprite = doc?.querySelector?.("[data-character-stage-preview-sprite]");
      const previewSummary = doc?.querySelector?.("[data-character-stage-preview-summary]");
      if (previewSprite) {
        previewSprite.dataset.position = position;
        previewSprite.setAttribute("style", options.getCharacterStageStyle(stage));
      }
      if (previewSummary) {
        previewSummary.textContent = buildCharacterStagePreviewSummary(stage, position, options);
      }

      const matchingBuiltInId = options.getMatchingBuiltInPresetId?.(stage, position) ?? "";
      const customPresets = getCurrentPresets();
      const matchingCustomId = getMatchingCustomCharacterStagePresetId(customPresets, stage, position, getToolOptions());
      doc?.querySelectorAll?.("[data-character-stage-preset]").forEach((button) => {
        const active = !matchingCustomId && button.getAttribute("data-character-stage-preset") === matchingBuiltInId;
        button.classList.toggle("is-active", active);
        button.setAttribute("aria-pressed", active ? "true" : "false");
      });
      doc?.querySelectorAll?.("[data-custom-character-stage-preset]").forEach((button) => {
        const active = button.getAttribute("data-custom-character-stage-preset") === matchingCustomId;
        button.classList.toggle("is-active", active);
        button.setAttribute("aria-pressed", active ? "true" : "false");
      });
      const library = doc?.querySelector?.("[data-character-stage-preset-library]");
      if (library) library.dataset.selectedCharacterStagePresetId = matchingCustomId;
      const deleteButton = doc?.querySelector?.('[data-action="delete-character-stage-preset"]');
      if (deleteButton) deleteButton.disabled = !matchingCustomId;
      return { stage, position, matchingBuiltInId, matchingCustomId };
    }

    function announce(message, delay = 220) {
      options.onChanged?.({ message, delay, stage: readStage(), position: readPosition() });
    }

    function applyBuiltInPreset(presetId) {
      const preset = options.getBuiltInPreset?.(presetId);
      if (!preset) return false;
      const position = preset.position ? setPosition(preset.position) : readPosition();
      setStage(preset.stage);
      update(preset.stage, position);
      announce(`已套用构图：${preset.label}`, 300);
      return true;
    }

    function applyCustomPreset(presetId) {
      const preset = getCharacterStagePresetById(getCurrentPresets(), presetId, getToolOptions());
      if (!preset) return false;
      setStage(preset.stage);
      setPosition(preset.position);
      update(preset.stage, preset.position);
      const nameInput = doc?.getElementById?.("editorCharacterStagePresetName");
      if (nameInput) nameInput.value = preset.name;
      announce(`已套用我的构图：${preset.name}`, 300);
      return true;
    }

    function applyAdjustment(adjustmentId) {
      const nextStage = options.applyCharacterStageAdjustment(readStage(), adjustmentId);
      setStage(nextStage);
      update(nextStage, readPosition());
      announce(`构图微调：${buildCharacterStagePreviewSummary(nextStage, readPosition(), options)}`, 220);
      return true;
    }

    function handleKeyboard(event) {
      if (event?.defaultPrevented || event?.altKey || event?.ctrlKey || event?.metaKey) return false;
      const target = event?.target;
      if (!target?.closest) return false;
      const controls = target.closest(".character-stage-controls");
      if (!controls || target.closest("input, textarea, select")) return false;
      const delta = getCharacterStageKeyboardDelta(event);
      if (!delta) return false;
      event.preventDefault?.();
      const nextStage = options.applyCharacterStageDelta(readStage(), delta);
      setStage(nextStage);
      update(nextStage, readPosition());
      announce(`键盘微调：${buildCharacterStagePreviewSummary(nextStage, readPosition(), options)}`, 180);
      return true;
    }

    function handlePointerDown(event) {
      if (event?.button != null && event.button !== 0) return false;
      const sprite = event?.target?.closest?.("[data-character-stage-preview-sprite]");
      const monitor = sprite?.closest?.("[data-character-stage-preview]");
      if (!sprite || !monitor) return false;
      const rect = sprite.getBoundingClientRect?.() ?? { width: 72, height: 108 };
      const startStage = readStage();
      const scale = Math.max(0.45, Number(startStage.scale) / 100 || 1);
      dragState = {
        pointerId: event.pointerId,
        startX: Number(event.clientX) || 0,
        startY: Number(event.clientY) || 0,
        referenceWidth: Math.max(24, (Number(rect.width) || 72) / scale),
        referenceHeight: Math.max(24, (Number(rect.height) || 108) / scale),
        startStage,
        sprite,
        monitor,
      };
      sprite.setPointerCapture?.(event.pointerId);
      sprite.setAttribute?.("aria-grabbed", "true");
      monitor.classList?.add("is-dragging");
      event.preventDefault?.();
      return true;
    }

    function handlePointerMove(event) {
      if (!dragState || (dragState.pointerId != null && event?.pointerId !== dragState.pointerId)) return false;
      const nextStage = buildDraggedCharacterStage(
        dragState.startStage,
        {
          deltaX: (Number(event.clientX) || 0) - dragState.startX,
          deltaY: (Number(event.clientY) || 0) - dragState.startY,
          referenceWidth: dragState.referenceWidth,
          referenceHeight: dragState.referenceHeight,
          precise: Boolean(event.altKey),
        },
        getToolOptions()
      );
      setStage(nextStage);
      update(nextStage, readPosition());
      options.onLiveChanged?.({ stage: nextStage, position: readPosition(), delay: 120 });
      event.preventDefault?.();
      return true;
    }

    function endPointerDrag(event) {
      if (!dragState || (dragState.pointerId != null && event?.pointerId !== dragState.pointerId)) return false;
      dragState.sprite?.releasePointerCapture?.(dragState.pointerId);
      dragState.sprite?.setAttribute?.("aria-grabbed", "false");
      dragState.monitor?.classList?.remove("is-dragging");
      dragState = null;
      announce(`构图位置已更新：${buildCharacterStagePreviewSummary(readStage(), readPosition(), options)}`, 160);
      return true;
    }

    function handleWheel(event) {
      const monitor = event?.target?.closest?.("[data-character-stage-preview]");
      if (!monitor) return false;
      event.preventDefault?.();
      const nextStage = options.applyCharacterStageDelta(readStage(), getCharacterStageWheelDelta(event));
      setStage(nextStage);
      update(nextStage, readPosition());
      announce(`滚轮缩放：${nextStage.scale}%`, 160);
      return true;
    }

    return Object.freeze({
      readStage,
      readPosition,
      setStage,
      setPosition,
      update,
      applyBuiltInPreset,
      applyCustomPreset,
      applyAdjustment,
      handleKeyboard,
      handlePointerDown,
      handlePointerMove,
      handlePointerUp: endPointerDrag,
      handlePointerCancel: endPointerDrag,
      handleWheel,
      isDragging: () => Boolean(dragState),
    });
  }

  global.CanvasiaEditorCharacterStageComposer = Object.freeze({
    CUSTOM_CHARACTER_STAGE_PRESET_LIMIT,
    CUSTOM_CHARACTER_STAGE_PRESET_NAME_MAX_LENGTH,
    CHARACTER_STAGE_FIELD_IDS,
    makeCharacterStagePresetBaseId,
    makeUniqueCharacterStagePresetId,
    normalizeCharacterStagePresetId,
    makeUniqueNormalizedCharacterStagePresetId,
    normalizeCharacterStagePreset,
    normalizeCharacterStagePresets,
    getCharacterStagePresetById,
    isSameCharacterStage,
    getMatchingCustomCharacterStagePresetId,
    buildCharacterStagePresetSavePlan,
    buildCharacterStagePresetDeletePlan,
    buildDraggedCharacterStage,
    getCharacterStageKeyboardDelta,
    getCharacterStageWheelDelta,
    readCharacterStageControls,
    setCharacterStageControlValues,
    getCharacterStageControlPosition,
    setCharacterStageControlPosition,
    buildCharacterStagePreviewSummary,
    renderCharacterStageLivePreview,
    renderCharacterStageControls,
    createCharacterStageComposerController,
  });
})(typeof window !== "undefined" ? window : globalThis);
