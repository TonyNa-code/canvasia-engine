(function attachStoryBlockFactoryTools(global) {
  "use strict";

  function asList(value) {
    return Array.isArray(value) ? value : [];
  }

  function getCallback(options, name, fallback) {
    return typeof options?.[name] === "function" ? options[name] : fallback;
  }

  function createDefaultStoryBlock(scene = {}, blockType = "", options = {}) {
    const safeType = String(blockType ?? "").trim();
    const blockId = String(options.blockId ?? "").trim() || "block_new";
    const sceneId = String(scene?.id ?? options.selectedSceneId ?? "");
    const blocks = asList(scene?.blocks);
    const characters = asList(options.characters);
    const variables = asList(options.variables);
    const assetList = asList(options.assetList);
    const characterId = options.selectedCharacterId ?? characters[0]?.id ?? "";
    const getSafeExpressionId = getCallback(options, "getSafeExpressionId", () => "");
    const getSafeAssetIdByType = getCallback(
      options,
      "getSafeAssetIdByType",
      (assetType) => assetList.find((asset) => asset?.type === assetType)?.id ?? ""
    );
    const getDefaultJumpTargetSceneId = getCallback(options, "getDefaultJumpTargetSceneId", () => "");

    if (safeType === "dialogue") {
      return {
        id: blockId,
        type: "dialogue",
        speakerId: characterId,
        expressionId: getSafeExpressionId(characterId, null),
        text: "新台词",
      };
    }

    if (safeType === "choice") {
      return {
        id: blockId,
        type: "choice",
        options: getCallback(options, "createDefaultChoiceOptions", () => [])(
          blockId,
          options.selectedSceneId ?? sceneId
        ),
      };
    }

    if (safeType === "narration") {
      return { id: blockId, type: "narration", text: "新旁白" };
    }

    if (safeType === "background") {
      return {
        id: blockId,
        type: "background",
        assetId: assetList.find((asset) => asset?.type === "background")?.id ?? "",
        transition: "fade",
      };
    }

    if (safeType === "stage_image") {
      const existingCount = blocks.filter((block) => block?.type === "stage_image").length;
      return {
        id: blockId,
        type: "stage_image",
        action: "show",
        layerId: `layer_${existingCount + 1}`,
        assetId: getCallback(options, "getSafeStageImageAssetId", () => "")(""),
        plane: "front",
        position: "center",
        transform: { ...(options.defaultStageImageTransform ?? {}) },
        durationMs: 520,
        easing: "ease_out",
      };
    }

    if (safeType === "character_show" || safeType === "character_move") {
      const result = {
        id: blockId,
        type: safeType,
        characterId,
        expressionId: getSafeExpressionId(characterId, null),
        position: getCallback(options, "getDefaultCharacterPosition", () => "center")(characterId),
        stage: { ...(options.defaultCharacterStage ?? {}) },
      };
      if (safeType === "character_show") {
        result.transition = "fade";
      } else {
        result.durationMs = 600;
        result.easing = "ease_out";
      }
      return result;
    }

    if (safeType === "character_hide") {
      return { id: blockId, type: "character_hide", characterId, transition: "fade" };
    }

    if (safeType === "music_play") {
      return {
        id: blockId,
        type: "music_play",
        assetId: getSafeAssetIdByType("bgm"),
        ...getCallback(options, "sanitizeMusicTransport", () => ({}))(),
        volume: 100,
        fadeInMs: 600,
        fadeOutMs: 600,
        endMode: "until_next_music",
        endBlockId: "",
      };
    }

    if (safeType === "music_stop") {
      return { id: blockId, type: "music_stop", fadeOutMs: 600 };
    }

    if (safeType === "sfx_play") {
      return {
        id: blockId,
        type: "sfx_play",
        assetId: getSafeAssetIdByType("sfx"),
        ...getCallback(options, "sanitizeSfxTransport", () => ({}))(),
      };
    }

    if (safeType === "sfx_stop") {
      return {
        id: blockId,
        type: "sfx_stop",
        ...getCallback(options, "sanitizeSfxStop", () => ({}))(),
      };
    }

    if (safeType === "video_play") {
      return {
        id: blockId,
        type: "video_play",
        assetId: getSafeAssetIdByType("video"),
        title: "Opening Movie",
        ...getCallback(options, "sanitizeVideoTransport", () => ({}))(),
      };
    }

    if (safeType === "credits_roll") {
      return {
        id: blockId,
        type: "credits_roll",
        title: "STAFF",
        subtitle: "Thank you for playing",
        lines: ["企划：Creator", "剧本：Writer", "美术：", "音乐：", "特别感谢：所有玩家"],
        durationSeconds: 18,
        background: "dark",
        skippable: true,
      };
    }

    if (safeType === "achievement_unlock") {
      const achievementCount = blocks.filter((block) => block?.type === "achievement_unlock").length;
      return {
        id: blockId,
        type: "achievement_unlock",
        achievementId: `story_achievement_${achievementCount + 1}`,
        title: "新的成就",
        description: "完成这段剧情时解锁。",
        category: "剧情里程碑",
        requirement: "推进到这段剧情",
        hiddenBeforeUnlock: false,
        iconAssetId: "",
      };
    }

    if (safeType === "wait") {
      return { id: blockId, type: "wait", durationSeconds: 1 };
    }

    if (safeType === "particle_effect") {
      return {
        id: blockId,
        type: "particle_effect",
        ...getCallback(options, "buildDefaultParticleEffectConfig", () => ({}))("snow"),
      };
    }

    if (safeType === "screen_shake") {
      return { id: blockId, type: "screen_shake", intensity: "medium", duration: "short" };
    }

    if (safeType === "screen_flash") {
      return {
        id: blockId,
        type: "screen_flash",
        color: "white",
        intensity: "medium",
        duration: "short",
      };
    }

    if (safeType === "screen_fade") {
      return {
        id: blockId,
        type: "screen_fade",
        action: "fade_out",
        color: "black",
        duration: "medium",
      };
    }

    if (safeType === "camera_zoom") {
      return {
        id: blockId,
        type: "camera_zoom",
        action: "zoom_in",
        strength: "medium",
        focus: "center",
      };
    }

    if (safeType === "camera_pan") {
      return { id: blockId, type: "camera_pan", target: "center", strength: "medium" };
    }

    if (safeType === "screen_filter") {
      return {
        id: blockId,
        type: "screen_filter",
        action: "apply",
        preset: "memory",
        strength: "medium",
        grade: getCallback(options, "getSafeScreenColorGrade", () => ({}))(),
      };
    }

    if (safeType === "depth_blur") {
      return {
        id: blockId,
        type: "depth_blur",
        action: "apply",
        focus: "center",
        strength: "medium",
      };
    }

    if (safeType === "jump" || safeType === "scene_call") {
      return {
        id: blockId,
        type: safeType,
        targetSceneId: getDefaultJumpTargetSceneId(sceneId),
      };
    }

    if (safeType === "scene_return") {
      return { id: blockId, type: "scene_return" };
    }

    if (safeType === "variable_set") {
      const variableId = getCallback(options, "getSafeVariableId", (value) => value ?? "")(variables[0]?.id);
      return {
        id: blockId,
        type: "variable_set",
        variableId,
        value: getCallback(options, "getVariableDefaultValue", () => null)(variableId),
      };
    }

    if (safeType === "variable_add") {
      return {
        id: blockId,
        type: "variable_add",
        variableId: getCallback(options, "getSafeVariableId", () => "")(null, "number"),
        value: 1,
      };
    }

    if (safeType === "text_input") {
      return {
        id: blockId,
        type: "text_input",
        variableId: getCallback(options, "getSafeVariableId", () => "")(null, ["string", "number"]),
        prompt: "请告诉我该怎样称呼你？",
        placeholder: "请输入姓名",
        defaultValue: "",
        maxLength: 32,
        allowEmpty: false,
      };
    }

    if (safeType === "condition") {
      return {
        id: blockId,
        type: "condition",
        branches: getCallback(options, "createDefaultConditionBranches", () => [])(blockId, sceneId),
        elseGotoSceneId: getDefaultJumpTargetSceneId(sceneId),
      };
    }

    return { id: blockId, type: safeType };
  }

  global.CanvasiaEditorStoryBlockFactory = Object.freeze({
    createDefaultStoryBlock,
  });
})(typeof window !== "undefined" ? window : globalThis);
