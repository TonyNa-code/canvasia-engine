(function attachScriptImportMappingTools(global) {
  function normalizeImportedLookupText(value) {
    return String(value ?? "")
      .trim()
      .toLowerCase()
      .replace(/\.[a-z0-9]+$/i, "")
      .replace(/[\s_-]+/g, "");
  }

  function getImportedLookupValues(item, extraValues = []) {
    const tags = Array.isArray(item?.tags) ? item.tags : [];
    return [
      item?.id,
      item?.name,
      item?.displayName,
      item?.fileName,
      item?.filename,
      item?.path,
      item?.src,
      item?.url,
      ...tags,
      ...extraValues,
    ].filter(Boolean);
  }

  function matchesImportedLookupHint(hint, values, { partial = false } = {}) {
    const normalizedHint = normalizeImportedLookupText(hint);
    if (!normalizedHint) {
      return false;
    }

    return values.some((value) => {
      const normalizedValue = normalizeImportedLookupText(value);
      if (!normalizedValue) {
        return false;
      }

      return (
        normalizedValue === normalizedHint ||
        (partial && (normalizedValue.includes(normalizedHint) || normalizedHint.includes(normalizedValue)))
      );
    });
  }

  function findImportedCharacterByHint(data, characterHint) {
    const characters = Array.isArray(data?.characters) ? data.characters : [];
    const exact = characters.find((character) => matchesImportedLookupHint(characterHint, getImportedLookupValues(character)));
    return (
      exact ??
      characters.find((character) =>
        matchesImportedLookupHint(characterHint, getImportedLookupValues(character), { partial: true })
      ) ??
      null
    );
  }

  function findImportedExpressionIdByHint(data, characterId, expressionHint) {
    const character = data?.charactersById instanceof Map
      ? data.charactersById.get(characterId)
      : (data?.characters ?? []).find((item) => item?.id === characterId);
    const expressions = Array.isArray(character?.expressions) ? character.expressions : [];
    const exact = expressions.find((expression) => matchesImportedLookupHint(expressionHint, getImportedLookupValues(expression)));
    const partial =
      exact ??
      expressions.find((expression) =>
        matchesImportedLookupHint(expressionHint, getImportedLookupValues(expression), { partial: true })
      );
    return partial?.id ?? "";
  }

  function findImportedAssetIdByHint(data, assetHint, assetTypes = []) {
    const allowedTypes = new Set(assetTypes.filter(Boolean));
    const assets = Array.isArray(data?.assetList) ? data.assetList : [];
    const candidates = allowedTypes.size ? assets.filter((asset) => allowedTypes.has(asset.type)) : assets;
    const exact = candidates.find((asset) => matchesImportedLookupHint(assetHint, getImportedLookupValues(asset)));
    const partial =
      exact ??
      candidates.find((asset) =>
        matchesImportedLookupHint(assetHint, getImportedLookupValues(asset), { partial: true })
      );
    return partial?.id ?? "";
  }

  function findImportedSceneByHint(data, sceneHint) {
    const scenes = Array.isArray(data?.scenes) ? data.scenes : [];
    const exact = scenes.find((scene) => matchesImportedLookupHint(sceneHint, getImportedLookupValues(scene)));
    return (
      exact ??
      scenes.find((scene) => matchesImportedLookupHint(sceneHint, getImportedLookupValues(scene), { partial: true })) ??
      null
    );
  }

  function findImportedSceneIdByHint(data, sceneHint) {
    return findImportedSceneByHint(data, sceneHint)?.id ?? "";
  }

  function getImportedEffectDuration(durationMs) {
    const ms = Number.parseFloat(durationMs ?? "");
    if (!Number.isFinite(ms)) {
      return "medium";
    }
    if (ms <= 450) {
      return "short";
    }
    if (ms >= 1000) {
      return "long";
    }
    return "medium";
  }

  function callScriptImportResolver(resolvers, name, args = [], fallback = "") {
    const resolver = resolvers?.[name];
    return typeof resolver === "function" ? resolver(...args) : fallback;
  }

  function cloneScriptImportStageDefaults(value) {
    return value && typeof value === "object" && !Array.isArray(value) ? { ...value } : {};
  }

  function normalizeImportedDraftBlockForScene(draftBlock, scene = null, resolvers = {}) {
    if (!draftBlock || typeof draftBlock !== "object") {
      return null;
    }

    const getAssetId = (hint, types) => callScriptImportResolver(resolvers, "findAssetIdByHint", [hint, types], "");
    const getSceneId = (hint) => callScriptImportResolver(resolvers, "findSceneIdByHint", [hint], "");
    const getTransition = (value) => callScriptImportResolver(resolvers, "getSafeTransition", [value], value || "fade");
    const getTransitionDurationMs = (value, fallback) =>
      callScriptImportResolver(resolvers, "getSafeTransitionDurationMs", [value, fallback], fallback ?? 600);
    const getNonNegativeNumber = (value, fallback) =>
      callScriptImportResolver(resolvers, "getSafeNonNegativeNumber", [value, fallback], fallback ?? 0);
    const getVolumePercent = (value, fallback) =>
      callScriptImportResolver(resolvers, "getSafeVolumePercent", [value, fallback], fallback ?? 100);
    const getVideoFit = (value) => callScriptImportResolver(resolvers, "getSafeVideoFit", [value], value || "contain");
    const getVideoVolume = (value) => callScriptImportResolver(resolvers, "getSafeVideoVolume", [value], 100);
    const getFadeAction = (value) => callScriptImportResolver(resolvers, "getSafeFadeAction", [value], value || "fade_out");
    const getEffectDuration = (value) =>
      callScriptImportResolver(resolvers, "getEffectDuration", [value], getImportedEffectDuration(value));
    const getChoiceContinueTarget = () => resolvers?.choiceContinueTarget ?? "__continue__";

    if (draftBlock.type === "dialogue") {
      const voiceAssetId = getAssetId(draftBlock.voiceHint, ["voice"]);
      return {
        type: "dialogue",
        speakerId: callScriptImportResolver(resolvers, "getSpeakerCharacterId", [draftBlock.speakerName], ""),
        text: String(draftBlock.text ?? "").trim(),
        ...(voiceAssetId ? { voiceAssetId, voiceVolume: 100 } : {}),
      };
    }

    if (draftBlock.type === "narration") {
      const voiceAssetId = getAssetId(draftBlock.voiceHint, ["voice"]);
      return {
        type: "narration",
        text: String(draftBlock.text ?? "").trim(),
        ...(voiceAssetId ? { voiceAssetId, voiceVolume: 100 } : {}),
      };
    }

    if (draftBlock.type === "choice") {
      return {
        type: "choice",
        options: (Array.isArray(draftBlock.options) ? draftBlock.options : [])
          .map((option) => ({
            text: String(option?.text ?? "").trim(),
            gotoSceneId: getSceneId(option?.targetHint) || getChoiceContinueTarget(),
          }))
          .filter((option) => option.text),
      };
    }

    if (draftBlock.type === "background") {
      return {
        type: "background",
        assetId: getAssetId(draftBlock.assetHint, ["background", "cg"]),
        transition: getTransition(draftBlock.transition ?? "fade"),
        transitionDurationMs: getTransitionDurationMs(draftBlock.transitionDurationMs, 600),
      };
    }

    if (draftBlock.type === "character_show") {
      const characterId = callScriptImportResolver(resolvers, "findCharacterIdByHint", [draftBlock.characterHint], "");
      const defaultPosition = callScriptImportResolver(
        resolvers,
        "getDefaultCharacterPosition",
        [characterId],
        "center"
      );
      return {
        type: "character_show",
        characterId,
        expressionId: callScriptImportResolver(
          resolvers,
          "findExpressionIdByHint",
          [characterId, draftBlock.expressionHint],
          ""
        ),
        position: callScriptImportResolver(
          resolvers,
          "getSafePosition",
          [draftBlock.position ?? defaultPosition],
          draftBlock.position ?? defaultPosition
        ),
        transition: getTransition(draftBlock.transition ?? "fade"),
        transitionDurationMs: getTransitionDurationMs(draftBlock.transitionDurationMs, 600),
        stage: cloneScriptImportStageDefaults(resolvers?.defaultCharacterStage),
      };
    }

    if (draftBlock.type === "character_hide") {
      return {
        type: "character_hide",
        characterId: callScriptImportResolver(resolvers, "findCharacterIdByHint", [draftBlock.characterHint], ""),
        transition: getTransition(draftBlock.transition ?? "fade"),
        transitionDurationMs: getTransitionDurationMs(draftBlock.transitionDurationMs, 600),
      };
    }

    if (draftBlock.type === "music_play") {
      return {
        type: "music_play",
        assetId: getAssetId(draftBlock.assetHint, ["bgm"]),
        loop: true,
        volume: 100,
        fadeInMs: getNonNegativeNumber(draftBlock.fadeInMs, 600),
        fadeOutMs: getNonNegativeNumber(draftBlock.fadeOutMs, 600),
        endMode: "until_next_music",
        endBlockId: "",
      };
    }

    if (draftBlock.type === "music_stop") {
      return {
        type: "music_stop",
        fadeOutMs: getNonNegativeNumber(draftBlock.fadeOutMs, 600),
      };
    }

    if (draftBlock.type === "sfx_play") {
      return {
        type: "sfx_play",
        assetId: getAssetId(draftBlock.assetHint, ["sfx"]),
        volume: getVolumePercent(draftBlock.volume, 100),
      };
    }

    if (draftBlock.type === "video_play") {
      const startTimeSeconds = getNonNegativeNumber(draftBlock.startTimeSeconds, 0);
      const endTimeSeconds = getNonNegativeNumber(draftBlock.endTimeSeconds, 0);
      return {
        type: "video_play",
        assetId: getAssetId(draftBlock.assetHint, ["video"]),
        title: String(draftBlock.title || draftBlock.assetHint || "").trim().slice(0, 80),
        fit: getVideoFit(draftBlock.fit),
        volume: getVideoVolume(draftBlock.volume),
        startTimeSeconds,
        endTimeSeconds: endTimeSeconds > startTimeSeconds ? endTimeSeconds : 0,
        skippable: draftBlock.skippable !== false,
      };
    }

    if (draftBlock.type === "screen_fade") {
      return {
        type: "screen_fade",
        action: getFadeAction(draftBlock.action ?? "fade_out"),
        color: "black",
        duration: getEffectDuration(draftBlock.durationMs),
      };
    }

    if (draftBlock.type === "jump") {
      return {
        type: "jump",
        targetSceneId:
          getSceneId(draftBlock.targetHint) ||
          callScriptImportResolver(resolvers, "getDefaultJumpTargetSceneId", [scene?.id], ""),
      };
    }

    return {
      type: "narration",
      text: String(draftBlock.text ?? "").trim(),
    };
  }

  global.CanvasiaEditorScriptImportMapping = Object.freeze({
    normalizeImportedLookupText,
    getImportedLookupValues,
    matchesImportedLookupHint,
    findImportedCharacterByHint,
    findImportedExpressionIdByHint,
    findImportedAssetIdByHint,
    findImportedSceneByHint,
    findImportedSceneIdByHint,
    getImportedEffectDuration,
    normalizeImportedDraftBlockForScene,
  });
})(typeof window !== "undefined" ? window : globalThis);
