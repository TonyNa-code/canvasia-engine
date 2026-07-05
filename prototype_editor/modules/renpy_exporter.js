(function attachRenpyExporterTools(global) {
  "use strict";

  const CHOICE_CONTINUE_TARGET = "__continue__";
  const BLOCK_TYPES_REQUIRING_COMMENT = Object.freeze([
    "particle_effect",
    "screen_shake",
    "screen_flash",
    "screen_filter",
    "depth_blur",
    "camera_zoom",
    "camera_pan",
    "video_play",
    "credits_roll",
    "variable_set",
    "variable_add",
    "condition",
  ]);

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
    return `"${String(value ?? "").replace(/\\/g, "\\\\").replace(/"/g, '\\"')}"`;
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

  function getBlockText(block = {}) {
    return cleanText(block.text ?? block.fields?.text);
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
        pushWarning(
          warnings,
          "renpy_choice_effects_review",
          `选项「${optionText}」包含 ${effectCount} 个变量或状态效果，需要在 Ren'Py 中手动确认。`,
          { ...getWarningContext(context), optionIndex }
        );
        lines.push(`            # Canvasia review choice effects: ${effectCount}`);
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
      const characterId = cleanText(block.characterId, "character");
      const expression = cleanText(block.expressionId);
      const position = cleanText(block.position, "center");
      return [`    show ${normalizeIdentifier(characterId, "character")}${expression ? ` ${normalizeIdentifier(expression, "expr")}` : ""} at ${position} with dissolve`];
    }
    if (type === "character_hide") {
      return [`    hide ${normalizeIdentifier(block.characterId, "character")} with dissolve`];
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
    if (type === "dialogue") {
      const characterId = cleanText(block.speakerId);
      const line = getBlockText(block);
      if (!characterId) {
        pushWarning(warnings, "renpy_missing_speaker", "台词缺少说话人，已作为旁白导出。", getWarningContext(context));
        return [`    ${quoteRenpy(line || " ")}`];
      }
      return [`    ${normalizeIdentifier(characterId, "character")} ${quoteRenpy(line || " ")}`];
    }
    if (type === "narration") {
      return [`    ${quoteRenpy(getBlockText(block) || " ")}`];
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
    const lines = [
      `# ${getProjectTitle(data, options)} - Canvasia Ren'Py draft`,
      "# Generated as a migration-friendly draft. Review labels, assets, and custom effects before shipping.",
      "",
      ...buildImageDefinitions(assetMap),
      "",
      ...buildCharacterDefinitions(characterMap),
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
