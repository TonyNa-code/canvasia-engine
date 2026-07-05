(function attachRenpyExporterTools(global) {
  "use strict";

  const CHOICE_CONTINUE_TARGET = "__continue__";
  const BLOCK_TYPES_REQUIRING_COMMENT = Object.freeze([
    "particle_effect",
    "screen_filter",
    "depth_blur",
    "camera_zoom",
    "camera_pan",
  ]);
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

  function clampNumber(value, min, max) {
    return Math.min(Math.max(value, min), max);
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

  function getTransitionDurationSeconds(block = {}) {
    const value = Number(block.transitionDurationMs ?? 600);
    const ms = Number.isFinite(value) ? clampNumber(value, 0, 5000) : 600;
    return Number((ms / 1000).toFixed(2));
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
      const assetId = cleanText(block.assetId, "missing_background");
      return [`    scene ${normalizeIdentifier(assetId, "background")} with fade`];
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
      return [`    play music ${quoteRenpy(path || "audio/bgm.ogg")}${fadeIn ? ` fadein ${fadeIn}` : ""}`];
    }
    if (type === "music_stop") {
      const fadeOut = secondsFromMs(block.fadeOutMs);
      return [`    stop music${fadeOut ? ` fadeout ${fadeOut}` : ""}`];
    }
    if (type === "sfx_play") {
      return [`    play sound ${quoteRenpy(getAssetPath(assetMap, block.assetId) || "audio/sfx.ogg")}`];
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
      return ['    with Fade(0.08, 0.0, 0.28, color="#ffffff")'];
    }
    if (type === "screen_fade") {
      return ["    with fade"];
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
      lines.push(`# ${record.chapterName} / ${cleanText(scene.name ?? scene.title, sceneId)}`);
      lines.push(`label ${getSceneLabel(sceneId, sceneMap)}:`);
      const blocks = toArray(scene.blocks);
      if (!blocks.length) {
        pushWarning(warnings, "renpy_empty_scene", "空场景已导出 pass。", { sceneId });
        lines.push("    pass");
      } else {
        blocks.forEach((block, blockIndex) => {
          renderBlock(block, { assetMap, characterMap, sceneMap, warnings, sceneId, blockIndex }).forEach((line) => lines.push(line));
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
