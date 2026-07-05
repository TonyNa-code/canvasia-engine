(function attachScenePolishTools(global) {
  "use strict";

  const DEFAULTS = Object.freeze({
    transition: "fade",
    transitionDurationMs: 700,
    characterTransitionDurationMs: 620,
    musicFadeInMs: 900,
    musicFadeOutMs: 900,
    musicStopFadeOutMs: 700,
    musicVolume: 88,
    sfxVolume: 92,
    textSpeed: "normal",
  });

  function cloneValue(value) {
    return JSON.parse(JSON.stringify(value ?? null));
  }

  function toBlocks(sceneOrBlocks) {
    if (Array.isArray(sceneOrBlocks)) {
      return sceneOrBlocks;
    }
    return Array.isArray(sceneOrBlocks?.blocks) ? sceneOrBlocks.blocks : [];
  }

  function cleanText(value) {
    return String(value ?? "").trim();
  }

  function hasPositiveMs(value) {
    const numberValue = Number(value);
    return Number.isFinite(numberValue) && numberValue > 0;
  }

  function hasVolume(value) {
    const numberValue = Number(value);
    return Number.isFinite(numberValue) && numberValue > 0;
  }

  function pushChange(operation, field, from, to, label) {
    if (from === to) {
      return;
    }
    operation.fields.push({ field, from, to, label });
  }

  function ensureTransition(block, operation, defaults, durationMs) {
    const transition = cleanText(block.transition);
    if (!transition) {
      const nextTransition = defaults.transition;
      pushChange(operation, "transition", block.transition, nextTransition, "补默认转场");
      block.transition = nextTransition;
    }

    if (cleanText(block.transition) !== "none" && !hasPositiveMs(block.transitionDurationMs)) {
      pushChange(operation, "transitionDurationMs", block.transitionDurationMs, durationMs, "补转场时长");
      block.transitionDurationMs = durationMs;
    }
  }

  function ensureFadeMs(block, operation, field, value, label) {
    if (!hasPositiveMs(block[field])) {
      pushChange(operation, field, block[field], value, label);
      block[field] = value;
    }
  }

  function polishBlock(block, index, defaults) {
    const nextBlock = cloneValue(block) ?? {};
    const operation = {
      blockId: cleanText(nextBlock.id),
      blockType: cleanText(nextBlock.type),
      index,
      fields: [],
    };

    if (nextBlock.type === "dialogue" || nextBlock.type === "narration") {
      if (!cleanText(nextBlock.textSpeed)) {
        pushChange(operation, "textSpeed", nextBlock.textSpeed, defaults.textSpeed, "补文字速度");
        nextBlock.textSpeed = defaults.textSpeed;
      }
    } else if (nextBlock.type === "background") {
      ensureTransition(nextBlock, operation, defaults, defaults.transitionDurationMs);
    } else if (nextBlock.type === "character_show" || nextBlock.type === "character_hide") {
      ensureTransition(nextBlock, operation, defaults, defaults.characterTransitionDurationMs);
    } else if (nextBlock.type === "music_play") {
      ensureFadeMs(nextBlock, operation, "fadeInMs", defaults.musicFadeInMs, "补 BGM 淡入");
      ensureFadeMs(nextBlock, operation, "fadeOutMs", defaults.musicFadeOutMs, "补 BGM 淡出");
      if (!hasVolume(nextBlock.volume)) {
        pushChange(operation, "volume", nextBlock.volume, defaults.musicVolume, "补 BGM 音量");
        nextBlock.volume = defaults.musicVolume;
      }
      if (typeof nextBlock.loop !== "boolean") {
        pushChange(operation, "loop", nextBlock.loop, true, "补循环播放");
        nextBlock.loop = true;
      }
      if (!cleanText(nextBlock.endMode)) {
        pushChange(operation, "endMode", nextBlock.endMode, "until_next_music", "补播放范围");
        nextBlock.endMode = "until_next_music";
      }
    } else if (nextBlock.type === "music_stop") {
      ensureFadeMs(nextBlock, operation, "fadeOutMs", defaults.musicStopFadeOutMs, "补停止淡出");
    } else if (nextBlock.type === "sfx_play") {
      if (!hasVolume(nextBlock.volume)) {
        pushChange(operation, "volume", nextBlock.volume, defaults.sfxVolume, "补音效音量");
        nextBlock.volume = defaults.sfxVolume;
      }
    }

    return {
      block: nextBlock,
      operation: operation.fields.length ? operation : null,
    };
  }

  function buildScenePresentationPolishPlan(scene, options = {}) {
    const defaults = Object.freeze({ ...DEFAULTS, ...(options.defaults ?? {}) });
    const sourceBlocks = toBlocks(scene);
    const nextScene = cloneValue(scene) ?? {};
    const operations = [];
    const blocks = sourceBlocks.map((block, index) => {
      const result = polishBlock(block, index, defaults);
      if (result.operation) {
        operations.push(result.operation);
      }
      return result.block;
    });

    nextScene.blocks = blocks;

    return {
      changed: operations.length > 0,
      scene: nextScene,
      operations,
      changedBlockCount: operations.length,
      changedFieldCount: operations.reduce((total, operation) => total + operation.fields.length, 0),
      firstChangedBlockId: operations[0]?.blockId ?? "",
      firstChangedIndex: operations[0]?.index ?? -1,
      summary: buildScenePresentationPolishSummary(operations),
    };
  }

  function buildScenePresentationPolishSummary(operations = []) {
    const safeOperations = Array.isArray(operations) ? operations : [];
    const fieldCount = safeOperations.reduce((total, operation) => total + (operation.fields?.length ?? 0), 0);
    if (!safeOperations.length) {
      return "本场基础演出参数已经比较完整";
    }
    return `已润色 ${safeOperations.length} 张卡片，补齐 ${fieldCount} 个演出参数`;
  }

  global.CanvasiaEditorScenePolish = Object.freeze({
    DEFAULTS,
    buildScenePresentationPolishPlan,
    buildScenePresentationPolishSummary,
  });
})(typeof window !== "undefined" ? window : globalThis);
